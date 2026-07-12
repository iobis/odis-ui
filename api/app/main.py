from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.dependencies import lifespan

app = FastAPI(
    title="ODIS Search API",
    description="Read-only faceted search over ODIS metadata records",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")
