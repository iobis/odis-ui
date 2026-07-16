import pytest
from httpx import AsyncClient

from tests.fakes import FakeSearchBackend


@pytest.mark.asyncio
async def test_list_backends(client: AsyncClient, fake_backend: FakeSearchBackend) -> None:
    response = await client.get("/api/v1/backends")
    assert response.status_code == 200
    payload = response.json()
    assert payload["default"] == "elasticsearch"
    assert len(payload["backends"]) == 2
    ids = {item["id"] for item in payload["backends"]}
    assert ids == {"elasticsearch", "gleaner"}
    assert all(item["health"]["status"] == "ok" for item in payload["backends"])


@pytest.mark.asyncio
async def test_search_respects_backend_header(
    client: AsyncClient, fake_backend: FakeSearchBackend
) -> None:
    response = await client.get(
        "/api/v1/search",
        headers={"X-Search-Backend": "gleaner"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_unknown_backend_header_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/search",
        headers={"X-Search-Backend": "nope"},
    )
    assert response.status_code == 400
