"""Unit tests for QueryIntent value object focusing on intent classification and confidence validation."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.query_intent import QueryIntent
from tests.unit.domain.factories import QueryIntentFactory


class TestQueryIntentTypes:
    """Test suite for all valid intent types."""

    def test_all_intent_types(self):
        """Test all valid intent types (product_inquiry, price_check, stock_check, general)."""
        intent_types = [
            ("product_inquiry", "Spesifikasi plat baja apa saja?"),
            ("price_check", "Berapa harga plat baja 5mm?"),
            ("stock_check", "Ada stok plat baja SS400?"),
            ("general", "Bagaimana cara memesan?"),
        ]

        for intent_type, expected_query in intent_types:
            intent = QueryIntent(type=intent_type, confidence=0.85)
            assert intent.type == intent_type
            assert intent.confidence == 0.85

    def test_product_inquiry_intent(self, product_inquiry_intent):
        """Test product inquiry intent with fixture."""
        assert product_inquiry_intent.type == "product_inquiry"
        assert product_inquiry_intent.product_name == "plat baja"
        assert product_inquiry_intent.confidence == 0.95

    def test_price_check_intent(self, price_check_intent):
        """Test price check intent with fixture."""
        assert price_check_intent.type == "price_check"
        assert price_check_intent.product_name == "plat baja 5mm"
        assert price_check_intent.confidence == 0.98

    def test_stock_check_intent(self, stock_check_intent):
        """Test stock check intent with fixture."""
        assert stock_check_intent.type == "stock_check"
        assert stock_check_intent.product_name == "plat baja SS400"
        assert stock_check_intent.quantity == 10
        assert stock_check_intent.confidence == 0.92

    def test_general_intent(self, general_intent):
        """Test general intent with fixture."""
        assert general_intent.type == "general"
        assert general_intent.product_name is None
        assert general_intent.quantity is None
        assert general_intent.confidence == 0.85


class TestConfidenceBoundaries:
    """Test suite for confidence score boundaries and validation."""

    def test_confidence_boundaries(self):
        """Test confidence at boundaries (0.0, 0.5, 1.0)."""
        intent_zero = QueryIntent(type="general", confidence=0.0)
        assert intent_zero.confidence == 0.0

        intent_half = QueryIntent(type="general", confidence=0.5)
        assert intent_half.confidence == 0.5

        intent_full = QueryIntent(type="general", confidence=1.0)
        assert intent_full.confidence == 1.0

    def test_confidence_validation(self):
        """Test our confidence validation (<0 and >1 rejected)."""
        with pytest.raises(ValidationError) as exc_info:
            QueryIntent(type="general", confidence=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            QueryIntent(type="general", confidence=1.1)
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_confidence_edge_cases(self):
        """Test confidence with very small positive values."""
        intent_tiny = QueryIntent(type="general", confidence=0.0001)
        assert intent_tiny.confidence == 0.0001

        intent_almost_one = QueryIntent(type="general", confidence=0.9999)
        assert intent_almost_one.confidence == 0.9999


class TestOptionalFields:
    """Test suite for optional fields behavior."""

    def test_optional_fields(self):
        """Verify product_name and quantity are optional."""
        intent = QueryIntent(type="general", confidence=0.75)
        assert intent.product_name is None
        assert intent.quantity is None

    def test_with_product_name_only(self):
        """Test intent with product name but no quantity."""
        intent = QueryIntent(
            type="product_inquiry", product_name="plat baja SS400", confidence=0.9
        )
        assert intent.product_name == "plat baja SS400"
        assert intent.quantity is None

    def test_with_quantity_only(self):
        """Test intent with quantity but no product name."""
        intent = QueryIntent(type="stock_check", quantity=50, confidence=0.88)
        assert intent.product_name is None
        assert intent.quantity == 50

    def test_with_both_optional_fields(self):
        """Test intent with both product name and quantity."""
        intent = QueryIntent(
            type="stock_check",
            product_name="H-Beam 200x200",
            quantity=25,
            confidence=0.95,
        )
        assert intent.product_name == "H-Beam 200x200"
        assert intent.quantity == 25


class TestIntentWithProductContext:
    """Test suite for intent classification with product context."""

    def test_intent_with_product_context(self):
        """Test intent classification with product context."""
        contexts = [
            {
                "type": "product_inquiry",
                "product_name": "plat baja hitam",
                "confidence": 0.92,
                "expected_context": "inquiry about steel plate specifications",
            },
            {
                "type": "price_check",
                "product_name": "pipa SCH40 4 inch",
                "confidence": 0.96,
                "expected_context": "checking price for specific pipe",
            },
            {
                "type": "stock_check",
                "product_name": "H-Beam 150x150",
                "quantity": 30,
                "confidence": 0.94,
                "expected_context": "checking availability for specific quantity",
            },
        ]

        for context in contexts:
            intent = QueryIntent(
                type=context["type"],
                product_name=context.get("product_name"),
                quantity=context.get("quantity"),
                confidence=context["confidence"],
            )
            assert intent.type == context["type"]
            assert intent.confidence == context["confidence"]
            if "product_name" in context:
                assert intent.product_name == context["product_name"]

    def test_product_related_intents(self):
        """Test different product-related intent scenarios."""
        intents = [
            QueryIntentFactory.create_product_inquiry(
                product_name="plat kapal grade A"
            ),
            QueryIntentFactory.create_price_check(product_name="wire mesh M8"),
            QueryIntentFactory.create_stock_check(
                product_name="besi beton ulir 16mm", quantity=100
            ),
        ]

        for intent in intents:
            assert intent.product_name is not None
            assert intent.type in ["product_inquiry", "price_check", "stock_check"]
            assert 0.0 <= intent.confidence <= 1.0


class TestConfidenceScoring:
    """Test suite for confidence scoring scenarios."""

    def test_confidence_scoring(self):
        """Test realistic confidence scores for different scenarios."""
        scenarios = [
            ("clear_product_inquiry", "product_inquiry", 0.98),
            ("ambiguous_query", "general", 0.45),
            ("likely_price_check", "price_check", 0.85),
            ("uncertain_stock_check", "stock_check", 0.62),
        ]

        for scenario_name, intent_type, confidence in scenarios:
            intent = QueryIntent(type=intent_type, confidence=confidence)
            assert intent.type == intent_type
            assert intent.confidence == confidence

    def test_high_confidence_scenarios(self):
        """Test high confidence intent classification."""
        high_conf = QueryIntentFactory.create_with_high_confidence(type="price_check")
        assert high_conf.confidence == 0.99
        assert high_conf.type == "price_check"

    def test_low_confidence_scenarios(self):
        """Test low confidence intent classification."""
        low_conf = QueryIntentFactory.create_with_low_confidence(type="general")
        assert low_conf.confidence == 0.3
        assert low_conf.type == "general"

    def test_confidence_thresholds(self):
        """Test various confidence threshold scenarios."""
        thresholds = [
            (0.95, "high", "Very confident classification"),
            (0.75, "medium", "Reasonably confident"),
            (0.5, "low", "Uncertain classification"),
            (0.25, "very_low", "Very uncertain"),
        ]

        for confidence, level, description in thresholds:
            intent = QueryIntent(type="general", confidence=confidence)
            assert intent.confidence == confidence
            if confidence >= 0.9:
                assert intent.confidence >= 0.9
            elif confidence >= 0.7:
                assert 0.7 <= intent.confidence < 0.9
            elif confidence >= 0.5:
                assert 0.5 <= intent.confidence < 0.7
            else:
                assert intent.confidence < 0.5


class TestQueryIntentFactory:
    """Test suite for QueryIntentFactory methods."""

    def test_factory_create_default(self):
        """Test factory default creation."""
        intent = QueryIntentFactory.create()
        assert intent.type == "general"
        assert intent.confidence == 0.85
        assert intent.product_name is None
        assert intent.quantity is None

    def test_factory_create_with_overrides(self):
        """Test factory with custom values."""
        intent = QueryIntentFactory.create(
            type="price_check", confidence=0.77, product_name="custom product"
        )
        assert intent.type == "price_check"
        assert intent.confidence == 0.77
        assert intent.product_name == "custom product"

    def test_factory_specific_intents(self):
        """Test factory methods for specific intent types."""
        inquiry = QueryIntentFactory.create_product_inquiry()
        assert inquiry.type == "product_inquiry"
        assert inquiry.product_name == "plat baja"

        price = QueryIntentFactory.create_price_check()
        assert price.type == "price_check"
        assert price.product_name == "plat baja 5mm"

        stock = QueryIntentFactory.create_stock_check()
        assert stock.type == "stock_check"
        assert stock.product_name == "plat baja SS400"
        assert stock.quantity == 10

        general = QueryIntentFactory.create_general_query()
        assert general.type == "general"
        assert general.product_name is None


class TestQueryIntentEdgeCases:
    """Test suite for edge cases and special scenarios."""

    def test_quantity_boundaries(self):
        """Test quantity field with various values."""
        intent_zero = QueryIntent(type="stock_check", quantity=0, confidence=0.9)
        assert intent_zero.quantity == 0

        intent_large = QueryIntent(type="stock_check", quantity=999999, confidence=0.9)
        assert intent_large.quantity == 999999

    def test_empty_product_name(self):
        """Test with empty string product name."""
        intent = QueryIntent(type="product_inquiry", product_name="", confidence=0.8)
        assert intent.product_name == ""

    def test_model_serialization(self):
        """Test model_dump() and model_dump_json() for our use cases."""
        intent = QueryIntentFactory.create_stock_check()

        dict_data = intent.model_dump()
        assert dict_data["type"] == "stock_check"
        assert dict_data["product_name"] == "plat baja SS400"
        assert dict_data["quantity"] == 10
        assert dict_data["confidence"] == 0.92

        json_data = intent.model_dump_json()
        assert "stock_check" in json_data
        assert "plat baja SS400" in json_data
