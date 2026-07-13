<script lang="ts">
  import { onMount } from "svelte";
  import FacetPanel from "./lib/FacetPanel.svelte";
  import HealthIndicator from "./lib/HealthIndicator.svelte";
  import SpatialExtentMap from "./lib/SpatialExtentMap.svelte";
  import TypeBadge from "./lib/TypeBadge.svelte";
  import TypePillBar from "./lib/TypePillBar.svelte";
  import SummaryText from "./lib/SummaryText.svelte";
  import {
    getHealth,
    recordUrl,
    search,
    type HealthStatus,
    type SearchFacets,
    type SearchParams,
    type SearchResponse,
  } from "./lib/api";
  import { formatNumber } from "./lib/format";
  import { buildSearchUrl, parseSearchParams, toggleValue } from "./lib/url";
  import "./app.css";

  let health: HealthStatus | null = $state(null);
  let healthError: string | null = $state(null);
  let query = $state("");
  let selectedTypes = $state<string[]>([]);
  let selectedSources = $state<string[]>([]);
  let page = $state(1);
  let results: SearchResponse | null = $state(null);
  let searchError: string | null = $state(null);
  let loading = $state(false);
  let loadingMore = $state(false);
  let scrollSentinel: HTMLDivElement | undefined = $state();
  let scrollObserver: IntersectionObserver | undefined = $state();
  let typeOptions = $state<string[]>([]);

  const hasMore = $derived(results !== null && results.items.length < results.total);

  function updateTypeOptions(facets: SearchFacets) {
    const order = facets.types.map((bucket) => bucket.value);
    const known = new Set([...typeOptions, ...order]);
    typeOptions = [...order, ...[...known].filter((value) => !order.includes(value))];
  }

  function currentParams(): SearchParams {
    return {
      q: query || undefined,
      types: selectedTypes.length ? selectedTypes : undefined,
      source: selectedSources.length ? selectedSources : undefined,
      page,
    };
  }

  async function runSearch(pushUrl = true, append = false) {
    if (append) {
      if (loading || loadingMore || !hasMore) return;
      loadingMore = true;
    } else {
      loading = true;
      searchError = null;
    }

    const params = currentParams();

    if (pushUrl && !append) {
      history.replaceState(null, "", buildSearchUrl(params));
    }

    try {
      const response = await search(params);
      if (append && results) {
        results = {
          ...response,
          items: [...results.items, ...response.items],
        };
      } else {
        results = response;
      }
      updateTypeOptions(response.facets);
    } catch (e) {
      if (append) {
        page = Math.max(1, page - 1);
      } else {
        searchError = e instanceof Error ? e.message : "Search failed";
        results = null;
      }
    } finally {
      loading = false;
      loadingMore = false;
    }
  }

  async function loadMore() {
    if (!hasMore || loading || loadingMore) return;
    page += 1;
    await runSearch(false, true);
  }

  function applyFromUrl(url: URL) {
    const params = parseSearchParams(url);
    query = params.q ?? "";
    selectedTypes = params.types ?? [];
    selectedSources = params.source ?? [];
    page = params.page ?? 1;
  }

  onMount(() => {
    applyFromUrl(new URL(window.location.href));
    page = 1;
    void runSearch(false);

    scrollObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          void loadMore();
        }
      },
      { rootMargin: "240px" },
    );

    void getHealth()
      .then((status) => {
        health = status;
      })
      .catch((e) => {
        healthError = e instanceof Error ? e.message : "Failed to reach API";
      });

    const onPopState = () => {
      applyFromUrl(new URL(window.location.href));
      page = 1;
      void runSearch(false);
    };
    window.addEventListener("popstate", onPopState);
    return () => {
      window.removeEventListener("popstate", onPopState);
      scrollObserver?.disconnect();
      scrollObserver = undefined;
    };
  });

  $effect(() => {
    const node = scrollSentinel;
    const observer = scrollObserver;
    if (!node || !observer) return;
    observer.observe(node);
    return () => observer.unobserve(node);
  });

  async function handleSearch(event: Event) {
    event.preventDefault();
    page = 1;
    await runSearch();
  }

  async function handleTypeToggle(value: string) {
    selectedTypes = toggleValue(selectedTypes, value);
    page = 1;
    await runSearch();
  }

  async function handleAllTypes() {
    selectedTypes = [];
    page = 1;
    await runSearch();
  }

  async function handleSourceToggle(id: string) {
    selectedSources = toggleValue(selectedSources, id);
    page = 1;
    await runSearch();
  }

  async function handleHomeClick(event: MouseEvent) {
    event.preventDefault();
    query = "";
    selectedTypes = [];
    selectedSources = [];
    page = 1;
    await runSearch();
  }
</script>

<main>
  <header class="page-header">
    <div class="page-header-top">
      <h1><a href="/" class="site-title" onclick={handleHomeClick}>ODIS Search</a></h1>
      <HealthIndicator {health} {healthError} />
    </div>
    <p class="subtitle">Faceted search over ODIS metadata records</p>
  </header>

  <form class="search-form" onsubmit={handleSearch}>
    <input type="search" bind:value={query} placeholder="Search title, description, keywords…" />
    <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"}</button>
  </form>

  <TypePillBar
    {typeOptions}
    {selectedTypes}
    onAllTypes={handleAllTypes}
    onTypeToggle={handleTypeToggle}
  />

  <div class="layout">
    <FacetPanel
      facets={results?.facets ?? null}
      {typeOptions}
      {selectedTypes}
      {selectedSources}
      onTypeToggle={handleTypeToggle}
      onSourceToggle={handleSourceToggle}
    />

    <section class="results">
      {#if searchError}
        <p class="error">{searchError}</p>
      {/if}

      {#if results}
        <p class="results-meta">{formatNumber(results.total)} result{results.total === 1 ? "" : "s"}</p>
        {#each results.items as item (item.id)}
          <article class="result-card">
            <TypeBadge type={item.type} />
            <h2>{item.title}</h2>
            {#if item.source?.name}
              <p class="source">{item.source.name}</p>
            {/if}
            {#if item.url}
              <p class="record-url">
                <a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a>
              </p>
            {/if}
            {#if item.summary}
              <SummaryText summary={item.summary} />
            {/if}
            {#if item.spatial && (item.spatial.boxes.length || item.spatial.points.length)}
              <div class="card-foot">
                <SpatialExtentMap spatial={item.spatial} recordType={item.type} />
              </div>
            {/if}
            <div class="record-links">
              <a class="record-link" href={recordUrl(item.id)} target="_blank" rel="noopener noreferrer">
                API record
              </a>
              {#if item.elasticsearch_document_url}
                <a
                  class="record-link"
                  href={item.elasticsearch_document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Elasticsearch document
                </a>
              {/if}
            </div>
          </article>
        {/each}

        {#if hasMore}
          <div class="scroll-sentinel" bind:this={scrollSentinel} aria-hidden="true"></div>
        {/if}

        {#if loadingMore}
          <p class="results-meta loading-more">Loading more…</p>
        {:else if !hasMore && results.items.length > 0}
          <p class="results-meta end-of-results">End of results</p>
        {/if}
      {:else if loading}
        <p class="results-meta">Searching…</p>
      {/if}
    </section>
  </div>
</main>
