from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceRef(BaseModel):
    id: str = Field(description="ODISCat datasource identifier")
    name: str | None = Field(default=None, description="Human-readable system name when enriched")


class SearchItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "ffb519bd6b732afc3948bfc8c1805a74",
                    "title": "Salinity observations — Bellingham Bay",
                    "summary": "Hourly salinity measurements from…",
                    "type": "Dataset",
                    "url": "https://data.ioos.us/dataset/example",
                    "source": {"id": "3308", "name": "IOOS Data Catalog"},
                    "highlight": {"summary": "Hourly <em>salinity</em>…"},
                }
            ]
        }
    )

    id: str
    title: str
    summary: str | None = None
    type: str
    url: str | None = None
    source: SourceRef | None = None
    highlight: dict[str, str] | None = None
    elasticsearch_document_url: str | None = Field(
        default=None,
        description="Direct link to the document in Elasticsearch",
    )


class FacetBucket(BaseModel):
    value: str
    count: int


class SourceFacetBucket(BaseModel):
    id: str
    name: str | None = None
    count: int


class SearchFacets(BaseModel):
    types: list[FacetBucket] = Field(default_factory=list)
    sources: list[SourceFacetBucket] = Field(default_factory=list)


class SearchQuery(BaseModel):
    q: str | None = Field(
        default=None,
        description="Search query matched against title, description, and keywords",
    )
    types: list[str] = Field(default_factory=list, description="Record type filters")
    sources: list[str] = Field(default_factory=list, description="Filter by datasource_id")
    sort: str = Field(default="relevance", description="Sort order: relevance or title")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=50)


class SearchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 412,
                    "facets": {
                        "types": [{"value": "dataset", "count": 380}],
                        "sources": [{"id": "3308", "name": "IOOS Data Catalog", "count": 210}],
                    },
                    "items": [],
                    "page": 1,
                    "size": 20,
                }
            ]
        }
    )

    total: int
    facets: SearchFacets
    items: list[SearchItem]
    page: int
    size: int


class HealthStatus(BaseModel):
    status: str = Field(description="Overall status: ok or degraded")
    backend: str = Field(description="Configured search backend identifier")
    index: str = Field(description="Search index name")
    index_reachable: bool = Field(description="Whether the search index is reachable")
    detail: str | None = Field(
        default=None,
        description="Error detail when status is degraded",
    )


class RecordResponse(SearchItem):
    raw: dict[str, Any] | None = Field(
        default=None,
        description="Full stored document when requested with ?raw=1",
    )
