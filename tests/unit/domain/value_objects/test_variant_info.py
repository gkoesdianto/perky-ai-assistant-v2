"""Unit tests for VariantInfo value object for Indonesian market."""

import pytest
from decimal import Decimal
from typing import Dict

from src.domain.value_objects.variant_info import VariantInfo
from tests.unit.domain.factories import VariantInfoFactory


class TestVariantInfoCreation:
    """Test suite for VariantInfo creation and initialization."""

    def test_required_fields_only(self):
        """Test creation with minimal required fields."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test Variant",
            price=Decimal("100000"),
            stock_quantity=10,
        )

        assert variant.variant_id == "var_001"
        assert variant.sku == "TEST-001"
        assert variant.product_id == "prod_001"
        assert variant.variant_name == "Test Variant"
        assert variant.price == Decimal("100000")
        assert variant.stock_quantity == 10
        assert variant.stock_unit == "lembar"  # Default
        assert variant.specifications == {}
        assert variant.source == "pim"  # Default
        assert variant.is_available is True  # Default

    def test_all_fields(self):
        """Test creation with all fields populated."""
        specs = {
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
            "weight": "56.52kg",
        }

        variant = VariantInfo(
            variant_id="var_steel_001",
            sku="STEEL-5MM-001",
            product_id="prod_plat_baja",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("500000"),
            stock_quantity=25,
            stock_unit="lembar",
            specifications=specs,
            source="pim",
            is_available=True,
        )

        assert variant.variant_id == "var_steel_001"
        assert variant.sku == "STEEL-5MM-001"
        assert variant.product_id == "prod_plat_baja"
        assert variant.variant_name == "Plat Baja 5mm x 1200mm x 2400mm"
        assert variant.price == Decimal("500000")
        assert variant.stock_quantity == 25
        assert variant.stock_unit == "lembar"
        assert variant.specifications == specs
        assert variant.source == "pim"
        assert variant.is_available is True

    def test_immutability(self):
        """Test that VariantInfo is immutable (frozen)."""
        from pydantic import ValidationError

        variant = VariantInfoFactory.create()

        with pytest.raises(ValidationError):
            variant.price = Decimal("200000")

        with pytest.raises(ValidationError):
            variant.stock_quantity = 50

        with pytest.raises(ValidationError):
            variant.variant_name = "Modified Name"


class TestPriceHandling:
    """Test suite for Decimal price handling and conversions."""

    def test_price_as_decimal(self):
        """Test that price is stored as Decimal."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price=Decimal("150000.50"),
            stock_quantity=10,
        )

        assert isinstance(variant.price, Decimal)
        assert variant.price == Decimal("150000.50")

    def test_price_from_float(self):
        """Test automatic conversion from float to Decimal."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price=150000.50,  # Float input
            stock_quantity=10,
        )

        assert isinstance(variant.price, Decimal)
        assert variant.price == Decimal("150000.5")

    def test_price_from_string(self):
        """Test automatic conversion from string to Decimal."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price="150000.50",  # String input
            stock_quantity=10,
        )

        assert isinstance(variant.price, Decimal)
        assert variant.price == Decimal("150000.50")

    def test_price_from_int(self):
        """Test automatic conversion from int to Decimal."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price=150000,  # Int input
            stock_quantity=10,
        )

        assert isinstance(variant.price, Decimal)
        assert variant.price == Decimal("150000")

    def test_price_precision(self):
        """Test that Decimal maintains precision for financial calculations."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price=Decimal("0.1") + Decimal("0.2"),  # Should be exactly 0.3
            stock_quantity=10,
        )

        assert variant.price == Decimal("0.3")
        # Float would give 0.30000000000000004
        assert variant.price != 0.1 + 0.2

    def test_display_price(self):
        """Test price formatting for display."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test",
            price=Decimal("1500000"),
            stock_quantity=10,
        )

        assert variant.get_display_price() == "Rp 1.500.000"

        # Test with decimal places
        variant2 = VariantInfo(
            variant_id="var_002",
            sku="TEST-002",
            product_id="prod_001",
            variant_name="Test",
            price=Decimal("150000.50"),
            stock_quantity=10,
        )

        assert variant2.get_display_price() == "Rp 150.000"


class TestStockAndAvailability:
    """Test suite for stock management and availability checking."""

    def test_has_stock_with_available_stock(self):
        """Test has_stock() returns True when stock > 0 and is_available."""
        variant = VariantInfoFactory.create(stock_quantity=10, is_available=True)
        assert variant.has_stock() is True

    def test_has_stock_with_zero_stock(self):
        """Test has_stock() returns False when stock is 0."""
        variant = VariantInfoFactory.create_out_of_stock()
        assert variant.stock_quantity == 0
        assert variant.has_stock() is False

    def test_has_stock_when_unavailable(self):
        """Test has_stock() returns False when is_available is False."""
        variant = VariantInfoFactory.create_unavailable()
        assert variant.stock_quantity == 100  # Has stock
        assert variant.is_available is False
        assert variant.has_stock() is False  # But not available

    def test_stock_boundaries(self):
        """Test stock field with various boundary values."""
        # Zero stock
        variant_zero = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Zero Stock",
            price=Decimal("100000"),
            stock_quantity=0,
        )
        assert variant_zero.stock_quantity == 0
        assert variant_zero.has_stock() is False

        # Large stock
        variant_large = VariantInfo(
            variant_id="var_002",
            sku="TEST-002",
            product_id="prod_001",
            variant_name="Large Stock",
            price=Decimal("100000"),
            stock_quantity=999999,
        )
        assert variant_large.stock_quantity == 999999
        assert variant_large.has_stock() is True


class TestSpecifications:
    """Test suite for variant specifications handling."""

    def test_empty_specifications(self):
        """Test variant with empty specifications dict."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="No Specs",
            price=Decimal("100000"),
            stock_quantity=10,
            specifications={},
        )

        assert variant.specifications == {}
        assert len(variant.specifications) == 0

    def test_specifications_default(self):
        """Test that specifications defaults to empty dict when not provided."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="No Specs Provided",
            price=Decimal("100000"),
            stock_quantity=10,
            # specifications not provided - should default to {}
        )

        assert variant.specifications == {}

    def test_get_specification(self):
        """Test get_specification helper method."""
        specs = {"thickness": "5mm", "width": "1200mm", "grade": "SS400"}
        variant = VariantInfoFactory.create_with_specifications(specs)

        assert variant.get_specification("thickness") == "5mm"
        assert variant.get_specification("width") == "1200mm"
        assert variant.get_specification("grade") == "SS400"
        assert variant.get_specification("non_existent") is None
        assert variant.get_specification("non_existent", "default") == "default"

    def test_matches_attributes(self):
        """Test variant matching against attribute filters."""
        variant = VariantInfoFactory.create_hollow_variant(
            material="hitam", dimensions="40x40"
        )

        # Exact match
        assert variant.matches_attributes({"material": "hitam"}) is True
        assert variant.matches_attributes({"dimensions": "40x40"}) is True
        assert (
            variant.matches_attributes({"material": "hitam", "dimensions": "40x40"})
            is True
        )

        # Case-insensitive match
        assert variant.matches_attributes({"material": "Hitam"}) is True
        assert variant.matches_attributes({"material": "HITAM"}) is True

        # No match
        assert variant.matches_attributes({"material": "galvanis"}) is False
        assert variant.matches_attributes({"dimensions": "50x50"}) is False

        # Non-existent attribute
        assert variant.matches_attributes({"color": "black"}) is False

        # Empty attributes (should match all)
        assert variant.matches_attributes({}) is True


class TestIndonesianMarketData:
    """Test suite for Indonesian steel market specific scenarios."""

    def test_indonesian_units(self):
        """Test various Indonesian units for steel products."""
        units = ["lembar", "batang", "kg", "meter", "roll", "unit", "pcs"]

        for unit in units:
            variant = VariantInfo(
                variant_id=f"var_{unit}",
                sku=f"TEST-{unit.upper()}",
                product_id="prod_001",
                variant_name=f"Product dengan unit {unit}",
                price=Decimal("100000"),
                stock_quantity=10,
                stock_unit=unit,
            )
            assert variant.stock_unit == unit

    def test_realistic_steel_variants(self):
        """Test realistic steel product variants for Indonesian market."""
        variants_data = [
            {
                "variant_id": "var_plate_5mm",
                "sku": "PLATE-SS400-5",
                "product_id": "prod_plat_baja",
                "variant_name": "Plat Baja SS400 5mm x 1200mm x 2400mm",
                "price": Decimal("500000"),
                "stock_quantity": 50,
                "stock_unit": "lembar",
                "specifications": {
                    "grade": "SS400",
                    "thickness": "5mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "56.52kg",
                    "standard": "JIS G3101",
                },
            },
            {
                "variant_id": "var_hollow_40x40",
                "sku": "HOLLOW-BLACK-40X40",
                "product_id": "prod_hollow",
                "variant_name": "Besi Hollow Hitam 40x40x2mm",
                "price": Decimal("750000"),
                "stock_quantity": 100,
                "stock_unit": "batang",
                "specifications": {
                    "type": "hollow",
                    "material": "hitam",
                    "dimensions": "40x40",
                    "thickness": "2mm",
                    "length": "6000mm",
                },
            },
            {
                "variant_id": "var_hbeam_200",
                "sku": "HBEAM-200X200",
                "product_id": "prod_hbeam",
                "variant_name": "H-Beam 200x200x8x12",
                "price": Decimal("2500000"),
                "stock_quantity": 20,
                "stock_unit": "batang",
                "specifications": {
                    "type": "H-Beam",
                    "height": "200mm",
                    "width": "200mm",
                    "web_thickness": "8mm",
                    "flange_thickness": "12mm",
                    "length": "12000mm",
                },
            },
        ]

        for variant_data in variants_data:
            variant = VariantInfo(**variant_data)
            assert variant.variant_id == variant_data["variant_id"]
            assert variant.sku == variant_data["sku"]
            assert variant.price == variant_data["price"]
            assert variant.specifications == variant_data["specifications"]

    def test_hollow_steel_variants(self):
        """Test besi hollow (hollow steel) variants with different materials."""
        # Hollow hitam (black hollow)
        black_hollow = VariantInfoFactory.create_hollow_variant(
            material="hitam", dimensions="40x40"
        )
        assert "hitam" in black_hollow.variant_name.lower()
        assert black_hollow.specifications["material"] == "hitam"

        # Hollow galvanis (galvanized hollow)
        galv_hollow = VariantInfoFactory.create_hollow_variant(
            material="galvanis", dimensions="50x50"
        )
        assert "galvanis" in galv_hollow.variant_name.lower()
        assert galv_hollow.specifications["material"] == "galvanis"


class TestHelperMethods:
    """Test suite for VariantInfo helper methods."""

    def test_to_summary_dict(self):
        """Test conversion to summary dictionary for API responses."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test Variant",
            price=Decimal("150000"),
            stock_quantity=25,
            stock_unit="lembar",
            specifications={"grade": "SS400"},
            source="pim",
            is_available=True,
        )

        summary = variant.to_summary_dict()

        assert summary["variant_id"] == "var_001"
        assert summary["sku"] == "TEST-001"
        assert summary["name"] == "Test Variant"
        assert summary["price"] == 150000.0  # Converted to float
        assert summary["display_price"] == "Rp 150.000"
        assert summary["stock"] == 25
        assert summary["unit"] == "lembar"
        assert summary["available"] is True
        assert summary["specifications"] == {"grade": "SS400"}

        # Check that internal metadata is excluded
        assert "product_id" not in summary
        assert "source" not in summary
        assert "is_available" not in summary

    def test_to_summary_dict_unavailable(self):
        """Test summary dict for unavailable variant."""
        variant = VariantInfoFactory.create_unavailable()
        summary = variant.to_summary_dict()

        assert summary["available"] is False  # Even though stock > 0
        assert summary["stock"] == 100


