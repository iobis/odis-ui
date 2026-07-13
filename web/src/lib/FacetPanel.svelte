<script lang="ts">
  import type { SearchFacets } from "./api";
  import { formatNumber } from "./format";
  import { formatTypeLabel, sourceLabel } from "./labels";

  interface Props {
    facets: SearchFacets | null;
    typeOptions: string[];
    selectedTypes: string[];
    selectedSources: string[];
    onTypeToggle: (value: string) => void;
    onSourceToggle: (id: string) => void;
  }

  let {
    facets,
    typeOptions,
    selectedTypes,
    selectedSources,
    onTypeToggle,
    onSourceToggle,
  }: Props = $props();

  function typeCount(value: string): number {
    return facets?.types.find((bucket) => bucket.value === value)?.count ?? 0;
  }
</script>

<aside class="facet-panel">
  <section class="facet-group">
    <h2>Type</h2>
    {#if typeOptions.length}
      <ul>
        {#each typeOptions as value (value)}
          <li>
            <label>
              <input
                type="checkbox"
                checked={selectedTypes.includes(value)}
                onchange={() => onTypeToggle(value)}
              />
              <span>{formatTypeLabel(value)}</span>
              <span class="count">{formatNumber(typeCount(value))}</span>
            </label>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="empty">Search to see type facets.</p>
    {/if}
  </section>

  <section class="facet-group">
    <h2>Datasource</h2>
    {#if facets?.sources.length}
      <ul>
        {#each facets.sources as bucket (bucket.id)}
          <li>
            <label>
              <input
                type="checkbox"
                checked={selectedSources.includes(bucket.id)}
                onchange={() => onSourceToggle(bucket.id)}
              />
              <span>{sourceLabel(bucket.id, bucket.name)}</span>
              <span class="count">{formatNumber(bucket.count)}</span>
            </label>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="empty">Search to see datasource facets.</p>
    {/if}
  </section>
</aside>

<style>
  .facet-panel {
    background: #fff;
    border: 1px solid #d7e0dc;
    border-radius: 4px;
    padding: 1rem;
  }

  .facet-group + .facet-group {
    margin-top: 1.25rem;
    padding-top: 1.25rem;
    border-top: 1px solid #d7e0dc;
  }

  h2 {
    margin: 0 0 0.75rem;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #4b5d63;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 18rem;
    overflow-y: auto;
  }

  li + li {
    margin-top: 0.35rem;
  }

  label {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.5rem;
    align-items: start;
    font-size: 0.9rem;
    cursor: pointer;
  }

  .count {
    color: #4b5d63;
    font-size: 0.8rem;
    font-variant-numeric: tabular-nums;
  }

  .empty {
    margin: 0;
    color: #4b5d63;
    font-size: 0.85rem;
  }
</style>
