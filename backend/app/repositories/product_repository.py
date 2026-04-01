import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.product import Category, Inventory, Order, OrderItem, Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self, page: int = 1, page_size: int = 20, is_active: bool = True
    ) -> tuple[Sequence[Product], int]:
        count_q = select(func.count(Product.id)).where(Product.is_active == is_active)
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.is_active == is_active)
            .order_by(Product.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(q)
        return result.unique().scalars().all(), total

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        q = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.id == product_id)
        )
        result = await self.db.execute(q)
        return result.unique().scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        q = select(Product).where(Product.sku == sku)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        q = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.slug == slug)
        )
        result = await self.db.execute(q)
        return result.unique().scalar_one_or_none()

    async def create(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product, ["category", "inventory"])
        return product

    async def update(self, product: Product, data: dict) -> Product:
        for key, value in data.items():
            setattr(product, key, value)
        await self.db.flush()
        await self.db.refresh(product, ["category", "inventory"])
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.flush()

    async def get_all_for_indexing(self) -> Sequence[Product]:
        q = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.is_active == True)
        )
        result = await self.db.execute(q)
        return result.unique().scalars().all()


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[Category]:
        q = select(Category).order_by(Category.name)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        q = select(Category).where(Category.id == category_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        q = select(Category).where(Category.slug == slug)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def create(self, category: Category) -> Category:
        self.db.add(category)
        await self.db.flush()
        return category


class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_product_id(self, product_id: uuid.UUID) -> Inventory | None:
        q = select(Inventory).where(Inventory.product_id == product_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_by_product_id_for_update(self, product_id: uuid.UUID) -> Inventory | None:
        q = (
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def create(self, inventory: Inventory) -> Inventory:
        self.db.add(inventory)
        await self.db.flush()
        return inventory

    async def update_quantity(
        self, inventory: Inventory, quantity: int
    ) -> Inventory:
        inventory.quantity = quantity
        await self.db.flush()
        return inventory


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order, ["items"])
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        q = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        result = await self.db.execute(q)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[Order], int]:
        count_q = select(func.count(Order.id))
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(q)
        return result.unique().scalars().all(), total

    async def get_all_with_items(self) -> Sequence[Order]:
        q = (
            select(Order)
            .options(selectinload(Order.items).joinedload(OrderItem.product))
        )
        result = await self.db.execute(q)
        return result.unique().scalars().all()
