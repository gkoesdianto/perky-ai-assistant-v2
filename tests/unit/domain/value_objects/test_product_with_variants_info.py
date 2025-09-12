"""Unit tests for ProductWithVariantsInfo aggregate value object."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from src.domain.value_objects.product_info import ProductInfo
from src.domain.value_objects.variant_info import VariantInfo
from src.domain.value_objects.product_with_variants_info import ProductWithVariantsInfo


class TestProductWithVariantsInfoCreation:
    """Test suite for ProductWithVariantsInfo creation and initialization."""

    def test_creation_with_single_variant(self):
        """Test creation with one variant."""
        product = ProductInfo(
            product_id="prod_001", product_name="Plat Baja", variant_count=1
        )

        variant = VariantInfo(
            variant_id="var_001",
            sku="PLATE-5MM",
            product_id="prod_001",
            variant_name="Plat Baja 5mm",
            price=Decimal("500000"),
            stock_quantity=10,
        )

        aggregate = ProductWithVariantsInfo(product=product, variants=[variant])

        assert aggregate.product == product
        assert len(aggregate.variants) == 1
        assert aggregate.variants[0] == variant

    def test_creation_with_multiple_variants(self):
        """Test creation with multiple variants."""
        product = ProductInfo(
            product_id="prod_hollow",
            product_name="Besi Hollow",
            product_description="Hollow steel sections",
            category="Hollow Steel",
            variant_count=3,
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="HOLLOW-BLACK-40X40",
                product_id="prod_hollow",
                variant_name="Besi Hollow Hitam 40x40",
                price=Decimal("750000"),
                stock_quantity=50,
                specifications={"material": "hitam", "dimensions": "40x40"},
            ),
            VariantInfo(
                variant_id="var_002",
                sku="HOLLOW-BLACK-50X50",
                product_id="prod_hollow",
                variant_name="Besi Hollow Hitam 50x50",
                price=Decimal("850000"),
                stock_quantity=30,
                specifications={"material": "hitam", "dimensions": "50x50"},
            ),
            VariantInfo(
                variant_id="var_003",
                sku="HOLLOW-GALV-40X40",
                product_id="prod_hollow",
                variant_name="Besi Hollow Galvanis 40x40",
                price=Decimal("950000"),
                stock_quantity=20,
                specifications={"material": "galvanis", "dimensions": "40x40"},
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        assert aggregate.product.product_id == "prod_hollow"
        assert len(aggregate.variants) == 3
        assert all(v.product_id == "prod_hollow" for v in aggregate.variants)

    def test_immutability(self):
        """Test that ProductWithVariantsInfo is immutable (frozen)."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=1
        )

        variant = VariantInfo(
            variant_id="var_001",
            sku="TEST-001",
            product_id="prod_001",
            variant_name="Test Variant",
            price=Decimal("100000"),
            stock_quantity=10,
        )

        aggregate = ProductWithVariantsInfo(product=product, variants=[variant])

        with pytest.raises(ValidationError, match="Instance is frozen"):
            aggregate.product = product

        with pytest.raises(ValidationError, match="Instance is frozen"):
            aggregate.variants = []

    def test_requires_at_least_one_variant(self):
        """Test that at least one variant is required."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=1
        )

        with pytest.raises(ValidationError) as exc_info:
            ProductWithVariantsInfo(product=product, variants=[])

        errors = exc_info.value.errors()
        assert any("at least 1" in str(error) for error in errors)


class TestPriceCalculations:
    """Test suite for price-related calculations."""

    def test_price_range_single_price(self):
        """Test price range when all variants have same price."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=2
        )

        variants = [
            VariantInfo(
                variant_id=f"var_{i}",
                sku=f"TEST-{i}",
                product_id="prod_001",
                variant_name=f"Variant {i}",
                price=Decimal("500000"),
                stock_quantity=10,
            )
            for i in range(2)
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        min_price, max_price = aggregate.price_range
        assert min_price == Decimal("500000")
        assert max_price == Decimal("500000")

    def test_price_range_different_prices(self):
        """Test price range with different variant prices."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="Cheap Variant",
                price=Decimal("100000"),
                stock_quantity=10,
            ),
            VariantInfo(
                variant_id="var_002",
                sku="TEST-002",
                product_id="prod_001",
                variant_name="Medium Variant",
                price=Decimal("500000"),
                stock_quantity=10,
            ),
            VariantInfo(
                variant_id="var_003",
                sku="TEST-003",
                product_id="prod_001",
                variant_name="Expensive Variant",
                price=Decimal("1000000"),
                stock_quantity=10,
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        min_price, max_price = aggregate.price_range
        assert min_price == Decimal("100000")
        assert max_price == Decimal("1000000")

    def test_get_price_display_range_single_price(self):
        """Test price display when all variants have same price."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=2
        )

        variants = [
            VariantInfo(
                variant_id=f"var_{i}",
                sku=f"TEST-{i}",
                product_id="prod_001",
                variant_name=f"Variant {i}",
                price=Decimal("1500000"),
                stock_quantity=10,
            )
            for i in range(2)
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        display_range = aggregate.get_price_display_range()
        assert display_range == "Rp 1.500.000"

    def test_get_price_display_range_different_prices(self):
        """Test price display with different variant prices."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=2
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="Cheap",
                price=Decimal("500000"),
                stock_quantity=10,
            ),
            VariantInfo(
                variant_id="var_002",
                sku="TEST-002",
                product_id="prod_001",
                variant_name="Expensive",
                price=Decimal("1500000"),
                stock_quantity=10,
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        display_range = aggregate.get_price_display_range()
        assert display_range == "Rp 500.000 - Rp 1.500.000"


class TestVariantOperations:
    """Test suite for variant lookup and filtering operations."""

    def test_get_variant_by_sku(self):
        """Test finding variant by SKU."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        variants = [
            VariantInfo(
                variant_id=f"var_{i}",
                sku=f"SKU-{i:03d}",
                product_id="prod_001",
                variant_name=f"Variant {i}",
                price=Decimal("100000"),
                stock_quantity=10,
            )
            for i in range(1, 4)
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        variant = aggregate.get_variant_by_sku("SKU-002")
        assert variant is not None
        assert variant.variant_id == "var_2"
        assert variant.sku == "SKU-002"

        non_existent = aggregate.get_variant_by_sku("SKU-999")
        assert non_existent is None

    def test_get_variant_by_id(self):
        """Test finding variant by variant ID."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=2
        )

        variants = [
            VariantInfo(
                variant_id="var_hollow_001",
                sku="HOLLOW-001",
                product_id="prod_001",
                variant_name="Variant 1",
                price=Decimal("100000"),
                stock_quantity=10,
            ),
            VariantInfo(
                variant_id="var_hollow_002",
                sku="HOLLOW-002",
                product_id="prod_001",
                variant_name="Variant 2",
                price=Decimal("200000"),
                stock_quantity=20,
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        variant = aggregate.get_variant_by_id("var_hollow_002")
        assert variant is not None
        assert variant.variant_id == "var_hollow_002"
        assert variant.price == Decimal("200000")

        non_existent = aggregate.get_variant_by_id("var_hollow_999")
        assert non_existent is None

    def test_get_variants_by_attributes(self):
        """Test filtering variants by attributes."""
        product = ProductInfo(
            product_id="prod_hollow", product_name="Besi Hollow", variant_count=4
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="HOLLOW-BLACK-40",
                product_id="prod_hollow",
                variant_name="Hollow Black 40x40",
                price=Decimal("750000"),
                stock_quantity=50,
                specifications={"material": "hitam", "dimensions": "40x40"},
            ),
            VariantInfo(
                variant_id="var_002",
                sku="HOLLOW-BLACK-50",
                product_id="prod_hollow",
                variant_name="Hollow Black 50x50",
                price=Decimal("850000"),
                stock_quantity=30,
                specifications={"material": "hitam", "dimensions": "50x50"},
            ),
            VariantInfo(
                variant_id="var_003",
                sku="HOLLOW-GALV-40",
                product_id="prod_hollow",
                variant_name="Hollow Galvanized 40x40",
                price=Decimal("950000"),
                stock_quantity=20,
                specifications={"material": "galvanis", "dimensions": "40x40"},
            ),
            VariantInfo(
                variant_id="var_004",
                sku="HOLLOW-GALV-50",
                product_id="prod_hollow",
                variant_name="Hollow Galvanized 50x50",
                price=Decimal("1050000"),
                stock_quantity=15,
                specifications={"material": "galvanis", "dimensions": "50x50"},
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        black_variants = aggregate.get_variants_by_attributes({"material": "hitam"})
        assert len(black_variants) == 2
        assert all(v.specifications["material"] == "hitam" for v in black_variants)

        size_40_variants = aggregate.get_variants_by_attributes({"dimensions": "40x40"})
        assert len(size_40_variants) == 2
        assert all(v.specifications["dimensions"] == "40x40" for v in size_40_variants)

        black_40_variants = aggregate.get_variants_by_attributes(
            {"material": "hitam", "dimensions": "40x40"}
        )
        assert len(black_40_variants) == 1
        assert black_40_variants[0].variant_id == "var_001"

    def test_available_skus(self):
        """Test getting list of available SKUs."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="AVAILABLE-001",
                product_id="prod_001",
                variant_name="Available 1",
                price=Decimal("100000"),
                stock_quantity=10,
                is_available=True,
            ),
            VariantInfo(
                variant_id="var_002",
                sku="UNAVAILABLE-002",
                product_id="prod_001",
                variant_name="Unavailable",
                price=Decimal("100000"),
                stock_quantity=10,
                is_available=False,
            ),
            VariantInfo(
                variant_id="var_003",
                sku="AVAILABLE-003",
                product_id="prod_001",
                variant_name="Available 2",
                price=Decimal("100000"),
                stock_quantity=10,
                is_available=True,
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        available_skus = aggregate.available_skus
        assert len(available_skus) == 2
        assert "AVAILABLE-001" in available_skus
        assert "AVAILABLE-003" in available_skus
        assert "UNAVAILABLE-002" not in available_skus


class TestStockOperations:
    """Test suite for stock-related operations."""

    def test_get_total_stock(self):
        """Test calculating total stock across all variants."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        variants = [
            VariantInfo(
                variant_id=f"var_{i}",
                sku=f"TEST-{i}",
                product_id="prod_001",
                variant_name=f"Variant {i}",
                price=Decimal("100000"),
                stock_quantity=i * 10,
            )
            for i in range(1, 4)
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        total = aggregate.get_total_stock()
        assert total == 60

    def test_has_available_stock(self):
        """Test checking if any variant has stock."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        variants_with_stock = [
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="With Stock",
                price=Decimal("100000"),
                stock_quantity=10,
                is_available=True,
            ),
            VariantInfo(
                variant_id="var_002",
                sku="TEST-002",
                product_id="prod_001",
                variant_name="No Stock",
                price=Decimal("100000"),
                stock_quantity=0,
                is_available=True,
            ),
        ]

        aggregate = ProductWithVariantsInfo(
            product=product, variants=variants_with_stock
        )
        assert aggregate.has_available_stock() is True

        variants_no_stock = [
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="No Stock 1",
                price=Decimal("100000"),
                stock_quantity=0,
                is_available=True,
            ),
            VariantInfo(
                variant_id="var_002",
                sku="TEST-002",
                product_id="prod_001",
                variant_name="No Stock 2",
                price=Decimal("100000"),
                stock_quantity=0,
                is_available=True,
            ),
        ]

        aggregate_no_stock = ProductWithVariantsInfo(
            product=product, variants=variants_no_stock
        )
        assert aggregate_no_stock.has_available_stock() is False

        variants_unavailable = [
            VariantInfo(
                variant_id="var_001",
                sku="TEST-001",
                product_id="prod_001",
                variant_name="Unavailable",
                price=Decimal("100000"),
                stock_quantity=100,
                is_available=False,
            )
        ]

        aggregate_unavailable = ProductWithVariantsInfo(
            product=product, variants=variants_unavailable
        )
        assert aggregate_unavailable.has_available_stock() is False


