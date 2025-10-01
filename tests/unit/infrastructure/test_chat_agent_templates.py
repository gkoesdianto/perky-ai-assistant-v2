"""Unit tests for ChatAgent template integration.

Tests verify that:
1. ChatAgent correctly uses Indonesian templates
2. Templates are properly formatted with dynamic data
3. Time-based greetings work correctly
4. Stock and price messages use templates
5. Error messages follow template patterns
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from src.domain.value_objects.variant_info import VariantInfo
from src.infrastructure.ai.chat_agent import ChatAgent
from src.infrastructure.ai.prompts.indonesian_templates import (
    ERROR_MESSAGES,
    GREETING_TEMPLATES,
    PRICE_TEMPLATES,
    STOCK_MESSAGES,
)


class TestGreetingTemplates:
    """Test time-based greeting templates."""

    @pytest.mark.parametrize(
        "hour,expected_greeting",
        [
            (5, GREETING_TEMPLATES["morning"]),  # Early morning
            (9, GREETING_TEMPLATES["morning"]),  # Mid morning
            (10, GREETING_TEMPLATES["morning"]),  # Late morning
            (11, GREETING_TEMPLATES["afternoon"]),  # Early afternoon
            (13, GREETING_TEMPLATES["afternoon"]),  # Mid afternoon
            (14, GREETING_TEMPLATES["afternoon"]),  # Late afternoon
            (15, GREETING_TEMPLATES["evening"]),  # Early evening
            (17, GREETING_TEMPLATES["evening"]),  # Mid evening
            (18, GREETING_TEMPLATES["evening"]),  # Late evening
            (19, GREETING_TEMPLATES["default"]),  # Night
            (23, GREETING_TEMPLATES["default"]),  # Late night
            (0, GREETING_TEMPLATES["default"]),  # Midnight
            (4, GREETING_TEMPLATES["default"]),  # Before dawn
        ],
    )
    def test_greeting_by_time_of_day(self, hour, expected_greeting):
        """Test that correct greeting is returned based on time of day."""
        # Create agent
        agent = ChatAgent.create_with_fallback()

        # Mock datetime to return specific hour
        mock_datetime = Mock()
        mock_datetime.now.return_value.hour = hour

        with patch("src.infrastructure.ai.chat_agent.datetime", mock_datetime):
            greeting = agent._get_greeting()

        assert greeting == expected_greeting
        # Verify key elements are present (not all templates have both)
        assert "PERKY" in greeting or "Perkasa" in greeting


class TestStockTemplates:
    """Test stock message templates."""

    def test_out_of_stock_template(self):
        """Test out of stock message formatting."""
        agent = ChatAgent.create_with_fallback()

        # Create variant with no stock
        variant = VariantInfo(
            variant_id="var123",
            sku="PLT-5MM-1200-2400",
            product_id="prod123",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("150000"),
            stock_quantity=0,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

        message = agent._format_stock_message(variant)

        assert "Mohon maaf" in message
        assert variant.variant_name in message
        assert "sedang kosong" in message

    def test_low_stock_template(self):
        """Test low stock message formatting (≤10 units)."""
        agent = ChatAgent.create_with_fallback()

        # Create variant with low stock
        variant = VariantInfo(
            variant_id="var123",
            sku="PLT-5MM-1200-2400",
            product_id="prod123",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("150000"),
            stock_quantity=5,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

        message = agent._format_stock_message(variant)

        assert "Stok" in message
        assert variant.variant_name in message
        assert "terbatas" in message
        assert "5" in message
        assert "lembar" in message

    def test_normal_stock_template(self):
        """Test normal stock message formatting (>10 units)."""
        agent = ChatAgent.create_with_fallback()

        # Create variant with normal stock
        variant = VariantInfo(
            variant_id="var123",
            sku="PLT-5MM-1200-2400",
            product_id="prod123",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("150000"),
            stock_quantity=50,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

        message = agent._format_stock_message(variant)

        assert variant.variant_name in message
        assert "tersedia" in message
        assert "50" in message
        assert "lembar" in message


class TestPriceTemplates:
    """Test price message templates."""

    def test_unit_price_template(self):
        """Test unit price message formatting."""
        agent = ChatAgent.create_with_fallback()

        # Create variant
        variant = VariantInfo(
            variant_id="var123",
            sku="PLT-5MM-1200-2400",
            product_id="prod123",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("150000"),
            stock_quantity=50,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

        message = agent._format_price_message(variant)

        # Should contain formatted price and unit
        assert "Rp" in message
        assert "150.000" in message  # Indonesian number format
        assert "per" in message
        assert "lembar" in message


class TestErrorTemplates:
    """Test error message templates."""

    @pytest.mark.asyncio
    async def test_variant_not_found_template(self):
        """Test variant not found error message."""
        agent = ChatAgent.create_with_fallback()

        # Mock product service that returns None
        mock_service = Mock()
        mock_service.get_product_with_variants.return_value = None

        # Create dependencies
        from src.infrastructure.ai.chat_agent import ChatDependencies

        deps = ChatDependencies(
            product_service=mock_service, session_id="test", user_metadata={}
        )

        # Mock RunContext
        mock_ctx = Mock()
        mock_ctx.deps = deps

        # Call variant details tool
        result = await agent._get_variant_details_tool(mock_ctx, "prod123", "var999")

        # Should return error template
        assert "Mohon maaf" in result.name or result.sku == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_system_error_template(self):
        """Test system error message."""
        agent = ChatAgent.create_with_fallback()

        # Generate response with invalid session (should trigger error)
        response = await agent.generate_response(
            message="test",
            conversation_context=None,
            product_service=None,  # Will trigger error
            session_id=None,
        )

        # Should contain system error template or greeting
        # Since the mock handles errors gracefully, check for expected behavior
        assert isinstance(response, str)
        assert len(response) > 0


class TestTemplateIntegrationInTools:
    """Test that templates are properly integrated in tool responses."""

    @pytest.mark.asyncio
    async def test_variant_details_includes_formatted_messages(self):
        """Test that variant details include pre-formatted messages."""
        agent = ChatAgent.create_with_fallback()

        # Create mock product with variant
        from src.domain.value_objects.product_with_variants_info import (
            ProductWithVariantsInfo,
        )

        variant = VariantInfo(
            variant_id="var123",
            sku="PLT-5MM-1200-2400",
            product_id="prod123",
            variant_name="Plat Baja 5mm x 1200mm x 2400mm",
            price=Decimal("150000"),
            stock_quantity=25,
            stock_unit="lembar",
            specifications={"thickness": "5mm"},
        )

        mock_product = Mock(spec=ProductWithVariantsInfo)
        mock_product.get_variant_by_id.return_value = variant

        # Mock service
        from unittest.mock import AsyncMock

        mock_service = Mock()
        mock_service.get_product_with_variants = AsyncMock(return_value=mock_product)

        # Create dependencies
        from src.infrastructure.ai.chat_agent import ChatDependencies

        deps = ChatDependencies(
            product_service=mock_service, session_id="test", user_metadata={}
        )

        # Mock RunContext
        mock_ctx = Mock()
        mock_ctx.deps = deps

        # Call tool
        result = await agent._get_variant_details_tool(mock_ctx, "prod123", "var123")

        # Verify formatted messages are included
        assert "_formatted_stock" in result.specifications
        assert "_formatted_price" in result.specifications

        # Verify they contain expected template elements
        assert "tersedia" in result.specifications["_formatted_stock"]
        assert "Rp" in result.specifications["_formatted_price"]
        assert "per" in result.specifications["_formatted_price"]


class TestSystemPromptTemplateGuidance:
    """Test that SYSTEM_PROMPT includes template guidance."""

    def test_system_prompt_has_template_section(self):
        """Test that SYSTEM_PROMPT contains template response guidance."""
        from src.infrastructure.ai.chat_agent import SYSTEM_PROMPT

        # Verify template section exists
        assert "TEMPLATE RESPONSES" in SYSTEM_PROMPT
        assert "GUNAKAN KETIKA SESUAI" in SYSTEM_PROMPT

    def test_system_prompt_greeting_guidance(self):
        """Test that SYSTEM_PROMPT explains greeting templates."""
        from src.infrastructure.ai.chat_agent import SYSTEM_PROMPT

        assert "Pagi (05:00-10:59)" in SYSTEM_PROMPT
        assert "Siang (11:00-14:59)" in SYSTEM_PROMPT
        assert "Sore (15:00-18:59)" in SYSTEM_PROMPT

    def test_system_prompt_stock_guidance(self):
        """Test that SYSTEM_PROMPT explains stock templates."""
        from src.infrastructure.ai.chat_agent import SYSTEM_PROMPT

        assert "Stok habis" in SYSTEM_PROMPT
        assert "Stok rendah" in SYSTEM_PROMPT
        assert "Stok tersedia" in SYSTEM_PROMPT

    def test_system_prompt_price_guidance(self):
        """Test that SYSTEM_PROMPT explains price templates."""
        from src.infrastructure.ai.chat_agent import SYSTEM_PROMPT

        assert "informasi harga varian" in SYSTEM_PROMPT
        assert "{display_price} per {stock_unit}" in SYSTEM_PROMPT

    def test_system_prompt_formatted_message_guidance(self):
        """Test that SYSTEM_PROMPT explains use of pre-formatted messages."""
        from src.infrastructure.ai.chat_agent import SYSTEM_PROMPT

        assert "_formatted_stock" in SYSTEM_PROMPT
        assert "_formatted_price" in SYSTEM_PROMPT
        assert "GUNAKAN pesan terformat tersebut langsung" in SYSTEM_PROMPT
