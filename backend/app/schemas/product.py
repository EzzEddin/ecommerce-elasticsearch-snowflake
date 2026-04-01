from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# --- Category Schemas ---

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: UUID
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Product Schemas ---

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    brand: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=50)
    image_url: str | None = None
    category_id: UUID


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    brand: str | None = Field(None, min_length=1, max_length=100)
    image_url: str | None = None
    category_id: UUID | None = None
    is_active: bool | None = None


class InventoryInfo(BaseModel):
    quantity: int
    reserved: int
    available: int
    reorder_level: int

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(ProductBase):
    id: UUID
    slug: str
    rating: float
    review_count: int
    is_active: bool
    category: CategoryResponse
    inventory: InventoryInfo | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


# --- Order Schemas ---

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_email: str = Field(..., min_length=5)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: UUID
    customer_email: str
    status: str
    total_amount: float
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


# --- Search Schemas ---

class SearchQuery(BaseModel):
    q: str = Field("", max_length=500)
    category: str | None = None
    brand: str | None = None
    price_min: float | None = Field(None, ge=0)
    price_max: float | None = Field(None, ge=0)
    rating_min: float | None = Field(None, ge=0, le=5)
    sort_by: str = Field("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SearchHit(BaseModel):
    id: str
    name: str
    description: str | None = None
    price: float
    brand: str
    category: str
    rating: float
    image_url: str | None = None
    highlight: dict | None = None
    score: float | None = None


class FacetBucket(BaseModel):
    key: str
    doc_count: int


class SearchFacets(BaseModel):
    categories: list[FacetBucket] = []
    brands: list[FacetBucket] = []
    price_ranges: list[FacetBucket] = []
    avg_rating: float | None = None


class SearchResponse(BaseModel):
    hits: list[SearchHit]
    total: int
    facets: SearchFacets
    page: int
    page_size: int
    pages: int
    query: str


class AutocompleteResponse(BaseModel):
    suggestions: list[str]


# --- Analytics Schemas ---

class RevenueDataPoint(BaseModel):
    period: str
    revenue: float
    order_count: int


class RevenueResponse(BaseModel):
    data: list[RevenueDataPoint]
    total_revenue: float
    total_orders: int
    period_type: str


class TopProductItem(BaseModel):
    product_name: str
    category: str
    total_sold: int
    total_revenue: float


class TopProductsResponse(BaseModel):
    products: list[TopProductItem]
    period: str | None = None


class CategoryPerformanceItem(BaseModel):
    category: str
    total_revenue: float
    total_sold: int
    avg_order_value: float


class CategoryPerformanceResponse(BaseModel):
    categories: list[CategoryPerformanceItem]