class TestSummaryGeneration:
    """Test suite for summary dictionary generation."""

    def test_to_summary_dict(self):
        """Test conversion to summary dictionary for API responses."""
        product = ProductInfo(
            product_id="prod_hollow",
            product_name="Besi Hollow",
            product_description="Hollow steel sections",
            category="Hollow Steel",
            variant_count=2,
        )

        variants = [
            VariantInfo(
                variant_id="var_001",
                sku="HOLLOW-001",
                product_id="prod_hollow",
                variant_name="Hollow Black 40x40",
                price=Decimal("750000"),
                stock_quantity=50,
                specifications={"material": "hitam", "dimensions": "40x40"},
            ),
            VariantInfo(
                variant_id="var_002",
                sku="HOLLOW-002",
                product_id="prod_hollow",
                variant_name="Hollow Galvanized 40x40",
                price=Decimal("950000"),
                stock_quantity=30,
                specifications={"material": "galvanis", "dimensions": "40x40"},
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        summary = aggregate.to_summary_dict()

        assert summary["product_id"] == "prod_hollow"
        assert summary["product_name"] == "Besi Hollow"
        assert summary["description"] == "Hollow steel sections"
        assert summary["category"] == "Hollow Steel"
        assert summary["variant_count"] == 2
        assert summary["price_range"] == "Rp 750.000 - Rp 950.000"
        assert summary["total_stock"] == 80
        assert summary["has_stock"] is True
        assert len(summary["variants"]) == 2

        variant_summary = summary["variants"][0]
        assert "variant_id" in variant_summary
        assert "sku" in variant_summary
        assert "name" in variant_summary
        assert "price" in variant_summary
        assert "display_price" in variant_summary
        assert "stock" in variant_summary
        assert "available" in variant_summary


class TestIndonesianMarketScenarios:
    """Test suite for Indonesian steel market specific scenarios."""

    def test_realistic_steel_product_aggregate(self):
        """Test realistic steel product with multiple variants."""
        product = ProductInfo(
            product_id="prod_plat_baja",
            product_name="Plat Baja",
            product_description="High quality steel plates for construction",
            category="Steel Plates",
            variant_count=3,
        )

        variants = [
            VariantInfo(
                variant_id="var_plate_5mm",
                sku="PLATE-SS400-5",
                product_id="prod_plat_baja",
                variant_name="Plat Baja SS400 5mm x 1200mm x 2400mm",
                price=Decimal("500000"),
                stock_quantity=50,
                stock_unit="lembar",
                specifications={
                    "grade": "SS400",
                    "thickness": "5mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "56.52kg",
                },
            ),
            VariantInfo(
                variant_id="var_plate_10mm",
                sku="PLATE-SS400-10",
                product_id="prod_plat_baja",
                variant_name="Plat Baja SS400 10mm x 1200mm x 2400mm",
                price=Decimal("1000000"),
                stock_quantity=25,
                stock_unit="lembar",
                specifications={
                    "grade": "SS400",
                    "thickness": "10mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "113.04kg",
                },
            ),
            VariantInfo(
                variant_id="var_plate_15mm",
                sku="PLATE-SS400-15",
                product_id="prod_plat_baja",
                variant_name="Plat Baja SS400 15mm x 1200mm x 2400mm",
                price=Decimal("1500000"),
                stock_quantity=10,
                stock_unit="lembar",
                specifications={
                    "grade": "SS400",
                    "thickness": "15mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "169.56kg",
                },
            ),
        ]

        aggregate = ProductWithVariantsInfo(product=product, variants=variants)

        assert aggregate.product.product_name == "Plat Baja"
        assert len(aggregate.variants) == 3

        min_price, max_price = aggregate.price_range
        assert min_price == Decimal("500000")
        assert max_price == Decimal("1500000")

        assert aggregate.get_total_stock() == 85
        assert aggregate.has_available_stock() is True

        thick_plates = aggregate.get_variants_by_attributes({"thickness": "10mm"})
        assert len(thick_plates) == 1
        assert thick_plates[0].price == Decimal("1000000")
