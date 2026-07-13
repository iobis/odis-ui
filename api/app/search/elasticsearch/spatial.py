"""Extract bounding boxes and points from ODIS JSON-LD `data` blobs."""

from __future__ import annotations

import re
from typing import Any

from app.domain.search import BoundingBox, GeoPoint, SpatialExtent

BOX_PATTERN = re.compile(
    r"^(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)$"
)
COORD_PAIR_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")

SPATIAL_COVERAGE_KEYS = ("spatialCoverage", "schema:spatialCoverage")
GEO_KEYS = ("geo", "schema:geo")
BOX_KEYS = ("box", "schema:box")
POLYGON_KEYS = ("polygon", "schema:polygon")


def _unwrap(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def _parse_box_string(raw: str) -> tuple[float, float, float, float] | None:
    match = BOX_PATTERN.match(raw.strip())
    if not match:
        return None
    south, west, north, east = (float(part) for part in match.groups())
    if south > north:
        return None
    return south, west, north, east


def _parse_polygon_string(raw: str) -> tuple[float, float, float, float] | None:
    """Parse schema.org GeoShape polygon into an axis-aligned bounding box."""
    pairs = COORD_PAIR_PATTERN.findall(raw.strip())
    if len(pairs) < 2:
        return None

    lats: list[float] = []
    lons: list[float] = []
    for lat_raw, lon_raw in pairs:
        lat = float(lat_raw)
        lon = float(lon_raw)
        if abs(lat) > 90 or abs(lon) > 180:
            return None
        lats.append(lat)
        lons.append(lon)

    return min(lats), min(lons), max(lats), max(lons)


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _append_box(
    boxes: list[tuple[float, float, float, float]],
    seen: set[tuple[float, float, float, float]],
    parsed: tuple[float, float, float, float] | None,
) -> None:
    if parsed is None or parsed in seen:
        return
    seen.add(parsed)
    boxes.append(parsed)


def _append_box_string(
    boxes: list[tuple[float, float, float, float]],
    seen: set[tuple[float, float, float, float]],
    raw: str,
) -> None:
    _append_box(boxes, seen, _parse_box_string(raw))


def _append_polygon_string(
    boxes: list[tuple[float, float, float, float]],
    seen: set[tuple[float, float, float, float]],
    raw: str,
) -> None:
    _append_box(boxes, seen, _parse_polygon_string(raw))


def _collect_from_geo(boxes: list[tuple[float, float, float, float]], seen: set, geo: Any) -> None:
    for geo_obj in _as_dict_list(geo):
        for box_key in BOX_KEYS:
            raw = _unwrap(geo_obj.get(box_key))
            if isinstance(raw, str):
                _append_box_string(boxes, seen, raw)
        for polygon_key in POLYGON_KEYS:
            raw = _unwrap(geo_obj.get(polygon_key))
            if isinstance(raw, str):
                _append_polygon_string(boxes, seen, raw)


def _collect_from_spatial_coverage(
    boxes: list[tuple[float, float, float, float]],
    seen: set,
    data: dict[str, Any],
) -> None:
    for coverage_key in SPATIAL_COVERAGE_KEYS:
        for place in _as_dict_list(data.get(coverage_key)):
            for geo_key in GEO_KEYS:
                if geo_key in place:
                    _collect_from_geo(boxes, seen, place.get(geo_key))


def _collect_direct_boxes(
    boxes: list[tuple[float, float, float, float]],
    seen: set,
    data: dict[str, Any],
) -> None:
    for box_key in BOX_KEYS:
        raw = _unwrap(data.get(box_key))
        if isinstance(raw, str):
            _append_box_string(boxes, seen, raw)
    for polygon_key in POLYGON_KEYS:
        raw = _unwrap(data.get(polygon_key))
        if isinstance(raw, str):
            _append_polygon_string(boxes, seen, raw)


def _to_extent(boxes: list[tuple[float, float, float, float]]) -> SpatialExtent | None:
    extent_boxes: list[BoundingBox] = []
    extent_points: list[GeoPoint] = []

    for south, west, north, east in boxes:
        if south == north and west == east:
            extent_points.append(GeoPoint(lat=south, lon=west))
        else:
            extent_boxes.append(
                BoundingBox(south=south, west=west, north=north, east=east)
            )

    if not extent_boxes and not extent_points:
        return None
    return SpatialExtent(boxes=extent_boxes, points=extent_points)


def extract_spatial_extent(source: dict[str, Any]) -> SpatialExtent | None:
    """Return boxes and degenerate-box points found in a record source."""
    data = source.get("data")
    if not isinstance(data, dict):
        return None

    boxes: list[tuple[float, float, float, float]] = []
    seen: set[tuple[float, float, float, float]] = set()

    _collect_direct_boxes(boxes, seen, data)
    _collect_from_spatial_coverage(boxes, seen, data)

    return _to_extent(boxes)
