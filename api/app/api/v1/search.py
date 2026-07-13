from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import SearchBackendDep
from app.domain.enums import SortOrder
from app.domain.search import SearchQuery, SearchResponse

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Faceted search over metadata records",
)
async def search(
    backend: SearchBackendDep,
    q: Annotated[
        str | None,
        Query(description="Search title, description, and keywords"),
    ] = None,
    types: Annotated[
        list[str] | None,
        Query(description="Record type filters (repeat param for multiple values)"),
    ] = None,
    source: Annotated[
        list[str] | None,
        Query(description="Filter by datasource_id (repeat param for multiple values)"),
    ] = None,
    sort: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.RELEVANCE,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=50, description="Results per page")] = 20,
) -> SearchResponse:
    """Search records in the odis_metadata index with optional type and source filters."""
    query = SearchQuery(
        q=q,
        types=types or [],
        sources=source or [],
        sort=sort.value,
        page=page,
        size=size,
    )
    return await backend.search(query)
