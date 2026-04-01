import asyncio
import logging
import time
from datetime import date, datetime
from typing import Any

import snowflake.connector

from app.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.core.snowflake import get_snowflake_connection
from app.schemas.product import (
    CategoryPerformanceItem,
    CategoryPerformanceResponse,
    RevenueDataPoint,
    RevenueResponse,
    TopProductItem,
    TopProductsResponse,
)

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60
_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[0]) < CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic(), value)


def _cache_clear() -> None:
    _cache.clear()


class AnalyticsService:
    def _get_connection(self):
        try:
            return get_snowflake_connection()
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise ServiceUnavailableException(
                "Analytics service is temporarily unavailable. "
                "Please ensure Snowflake credentials are configured."
            )

    def _sync_setup_snowflake_schema(self) -> None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}"
            )
            cursor.execute(
                f"USE DATABASE {settings.snowflake_database}"
            )
            cursor.execute(
                f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}"
            )
            cursor.execute(
                f"USE SCHEMA {settings.snowflake_schema}"
            )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS PRODUCT_DIMENSIONS (
                    product_id VARCHAR(36) PRIMARY KEY,
                    product_name VARCHAR(255),
                    brand VARCHAR(100),
                    category VARCHAR(100),
                    price FLOAT,
                    sku VARCHAR(50),
                    created_at TIMESTAMP_NTZ
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS SALES_FACTS (
                    order_id VARCHAR(36),
                    order_item_id VARCHAR(36) PRIMARY KEY,
                    product_id VARCHAR(36),
                    customer_email VARCHAR(255),
                    quantity INTEGER,
                    unit_price FLOAT,
                    total_price FLOAT,
                    order_status VARCHAR(20),
                    order_date TIMESTAMP_NTZ,
                    FOREIGN KEY (product_id) REFERENCES PRODUCT_DIMENSIONS(product_id)
                )
            """)

            cursor.execute("""
                CREATE OR REPLACE VIEW DAILY_REVENUE AS
                SELECT
                    DATE_TRUNC('DAY', order_date) AS day,
                    SUM(total_price) AS revenue,
                    COUNT(DISTINCT order_id) AS order_count
                FROM SALES_FACTS
                WHERE order_status != 'cancelled'
                GROUP BY DATE_TRUNC('DAY', order_date)
                ORDER BY day
            """)

            conn.commit()
            logger.info("Snowflake schema setup complete")
        finally:
            conn.close()

    async def setup_snowflake_schema(self) -> None:
        await asyncio.to_thread(self._sync_setup_snowflake_schema)

    def _sync_products_to_snowflake(self, rows: list[tuple]) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

            cursor.execute("DELETE FROM PRODUCT_DIMENSIONS")

            if rows:
                cursor.executemany(
                    """
                    INSERT INTO PRODUCT_DIMENSIONS
                    (product_id, product_name, brand, category, price, sku, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )

            conn.commit()
            logger.info(f"Synced {len(rows)} products to Snowflake")
            return len(rows)
        finally:
            conn.close()

    async def sync_products_to_snowflake(self, products: list[Any]) -> int:
        rows = [
            (
                str(p.id),
                p.name,
                p.brand,
                p.category.name if p.category else "",
                p.price,
                p.sku,
                p.created_at,
            )
            for p in products
        ]
        result = await asyncio.to_thread(self._sync_products_to_snowflake, rows)
        _cache_clear()
        return result

    def _sync_orders_to_snowflake(self, rows: list[tuple]) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

            cursor.execute("DELETE FROM SALES_FACTS")

            if rows:
                cursor.executemany(
                    """
                    INSERT INTO SALES_FACTS
                    (order_id, order_item_id, product_id, customer_email,
                     quantity, unit_price, total_price, order_status, order_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )

            conn.commit()
            logger.info(f"Synced {len(rows)} order items to Snowflake")
            return len(rows)
        finally:
            conn.close()

    async def sync_orders_to_snowflake(self, orders: list[Any]) -> int:
        rows = [
            (
                str(order.id),
                str(item.id),
                str(item.product_id),
                order.customer_email,
                item.quantity,
                item.unit_price,
                round(item.quantity * item.unit_price, 2),
                order.status,
                order.created_at,
            )
            for order in orders
            for item in order.items
        ]
        result = await asyncio.to_thread(self._sync_orders_to_snowflake, rows)
        _cache_clear()
        return result

    def _sync_get_revenue(
        self,
        period: str,
        from_date: date | None,
        to_date: date | None,
    ) -> RevenueResponse:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

            trunc_map = {
                "daily": "DAY",
                "weekly": "WEEK",
                "monthly": "MONTH",
            }
            trunc = trunc_map.get(period, "DAY")

            where_clauses = ["order_status != 'cancelled'"]
            params = []
            if from_date:
                where_clauses.append("order_date >= %s")
                params.append(datetime.combine(from_date, datetime.min.time()))
            if to_date:
                where_clauses.append("order_date <= %s")
                params.append(datetime.combine(to_date, datetime.max.time()))

            where_sql = " AND ".join(where_clauses)

            cursor.execute(
                f"""
                SELECT
                    DATE_TRUNC('{trunc}', order_date) AS period,
                    SUM(total_price) AS revenue,
                    COUNT(DISTINCT order_id) AS order_count
                FROM SALES_FACTS
                WHERE {where_sql}
                GROUP BY DATE_TRUNC('{trunc}', order_date)
                ORDER BY period
                """,
                params,
            )

            rows = cursor.fetchall()
            data = [
                RevenueDataPoint(
                    period=str(row[0].date()) if row[0] else "",
                    revenue=round(float(row[1]), 2),
                    order_count=int(row[2]),
                )
                for row in rows
            ]

            total_revenue = sum(d.revenue for d in data)
            total_orders = sum(d.order_count for d in data)

            return RevenueResponse(
                data=data,
                total_revenue=round(total_revenue, 2),
                total_orders=total_orders,
                period_type=period,
            )
        finally:
            conn.close()

    async def get_revenue(
        self,
        period: str = "daily",
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> RevenueResponse:
        cache_key = f"revenue:{period}:{from_date}:{to_date}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        result = await asyncio.to_thread(
            self._sync_get_revenue, period, from_date, to_date
        )
        _cache_set(cache_key, result)
        return result

    def _sync_get_top_products(self, limit: int) -> TopProductsResponse:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

            cursor.execute(
                """
                SELECT
                    p.product_name,
                    p.category,
                    SUM(s.quantity) AS total_sold,
                    SUM(s.total_price) AS total_revenue
                FROM SALES_FACTS s
                JOIN PRODUCT_DIMENSIONS p ON s.product_id = p.product_id
                WHERE s.order_status != 'cancelled'
                GROUP BY p.product_name, p.category
                ORDER BY total_revenue DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            products = [
                TopProductItem(
                    product_name=row[0],
                    category=row[1],
                    total_sold=int(row[2]),
                    total_revenue=round(float(row[3]), 2),
                )
                for row in rows
            ]

            return TopProductsResponse(products=products)
        finally:
            conn.close()

    async def get_top_products(self, limit: int = 10) -> TopProductsResponse:
        cache_key = f"top_products:{limit}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        result = await asyncio.to_thread(self._sync_get_top_products, limit)
        _cache_set(cache_key, result)
        return result

    def _sync_get_category_performance(self) -> CategoryPerformanceResponse:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

            cursor.execute("""
                SELECT
                    p.category,
                    SUM(s.total_price) AS total_revenue,
                    SUM(s.quantity) AS total_sold,
                    AVG(order_totals.order_total) AS avg_order_value
                FROM SALES_FACTS s
                JOIN PRODUCT_DIMENSIONS p ON s.product_id = p.product_id
                JOIN (
                    SELECT order_id, SUM(total_price) AS order_total
                    FROM SALES_FACTS
                    WHERE order_status != 'cancelled'
                    GROUP BY order_id
                ) order_totals ON s.order_id = order_totals.order_id
                WHERE s.order_status != 'cancelled'
                GROUP BY p.category
                ORDER BY total_revenue DESC
            """)

            rows = cursor.fetchall()
            categories = [
                CategoryPerformanceItem(
                    category=row[0],
                    total_revenue=round(float(row[1]), 2),
                    total_sold=int(row[2]),
                    avg_order_value=round(float(row[3]), 2),
                )
                for row in rows
            ]

            return CategoryPerformanceResponse(categories=categories)
        finally:
            conn.close()

    async def get_category_performance(self) -> CategoryPerformanceResponse:
        cache_key = "category_performance"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        result = await asyncio.to_thread(self._sync_get_category_performance)
        _cache_set(cache_key, result)
        return result
