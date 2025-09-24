"""Integration tests for ChatAgent with mock services.

These tests verify the integration between ChatAgent and other components,
without testing LLM responses or third-party library internals.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import os

import pytest

from src.application.dto import MessageDTO
from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies


class TestChatAgentIntegrationWithMockServices:
    """Test ChatAgent integration with mock services."""

    @pytest.mark.asyncio
    async def test_integration_with_mock_product_service(
        self, chat_agent_with_mocked_llm, mock_product_service
    ):
        """Test that ChatAgent properly integrates with mock product service."""
        mock_response = MagicMock()
        mock_response.data = "Saya akan membantu mencari produk."
        chat_agent_with_mocked_llm.agent.run.return_value = mock_response

        response = await chat_agent_with_mocked_llm.generate_response(
            message="Cari plat baja",
            product_service=mock_product_service,
            session_id="test-session",
        )

        assert response is not None
        chat_agent_with_mocked_llm.agent.run.assert_called_once()

        call_args = chat_agent_with_mocked_llm.agent.run.call_args
        assert "deps" in call_args.kwargs
        deps = call_args.kwargs["deps"]
        assert isinstance(deps, ChatDependencies)
        assert deps.product_service == mock_product_service
        assert deps.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_message_context_transformation(self, chat_agent_with_mocked_llm):
        """Test that message context is properly transformed for the LLM."""
        # Create sample messages
        messages = [
            MessageDTO(
                conversation_id="conv-1",
                content="Halo",
                sender_type="user",
                session_id="test-session",
                timestamp=None,
            ),
            MessageDTO(
                conversation_id="conv-1",
                content="Selamat datang",
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=None,
            ),
            MessageDTO(
                conversation_id="conv-1",
                content="Ada plat baja?",
                sender_type="user",
                session_id="test-session",
                timestamp=None,
            ),
        ]

        mock_response = MagicMock()
        mock_response.data = "Ya, ada"
        chat_agent_with_mocked_llm.agent.run.return_value = mock_response

        await chat_agent_with_mocked_llm.generate_response(
            message="Berapa harganya?",
            conversation_context=messages,
            product_service=AsyncMock(),
        )

        # Check that message history was passed correctly
        call_args = chat_agent_with_mocked_llm.agent.run.call_args
        message_history = call_args.kwargs.get("message_history", [])

        # Should have the 3 previous messages as tuples
        assert len(message_history) == 3
        assert message_history[0] == ("user", "Halo")
        assert message_history[1] == ("assistant", "Selamat datang")
        assert message_history[2] == ("user", "Ada plat baja?")


class TestChatAgentFallbackMechanism:
    """Test the fallback mechanism for missing API keys."""

    @pytest.mark.asyncio
    async def test_fallback_to_mock_agent(self):
        """Test that system falls back to MockAIAgent when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            agent = ChatAgent.create_with_fallback()

            from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

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
    async def test_conversation_flow(self, chat_agent_with_mocked_llm):
        """Test a typical conversation flow."""
        # Get the appropriate greeting based on current time
        from datetime import datetime
        from src.infrastructure.ai.prompts.indonesian_templates import GREETING_TEMPLATES

        hour = datetime.now().hour
        if 5 <= hour < 11:
            expected_greeting = GREETING_TEMPLATES["morning"]
        elif 11 <= hour < 15:
            expected_greeting = GREETING_TEMPLATES["afternoon"]
        elif 15 <= hour < 19:
            expected_greeting = GREETING_TEMPLATES["evening"]
        else:
            expected_greeting = GREETING_TEMPLATES["default"]

        # Simulate a conversation with controlled responses
        responses = [
            "Kami punya berbagai jenis plat baja.",
            "Plat baja 5mm harganya Rp 125.000 per lembar.",
        ]

        conversation = []

        # First message - greeting detection
        user_message = "Halo"
        response = await chat_agent_with_mocked_llm.generate_response(
            message=user_message,
            conversation_context=conversation,
            product_service=AsyncMock(),
        )

        # Should return template-based greeting
        assert response == expected_greeting

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

        # Subsequent messages - use LLM
        for i, user_message in enumerate(["Ada plat baja?", "Berapa harga plat 5mm?"]):
            # Set up mock response
            mock_result = MagicMock()
            mock_result.data = responses[i]
            chat_agent_with_mocked_llm.agent.run.return_value = mock_result

            response = await chat_agent_with_mocked_llm.generate_response(
                message=user_message,
                conversation_context=conversation,
                product_service=AsyncMock(),
            )

            # Add to conversation
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

            assert response == responses[i]

        # Verify conversation built correctly
        assert len(conversation) == 6  # 3 user + 3 agent messages

    @pytest.mark.asyncio
    async def test_handles_service_unavailable(self, chat_agent_with_mocked_llm):
        """Test handling when services are unavailable."""
        # Make the LLM call fail
        chat_agent_with_mocked_llm.agent.run.side_effect = Exception("Service unavailable")

        response = await chat_agent_with_mocked_llm.generate_response(
            message="Test message", product_service=None
        )

        # Should return the template-based error message
        assert "Mohon maaf" in response
        assert "kesalahan sistem" in response
