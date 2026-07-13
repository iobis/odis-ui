<script lang="ts">
  import type { SearchFacets } from "./api";
  import { formatNumber } from "./format";
  import { formatTypeLabel, sourceLabel } from "./labels";

  interface SourceOption {
    id: string;
    name?: string | null;
  }

  interface Props {
    facets: SearchFacets | null;
    typeOptions: string[];
    sourceOptions: SourceOption[];
    selectedTypes: string[];
    selectedSources: string[];
    onTypeToggle: (value: string) => void;
    onSourceToggle: (id: string) => void;
  }

  let {
    facets,
    typeOptions,
    sourceOptions,
    selectedTypes,
    selectedSources,
    onTypeToggle,
    onSourceToggle,
  }: Props = $props();

  function typeCount(value: string): number {
    return facets?.types.find((bucket) => bucket.value === value)?.count ?? 0;
  }

  function sourceCount(id: string): number {
    return facets?.sources.find((bucket) => bucket.id === id)?.count ?? 0;
  }

  function sourceName(id: string): string | null | undefined {
    return (
      facets?.sources.find((bucket) => bucket.id === id)?.name ??
      sourceOptions.find((option) => option.id === id)?.name
    );
  }
</script>

<aside class="facet-panel">
  <section class="facet-group">
    <h2>Type</h2>
    <p class="facet-hint">Match any selected</p>
    {#if typeOptions.length}
      <ul>
        {#each typeOptions as value (value)}
          {@const count = typeCount(value)}
          <li class:inactive={count === 0 && !selectedTypes.includes(value)}>
            <label>
              <input
                type="checkbox"
                checked={selectedTypes.includes(value)}
                onchange={() => onTypeToggle(value)}
              />
              <span>{formatTypeLabel(value)}</span>
              <span class="count">{formatNumber(count)}</span>
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
    <p class="facet-hint">Match any selected</p>
    {#if sourceOptions.length}
      <ul>
        {#each sourceOptions as option (option.id)}
          {@const count = sourceCount(option.id)}
          <li class:inactive={count === 0 && !selectedSources.includes(option.id)}>
            <label>
              <input
                type="checkbox"
                checked={selectedSources.includes(option.id)}
                onchange={() => onSourceToggle(option.id)}
              />
              <span>{sourceLabel(option.id, sourceName(option.id) ?? option.name)}</span>
              <span class="count">{formatNumber(count)}</span>
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
    margin: 0 0 0.25rem;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #4b5d63;
  }

  .facet-hint {
    margin: 0 0 0.75rem;
    font-size: 0.75rem;
    color: #8a9a9f;
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

  li.inactive {
    opacity: 0.45;
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
