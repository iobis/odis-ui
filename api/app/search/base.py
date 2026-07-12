from typing import Protocol

from app.domain.search import HealthStatus, SearchQuery, SearchResponse


class SearchBackend(Protocol):
    async def search(self, query: SearchQuery) -> SearchResponse: ...

    async def health(self) -> HealthStatus: ...

    async def close(self) -> None: ...
