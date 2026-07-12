# Record type field population report

**Date:** 2026-07-12  
**Index:** `odis_metadata`  
**Related:** [Data sources analysis](./data-sources-analysis.md)

This report measures which **candidate search fields** are populated per record type, to guide full-text search, faceting, and result-card design. Types are ordered by **search relevance** (highest first), then by document count.

---

## Executive summary

### Best fields to target in search (primary types)

For the **high-relevance types** used in default search (`dataset`, `creativework`, `person`, `organization`, plus medium types `event`, `researchproject`), these root-level fields are consistently useful:

| Search role | ES fields | Coverage on primary types |
|-------------|-----------|---------------------------|
| **Title** (boost highest) | `name`, `schema:name` | 99–100% |
| **Body text** | `description`, `schema:description` | 0–99% (varies by type; see table) |
| **Subject terms** (boost medium) | `keywords`, `schema:keywords` | 0–99% (varies by type) |
| **Filter / facet** | `datasource_id` | 100% |
| **Link** | `url` | 100% |

**Recommended `multi_match` fields** (current API):

```
name^3, schema:name^3, description, schema:description, keywords^2, schema:keywords^2
```

### Fields **not** useful at root level

| Field | Finding |
|-------|---------|
| `author`, `creator`, `publisher` | **0% populated** at root on all types (stored as flattened relation objects, not indexed for text search) |
| `data` | Present on many docs but **not indexed** — only for detail views |

### Key caveats

1. **Type filter is essential.** Low-relevance graph fragments (`datadownload`, `place`, `geoshape`, `contactpoint`) dominate by volume but often lack meaningful titles despite a `name` field being present.
2. **`@type` variants are merged** in this report (`Dataset` + `schema:Dataset` → `dataset`).
3. **Person** records have titles (names) but essentially **no description or keywords** at root.
4. **CreativeWork** has titles on 100% of docs but description/keywords on only ~40%.

---

## Methodology

- **Source:** live Elasticsearch aggregation on `odis_metadata` (930,223 documents at time of run).
- **Type normalisation:** `@type.keyword` values merged after lowercasing and stripping `schema:` / URI prefixes (same logic as search faceting).
- **Field presence:** a field counts as populated if **either** plain or `schema:` variant exists (e.g. `name` OR `schema:name`).
- **Script:** [`api/scripts/field_population_report.py`](../api/scripts/field_population_report.py) — re-run with:

  ```bash
  docker compose exec api sh -c 'cd /app && PYTHONPATH=/app python scripts/field_population_report.py'
  ```

---

## Field population by record type

Percentages show the share of documents **of that type** with the field populated.

### High relevance

| Type | Raw `@type` values | Docs | Relevance | Title | Description | Keywords | URL | Source ID |
|------|-------------------|-----:|-----------|------:|------------:|---------:|----:|----------:|
| **dataset** | `Dataset`, `schema:Dataset` | 94,268 | High | 99.5% | 99.0% | 99.0% | 100% | 100% |
| **creativework** | `CreativeWork`, `schema:CreativeWork` | 92,714 | High | 100% | 42.3% | 40.3% | 100% | 100% |
| **person** | `Person` | 39,520 | High | 99.8% | 0% | 0% | 100% | 100% |
| **organization** | `Organization`, `schema:Organization` | 15,473 | High | 100% | 25.1% | 0% | 100% | 100% |

### Medium relevance

| Type | Raw `@type` values | Docs | Relevance | Title | Description | Keywords | URL | Source ID |
|------|-------------------|-----:|-----------|------:|------------:|---------:|----:|----------:|
| **datacatalog** | `DataCatalog`, `schema:DataCatalog` | 56,378 | Medium | 100% | 100% | 4.5% | 100% | 100% |
| **event** | `Event` | 4,080 | Medium | 100% | 64.1% | 3.2% | 100% | 100% |
| **researchproject** | `ResearchProject`, `schema:ResearchProject` | 4,258 | Medium | 100% | 93.5% | 14.0% | 100% | 100% |