class TestFactoryMethods:
    """Test suite for VariantInfoFactory helper methods."""

    def test_factory_create_basic(self):
        """Test basic factory creation."""
        variant = VariantInfoFactory.create()

        assert variant.variant_id.startswith("var_")
        assert variant.sku.startswith("SKU-")
        assert variant.product_id.startswith("prod_")
        assert variant.price == Decimal("100000")
        assert variant.stock_quantity == 10

    def test_factory_create_steel(self):
        """Test steel variant factory creation."""
        variant = VariantInfoFactory.create_steel_variant()

        assert "steel" in variant.variant_id
        assert variant.product_id == "prod_plat_baja"
        assert variant.price == Decimal("500000")
        assert variant.specifications["grade"] == "SS400"
        assert variant.specifications["thickness"] == "5mm"

    def test_factory_create_hollow(self):
        """Test hollow steel variant factory creation."""
        variant = VariantInfoFactory.create_hollow_variant(
            material="galvanis", dimensions="100x100"
        )

        assert "hollow" in variant.variant_id
        assert variant.sku == "HOLLOW-GALVANIS-100x100"
        assert variant.specifications["material"] == "galvanis"
        assert variant.specifications["dimensions"] == "100x100"

    def test_factory_override_defaults(self):
        """Test factory with custom values overriding defaults."""
        custom = VariantInfoFactory.create_steel_variant(
            variant_name="Custom Steel Variant",
            price=Decimal("800000"),
            stock_quantity=200,
        )

        assert custom.variant_name == "Custom Steel Variant"
        assert custom.price == Decimal("800000")
        assert custom.stock_quantity == 200
        assert custom.stock_unit == "lembar"  # Default preserved


