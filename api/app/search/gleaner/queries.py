"""Map Gleaner summoned documents to domain SearchItem models."""

from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

from app.domain.enums import PRIMARY_RECORD_TYPES, SortOrder
from app.domain.search import (
    BoundingBox,
    FacetBucket,
    GeoPoint,
    SearchFacets,
    SearchItem,
    SearchQuery,
    SearchResponse,
    SourceFacetBucket,
    SourceRef,
    SpatialExtent,
)
from app.search.elasticsearch.mappings import raw_types_for_filter
from app.search.gleaner.ids import GLEANER_SOURCES, encode_record_id, source_from_index

# Gleaner also indexes Course; keep ODIS PRIMARY_RECORD_TYPES unchanged.
GLEANER_PRIMARY_TYPES: tuple[str, ...] = (*PRIMARY_RECORD_TYPES, "course")

SEARCH_SOURCE_FIELDS = [
    "id",
    "name",
    "description",
    "keywords",
    "type",
    "url",
    "source",
    "source_url",
    "jsonld",
]


def _type_values_for_filter(normalized: list[str]) -> list[str]:
    """Gleaner stores PascalCase schema.org types on keyword field `type`."""
    values: list[str] = []
    seen: set[str] = set()
    for raw in raw_types_for_filter(normalized):
        value = raw.removeprefix("schema:")
        if value not in seen:
            seen.add(value)
            values.append(value)
    return values


def _base_filters(query: SearchQuery) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = [
        {"terms": {"type": _type_values_for_filter(list(GLEANER_PRIMARY_TYPES))}},
    ]
    return filters


def _type_facet_filters(query: SearchQuery) -> list[dict[str, Any]]:
    filters = _base_filters(query)
    if query.sources:
        filters.append({"terms": {"source": query.sources}})
    return filters


def _source_facet_filters(query: SearchQuery) -> list[dict[str, Any]]:
    filters = _base_filters(query)
    if query.types:
        filters.append({"terms": {"type": _type_values_for_filter([t.lower() for t in query.types])}})
    return filters


def _user_post_filter(query: SearchQuery) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if query.types:
        clauses.append({"terms": {"type": _type_values_for_filter([t.lower() for t in query.types])}})
    if query.sources:
        clauses.append({"terms": {"source": query.sources}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"bool": {"filter": clauses}}


def _filter_agg(filters: list[dict[str, Any]], field: str, size: int) -> dict[str, Any]:
    return {
        "filter": {"bool": {"filter": filters}},
        "aggs": {"buckets": {"terms": {"field": field, "size": size}}},
    }


def build_search_body(query: SearchQuery) -> dict[str, Any]:
    filters = _base_filters(query)
    must: list[dict[str, Any]] = []
    if query.q:
        must.append(
            {
                "multi_match": {
                    "query": query.q,
                    "fields": ["name^3", "description", "keywords^2"],
                    "type": "best_fields",
                }
            }
        )

    body: dict[str, Any] = {
        "query": {
            "bool": {
                "filter": filters,
                **({"must": must} if must else {}),
            }
        },
        "from": (query.page - 1) * query.size,
        "size": query.size,
        "_source": SEARCH_SOURCE_FIELDS,
        "aggs": {
            "types": _filter_agg(_type_facet_filters(query), "type", 100),
            "sources": _filter_agg(_source_facet_filters(query), "source", 50),
        },
        "track_scores": True,
    }

    post_filter = _user_post_filter(query)
    if post_filter is not None:
        body["post_filter"] = post_filter

    if query.q:
        body["highlight"] = {
            "fields": {
                "name": {},
                "description": {},
                "keywords": {},
            }
        }

    if query.sort == SortOrder.TITLE.value:
        body["sort"] = [{"name.raw": {"order": "asc", "missing": "_last"}}]

    return body


def _as_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return html.unescape(value.strip())
    return None


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_as_str(v) for v in value) if item]
    single = _as_str(value)
    return [single] if single else []


def _normalize_type(raw: Any) -> str | None:
    values = _as_str_list(raw) if not isinstance(raw, str) else [_as_str(raw) or ""]
    candidates = [v.lower() for v in values if v]
    if not candidates:
        return None
    priority = (
        "dataset",
        "person",
        "organization",
        "creativework",
        "researchproject",
        "event",
        "course",
        "service",
    )
    for preferred in priority:
        if preferred in candidates:
            return preferred
    return candidates[0]


def _display_type(normalized: str | None, raw: Any) -> str:
    if normalized == "creativework":
        return "CreativeWork"
    if normalized == "researchproject":
        return "ResearchProject"
    if normalized:
        return normalized.title()
    values = _as_str_list(raw)
    return values[0] if values else "Record"


