from app.domain.enums import PRIMARY_RECORD_TYPES
from app.domain.search import SearchQuery
from app.search.elasticsearch.queries import build_search_body, map_search_response
from app.search.elasticsearch.urls import elasticsearch_document_url


def test_elasticsearch_document_url() -> None:
    assert (
        elasticsearch_document_url("http://localhost:9200/", "odis_metadata", "abc123")
        == "http://localhost:9200/odis_metadata/_doc/abc123"
    )
from app.domain.search import SearchQuery
from app.search.elasticsearch.queries import build_search_body, map_search_response


def test_title_search_uses_name_fields() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    must = body["query"]["bool"]["must"][0]["multi_match"]
    assert must["query"] == "marine"
    assert set(must["fields"]) == {"name^3", "schema:name^3"}
    assert must["type"] == "best_fields"


def test_title_search_requires_title_field() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    filters = body["query"]["bool"]["filter"]
    assert any("exists" in str(f) for f in filters)


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
