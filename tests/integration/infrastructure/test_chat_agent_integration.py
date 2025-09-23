"""Integration tests for ChatAgent with mock services.

These tests verify the integration between ChatAgent and other components,
without testing LLM responses or third-party library internals.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.dto import MessageDTO
from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo, VariantInfo
from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies
from src.infrastructure.mocks.mock_product_repository import MockProductRepository


class TestChatAgentIntegrationWithMockServices:
    """Test ChatAgent integration with mock services."""

    @pytest.fixture
    def mock_product_repository(self):
        """Create actual MockProductRepository instance."""
        return MockProductRepository()

    @pytest.fixture
    def chat_agent_with_mocks(self):
        """Create ChatAgent with mocked LLM but real mock services."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent") as MockAgent:
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    # Create a mock agent that we can control
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run = AsyncMock()
                    MockAgent.return_value = mock_agent_instance

                    agent = ChatAgent()
                    # Replace the agent with our controlled mock
                    agent.agent = mock_agent_instance
                    return agent

    @pytest.mark.asyncio
    async def test_integration_with_mock_product_service(
        self, chat_agent_with_mocks, mock_product_repository
    ):
        """Test that ChatAgent properly integrates with MockProductRepository."""
        # Setup mock LLM response
        mock_response = MagicMock()
        mock_response.data = "Saya akan membantu mencari produk."
        chat_agent_with_mocks.agent.run.return_value = mock_response

        # Use actual mock product repository
        response = await chat_agent_with_mocks.generate_response(
            message="Cari plat baja",
            product_service=mock_product_repository,
            session_id="test-session",
        )

        # Verify the integration happened
        assert response is not None
        chat_agent_with_mocks.agent.run.assert_called_once()

        # Verify dependencies were passed correctly
        call_args = chat_agent_with_mocks.agent.run.call_args
        assert "deps" in call_args.kwargs
        deps = call_args.kwargs["deps"]
        assert isinstance(deps, ChatDependencies)
        assert deps.product_service == mock_product_repository
        assert deps.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_message_context_transformation(self, chat_agent_with_mocks):
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
        chat_agent_with_mocks.agent.run.return_value = mock_response

        await chat_agent_with_mocks.generate_response(
            message="Berapa harganya?",
            conversation_context=messages,
            product_service=AsyncMock(),
        )

        # Check that message history was passed correctly
        call_args = chat_agent_with_mocks.agent.run.call_args
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

    @pytest.fixture
    def chat_agent_controlled(self):
        """Create ChatAgent with controlled responses."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    agent = ChatAgent()
                    agent.agent = MagicMock()
                    agent.agent.run = AsyncMock()
                    return agent

    @pytest.mark.asyncio
    async def test_conversation_flow(self, chat_agent_controlled):
        """Test a typical conversation flow."""
        # Simulate a conversation with controlled responses
        responses = [
            "Selamat datang di SMS Perkasa!",
            "Kami punya berbagai jenis plat baja.",
            "Plat baja 5mm harganya Rp 125.000 per lembar.",
        ]

        conversation = []

        for i, user_message in enumerate(
            ["Halo", "Ada plat baja?", "Berapa harga plat 5mm?"]
        ):
            # Set up mock response
            mock_result = MagicMock()
            mock_result.data = responses[i]
            chat_agent_controlled.agent.run.return_value = mock_result

            response = await chat_agent_controlled.generate_response(
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
    async def test_handles_service_unavailable(self, chat_agent_controlled):
        """Test handling when services are unavailable."""
        # Make the LLM call fail
        chat_agent_controlled.agent.run.side_effect = Exception("Service unavailable")

        response = await chat_agent_controlled.generate_response(
            message="Test message", product_service=None
        )

        # Should return the fallback Indonesian message
        assert "Mohon maaf" in response
        assert "kesulitan" in response
