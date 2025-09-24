"""Unit tests for ChatAgent implementation.

Focus on testing our code logic, not third-party libraries or LLM responses.
"""

import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies


class TestChatAgentInitialization:
    """Test ChatAgent initialization - focus on our configuration logic."""

    @patch("src.infrastructure.ai.chat_agent.OpenAIChatModel")
    @patch("src.infrastructure.ai.chat_agent.Agent")
    @patch.dict("os.environ", {}, clear=True)
    def test_initialization_with_explicit_api_key(self, mock_agent, mock_model):
        """Test that explicit API key is set in environment."""
        ChatAgent(api_key="explicit-key")
        assert os.environ.get("OPENAI_API_KEY") == "explicit-key"

    @patch("src.infrastructure.ai.chat_agent.OpenAIChatModel")
    @patch("src.infrastructure.ai.chat_agent.Agent")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})
    def test_initialization_from_environment(self, mock_agent, mock_model):
        """Test that environment variable is used when no explicit key."""
        ChatAgent()  # Should succeed with environment variable
        assert os.environ.get("OPENAI_API_KEY") == "env-key"

    def test_initialization_requires_api_key(self):
        """Test that initialization fails without any API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                ChatAgent()

    def test_create_with_fallback_handles_missing_key(self):
        """Test fallback mechanism when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            # Should return MockAIAgent instead
            from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

            agent = ChatAgent.create_with_fallback()
            assert isinstance(agent, MockAIAgent)


class TestChatAgentToolDataTransformation:
    """Test data transformation in tools - our code, not LLM behavior."""

    @pytest.mark.asyncio
    async def test_product_service_integration(self, mock_product_service):
        """Test that our code properly integrates with ProductService."""
        # This tests OUR integration code, not the service itself
        deps = ChatDependencies(product_service=mock_product_service, session_id="test")

        assert deps.product_service == mock_product_service
        assert deps.session_id == "test"

    def test_variant_data_transformation(self, variant):
        """Test that we correctly transform variant data for tools."""
        # Test our transformation logic using fixture from conftest
        variant_dict = {
            "variant_id": variant.variant_id,
            "sku": variant.sku,
            "name": variant.variant_name,
            "price": float(variant.price),
            "display_price": variant.get_display_price(),
            "stock": variant.stock_quantity,
            "stock_unit": variant.stock_unit,
            "available": variant.has_stock(),
            "specifications": variant.specifications,
        }

        assert variant_dict["price"] == 100000.0
        assert variant_dict["display_price"] == "Rp 100.000"
        assert variant_dict["available"] is True

    def test_product_with_variants_transformation(self, product_with_variants):
        """Test transformation of product with variants."""
        # Use fixture from conftest instead of local fixtures
        # Test our code's ability to extract data
        assert product_with_variants.product.product_name == "Plat Baja"
        assert len(product_with_variants.variants) == 2  # steel_plate_10mm and steel_plate_5mm
        assert product_with_variants.get_total_stock() == 75  # 25 + 50 from the two variants
        assert product_with_variants.has_available_stock() is True


class TestChatAgentErrorHandling:
    """Test error handling - important for production reliability."""

    @pytest.mark.asyncio
    async def test_handles_product_service_failure(self, chat_agent_with_mocked_llm):
        """Test graceful handling when product service fails."""
        mock_service = AsyncMock()
        mock_service.search_products.side_effect = Exception("Database down")

        # Mock LLM to fail
        chat_agent_with_mocked_llm.agent.run.side_effect = Exception("LLM error")

        response = await chat_agent_with_mocked_llm.generate_response(
            message="Test", product_service=mock_service
        )

        # Should return Indonesian error message from template
        assert "Mohon maaf" in response
        assert "kesalahan sistem" in response

    @pytest.mark.asyncio
    async def test_creates_mock_service_when_none_provided(
        self, chat_agent_with_mocked_llm
    ):
        """Test that mock service is created when none provided."""
        chat_agent_with_mocked_llm.agent.run.return_value = MagicMock(data="Response")

        with patch.object(
            chat_agent_with_mocked_llm, "_create_mock_product_service"
        ) as mock_create:
            mock_create.return_value = AsyncMock()

            await chat_agent_with_mocked_llm.generate_response(
                message="Test", product_service=None
            )

            mock_create.assert_called_once()


class TestChatAgentHelpers:
    """Test helper methods - these are deterministic and should be tested."""

    @patch("src.infrastructure.ai.chat_agent.OpenAIChatModel")
    @patch("src.infrastructure.ai.chat_agent.Agent")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_format_rupiah(self, mock_agent, mock_model):
        """Test Rupiah formatting helper."""
        agent = ChatAgent()

        assert agent._format_rupiah(Decimal("125000")) == "Rp 125.000"
        assert agent._format_rupiah(Decimal("1250000")) == "Rp 1.250.000"
        assert agent._format_rupiah(Decimal("999")) == "Rp 999"


class TestChatDependencies:
    """Test ChatDependencies dataclass."""

    def test_dependencies_with_all_fields(self):
        """Test ChatDependencies creation with all fields."""
        mock_service = Mock()
        deps = ChatDependencies(
            product_service=mock_service,
            session_id="test-123",
            user_metadata={"key": "value"},
        )

        assert deps.product_service == mock_service
        assert deps.session_id == "test-123"
        assert deps.user_metadata["key"] == "value"

    def test_dependencies_with_optional_metadata(self):
        """Test ChatDependencies with None metadata."""
        mock_service = Mock()
        deps = ChatDependencies(product_service=mock_service, session_id="test-456")

        assert deps.user_metadata is None
