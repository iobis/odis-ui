from fastapi import APIRouter

from app.dependencies import SearchBackendDep
from app.domain.search import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health(backend: SearchBackendDep) -> HealthStatus:
    """Check API and search index reachability."""
    return await backend.health()
