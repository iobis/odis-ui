<script lang="ts">
  import { onMount } from "svelte";
  import FacetPanel from "./lib/FacetPanel.svelte";
  import HealthIndicator from "./lib/HealthIndicator.svelte";
  import {
    getHealth,
    recordUrl,
    search,
    type HealthStatus,
    type SearchParams,
    type SearchResponse,
  } from "./lib/api";
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

  function currentParams(): SearchParams {
    return {
      q: query || undefined,
      types: selectedTypes.length ? selectedTypes : undefined,
      source: selectedSources.length ? selectedSources : undefined,
      page,
    };
  }

  async function runSearch(pushUrl = true) {
    loading = true;
    searchError = null;
    const params = currentParams();

    if (pushUrl) {
      history.replaceState(null, "", buildSearchUrl(params));
    }

    try {
      results = await search(params);
    } catch (e) {
      searchError = e instanceof Error ? e.message : "Search failed";
      results = null;
    } finally {
      loading = false;
    }
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
    void runSearch(false);

    void getHealth()
      .then((status) => {
        health = status;
      })
      .catch((e) => {
        healthError = e instanceof Error ? e.message : "Failed to reach API";
      });

    const onPopState = () => {
      applyFromUrl(new URL(window.location.href));
      void runSearch(false);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
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

  async function handleSourceToggle(id: string) {
    selectedSources = toggleValue(selectedSources, id);
    page = 1;
    await runSearch();
  }
</script>

<main>
  <header class="page-header">
    <div class="page-header-top">
      <h1>ODIS Search</h1>
      <HealthIndicator {health} {healthError} />
    </div>
    <p class="subtitle">Faceted search over ODIS metadata records</p>
  </header>

  <form class="search-form" onsubmit={handleSearch}>
    <input type="search" bind:value={query} placeholder="Search title, description, keywords…" />
    <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"}</button>
  </form>

  <div class="layout">
    <FacetPanel
      facets={results?.facets ?? null}
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
        <p class="results-meta">{results.total} result{results.total === 1 ? "" : "s"}</p>
        {#each results.items as item (item.id)}
          <article class="result-card">
            <span class="type">{item.type}</span>
            <h2>{item.title}</h2>
            {#if item.source?.name}
              <p class="source">{item.source.name}</p>
            {/if}
            {#if item.summary}
              <p>{item.summary}</p>
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
      {:else if loading}
        <p class="results-meta">Searching…</p>
      {/if}
    </section>
  </div>
</main>
