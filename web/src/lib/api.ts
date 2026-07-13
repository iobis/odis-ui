const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

export interface HealthStatus {
  status: string;
  backend: string;
  index: string;
  index_reachable: boolean;
  detail?: string | null;
}

export interface SourceRef {
  id: string;
  name?: string | null;
}

export interface SearchItem {
  id: string;
  title: string;
  summary?: string | null;
  type: string;
  url?: string | null;
  source?: SourceRef | null;
  highlight?: Record<string, string> | null;
  elasticsearch_document_url?: string | null;
}

export interface FacetBucket {
  value: string;
  count: number;
}

export interface SourceFacetBucket {
  id: string;
  name?: string | null;
  count: number;
}

export interface SearchFacets {
  types: FacetBucket[];
  sources: SourceFacetBucket[];
}

export interface SearchResponse {
  total: number;
  facets: SearchFacets;
  items: SearchItem[];
  page: number;
  size: number;
}

export interface SearchParams {
  q?: string;
  types?: string[];
  source?: string;
  sort?: "relevance" | "title";
  page?: number;
  size?: number;
}

async function fetchJson<T>(path: string, params?: Record<string, string | string[]>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else if (value !== undefined && value !== "") {
        url.searchParams.set(key, value);
      }
    }
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function recordUrl(id: string): string {
  return `${API_BASE}/records/${encodeURIComponent(id)}`;
}

export function getHealth(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>("/health");
}

export function search(params: SearchParams = {}): Promise<SearchResponse> {
  const query: Record<string, string | string[]> = {};
  if (params.q) query.q = params.q;
  if (params.types?.length) query.types = params.types;
  if (params.source) query.source = params.source;
  if (params.sort) query.sort = params.sort;
  if (params.page) query.page = String(params.page);
  if (params.size) query.size = String(params.size);
  return fetchJson<SearchResponse>("/search", query);
}
