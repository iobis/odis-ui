"""Field mappings for the odis_metadata index."""

from app.domain.enums import PRIMARY_RECORD_TYPES

TITLE_FIELDS = ("name^3", "schema:name^3")
TEXT_FIELDS = (
    *TITLE_FIELDS,
    "description",
    "schema:description",
    "keywords^2",
    "schema:keywords^2",
)
TYPE_FIELD = "@type"
DATASOURCE_FIELD = "datasource_id"

# Raw @type.keyword values for each normalised primary record type.
PRIMARY_TYPE_VARIANTS: dict[str, tuple[str, ...]] = {
    "dataset": ("Dataset", "schema:Dataset"),
    "person": ("Person",),
    "organization": ("Organization", "schema:Organization"),
    "creativework": ("CreativeWork", "schema:CreativeWork"),
    "event": ("Event",),
    "researchproject": ("ResearchProject", "schema:ResearchProject"),
    "boattrip": ("BoatTrip",),
    "service": ("Service",),
}

# Word segments used to reconstruct PascalCase @type values from normalised keys.
_TYPE_WORDS = sorted(
    [
        "scholarly",
        "creative",
        "research",
        "organization",
        "professional",
        "project",
        "article",
        "dataset",
        "service",
        "person",
        "event",
        "course",
        "boat",
        "trip",
        "work",
        "data",
        "set",
    ],
    key=len,
    reverse=True,
)


def _lowercase_to_pascal(normalized: str) -> str:
    parts: list[str] = []
    remaining = normalized
    while remaining:
        for word in _TYPE_WORDS:
            if remaining.startswith(word):
                parts.append(word.capitalize())
                remaining = remaining[len(word) :]
                break
        else:
            parts.append(remaining.capitalize())
            break
    return "".join(parts)


def _raw_type_variants(normalized: str) -> tuple[str, ...]:
    if normalized in PRIMARY_TYPE_VARIANTS:
        return PRIMARY_TYPE_VARIANTS[normalized]
    pascal = _lowercase_to_pascal(normalized)
    return (pascal, f"schema:{pascal}")


def raw_types_for_filter(normalized_types: list[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for normalized in normalized_types:
        for raw in _raw_type_variants(normalized):
            if raw not in seen:
                seen.add(raw)
                values.append(raw)
    return values


def default_raw_types() -> list[str]:
    return raw_types_for_filter(list(PRIMARY_RECORD_TYPES))
