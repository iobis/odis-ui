"""Gleaner multi-index Elasticsearch corpus (one index per data source)."""

from __future__ import annotations

from urllib.parse import quote, unquote

# Index name suffix ↔ source facet id ↔ display label
GLEANER_SOURCES: dict[str, str] = {
    "obps": "Ocean Best Practices System (OBPS)",
    "medin": "Portal - Marine Environmental Data and Information Network",
    "obis": "Ocean Biodiversity Information System",
    "oe": "OceanExpert - A Directory of Marine and Freshwater Professionals",
}

GLEANER_SOURCE_IDS: frozenset[str] = frozenset(GLEANER_SOURCES)

DEFAULT_INDICES: tuple[str, ...] = tuple(f"gleaner-{source}" for source in GLEANER_SOURCES)


def index_for_source(source: str) -> str:
    return f"gleaner-{source}"


def source_from_index(index: str) -> str | None:
    if index.startswith("gleaner-"):
        source = index.removeprefix("gleaner-")
        return source if source in GLEANER_SOURCE_IDS else source
    return None


def encode_record_id(source: str, doc_id: str) -> str:
    """Namespace Gleaner ids so composite routing can find them later."""
    return f"gleaner:{source}:{quote(doc_id, safe='')}"


def decode_record_id(record_id: str) -> tuple[str, str] | None:
    if not record_id.startswith("gleaner:"):
        return None
    parts = record_id.split(":", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], unquote(parts[2])


def is_gleaner_source(source_id: str) -> bool:
    return source_id in GLEANER_SOURCE_IDS
