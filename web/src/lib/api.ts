const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";
const REQUEST_TIMEOUT_MS = 15_000;
const BACKEND_STORAGE_KEY = "odis-search-backend";

export interface HealthStatus {
  status: string;
  backend: string;
  index: string;
  index_reachable: boolean;
  detail?: string | null;
}

export interface BackendInfo {
  id: string;
  label: string;
  health: HealthStatus;
}

export interface BackendsResponse {
  default: string;
  backends: BackendInfo[];
}

export interface SourceRef {
  id: string;
  name?: string | null;
}

export interface BoundingBox {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface SpatialExtent {
  boxes: BoundingBox[];
  points: GeoPoint[];
}

export interface SearchItem {
  id: string;
  title: string;
  summary?: string | null;
  type: string;
  url?: string | null;
  source?: SourceRef | null;
  highlight?: Record<string, string> | null;
  spatial?: SpatialExtent | null;
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
  source?: string[];
  sort?: "relevance" | "title";
  page?: number;
  size?: number;
}

let activeBackend: string | null = localStorage.getItem(BACKEND_STORAGE_KEY);

export function getActiveBackend(): string | null {
  return activeBackend;
}

export function setActiveBackend(backendId: string | null): void {
  activeBackend = backendId;
  if (backendId) {
    localStorage.setItem(BACKEND_STORAGE_KEY, backendId);
  } else {
    localStorage.removeItem(BACKEND_STORAGE_KEY);
  }
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

  const headers: HeadersInit = {};
  if (activeBackend) {
    headers["X-Search-Backend"] = activeBackend;
  }

  let response: Response;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    response = await fetch(url, { signal: controller.signal, headers });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        "The search backend is not responding. It may be temporarily unavailable.",
      );
    }
    throw new Error(
      "The search backend cannot be reached. Check your connection or try again later.",
    );
  } finally {
    window.clearTimeout(timeout);
  }

  if (!response.ok) {
    if (response.status >= 500) {
      throw new Error(
        "The search backend cannot be reached. It may be temporarily unavailable.",
      );
    }
    throw new Error(`Request failed (${response.status}).`);
  }

  return response.json() as Promise<T>;
}

export function recordUrl(id: string): string {
  return `${API_BASE}/records/${encodeURIComponent(id)}`;
}

export function getHealth(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>("/health");
}

export function getBackends(): Promise<BackendsResponse> {
  return fetchJson<BackendsResponse>("/backends");
}

export function search(params: SearchParams = {}): Promise<SearchResponse> {
  const query: Record<string, string | string[]> = {};
  if (params.q) query.q = params.q;
  if (params.types?.length) query.types = params.types;
  if (params.source?.length) query.source = params.source;
  if (params.sort) query.sort = params.sort;
  if (params.page) query.page = String(params.page);
  if (params.size) query.size = String(params.size);
  return fetchJson<SearchResponse>("/search", query);
}
