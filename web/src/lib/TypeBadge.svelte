<script lang="ts">
  import { resolveTypeTheme } from "./typeTheme";

  interface Props {
    type: string;
  }

  let { type }: Props = $props();

  const theme = $derived(resolveTypeTheme(type));
</script>

<span class="type-badge {theme.key}">
  {theme.badge}
</span>
