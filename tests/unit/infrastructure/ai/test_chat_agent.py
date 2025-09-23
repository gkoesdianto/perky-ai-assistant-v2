"""Unit tests for ChatAgent implementation.

Focus on testing our code logic, not third-party libraries or LLM responses.
"""

import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.application.dto import MessageDTO
from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo, VariantInfo
from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies


class TestChatAgentInitialization:
    """Test ChatAgent initialization - focus on our configuration logic."""

    def test_initialization_with_explicit_api_key(self):
        """Test that explicit API key is set in environment."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    ChatAgent(api_key="explicit-key")
                    assert os.environ.get("OPENAI_API_KEY") == "explicit-key"

    def test_initialization_from_environment(self):
        """Test that environment variable is used when no explicit key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
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

    @pytest.fixture
    def mock_product_service(self):
        """Create mock product service."""
        return AsyncMock()

    @pytest.fixture
    def sample_product(self):
        """Create a sample product."""
        return ProductInfo(
            product_id="prod-1",
            product_name="Plat Baja",
            product_description="Steel plates",
            category="Plates",
            variant_count=3,
        )

    @pytest.fixture
    def sample_variant(self):
        """Create a sample variant."""
        return VariantInfo(
            variant_id="var-1",
            sku="PLT-5MM",
            product_id="prod-1",
            variant_name="Plat Baja 5mm",
            price=Decimal("125000"),
            stock_quantity=100,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

    @pytest.mark.asyncio
    async def test_product_service_integration(self, mock_product_service):
        """Test that our code properly integrates with ProductService."""
        # This tests OUR integration code, not the service itself
        deps = ChatDependencies(product_service=mock_product_service, session_id="test")

        assert deps.product_service == mock_product_service
        assert deps.session_id == "test"

    def test_variant_data_transformation(self, sample_variant):
        """Test that we correctly transform variant data for tools."""
        # Test our transformation logic
        variant_dict = {
            "variant_id": sample_variant.variant_id,
            "sku": sample_variant.sku,
            "name": sample_variant.variant_name,
            "price": float(sample_variant.price),
            "display_price": sample_variant.get_display_price(),
            "stock": sample_variant.stock_quantity,
            "stock_unit": sample_variant.stock_unit,
            "available": sample_variant.has_stock(),
            "specifications": sample_variant.specifications,
        }

        assert variant_dict["price"] == 125000.0
        assert variant_dict["display_price"] == "Rp 125.000"
        assert variant_dict["available"] is True

    def test_product_with_variants_transformation(self, sample_product, sample_variant):
        """Test transformation of product with variants."""
        product_with_variants = ProductWithVariantsInfo(
            product=sample_product, variants=[sample_variant]
        )

        # Test our code's ability to extract data
        assert product_with_variants.product.product_name == "Plat Baja"
        assert len(product_with_variants.variants) == 1
        assert product_with_variants.get_total_stock() == 100
        assert product_with_variants.has_available_stock() is True


class TestChatAgentErrorHandling:
    """Test error handling - important for production reliability."""

    @pytest.fixture
    def chat_agent_with_mocked_llm(self):
        """Create ChatAgent with mocked LLM calls."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    agent = ChatAgent()
                    agent.agent = MagicMock()
                    agent.agent.run = AsyncMock()
                    return agent

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

        # Should return Indonesian error message
        assert "Mohon maaf" in response
        assert "kesulitan" in response

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

    def test_format_rupiah(self):
        """Test Rupiah formatting helper."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
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
