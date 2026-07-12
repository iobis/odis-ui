"""Build Elasticsearch query bodies and map responses to domain models."""

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
from app.search.elasticsearch.mappings import DATASOURCE_FIELD, TITLE_FIELDS

RECORD_TYPE_RUNTIME = {
    "record_type": {
        "type": "keyword",
        "script": {
            "source": """
                String typeVal = null;
                if (doc.containsKey('@type.keyword') && doc['@type.keyword'].size() > 0) {
                    typeVal = doc['@type.keyword'].value;
                } else if (doc.containsKey('@type') && doc['@type'].size() > 0) {
                    typeVal = doc['@type'].value;
                }
                if (typeVal == null || typeVal.length() == 0) {
                    return;
                }
                int idx = typeVal.lastIndexOf('/');
                if (idx >= 0) {
                    typeVal = typeVal.substring(idx + 1);
                }
                if (typeVal.startsWith('schema:')) {
                    typeVal = typeVal.substring(7);
                }
                emit(typeVal.toLowerCase());
            """,
        },
    }
}

HAS_TITLE = {
    "bool": {
        "should": [{"exists": {"field": "name"}}, {"exists": {"field": "schema:name"}}],
        "minimum_should_match": 1,
    }
}


def _resolved_types(query: SearchQuery) -> list[str]:
    if query.types:
        return [value.lower() for value in query.types]
    return list(PRIMARY_RECORD_TYPES)


def _title_clause(query: SearchQuery) -> dict[str, Any]:
    return {
        "multi_match": {
            "query": query.q,
            "fields": list(TITLE_FIELDS),
            "type": "best_fields",
        }
    }


def build_search_body(query: SearchQuery) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [
        {"terms": {"record_type": _resolved_types(query)}},
    ]
    if query.source:
        filters.append({"term": {f"{DATASOURCE_FIELD}.keyword": query.source}})
    if query.q:
        filters.append(HAS_TITLE)

    must: list[dict[str, Any]] = []
    if query.q:
        must.append(_title_clause(query))

    body: dict[str, Any] = {
        "runtime_mappings": RECORD_TYPE_RUNTIME,
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
            "types": {"terms": {"field": "record_type", "size": 30}},
            "sources": {"terms": {"field": f"{DATASOURCE_FIELD}.keyword", "size": 30}},
        },
    }

    if query.q:
        body["highlight"] = {
            "fields": {
                "name": {},
                "schema:name": {},
            }
        }

    if query.sort == SortOrder.TITLE.value:
        body["sort"] = [
            {"name.keyword": {"order": "asc", "missing": "_last", "unmapped_type": "keyword"}},
            {"schema:name.keyword": {"order": "asc", "missing": "_last", "unmapped_type": "keyword"}},
        ]
    elif not query.q:
        body["sort"] = [{"indexed_at": {"order": "desc", "unmapped_type": "keyword"}}]

    return body


def _field_value(source: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
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
            mapped[key] = fragments[0]
    return mapped or None


def map_search_response(query: SearchQuery, raw: dict[str, Any]) -> SearchResponse:
    hits = raw.get("hits", {})
    total_value = hits.get("total", {})
    total = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value or 0)

    items: list[SearchItem] = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        title = _field_value(source, "name", "schema:name") or "(untitled)"
        summary = _field_value(source, "description", "schema:description")
        datasource_id = _field_value(source, DATASOURCE_FIELD)
        fields = hit.get("fields") or {}
        record_type_values = fields.get("record_type") or []
        record_type = record_type_values[0] if record_type_values else None

        source_ref = SourceRef(id=datasource_id) if datasource_id else None
        items.append(
            SearchItem(
                id=hit.get("_id", ""),
                title=title,
                summary=summary,
                type=_display_type(record_type, source.get("@type")),
                url=_field_value(source, "url"),
                source=source_ref,
                highlight=_map_highlight(hit.get("highlight")),
            )
        )

    aggs = raw.get("aggregations", {})
    type_facets = [
        FacetBucket(value=bucket["key"], count=bucket["doc_count"])
        for bucket in aggs.get("types", {}).get("buckets", [])
        if bucket.get("key")
    ]
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
