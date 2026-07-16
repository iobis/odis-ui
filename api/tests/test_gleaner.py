from app.domain.search import SearchQuery
from app.search.gleaner.ids import decode_record_id, encode_record_id
from app.search.gleaner.queries import build_search_body, map_document_to_item


def test_encode_decode_roundtrip() -> None:
    encoded = encode_record_id("obis", "https://obis.org/dataset/abc")
    assert encoded.startswith("gleaner:obis:")
    assert decode_record_id(encoded) == ("obis", "https://obis.org/dataset/abc")


def test_map_gleaner_dataset() -> None:
    item = map_document_to_item(
        "https://obis.org/dataset/abc",
        {
            "source": "obis",
            "id": "https://obis.org/dataset/abc",
            "type": ["Dataset"],
            "name": "Turtle tracks",
            "description": "Telemetry summary",
            "url": "https://obis.org/dataset/abc",
            "keywords": ["Occurrence"],
        },
        index="gleaner-obis",
    )
    assert item.id.startswith("gleaner:obis:")
    assert item.type == "Dataset"
    assert item.title == "Turtle tracks"
    assert item.source is not None
    assert item.source.id == "obis"
    assert item.source.name is not None
    assert "Biodiversity" in item.source.name


def test_map_gleaner_person_with_geo() -> None:
    item = map_document_to_item(
        "https://oceanexpert.org/expert/1",
        {
            "source": "oe",
            "id": "https://oceanexpert.org/expert/1",
            "type": ["Person"],
            "name": "Ada Lovelace",
            "description": None,
            "url": None,
            "source_url": "https://oceanexpert.org/expert/1",
            "jsonld": {
                "workLocation": {
                    "geo": {"latitude": -14.2, "longitude": -51.9},
                }
            },
        },
        index="gleaner-oe",
    )
    assert item.type == "Person"
    assert item.url == "https://oceanexpert.org/expert/1"
    assert item.spatial is not None
    assert item.spatial.points[0].lat == -14.2


def test_gleaner_search_body_filters_and_aggs() -> None:
    body = build_search_body(SearchQuery(q="coral", types=["dataset"], sources=["obis"]))
    assert body["post_filter"]["bool"]["filter"]
    assert "types" in body["aggs"]
    assert "sources" in body["aggs"]
    assert body["query"]["bool"]["must"][0]["multi_match"]["query"] == "coral"
