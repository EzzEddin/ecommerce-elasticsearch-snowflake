from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, ESClient
from app.schemas.product import AutocompleteResponse, SearchQuery, SearchResponse
from app.services.product_service import ProductService
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def search_products(
    es: ESClient,
    q: str = Query("", max_length=500),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    price_min: float | None = Query(None, ge=0),
    price_max: float | None = Query(None, ge=0),
    rating_min: float | None = Query(None, ge=0, le=5),
    sort_by: str = Query("relevance"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    search_query = SearchQuery(
        q=q,
        category=category,
        brand=brand,
        price_min=price_min,
        price_max=price_max,
        rating_min=rating_min,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    service = SearchService(es)
    return await service.search(search_query)


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    es: ESClient,
    q: str = Query(..., min_length=1, max_length=100),
    size: int = Query(10, ge=1, le=20),
):
    service = SearchService(es)
    return await service.autocomplete(q, size=size)


@router.post("/reindex", status_code=200)
async def reindex_products(db: DBSession, es: ESClient):
    search_service = SearchService(es)
    product_service = ProductService(db)

    await search_service.delete_index()
    await search_service.create_index()

    products = await product_service.get_all_for_indexing()
    indexed = await search_service.bulk_index_products(products)

    return {"message": f"Reindexed {indexed} products", "total": indexed}
