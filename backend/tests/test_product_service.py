"""
Unit tests for ProductService and CategoryService.
Demonstrates TDD practices with pytest and async testing.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import CategoryService, ProductService, slugify


class TestSlugify:
    def test_basic_text(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        assert slugify("Product #1 (Best!)") == "product-1-best"

    def test_multiple_spaces(self):
        assert slugify("  lots   of   spaces  ") == "lots-of-spaces"

    def test_already_slugified(self):
        assert slugify("already-a-slug") == "already-a-slug"

    def test_mixed_case(self):
        assert slugify("Premium USB-C Hub") == "premium-usb-c-hub"


class TestProductService:
    @pytest_asyncio.fixture
    async def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_list_products_returns_tuple(self, mock_db):
        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_all = AsyncMock(return_value=([], 0))

            service = ProductService(mock_db)
            products, total = await service.list_products(page=1, page_size=20)

            assert products == []
            assert total == 0
            mock_repo.get_all.assert_awaited_once_with(page=1, page_size=20)

    @pytest.mark.asyncio
    async def test_get_product_not_found_raises(self, mock_db):
        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            service = ProductService(mock_db)

            from app.core.exceptions import NotFoundException

            with pytest.raises(NotFoundException):
                await service.get_product(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_product_found(self, mock_db):
        product_id = uuid.uuid4()
        mock_product = MagicMock()
        mock_product.id = product_id

        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_product)

            service = ProductService(mock_db)
            result = await service.get_product(product_id)

            assert result.id == product_id

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku_raises(self, mock_db):
        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_sku = AsyncMock(return_value=MagicMock())

            service = ProductService(mock_db)

            from app.core.exceptions import ConflictException

            data = ProductCreate(
                name="Test Product",
                price=29.99,
                brand="TestBrand",
                sku="EXISTING-SKU",
                category_id=uuid.uuid4(),
            )

            with pytest.raises(ConflictException):
                await service.create_product(data)

    @pytest.mark.asyncio
    async def test_create_product_category_not_found_raises(self, mock_db):
        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo, patch(
            "app.services.product_service.CategoryRepository"
        ) as MockCatRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_sku = AsyncMock(return_value=None)

            mock_cat_repo = MockCatRepo.return_value
            mock_cat_repo.get_by_id = AsyncMock(return_value=None)

            service = ProductService(mock_db)

            from app.core.exceptions import NotFoundException

            data = ProductCreate(
                name="Test Product",
                price=29.99,
                brand="TestBrand",
                sku="NEW-SKU",
                category_id=uuid.uuid4(),
            )

            with pytest.raises(NotFoundException):
                await service.create_product(data)

    @pytest.mark.asyncio
    async def test_delete_product_not_found_raises(self, mock_db):
        with patch(
            "app.services.product_service.ProductRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            service = ProductService(mock_db)

            from app.core.exceptions import NotFoundException

            with pytest.raises(NotFoundException):
                await service.delete_product(uuid.uuid4())


class TestCategoryService:
    @pytest_asyncio.fixture
    async def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_list_categories(self, mock_db):
        with patch(
            "app.services.product_service.CategoryRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_all = AsyncMock(return_value=[])

            service = CategoryService(mock_db)
            result = await service.list_categories()

            assert result == []

    @pytest.mark.asyncio
    async def test_create_category_duplicate_raises(self, mock_db):
        with patch(
            "app.services.product_service.CategoryRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_slug = AsyncMock(return_value=MagicMock())

            service = CategoryService(mock_db)

            from app.core.exceptions import ConflictException

            with pytest.raises(ConflictException):
                await service.create_category("Electronics")
