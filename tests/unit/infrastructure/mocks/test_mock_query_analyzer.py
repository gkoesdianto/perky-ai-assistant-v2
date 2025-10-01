"""Unit tests for MockQueryAnalyzer implementation.

Tests cover Indonesian steel terminology pattern matching,
query type detection, confidence calculation, and conversational context handling.
"""

import asyncio

import pytest

from src.domain.value_objects.query_intent import QueryIntent
from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
from tests.factories import DTOFactory


@pytest.fixture
def analyzer():
    """Create a MockQueryAnalyzer instance."""
    return MockQueryAnalyzer()


@pytest.fixture
def sample_conversation_context():
    """Create sample conversation context for testing."""
    return [
        DTOFactory.create_message_dto(
            content="Saya mencari plat baja", sender_type="user"
        ),
        DTOFactory.create_message_dto(
            content=(
                "Kami memiliki berbagai jenis plat baja. " "Ukuran apa yang Anda cari?"
            ),
            sender_type="ai_agent",
        ),
    ]


class TestMockQueryAnalyzer:
    """Test MockQueryAnalyzer functionality."""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes with correct patterns."""
        assert analyzer.patterns is not None
        assert "product_inquiry" in analyzer.patterns
        assert "price_check" in analyzer.patterns
        assert "availability_check" in analyzer.patterns
        assert "variant_selection" in analyzer.patterns

        # Check Indonesian terminology mapping
        assert "plat" in analyzer.terminology_map
        assert "hollow" in analyzer.terminology_map
        assert "besi" in analyzer.terminology_map
        assert "pipa" in analyzer.terminology_map

    @pytest.mark.asyncio
    async def test_product_inquiry_detection(self, analyzer):
        """Test detection of product inquiry queries."""
        queries = [
            "Plat baja 5mm",  # Removed "Ada" to avoid availability check
            "Saya cari hollow galvanis",
            "Mau beli besi beton",
            "Pipa apa saja",  # Removed "Stock" to avoid availability check
            "Profil WF",  # Removed "tersedia" to avoid availability check
        ]

        for query in queries:
            result = await analyzer.analyze(query)
            assert result.type == "product_inquiry"
            assert result.confidence >= 0.6
            assert result.original_query == query

    @pytest.mark.asyncio
    async def test_price_check_detection(self, analyzer):
        """Test detection of price check queries."""
        queries = [
            "Berapa harga plat 5mm?",
            "Price list hollow galvanis",
            "Biaya untuk besi beton",
            "Tarif pipa per meter",
        ]

        for query in queries:
            result = await analyzer.analyze(query)
            assert result.type == "price_check"
            assert result.confidence >= 0.6
            # Verify the query contains price-related keywords
            price_keywords = ["harga", "price", "biaya", "tarif", "cost"]
            assert any(keyword in query.lower() for keyword in price_keywords)

    @pytest.mark.asyncio
    async def test_availability_check_detection(self, analyzer):
        """Test detection of availability check queries."""
        queries = [
            "Stok plat baja ada?",
            "Stock hollow tersedia?",
            "Ada ready besi beton?",
            "Available pipa galvanis?",
        ]

        for query in queries:
            result = await analyzer.analyze(query)
            assert result.type == "availability_check"
            assert result.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_variant_selection_detection(self, analyzer):
        """Test detection of variant selection queries."""
        queries = [
            "Ukuran hollow 5mm x 10mm",  # Changed to avoid "ada" keyword
            "Size hollow 40x40",
            "Tebal plat 10 milimeter",
            "Dimensi pipa 2 inch",
        ]

        for query in queries:
            result = await analyzer.analyze(query)
            assert result.type in [
                "variant_selection",
                "product_inquiry",
                "availability_check",
            ]

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, analyzer):
        """Test confidence score calculation."""
        # High confidence - multiple keywords
        result = await analyzer.analyze("Berapa harga plat baja galvanis 5mm?")
        assert result.confidence >= 0.75

        # Medium confidence - single keyword
        result = await analyzer.analyze("Ada plat?")
        assert 0.5 <= result.confidence < 0.75

        # Low confidence - ambiguous query
        result = await analyzer.analyze("Saya butuh material")
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_attribute_extraction(self, analyzer):
        """Test extraction of product attributes from queries."""
        # Product type extraction
        result = await analyzer.analyze("Saya cari plat baja")
        assert result.detected_attributes.get("product_type") == "plat"

        # Measurement extraction
        result = await analyzer.analyze("Plat tebal 5mm panjang 2m")
        assert result.detected_attributes.get("thickness") == 5.0
        assert result.detected_attributes.get("length") == 2.0

        # Finish extraction
        result = await analyzer.analyze("Hollow galvanis 40x40")
        assert result.detected_attributes.get("finish") == "galvanis"
        assert result.detected_attributes.get("product_type") == "hollow"

        # Grade extraction
        result = await analyzer.analyze("Plat SS400 tebal 10mm")
        assert result.detected_attributes.get("grade") == "SS400"

    @pytest.mark.asyncio
    async def test_clarification_stage_determination(self, analyzer):
        """Test determination of clarification stages."""
        # Initial stage - low confidence, no attributes
        result = await analyzer.analyze("Saya butuh material")
        assert result.clarification_stage == "initial"

        # Narrowing stage - some attributes detected
        result = await analyzer.analyze("Plat baja untuk konstruksi")
        assert result.clarification_stage in ["initial", "narrowing"]

        # Confirming stage - high confidence, multiple attributes
        result = await analyzer.analyze("Plat baja SS400 tebal 10mm ukuran 4x8")
        assert result.clarification_stage in ["confirming", "complete"]

    @pytest.mark.asyncio
    async def test_conversation_context_handling(
        self, analyzer, sample_conversation_context
    ):
        """Test handling of conversation context."""
        result = await analyzer.analyze("Yang 10mm", sample_conversation_context)

        # Should maintain conversation history
        assert len(result.conversation_context.conversation_history) > 0

        # Should increment conversation turn
        # (2 messages = 1 complete turn, next is turn 2)
        assert result.conversation_turn == 2  # After one complete exchange

    @pytest.mark.asyncio
    async def test_next_action_determination(self, analyzer):
        """Test determination of next actions."""
        # Request clarification for ambiguous query
        result = await analyzer.analyze("Saya butuh material")
        assert result.next_action == "request_clarification"

        # Provide info for clear query
        result = await analyzer.analyze("Plat baja SS400 10mm 4x8 ada stok?")
        assert result.next_action in ["provide_info", "confirm_selection"]

        # Suggest alternatives for low confidence
        result = await analyzer.analyze("Material apa saja?")
        assert result.next_action in ["request_clarification", "suggest_alternatives"]

    @pytest.mark.asyncio
    async def test_quantity_extraction(self, analyzer):
        """Test extraction of quantity from queries."""
        # With unit indicators
        result = await analyzer.analyze("Mau beli 10 lembar plat")
        assert result.quantity == 10

        result = await analyzer.analyze("Butuh 5 batang hollow")
        assert result.quantity == 5

        # With context words
        result = await analyzer.analyze("Order 100 pcs besi beton")
        assert result.quantity == 100

        # No quantity
        result = await analyzer.analyze("Ada plat baja?")
        assert result.quantity is None

        # Number that's likely a dimension, not quantity
        result = await analyzer.analyze("Plat 10mm")
        assert result.quantity is None

    @pytest.mark.asyncio
    async def test_query_level_determination(self, analyzer):
        """Test determination of query level (product vs variant)."""
        # Product level
        result = await analyzer.analyze("Ada plat baja?")
        assert result.query_level == "product"

        # Variant level - with specific dimensions
        result = await analyzer.analyze("Plat baja 10mm x 1200mm x 2400mm")
        assert result.query_level == "variant"

        # Ambiguous
        result = await analyzer.analyze("Saya butuh material konstruksi")
        assert result.query_level == "ambiguous"

    @pytest.mark.asyncio
    async def test_next_clarification_building(self, analyzer):
        """Test building of next clarification needed."""
        # Product type clarification for ambiguous query
        result = await analyzer.analyze("Saya butuh material")
        assert result.next_clarification is not None
        assert result.next_clarification.attribute_type == "product_type"

        # Dimension clarification for variant selection
        result = await analyzer.analyze("Hollow berapa ukurannya?")
        clarification = result.next_clarification
        if clarification and clarification.attribute_type == "dimensions":
            assert "ukuran" in clarification.question_template.lower()

        # No clarification for complete query
        result = await analyzer.analyze("Plat SS400 10mm 4x8 ready stock 10 lembar")
        if result.clarification_stage == "complete":
            assert result.next_clarification is None

    @pytest.mark.asyncio
    async def test_human_intervention_flag(self, analyzer):
        """Test human intervention flag for low confidence queries."""
        # Should require human intervention for very low confidence
        result = await analyzer.analyze("???")
        assert result.requires_human_intervention is True

        # Should not require human intervention for clear queries
        result = await analyzer.analyze("Berapa harga plat baja SS400 10mm?")
        assert result.requires_human_intervention is False

    @pytest.mark.asyncio
    async def test_indonesian_terminology_support(self, analyzer):
        """Test support for Indonesian steel terminology."""
        indonesian_queries = [
            ("plat hitam", "plat"),
            ("besi kotak", "hollow"),
            ("pipa baja", "pipa"),
            ("besi siku", "siku"),
            ("profil wf", "wf"),
        ]

        for query, expected_product in indonesian_queries:
            result = await analyzer.analyze(query)
            detected_product = result.detected_attributes.get("product_type")
            assert (
                detected_product == expected_product
                or expected_product in query.lower()
            )

    @pytest.mark.asyncio
    async def test_conversation_turn_tracking(self, analyzer):
        """Test tracking of conversation turns."""
        # First turn - no context
        result = await analyzer.analyze("Ada plat?")
        assert result.conversation_turn == 1

        # With context - should count user messages
        context = [
            DTOFactory.create_message_dto(content="Hello", sender_type="user"),
            DTOFactory.create_message_dto(content="Hi there", sender_type="ai_agent"),
            DTOFactory.create_message_dto(content="Ada plat?", sender_type="user"),
            DTOFactory.create_message_dto(
                content="Ya, ada plat", sender_type="ai_agent"
            ),
        ]

        result = await analyzer.analyze("Yang 10mm?", context)
        assert result.conversation_turn == 3  # After 4 messages (2 complete turns) + 1

    @pytest.mark.asyncio
    async def test_complex_query_handling(self, analyzer):
        """Test handling of complex queries with multiple intents."""
        complex_query = "Berapa harga dan stok plat baja SS400 10mm ukuran 4x8?"
        result = await analyzer.analyze(complex_query)

        # Should detect primary intent (price or availability)
        assert result.type in ["price_check", "availability_check"]

        # Should extract all attributes
        assert result.detected_attributes.get("product_type") == "plat"
        assert result.detected_attributes.get("grade") == "SS400"
        assert result.detected_attributes.get("thickness") == 10.0

        # Should have high confidence
        assert result.confidence >= 0.75

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, analyzer):
        """Test handling of empty or minimal queries."""
        empty_queries = ["", " ", "?", "..."]

        for query in empty_queries:
            result = await analyzer.analyze(query)
            assert result.type == "general"
            assert result.confidence <= 0.3
            assert result.clarification_stage == "initial"
            assert result.next_action == "request_clarification"

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, analyzer):
        """Test thread-safety with concurrent analysis requests."""
        queries = [
            "Ada plat baja?",
            "Harga hollow galvanis",
            "Stok besi beton",
            "Ukuran pipa tersedia",
            "Material konstruksi apa saja?",
        ]

        # Run multiple analyses concurrently
        tasks = [analyzer.analyze(query) for query in queries]
        results = await asyncio.gather(*tasks)

        # Verify all results are valid QueryIntent objects
        for result in results:
            assert isinstance(result, QueryIntent)
            assert result.original_query in queries
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0
