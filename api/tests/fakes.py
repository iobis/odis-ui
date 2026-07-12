from app.domain.search import (
    FacetBucket,
    HealthStatus,
    SearchFacets,
    SearchItem,
    SearchQuery,
    SearchResponse,
    SourceFacetBucket,
    SourceRef,
)


class FakeSearchBackend:
    def __init__(self) -> None:
        self.last_query: SearchQuery | None = None
        self.health_status = HealthStatus(
            status="ok",
            backend="fake",
            index="odis_metadata",
            index_reachable=True,
        )
        self.search_response = SearchResponse(
            total=1,
            facets=SearchFacets(
                types=[FacetBucket(value="dataset", count=1)],
                sources=[SourceFacetBucket(id="3308", name="IOOS Data Catalog", count=1)],
            ),
            items=[
                SearchItem(
                    id="test-id",
                    title="Test Dataset",
                    summary="A test record",
                    type="Dataset",
                    url="https://example.com/dataset",
                    source=SourceRef(id="3308", name="IOOS Data Catalog"),
                )
            ],
            page=1,
            size=20,
        )

    async def search(self, query: SearchQuery) -> SearchResponse:
        self.last_query = query
        return self.search_response.model_copy(update={"page": query.page, "size": query.size})

    async def health(self) -> HealthStatus:
        return self.health_status

    async def close(self) -> None:
        pass
