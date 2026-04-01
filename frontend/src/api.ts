const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Types ---

export interface SearchHit {
  id: string;
  name: string;
  description: string | null;
  price: number;
  brand: string;
  category: string;
  rating: number;
  image_url: string | null;
  highlight: Record<string, string[]> | null;
  score: number | null;
}

export interface FacetBucket {
  key: string;
  doc_count: number;
}

export interface SearchFacets {
  categories: FacetBucket[];
  brands: FacetBucket[];
  price_ranges: FacetBucket[];
  avg_rating: number | null;
}

export interface SearchResponse {
  hits: SearchHit[];
  total: number;
  facets: SearchFacets;
  page: number;
  page_size: number;
  pages: number;
  query: string;
}

export interface AutocompleteResponse {
  suggestions: string[];
}

export interface RevenueDataPoint {
  period: string;
  revenue: number;
  order_count: number;
}

export interface RevenueResponse {
  data: RevenueDataPoint[];
  total_revenue: number;
  total_orders: number;
  period_type: string;
}

export interface TopProductItem {
  product_name: string;
  category: string;
  total_sold: number;
  total_revenue: number;
}

export interface TopProductsResponse {
  products: TopProductItem[];
}

export interface CategoryPerformanceItem {
  category: string;
  total_revenue: number;
  total_sold: number;
  avg_order_value: number;
}

export interface CategoryPerformanceResponse {
  categories: CategoryPerformanceItem[];
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  price: number;
  brand: string;
  sku: string;
  rating: number;
  review_count: number;
  image_url: string | null;
  is_active: boolean;
  category: { id: string; name: string; slug: string };
  inventory: { quantity: number; reserved: number; available: number; reorder_level: number } | null;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface HealthResponse {
  status: string;
  services: Record<string, { status: string; version?: string; error?: string }>;
}

// --- API Functions ---

export const api = {
  search(params: Record<string, string>): Promise<SearchResponse> {
    const qs = new URLSearchParams(params).toString();
    return fetchJson(`${API_BASE}/search?${qs}`);
  },

  autocomplete(q: string): Promise<AutocompleteResponse> {
    return fetchJson(`${API_BASE}/search/autocomplete?q=${encodeURIComponent(q)}`);
  },

  getProducts(page = 1, pageSize = 20): Promise<ProductListResponse> {
    return fetchJson(`${API_BASE}/products?page=${page}&page_size=${pageSize}`);
  },

  getProduct(id: string): Promise<Product> {
    return fetchJson(`${API_BASE}/products/${id}`);
  },

  getRevenue(period = 'daily'): Promise<RevenueResponse> {
    return fetchJson(`${API_BASE}/analytics/revenue?period=${period}`);
  },

  getTopProducts(limit = 10): Promise<TopProductsResponse> {
    return fetchJson(`${API_BASE}/analytics/top-products?limit=${limit}`);
  },

  getCategoryPerformance(): Promise<CategoryPerformanceResponse> {
    return fetchJson(`${API_BASE}/analytics/categories`);
  },

  health(): Promise<HealthResponse> {
    return fetchJson('/health');
  },

  reindex(): Promise<{ message: string; total: number }> {
    return fetchJson(`${API_BASE}/search/reindex`, { method: 'POST' });
  },

  syncToSnowflake(): Promise<{ message: string }> {
    return fetchJson(`${API_BASE}/analytics/sync`, { method: 'POST' });
  },
};
