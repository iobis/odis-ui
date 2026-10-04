<script lang="ts">
  import { onMount } from "svelte";
  import { getNetworkStatus, type NetworkNodeStatus, type NetworkStatusResponse } from "./api";
  import { formatNumber } from "./format";

  let status: NetworkStatusResponse | null = $state(null);
  let error: string | null = $state(null);
  let loading = $state(true);

  onMount(() => {
    void (async () => {
      loading = true;
      error = null;
      try {
        status = await getNetworkStatus();
      } catch (e) {
        error = e instanceof Error ? e.message : "Failed to load network status.";
      } finally {
        loading = false;
      }
    })();
  });

  function pct(part: number, whole: number): number {
    if (whole <= 0) return 0;
    return Math.min(100, Math.max(0, (part / whole) * 100));
  }

  function formatLastIndexed(value: string | null | undefined): string {
    if (value == null || value === "") return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
</script>

{#snippet nodeTable(nodes: NetworkNodeStatus[])}
  {#if nodes.length === 0}
    <p class="network-empty">None</p>
  {:else}
    <div class="network-table-wrap">
      <table class="network-table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Errors</th>
          </tr>
        </thead>
        <tbody>
          {#each nodes as node (node.id)}
            <tr>
              <td>
                {#if node.url}
                  <a href={node.url} target="_blank" rel="noopener noreferrer">{node.name}</a>
                {:else}
                  {node.name}
                {/if}
              </td>
              <td>
                <ul class="network-errors">
                  {#each node.errors as msg, i (i)}
                    <li>{msg}</li>
                  {/each}
                </ul>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
{/snippet}

<section class="network-page">
  <h1>ODIS network status</h1>
  <p class="network-lede">Status of the federated nodes of the ODIS network.</p>

  {#if loading}
    <p class="results-meta">Loading…</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if status}
    {@const total = status.total_nodes}
    {@const unresponsivePct = pct(status.unresponsive_count, total)}
    {@const parsingPct = pct(status.parsing_error_count, total)}
    {@const summonerPct = pct(status.summoner_error_count, total)}

    <h2>Summary</h2>
    <dl class="network-summary">
      <div>
        <dt>Total Nodes</dt>
        <dd>
          <a href="#all-nodes" class="network-stat-link">{status.total_nodes}</a>
        </dd>
      </div>
      <div>
        <dt>Unresponsive Nodes</dt>
        <dd>
          <a href="#unresponsive" class="network-stat-link">{status.unresponsive_count}</a>
        </dd>
        <div
          class="network-stat-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={status.unresponsive_count}
          aria-label="{status.unresponsive_count} of {total} nodes unresponsive"
        >
          <span class="network-stat-bar-subset" style="width: {unresponsivePct}%"></span>
        </div>
      </div>
      <div>
        <dt>Nodes with Parsing Errors</dt>
        <dd>
          <a href="#parsing-errors" class="network-stat-link">{status.parsing_error_count}</a>
        </dd>
        <div
          class="network-stat-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={status.parsing_error_count}
          aria-label="{status.parsing_error_count} of {total} nodes with parsing errors"
        >
          <span class="network-stat-bar-subset" style="width: {parsingPct}%"></span>
        </div>
      </div>
      {#if status.summoner_error_count > 0}
        <div>
          <dt>Summoner errors</dt>
          <dd>
            <a href="#all-nodes" class="network-stat-link">{status.summoner_error_count}</a>
          </dd>
          <div
            class="network-stat-bar"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={status.summoner_error_count}
            aria-label="{status.summoner_error_count} of {total} nodes with summoner errors"
          >
            <span class="network-stat-bar-subset" style="width: {summonerPct}%"></span>
          </div>
        </div>
      {/if}
    </dl>

    <h2 id="all-nodes">All nodes ({status.all_nodes.length})</h2>
    {#if status.all_nodes.length === 0}
      <p class="network-empty">None</p>
    {:else}
      <div class="network-table-wrap">
        <table class="network-table network-table-all">
          <thead>
            <tr>
              <th scope="col" class="network-status-col">
                <span class="visually-hidden">Status</span>
              </th>
              <th scope="col">Name</th>
              <th scope="col">Last indexed</th>
              <th scope="col">URL</th>
              <th scope="col">Indexed documents</th>
            </tr>
          </thead>
          <tbody>
            {#each status.all_nodes as node (node.id)}
              <tr>
                <td class="network-status-col">
                  <svg
                    class="network-status-dot"
                    class:network-status-ok={node.responsive}
                    class:network-status-down={!node.responsive}
                    width="8"
                    height="8"
                    viewBox="0 0 8 8"
                    aria-label={node.responsive ? "Responsive" : "Unresponsive"}
                    role="img"
                  >
                    <title>{node.responsive ? "Responsive" : "Unresponsive"}</title>
                    <circle cx="4" cy="4" r="4" />
                  </svg>
                </td>
                <td>{node.name}</td>
                <td class="network-num">{formatLastIndexed(node.last_indexed)}</td>
                <td>
                  {#if node.url}
                    <a href={node.url} target="_blank" rel="noopener noreferrer">{node.url}</a>
                  {:else}
                    —
                  {/if}
                </td>
                <td class="network-num">
                  {node.summoner_stored != null ? formatNumber(node.summoner_stored) : "—"}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    <h2 id="unresponsive">Unresponsive nodes ({status.unresponsive_count})</h2>
    {@render nodeTable(status.unresponsive)}

    <h2 id="parsing-errors">Nodes with parsing errors ({status.parsing_error_count})</h2>
    {@render nodeTable(status.parsing_errors)}
  {/if}
</section>
