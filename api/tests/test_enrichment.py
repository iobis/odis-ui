from app.domain.search import (
    FacetBucket,
    SearchFacets,
    SearchItem,
    SearchResponse,
    SourceFacetBucket,
    SourceRef,
)
from app.search.elasticsearch.catalogue import CatalogueNames
from app.search.elasticsearch.enrichment import enrich_search_response


def test_enrich_search_response_adds_catalogue_names() -> None:
    catalogue = CatalogueNames()
    catalogue._names = {"3308": "IOOS Data Catalog"}
    catalogue._loaded = True

    response = SearchResponse(
        total=1,
        facets=SearchFacets(
            types=[FacetBucket(value="dataset", count=1)],
            sources=[SourceFacetBucket(id="3308", count=10)],
        ),
        items=[
            SearchItem(
                id="abc",
                title="Test",
                type="Dataset",
                source=SourceRef(id="3308"),
            )
        ],
        page=1,
        size=20,
    )

    enriched = enrich_search_response(response, catalogue)
    assert enriched.facets.sources[0].name == "IOOS Data Catalog"
    assert enriched.items[0].source is not None
    assert enriched.items[0].source.name == "IOOS Data Catalog"
