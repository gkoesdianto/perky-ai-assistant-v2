"""Integration tests for ChatAgent with mock services.

These tests verify the integration between ChatAgent and other components,
without testing LLM responses or third-party library internals.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.dto import MessageDTO
from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent


class TestChatAgentIntegrationWithMockServices:
    """Test ChatAgent integration with mock services."""

    @pytest.mark.asyncio
    async def test_integration_with_mock_product_service(
        self, mock_ai_agent, mock_product_service
    ):
        """Test that ChatAgent properly integrates with mock product service."""
        response = await mock_ai_agent.generate_response(
            message="Cari plat baja",
            product_service=mock_product_service,
            session_id="test-session",
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_message_context_handling(self, mock_ai_agent):
        """Test that message context is properly handled."""
        sample_messages = [
            MessageDTO(
                conversation_id="conv-1",
                content="Ada plat baja?",
                sender_type="user",
                session_id="test-session",
                timestamp=None,
            ),
            MessageDTO(
                conversation_id="conv-1",
                content="Ya, kami memiliki berbagai jenis plat baja.",
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=None,
            ),
        ]

        response = await mock_ai_agent.generate_response(
            message="Berapa harganya?",
            conversation_context=sample_messages,
            product_service=AsyncMock(),
        )

        assert response is not None
        assert isinstance(response, str)


class TestChatAgentFallbackMechanism:
    """Test the fallback mechanism for missing API keys."""

    @pytest.mark.asyncio
    async def test_fallback_to_mock_agent(self):
        """Test that system falls back to MockAIAgent when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            agent = ChatAgent.create_with_fallback()

            assert isinstance(agent, MockAIAgent)

            # Test that the mock agent can generate responses
            response = await agent.generate_response(
                message="Halo", conversation_context=None
            )

            # MockAIAgent should return Indonesian responses
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_fallback_agent_handles_product_queries(self):
        """Test that fallback agent can handle product-related queries."""
        with patch.dict("os.environ", {}, clear=True):
            agent = ChatAgent.create_with_fallback()

            # Test various product queries
            queries = ["harga plat baja", "stok hollow", "ada h-beam?"]

            for query in queries:
                response = await agent.generate_response(
                    message=query, conversation_context=None
                )
                assert isinstance(response, str)
                assert len(response) > 0


class TestChatAgentRealWorldScenarios:
    """Test realistic usage scenarios without depending on LLM responses."""

    @pytest.mark.asyncio
    async def test_conversation_flow(self, mock_ai_agent):
        """Test a typical conversation flow."""
        conversation = []

        user_message = "Halo"
        response = await mock_ai_agent.generate_response(
            message=user_message,
            conversation_context=conversation,
            product_service=AsyncMock(),
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        conversation.append(
            MessageDTO(
                conversation_id="conv-1",
                content=user_message,
                sender_type="user",
                session_id="test-session",
                timestamp=None,
            )
        )
        conversation.append(
            MessageDTO(
                conversation_id="conv-1",
                content=response,
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=None,
            )
        )

        for user_message in ["Ada plat baja?", "Berapa harga plat 5mm?"]:
            response = await mock_ai_agent.generate_response(
                message=user_message,
                conversation_context=conversation,
                product_service=AsyncMock(),
            )

            conversation.append(
                MessageDTO(
                    conversation_id="conv-1",
                    content=user_message,
                    sender_type="user",
                    session_id="test-session",
                    timestamp=None,
                )
            )
            conversation.append(
                MessageDTO(
                    conversation_id="conv-1",
                    content=response,
                    sender_type="ai_agent",
                    session_id="test-session",
                    timestamp=None,
                )
            )

            assert response is not None
            assert isinstance(response, str)

        assert len(conversation) == 6

    @pytest.mark.asyncio
    async def test_handles_service_unavailable(self):
        """Test handling when services are unavailable."""
        # Create a real MockAIAgent instance
        agent = MockAIAgent()

        # Set error rate to always fail
        agent.error_simulator.error_rate = 1.0

        with pytest.raises(Exception, match="Simulated failure"):
            await agent.generate_response(
                message="Test message",
                conversation_context=None
            )
