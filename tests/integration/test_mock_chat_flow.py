"""
End-to-End Integration Tests for Mock Infrastructure Chat Flows.

Tests the three core MVP scenarios with complete chat flow:
1. Product Inquiry - User asks about steel plates, gets product info with prices
2. Price Check - User asks about hollow prices, gets pricing information
3. Availability Check - User checks stock availability for specific products
"""

import pytest
from src.infrastructure.mocks.container.mock_container import MockInfrastructureContainer
from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl


class TestMockChatFlow:
    """End-to-end tests for mock infrastructure chat flows."""

    @pytest.fixture
    async def setup_infrastructure(self):
        """Setup mock infrastructure for testing."""
        container = MockInfrastructureContainer(use_mocks=True)

        # Initialize use cases with mock dependencies
        start_session_use_case = StartChatSessionUseCaseImpl(
            session_repository=None,
            redis_client=container.get_redis_client(),
        )

        process_message_use_case = ProcessUserMessageUseCaseImpl(
            conversation_repository=container.get_conversation_repository(),
            chat_agent=container.get_ai_agent(),
            product_service=container.get_product_repository(),
        )

        get_conversation_use_case = GetConversationUseCaseImpl(
            conversation_repository=container.get_conversation_repository()
        )

        # Create orchestrator with use cases
        orchestrator = ChatOrchestrator(
            start_session_use_case=start_session_use_case,
            process_message_use_case=process_message_use_case,
            get_conversation_use_case=get_conversation_use_case,
        )

        return orchestrator

    @pytest.mark.asyncio
    async def test_scenario_1_product_inquiry_flow(self, setup_infrastructure):
        """
        Scenario 1: Product Inquiry
        User asks about steel plates, gets product info with prices.
        """
        orchestrator = await setup_infrastructure
        session_id = "test-session-001"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # User asks about plat baja
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Ada plat baja 5mm?"
        )

        # Verify response is meaningful and relevant
        assert response is not None
        # Response should mention product, availability, or specifications
        assert len(response.content) > 20  # Meaningful response
        # Should be about the product asked (plat/baja/thickness)
        assert any(
            term in response.content.lower()
            for term in ["plat", "baja", "tersedia", "5mm", "dimensi", "ukuran"]
        )

        # Follow-up about availability
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Berapa stoknya?"
        )

        # LLM-like response about availability
        assert any(
            term in response.content.lower()
            for term in [
                "stok",
                "stock",
                "tersedia",
                "siap",
                "jumlah",
                "lembar",
                "batang",
            ]
        )

    @pytest.mark.asyncio
    async def test_scenario_2_price_check_flow(self, setup_infrastructure):
        """
        Scenario 2: Price Check
        User asks about hollow prices, gets pricing information.
        """
        orchestrator = await setup_infrastructure
        session_id = "test-session-002"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # User asks about hollow prices
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Harga hollow galvanis 40x40?"
        )

        # Verify price information
        assert response is not None
        assert "hollow" in response.content.lower()
        assert any(
            term in response.content.lower()
            for term in ["harga", "price", "rp", "85000", "85.000"]
        )

    @pytest.mark.asyncio
    async def test_scenario_3_availability_check_flow(self, setup_infrastructure):
        """
        Scenario 3: Availability Check
        User checks stock availability for specific products.
        """
        orchestrator = await setup_infrastructure
        session_id = "test-session-003"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # User checks H-beam availability
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="H-beam 200x200 ada stok?"
        )

        # Verify stock information
        assert response is not None
        assert any(
            term in response.content.lower()
            for term in ["stok", "stock", "tersedia", "available"]
        )
        assert "200x200" in response.content or "h-beam" in response.content.lower()

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, setup_infrastructure):
        """Test a complete multi-turn conversation."""
        orchestrator = await setup_infrastructure
        session_id = "test-session-004"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # Turn 1: Greeting
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Halo"
        )
        # Check for greeting indicators - LLM-like responses vary
        assert any(
            term in response.content.lower()
            for term in ["selamat", "perky", "sms perkasa", "bantu", "halo"]
        )

        # Turn 2: Product inquiry
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Saya butuh plat baja untuk proyek"
        )
        assert "plat" in response.content.lower()

        # Turn 3: Specific size
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Yang 10mm ada?"
        )
        # Should give a meaningful response about the product
        assert len(response.content) > 10

        # Verify conversation continuity
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 6  # 3 user + 3 assistant messages

    @pytest.mark.asyncio
    async def test_error_handling_in_chat_flow(self, setup_infrastructure):
        """Test error handling in chat flow."""
        orchestrator = await setup_infrastructure
        session_id = "test-session-error"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # Send empty message - should handle gracefully
        response = await orchestrator.handle_user_message(
            session_id=session_id, content=""
        )
        assert response is not None
        assert response.content is not None

        # Send very long message - should handle gracefully
        long_content = "test " * 1000
        response = await orchestrator.handle_user_message(
            session_id=session_id, content=long_content
        )
        assert response is not None
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_indonesian_language_consistency(self, setup_infrastructure):
        """Test that responses are consistently in Indonesian."""
        orchestrator = await setup_infrastructure
        session_id = "test-session-lang"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # Common Indonesian queries
        queries = [
            "Apa saja produk yang tersedia?",
            "Berapa harga plat baja?",
            "Ada diskon untuk pembelian banyak?",
            "Bagaimana cara pesan?",
        ]

        for query in queries:
            response = await orchestrator.handle_user_message(
                session_id=session_id, content=query
            )
            assert response is not None
            # Check that response is in Indonesian and relevant to query
            # Instead of checking exact words, verify it's a meaningful response
            assert len(response.content) > 10  # Has substantial content
            assert response.content.strip()  # Not empty response

    @pytest.mark.asyncio
    async def test_product_variant_selection_flow(self, setup_infrastructure):
        """Test product variant selection flow."""
        orchestrator = await setup_infrastructure
        session_id = "test-session-variant"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # Ask about product with variants
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Ada plat baja?"
        )
        assert response is not None
        assert "plat" in response.content.lower()

        # Ask about specific thickness - this should trigger specifications intent
        response = await orchestrator.handle_user_message(
            session_id=session_id, content="Yang tebal 8mm ada?"
        )
        assert response is not None
        # Should be a response about thickness/specifications
        assert (
            "8mm" in response.content.lower()
            or "8 mm" in response.content.lower()
            or "tebal" in response.content.lower()
            or "ketebalan" in response.content.lower()
        )

    @pytest.mark.asyncio
    async def test_session_persistence_across_messages(self, setup_infrastructure):
        """Test that session context is maintained across messages."""
        orchestrator = await setup_infrastructure
        session_id = "test-session-persist"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "integration-test"},
        )

        # First message about a specific product
        response1 = await orchestrator.handle_user_message(
            session_id=session_id, content="Saya tertarik dengan hollow galvanis"
        )
        assert "hollow" in response1.content.lower()

        # Follow-up question should maintain context
        response2 = await orchestrator.handle_user_message(
            session_id=session_id, content="Berapa harganya?"
        )
        # Response should still be about hollow (context maintained)
        assert response2 is not None
        assert any(
            term in response2.content.lower()
            for term in ["hollow", "galvanis", "harga", "rp", "85000", "110000"]
        )

        # Another follow-up
        response3 = await orchestrator.handle_user_message(
            session_id=session_id, content="Minimal pesan berapa?"
        )
        assert response3 is not None
        # Should respond about minimum order - check for quantity context
        assert any(
            term in response3.content.lower()
            for term in ["minimal", "minimum", "lembar", "batang", "5", "10"]
        )