class TestDataSourceHandling:
    """Test suite for data source management."""

    def test_pim_source(self):
        """Test variant from PIM source."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="PIM Variant",
            price=Decimal("100000"),
            stock_quantity=10,
            source="pim",
        )

        assert variant.source == "pim"

    def test_cache_source(self):
        """Test variant from cache source."""
        variant = VariantInfoFactory.create_from_cache()

        assert variant.source == "cache"
        assert variant.sku.startswith("CACHE-")


class TestValidation:
    """Test suite for field validation."""

    def test_negative_price_validation(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError):
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="Negative Price",
                price=Decimal("-100000"),
                stock_quantity=10,
            )

    def test_negative_stock_validation(self):
        """Test that negative stock quantities are rejected."""
        with pytest.raises(ValueError):
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="Negative Stock",
                price=Decimal("100000"),
                stock_quantity=-10,
            )

    def test_zero_price_allowed(self):
        """Test that zero price is allowed (for free samples/promotions)."""
        variant = VariantInfo(
            variant_id="var_001",
            sku="FREE-001",
            product_id="prod_001",
            variant_name="Free Sample",
            price=Decimal("0"),
            stock_quantity=10,
        )

        assert variant.price == Decimal("0")
        assert variant.get_display_price() == "Rp 0"


class TestSerialization:
    """Test suite for model serialization."""

    def test_model_dump(self):
        """Test model_dump() for dictionary conversion."""
        variant = VariantInfoFactory.create_steel_variant()

        dict_data = variant.model_dump()

        assert dict_data["variant_id"] == variant.variant_id
        assert dict_data["sku"] == variant.sku
        assert dict_data["product_id"] == variant.product_id
        assert dict_data["variant_name"] == variant.variant_name
        assert dict_data["price"] == variant.price  # Remains as Decimal
        assert dict_data["stock_quantity"] == variant.stock_quantity
        assert dict_data["stock_unit"] == "lembar"
        assert dict_data["specifications"] == variant.specifications
        assert dict_data["source"] == "pim"
        assert dict_data["is_available"] is True

    def test_model_dump_json(self):
        """Test model_dump_json() for JSON string conversion."""
        variant = VariantInfoFactory.create_steel_variant()

        json_data = variant.model_dump_json()

        assert variant.sku in json_data
        assert variant.variant_name in json_data
        assert "500000" in json_data  # Price as string in JSON
        assert "lembar" in json_data
        assert "SS400" in json_data  # From specifications
