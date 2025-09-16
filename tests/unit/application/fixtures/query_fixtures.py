"""Query intent fixtures for application layer testing.

This module contains fixtures for creating sample query intents and related objects.
"""

import pytest

from src.application.services.query_analyzer import QueryAnalyzerService
from src.domain.value_objects.query_intent import (
    ClarificationNeeded,
    ConversationContext,
    QueryIntent,
)


@pytest.fixture
def query_analyzer_service(mock_query_analyzer):
    """Create a QueryAnalyzerService instance with mock dependencies."""
    return QueryAnalyzerService(query_analyzer=mock_query_analyzer)


@pytest.fixture
def sample_query_intent_with_clarification():
    """Create a sample QueryIntent with clarification needed for testing."""
    return QueryIntent(
        type="product_inquiry",
        clarification_stage="narrowing",
        query_level="variant",
        conversation_context=ConversationContext(
            resolved_attributes={
                "product_type": "besi_hollow",
                "dimensions": "4x4",
            },
            pending_clarifications=[
                ClarificationNeeded(
                    attribute_type="thickness",
                    question_template="Berapa ketebalan yang Anda butuhkan?",
                    options=["1.2mm", "1.4mm", "1.8mm", "2.0mm"],
                    priority=1,
                )
            ],
        ),
        next_action="request_clarification",
        original_query="Yang ukuran 4x4",
        current_query="besi hollow ukuran 4x4",
        detected_attributes={"dimensions": "4x4"},
        confidence=0.85,
        matched_products=["PROD-001", "PROD-002"],
        possible_variants=["VAR-001", "VAR-002", "VAR-003"],
    )


@pytest.fixture
def sample_query_intent_product():
    """Create a sample QueryIntent for product inquiry."""
    return QueryIntent(
        type="product_inquiry",
        clarification_stage="complete",
        query_level="product",
        conversation_context=ConversationContext(
            resolved_attributes={"product_type": "plat"},
            attribute_confidence={"product_type": 0.9},
        ),
        conversation_turn=1,
        next_action="provide_info",
        original_query="Ada plat baja 10mm?",
        current_query="Ada plat baja 10mm?",
        detected_attributes={"product_type": "plat", "thickness": "10mm"},
        confidence=0.95,
        product_name="plat baja",
        quantity=None,
    )


@pytest.fixture
def sample_query_intent_price():
    """Create a sample QueryIntent for price check."""
    return QueryIntent(
        type="price_check",
        clarification_stage="complete",
        query_level="variant",
        conversation_context=ConversationContext(
            resolved_attributes={"product_type": "hollow", "size": "40x40"},
            attribute_confidence={"product_type": 0.85, "size": 0.9},
        ),
        conversation_turn=2,
        next_action="provide_info",
        original_query="Berapa harga hollow 40x40?",
        current_query="Berapa harga hollow 40x40 galvanis?",
        detected_attributes={
            "product_type": "hollow",
            "size": "40x40",
            "finish": "galvanis",
        },
        confidence=0.88,
        product_name="hollow galvanis",
    )


@pytest.fixture
def sample_query_intent_availability():
    """Create a sample QueryIntent for availability check."""
    return QueryIntent(
        type="availability_check",
        clarification_stage="narrowing",
        query_level="product",
        conversation_context=ConversationContext(),
        conversation_turn=1,
        next_action="request_clarification",
        next_clarification=ClarificationNeeded(
            attribute_type="dimensions",
            question_template="Ukuran berapa yang Anda cari?",
            options=["1200x2400", "1500x3000", "2000x4000"],
            priority=1,
        ),
        original_query="Ada stok plat?",
        current_query="Ada stok plat?",
        detected_attributes={"product_type": "plat"},
        confidence=0.7,
        product_name="plat",
    )


@pytest.fixture
def sample_query_intent_ambiguous():
    """Create a sample QueryIntent for ambiguous query."""
    return QueryIntent(
        type="general",
        clarification_stage="initial",
        query_level="ambiguous",
        conversation_context=ConversationContext(),
        conversation_turn=1,
        next_action="request_clarification",
        original_query="Saya butuh bahan konstruksi",
        current_query="Saya butuh bahan konstruksi",
        detected_attributes={},
        confidence=0.4,
        requires_human_intervention=False,
    )


__all__ = [
    "query_analyzer_service",
    "sample_query_intent_with_clarification",
    "sample_query_intent_product",
    "sample_query_intent_price",
    "sample_query_intent_availability",
    "sample_query_intent_ambiguous",
]
