<script lang="ts">
  import { prepareSummary } from "./summary";

  type Props = {
    summary: string;
    collapsedLength?: number;
  };

  let { summary, collapsedLength = 360 }: Props = $props();

  let expanded = $state(false);

  const prepared = $derived(prepareSummary(summary));
  const collapsible = $derived(prepared.structured && prepared.text.length > collapsedLength);
  const displayText = $derived(
    !collapsible || expanded ? prepared.text : `${prepared.text.slice(0, collapsedLength).trimEnd()}…`,
  );
</script>

<p class:summary-structured={prepared.structured}>
  {displayText}
  {#if collapsible}
    <button type="button" class="summary-toggle" onclick={() => (expanded = !expanded)}>
      {expanded ? "Show less" : "Show more"}
    </button>
  {/if}
</p>
