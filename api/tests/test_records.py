import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_record_returns_item(client: AsyncClient) -> None:
    response = await client.get("/api/v1/records/test-id")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-id"
    assert data["title"] == "Test Dataset"
    assert data["raw"] is None


@pytest.mark.asyncio
async def test_get_record_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/records/missing-id")
    assert response.status_code == 404
