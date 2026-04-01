"""
Unit tests for SearchService.
Tests Elasticsearch query building and response parsing.
"""

import pytest

from app.schemas.product import SearchQuery
from app.services.search_service import SearchService


class TestSearchQueryBuilding:
    """Test that search queries are built correctly for Elasticsearch."""

    def setup_method(self):
        # Create service with a mock ES client (not used for query building)
        self.service = SearchService.__new__(SearchService)
        self.service.index = "test_products"

    def test_empty_query_uses_match_all(self):
        query = SearchQuery(q="", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        assert body["query"]["bool"]["must"][0] == {"match_all": {}}

    def test_text_query_uses_multi_match(self):
        query = SearchQuery(q="wireless headphones", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        must = body["query"]["bool"]["must"][0]
        assert must["multi_match"]["query"] == "wireless headphones"
        assert "name^3" in must["multi_match"]["fields"]
        assert must["multi_match"]["fuzziness"] == "AUTO"

    def test_category_filter(self):
        query = SearchQuery(q="test", category="Electronics", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        filters = body["query"]["bool"]["filter"]
        assert {"term": {"category.keyword": "Electronics"}} in filters

    def test_brand_filter(self):
        query = SearchQuery(q="test", brand="TechVolt", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        filters = body["query"]["bool"]["filter"]
        assert {"term": {"brand.keyword": "TechVolt"}} in filters

    def test_price_range_filter(self):
        query = SearchQuery(
            q="test", price_min=10, price_max=100,
            page=1, page_size=20, sort_by="relevance"
        )
        body = self.service._build_search_query(query)

        filters = body["query"]["bool"]["filter"]
        price_filter = [f for f in filters if "range" in f and "price" in f["range"]]
        assert len(price_filter) == 1
        assert price_filter[0]["range"]["price"]["gte"] == 10
        assert price_filter[0]["range"]["price"]["lte"] == 100

    def test_rating_filter(self):
        query = SearchQuery(q="test", rating_min=4.0, page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        filters = body["query"]["bool"]["filter"]
        rating_filter = [f for f in filters if "range" in f and "rating" in f.get("range", {})]
        assert len(rating_filter) == 1
        assert rating_filter[0]["range"]["rating"]["gte"] == 4.0

    def test_pagination(self):
        query = SearchQuery(q="test", page=3, page_size=10, sort_by="relevance")
        body = self.service._build_search_query(query)

        assert body["from"] == 20  # (3-1) * 10
        assert body["size"] == 10

    def test_sort_by_price_asc(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="price_asc")
        body = self.service._build_search_query(query)

        assert body["sort"][0] == {"price": "asc"}

    def test_sort_by_price_desc(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="price_desc")
        body = self.service._build_search_query(query)

        assert body["sort"][0] == {"price": "desc"}

    def test_sort_by_rating(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="rating")
        body = self.service._build_search_query(query)

        assert body["sort"][0] == {"rating": "desc"}

    def test_sort_by_newest(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="newest")
        body = self.service._build_search_query(query)

        assert body["sort"][0] == {"created_at": "desc"}

    def test_sort_by_relevance(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        assert body["sort"] == ["_score"]

    def test_aggregations_included(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        assert "categories" in body["aggs"]
        assert "brands" in body["aggs"]
        assert "price_ranges" in body["aggs"]
        assert "avg_rating" in body["aggs"]

    def test_highlight_included(self):
        query = SearchQuery(q="test", page=1, page_size=20, sort_by="relevance")
        body = self.service._build_search_query(query)

        assert "name" in body["highlight"]["fields"]
        assert "description" in body["highlight"]["fields"]

    def test_combined_filters(self):
        query = SearchQuery(
            q="laptop",
            category="Electronics",
            brand="TechVolt",
            price_min=500,
            price_max=2000,
            rating_min=4.0,
            page=1,
            page_size=20,
            sort_by="price_asc",
        )
        body = self.service._build_search_query(query)

        filters = body["query"]["bool"]["filter"]
        assert len(filters) == 4  # category, brand, price, rating


class TestFacetParsing:
    def setup_method(self):
        self.service = SearchService.__new__(SearchService)

    def test_parse_empty_aggregations(self):
        facets = self.service._parse_facets({})
        assert facets.categories == []
        assert facets.brands == []
        assert facets.price_ranges == []
        assert facets.avg_rating is None

    def test_parse_category_buckets(self):
        aggs = {
            "categories": {
                "buckets": [
                    {"key": "Electronics", "doc_count": 50},
                    {"key": "Clothing", "doc_count": 30},
                ]
            }
        }
        facets = self.service._parse_facets(aggs)
        assert len(facets.categories) == 2
        assert facets.categories[0].key == "Electronics"
        assert facets.categories[0].doc_count == 50

    def test_parse_avg_rating(self):
        aggs = {"avg_rating": {"value": 4.2345}}
        facets = self.service._parse_facets(aggs)
        assert facets.avg_rating == 4.23

    def test_filters_zero_count_price_ranges(self):
        aggs = {
            "price_ranges": {
                "buckets": [
                    {"key": "Under $25", "doc_count": 10},
                    {"key": "$25-$50", "doc_count": 0},
                    {"key": "$50-$100", "doc_count": 5},
                ]
            }
        }
        facets = self.service._parse_facets(aggs)
        assert len(facets.price_ranges) == 2
