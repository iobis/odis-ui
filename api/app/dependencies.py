from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from app.config import Settings, settings
from app.search.base import SearchBackend
from app.search.factory import KNOWN_BACKENDS, create_all_backends


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    backends = create_all_backends(settings)
    default = settings.search_backend.lower()
    if default not in backends:
        default = KNOWN_BACKENDS[0]
    app.state.search_backends = backends
    app.state.default_backend = default
    # Keep legacy attribute for anything that still expects a single backend.
    app.state.search_backend = backends[default]
    yield
    for backend in backends.values():
        await backend.close()


def get_settings() -> Settings:
    return settings


def get_search_backend(
    request: Request,
    x_search_backend: Annotated[str | None, Header(alias="X-Search-Backend")] = None,
) -> SearchBackend:
    backends: dict[str, SearchBackend] = request.app.state.search_backends
    name = (x_search_backend or request.app.state.default_backend).lower()
    backend = backends.get(name)
    if backend is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown search backend '{name}'. Choose one of: {', '.join(backends)}",
        )
    return backend


SettingsDep = Annotated[Settings, Depends(get_settings)]
SearchBackendDep = Annotated[SearchBackend, Depends(get_search_backend)]
