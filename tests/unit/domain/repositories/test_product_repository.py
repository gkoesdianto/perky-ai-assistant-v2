"""
Unit tests for ProductRepository abstract class.
Tests the interface contract and mock implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, List
from decimal import Decimal

from src.domain.repositories.product_repository import ProductRepository
from src.domain.value_objects import ProductInfo, VariantInfo
from src.domain.value_objects.product_with_variants_info import ProductWithVariantsInfo


class MockProductRepository(ProductRepository):
    """Mock implementation of ProductRepository for testing"""

    def __init__(self):
        self.get_product_with_variants_mock = AsyncMock()
        self.get_variant_by_sku_mock = AsyncMock()
        self.search_products_mock = AsyncMock()
        self.get_variants_by_product_mock = AsyncMock()

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        return await self.get_product_with_variants_mock(product_id)

    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        return await self.get_variant_by_sku_mock(sku)

    async def search_products(self, query: str) -> List[ProductInfo]:
        return await self.search_products_mock(query)

    async def get_variants_by_product(self, product_id: str) -> List[VariantInfo]:
        return await self.get_variants_by_product_mock(product_id)


@pytest.fixture
def mock_repository():
    return MockProductRepository()


@pytest.fixture
def sample_product_info():
    return ProductInfo(
        product_id="prod_plat_baja",
        product_name="Plat Baja",
        product_description="High-quality steel plates",
        category="Steel Products",
        variant_count=3,
    )


@pytest.fixture
def sample_variant_info():
    return VariantInfo(
        variant_id="var_001",
        sku="PLT-5MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 5mm x 1200mm x 2400mm",
        price=Decimal("500000"),
        stock_quantity=25,
        stock_unit="lembar",
        specifications={
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )


@pytest.fixture
def sample_product_with_variants(sample_product_info, sample_variant_info):
    variant2 = VariantInfo(
        variant_id="var_002",
        sku="PLT-10MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 10mm x 1200mm x 2400mm",
        price=Decimal("850000"),
        stock_quantity=15,
        stock_unit="lembar",
        specifications={
            "thickness": "10mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )

    return ProductWithVariantsInfo(
        product=sample_product_info, variants=[sample_variant_info, variant2]
    )


class TestProductRepository:
    """Test suite for ProductRepository interface"""

    @pytest.mark.asyncio
    async def test_get_product_with_variants(
        self, mock_repository, sample_product_with_variants
    ):
        mock_repository.get_product_with_variants_mock.return_value = (
            sample_product_with_variants
        )

        result = await mock_repository.get_product_with_variants("prod_plat_baja")

        assert result == sample_product_with_variants
        assert result.product.product_id == "prod_plat_baja"
        assert len(result.variants) == 2
        mock_repository.get_product_with_variants_mock.assert_called_once_with(
            "prod_plat_baja"
        )

    @pytest.mark.asyncio
    async def test_get_product_with_variants_not_found(self, mock_repository):
        mock_repository.get_product_with_variants_mock.return_value = None

        result = await mock_repository.get_product_with_variants("non_existent")

        assert result is None
        mock_repository.get_product_with_variants_mock.assert_called_once_with(
            "non_existent"
        )

    @pytest.mark.asyncio
    async def test_get_variant_by_sku(self, mock_repository, sample_variant_info):
        mock_repository.get_variant_by_sku_mock.return_value = sample_variant_info

        result = await mock_repository.get_variant_by_sku("PLT-5MM-001")

        assert result == sample_variant_info
        assert result.sku == "PLT-5MM-001"
        mock_repository.get_variant_by_sku_mock.assert_called_once_with("PLT-5MM-001")

    @pytest.mark.asyncio
    async def test_get_variant_by_sku_not_found(self, mock_repository):
        mock_repository.get_variant_by_sku_mock.return_value = None

        result = await mock_repository.get_variant_by_sku("NON-EXISTENT-SKU")

        assert result is None
        mock_repository.get_variant_by_sku_mock.assert_called_once_with(
            "NON-EXISTENT-SKU"
        )

    @pytest.mark.asyncio
    async def test_search_products(self, mock_repository, sample_product_info):
        products = [sample_product_info]
        mock_repository.search_products_mock.return_value = products

        result = await mock_repository.search_products("plat baja")

        assert result == products
        assert len(result) == 1
        assert result[0].product_name == "Plat Baja"
        mock_repository.search_products_mock.assert_called_once_with("plat baja")

    @pytest.mark.asyncio
    async def test_search_products_empty_results(self, mock_repository):
        mock_repository.search_products_mock.return_value = []

        result = await mock_repository.search_products("non existent product")

        assert result == []
        mock_repository.search_products_mock.assert_called_once_with(
            "non existent product"
        )

    @pytest.mark.asyncio
    async def test_get_variants_by_product(self, mock_repository, sample_variant_info):
        variant2 = VariantInfo(
            variant_id="var_002",
            sku="PLT-10MM-001",
            product_id="prod_plat_baja",
            variant_name="Plat Baja 10mm x 1200mm x 2400mm",
            price=Decimal("850000"),
            stock_quantity=15,
            stock_unit="lembar",
            specifications={
                "thickness": "10mm",
                "width": "1200mm",
                "length": "2400mm",
                "grade": "SS400",
            },
        )

        variants = [sample_variant_info, variant2]
        mock_repository.get_variants_by_product_mock.return_value = variants

        result = await mock_repository.get_variants_by_product("prod_plat_baja")

        assert result == variants
        assert len(result) == 2
        assert all(v.product_id == "prod_plat_baja" for v in result)
        mock_repository.get_variants_by_product_mock.assert_called_once_with(
            "prod_plat_baja"
        )

    @pytest.mark.asyncio
    async def test_get_variants_by_product_empty(self, mock_repository):
        mock_repository.get_variants_by_product_mock.return_value = []

        result = await mock_repository.get_variants_by_product("non_existent_product")

        assert result == []
        mock_repository.get_variants_by_product_mock.assert_called_once_with(
            "non_existent_product"
        )


class TestProductRepositoryInterface:
    """Test that ProductRepository is abstract and cannot be instantiated directly"""

    def test_cannot_instantiate_abstract_repository(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProductRepository()

    def test_repository_has_required_abstract_methods(self):
        abstract_methods = ProductRepository.__abstractmethods__

        assert "get_product_with_variants" in abstract_methods
        assert "get_variant_by_sku" in abstract_methods
        assert "search_products" in abstract_methods
        assert "get_variants_by_product" in abstract_methods
