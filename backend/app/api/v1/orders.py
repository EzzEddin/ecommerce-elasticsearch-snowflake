import math
import uuid

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.schemas.product import OrderCreate, OrderListResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(db: DBSession, data: OrderCreate):
    service = OrderService(db)
    return await service.create_order(data)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(db: DBSession, order_id: uuid.UUID):
    service = OrderService(db)
    return await service.get_order(order_id)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = OrderService(db)
    orders, total = await service.list_orders(page=page, page_size=page_size)
    return OrderListResponse(
        items=orders,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
