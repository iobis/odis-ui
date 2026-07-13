from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import SearchBackendDep
from app.domain.errors import RecordNotFoundError
from app.domain.search import RecordResponse

router = APIRouter(tags=["records"])


@router.get(
    "/records/{record_id}",
    response_model=RecordResponse,
    summary="Get a metadata record by ID",
)
async def get_record(
    record_id: str,
    backend: SearchBackendDep,
    raw: Annotated[
        bool,
        Query(description="Include the full stored document in the response"),
    ] = False,
) -> RecordResponse:
    try:
        return await backend.get_record(record_id, include_raw=raw)
    except RecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Record not found: {exc.record_id}") from exc
