<script lang="ts">
  import type { SpatialExtent } from "./api";
  import { resolveTypeTheme } from "./typeTheme";
  import {
    boundsToSvg,
    extentThemeClass,
    formatExtentLabel,
    unionBounds,
  } from "./spatial";

  interface Props {
    spatial: SpatialExtent;
    recordType: string;
  }

  let { spatial, recordType }: Props = $props();

  const bounds = $derived(unionBounds(spatial));
  const svg = $derived(bounds ? boundsToSvg(bounds) : null);
  const label = $derived(bounds ? formatExtentLabel(bounds) : "");
  const themeClass = $derived(extentThemeClass[resolveTypeTheme(recordType).key]);
</script>

{#if bounds && svg}
  <div class="extent" aria-label="Spatial extent: {label}">
    <svg viewBox="0 0 36 20" width="26" height="15" aria-hidden="true">
      <rect
        x="0.5"
        y="0.5"
        width="35"
        height="19"
        fill="none"
        stroke="var(--line-strong)"
      />
      {#if svg.isPoint}
        <circle
          class="extent-marker {themeClass}"
          cx={svg.x}
          cy={svg.y}
          r="1.4"
        />
      {:else}
        <rect
          class="extent-marker {themeClass}"
          x={svg.x}
          y={svg.y}
          width={svg.width}
          height={svg.height}
          stroke-width="0.75"
        />
      {/if}
    </svg>
    <span class="extent-label">{label}</span>
  </div>
{/if}

<style>
  .extent {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--ink-soft);
    font-size: 0.72rem;
  }

  .extent svg {
    flex: none;
  }

  .extent-label {
    font-family: "IBM Plex Mono", monospace;
    font-variant-numeric: tabular-nums;
    line-height: 1.3;
  }

  .extent-marker.dataset {
    fill: var(--dataset-tint);
    stroke: var(--dataset);
  }

  .extent-marker.literature {
    fill: var(--literature-tint);
    stroke: var(--literature);
  }

  .extent-marker.org {
    fill: var(--org-tint);
    stroke: var(--org);
  }

  .extent-marker.training {
    fill: var(--training-tint);
    stroke: var(--training);
  }

  .extent-marker.project {
    fill: var(--project-tint);
    stroke: var(--project);
  }

  .extent-marker.default {
    fill: var(--depth-tint);
    stroke: var(--depth);
  }
</style>