### Low relevance (graph fragments — excluded from default search)

| Type | Raw `@type` values | Docs | Relevance | Title | Description | Keywords | URL | Source ID |
|------|-------------------|-----:|-----------|------:|------------:|---------:|----:|----------:|
| **datadownload** | `DataDownload`, `schema:DataDownload` | 290,079 | Low | 100%* | 99.2% | 0% | 100% | 100% |
| **contactpoint** | `ContactPoint`, `schema:ContactPoint` | 107,749 | Low | 0.1% | 0.1% | 0% | 100% | 100% |
| **place** | `Place`, `schema:Place` | 107,665 | Low | 0% | 0% | 0% | 100% | 100% |
| **geoshape** | `GeoShape`, `schema:GeoShape` | 107,621 | Low | 0% | 0% | 0% | 100% | 100% |

\* `datadownload` documents often have a `name` value (e.g. format label or URL fragment), but these are **not user-facing titles**. Default search excludes this type for that reason.

### Relation fields (all types)

| Field | Population across all types |
|-------|----------------------------|
| `author` | 0% |
| `creator` | 0% |
| `publisher` | 0% |

These relations exist inside nested/flattened structures and are **not available** for root-level full-text search today.

---

## Search design implications

### 1. Default primary-type filter

Restrict default search to:

```
dataset, creativework, person, organization, event, researchproject
```

Optionally include `datacatalog` (56k docs, excellent title + description coverage) if catalogue-like results are desired in the same UI.

### 2. Per-type field strategy

| Type | Title search | Description search | Keywords search | Notes |
|------|:------------:|:------------------:|:---------------:|-------|
| dataset | ✓ | ✓ | ✓ | Richest text fields; primary corpus |
| creativework | ✓ | ✓ (partial) | ✓ (partial) | Title always present; body terms sparse on ~60% |
| person | ✓ | ✗ | ✗ | Search names only unless relations are indexed later |
| organization | ✓ | ✓ (partial) | ✗ | Name + optional description |
| researchproject | ✓ | ✓ | ✓ (partial) | Good secondary corpus |
| event | ✓ | ✓ (partial) | ✗ | Moderate description coverage |
| datacatalog | ✓ | ✓ | ✗ | Strong metadata; medium relevance |

### 3. Universal metadata (all searchable types)

Always available for **filtering, facets, and links**:

- `datasource_id` — source filter + facet
- `url` — result link (not full-text)

### 4. Future index improvements

| Gap | Possible reindex change |
|-----|-------------------------|
| Person/org discovery by affiliation | Index `author` / `creator` / `publisher` as searchable text or nested objects |
| Provenance search | Extract publisher/creator names from JSON-LD graph into root fields |
| Spatial search | Promote geometry from `GeoShape` fragments onto parent records |

---

## Other record types (< 8,000 docs each)

46 additional normalised types exist with smaller counts (e.g. `thing` 7,397; `course` 785; `scholarlyarticle` 328). Most have 100% `url` and `datasource_id`; text field coverage varies widely.

These are omitted from the main table because they are outside the primary search relevance tiers. They can be included by widening the type filter if product needs expand.

---

## Comparison with earlier analysis

| Metric | [Data analysis (Jul 3)](./data-sources-analysis.md) | This report (Jul 12) |
|--------|-----------------------------------------------------|----------------------|
| Total documents | ~928k | 930,223 (aggregated) |
| Dataset count | ~94k | 94,268 |
| Docs without `name` (all types) | 83% | Still true globally — driven by low-relevance graph fragments |
| Root `author`/`creator`/`publisher` | flattened, subset | 0% at root on all types |

The earlier “17% have name” figure applies **across all types including graph fragments**. Among **high-relevance types alone**, title coverage is 99–100%.
