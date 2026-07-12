from elasticsearch import AsyncElasticsearch

from app.config import Settings
from app.domain.search import HealthStatus, SearchFacets, SearchQuery, SearchResponse
from app.search.elasticsearch.client import create_client


class ElasticsearchBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncElasticsearch = create_client(settings)

    @property
    def index(self) -> str:
        return self._settings.es_index

    async def search(self, query: SearchQuery) -> SearchResponse:
        # Stub: full query logic (runtime record_type, facets, pagination) comes later.
        _ = query
        return SearchResponse(
            total=0,
            facets=SearchFacets(),
            items=[],
            page=query.page,
            size=query.size,
        )

    async def health(self) -> HealthStatus:
        index_reachable = False
        detail: str | None = None
        try:
            exists = await self._client.indices.exists(index=self.index)
            index_reachable = bool(exists)
            if not index_reachable:
                detail = f"Index '{self.index}' not found"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"

        status = "ok" if index_reachable else "degraded"
        return HealthStatus(
            status=status,
            backend="elasticsearch",
            index=self.index,
            index_reachable=index_reachable,
            detail=detail,
        )

    async def close(self) -> None:
        await self._client.close()
