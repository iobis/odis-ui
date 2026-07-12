from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_search_backend
from app.main import app
from tests.fakes import FakeSearchBackend


@pytest.fixture
def fake_backend() -> FakeSearchBackend:
    return FakeSearchBackend()


@pytest.fixture
async def client(fake_backend: FakeSearchBackend) -> AsyncIterator[AsyncClient]:
    @asynccontextmanager
    async def test_lifespan(app_instance):
        app_instance.state.search_backend = fake_backend
        yield

    app.router.lifespan_context = test_lifespan
    app.dependency_overrides[get_search_backend] = lambda: fake_backend

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
