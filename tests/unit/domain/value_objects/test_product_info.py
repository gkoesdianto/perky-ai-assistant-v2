"""Unit tests for ProductInfo value object focusing on business logic and Indonesian market."""

import pytest
from typing import Dict, Any

from src.domain.value_objects.product_info import ProductInfo
from tests.unit.domain.factories import ProductInfoFactory


class TestProductInfoCreation:
    """Test suite for ProductInfo creation and initialization."""

    def test_required_fields(self):
        """Test creation with only SKU and name."""
        product = ProductInfo(sku="TEST-001", name="Test Product")

        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.description is None
        assert product.price is None
        assert product.stock is None
        assert product.unit == "lembar"
        assert product.specifications == {}
        assert product.source == "pim"

    def test_all_fields(self):
        """Test with all fields populated."""
        specs = {
            "thickness": "10mm",
            "width": "1500mm",
            "length": "3000mm",
            "weight": "117.75kg",
        }

        product = ProductInfo(
            sku="STEEL-001",
            name="Plat Baja SS400",
            description="Plat baja kualitas tinggi untuk konstruksi",
            price=250000.0,
            stock=50,
            unit="lembar",
            specifications=specs,
            source="pim",
        )

        assert product.sku == "STEEL-001"
        assert product.name == "Plat Baja SS400"
        assert product.description == "Plat baja kualitas tinggi untuk konstruksi"
        assert product.price == 250000.0
        assert product.stock == 50
        assert product.unit == "lembar"
        assert product.specifications == specs
        assert product.source == "pim"

    def test_optional_fields_none(self):
        """Verify optional fields default to None."""
        product = ProductInfo(sku="MIN-001", name="Minimal Product")

        assert product.description is None
        assert product.price is None
        assert product.stock is None


class TestProductInfoDefaults:
    """Test suite for ProductInfo default values."""

    def test_default_unit(self):
        """Verify unit defaults to 'lembar' (Indonesian)."""
        product = ProductInfo(sku="DEFAULT-001", name="Default Unit Product")
        assert product.unit == "lembar"

        product_explicit = ProductInfo(
            sku="EXPLICIT-001", name="Explicit Unit Product", unit="lembar"
        )
        assert product_explicit.unit == "lembar"

    def test_source_values(self):
        """Test both valid source values (pim, cache)."""
        product_pim = ProductInfo(sku="PIM-001", name="PIM Product", source="pim")
        assert product_pim.source == "pim"

        product_cache = ProductInfo(
            sku="CACHE-001", name="Cache Product", source="cache"
        )
        assert product_cache.source == "cache"

    def test_specifications_dict(self):
        """Test specifications storage for steel products."""
        steel_specs = {
            "grade": "SS400",
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "tensile_strength": "400-510 N/mm²",
            "yield_strength": "245 N/mm²",
        }

        product = ProductInfo(
            sku="STEEL-002", name="Plat Baja SS400 5mm", specifications=steel_specs
        )

        assert product.specifications == steel_specs
        assert product.specifications["grade"] == "SS400"
        assert product.specifications["thickness"] == "5mm"
        assert len(product.specifications) == 6


