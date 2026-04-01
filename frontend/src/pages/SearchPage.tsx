import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Search, Star, SlidersHorizontal, Package, Loader2 } from 'lucide-react';
import { api, SearchResponse, SearchHit } from '../api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortBy, setSortBy] = useState('relevance');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const doSearch = useCallback(async (q: string, p: number, f: Record<string, string>, sort: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { q, page: String(p), page_size: '20', sort_by: sort };
      Object.entries(f).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await api.search(params);
      setResults(res);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    doSearch(query, page, filters, sortBy);
  }, [page, filters, sortBy]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setShowSuggestions(false);
    doSearch(query, 1, filters, sortBy);
  };

  const handleAutocomplete = async (value: string) => {
    setQuery(value);
    if (value.length >= 2) {
      try {
        const res = await api.autocomplete(value);
        setSuggestions(res.suggestions);
        setShowSuggestions(true);
      } catch {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const selectSuggestion = (s: string) => {
    setQuery(s);
    setShowSuggestions(false);
    setPage(1);
    doSearch(s, 1, filters, sortBy);
  };

  const toggleFilter = (key: string, value: string) => {
    setFilters(prev => {
      const next = { ...prev };
      if (next[key] === value) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const activeFilterCount = Object.keys(filters).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search Bar */}
      <div className="max-w-3xl mx-auto mb-8">
        <form onSubmit={handleSearch} className="relative">
          <div className="relative" ref={suggestionsRef}>
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => handleAutocomplete(e.target.value)}
              placeholder="Search products... (try 'wireless headphones', 'yoga mat', 'coffee')"
              className="w-full pl-12 pr-32 py-4 rounded-xl border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-lg transition-shadow"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Search
            </button>

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => selectSuggestion(s)}
                    className="w-full text-left px-4 py-3 hover:bg-indigo-50 text-sm flex items-center gap-2 transition-colors"
                  >
                    <Search className="w-4 h-4 text-gray-400" />
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        </form>

        {results && (
          <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
            <span>
              {results.total} result{results.total !== 1 ? 's' : ''}
              {query && <> for "<strong>{results.query}</strong>"</>}
            </span>
            <div className="flex items-center gap-4">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white"
              >
                <option value="relevance">Relevance</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="rating">Top Rated</option>
                <option value="newest">Newest</option>
              </select>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg border transition-colors ${
                  showFilters ? 'bg-indigo-50 border-indigo-300 text-indigo-700' : 'border-gray-300'
                }`}
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="bg-indigo-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex gap-6">
        {/* Facets Sidebar */}
        {showFilters && results?.facets && (
          <aside className="w-64 shrink-0">
            <div className="bg-white rounded-xl border border-gray-200 p-4 sticky top-24">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Filters</h3>
                {activeFilterCount > 0 && (
                  <button
                    onClick={clearFilters}
                    className="text-xs text-indigo-600 hover:underline"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {/* Categories */}
              {results.facets.categories.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Category</h4>
                  <div className="space-y-1">
                    {results.facets.categories.map((b) => (
                      <button
                        key={b.key}
                        onClick={() => toggleFilter('category', b.key)}
                        className={`w-full text-left text-sm px-2 py-1.5 rounded flex justify-between items-center transition-colors ${
                          filters.category === b.key
                            ? 'bg-indigo-100 text-indigo-700 font-medium'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                      >
                        <span>{b.key}</span>
                        <span className="text-xs text-gray-400">{b.doc_count}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Brands */}
              {results.facets.brands.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Brand</h4>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {results.facets.brands.map((b) => (
                      <button
                        key={b.key}
                        onClick={() => toggleFilter('brand', b.key)}
                        className={`w-full text-left text-sm px-2 py-1.5 rounded flex justify-between items-center transition-colors ${
                          filters.brand === b.key
                            ? 'bg-indigo-100 text-indigo-700 font-medium'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                      >
                        <span>{b.key}</span>
                        <span className="text-xs text-gray-400">{b.doc_count}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Price Ranges */}
              {results.facets.price_ranges.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Price Range</h4>
                  <div className="space-y-1">
                    {results.facets.price_ranges.map((b) => (
                      <button
                        key={b.key}
                        onClick={() => {
                          const rangeMap: Record<string, [string, string]> = {
                            'Under $25': ['0', '25'],
                            '$25-$50': ['25', '50'],
                            '$50-$100': ['50', '100'],
                            '$100-$200': ['100', '200'],
                            '$200+': ['200', ''],
                          };
                          const [min, max] = rangeMap[b.key] || ['', ''];
                          setFilters(prev => {
                            const next = { ...prev };
                            if (next.price_min === min && next.price_max === max) {
                              delete next.price_min;
                              delete next.price_max;
                            } else {
                              if (min) next.price_min = min;
                              else delete next.price_min;
                              if (max) next.price_max = max;
                              else delete next.price_max;
                            }
                            return next;
                          });
                          setPage(1);
                        }}
                        className="w-full text-left text-sm px-2 py-1.5 rounded flex justify-between items-center hover:bg-gray-50 text-gray-700 transition-colors"
                      >
                        <span>{b.key}</span>
                        <span className="text-xs text-gray-400">{b.doc_count}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {results.facets.avg_rating && (
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    Avg rating: <strong>{results.facets.avg_rating}</strong> / 5
                  </p>
                </div>
              )}
            </div>
          </aside>
        )}

        {/* Results Grid */}
        <div className="flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          ) : results && results.hits.length > 0 ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.hits.map((hit) => (
                  <ProductCard key={hit.id} hit={hit} />
                ))}
              </div>

              {/* Pagination */}
              {results.pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-50 hover:bg-gray-50 transition-colors"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {results.page} of {results.pages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(results.pages, p + 1))}
                    disabled={page === results.pages}
                    className="px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-50 hover:bg-gray-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : results ? (
            <div className="text-center py-20">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No products found</p>
              <p className="text-gray-400 text-sm mt-1">Try a different search term or clear filters</p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ProductCard({ hit }: { hit: SearchHit }) {
  return (
    <Link
      to={`/product/${hit.id}`}
      className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow group"
    >
      <div className="aspect-square bg-gray-100 relative overflow-hidden">
        {hit.image_url ? (
          <img
            src={hit.image_url}
            alt={hit.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <Package className="w-16 h-16" />
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="text-xs text-indigo-600 font-medium mb-1">{hit.category}</p>
        <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 mb-1">{hit.name}</h3>
        <p className="text-xs text-gray-500 mb-2">{hit.brand}</p>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">${hit.price.toFixed(2)}</span>
          <div className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span className="text-xs text-gray-600">{hit.rating.toFixed(1)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
