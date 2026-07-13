from elasticsearch import NotFoundError

from app.config import Settings
from app.domain.errors import RecordNotFoundError
from app.domain.search import HealthStatus, RecordResponse, SearchQuery, SearchResponse
from app.search.elasticsearch.client import create_client
from app.search.elasticsearch.queries import build_search_body, map_document_to_item, map_search_response
from app.search.elasticsearch.urls import elasticsearch_document_url


class ElasticsearchBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = create_client(settings)

    @property
    def index(self) -> str:
        return self._settings.es_index

    def _document_url(self, record_id: str) -> str:
        return elasticsearch_document_url(
            self._settings.elasticsearch_url,
            self.index,
            record_id,
        )

    async def search(self, query: SearchQuery) -> SearchResponse:
        body = build_search_body(query)
        body["fields"] = ["record_type"]
        raw = await self._client.search(index=self.index, body=body)
        payload = raw.body if hasattr(raw, "body") else raw
        return map_search_response(query, payload, document_url_for=self._document_url)

    async def get_record(self, record_id: str, *, include_raw: bool = False) -> RecordResponse:
        try:
            source_excludes = None if include_raw else ["data"]
            doc = await self._client.get(index=self.index, id=record_id, source_excludes=source_excludes)
        except NotFoundError as exc:
            raise RecordNotFoundError(record_id) from exc

        payload = doc.body if hasattr(doc, "body") else doc
        source = payload.get("_source", {})
        record_id = payload.get("_id", record_id)
        item = map_document_to_item(
            record_id,
            source,
            elasticsearch_document_url=self._document_url(record_id),
        )
        return RecordResponse(**item.model_dump(), raw=source if include_raw else None)

    async def health(self) -> HealthStatus:
        index_reachable = False
        detail: str | None = None
        try:
            exists = await self._client.indices.exists(index=self.index)
            index_reachable = bool(exists)
            if not index_reachable:
                detail = f"Index '{self.index}' not found"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"

        status = "ok" if index_reachable else "degraded"
        return HealthStatus(
            status=status,
            backend="elasticsearch",
            index=self.index,
            index_reachable=index_reachable,
            detail=detail,
        )

    async def close(self) -> None:
        await self._client.close()
