# Spatial coverage & bounding box analysis

> Generated 2026-07-13 by querying the live `odis_metadata` and `catalogue` Elasticsearch indices.

## Executive summary

Bounding boxes **exist** in the ODIS metadata corpus, but they are **not normalized to a single field** and are **not indexed for geo search**. Coordinates live almost exclusively inside the stored `data` JSON-LD blob, not at the root fields that the mapping defines (`spatialCoverage`, `geo`, etc.).

| Finding | Detail |
|---------|--------|
| Primary bbox format | schema.org **GeoShape box** string: `"south west north east"` (WGS84 degrees) |
| Main dataset path | `data.spatialCoverage → Place → geo → GeoShape → box` |
| Fragment path | Separate `schema:GeoShape` / `GeoShape` documents with `data.schema:box` or `data.box` |
| Root-level spatial fields | Mapped as `flattened`, **0 documents populated** in samples |
| Datasets with bbox (sample) | **~66%** of 5,000 `Dataset` / `schema:Dataset` docs |
| Multi-extent datasets | **~28%** of bbox-bearing datasets have more than one box |
| Geo query ready | **No** — requires extraction + reindex as `geo_shape` / `geo_point` |

---

## 1. Where spatial data lives

### 1.1 Root-level fields (indexed mapping, unused)

The index mapping defines these spatial-related root fields, all as **`flattened`** (not `geo_point` / `geo_shape`):

| Field | ES type |
|-------|---------|
| `spatialCoverage` | flattened |
| `schema:spatialCoverage` | flattened |
| `geo` | flattened |
| `schema:geo` | flattened |
| `location` | flattened |
| `schema:location` | flattened |

**Population:** `exists` queries on all of the above return **0 hits** across the full index. The harvester does not promote spatial values to these root fields.

### 1.2 The `data` blob (where values actually are)

The full JSON-LD graph is stored under `data`. Most subfields are `enabled: false` (stored for retrieval, not searchable). Spatial extraction must read `data` at query time or during a reindex pipeline.

---

## 2. Bounding box field paths

Schema.org encodes a rectangle as a single string on `GeoShape.box` (or `schema:box`):  
**`"southLat westLon northLat eastLon"`**

### 2.1 Path catalog

| Normalized path | Typical `@type` | Approx. prevalence | Notes |
|-----------------|-----------------|--------------------|-------|
| `data.spatialCoverage.geo.box` | `Dataset` | Common (e.g. datasource **40** — UK DECC) | Single Place, inline GeoShape; user's example pattern |
| `data.spatialCoverage.geo.box.value` | `Dataset` | Same as above | Wrapped `{ "value": "…" }` form |
| `data.spatialCoverage[].geo[].box` | `schema:Dataset` | Common (e.g. datasource **364** — UKHD) | **Array** of Places; up to 200+ extents on one record |
| `data.spatialCoverage[].geo.box` | `Dataset` | Occasional (e.g. ds **3267**) | Array Place, singular `geo` object |
| `data.schema:box` | `schema:GeoShape` | **107,594** fragment docs | Standalone graph node; often referenced by `@id` |
| `data.box` | `GeoShape` | **27** fragment docs | Unprefixed variant |

No significant use was found in a 300-document sample of: `polygon`, `circle`, `coordinates`, `westBoundingLongitude`, WKT, or GML geometry fields on datasets.

### 2.2 Example — inline on Dataset (datasource 40)

Record: `d949f4c4f826ef4bc9e05612a6bff730` (UK DECC survey — matches user example)

```json
"spatialCoverage": {
  "@type": { "value": "Place" },
  "geo": {
    "@type": { "value": "GeoShape" },
    "box": { "value": "54.0491 -3.7115 54.0643 -3.6885" }
  },
  "name": [ { "@type": "DefinedTerm", "name": "Irish Sea", … } ],
  "additionalProperty": [
    { "propertyID": "http://www.opengis.net/def/crs/EPSG/0/4230", … }
  ]
}
```

CRS may be declared separately (here EPSG:4230 on the Place, not inside the box string).

### 2.3 Example — graph fragment GeoShape (datasource 3308, IOOS)

Separate indexed document, `@type: schema:GeoShape`:

```json
"data": {
  "schema:box": { "value": "29.711433 -81.21843 29.711433 -81.21843" },
  "@type": { "value": "schema:GeoShape" },
  "@id": { "value": "_:N3d834136edfb466fb5e2168bc44c0c53" }
}
```

### 2.4 Example — graph fragment GeoShape (datasource 3305)

`@type: GeoShape` with unprefixed `box`:

```json
"data": {
  "box": { "value": "58.8445 19.0832 66.77516 27.8312" },
  "@type": { "value": "GeoShape" },
  "name": { "value": "Finnish EEZ Bounding Box" }
}
```

### 2.5 Place fragments (107,630 docs) — indirection, not coordinates

`schema:Place` documents typically **do not** embed a box. They point at a sibling GeoShape:

```json
"data": {
  "@type": { "value": "schema:Place" },
  "schema:geo": { "@id": { "value": "_:N3d834136edfb466fb5e2168bc44c0c53" } }
}
```

The coordinates live on the referenced `schema:GeoShape` document. Resolving extent for a dataset may require **joining graph nodes** by `@id`, not reading a single document.

---

## 3. Structural variation

### 3.1 `spatialCoverage` cardinality

In a 1,000-dataset sample, every spatial field used the key **`spatialCoverage`** (not `schema:spatialCoverage`) inside `data`.

