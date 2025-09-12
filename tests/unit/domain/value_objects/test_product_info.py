"""Unit tests for refactored ProductInfo value object."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.product_info import ProductInfo


class TestProductInfoCreation:
    """Test suite for ProductInfo creation and initialization."""

    def test_required_fields_only(self):
        """Test creation with minimal required fields."""
        product = ProductInfo(
            product_id="prod_001", product_name="Plat Baja", variant_count=5
        )

        assert product.product_id == "prod_001"
        assert product.product_name == "Plat Baja"
        assert product.variant_count == 5
        assert product.product_description is None
        assert product.category is None

    def test_all_fields(self):
        """Test creation with all fields populated."""
        product = ProductInfo(
            product_id="prod_plat_baja",
            product_name="Plat Baja",
            product_description="High quality steel plates for construction",
            category="Steel Plates",
            variant_count=10,
        )

        assert product.product_id == "prod_plat_baja"
        assert product.product_name == "Plat Baja"
        assert (
            product.product_description == "High quality steel plates for construction"
        )
        assert product.category == "Steel Plates"
        assert product.variant_count == 10

    def test_immutability(self):
        """Test that ProductInfo is immutable (frozen)."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=3
        )

        with pytest.raises(ValidationError, match="Instance is frozen"):
            product.product_name = "Modified Name"

        with pytest.raises(ValidationError, match="Instance is frozen"):
            product.variant_count = 10

        with pytest.raises(ValidationError, match="Instance is frozen"):
            product.product_id = "new_id"


class TestProductInfoValidation:
    """Test suite for ProductInfo validation rules."""

    def test_variant_count_must_be_positive(self):
        """Test that variant_count must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            ProductInfo(
                product_id="prod_001", product_name="Test Product", variant_count=0
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("variant_count",)
        assert "greater than or equal to 1" in str(errors[0]["msg"])

    def test_negative_variant_count_rejected(self):
        """Test that negative variant_count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProductInfo(
                product_id="prod_001", product_name="Test Product", variant_count=-5
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("variant_count",)

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ProductInfo(product_id="prod_001", product_name="Test Product")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "variant_count" in str(errors[0])

    def test_empty_product_id_rejected(self):
        """Test that empty product_id is rejected."""
        with pytest.raises(ValidationError):
            ProductInfo(product_id="", product_name="Test Product", variant_count=1)

    def test_empty_product_name_rejected(self):
        """Test that empty product_name is rejected."""
        with pytest.raises(ValidationError):
            ProductInfo(product_id="prod_001", product_name="", variant_count=1)


class TestProductInfoForIndonesianMarket:
    """Test suite for Indonesian steel market specific scenarios."""

    def test_indonesian_product_names(self):
        """Test ProductInfo with Indonesian product names."""
        products = [
            ("Plat Baja", "Steel Plates"),
            ("Besi Hollow", "Hollow Steel"),
            ("H-Beam", "Structural Beams"),
            ("WF (Wide Flange)", "Structural Steel"),
            ("CNP (Channel)", "Channel Steel"),
            ("Pipa Besi", "Steel Pipes"),
            ("Besi Beton", "Rebar"),
            ("Wiremesh", "Wire Mesh"),
        ]

        for name, category in products:
            product = ProductInfo(
                product_id=f"prod_{name.lower().replace(' ', '_')}",
                product_name=name,
                product_description=f"High quality {name} for construction",
                category=category,
                variant_count=5,
            )

            assert product.product_name == name
            assert product.category == category

    def test_realistic_steel_products(self):
        """Test realistic steel product data for Indonesian market."""
        products_data = [
            {
                "product_id": "prod_plat_baja",
                "product_name": "Plat Baja",
                "product_description": "Steel plates in various thicknesses and grades",
                "category": "Steel Plates",
                "variant_count": 25,
            },
            {
                "product_id": "prod_hollow",
                "product_name": "Besi Hollow",
                "product_description": "Hollow steel sections in black and galvanized",
                "category": "Hollow Steel",
                "variant_count": 40,
            },
            {
                "product_id": "prod_hbeam",
                "product_name": "H-Beam",
                "product_description": "Structural H-beams for construction",
                "category": "Structural Steel",
                "variant_count": 15,
            },
        ]

        for product_data in products_data:
            product = ProductInfo(**product_data)
            assert product.product_id == product_data["product_id"]
            assert product.product_name == product_data["product_name"]
            assert product.variant_count == product_data["variant_count"]


class TestProductInfoSerialization:
    """Test suite for ProductInfo serialization."""

    def test_model_dump(self):
        """Test model_dump() for dictionary conversion."""
        product = ProductInfo(
            product_id="prod_001",
            product_name="Test Product",
            product_description="Test description",
            category="Test Category",
            variant_count=5,
        )

        dict_data = product.model_dump()

        assert dict_data["product_id"] == "prod_001"
        assert dict_data["product_name"] == "Test Product"
        assert dict_data["product_description"] == "Test description"
        assert dict_data["category"] == "Test Category"
        assert dict_data["variant_count"] == 5

    def test_model_dump_json(self):
        """Test model_dump_json() for JSON string conversion."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        json_data = product.model_dump_json()

        assert "prod_001" in json_data
        assert "Test Product" in json_data
        assert "5" in json_data

    def test_model_dump_exclude_none(self):
        """Test model_dump with exclude_none option."""
        product = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        dict_data = product.model_dump(exclude_none=True)

        assert "product_id" in dict_data
        assert "product_name" in dict_data
        assert "variant_count" in dict_data
        assert "product_description" not in dict_data
        assert "category" not in dict_data


class TestProductInfoComparison:
    """Test suite for ProductInfo comparison and equality."""

    def test_equality(self):
        """Test equality comparison between ProductInfo instances."""
        product1 = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        product2 = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        product3 = ProductInfo(
            product_id="prod_002", product_name="Different Product", variant_count=3
        )

        assert product1 == product2
        assert product1 != product3
        assert product2 != product3

    def test_hash_consistency(self):
        """Test that equal objects have equal hashes."""
        product1 = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        product2 = ProductInfo(
            product_id="prod_001", product_name="Test Product", variant_count=5
        )

        assert hash(product1) == hash(product2)
