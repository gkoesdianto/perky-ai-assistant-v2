"""Unit tests for QueryIntent: intent classification and confidence."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.query_intent import (
    ClarificationNeeded,
    ConversationContext,
    QueryIntent,
)
from tests.factories import QueryIntentFactory


class TestClarificationNeeded:
    """Test suite for ClarificationNeeded value object."""

    def test_clarification_creation(self):
        """Test creating clarification needed objects."""
        clarification = ClarificationNeeded(
            attribute_type="material",
            question_template="What material grade do you need?",
            options=["SS400", "A36", "Q235B"],
            priority=1,
        )

        assert clarification.attribute_type == "material"
        assert clarification.question_template == "What material grade do you need?"
        assert clarification.options == ["SS400", "A36", "Q235B"]
        assert clarification.priority == 1
        assert clarification.depends_on is None

    def test_clarification_with_dependency(self):
        """Test clarification with dependency on another attribute."""
        clarification = ClarificationNeeded(
            attribute_type="dimensions",
            question_template="What dimensions do you need?",
            options=["5mm", "10mm", "15mm"],
            priority=2,
            depends_on="product_type",
        )

        assert clarification.depends_on == "product_type"
        assert clarification.priority == 2

    def test_clarification_attributes(self):
        """Test ClarificationNeeded attributes."""
        clarification = ClarificationNeeded(
            attribute_type="material",
            question_template="What material?",
            options=["SS400"],
            priority=1,
        )

        assert clarification.attribute_type == "material"
        assert clarification.priority == 1


class TestConversationContext:
    """Test suite for ConversationContext value object."""

    def test_context_creation(self):
        """Test creating conversation context."""
        context = ConversationContext(
            resolved_attributes={},
            pending_clarifications=[],
            conversation_history=[],
            attribute_confidence={},
        )

        assert context.resolved_attributes == {}
        assert context.pending_clarifications == []
        assert context.conversation_history == []
        assert context.attribute_confidence == {}

    def test_context_with_clarifications(self):
        """Test context with clarification history."""
        clarification = ClarificationNeeded(
            attribute_type="material",
            question_template="What material?",
            options=["SS400"],
            priority=1,
        )

        context = ConversationContext(
            resolved_attributes={"product_type": "plat_baja"},
            pending_clarifications=[clarification],
            conversation_history=[
                {"role": "user", "content": "I need steel plates"},
                {"role": "ai", "content": "What type of steel plates?"},
            ],
            attribute_confidence={"product_type": 0.95},
        )

        assert context.resolved_attributes["product_type"] == "plat_baja"
        assert len(context.pending_clarifications) == 1
        assert len(context.conversation_history) == 2
        assert context.attribute_confidence["product_type"] == 0.95

    def test_context_defaults(self):
        """Test that ConversationContext has proper defaults."""
        context = ConversationContext()

        assert context.resolved_attributes == {}
        assert context.pending_clarifications == []
        assert context.conversation_history == []
        assert context.attribute_confidence == {}


class TestQueryIntentTypes:
    """Test suite for all valid intent types."""

    def test_all_intent_types(self):
        """Test all valid intent types.

        Tests: product_inquiry, price_check, availability_check, general.
        """
        intent_types = [
            ("product_inquiry", "Spesifikasi plat baja apa saja?"),
            ("price_check", "Berapa harga plat baja 5mm?"),
            ("availability_check", "Ada stok plat baja SS400?"),
            ("general", "Bagaimana cara memesan?"),
        ]

        for intent_type, expected_query in intent_types:
            intent = QueryIntent(
                type=intent_type,
                confidence=0.85,
                original_query=expected_query,
                current_query=expected_query,
                conversation_context=ConversationContext(),
                clarification_stage="complete",
            )
            assert intent.type == intent_type
            assert intent.confidence == 0.85
            assert intent.original_query == expected_query

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

    def test_availability_check_intent(self, availability_check_intent):
        """Test stock check intent with fixture."""
        assert availability_check_intent.type == "availability_check"
        assert availability_check_intent.product_name == "plat baja SS400"
        assert availability_check_intent.quantity == 10
        assert availability_check_intent.confidence == 0.92

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
        intent_zero = QueryIntent(
            type="general",
            confidence=0.0,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_zero.confidence == 0.0

        intent_half = QueryIntent(
            type="general",
            confidence=0.5,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_half.confidence == 0.5

        intent_full = QueryIntent(
            type="general",
            confidence=1.0,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_full.confidence == 1.0

    def test_confidence_validation(self):
        """Test our confidence validation (<0 and >1 rejected)."""
        with pytest.raises(ValidationError) as exc_info:
            QueryIntent(
                type="general",
                confidence=-0.1,
                original_query="test",
                current_query="test",
                conversation_context=ConversationContext(),
                clarification_stage="complete",
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            QueryIntent(
                type="general",
                confidence=1.1,
                original_query="test",
                current_query="test",
                conversation_context=ConversationContext(),
                clarification_stage="complete",
            )
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_confidence_edge_cases(self):
        """Test confidence with very small positive values."""
        intent_tiny = QueryIntent(
            type="general",
            confidence=0.0001,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_tiny.confidence == 0.0001

        intent_almost_one = QueryIntent(
            type="general",
            confidence=0.9999,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_almost_one.confidence == 0.9999


class TestOptionalFields:
    """Test suite for optional fields behavior."""

    def test_optional_fields(self):
        """Verify product_name and quantity are optional."""
        intent = QueryIntent(
            type="general",
            confidence=0.75,
            original_query="general question",
            current_query="general question",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent.product_name is None
        assert intent.quantity is None

    def test_with_product_name_only(self):
        """Test intent with product name but no quantity."""
        intent = QueryIntent(
            type="product_inquiry",
            product_name="plat baja SS400",
            confidence=0.9,
            original_query="info plat baja SS400",
            current_query="info plat baja SS400",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent.product_name == "plat baja SS400"
        assert intent.quantity is None

    def test_with_quantity_only(self):
        """Test intent with quantity but no product name."""
        intent = QueryIntent(
            type="availability_check",
            quantity=50,
            confidence=0.88,
            original_query="check stock 50 units",
            current_query="check stock 50 units",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent.product_name is None
        assert intent.quantity == 50

    def test_with_both_optional_fields(self):
        """Test intent with both product name and quantity."""
        intent = QueryIntent(
            type="availability_check",
            product_name="H-Beam 200x200",
            quantity=25,
            confidence=0.95,
            original_query="check stock H-Beam 200x200 25 units",
            current_query="check stock H-Beam 200x200 25 units",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
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
                "type": "availability_check",
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
                original_query="test query",
                current_query="test query",
                conversation_context=ConversationContext(),
                clarification_stage="complete",
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
            QueryIntentFactory.create_availability_check(
                product_name="besi beton ulir 16mm", quantity=100
            ),
        ]

        for intent in intents:
            assert intent.product_name is not None
            assert intent.type in [
                "product_inquiry",
                "price_check",
                "availability_check",
            ]
            assert 0.0 <= intent.confidence <= 1.0


class TestConfidenceScoring:
    """Test suite for confidence scoring scenarios."""

    def test_confidence_scoring(self):
        """Test realistic confidence scores for different scenarios."""
        scenarios = [
            ("clear_product_inquiry", "product_inquiry", 0.98),
            ("ambiguous_query", "general", 0.45),
            ("likely_price_check", "price_check", 0.85),
            ("uncertain_availability_check", "availability_check", 0.62),
        ]

        for scenario_name, intent_type, confidence in scenarios:
            intent = QueryIntent(
                type=intent_type,
                confidence=confidence,
                original_query="test query",
                current_query="test query",
                conversation_context=ConversationContext(),
                clarification_stage="complete",
            )
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
            intent = QueryIntent(
                type="general",
                confidence=confidence,
                original_query="test",
                current_query="test",
                conversation_context=ConversationContext(),
                clarification_stage="complete",
            )
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
        assert intent.original_query is not None
        assert intent.current_query is not None
        assert intent.conversation_context is not None
        assert intent.clarification_stage == "complete"

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

        stock = QueryIntentFactory.create_availability_check()
        assert stock.type == "availability_check"
        assert stock.product_name == "plat baja SS400"
        assert stock.quantity == 10

        general = QueryIntentFactory.create_general_query()
        assert general.type == "general"
        assert general.product_name is None


class TestQueryIntentEdgeCases:
    """Test suite for edge cases and special scenarios."""

    def test_quantity_boundaries(self):
        """Test quantity field with various values."""
        intent_zero = QueryIntent(
            type="availability_check",
            quantity=0,
            confidence=0.9,
            original_query="check stock",
            current_query="check stock",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_zero.quantity == 0

        intent_large = QueryIntent(
            type="availability_check",
            quantity=999999,
            confidence=0.9,
            original_query="check stock",
            current_query="check stock",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent_large.quantity == 999999

    def test_empty_product_name(self):
        """Test with empty string product name."""
        intent = QueryIntent(
            type="product_inquiry",
            product_name="",
            confidence=0.8,
            original_query="product inquiry",
            current_query="product inquiry",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )
        assert intent.product_name == ""

    def test_model_serialization(self):
        """Test model_dump() and model_dump_json() for our use cases."""
        intent = QueryIntentFactory.create_availability_check()

        dict_data = intent.model_dump()
        assert dict_data["type"] == "availability_check"
        assert dict_data["product_name"] == "plat baja SS400"
        assert dict_data["quantity"] == 10
        assert dict_data["confidence"] == 0.92

        json_data = intent.model_dump_json()
        assert "availability_check" in json_data
        assert "plat baja SS400" in json_data


class TestConversationalFlow:
    """Test suite for conversational AI flow capabilities."""

    def test_clarification_stages(self):
        """Test different clarification stages."""
        stages = ["initial", "narrowing", "confirming", "complete"]

        for stage in stages:
            intent = QueryIntent(
                type="product_inquiry",
                confidence=0.85,
                original_query="I need steel plates",
                current_query="I need steel plates",
                conversation_context=ConversationContext(),
                clarification_stage=stage,
            )
            assert intent.clarification_stage == stage

    def test_query_evolution(self):
        """Test how queries evolve through conversation."""
        context = ConversationContext(
            resolved_attributes={"product_type": "plat_baja"},
            pending_clarifications=[],
            conversation_history=[
                {"role": "user", "content": "I need steel"},
                {"role": "ai", "content": "What type of steel product?"},
                {"role": "user", "content": "Steel plates"},
            ],
            attribute_confidence={"product_type": 0.95},
        )

        intent = QueryIntent(
            type="product_inquiry",
            confidence=0.95,
            original_query="I need steel",
            current_query="I need steel plates",
            conversation_context=context,
            clarification_stage="narrowing",
            product_name="plat baja",
        )

        assert intent.original_query == "I need steel"
        assert intent.current_query == "I need steel plates"
        assert "product_type" in intent.conversation_context.resolved_attributes
        assert len(intent.conversation_context.conversation_history) == 3

    def test_intent_new_fields(self):
        """Test QueryIntent with new conversational fields."""
        intent = QueryIntent(
            type="general",
            confidence=0.8,
            original_query="test",
            current_query="test",
            conversation_context=ConversationContext(),
            clarification_stage="complete",
        )

        assert intent.clarification_stage == "complete"
        assert intent.original_query == "test"

    def test_progressive_clarification(self):
        """Test progressive attribute clarification."""
        clarification1 = ClarificationNeeded(
            attribute_type="product_type",
            question_template="What type of steel product?",
            options=["plat_baja", "h_beam", "pipa"],
            priority=1,
        )

        clarification2 = ClarificationNeeded(
            attribute_type="material",
            question_template="What material grade?",
            options=["SS400", "A36"],
            priority=2,
            depends_on="product_type",
        )

        context = ConversationContext(
            resolved_attributes={},
            pending_clarifications=[clarification1, clarification2],
            conversation_history=[{"role": "user", "content": "I need steel"}],
            attribute_confidence={},
        )

        intent = QueryIntent(
            type="product_inquiry",
            confidence=0.7,
            original_query="I need steel",
            current_query="I need steel",
            conversation_context=context,
            clarification_stage="initial",
        )

        assert len(intent.conversation_context.pending_clarifications) == 2
        assert intent.conversation_context.pending_clarifications[0].priority == 1
        assert (
            intent.conversation_context.pending_clarifications[1].depends_on
            == "product_type"
        )
