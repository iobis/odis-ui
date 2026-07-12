import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_openapi_json(client: AsyncClient) -> None:
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "ODIS Search API"
    assert "/api/v1/search" in spec["paths"]
    assert "/api/v1/health" in spec["paths"]