| Structure | Count (of 1,000) |
|-----------|------------------|
| Single object, `geo` object | 501 |
| Array of 1 Place | 287 |
| Array of 2–5 Places | 124 |
| Array of 6+ Places | 88 |
| Largest seen | **216** Places on one dataset (ds 364) |

When `spatialCoverage` is an array, bbox paths use numeric indices:  
`spatialCoverage[0].geo[0].box`, `spatialCoverage[1].geo[0].box`, …

### 3.2 Prefix conventions

| Context | Property style |
|---------|----------------|
| Dataset spatial extent | `spatialCoverage`, `geo`, `box` (often **unprefixed**) |
| Standalone GeoShape fragments | `schema:box` (**prefixed**) or `box` |
| Place → geo link | `schema:geo` with `@id` reference |

The same logical property appears with and without the `schema:` prefix depending on source and entity role in the graph.

### 3.3 Value wrapping

Coordinates appear as either:

- Bare string: `"box": "51.38 -4.89 51.60 -4.17"`
- Wrapped: `"box": { "value": "51.38 -4.89 51.60 -4.17" }`

Both forms are common; extraction logic must handle either.

---

## 4. Document counts

| `@type` | Documents | Role |
|---------|-----------|------|
| `schema:Dataset` | 57,808 | Harvested datasets (schema prefix) |
| `Dataset` | 36,460 | Harvested datasets |
| **Combined datasets** | **94,268** | Primary search targets |
| `schema:GeoShape` | 107,594 | Bbox graph fragments |
| `schema:Place` | 107,630 | Place graph fragments (usually geo by reference) |
| `GeoShape` | 27 | Unprefixed bbox fragments |
| `Place` | 35 | Unprefixed place fragments |

There are roughly as many Place / GeoShape fragments as harvested graph edges — consistent with **one JSON-LD page producing multiple indexed entities**.

---

## 5. Coverage by datasource

Bounding-box presence is **highly source-dependent**. From a 5,000-dataset scroll sample:

| `datasource_id` | Datasets sampled | With bbox | Rate |
|-----------------|------------------|-----------|------|
| 364 (UKHD) | 1,931 | 1,928 | ~100% |
| 40 (UK DECC) | 773 | 773 | ~100% |
| 3300 | 198 | 198 | ~100% |
| 3267 | 245 | 201 | ~82% |
| 3303 | 158 | 156 | ~99% |
| 29 | 743 | 1 | ~0% |
| 3305 | 334 | 0 | 0% |
| 3308 (IOOS) | 94 | 0 | 0%* |

\*IOOS datasets often reference **separate** `schema:GeoShape` fragments (`schema:box` on another document) rather than inline `spatialCoverage` on the Dataset record. Bbox exists in the index but not on the Dataset `data` path.

**Overall sample:** 3,307 / 5,000 datasets (**66.1%**) contained at least one parseable box string in `data`.

---

## 6. Catalogue index (system-level spatial text)

The `catalogue` index (registered data systems, not harvested records) has:

| Field | Documents | Content |
|-------|-----------|---------|
| `mdSpatialCoverage` | 264 | **Free-text** place names (e.g. `"Bay of Plenty"`) |
| `mdBoundingBox` | 0 | Unused |

This is prose extent metadata for **catalogue entries**, not machine-readable bounding boxes for records.

---

## 7. Implications for search & UI

### 7.1 Displaying extent on result cards

To show a bbox on a dataset card today:

1. Fetch raw record (`?raw=1` or include `data` in `_source`).
2. Walk `data` for box strings using the paths in §2.1.
3. Handle arrays (`spatialCoverage[]`) — UI may need multi-extent or envelope union.
4. Optionally resolve `schema:Place` → `schema:GeoShape` via `@id` when only a reference exists.

### 7.2 Suggested extraction priority

```
1. data.spatialCoverage[].geo[].box[.value]
2. data.spatialCoverage.geo.box[.value]
3. data.spatialCoverage[].geo.box[.value]
4. Follow schema:geo.@id → sibling schema:GeoShape document → data.schema:box
5. data.box[.value] on GeoShape documents
```

### 7.3 Indexing for spatial search (future)

To support `?bbox=w,s,e,n` or map clustering:

1. **Normalize** all paths to a single field, e.g. `extent_bbox` (`geo_shape`) and optionally `extent_centroid` (`geo_point`).
2. **Promote** from `data` at harvest time (preferred) or with an ingest pipeline.
3. **Collapse** multi-place datasets to an envelope (min/max) or store as `geo_shape` multipolygon.
4. **Link** Place → GeoShape fragments when datasets only hold references.

Root `flattened` fields are unsuitable for geo queries; a reindex is required.

---

## 8. Validation notes

- Box strings were validated with pattern: `south west north east` (four floats).
- **Point boxes** occur (identical south/north and west/east): e.g. `"29.711433 -81.21843 29.711433 -81.21843"`.
- CRS is sometimes declared on the Place (`additionalProperty` / EPSG URI) but the box string itself does not encode CRS.
- Assume WGS84 unless CRS metadata is present and a transform is applied.

---

## 9. Related documents

- [data-sources-analysis.md §6](./data-sources-analysis.md#6-spatial-data-capabilities) — earlier spatial capability summary
- [record-type-field-population.md](./record-type-field-population.md) — GeoShape / Place fragment volumes
- [faceted-search-plan.md §7](./faceted-search-plan.md#7-spatial-search) — deferred spatial API design
