<script lang="ts">
  import type { BackendInfo } from "./api";

  interface Props {
    backends: BackendInfo[];
    selectedId: string | null;
    loading?: boolean;
    error?: string | null;
    onSelect: (backendId: string) => void;
  }

  let { backends, selectedId, loading = false, error = null, onSelect }: Props = $props();

  function tone(backend: BackendInfo): "ok" | "warning" | "error" | "pending" {
    if (loading && backends.length === 0) return "pending";
    const health = backend.health;
    if (!health.index_reachable || health.status !== "ok") {
      return health.index_reachable ? "warning" : "error";
    }
    return "ok";
  }

  function title(backend: BackendInfo): string {
    const health = backend.health;
    return [backend.label, health.status, health.index, health.detail].filter(Boolean).join(" · ");
  }
</script>

{#if error && backends.length === 0}
  <span class="backend-switcher error" title={error}>
    <span class="health-dot" aria-hidden="true"></span>
    <span>API unreachable</span>
  </span>
{:else if backends.length}
  <div class="backend-switcher" role="group" aria-label="Search backend">
    {#each backends as backend (backend.id)}
      <button
        type="button"
        class="backend-option {tone(backend)}"
        class:selected={selectedId === backend.id}
        title={title(backend)}
        aria-pressed={selectedId === backend.id}
        onclick={() => onSelect(backend.id)}
      >
        <span class="health-dot" aria-hidden="true"></span>
        <span class="backend-label">{backend.label}</span>
      </button>
    {/each}
  </div>
{:else}
  <span class="backend-switcher pending">
    <span class="health-dot" aria-hidden="true"></span>
    <span>Checking…</span>
  </span>
{/if}

<style>
  .backend-switcher {
    display: inline-flex;
    align-items: center;
    gap: 0.15rem;
    flex-shrink: 0;
    font-size: 0.72rem;
    letter-spacing: 0.02em;
    color: #8a9a9f;
    user-select: none;
  }

  .backend-option {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.55rem;
    border: 1px solid transparent;
    border-radius: 4px;
    background: transparent;
    color: inherit;
    font: inherit;
    cursor: pointer;
  }

  .backend-option.selected {
    border-color: #d7e0dc;
    background: #fff;
    color: #1b2429;
  }

  .backend-label {
    font-weight: 500;
  }

  .health-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.55;
    flex-shrink: 0;
  }

  .ok .health-dot {
    background: #3d9b7a;
    opacity: 1;
    box-shadow: 0 0 0 2px rgba(61, 155, 122, 0.15);
  }

  .warning {
    color: #9a6b3d;
  }

  .warning .health-dot {
    background: #c4843a;
    opacity: 1;
  }

  .error {
    color: #a35a4a;
  }

  .error .health-dot {
    background: #c45f4f;
    opacity: 1;
  }

  .pending .health-dot {
    animation: pulse 1.4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 0.35;
    }
    50% {
      opacity: 0.9;
    }
  }
</style>
