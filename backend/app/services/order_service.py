import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.product import Order, OrderItem
from app.repositories.product_repository import (
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)
from app.schemas.product import OrderCreate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.inventory_repo = InventoryRepository(db)

    async def create_order(self, data: OrderCreate) -> Order:
        order_items = []
        total = 0.0

        for item_data in data.items:
            product = await self.product_repo.get_by_id(item_data.product_id)
            if not product:
                raise NotFoundException(
                    f"Product {item_data.product_id} not found"
                )

            inventory = await self.inventory_repo.get_by_product_id_for_update(
                item_data.product_id
            )

            if inventory and inventory.available < item_data.quantity:
                raise BadRequestException(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {inventory.available}, requested: {item_data.quantity}"
                )

            order_item = OrderItem(
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=product.price,
            )
            order_items.append(order_item)
            total += product.price * item_data.quantity

            if inventory:
                inventory.reserved += item_data.quantity

        order = Order(
            customer_email=data.customer_email,
            total_amount=round(total, 2),
            items=order_items,
        )
        return await self.order_repo.create(order)

    async def get_order(self, order_id: uuid.UUID) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(f"Order {order_id} not found")
        return order

    async def list_orders(self, page: int = 1, page_size: int = 20):
        return await self.order_repo.get_all(page=page, page_size=page_size)

    async def get_all_orders_with_items(self):
        return await self.order_repo.get_all_with_items()
