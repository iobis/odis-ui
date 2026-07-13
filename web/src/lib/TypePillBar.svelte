<script lang="ts">
  import { formatTypeLabel } from "./labels";

  interface Props {
    typeOptions: string[];
    selectedTypes: string[];
    onAllTypes: () => void;
    onTypeToggle: (value: string) => void;
  }

  let { typeOptions, selectedTypes, onAllTypes, onTypeToggle }: Props = $props();

  const allTypesActive = $derived(selectedTypes.length === 0);
</script>

<div class="type-pillbar" role="group" aria-label="Record type filters">
  <button type="button" class="pill" class:on={allTypesActive} onclick={onAllTypes}>
    All types
  </button>

  {#each typeOptions as value (value)}
    <button
      type="button"
      class="pill"
      class:on={selectedTypes.includes(value)}
      onclick={() => onTypeToggle(value)}
    >
      {formatTypeLabel(value)}
    </button>
  {/each}
</div>

<style>
  .type-pillbar {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
  }

  .pill {
    padding: 0.45rem 0.85rem;
    border-radius: 20px;
    border: 1px solid var(--line-strong);
    background: var(--paper);
    color: var(--ink-soft);
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    line-height: 1.2;
  }

  .pill:hover {
    color: var(--ink);
    border-color: var(--ink-faint);
  }

  .pill.on {
    background: var(--ink);
    border-color: var(--ink);
    color: var(--paper-raised);
  }

  .pill.on:hover {
    color: var(--paper-raised);
  }
</style>
