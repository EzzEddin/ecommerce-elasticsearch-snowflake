import logging

from elasticsearch import AsyncElasticsearch, NotFoundError

from app.config import settings
from app.schemas.product import (
    AutocompleteResponse,
    FacetBucket,
    SearchFacets,
    SearchHit,
    SearchQuery,
    SearchResponse,
)

logger = logging.getLogger(__name__)

PRODUCT_INDEX = f"{settings.elasticsearch_index_prefix}_products"

PRODUCT_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase"],
                },
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                },
            },
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"],
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                        "search_analyzer": "search_analyzer",
                    },
                    "keyword": {"type": "keyword"},
                },
            },
            "description": {"type": "text", "analyzer": "standard"},
            "price": {"type": "float"},
            "brand": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "category": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "category_slug": {"type": "keyword"},
            "sku": {"type": "keyword"},
            "rating": {"type": "float"},
            "review_count": {"type": "integer"},
            "image_url": {"type": "keyword", "index": False},
            "in_stock": {"type": "boolean"},
            "created_at": {"type": "date"},
        }
    },
}


class SearchService:
    def __init__(self, es: AsyncElasticsearch):
        self.es = es
        self.index = PRODUCT_INDEX

    async def create_index(self) -> None:
        exists = await self.es.indices.exists(index=self.index)
        if not exists:
            await self.es.indices.create(
                index=self.index, body=PRODUCT_INDEX_MAPPING
            )
            logger.info(f"Created Elasticsearch index: {self.index}")
        else:
            logger.info(f"Index {self.index} already exists")

    async def delete_index(self) -> None:
        try:
            await self.es.indices.delete(index=self.index)
            logger.info(f"Deleted Elasticsearch index: {self.index}")
        except NotFoundError:
            pass

    async def index_product(self, product) -> None:
        doc = self._product_to_doc(product)
        await self.es.index(index=self.index, id=str(product.id), document=doc)

    async def bulk_index_products(self, products) -> int:
        if not products:
            return 0

        operations = []
        for product in products:
            operations.append({"index": {"_index": self.index, "_id": str(product.id)}})
            operations.append(self._product_to_doc(product))

        result = await self.es.bulk(operations=operations, refresh=True)
        indexed = sum(
            1 for item in result["items"] if item["index"]["status"] in (200, 201)
        )
        logger.info(f"Bulk indexed {indexed}/{len(products)} products")
        return indexed

    async def delete_product(self, product_id: str) -> None:
        try:
            await self.es.delete(index=self.index, id=product_id, refresh=True)
        except NotFoundError:
            pass

    async def search(self, query: SearchQuery) -> SearchResponse:
        body = self._build_search_query(query)
        result = await self.es.search(index=self.index, body=body)

        hits = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            highlight = hit.get("highlight", None)
            hits.append(
                SearchHit(
                    id=hit["_id"],
                    name=source["name"],
                    description=source.get("description"),
                    price=source["price"],
                    brand=source["brand"],
                    category=source["category"],
                    rating=source.get("rating", 0),
                    image_url=source.get("image_url"),
                    highlight=highlight,
                    score=hit["_score"],
                )
            )

        total = result["hits"]["total"]["value"]
        facets = self._parse_facets(result.get("aggregations", {}))
        pages = max(1, (total + query.page_size - 1) // query.page_size)

        return SearchResponse(
            hits=hits,
            total=total,
            facets=facets,
            page=query.page,
            page_size=query.page_size,
            pages=pages,
            query=query.q,
        )

    async def autocomplete(self, query: str, size: int = 10) -> AutocompleteResponse:
        body = {
            "size": size,
            "query": {
                "match": {
                    "name.autocomplete": {
                        "query": query,
                        "operator": "and",
                    }
                }
            },
            "_source": ["name"],
        }
        result = await self.es.search(index=self.index, body=body)
        suggestions = list(
            dict.fromkeys(hit["_source"]["name"] for hit in result["hits"]["hits"])
        )
        return AutocompleteResponse(suggestions=suggestions)

    def _product_to_doc(self, product) -> dict:
        return {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "brand": product.brand,
            "category": product.category.name if product.category else "",
            "category_slug": product.category.slug if product.category else "",
            "sku": product.sku,
            "rating": product.rating,
            "review_count": product.review_count,
            "image_url": product.image_url,
            "in_stock": (
                product.inventory.available > 0 if product.inventory else False
            ),
            "created_at": (
                product.created_at.isoformat() if product.created_at else None
            ),
        }

    def _build_search_query(self, query: SearchQuery) -> dict:
        must = []
        filter_clauses = []

        if query.q:
            must.append(
                {
                    "multi_match": {
                        "query": query.q,
                        "fields": ["name^3", "description", "brand^2"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            )
        else:
            must.append({"match_all": {}})

        if query.category:
            filter_clauses.append({"term": {"category.keyword": query.category}})
        if query.brand:
            filter_clauses.append({"term": {"brand.keyword": query.brand}})
        if query.price_min is not None or query.price_max is not None:
            price_range = {}
            if query.price_min is not None:
                price_range["gte"] = query.price_min
            if query.price_max is not None:
                price_range["lte"] = query.price_max
            filter_clauses.append({"range": {"price": price_range}})
        if query.rating_min is not None:
            filter_clauses.append({"range": {"rating": {"gte": query.rating_min}}})

        sort = self._get_sort(query.sort_by)

        body = {
            "query": {"bool": {"must": must, "filter": filter_clauses}},
            "from": (query.page - 1) * query.page_size,
            "size": query.page_size,
            "sort": sort,
            "highlight": {
                "fields": {
                    "name": {"number_of_fragments": 0},
                    "description": {"fragment_size": 150, "number_of_fragments": 3},
                }
            },
            "aggs": {
                "categories": {"terms": {"field": "category.keyword", "size": 50}},
                "brands": {"terms": {"field": "brand.keyword", "size": 50}},
                "price_ranges": {
                    "range": {
                        "field": "price",
                        "ranges": [
                            {"key": "Under $25", "to": 25},
                            {"key": "$25-$50", "from": 25, "to": 50},
                            {"key": "$50-$100", "from": 50, "to": 100},
                            {"key": "$100-$200", "from": 100, "to": 200},
                            {"key": "$200+", "from": 200},
                        ],
                    }
                },
                "avg_rating": {"avg": {"field": "rating"}},
            },
        }
        return body

    def _get_sort(self, sort_by: str) -> list:
        if sort_by == "price_asc":
            return [{"price": "asc"}, "_score"]
        elif sort_by == "price_desc":
            return [{"price": "desc"}, "_score"]
        elif sort_by == "rating":
            return [{"rating": "desc"}, "_score"]
        elif sort_by == "newest":
            return [{"created_at": "desc"}, "_score"]
        else:
            return ["_score"]

    def _parse_facets(self, aggs: dict) -> SearchFacets:
        categories = [
            FacetBucket(key=b["key"], doc_count=b["doc_count"])
            for b in aggs.get("categories", {}).get("buckets", [])
        ]
        brands = [
            FacetBucket(key=b["key"], doc_count=b["doc_count"])
            for b in aggs.get("brands", {}).get("buckets", [])
        ]
        price_ranges = [
            FacetBucket(key=b["key"], doc_count=b["doc_count"])
            for b in aggs.get("price_ranges", {}).get("buckets", [])
            if b["doc_count"] > 0
        ]
        avg_rating = aggs.get("avg_rating", {}).get("value")

        return SearchFacets(
            categories=categories,
            brands=brands,
            price_ranges=price_ranges,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
        )
