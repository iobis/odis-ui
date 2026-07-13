from app.domain.search import SearchItem, SearchResponse, SourceFacetBucket, SourceRef
from app.search.elasticsearch.catalogue import CatalogueNames


def enrich_search_response(response: SearchResponse, catalogue: CatalogueNames) -> SearchResponse:
    sources = [
        SourceFacetBucket(
            id=bucket.id,
            name=catalogue.get(bucket.id),
            count=bucket.count,
        )
        for bucket in response.facets.sources
    ]

    items: list[SearchItem] = []
    for item in response.items:
        if item.source:
            item = item.model_copy(
                update={
                    "source": SourceRef(
                        id=item.source.id,
                        name=catalogue.get(item.source.id),
                    )
                }
            )
        items.append(item)

    return response.model_copy(
        update={
            "facets": response.facets.model_copy(update={"sources": sources}),
            "items": items,
        }
    )
