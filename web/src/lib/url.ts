import type { SearchParams } from "./api";

export function parseSearchParams(url: URL): SearchParams {
  const params: SearchParams = {};
  const q = url.searchParams.get("q");
  if (q) params.q = q;

  const types = url.searchParams.getAll("types");
  if (types.length) params.types = types;

  const sources = url.searchParams.getAll("source");
  if (sources.length) params.source = sources;

  const page = url.searchParams.get("page");
  if (page) params.page = Number(page);

  return params;
}

export function buildSearchUrl(params: SearchParams): string {
  const url = new URL(window.location.href);
  url.search = "";

  if (params.q) url.searchParams.set("q", params.q);
  params.types?.forEach((type) => url.searchParams.append("types", type));
  params.source?.forEach((source) => url.searchParams.append("source", source));
  if (params.page && params.page > 1) url.searchParams.set("page", String(params.page));

  return `${url.pathname}${url.search}`;
}

export function toggleValue(values: string[], value: string): string[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}
