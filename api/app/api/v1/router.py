from fastapi import APIRouter

from app.api.v1 import health, records, search

router = APIRouter()
router.include_router(health.router)
router.include_router(search.router)
router.include_router(records.router)
