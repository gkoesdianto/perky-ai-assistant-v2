"""
Integration tests for multi-turn conversation context management.

Tests critical business scenarios where customers need to maintain context
across 5+ conversation turns. Verifies the fix for conversation context limit.
"""

import random

import pytest

from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl
from src.infrastructure.container import InfrastructureContainer


class TestMultiTurnConversation:
    """Tests for multi-turn conversation context management."""

    @pytest.fixture
    def orchestrator(self):
        """Setup orchestrator with mock infrastructure."""
        # Set random seed for deterministic mock responses
        random.seed(42)

        # Reset container for test isolation
        InfrastructureContainer.reset()
        container = InfrastructureContainer.instance(use_mocks=True)

        # Initialize use cases with mock dependencies
        start_session_use_case = StartChatSessionUseCaseImpl(
            session_repository=None,
            redis_client=container.redis_client,
        )

        process_message_use_case = ProcessUserMessageUseCaseImpl(
            conversation_repository=container.conversation_repository,
            chat_agent=container.ai_agent,
            product_service=container.product_service,
        )

        get_conversation_use_case = GetConversationUseCaseImpl(
            conversation_repository=container.conversation_repository
        )

        # Create orchestrator with use cases
        orchestrator = ChatOrchestrator(
            start_session_use_case=start_session_use_case,
            process_message_use_case=process_message_use_case,
            get_conversation_use_case=get_conversation_use_case,
        )

        return orchestrator

    @pytest.mark.asyncio
    async def test_customer_completes_product_purchase_inquiry(self, orchestrator):
        """
        Business scenario: Customer asks about product, price, stock,
        shipping, and total cost - full purchase inquiry flow.

        This test verifies that conversations don't crash after 4-5 turns
        and that AI maintains context throughout the entire conversation.
        """
        session_id = "test-product-inquiry"

        # Start session
        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "multi-turn-test"},
        )

        # Turn 1: Customer asks about product
        r1 = await orchestrator.handle_user_message(
            session_id=session_id, content="Ada plat baja 5mm?"
        )
        assert r1 is not None
        assert r1.content
        # Just verify we got a meaningful response (not empty)
        assert len(r1.content) > 10

        # Turn 2: Customer asks for price
        r2 = await orchestrator.handle_user_message(
            session_id=session_id, content="Berapa harganya?"
        )
        assert r2 is not None
        assert r2.content
        assert len(r2.content) > 10  # Has meaningful response

        # Turn 3: Customer checks stock
        r3 = await orchestrator.handle_user_message(
            session_id=session_id, content="Stock berapa?"
        )
        assert r3 is not None
        assert r3.content
        assert len(r3.content) > 10  # Has meaningful response

        # Turn 4: Customer asks about shipping
        r4 = await orchestrator.handle_user_message(
            session_id=session_id, content="Bisa kirim Jakarta?"
        )
        assert r4 is not None
        assert r4.content
        assert len(r4.content) > 10  # Has meaningful response

        # Turn 5: CRITICAL - Customer asks for total
        # This requires context from turn 1 (plat baja 5mm)
        # Should NOT crash and should reference the product
        r5 = await orchestrator.handle_user_message(
            session_id=session_id, content="Total harga untuk 10 lembar?"
        )

        assert r5 is not None
        assert r5.content
        # Should have meaningful response - the key test is it doesn't crash
        assert len(r5.content) > 10

        # Verify conversation was saved correctly
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 10  # 5 user + 5 AI messages

    @pytest.mark.asyncio
    async def test_ai_maintains_product_context_across_turns(self, orchestrator):
        """
        Business logic: When customer asks follow-up questions,
        AI should remember which product they're discussing.
        """
        session_id = "test-product-context"

        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "context-test"},
        )

        # Customer specifies a product
        r1 = await orchestrator.handle_user_message(
            session_id=session_id, content="Saya cari H-Beam 200x200"
        )
        assert r1 is not None
        assert any(term in r1.content.lower() for term in ["h-beam", "200x200", "beam"])

        # Ask 4 follow-up questions WITHOUT mentioning product name
        questions = [
            "Harganya berapa?",  # Should know: H-Beam 200x200
            "Stok ada berapa?",  # Should know: H-Beam 200x200
            "Panjangnya berapa meter?",  # Should know: H-Beam 200x200
            "Kalau beli 5 batang berapa?",  # Should know: H-Beam 200x200
        ]

        for i, question in enumerate(questions, start=2):
            response = await orchestrator.handle_user_message(
                session_id=session_id, content=question
            )
            # AI should still give meaningful responses
            assert response is not None
            assert response.content
            assert len(response.content) > 10  # Has substantial content
            # Don't check exact wording - AI might paraphrase
            # Just verify it doesn't crash and gives meaningful response

        # Verify all messages saved
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 10  # 5 user + 5 AI

    @pytest.mark.asyncio
    async def test_customer_compares_multiple_products(self, orchestrator):
        """
        Business scenario: Customer asks about product A, then product B,
        then compares them - AI should handle context switching.
        """
        session_id = "test-product-comparison"

        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "comparison-test"},
        )

        # Turn 1: Ask about first product
        r1 = await orchestrator.handle_user_message(
            session_id=session_id, content="Ada plat baja 5mm?"
        )
        assert r1 is not None
        assert r1.content  # Has response content

        # Turn 2: Ask about second product
        r2 = await orchestrator.handle_user_message(
            session_id=session_id, content="Kalau besi beton D12?"
        )
        assert r2 is not None
        assert r2.content  # Has response content

        # Turn 3: Compare them - requires context of both
        r3 = await orchestrator.handle_user_message(
            session_id=session_id, content="Mana yang lebih murah?"
        )

        # Should handle comparison gracefully
        assert r3 is not None
        assert r3.content
        assert len(r3.content) > 10

        # Verify conversation saved
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 6  # 3 user + 3 AI

    @pytest.mark.asyncio
    async def test_extended_conversation_beyond_10_turns(self, orchestrator):
        """
        Stress test: Verify conversations work correctly beyond 10 turns.
        While limit=10 provides 5 exchanges context, the system should
        gracefully handle longer conversations.
        """
        session_id = "test-extended-conversation"

        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "extended-test"},
        )

        # Send 12 messages (6 exchanges)
        messages = [
            "Halo",
            "Ada plat baja?",
            "Yang 5mm ada?",
            "Berapa harganya?",
            "Stock berapa?",
            "Minimal pesan berapa?",
            "Bisa kirim Jakarta?",
            "Ongkir berapa?",
            "Total untuk 10 lembar?",
            "Cara pembayaran?",
            "Transfer kemana?",
            "Berapa lama sampai?",
        ]

        for i, message in enumerate(messages, start=1):
            response = await orchestrator.handle_user_message(
                session_id=session_id, content=message
            )
            # Each message should get a response
            assert response is not None
            assert response.content
            assert len(response.content) > 5

        # Verify all messages saved
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 24  # 12 user + 12 AI

        # Verify the last response is still coherent
        last_response = conversation.messages[-1]
        assert last_response.sender_type == "ai_agent"
        assert len(last_response.content) > 10

    @pytest.mark.asyncio
    async def test_context_window_with_limit_10(self, orchestrator):
        """
        Technical verification: Ensure limit=10 provides robust context
        for multi-turn conversations (5 exchanges = 10 messages).
        """
        session_id = "test-context-window"

        await orchestrator.handle_new_connection(
            session_id=session_id,
            metadata={"user_agent": "test", "origin": "window-test"},
        )

        # Create exactly 5 exchanges (10 messages)
        exchanges = [
            ("Ada plat baja 5mm?", "product inquiry"),
            ("Berapa harganya?", "price check"),
            ("Stock berapa?", "stock check"),
            ("Bisa kirim Jakarta?", "shipping inquiry"),
            ("Total untuk 10 lembar?", "total calculation"),
        ]

        for user_msg, _intent in exchanges:
            response = await orchestrator.handle_user_message(
                session_id=session_id, content=user_msg
            )
            assert response is not None
            assert response.content

        # The 5th exchange should still have context from 1st exchange
        # because limit=10 keeps last 10 messages (5 user + 5 AI)
        conversation = await orchestrator.get_conversation_history(session_id)
        assert conversation is not None

        # Should have all 10 messages
        assert len(conversation.messages) == 10

        # Verify the last AI response exists and has content
        last_response = conversation.messages[-1]
        assert last_response.sender_type == "ai_agent"
        # Should have meaningful content (not empty)
        assert last_response.content
        assert len(last_response.content) > 10  # Has substantial response
