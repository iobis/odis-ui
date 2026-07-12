from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from app.config import Settings, settings
from app.search.base import SearchBackend
from app.search.factory import create_search_backend


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    backend = create_search_backend(settings)
    app.state.search_backend = backend
    yield
    await backend.close()


def get_settings() -> Settings:
    return settings


def get_search_backend(request: Request) -> SearchBackend:
    return request.app.state.search_backend


SettingsDep = Annotated[Settings, Depends(get_settings)]
SearchBackendDep = Annotated[SearchBackend, Depends(get_search_backend)]