def _map_highlight(highlight: dict[str, list[str]] | None) -> dict[str, str] | None:
    if not highlight:
        return None
    mapped: dict[str, str] = {}
    for field, fragments in highlight.items():
        if not fragments:
            continue
        key = "title" if field == "name" else field
        mapped[key] = html.unescape(fragments[0])
    return mapped or None


def _extract_spatial(jsonld: Any) -> SpatialExtent | None:
    """Best-effort spatial from stored JSON-LD (object is not indexed)."""
    if not isinstance(jsonld, dict):
        return None

    boxes: list[BoundingBox] = []
    points: list[GeoPoint] = []

    work_location = jsonld.get("workLocation")
    if isinstance(work_location, dict):
        geo = work_location.get("geo")
        if isinstance(geo, dict):
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            try:
                if lat is not None and lon is not None:
                    points.append(GeoPoint(lat=float(lat), lon=float(lon)))
            except (TypeError, ValueError):
                pass

    spatial = jsonld.get("spatialCoverage")
    coverages = spatial if isinstance(spatial, list) else [spatial] if spatial else []
    for coverage in coverages:
        if not isinstance(coverage, dict):
            continue
        geo = coverage.get("geo")
        geos = geo if isinstance(geo, list) else [geo] if geo else []
        for entry in geos:
            if not isinstance(entry, dict):
                continue
            box = entry.get("box")
            if isinstance(box, str):
                parts = box.replace(",", " ").split()
                if len(parts) == 4:
                    try:
                        south, west, north, east = (float(p) for p in parts)
                        boxes.append(BoundingBox(south=south, west=west, north=north, east=east))
                    except ValueError:
                        pass

    if not boxes and not points:
        return None
    return SpatialExtent(boxes=boxes, points=points)


def map_document_to_item(
    es_id: str,
    source: dict[str, Any],
    *,
    index: str | None = None,
    highlight: dict[str, list[str]] | None = None,
    elasticsearch_document_url: str | None = None,
    score: float | None = None,
) -> SearchItem:
    source_code = _as_str(source.get("source")) or (source_from_index(index) if index else None) or "unknown"
    doc_id = _as_str(source.get("id")) or es_id
    record_id = encode_record_id(source_code, doc_id)
    normalized = _normalize_type(source.get("type"))
    summary = _as_str(source.get("description"))
    url = _as_str(source.get("url")) or _as_str(source.get("source_url"))
    item = SearchItem(
        id=record_id,
        title=_as_str(source.get("name")) or "(untitled)",
        summary=summary,
        type=_display_type(normalized, source.get("type")),
        url=url,
        source=SourceRef(
            id=source_code,
            name=GLEANER_SOURCES.get(source_code),
        ),
        highlight=_map_highlight(highlight),
        spatial=_extract_spatial(source.get("jsonld")),
        elasticsearch_document_url=elasticsearch_document_url,
    )
    # Attach score for composite ranking without changing the public schema.
    object.__setattr__(item, "_score", score if score is not None else 0.0)
    return item


def map_search_response(
    query: SearchQuery,
    raw: dict[str, Any],
    *,
    document_url_for: Callable[[str, str], str] | None = None,
) -> SearchResponse:
    hits = raw.get("hits", {})
    total_value = hits.get("total", {})
    total = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value or 0)

    items: list[SearchItem] = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        es_id = hit.get("_id", "")
        index = hit.get("_index", "")
        source_code = _as_str(source.get("source")) or source_from_index(index) or "unknown"
        doc_url = None
        if document_url_for and index:
            doc_url = document_url_for(index, es_id)
        items.append(
            map_document_to_item(
                es_id,
                source,
                index=index,
                highlight=hit.get("highlight"),
                elasticsearch_document_url=doc_url,
                score=hit.get("_score") or 0.0,
            )
        )

    aggs = raw.get("aggregations", {})
    type_facets = [
        FacetBucket(value=str(bucket["key"]).lower(), count=bucket["doc_count"])
        for bucket in aggs.get("types", {}).get("buckets", {}).get("buckets", [])
        if bucket.get("key")
    ]
    source_facets = [
        SourceFacetBucket(
            id=str(bucket["key"]),
            name=GLEANER_SOURCES.get(str(bucket["key"])),
            count=bucket["doc_count"],
        )
        for bucket in aggs.get("sources", {}).get("buckets", {}).get("buckets", [])
        if bucket.get("key")
    ]

    return SearchResponse(
        total=total,
        facets=SearchFacets(types=type_facets, sources=source_facets),
        items=items,
        page=query.page,
        size=query.size,
    )
