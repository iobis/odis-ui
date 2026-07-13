from app.domain.enums import PRIMARY_RECORD_TYPES
from app.domain.search import SearchQuery
from app.search.elasticsearch.mappings import TEXT_FIELDS
from app.search.elasticsearch.queries import build_search_body, map_search_response
from app.search.elasticsearch.urls import elasticsearch_document_url


def test_elasticsearch_document_url() -> None:
    assert (
        elasticsearch_document_url("http://localhost:9200/", "odis_metadata", "abc123")
        == "http://localhost:9200/odis_metadata/_doc/abc123"
    )


def test_text_search_uses_boosted_fields() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    must = body["query"]["bool"]["must"][0]["multi_match"]
    assert must["query"] == "marine"
    assert must["fields"] == list(TEXT_FIELDS)
    assert must["type"] == "best_fields"


def test_text_search_requires_searchable_text() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    filters = body["query"]["bool"]["filter"]
    assert any("description" in str(f) or "keywords" in str(f) for f in filters)


def test_default_type_filter() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    type_filter = next(
        item for item in body["query"]["bool"]["filter"] if "record_type" in item.get("terms", {})
    )
    assert type_filter["terms"]["record_type"] == list(PRIMARY_RECORD_TYPES)


def test_map_search_response_highlight_title() -> None:
    query = SearchQuery(q="marine")
    raw = {
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "hits": [
                {
                    "_id": "abc",
                    "_source": {
                        "@type": "Dataset",
                        "name": "Marine dataset",
                        "url": "https://example.com",
                        "datasource_id": "40",
                    },
                    "fields": {"record_type": ["dataset"]},
                    "highlight": {"name": ["<em>Marine</em> dataset"]},
                }
            ],
        },
        "aggregations": {"types": {"buckets": []}, "sources": {"buckets": []}},
    }
    response = map_search_response(query, raw)
    assert response.items[0].highlight == {"title": "<em>Marine</em> dataset"}


def test_map_search_response_highlight_description() -> None:
    query = SearchQuery(q="coral")
    raw = {
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "hits": [
                {
                    "_id": "abc",
                    "_source": {
                        "@type": "Dataset",
                        "name": "Reef study",
                        "description": "Analysis of coral growth",
                        "url": "https://example.com",
                        "datasource_id": "40",
                    },
                    "fields": {"record_type": ["dataset"]},
                    "highlight": {"description": ["Analysis of <em>coral</em> growth"]},
                }
            ],
        },
        "aggregations": {"types": {"buckets": []}, "sources": {"buckets": []}},
    }
    response = map_search_response(query, raw)
    assert response.items[0].highlight == {"description": "Analysis of <em>coral</em> growth"}