class TestIndonesianProductData:
    """Test suite for Indonesian steel product data."""

    def test_indonesian_product_data(self, steel_product):
        """Test with real Indonesian steel product data."""
        assert steel_product.name == "Plat Baja 5mm"
        assert steel_product.unit == "lembar"
        assert steel_product.price == 150000.0
        assert steel_product.stock == 100
        assert steel_product.specifications["thickness"] == "5mm"
        assert steel_product.specifications["width"] == "1200mm"
        assert steel_product.specifications["length"] == "2400mm"

    def test_indonesian_units(self):
        """Test various Indonesian units for steel products."""
        units = ["lembar", "batang", "kg", "meter", "roll"]

        for unit in units:
            product = ProductInfo(
                sku=f"UNIT-{unit.upper()}",
                name=f"Product dengan unit {unit}",
                unit=unit,
            )
            assert product.unit == unit

    def test_realistic_steel_product_specifications(self):
        """Test realistic specifications for Indonesian steel products."""
        products = [
            {
                "sku": "PLATE-SS400-10",
                "name": "Plat Baja SS400 10mm",
                "specifications": {
                    "grade": "SS400",
                    "thickness": "10mm",
                    "width": "1500mm",
                    "length": "6000mm",
                    "weight_per_unit": "706.5kg",
                    "standard": "JIS G3101",
                },
            },
            {
                "sku": "BEAM-H-200",
                "name": "H-Beam 200x200",
                "specifications": {
                    "type": "H-Beam",
                    "height": "200mm",
                    "width": "200mm",
                    "web_thickness": "8mm",
                    "flange_thickness": "12mm",
                    "length": "12000mm",
                },
            },
            {
                "sku": "PIPE-SCH40-4",
                "name": "Pipa Baja SCH40 4 inch",
                "specifications": {
                    "schedule": "40",
                    "diameter": "4 inch",
                    "wall_thickness": "6.02mm",
                    "length": "6000mm",
                    "standard": "ASTM A53",
                },
            },
        ]

        for product_data in products:
            product = ProductInfo(**product_data)
            assert product.sku == product_data["sku"]
            assert product.name == product_data["name"]
            assert product.specifications == product_data["specifications"]


class TestProductInfoFactory:
    """Test suite for ProductInfoFactory methods."""

    def test_factory_create_minimal(self, minimal_product):
        """Test factory creation with minimal fields."""
        assert minimal_product.sku.startswith("MIN-")
        assert minimal_product.name == "Minimal Product"
        assert minimal_product.unit == "lembar"
        assert minimal_product.source == "pim"

    def test_factory_create_complete(self, complete_product):
        """Test factory creation with all fields."""
        assert complete_product.sku.startswith("FULL-")
        assert complete_product.name == "Plat Baja SS400"
        assert complete_product.description is not None
        assert complete_product.price == 250000.0
        assert complete_product.stock == 50
        assert complete_product.specifications["grade"] == "SS400"

    def test_factory_create_from_cache(self):
        """Test factory creation for cached products."""
        cached = ProductInfoFactory.create_from_cache()
        assert cached.source == "cache"
        assert cached.sku.startswith("CACHE-")

    def test_factory_override_defaults(self):
        """Test factory with custom values overriding defaults."""
        custom = ProductInfoFactory.create_steel_product(
            name="Custom Steel Product", price=300000.0, stock=200
        )
        assert custom.name == "Custom Steel Product"
        assert custom.price == 300000.0
        assert custom.stock == 200
        assert custom.unit == "lembar"


class TestProductInfoEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_empty_specifications(self):
        """Test product with empty specifications dict."""
        product = ProductInfo(
            sku="EMPTY-SPEC", name="No Specifications", specifications={}
        )
        assert product.specifications == {}
        assert len(product.specifications) == 0

    def test_price_boundaries(self):
        """Test price field with various values."""
        product_zero = ProductInfo(sku="ZERO", name="Free Product", price=0.0)
        assert product_zero.price == 0.0

        product_high = ProductInfo(sku="HIGH", name="Expensive", price=999999999.99)
        assert product_high.price == 999999999.99

    def test_stock_boundaries(self):
        """Test stock field with various values."""
        product_zero = ProductInfo(sku="NO-STOCK", name="Out of Stock", stock=0)
        assert product_zero.stock == 0

        product_high = ProductInfo(sku="HIGH-STOCK", name="Abundant", stock=999999)
        assert product_high.stock == 999999

    def test_model_serialization(self):
        """Test model_dump() and model_dump_json() for our use cases."""
        product = ProductInfoFactory.create_steel_product()

        dict_data = product.model_dump()
        assert dict_data["sku"] == product.sku
        assert dict_data["name"] == product.name
        assert dict_data["unit"] == "lembar"
        assert dict_data["source"] == "pim"

        json_data = product.model_dump_json()
        assert product.sku in json_data
        assert "lembar" in json_data
