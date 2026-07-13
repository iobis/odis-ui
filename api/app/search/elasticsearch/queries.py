"""Build Elasticsearch query bodies and map responses to domain models."""

import html
from collections.abc import Callable
from typing import Any

from app.domain.enums import PRIMARY_RECORD_TYPES, SortOrder
from app.domain.search import (
    FacetBucket,
    SearchFacets,
    SearchItem,
    SearchQuery,
    SearchResponse,
    SourceFacetBucket,
    SourceRef,
)
from app.search.elasticsearch.mappings import (
    DATASOURCE_FIELD,
    TEXT_FIELDS,
    raw_types_for_filter,
)

HAS_SEARCHABLE_TEXT = {
    "bool": {
        "should": [
            {"exists": {"field": "name"}},
            {"exists": {"field": "schema:name"}},
            {"exists": {"field": "description"}},
            {"exists": {"field": "schema:description"}},
            {"exists": {"field": "keywords"}},
            {"exists": {"field": "schema:keywords"}},
        ],
        "minimum_should_match": 1,
    }
}


def _resolved_types(query: SearchQuery) -> list[str]:
    if query.types:
        return [value.lower() for value in query.types]
    return list(PRIMARY_RECORD_TYPES)


def _scope_type_filter() -> dict[str, Any]:
    """Default record-type scope for search and facet counts."""
    return {"terms": {"@type.keyword": raw_types_for_filter(list(PRIMARY_RECORD_TYPES))}}


def _selected_type_post_filter(query: SearchQuery) -> dict[str, Any] | None:
    if not query.types:
        return None
    return {"terms": {"@type.keyword": raw_types_for_filter(_resolved_types(query))}}


def _text_clause(query: SearchQuery) -> dict[str, Any]:
    return {
        "multi_match": {
            "query": query.q,
            "fields": list(TEXT_FIELDS),
            "type": "best_fields",
        }
    }


def build_search_body(query: SearchQuery) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [
        _scope_type_filter(),
    ]
    if query.sources:
        filters.append({"terms": {f"{DATASOURCE_FIELD}.keyword": query.sources}})
    if query.q:
        filters.append(HAS_SEARCHABLE_TEXT)

    must: list[dict[str, Any]] = []
    if query.q:
        must.append(_text_clause(query))

    body: dict[str, Any] = {
        "query": {
            "bool": {
                "filter": filters,
                **({"must": must} if must else {}),
            }
        },
        "from": (query.page - 1) * query.size,
        "size": query.size,
        "_source": {"excludes": ["data"]},
        "aggs": {
            "types": {"terms": {"field": "@type.keyword", "size": 100}},
            "sources": {"terms": {"field": f"{DATASOURCE_FIELD}.keyword", "size": 30}},
        },
    }

    post_filter = _selected_type_post_filter(query)
    if post_filter is not None:
        body["post_filter"] = post_filter

    if query.q:
        body["highlight"] = {
            "fields": {
                "name": {},
                "schema:name": {},
                "description": {},
                "schema:description": {},
                "keywords": {},
                "schema:keywords": {},
            }
        }

    if query.sort == SortOrder.TITLE.value:
        body["sort"] = [
            {"name.keyword": {"order": "asc", "missing": "_last", "unmapped_type": "keyword"}},
            {"schema:name.keyword": {"order": "asc", "missing": "_last", "unmapped_type": "keyword"}},
        ]

    return body


def _field_value(source: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return html.unescape(value.strip())
    return None


def _display_type(record_type: str | None, raw_type: Any) -> str:
    if record_type:
        return record_type.replace("creativework", "CreativeWork").title()
    if isinstance(raw_type, str) and raw_type.strip():
        value = raw_type.strip()
        if value.startswith("schema:"):
            value = value[7:]
        if "/" in value:
            value = value.rsplit("/", 1)[-1]
        return value
    return "Record"


def _map_highlight(highlight: dict[str, list[str]] | None) -> dict[str, str] | None:
    if not highlight:
        return None
    mapped: dict[str, str] = {}
    for field, fragments in highlight.items():
        if fragments:
            key = "title" if field in {"name", "schema:name"} else field.replace("schema:", "")
            mapped[key] = html.unescape(fragments[0])
    return mapped or None


def _normalize_record_type(raw_type: Any) -> str | None:
    if not isinstance(raw_type, str) or not raw_type.strip():
        return None
    value = raw_type.strip()
    if "/" in value:
        value = value.rsplit("/", 1)[-1]
    if value.startswith("schema:"):
        value = value[7:]
    return value.lower()


def _merge_type_facet_buckets(buckets: list[dict[str, Any]]) -> list[FacetBucket]:
    counts: dict[str, int] = {}
    for bucket in buckets:
        normalized = _normalize_record_type(bucket.get("key"))
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + bucket["doc_count"]
    return sorted(
        [FacetBucket(value=value, count=count) for value, count in counts.items()],
        key=lambda bucket: bucket.count,
        reverse=True,
    )


def map_document_to_item(
    record_id: str,
    source: dict[str, Any],
    *,
    highlight: dict[str, list[str]] | None = None,
    elasticsearch_document_url: str | None = None,
) -> SearchItem:
    title = _field_value(source, "name", "schema:name") or "(untitled)"
    summary = _field_value(source, "description", "schema:description")
    datasource_id = _field_value(source, DATASOURCE_FIELD)
    normalized_type = _normalize_record_type(source.get("@type"))
    source_ref = SourceRef(id=datasource_id) if datasource_id else None
    return SearchItem(
        id=record_id,
        title=title,
        summary=summary,
        type=_display_type(normalized_type, source.get("@type")),
        url=_field_value(source, "url"),
        source=source_ref,
        highlight=_map_highlight(highlight),
        elasticsearch_document_url=elasticsearch_document_url,
    )


def map_search_response(
    query: SearchQuery,
    raw: dict[str, Any],
    *,
    document_url_for: Callable[[str], str] | None = None,
) -> SearchResponse:
    hits = raw.get("hits", {})
    total_value = hits.get("total", {})
    total = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value or 0)

    items: list[SearchItem] = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        record_id = hit.get("_id", "")
        items.append(
            map_document_to_item(
                record_id,
                source,
                highlight=hit.get("highlight"),
                elasticsearch_document_url=document_url_for(record_id) if document_url_for else None,
            )
        )

    aggs = raw.get("aggregations", {})
    type_facets = _merge_type_facet_buckets(aggs.get("types", {}).get("buckets", []))
    source_facets = [
        SourceFacetBucket(id=str(bucket["key"]), count=bucket["doc_count"])
        for bucket in aggs.get("sources", {}).get("buckets", [])
        if bucket.get("key")
    ]

    return SearchResponse(
        total=total,
        facets=SearchFacets(types=type_facets, sources=source_facets),
        items=items,
        page=query.page,
        size=query.size,
    )
