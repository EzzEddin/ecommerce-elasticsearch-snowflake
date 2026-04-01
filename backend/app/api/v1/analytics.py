from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.schemas.product import (
    CategoryPerformanceResponse,
    RevenueResponse,
    TopProductsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.order_service import OrderService
from app.services.product_service import ProductService

router = APIRouter(prefix="/analytics", tags=["Analytics (Snowflake)"])


@router.get("/revenue", response_model=RevenueResponse)
async def get_revenue(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
):
    service = AnalyticsService()
    return await service.get_revenue(
        period=period, from_date=from_date, to_date=to_date
    )


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
):
    service = AnalyticsService()
    return await service.get_top_products(limit=limit)


@router.get("/categories", response_model=CategoryPerformanceResponse)
async def get_category_performance():
    service = AnalyticsService()
    return await service.get_category_performance()


@router.post("/sync", status_code=200)
async def sync_data_to_snowflake(db: DBSession):
    analytics = AnalyticsService()
    product_service = ProductService(db)
    order_service = OrderService(db)

    await analytics.setup_snowflake_schema()

    products = await product_service.get_all_for_indexing()
    products_synced = await analytics.sync_products_to_snowflake(products)

    orders = await order_service.get_all_orders_with_items()
    items_synced = await analytics.sync_orders_to_snowflake(orders)

    return {
        "message": "Data synced to Snowflake",
        "products_synced": products_synced,
        "order_items_synced": items_synced,
    }


@router.post("/setup", status_code=200)
async def setup_snowflake():
    service = AnalyticsService()
    await service.setup_snowflake_schema()
    return {"message": "Snowflake schema created successfully"}
