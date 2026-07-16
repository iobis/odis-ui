from app.domain.search import SearchQuery
from app.search.elasticsearch.mappings import TEXT_FIELDS, raw_types_for_filter
from app.search.elasticsearch.queries import build_search_body, map_document_to_item, map_search_response
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


def test_sources_filter_uses_post_filter() -> None:
    body = build_search_body(SearchQuery(q="marine", sources=["40", "3308"]))
    assert body["post_filter"]["terms"]["datasource_id.keyword"] == ["40", "3308"]
    query_filters = body["query"]["bool"]["filter"]
    assert not any("datasource_id.keyword" in str(f) for f in query_filters)


def test_disjunctive_source_facet_applies_type_not_source() -> None:
    body = build_search_body(SearchQuery(types=["dataset"], sources=["40"]))
    source_facet_filter = body["aggs"]["sources"]["filter"]["bool"]["filter"]
    assert any("@type.keyword" in str(f) for f in source_facet_filter)
    assert not any("datasource_id.keyword" in str(f) for f in source_facet_filter)


def test_disjunctive_type_facet_applies_source_not_type() -> None:
    body = build_search_body(SearchQuery(types=["dataset"], sources=["40"]))
    type_facet_filter = body["aggs"]["types"]["filter"]["bool"]["filter"]
    assert any("datasource_id.keyword" in str(f) for f in type_facet_filter)
    assert not any(
        item.get("terms", {}).get("@type.keyword") == ["Dataset", "schema:Dataset"]
        for item in type_facet_filter
        if isinstance(item, dict)
    )


def test_combined_filters_use_post_filter_bool() -> None:
    body = build_search_body(SearchQuery(types=["dataset"], sources=["40", "3308"]))
    post_filter = body["post_filter"]["bool"]["filter"]
    assert len(post_filter) == 2


def test_default_type_filter() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    type_filter = next(
        item for item in body["query"]["bool"]["filter"] if "@type.keyword" in item.get("terms", {})
    )
    assert "Dataset" in type_filter["terms"]["@type.keyword"]
    assert "schema:Dataset" in type_filter["terms"]["@type.keyword"]


def test_boattrip_type_filter_uses_pascal_case_keyword() -> None:
    assert raw_types_for_filter(["boattrip"]) == ["BoatTrip"]
    body = build_search_body(SearchQuery(types=["boattrip"]))
    assert body["post_filter"]["terms"]["@type.keyword"] == ["BoatTrip"]
    scope_filter = next(
        item for item in body["query"]["bool"]["filter"] if "@type.keyword" in item.get("terms", {})
    )
    assert "Dataset" in scope_filter["terms"]["@type.keyword"]


def test_selected_type_filter_uses_post_filter() -> None:
    body = build_search_body(SearchQuery(types=["dataset"]))
    assert body["post_filter"]["terms"]["@type.keyword"] == ["Dataset", "schema:Dataset"]


def test_search_limits_source_fields() -> None:
    body = build_search_body(SearchQuery(q="marine"))
    assert "data" in body["_source"]
    assert "name" in body["_source"]
    assert "indexed_at" not in body["_source"]


def test_map_search_response_decodes_html_entities_in_title() -> None:
    item = map_document_to_item(
        "abc",
        {"@type": "Dataset", "name": "Total E&amp;P UK Ltd"},
    )
    assert item.title == "Total E&P UK Ltd"


def test_boattrip_with_event_types_displays_as_cruise() -> None:
    item = map_document_to_item(
        "cruise-1",
        {"@type": ["Event", "BoatTrip"], "name": "Cruise: D231"},
    )
    assert item.type == "Cruise"


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
        "aggregations": {
            "types": {"buckets": {"buckets": []}},
            "sources": {"buckets": {"buckets": []}},
        },
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
        "aggregations": {
            "types": {"buckets": {"buckets": []}},
            "sources": {"buckets": {"buckets": []}},
        },
    }
    response = map_search_response(query, raw)
    assert response.items[0].highlight == {"description": "Analysis of <em>coral</em> growth"}
