<script lang="ts">
  import type { HealthStatus } from "./api";

  interface Props {
    health: HealthStatus | null;
    healthError: string | null;
  }

  let { health, healthError }: Props = $props();

  const state = $derived.by(() => {
    if (healthError) {
      return {
        tone: "error" as const,
        label: "API unreachable",
        detail: healthError,
      };
    }
    if (!health) {
      return {
        tone: "pending" as const,
        label: "Checking…",
        detail: "Contacting search API",
      };
    }
    if (health.status !== "ok" || !health.index_reachable) {
      return {
        tone: "warning" as const,
        label: health.index_reachable ? "Degraded" : "Index unreachable",
        detail: [
          `Backend: ${health.backend}`,
          `Index: ${health.index}`,
          health.detail,
        ]
          .filter(Boolean)
          .join(" · "),
      };
    }
    return {
      tone: "ok" as const,
      label: "Operational",
      detail: `${health.backend} · ${health.index}`,
    };
  });
</script>

<span
  class="health-indicator"
  class:ok={state.tone === "ok"}
  class:warning={state.tone === "warning"}
  class:error={state.tone === "error"}
  class:pending={state.tone === "pending"}
  title={state.detail}
  aria-live="polite"
>
    <span class="health-dot" aria-hidden="true"></span>
    <span class="health-label">{state.label}</span>
    {#if state.tone === "ok" && health}
      <span class="health-meta">{health.backend}</span>
    {/if}
</span>

<style>
  .health-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.72rem;
    color: #8a9a9f;
    letter-spacing: 0.02em;
    cursor: default;
    user-select: none;
    flex-shrink: 0;
  }

  .health-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.55;
    flex-shrink: 0;
  }

  .health-label {
    font-weight: 500;
  }

  .health-meta {
    opacity: 0.75;
  }

  .health-meta::before {
    content: "·";
    margin-right: 0.45rem;
    opacity: 0.6;
  }

  .ok {
    color: #6b8f84;
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
