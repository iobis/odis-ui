<script lang="ts">
  import { onMount } from "svelte";
  import { getHealth, recordUrl, search, type HealthStatus, type SearchResponse } from "./lib/api";
  import "./app.css";

  let health: HealthStatus | null = $state(null);
  let healthError: string | null = $state(null);
  let query = $state("");
  let results: SearchResponse | null = $state(null);
  let searchError: string | null = $state(null);
  let loading = $state(false);

  onMount(async () => {
    try {
      health = await getHealth();
    } catch (e) {
      healthError = e instanceof Error ? e.message : "Failed to reach API";
    }
  });

  async function handleSearch(event: Event) {
    event.preventDefault();
    loading = true;
    searchError = null;
    try {
      results = await search({ q: query || undefined });
    } catch (e) {
      searchError = e instanceof Error ? e.message : "Search failed";
      results = null;
    } finally {
      loading = false;
    }
  }
</script>

<main>
  <h1>ODIS Search</h1>
  <p class="subtitle">Faceted search over ODIS metadata records</p>

  {#if healthError}
    <div class="status degraded">API unreachable: {healthError}</div>
  {:else if health}
    <div class="status" class:ok={health.status === "ok"} class:degraded={health.status !== "ok"}>
      API {health.status} · backend {health.backend} · index {health.index}
      {#if health.index_reachable}
        (reachable)
      {:else}
        (not reachable)
      {/if}
      {#if health.detail}
        <br /><span class="error">{health.detail}</span>
      {/if}
    </div>
  {:else}
    <div class="status">Checking API health…</div>
  {/if}

  <form class="search-form" onsubmit={handleSearch}>
    <input type="search" bind:value={query} placeholder="Search by title…" />
    <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"}</button>
  </form>

  {#if searchError}
    <p class="error">{searchError}</p>
  {/if}

  {#if results}
    <p class="results-meta">{results.total} result{results.total === 1 ? "" : "s"}</p>
    {#each results.items as item (item.id)}
      <article class="result-card">
        <span class="type">{item.type}</span>
        <h2>{item.title}</h2>
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
  {/if}
</main>
