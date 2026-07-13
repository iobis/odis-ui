from elasticsearch import AsyncElasticsearch


class CatalogueNames:
    def __init__(self) -> None:
        self._names: dict[str, str] = {}
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    async def load(self, client: AsyncElasticsearch, index: str) -> None:
        if self._loaded:
            return

        response = await client.search(
            index=index,
            body={
                "size": 5000,
                "query": {"match_all": {}},
                "_source": ["dsNameEnglish", "dsAcronym"],
            },
        )
        payload = response.body if hasattr(response, "body") else response
        for hit in payload.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            name = source.get("dsNameEnglish") or source.get("dsAcronym")
            if name:
                self._names[hit["_id"]] = name

        self._loaded = True

    def get(self, datasource_id: str) -> str | None:
        return self._names.get(datasource_id)
