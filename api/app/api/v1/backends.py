import asyncio

from fastapi import APIRouter, Request

from app.domain.search import BackendInfo, BackendsResponse, HealthStatus
from app.search.base import SearchBackend
from app.search.labels import backend_label

router = APIRouter(tags=["backends"])


@router.get(
    "/backends",
    response_model=BackendsResponse,
    summary="List search backends and their health",
)
async def list_backends(request: Request) -> BackendsResponse:
    """Return every configured backend with a live health probe."""
    backends: dict[str, SearchBackend] = request.app.state.search_backends
    default: str = request.app.state.default_backend

    async def probe(backend_id: str, backend: SearchBackend) -> BackendInfo:
        try:
            health = await backend.health()
        except Exception as exc:
            health = HealthStatus(
                status="degraded",
                backend=backend_id,
                index="",
                index_reachable=False,
                detail=f"{type(exc).__name__}: {exc}",
            )
        return BackendInfo(id=backend_id, label=backend_label(backend_id), health=health)

    results = await asyncio.gather(
        *(probe(backend_id, backend) for backend_id, backend in backends.items())
    )
    # Stable order matching registration.
    order = list(backends.keys())
    by_id = {item.id: item for item in results}
    return BackendsResponse(
        default=default,
        backends=[by_id[backend_id] for backend_id in order if backend_id in by_id],
    )
