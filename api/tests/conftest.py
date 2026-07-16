from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fakes import FakeSearchBackend


@pytest.fixture
def fake_backend() -> FakeSearchBackend:
    return FakeSearchBackend()


@pytest.fixture
async def client(fake_backend: FakeSearchBackend) -> AsyncIterator[AsyncClient]:
    app.state.search_backends = {
        "elasticsearch": fake_backend,
        "gleaner": fake_backend,
    }
    app.state.default_backend = "elasticsearch"
    app.state.search_backend = fake_backend
    app.dependency_overrides.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    for key in ("search_backends", "default_backend", "search_backend"):
        if hasattr(app.state, key):
            delattr(app.state, key)
