"""Product-related fixtures for application layer testing.

This module contains fixtures for creating sample product value objects.
"""

from decimal import Decimal

import pytest

from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo, VariantInfo


@pytest.fixture
def sample_product_info():
    """Create sample ProductInfo for testing."""
    return ProductInfo(
        product_id="prod_plat_baja",
        product_name="Plat Baja",
        product_description="High-quality steel plates for construction",
        category="Steel Products",
        variant_count=3,
    )


@pytest.fixture
def sample_variant_info():
    """Create sample VariantInfo for testing."""
    return VariantInfo(
        variant_id="var_001",
        sku="PLT-10MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 10mm x 1200mm x 2400mm",
        price=Decimal("750000"),
        stock_quantity=25,
        stock_unit="lembar",
        specifications={
            "thickness": "10mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )


@pytest.fixture
def sample_product_with_variants(sample_product_info, sample_variant_info):
    """Create sample ProductWithVariantsInfo for testing."""
    variant2 = VariantInfo(
        variant_id="var_002",
        sku="PLT-5MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 5mm x 1200mm x 2400mm",
        price=Decimal("450000"),
        stock_quantity=40,
        stock_unit="lembar",
        specifications={
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )

    return ProductWithVariantsInfo(
        product=sample_product_info, variants=[sample_variant_info, variant2]
    )


__all__ = [
    "sample_product_info",
    "sample_variant_info",
    "sample_product_with_variants",
]
