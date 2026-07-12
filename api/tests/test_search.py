import pytest
from httpx import AsyncClient

from tests.fakes import FakeSearchBackend


@pytest.mark.asyncio
async def test_search_returns_results(client: AsyncClient, fake_backend: FakeSearchBackend) -> None:
    response = await client.get("/api/v1/search", params={"q": "salinity", "page": 1, "size": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Dataset"
    assert data["page"] == 1
    assert data["size"] == 10
    assert fake_backend.last_query is not None
    assert fake_backend.last_query.q == "salinity"


@pytest.mark.asyncio
async def test_search_validates_size_max(client: AsyncClient) -> None:
    response = await client.get("/api/v1/search", params={"size": 100})
    assert response.status_code == 422
