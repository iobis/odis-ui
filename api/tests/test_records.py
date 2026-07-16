import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.search import SearchItem, SearchResponse, SourceRef
from app.main import app
from tests.fakes import FakeSearchBackend


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


@pytest.mark.asyncio
async def test_gleaner_record_id_routes_without_backend_header() -> None:
    """Browser 'API record' links omit X-Search-Backend; route by id prefix."""
    elasticsearch = FakeSearchBackend()
    gleaner = FakeSearchBackend()
    gleaner_id = "gleaner:obis:abc"
    gleaner.search_response = SearchResponse(
        total=1,
        facets=elasticsearch.search_response.facets,
        items=[
            SearchItem(
                id=gleaner_id,
                title="Gleaner Dataset",
                summary=None,
                type="Dataset",
                url="https://obis.org/dataset/abc",
                source=SourceRef(id="obis", name="OBIS"),
            )
        ],
        page=1,
        size=20,
    )
    app.state.search_backends = {"elasticsearch": elasticsearch, "gleaner": gleaner}
    app.state.default_backend = "elasticsearch"
    app.state.search_backend = elasticsearch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/records/{gleaner_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Gleaner Dataset"
