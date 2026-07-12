from enum import StrEnum

PRIMARY_RECORD_TYPES: tuple[str, ...] = (
    "dataset",
    "person",
    "organization",
    "creativework",
    "event",
    "researchproject",
)


class SortOrder(StrEnum):
    RELEVANCE = "relevance"
    TITLE = "title"
