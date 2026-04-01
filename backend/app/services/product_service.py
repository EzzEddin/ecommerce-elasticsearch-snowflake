import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.product import Category, Inventory, Product
from app.repositories.product_repository import (
    CategoryRepository,
    InventoryRepository,
    ProductRepository,
)
from app.schemas.product import ProductCreate, ProductUpdate


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.inventory_repo = InventoryRepository(db)

    async def list_products(self, page: int = 1, page_size: int = 20):
        products, total = await self.repo.get_all(page=page, page_size=page_size)
        return products, total

    async def get_product(self, product_id: uuid.UUID) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product {product_id} not found")
        return product

    async def create_product(
        self, data: ProductCreate, initial_stock: int = 0
    ) -> Product:
        existing = await self.repo.get_by_sku(data.sku)
        if existing:
            raise ConflictException(f"Product with SKU '{data.sku}' already exists")

        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise NotFoundException(f"Category {data.category_id} not found")

        slug = slugify(data.name)
        existing_slug = await self.repo.get_by_slug(slug)
        if existing_slug:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

        product = Product(
            name=data.name,
            slug=slug,
            description=data.description,
            price=data.price,
            brand=data.brand,
            sku=data.sku,
            image_url=data.image_url,
            category_id=data.category_id,
        )
        product = await self.repo.create(product)

        inventory = Inventory(
            product_id=product.id,
            quantity=initial_stock,
        )
        await self.inventory_repo.create(inventory)

        return await self.repo.get_by_id(product.id)

    async def update_product(
        self, product_id: uuid.UUID, data: ProductUpdate
    ) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product {product_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"]:
            update_data["slug"] = slugify(update_data["name"])

        return await self.repo.update(product, update_data)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(f"Product {product_id} not found")
        await self.repo.delete(product)

    async def get_all_for_indexing(self):
        return await self.repo.get_all_for_indexing()


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def list_categories(self):
        return await self.repo.get_all()

    async def create_category(self, name: str, description: str | None = None):
        slug = slugify(name)
        existing = await self.repo.get_by_slug(slug)
        if existing:
            raise ConflictException(f"Category '{name}' already exists")

        category = Category(name=name, slug=slug, description=description)
        return await self.repo.create(category)
