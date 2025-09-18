"""
Unit tests for QueryAnalyzerPort protocol.
Tests the protocol contract using mock implementations from conftest.
"""

from unittest.mock import AsyncMock

import pytest

from src.domain.value_objects.query_intent import (
    ClarificationNeeded,
    ConversationContext,
    QueryIntent,
)
from tests.factories import QueryIntentFactory


@pytest.mark.asyncio
class TestMockQueryAnalyzerAdapter:
    """Test suite for Query Analyzer port mock implementation."""

    async def test_analyze_without_context(
        self, mock_query_analyzer, sample_query_intent_product
    ):
        """Test analyzing query without conversation context."""
        # Arrange
        query = "Ada plat baja 10mm?"
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_product

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert isinstance(result, QueryIntent)
        assert result.type == "product_inquiry"
        assert result.original_query == "Ada plat baja 10mm?"
        assert result.product_name == "plat baja"
        assert result.confidence == 0.95
        assert mock_query_analyzer.call_count == 1
        assert mock_query_analyzer.last_query == query
        assert mock_query_analyzer.last_context is None

    async def test_analyze_with_context(
        self,
        mock_query_analyzer,
        sample_conversation_context,
        sample_query_intent_price,
    ):
        """Test analyzing query with conversation context."""
        # Arrange
        query = "Berapa harga hollow 40x40?"
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_price

        # Act
        result = await mock_query_analyzer.analyze(query, sample_conversation_context)

        # Assert
        assert isinstance(result, QueryIntent)
        assert result.type == "price_check"
        assert result.query_level == "variant"
        assert result.conversation_turn == 2
        assert mock_query_analyzer.call_count == 1
        assert mock_query_analyzer.last_query == query
        assert mock_query_analyzer.last_context == sample_conversation_context
        assert len(mock_query_analyzer.last_context) == 2

    async def test_analyze_product_inquiry(self, mock_query_analyzer):
        """Test analyzing product inquiry query."""
        # Arrange
        query = "Apakah ada besi beton ulir?"
        expected_intent = QueryIntentFactory.create_product_inquiry(
            product_name="besi beton", original_query=query, confidence=0.92
        )
        mock_query_analyzer.analyze_mock.return_value = expected_intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "product_inquiry"
        assert result.product_name == "besi beton"
        assert result.confidence == 0.92
        assert result.clarification_stage == "complete"
        mock_query_analyzer.analyze_mock.assert_called_once_with(query, None)

    async def test_analyze_availability_check(
        self, mock_query_analyzer, sample_query_intent_availability
    ):
        """Test analyzing availability check with clarification needed."""
        # Arrange
        query = "Ada stok plat?"
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_availability

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "availability_check"
        assert result.clarification_stage == "narrowing"
        assert result.next_action == "request_clarification"
        assert result.next_clarification is not None
        assert isinstance(result.next_clarification, ClarificationNeeded)
        assert result.next_clarification.attribute_type == "dimensions"
        assert result.confidence == 0.7

    async def test_analyze_price_check(self, mock_query_analyzer):
        """Test analyzing price check query."""
        # Arrange
        query = "Berapa harga plat baja 5mm per lembar?"
        intent = QueryIntent(
            type="price_check",
            clarification_stage="complete",
            query_level="variant",
            conversation_context=ConversationContext(
                resolved_attributes={"product_type": "plat", "thickness": "5mm"},
                attribute_confidence={"product_type": 0.95, "thickness": 0.9},
            ),
            next_action="provide_info",
            original_query=query,
            current_query=query,
            detected_attributes={
                "product_type": "plat",
                "thickness": "5mm",
                "unit": "lembar",
            },
            confidence=0.93,
            product_name="plat baja",
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "price_check"
        assert result.query_level == "variant"
        assert result.detected_attributes["thickness"] == "5mm"
        assert result.detected_attributes["unit"] == "lembar"
        assert result.confidence == 0.93

    async def test_analyze_variant_selection(self, mock_query_analyzer):
        """Test analyzing variant selection query."""
        # Arrange
        query = "Saya mau yang tebal 10mm dengan lebar 1200mm"
        intent = QueryIntent(
            type="variant_selection",
            clarification_stage="confirming",
            query_level="variant",
            conversation_context=ConversationContext(
                resolved_attributes={
                    "product_type": "plat",
                    "thickness": "10mm",
                    "width": "1200mm",
                },
                attribute_confidence={
                    "product_type": 0.85,
                    "thickness": 0.95,
                    "width": 0.95,
                },
            ),
            next_action="confirm_selection",
            original_query=query,
            current_query=query,
            detected_attributes={"thickness": "10mm", "width": "1200mm"},
            confidence=0.91,
            product_name="plat baja",
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "variant_selection"
        assert result.clarification_stage == "confirming"
        assert result.next_action == "confirm_selection"
        assert result.detected_attributes["thickness"] == "10mm"
        assert result.detected_attributes["width"] == "1200mm"

    async def test_analyze_ambiguous_query(
        self, mock_query_analyzer, sample_query_intent_ambiguous
    ):
        """Test analyzing ambiguous query."""
        # Arrange
        query = "Saya butuh bahan konstruksi"
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_ambiguous

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "general"
        assert result.clarification_stage == "initial"
        assert result.query_level == "ambiguous"
        assert result.next_action == "request_clarification"
        assert result.confidence == 0.4
        assert result.detected_attributes == {}
        assert not result.requires_human_intervention

    async def test_analyze_empty_query(self, mock_query_analyzer):
        """Test handling empty query."""
        # Arrange
        query = ""
        intent = QueryIntent(
            type="general",
            clarification_stage="initial",
            query_level="ambiguous",
            conversation_context=ConversationContext(),
            next_action="request_clarification",
            original_query="",
            current_query="",
            detected_attributes={},
            confidence=0.0,
            requires_human_intervention=False,
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.type == "general"
        assert result.confidence == 0.0
        assert result.original_query == ""
        assert mock_query_analyzer.last_query == ""

    async def test_analyze_with_quantity(self, mock_query_analyzer):
        """Test analyzing query with quantity detection."""
        # Arrange
        query = "Saya butuh 50 lembar plat baja 10mm"
        intent = QueryIntent(
            type="product_inquiry",
            clarification_stage="complete",
            query_level="variant",
            conversation_context=ConversationContext(),
            next_action="provide_info",
            original_query=query,
            current_query=query,
            detected_attributes={
                "product_type": "plat",
                "thickness": "10mm",
                "quantity": 50,
            },
            confidence=0.96,
            product_name="plat baja",
            quantity=50,
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.quantity == 50
        assert result.detected_attributes["quantity"] == 50
        assert result.confidence == 0.96

    async def test_analyze_multi_turn_conversation(
        self, mock_query_analyzer, sample_conversation_context
    ):
        """Test analyzing query in multi-turn conversation."""
        # Arrange
        query = "Yang lebih murah ada?"
        intent = QueryIntent(
            type="price_check",
            clarification_stage="narrowing",
            query_level="product",
            conversation_context=ConversationContext(
                resolved_attributes={"product_type": "plat"},
                conversation_history=[
                    {"sender": "user", "content": "Saya butuh plat baja tebal 10mm"},
                    {
                        "sender": "ai_agent",
                        "content": "Baik, kami punya plat baja 10mm",
                    },
                ],
            ),
            conversation_turn=3,
            next_action="suggest_alternatives",
            original_query="Saya butuh plat baja tebal 10mm",
            current_query=query,
            detected_attributes={"price_preference": "lower"},
            confidence=0.78,
            product_name="plat baja",
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query, sample_conversation_context)

        # Assert
        assert result.conversation_turn == 3
        assert result.next_action == "suggest_alternatives"
        assert result.detected_attributes["price_preference"] == "lower"
        assert len(result.conversation_context.conversation_history) == 2

    async def test_reset_functionality(
        self,
        mock_query_analyzer,
        sample_conversation_context,
        sample_query_intent_product,
    ):
        """Test reset clears all state."""
        # Arrange
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_product

        # Act - First call
        await mock_query_analyzer.analyze("Test query", sample_conversation_context)

        # Assert - State is set
        assert mock_query_analyzer.call_count == 1
        assert mock_query_analyzer.last_query == "Test query"
        assert mock_query_analyzer.last_context == sample_conversation_context

        # Act - Reset
        mock_query_analyzer.reset()

        # Assert - State is cleared
        assert mock_query_analyzer.call_count == 0
        assert mock_query_analyzer.last_query is None
        assert mock_query_analyzer.last_context is None
        mock_query_analyzer.analyze_mock.assert_not_called()

    async def test_multiple_calls_tracking(self, mock_query_analyzer):
        """Test tracking multiple analyze calls."""
        # Arrange
        queries = ["Query 1", "Query 2", "Query 3"]
        intents = [
            QueryIntentFactory.create(original_query=q, confidence=0.8 + i * 0.05)
            for i, q in enumerate(queries)
        ]
        mock_query_analyzer.analyze_mock.side_effect = intents

        # Act & Assert
        for i, (query, expected_intent) in enumerate(zip(queries, intents), 1):
            result = await mock_query_analyzer.analyze(query)
            assert result.original_query == query
            assert result.confidence == expected_intent.confidence
            assert mock_query_analyzer.call_count == i
            assert mock_query_analyzer.last_query == query

    async def test_clarification_needed_handling(self, mock_query_analyzer):
        """Test handling queries that need clarification."""
        # Arrange
        query = "Ada yang murah?"
        clarification = ClarificationNeeded(
            attribute_type="product_type",
            question_template="Produk apa yang Anda cari?",
            options=["Plat Baja", "Besi Beton", "Hollow", "Pipa"],
            priority=1,
        )
        intent = QueryIntent(
            type="price_check",
            clarification_stage="initial",
            query_level="ambiguous",
            conversation_context=ConversationContext(
                pending_clarifications=[clarification]
            ),
            next_action="request_clarification",
            next_clarification=clarification,
            original_query=query,
            current_query=query,
            detected_attributes={},
            confidence=0.45,
            requires_human_intervention=False,
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.next_action == "request_clarification"
        assert result.next_clarification is not None
        assert result.next_clarification.attribute_type == "product_type"
        assert len(result.next_clarification.options) == 4
        assert result.confidence == 0.45
        assert len(result.conversation_context.pending_clarifications) == 1

    async def test_protocol_compliance(self, mock_query_analyzer):
        """Test that mock implementation satisfies the protocol."""
        # Verify required attributes
        assert hasattr(mock_query_analyzer, "analyze")
        assert callable(mock_query_analyzer.analyze)

        # Verify method signature matches protocol
        import inspect

        sig = inspect.signature(mock_query_analyzer.analyze)
        params = list(sig.parameters.keys())
        assert "query" in params
        assert "conversation_context" in params

        # Verify return type annotation
        return_annotation = sig.return_annotation
        assert return_annotation is not None

    async def test_edge_case_special_characters(self, mock_query_analyzer):
        """Test handling queries with special characters."""
        # Arrange
        query = "Harga plat @#$% ukuran 10mm?"
        intent = QueryIntent(
            type="price_check",
            clarification_stage="complete",
            query_level="variant",
            conversation_context=ConversationContext(),
            next_action="provide_info",
            original_query=query,
            current_query=query,
            detected_attributes={"product_type": "plat", "thickness": "10mm"},
            confidence=0.75,
            product_name="plat",
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.original_query == query
        assert result.confidence == 0.75
        assert mock_query_analyzer.last_query == query

    async def test_human_intervention_required(self, mock_query_analyzer):
        """Test handling queries that require human intervention."""
        # Arrange
        query = "Saya butuh konsultasi khusus untuk proyek besar"
        intent = QueryIntent(
            type="general",
            clarification_stage="initial",
            query_level="ambiguous",
            conversation_context=ConversationContext(),
            next_action="request_clarification",
            original_query=query,
            current_query=query,
            detected_attributes={"project_type": "large", "needs": "consultation"},
            confidence=0.3,
            requires_human_intervention=True,
        )
        mock_query_analyzer.analyze_mock.return_value = intent

        # Act
        result = await mock_query_analyzer.analyze(query)

        # Assert
        assert result.requires_human_intervention is True
        assert result.confidence == 0.3
        assert result.detected_attributes["needs"] == "consultation"
