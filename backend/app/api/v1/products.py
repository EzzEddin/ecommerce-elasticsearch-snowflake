import math
import uuid

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.schemas.product import (
    CategoryCreate,
    CategoryResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import CategoryService, ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = ProductService(db)
    products, total = await service.list_products(page=page, page_size=page_size)
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(db: DBSession, product_id: uuid.UUID):
    service = ProductService(db)
    return await service.get_product(product_id)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    db: DBSession,
    data: ProductCreate,
    initial_stock: int = Query(0, ge=0),
):
    service = ProductService(db)
    return await service.create_product(data, initial_stock=initial_stock)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    db: DBSession, product_id: uuid.UUID, data: ProductUpdate
):
    service = ProductService(db)
    return await service.update_product(product_id, data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(db: DBSession, product_id: uuid.UUID):
    service = ProductService(db)
    await service.delete_product(product_id)


# --- Category endpoints ---

category_router = APIRouter(prefix="/categories", tags=["Categories"])


@category_router.get("", response_model=list[CategoryResponse])
async def list_categories(db: DBSession):
    service = CategoryService(db)
    return await service.list_categories()


@category_router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(db: DBSession, data: CategoryCreate):
    service = CategoryService(db)
    return await service.create_category(data.name, data.description)
