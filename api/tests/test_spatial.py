from app.domain.search import BoundingBox, GeoPoint, SpatialExtent
from app.search.elasticsearch.spatial import extract_spatial_extent

DECC_DATA = {
    "spatialCoverage": {
        "@type": {"value": "Place"},
        "geo": {
            "@type": {"value": "GeoShape"},
            "box": {"value": "51.3837 -4.8934 51.6061 -4.1717"},
        },
    }
}

UKHD_DATA = {
    "spatialCoverage": [
        {
            "@type": {"value": "Place"},
            "geo": [{"box": {"value": "51.59 -10.20 54.29 -6.04"}}],
        },
        {
            "@type": {"value": "Place"},
            "geo": [{"box": {"value": "53.725199 3.358332 55.916929 8.161185"}}],
        },
    ]
}

IOOS_GEOSHAPE_DATA = {
    "schema:box": {"value": "29.711433 -81.21843 29.711433 -81.21843"},
    "@type": {"value": "schema:GeoShape"},
}

MARINEREGIONS_DATA = {
    "box": {"value": "58.8445 19.0832 66.77516 27.8312"},
    "@type": {"value": "GeoShape"},
}

OBIS_POLYGON_DATA = {
    "spatialCoverage": {
        "@type": {"value": "Place"},
        "geo": {
            "@type": {"value": "GeoShape"},
            "polygon": {
                "value": (
                    "-9.533333 -24.5166666666667, -9.533333 147.266667, "
                    "63.7 147.266667, 63.7 -24.5166666666667, "
                    "-9.533333 -24.5166666666667"
                )
            },
        },
        "additionalProperty": {
            "@type": {"value": "PropertyValue"},
            "propertyID": {"value": "http://dbpedia.org/resource/Spatial_reference_system"},
            "value": {"value": "http://www.w3.org/2003/01/geo/wgs84_pos#lat_long"},
        },
    }
}


def test_extract_inline_dataset_box() -> None:
    extent = extract_spatial_extent({"data": DECC_DATA})
    assert extent is not None
    assert len(extent.boxes) == 1
    box = extent.boxes[0]
    assert box.south == 51.3837
    assert box.west == -4.8934
    assert box.north == 51.6061
    assert box.east == -4.1717
    assert extent.points == []


def test_extract_array_spatial_coverage() -> None:
    extent = extract_spatial_extent({"data": UKHD_DATA})
    assert extent is not None
    assert len(extent.boxes) == 2
    assert extent.boxes[0].north == 54.29
    assert extent.boxes[1].east == 8.161185


def test_extract_point_from_degenerate_box() -> None:
    extent = extract_spatial_extent({"data": IOOS_GEOSHAPE_DATA})
    assert extent is not None
    assert extent.boxes == []
    assert len(extent.points) == 1
    assert extent.points[0] == GeoPoint(lat=29.711433, lon=-81.21843)


def test_extract_direct_geoshape_box() -> None:
    extent = extract_spatial_extent({"data": MARINEREGIONS_DATA})
    assert extent is not None
    assert extent.boxes[0] == BoundingBox(
        south=58.8445, west=19.0832, north=66.77516, east=27.8312
    )


def test_extract_ignores_invalid_and_duplicate_boxes() -> None:
    extent = extract_spatial_extent(
        {
            "data": {
                "spatialCoverage": {
                    "geo": {
                        "box": {"value": "not-a-box"},
                    }
                },
                "box": {"value": "1 2 3 4"},
            }
        }
    )
    assert extent is not None
    assert len(extent.boxes) == 1
    assert extent.boxes[0].south == 1.0


def test_extract_obis_polygon_as_bounding_box() -> None:
    extent = extract_spatial_extent({"data": OBIS_POLYGON_DATA})
    assert extent is not None
    assert len(extent.boxes) == 1
    box = extent.boxes[0]
    assert box.south == -9.533333
    assert box.west == -24.5166666666667
    assert box.north == 63.7
    assert box.east == 147.266667
    assert extent.points == []


def test_extract_returns_none_without_data() -> None:
    assert extract_spatial_extent({}) is None
    assert extract_spatial_extent({"data": {"name": {"value": "No extent"}}}) is None
