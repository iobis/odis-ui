from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from app.dependencies import SearchBackendDep
from app.domain.errors import RecordNotFoundError
from app.domain.search import RecordResponse
from app.search.base import SearchBackend

router = APIRouter(tags=["records"])

_GLEANER_ID_PREFIX = "gleaner:"


def _backend_for_record(request: Request, record_id: str, fallback: SearchBackend) -> SearchBackend:
    """Route namespaced ids to their owning backend (links cannot send X-Search-Backend)."""
    backends: dict[str, SearchBackend] = request.app.state.search_backends
    if record_id.startswith(_GLEANER_ID_PREFIX) and "gleaner" in backends:
        return backends["gleaner"]
    return fallback


@router.get(
    "/records/{record_id}",
    response_model=RecordResponse,
    summary="Get a metadata record by ID",
)
async def get_record(
    record_id: str,
    request: Request,
    backend: SearchBackendDep,
    raw: Annotated[
        bool,
        Query(description="Include the full stored document in the response"),
    ] = False,
) -> RecordResponse:
    resolved = _backend_for_record(request, record_id, backend)
    try:
        return await resolved.get_record(record_id, include_raw=raw)
    except RecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Record not found: {exc.record_id}") from exc
