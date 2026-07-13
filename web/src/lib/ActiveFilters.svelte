<script lang="ts">
  import { formatTypeLabel, sourceLabel } from "./labels";

  interface SourceOption {
    id: string;
    name?: string | null;
  }

  interface Props {
    selectedTypes: string[];
    selectedSources: string[];
    sourceOptions: SourceOption[];
    onTypeToggle: (value: string) => void;
    onSourceToggle: (id: string) => void;
    onClearAll: () => void;
  }

  let {
    selectedTypes,
    selectedSources,
    sourceOptions,
    onTypeToggle,
    onSourceToggle,
    onClearAll,
  }: Props = $props();

  const hasFilters = $derived(selectedTypes.length > 0 || selectedSources.length > 0);

  function sourceName(id: string): string | null | undefined {
    return sourceOptions.find((option) => option.id === id)?.name;
  }
</script>

{#if hasFilters}
  <div class="active-filters" aria-label="Active filters">
    {#each selectedTypes as value (value)}
      <button type="button" class="filter-chip" onclick={() => onTypeToggle(value)}>
        {formatTypeLabel(value)}
        <span class="remove" aria-hidden="true">×</span>
      </button>
    {/each}
    {#each selectedSources as id (id)}
      <button type="button" class="filter-chip" onclick={() => onSourceToggle(id)}>
        {sourceLabel(id, sourceName(id))}
        <span class="remove" aria-hidden="true">×</span>
      </button>
    {/each}
    <button type="button" class="clear-filters" onclick={onClearAll}>Clear all</button>
  </div>
{/if}

<style>
  .active-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    margin: 0 0 1rem;
  }

  .filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.55rem;
    border: 1px solid #c5d5cf;
    border-radius: 999px;
    background: #eef5f2;
    color: #1f3d34;
    font-size: 0.82rem;
    cursor: pointer;
  }

  .remove {
    font-size: 1rem;
    line-height: 1;
    opacity: 0.7;
  }

  .clear-filters {
    padding: 0;
    border: 0;
    background: none;
    color: #0f6e56;
    font-size: 0.82rem;
    cursor: pointer;
    text-decoration: underline;
  }
</style>
