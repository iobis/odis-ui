from elasticsearch import AsyncElasticsearch, NotFoundError

from app.config import Settings
from app.domain.errors import RecordNotFoundError
from app.domain.search import HealthStatus, RecordResponse, SearchQuery, SearchResponse
from app.search.elasticsearch.urls import elasticsearch_document_url
from app.search.gleaner.ids import DEFAULT_INDICES, decode_record_id, index_for_source
from app.search.gleaner.queries import build_search_body, map_document_to_item, map_search_response


def create_gleaner_client(settings: Settings) -> AsyncElasticsearch:
    kwargs: dict = {"hosts": [settings.gleaner_elasticsearch_url]}
    if settings.gleaner_elasticsearch_user:
        kwargs["basic_auth"] = (
            settings.gleaner_elasticsearch_user,
            settings.gleaner_elasticsearch_password,
        )
    return AsyncElasticsearch(**kwargs)


class GleanerBackend:
    """Search backend for the Gleaner multi-index cluster (one index per source)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = create_gleaner_client(settings)
        indices = [part.strip() for part in settings.gleaner_indices.split(",") if part.strip()]
        self._indices = tuple(indices) if indices else DEFAULT_INDICES

    @property
    def indices(self) -> tuple[str, ...]:
        return self._indices

    def _document_url(self, index: str, record_id: str) -> str:
        return elasticsearch_document_url(
            self._settings.gleaner_elasticsearch_url,
            index,
            record_id,
        )

    def _index_list(self, query: SearchQuery) -> str:
        if not query.sources:
            return ",".join(self._indices)
        selected = [index_for_source(source) for source in query.sources]
        selected = [index for index in selected if index in self._indices]
        return ",".join(selected) if selected else ",".join(self._indices)

    async def search(self, query: SearchQuery) -> SearchResponse:
        body = build_search_body(query)
        raw = await self._client.search(index=self._index_list(query), body=body)
        payload = raw.body if hasattr(raw, "body") else raw
        return map_search_response(query, payload, document_url_for=self._document_url)

    async def get_record(self, record_id: str, *, include_raw: bool = False) -> RecordResponse:
        decoded = decode_record_id(record_id)
        if decoded is None:
            raise RecordNotFoundError(record_id)
        source_code, doc_id = decoded
        index = index_for_source(source_code)
        try:
            doc = await self._client.get(index=index, id=doc_id)
        except NotFoundError as exc:
            raise RecordNotFoundError(record_id) from exc

        payload = doc.body if hasattr(doc, "body") else doc
        source = payload.get("_source", {})
        es_id = payload.get("_id", doc_id)
        item = map_document_to_item(
            es_id,
            source,
            index=index,
            elasticsearch_document_url=self._document_url(index, es_id),
        )
        return RecordResponse(**item.model_dump(), raw=source if include_raw else None)

    async def health(self) -> HealthStatus:
        reachable = False
        detail: str | None = None
        try:
            # Probe first configured index; cluster may still be up if one index is missing.
            exists = await self._client.indices.exists(index=self._indices[0])
            reachable = bool(exists)
            if not reachable:
                detail = f"Index '{self._indices[0]}' not found"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"

        return HealthStatus(
            status="ok" if reachable else "degraded",
            backend="gleaner",
            index=",".join(self._indices),
            index_reachable=reachable,
            detail=detail,
        )

    async def close(self) -> None:
        await self._client.close()
