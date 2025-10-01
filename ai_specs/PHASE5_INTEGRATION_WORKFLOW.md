# Phase 5: Integration & Testing - Comprehensive Implementation Workflow

## Executive Summary

This document provides a **systematic, deep, and parallel-optimized workflow** for
implementing Phase 5 of the Steel Chat MVP, focusing on PydanticAI integration, mock
services, and comprehensive testing. The workflow is designed for **Days 4-5** of
the MVP sprint, enabling multiple teams to work in parallel while maintaining clear
convergence points.

**Key Deliverables**:
- ✅ Fully integrated PydanticAI chat agent with Indonesian language support
- ✅ Mock product service with realistic steel industry data
- ✅ Complete dependency injection system
- ✅ WebSocket integration with real-time chat
- ✅ Comprehensive testing suite (unit, integration, E2E)
- ✅ Working internal MVP ready for stakeholder demo

**Parallel Execution**: 5 independent tracks that can run simultaneously, converging at defined integration points.

---

## Table of Contents

1. [Prerequisites & Dependencies](#prerequisites--dependencies)
2. [Parallel Execution Strategy](#parallel-execution-strategy)
3. [Track 1: PydanticAI Agent Implementation](#track-1-pydanticai-agent-implementation)
4. [Track 2: Mock Services & Repositories](#track-2-mock-services--repositories)
5. [Track 3: Dependency Injection System](#track-3-dependency-injection-system)
6. [Track 4: Main Application Integration](#track-4-main-application-integration)
7. [Track 5: Testing Infrastructure](#track-5-testing-infrastructure)
8. [Integration & Convergence Points](#integration--convergence-points)
9. [Quality Gates & Validation](#quality-gates--validation)
10. [Risk Mitigation](#risk-mitigation)
11. [Success Criteria](#success-criteria)

---

## Prerequisites & Dependencies

### Required Completed Phases

- ✅ **Phase 1**: Application Layer Foundation (DTOs, Use Cases, Service Protocols)
- ✅ **Phase 2**: Single Agent Implementation scaffolding
- ✅ **Phase 3**: Mock Infrastructure basics
- ✅ **Phase 4**: WebSocket Integration

### Environment Configuration

```bash
# .env file configuration
OPENAI_API_KEY=sk-...  # Required for PydanticAI
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7
USE_MOCK_MODE=true  # Use mock PIM data for MVP
REDIS_URL=redis://localhost:6379/0  # Optional for MVP
SESSION_TTL_SECONDS=3600
```

### Dependency Verification

```python
# requirements/base.txt (Verify these are installed)
pydantic-ai==1.0.1      # AI agent framework
openai==1.57.0          # OpenAI client
fastapi==0.115.5        # Web framework
uvicorn[standard]==0.32.1  # ASGI server
redis==5.2.0            # Session management (optional for MVP)
httpx==0.27.2           # Async HTTP client
```

---

## Parallel Execution Strategy

### Team Distribution & Timing

```text
gantt
    title Phase 5 Parallel Execution Timeline
    dateFormat HH:mm
    section Track 1
    PydanticAI Agent    :active, t1, 00:00, 4h
    section Track 2
    Mock Services       :active, t2, 00:00, 3h
    section Track 3
    Dependency Injection :active, t3, 00:00, 2h
    section Track 4
    Main App Integration :t4, 02:00, 3h
    section Track 5
    Testing Infrastructure :active, t5, 00:00, 4h
    section Integration
    Convergence Point 1  :milestone, m1, 03:00, 0h
    Final Integration    :crit, int, 04:00, 2h
    E2E Testing         :e2e, 06:00, 2h
```

### Resource Allocation

| Track | Team Size | Skills Required | Dependencies |
|-------|-----------|----------------|--------------|
| Track 1 | 2 devs | AI/LLM, Python async | OpenAI API key |
| Track 2 | 1 dev | Python, domain knowledge | Product data |
| Track 3 | 1 dev | Python, DI patterns | Use case interfaces |
| Track 4 | 1 dev | FastAPI, WebSocket | Tracks 1-3 |
| Track 5 | 2 devs | Testing, pytest | All tracks |

---

## Track 1: PydanticAI Agent Implementation

### 1.1 Chat Agent Core Implementation

#### Step 1: Create Base Agent Structure

```python
# src/infrastructure/ai/chat_agent.py
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChatDependencies:
    """Dependencies for chat agent"""
    product_service: Any  # ProductServicePort
    conversation_repository: Any  # ConversationRepository
    session_id: str
    user_metadata: Dict[str, Any]

class ChatAgent:
    """Single chat agent with tool calling using PydanticAI"""

    SYSTEM_PROMPT = """
    You are PERKY, an AI assistant for SMS Perkasa steel products, helping B2B customers in Indonesia.

    CRITICAL RULES:
    1. ALWAYS respond in Indonesian (Bahasa Indonesia) unless the user writes in English
    2. Use professional yet friendly language suitable for B2B communication
    3. You have deep knowledge of steel industry terminology:
       - Plat (plates), besi beton (rebar), hollow (hollow sections)
       - H-beam, I-beam, WF (wide flange), UNP, CNP profiles
       - Galvanis (galvanized), hot rolled, cold rolled
    4. Format prices in Indonesian Rupiah (Rp) with proper thousands separator
    5. Always confirm product specifications before quoting prices
    6. Mention minimum order quantities when relevant

    AVAILABLE TOOLS:
    - search_products: Search for products by name or category
    - check_stock: Check real-time stock availability
    - get_product_details: Get detailed product specifications
    - calculate_price: Calculate price based on quantity

    CONVERSATION FLOW:
    1. Greet professionally using customer context
    2. Understand product requirements clearly
    3. Search and present relevant options
    4. Confirm specifications and quantity
    5. Provide accurate pricing and availability
    6. Suggest related products when appropriate
    """

    def __init__(self,
                 product_service,
                 openai_api_key: str,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.7,
                 max_tokens: int = 500):
        """Initialize chat agent with dependencies"""

        # Create OpenAI model
        self.model = OpenAIModel(
            model=model,
            api_key=openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Initialize agent
        self.agent = Agent(
            model=self.model,
            system_prompt=self.SYSTEM_PROMPT,
            deps_type=ChatDependencies,
            tools=[]  # Will register tools next
        )

        self.product_service = product_service
        self._register_tools()
```

#### Step 2: Register Product Tools

```python
    def _register_tools(self):
        """Register product search and stock tools"""

        @self.agent.tool
        async def search_products(
            ctx: RunContext[ChatDependencies],
            query: str,
            category: Optional[str] = None,
            max_results: int = 5
        ) -> List[Dict[str, Any]]:
            """
            Search for steel products by name or category.
            Returns list of products with basic info.
            """
            try:
                products = await ctx.deps.product_service.search_products(
                    query=query,
                    category=category
                )

                # Format for LLM consumption
                return [
                    {
                        "product_id": p.product_id,
                        "name": p.name,
                        "description": p.description,
                        "category": p.category,
                        "base_unit": p.base_unit
                    }
                    for p in products[:max_results]
                ]
            except Exception as e:
                logger.error(f"Product search error: {e}")
                return []

        @self.agent.tool
        async def check_stock(
            ctx: RunContext[ChatDependencies],
            sku: str
        ) -> Dict[str, Any]:
            """
            Check stock availability for a specific SKU.
            Returns availability status and quantity.
            """
            try:
                variant = await ctx.deps.product_service.get_variant_by_sku(sku)
                if variant:
                    return {
                        "sku": variant.sku,
                        "name": variant.name,
                        "available": variant.stock_quantity > 0,
                        "quantity": variant.stock_quantity,
                        "unit": variant.unit,
                        "min_order": variant.min_order_quantity or 1
                    }
                return {"sku": sku, "available": False, "error": "SKU not found"}
            except Exception as e:
                logger.error(f"Stock check error: {e}")
                return {"sku": sku, "available": False, "error": str(e)}

        @self.agent.tool
        async def get_product_details(
            ctx: RunContext[ChatDependencies],
            product_id: str
        ) -> Dict[str, Any]:
            """
            Get detailed product information including all variants.
            """
            try:
                product_with_variants = await ctx.deps.product_service.get_product_with_variants(
                    product_id
                )
                if not product_with_variants:
                    return {"error": "Product not found"}

                return {
                    "product": {
                        "id": product_with_variants.product.product_id,
                        "name": product_with_variants.product.name,
                        "description": product_with_variants.product.description,
                        "category": product_with_variants.product.category,
                        "brand": product_with_variants.product.brand
                    },
                    "variants": [
                        {
                            "sku": v.sku,
                            "name": v.name,
                            "size": v.size,
                            "material": v.material,
                            "price": f"Rp {v.price:,.0f}",
                            "stock": v.stock_quantity,
                            "unit": v.unit
                        }
                        for v in product_with_variants.variants
                    ]
                }
            except Exception as e:
                logger.error(f"Product details error: {e}")
                return {"error": str(e)}

        @self.agent.tool
        async def calculate_price(
            ctx: RunContext[ChatDependencies],
            sku: str,
            quantity: int
        ) -> Dict[str, Any]:
            """
            Calculate total price for given quantity.
            Includes volume discounts if applicable.
            """
            try:
                variant = await ctx.deps.product_service.get_variant_by_sku(sku)
                if not variant:
                    return {"error": "SKU not found"}

                # Basic price calculation (can add discount logic)
                base_price = variant.price * quantity

                # Volume discount tiers (example)
                discount = 0
                if quantity >= 100:
                    discount = 0.05  # 5% discount
                elif quantity >= 50:
                    discount = 0.03  # 3% discount
                elif quantity >= 20:
                    discount = 0.02  # 2% discount

                final_price = base_price * (1 - discount)

                return {
                    "sku": sku,
                    "product_name": variant.name,
                    "quantity": quantity,
                    "unit_price": f"Rp {variant.price:,.0f}",
                    "base_total": f"Rp {base_price:,.0f}",
                    "discount_percentage": f"{discount*100:.0f}%",
                    "discount_amount": f"Rp {base_price * discount:,.0f}",
                    "final_price": f"Rp {final_price:,.0f}",
                    "unit": variant.unit
                }
            except Exception as e:
                logger.error(f"Price calculation error: {e}")
                return {"error": str(e)}
```

#### Step 3: Implement Run Method

```python
    async def run(self,
                  message: str,
                  conversation_context: Dict[str, Any],
                  session_id: str) -> str:
        """
        Process message and return response.

        Args:
            message: User's input message
            conversation_context: Previous conversation history
            session_id: Current session identifier

        Returns:
            AI-generated response in Indonesian
        """
        try:
            # Prepare dependencies
            deps = ChatDependencies(
                product_service=self.product_service,
                conversation_repository=None,  # Optional for MVP
                session_id=session_id,
                user_metadata=conversation_context.get("metadata", {})
            )

            # Format conversation history for context
            history = conversation_context.get("conversation_history", [])
            context_prompt = ""
            if history:
                context_prompt = "\nPrevious conversation:\n"
                for msg in history[-4:]:  # Last 2 exchanges
                    role = "Customer" if msg["sender"] == "user" else "PERKY"
                    context_prompt += f"{role}: {msg['content']}\n"
                context_prompt += "\nContinue the conversation naturally.\n"

            # Run agent with context
            result = await self.agent.run(
                prompt=context_prompt + f"\nCustomer: {message}",
                deps=deps
            )

            # Extract text response
            return result.data if hasattr(result, 'data') else str(result)

        except Exception as e:
            logger.error(f"Chat agent error: {e}")
            return "Mohon maaf, terjadi kesalahan sistem. Silakan coba lagi atau hubungi customer service kami."
```

### 1.2 Indonesian Language Optimization

```python
# src/infrastructure/ai/prompts/indonesian_templates.py

GREETING_TEMPLATES = {
    "morning": "Selamat pagi! Saya PERKY, asisten digital SMS Perkasa. Ada yang bisa saya bantu hari ini?",
    "afternoon": "Selamat siang! Terima kasih telah menghubungi SMS Perkasa. Produk baja apa yang Anda cari?",
    "evening": "Selamat sore! Saya PERKY, siap membantu kebutuhan produk baja Anda.",
    "default": "Selamat datang di SMS Perkasa! Saya PERKY, asisten produk baja Anda."
}

PRODUCT_INQUIRY_TEMPLATES = {
    "availability": "Baik, saya akan cek ketersediaan varian {variant_name} untuk Anda.",
    "specifications": "Berikut spesifikasi lengkap untuk {variant_name}:",
    "pricing": "Untuk {variant_name}, harga per {stock_unit}: {display_price}",
    "pricing_inquiry": "Produk {product_name} memiliki beberapa varian. Varian mana yang Anda butuhkan?",
    "variant_options": "Produk {product_name} tersedia dalam {variant_count} varian:",
    "variant_list": "- {variant_name}: {display_price} per {stock_unit} (Stok: {stock_quantity})",
    "recommendation": "Berdasarkan kebutuhan Anda, saya merekomendasikan produk berikut:"
}

STOCK_MESSAGES = {
    "in_stock": "✅ {variant_name} tersedia: {stock_quantity} {stock_unit}",
    "low_stock": "⚠️ Stok {variant_name} terbatas: tersisa {stock_quantity} {stock_unit}",
    "out_of_stock": "❌ Mohon maaf, stok {variant_name} sedang kosong",
    "product_stock_summary": "Stok {product_name}: {available_variants} dari {total_variants} varian tersedia",
    "all_variants_available": "✅ Semua varian {product_name} tersedia",
    "some_variants_available": "⚠️ Beberapa varian {product_name} tersedia",
    "no_variants_available": "❌ Semua varian {product_name} sedang kosong"
}

PRICE_TEMPLATES = {
    "unit_price": "{display_price} per {stock_unit}",
    "total_price": "Total untuk {quantity} {stock_unit}: {total_price}",
    "price_range": "Harga {product_name}: {min_price} - {max_price} (tergantung varian)",
    "volume_discount": "Diskon {discount_percentage}% untuk pembelian di atas {min_quantity} {stock_unit}",
    "final_price_with_discount": "Harga setelah diskon: {final_price} (hemat {discount_amount})"
}

ERROR_MESSAGES = {
    "product_not_found": "Maaf, produk {product_name} tidak ditemukan dalam katalog kami.",
    "variant_not_found": "Maaf, varian {variant_spec} tidak tersedia untuk produk {product_name}.",
    "variant_out_of_stock": "Mohon maaf, stok {variant_name} sedang kosong. Estimasi tersedia {date}.",
    "insufficient_stock": "Stok {variant_name} tidak mencukupi. Tersedia: {available} {stock_unit}",
    "system_error": "Mohon maaf, terjadi kesalahan sistem. Tim kami akan segera memperbaikinya.",
    "clarification": "Mohon maaf, saya perlu informasi lebih detail. Bisa tolong jelaskan spesifikasi yang Anda butuhkan?",
    "variant_selection_needed": "Produk {product_name} memiliki beberapa varian. Mohon pilih spesifikasi yang Anda inginkan:",
    "specification_needed": "Untuk memberikan harga yang tepat, saya perlu tahu spesifikasi: {required_specs}"
}

VARIANT_SELECTION_TEMPLATES = {
    "thickness_selection": "Pilih ketebalan yang dibutuhkan: {available_thicknesses}",
    "size_selection": "Pilih ukuran yang dibutuhkan: {available_sizes}",
    "material_selection": "Pilih grade material: {available_materials}",
    "confirm_variant": "Apakah Anda memilih {variant_name}? (SKU: {sku})",
    "variant_details": """
{variant_name}
- SKU: {sku}
- Harga: {display_price}/{stock_unit}
- Stok: {stock_quantity} {stock_unit}
- Spesifikasi: {specifications}
"""
}

UNIT_TEMPLATES = {
    "lembar": "lembar (sheet)",
    "batang": "batang (bar/rod)",
    "kg": "kilogram",
    "meter": "meter",
    "roll": "roll",
    "unit": "unit",
    "pcs": "pcs (pieces)",
    "quantity_format": "{quantity} {stock_unit}",
    "minimum_order": "Minimum order: {min_quantity} {stock_unit}"
}

CLOSING_TEMPLATES = {
    "order_ready": "Terima kasih! Pesanan Anda siap diproses. Tim sales kami akan menghubungi Anda segera.",
    "need_help": "Ada yang bisa saya bantu lagi?",
    "thank_you": "Terima kasih telah menghubungi SMS Perkasa. Semoga hari Anda menyenangkan!"
}
```

### 1.3 Simple Template Integration for MVP

#### Modifications to Existing ChatAgent

```python
# src/infrastructure/ai/chat_agent.py - Simple template integration

# 1. Add imports at the top (after existing imports)
from src.infrastructure.ai.prompts.indonesian_templates import (
    GREETING_TEMPLATES, STOCK_MESSAGES, PRICE_TEMPLATES, ERROR_MESSAGES
)
from datetime import datetime

class ChatAgent(AIAgentPort):
    """PydanticAI-based chat agent for Indonesian steel products."""

    # 2. Add simple helper methods for templates
    def _get_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        hour = datetime.now().hour

        if 5 <= hour < 11:
            return GREETING_TEMPLATES["morning"]
        elif 11 <= hour < 15:
            return GREETING_TEMPLATES["afternoon"]
        elif 15 <= hour < 19:
            return GREETING_TEMPLATES["evening"]
        else:
            return GREETING_TEMPLATES["default"]

    def _format_stock_message(self, variant: Any) -> str:
        """Format stock information using templates"""
        if not variant.has_stock():
            return STOCK_MESSAGES["out_of_stock"].format(
                variant_name=variant.variant_name
            )
        elif variant.stock_quantity <= 10:
            return STOCK_MESSAGES["low_stock"].format(
                variant_name=variant.variant_name,
                stock_quantity=variant.stock_quantity,
                stock_unit=variant.stock_unit
            )
        else:
            return STOCK_MESSAGES["in_stock"].format(
                variant_name=variant.variant_name,
                stock_quantity=variant.stock_quantity,
                stock_unit=variant.stock_unit
            )

    def _format_price_message(self, variant: Any) -> str:
        """Format price information using templates"""
        return PRICE_TEMPLATES["unit_price"].format(
            display_price=variant.get_display_price(),
            stock_unit=variant.stock_unit
        )

    # 3. Modify existing generate_response method - Add greeting detection
    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None,
        product_service: Optional[ProductServicePort] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate a response using the PydanticAI agent."""
        try:
            # Simple greeting detection for first message
            if not conversation_context or len(conversation_context) == 0:
                greeting_keywords = ['halo', 'hai', 'pagi', 'siang', 'sore']
                if any(word in message.lower() for word in greeting_keywords):
                    return self._get_greeting()

            # Rest of existing implementation...
            messages = []
            if conversation_context:
                for msg in conversation_context[-10:]:
                    if msg.sender_type == "user":
                        messages.append(("user", msg.content))
                    else:
                        messages.append(("assistant", msg.content))

            messages.append(("user", message))

            deps = ChatDependencies(
                product_service=product_service or self._create_mock_product_service(),
                session_id=session_id or "default",
                user_metadata={},
            )

            result = await self.agent.run(
                message,
                message_history=messages[:-1],
                deps=deps,
            )

            response = result.data if hasattr(result, "data") else str(result)
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Use template for error message
            return ERROR_MESSAGES["system_error"]

    # 4. Enhanced tool methods - Add template formatting to tool responses
    async def _get_variant_details_tool(
        self, ctx: RunContext[ChatDependencies], product_id: str, variant_id: str
    ) -> VariantDetails:
        """Get detailed information about a specific variant."""
        try:
            product_with_variants = (
                await ctx.deps.product_service.get_product_with_variants(product_id)
            )

            if product_with_variants:
                variant = product_with_variants.get_variant_by_id(variant_id)
                if variant:
                    # Create base response
                    details = VariantDetails(
                        variant_id=variant.variant_id,
                        sku=variant.sku,
                        name=variant.variant_name,
                        price=float(variant.price),
                        display_price=variant.get_display_price(),
                        stock_quantity=variant.stock_quantity,
                        stock_unit=variant.stock_unit,
                        specifications=variant.specifications,
                        available=variant.has_stock(),
                    )

                    # Add formatted messages to specifications for LLM to use
                    details.specifications["_formatted_stock"] = self._format_stock_message(variant)
                    details.specifications["_formatted_price"] = self._format_price_message(variant)

                    return details

            # Return empty variant if not found with error message
            return VariantDetails(
                variant_id=variant_id,
                sku="NOT_FOUND",
                name=ERROR_MESSAGES["variant_not_found"].format(
                    variant_spec=variant_id,
                    product_name="Unknown"
                ),
                price=0.0,
                display_price="Rp 0",
                stock_quantity=0,
                stock_unit="unit",
                available=False,
            )
        except Exception as e:
            logger.error(f"Error getting variant details: {e}")
            return VariantDetails(
                variant_id=variant_id,
                sku="ERROR",
                name=ERROR_MESSAGES["system_error"],
                price=0.0,
                display_price="Rp 0",
                stock_quantity=0,
                stock_unit="unit",
                available=False,
            )
```

#### Update System Prompt to Use Templates

```python
# Modify the SYSTEM_PROMPT to instruct LLM to use template fragments

SYSTEM_PROMPT = """Kamu adalah PERKY, asisten virtual untuk SMS Perkasa yang membantu
pelanggan B2B menemukan produk baja yang tepat.

[... existing prompt content ...]

PANDUAN TEMPLATE:
1. Gunakan pesan terformat yang disediakan dalam specifications["_formatted_stock"] dan
   specifications["_formatted_price"] untuk informasi stok dan harga
2. Untuk error, gunakan pesan yang sudah terformat dalam field 'name' jika SKU adalah 'ERROR' atau 'NOT_FOUND'
3. Tetap gunakan bahasa yang natural dan kontekstual, tapi pastikan data faktual
   (harga, stok, SKU) disampaikan persis seperti yang terformat
4. Jangan ubah angka atau format harga/stok yang sudah disediakan

[... rest of existing prompt ...]
"""
```

#### Simple Integration Test

```python
# tests/unit/infrastructure/test_chat_agent_templates.py

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.infrastructure.ai.chat_agent import ChatAgent

@pytest.mark.asyncio
async def test_greeting_response():
    """Test that greetings use templates"""
    agent = ChatAgent.create_with_fallback()

    # Mock time for consistent testing
    with patch('src.infrastructure.ai.chat_agent.datetime') as mock_datetime:
        mock_datetime.now.return_value.hour = 9  # Morning

        response = await agent.generate_response(
            message="Halo",
            conversation_context=None  # First message
        )

        assert "Selamat pagi" in response
        assert "PERKY" in response

@pytest.mark.asyncio
async def test_error_uses_template():
    """Test that errors use templates"""
    agent = ChatAgent.create_with_fallback()

    # Force an error
    with patch.object(agent, 'agent') as mock_agent:
        mock_agent.run.side_effect = Exception("Test error")

        response = await agent.generate_response("test message")

        assert response == ERROR_MESSAGES["system_error"]

@pytest.mark.asyncio
async def test_stock_formatting():
    """Test stock message formatting"""
    agent = ChatAgent()

    # Mock variant with low stock
    variant = Mock()
    variant.variant_name = "Plat Baja 5mm"
    variant.stock_quantity = 5
    variant.stock_unit = "lembar"
    variant.has_stock.return_value = True

    formatted = agent._format_stock_message(variant)

    assert "terbatas" in formatted
    assert "5 lembar" in formatted
```

---

## Track 2: Mock Services & Repositories

### 2.1 Mock Product Service Implementation

```python
# src/infrastructure/services/mock_product_service.py
from typing import List, Optional, Dict, Any
from src.domain.value_objects import ProductInfo, VariantInfo, ProductWithVariantsInfo
import asyncio
import random

class MockProductService:
    """Mock product service with realistic steel industry data"""

    def __init__(self):
        self.products = self._create_comprehensive_catalog()
        self._init_search_index()

    def _create_comprehensive_catalog(self) -> Dict[str, ProductWithVariantsInfo]:
        """Create realistic steel product catalog"""

        catalog = {}

        # 1. Plat Baja (Steel Plates)
        plat_product = ProductInfo(
            product_id="PLAT-001",
            name="Plat Baja SS400",
            description="Plat baja kualitas JIS SS400 untuk konstruksi umum",
            category="plat",
            brand="SMS Perkasa",
            base_unit="lembar"
        )

        plat_variants = [
            VariantInfo(
                sku="PLAT-SS400-3MM-4X8",
                product_id="PLAT-001",
                name="Plat SS400 3mm 4x8",
                size="3mm x 1220mm x 2440mm",
                material="SS400",
                price=650000,
                stock_quantity=200,
                unit="lembar",
                weight=72.0,
                min_order_quantity=5
            ),
            VariantInfo(
                sku="PLAT-SS400-5MM-4X8",
                product_id="PLAT-001",
                name="Plat SS400 5mm 4x8",
                size="5mm x 1220mm x 2440mm",
                material="SS400",
                price=1080000,
                stock_quantity=150,
                unit="lembar",
                weight=120.0,
                min_order_quantity=3
            ),
            VariantInfo(
                sku="PLAT-SS400-6MM-4X8",
                product_id="PLAT-001",
                name="Plat SS400 6mm 4x8",
                size="6mm x 1220mm x 2440mm",
                material="SS400",
                price=1295000,
                stock_quantity=100,
                unit="lembar",
                weight=144.0,
                min_order_quantity=3
            ),
            VariantInfo(
                sku="PLAT-SS400-8MM-4X8",
                product_id="PLAT-001",
                name="Plat SS400 8mm 4x8",
                size="8mm x 1220mm x 2440mm",
                material="SS400",
                price=1730000,
                stock_quantity=75,
                unit="lembar",
                weight=192.0,
                min_order_quantity=2
            ),
            VariantInfo(
                sku="PLAT-SS400-10MM-4X8",
                product_id="PLAT-001",
                name="Plat SS400 10mm 4x8",
                size="10mm x 1220mm x 2440mm",
                material="SS400",
                price=2160000,
                stock_quantity=50,
                unit="lembar",
                weight=240.0,
                min_order_quantity=2
            )
        ]

        catalog["PLAT-001"] = ProductWithVariantsInfo(
            product=plat_product,
            variants=plat_variants
        )

        # 2. Besi Beton (Rebar)
        besi_beton_product = ProductInfo(
            product_id="BESI-001",
            name="Besi Beton SNI Ulir",
            description="Besi beton ulir standar SNI untuk konstruksi beton bertulang",
            category="besi_beton",
            brand="SMS Perkasa",
            base_unit="batang"
        )

        besi_beton_variants = [
            VariantInfo(
                sku="BESI-D10-SNI",
                product_id="BESI-001",
                name="Besi Beton Ulir D10 SNI",
                size="10mm x 12m",
                material="BJTS 420B",
                price=95000,
                stock_quantity=500,
                unit="batang",
                weight=7.4,
                min_order_quantity=10
            ),
            VariantInfo(
                sku="BESI-D12-SNI",
                product_id="BESI-001",
                name="Besi Beton Ulir D12 SNI",
                size="12mm x 12m",
                material="BJTS 420B",
                price=135000,
                stock_quantity=400,
                unit="batang",
                weight=10.7,
                min_order_quantity=10
            ),
            VariantInfo(
                sku="BESI-D16-SNI",
                product_id="BESI-001",
                name="Besi Beton Ulir D16 SNI",
                size="16mm x 12m",
                material="BJTS 420B",
                price=240000,
                stock_quantity=300,
                unit="batang",
                weight=19.0,
                min_order_quantity=5
            )
        ]

        catalog["BESI-001"] = ProductWithVariantsInfo(
            product=besi_beton_product,
            variants=besi_beton_variants
        )

        # 3. H-Beam
        hbeam_product = ProductInfo(
            product_id="HBEAM-001",
            name="H-Beam SS400",
            description="Baja profil H untuk struktur bangunan dan jembatan",
            category="h_beam",
            brand="SMS Perkasa",
            base_unit="batang"
        )

        hbeam_variants = [
            VariantInfo(
                sku="HBEAM-150X150",
                product_id="HBEAM-001",
                name="H-Beam 150x150x7x10",
                size="150x150x7x10mm x 12m",
                material="SS400",
                price=3250000,
                stock_quantity=40,
                unit="batang",
                weight=378.0,
                min_order_quantity=1
            ),
            VariantInfo(
                sku="HBEAM-200X200",
                product_id="HBEAM-001",
                name="H-Beam 200x200x8x12",
                size="200x200x8x12mm x 12m",
                material="SS400",
                price=5800000,
                stock_quantity=30,
                unit="batang",
                weight=598.8,
                min_order_quantity=1
            )
        ]

        catalog["HBEAM-001"] = ProductWithVariantsInfo(
            product=hbeam_product,
            variants=hbeam_variants
        )

        # 4. Besi Hollow (Hollow Section)
        hollow_product = ProductInfo(
            product_id="HOLLOW-001",
            name="Besi Hollow Galvanis",
            description="Besi hollow dengan lapisan galvanis anti karat",
            category="hollow",
            brand="SMS Perkasa",
            base_unit="batang"
        )

        hollow_variants = [
            VariantInfo(
                sku="HOLLOW-4040-GLV",
                product_id="HOLLOW-001",
                name="Hollow Galvanis 40x40x2.0",
                size="40x40x2.0mm x 6m",
                material="Galvanis",
                price=185000,
                stock_quantity=200,
                unit="batang",
                weight=14.4,
                min_order_quantity=5
            ),
            VariantInfo(
                sku="HOLLOW-5050-GLV",
                product_id="HOLLOW-001",
                name="Hollow Galvanis 50x50x2.3",
                size="50x50x2.3mm x 6m",
                material="Galvanis",
                price=265000,
                stock_quantity=150,
                unit="batang",
                weight=20.7,
                min_order_quantity=5
            )
        ]

        catalog["HOLLOW-001"] = ProductWithVariantsInfo(
            product=hollow_product,
            variants=hollow_variants
        )

        return catalog

    def _init_search_index(self):
        """Initialize search index for fast lookup"""
        self.search_index = {}

        for product_id, product_with_variants in self.products.items():
            product = product_with_variants.product

            # Index by product name words
            for word in product.name.lower().split():
                if word not in self.search_index:
                    self.search_index[word] = []
                if product_id not in self.search_index[word]:
                    self.search_index[word].append(product_id)

            # Index by category
            category_key = f"cat_{product.category}"
            if category_key not in self.search_index:
                self.search_index[category_key] = []
            self.search_index[category_key].append(product_id)

    async def search_products(self,
                             query: str,
                             category: Optional[str] = None) -> List[ProductInfo]:
        """Search products with simulated network delay"""
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.3))

        results = set()

        # Search by category if specified
        if category:
            category_key = f"cat_{category.lower()}"
            if category_key in self.search_index:
                for product_id in self.search_index[category_key]:
                    results.add(product_id)

        # Search by query words
        query_lower = query.lower()
        for word in query_lower.split():
            if word in self.search_index:
                for product_id in self.search_index[word]:
                    results.add(product_id)

        # Return product info objects
        return [
            self.products[pid].product
            for pid in results
        ]

    async def get_product_with_variants(self,
                                       product_id: str) -> Optional[ProductWithVariantsInfo]:
        """Get product with all variants"""
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.2))
        return self.products.get(product_id)

    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Get specific variant by SKU"""
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.05, 0.15))

        for product_with_variants in self.products.values():
            for variant in product_with_variants.variants:
                if variant.sku == sku:
                    return variant
        return None
```

### 2.2 In-Memory Conversation Repository

```python
# src/infrastructure/repositories/in_memory_conversation_repository.py
from typing import Optional, Dict, List
from datetime import datetime, timezone
from src.domain.entities import Conversation, Message
import asyncio
from asyncio import Lock

class InMemoryConversationRepository:
    """Thread-safe in-memory conversation storage"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.lock = Lock()
        self.message_count = 0
        self.max_conversations = 1000  # Limit for MVP
        self.max_messages_per_conversation = 500

    async def save(self, conversation: Conversation) -> None:
        """Save conversation with thread safety"""
        async with self.lock:
            # Check limits
            if len(self.conversations) >= self.max_conversations:
                # Remove oldest conversation
                oldest_id = min(
                    self.conversations.keys(),
                    key=lambda k: self.conversations[k].created_at
                )
                del self.conversations[oldest_id]

            # Limit messages per conversation
            if len(conversation.messages) > self.max_messages_per_conversation:
                # Keep only recent messages
                conversation.messages = conversation.messages[-self.max_messages_per_conversation:]

            self.conversations[conversation.session_id] = conversation
            self.message_count = sum(
                len(c.messages) for c in self.conversations.values()
            )

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID"""
        async with self.lock:
            return self.conversations.get(session_id)

    async def delete(self, session_id: str) -> None:
        """Delete conversation"""
        async with self.lock:
            if session_id in self.conversations:
                del self.conversations[session_id]

    async def get_recent_messages(self,
                                 session_id: str,
                                 limit: int = 10) -> List[Message]:
        """Get recent messages for context"""
        conversation = await self.get_by_session(session_id)
        if conversation:
            return conversation.messages[-limit:] if conversation.messages else []
        return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        async with self.lock:
            return {
                "total_conversations": len(self.conversations),
                "total_messages": self.message_count,
                "memory_usage_estimate": self.message_count * 500  # Rough bytes estimate
            }
```

---

## Track 3: Dependency Injection System

### 3.1 Dependency Container Implementation

```python
# src/infrastructure/dependencies/container.py
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServiceRegistration:
    """Service registration metadata"""
    factory: Callable
    singleton: bool
    dependencies: List[str]
    instance: Optional[Any] = None

class DIContainer:
    """Enhanced dependency injection container with lifecycle management"""

    def __init__(self):
        self._services: Dict[str, ServiceRegistration] = {}
        self._resolving: set = set()  # Circular dependency detection

    def register(self,
                name: str,
                factory: Callable,
                singleton: bool = False,
                dependencies: List[str] = None):
        """Register a service with its factory"""
        self._services[name] = ServiceRegistration(
            factory=factory,
            singleton=singleton,
            dependencies=dependencies or [],
            instance=None
        )
        logger.info(f"Registered service: {name} (singleton={singleton})")

    def register_instance(self, name: str, instance: Any):
        """Register an existing instance"""
        self._services[name] = ServiceRegistration(
            factory=lambda: instance,
            singleton=True,
            dependencies=[],
            instance=instance
        )

    async def resolve(self, name: str) -> Any:
        """Resolve a service with its dependencies"""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")

        # Circular dependency detection
        if name in self._resolving:
            raise ValueError(f"Circular dependency detected: {name}")

        registration = self._services[name]

        # Return existing singleton instance
        if registration.singleton and registration.instance:
            return registration.instance

        try:
            self._resolving.add(name)

            # Resolve dependencies first
            deps = {}
            for dep_name in registration.dependencies:
                deps[dep_name] = await self.resolve(dep_name)

            # Create instance
            if deps:
                instance = await registration.factory(**deps)
            else:
                instance = await registration.factory()

            # Store singleton instance
            if registration.singleton:
                registration.instance = instance

            return instance

        finally:
            self._resolving.remove(name)

    def clear_singletons(self):
        """Clear all singleton instances"""
        for registration in self._services.values():
            registration.instance = None
```

### 3.2 Service Configuration

```python
# src/infrastructure/dependencies/service_config.py
from src.core.config import settings
from src.infrastructure.dependencies.container import DIContainer
from src.infrastructure.ai.chat_agent import ChatAgent
from src.infrastructure.services.mock_product_service import MockProductService
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository
)
from src.application.use_cases import (
    StartChatSessionUseCaseImpl,
    ProcessUserMessageUseCaseImpl,
    GetConversationUseCaseImpl
)
from src.application.services.chat_orchestrator import ChatOrchestrator

async def configure_services(container: DIContainer):
    """Configure all services for DI container"""

    # Infrastructure services
    container.register(
        "product_service",
        MockProductService,
        singleton=True
    )

    container.register(
        "conversation_repository",
        InMemoryConversationRepository,
        singleton=True
    )

    # Chat Agent with dependencies
    async def create_chat_agent(product_service):
        return ChatAgent(
            product_service=product_service,
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS
        )

    container.register(
        "chat_agent",
        create_chat_agent,
        singleton=True,
        dependencies=["product_service"]
    )

    # Use cases
    async def create_process_message_use_case(chat_agent, product_service, conversation_repository):
        return ProcessUserMessageUseCaseImpl(
            chat_agent=chat_agent,
            product_service=product_service,
            conversation_repository=conversation_repository
        )

    container.register(
        "process_message_use_case",
        create_process_message_use_case,
        singleton=False,
        dependencies=["chat_agent", "product_service", "conversation_repository"]
    )

    # Chat Orchestrator
    async def create_chat_orchestrator(
        start_session_use_case,
        process_message_use_case,
        get_conversation_use_case
    ):
        return ChatOrchestrator(
            start_session_use_case=start_session_use_case,
            process_message_use_case=process_message_use_case,
            get_conversation_use_case=get_conversation_use_case
        )

    container.register(
        "chat_orchestrator",
        create_chat_orchestrator,
        singleton=True,
        dependencies=[
            "start_session_use_case",
            "process_message_use_case",
            "get_conversation_use_case"
        ]
    )

# Global container instance
container = DIContainer()
```

---

## Track 4: Main Application Integration

### 4.1 FastAPI Application Setup

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from src.presentation.api import health
from src.presentation.api.v1 import websocket
from src.core.config import settings
from src.infrastructure.dependencies import container, configure_services
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Steel Chat MVP application...")
    await configure_services(container)
    logger.info("Services configured successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    container.clear_singletons()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # CORS configuration for MVP
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for MVP, restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(
        websocket.router,
        prefix=settings.API_V1_STR,
        tags=["websocket"]
    )

    # Serve test client HTML
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve test client interface"""
        try:
            with open("static/test_client.html", "r") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(
                content="<h1>Steel Chat MVP</h1><p>WebSocket endpoint: /api/v1/ws/{session_id}</p>"
            )

    # API documentation redirect
    @app.get("/api")
    async def api_redirect():
        """Redirect to API documentation"""
        return {"message": "API Documentation", "url": "/docs"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### 4.2 WebSocket Endpoint Enhancement

```python
# src/presentation/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from typing import Optional
import json
import asyncio
import logging
from datetime import datetime
from src.presentation.websocket.connection_manager import ConnectionManager
from src.infrastructure.dependencies import container

router = APIRouter()
logger = logging.getLogger(__name__)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint with full chat functionality"""

    await manager.connect(websocket, session_id)

    try:
        # Get orchestrator from DI container
        chat_orchestrator = await container.resolve("chat_orchestrator")

        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "event": "connected",
            "message": "Selamat datang di SMS Perkasa Steel Chat!",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            send_heartbeat(websocket, session_id)
        )

        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get("type") == "user_message":
                    # Send typing indicator
                    await websocket.send_json({
                        "type": "system",
                        "event": "typing",
                        "message": "PERKY sedang mengetik..."
                    })

                    # Process message
                    response = await chat_orchestrator.handle_user_message(
                        session_id=session_id,
                        content=message_data.get("message", ""),
                        metadata=message_data.get("metadata", {})
                    )

                    # Send AI response
                    await websocket.send_json({
                        "type": "ai_response",
                        "message": response.content,
                        "metadata": response.metadata,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})

                elif message_data.get("type") == "get_history":
                    # Send conversation history
                    history = await chat_orchestrator.get_conversation_history(
                        session_id
                    )
                    await websocket.send_json({
                        "type": "history",
                        "messages": history.messages if history else []
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Terjadi kesalahan. Silakan coba lagi."
                })

    except WebSocketDisconnect:
        logger.info(f"Client {session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        heartbeat_task.cancel()
        manager.disconnect(session_id)

async def send_heartbeat(websocket: WebSocket, session_id: str):
    """Send periodic heartbeat to keep connection alive"""
    while True:
        try:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            break
```

---

## Track 5: Testing Infrastructure

### 5.1 Unit Tests for Chat Agent

```python
# tests/unit/infrastructure/test_chat_agent.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.infrastructure.ai.chat_agent import ChatAgent, ChatDependencies

@pytest.fixture
def mock_product_service():
    """Create mock product service"""
    service = AsyncMock()
    service.search_products.return_value = [
        Mock(
            product_id="PLAT-001",
            name="Plat Baja SS400",
            description="Test product",
            category="plat",
            base_unit="lembar"
        )
    ]
    service.get_variant_by_sku.return_value = Mock(
        sku="PLAT-SS400-5MM",
        name="Plat 5mm",
        stock_quantity=100,
        unit="lembar",
        price=1080000,
        min_order_quantity=3
    )
    return service

@pytest.fixture
def chat_agent(mock_product_service):
    """Create chat agent with mocked dependencies"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        agent = ChatAgent(
            product_service=mock_product_service,
            openai_api_key="test-key",
            model="gpt-4o-mini"
        )
        # Mock the PydanticAI agent run method
        agent.agent.run = AsyncMock(
            return_value=Mock(
                data="Baik, saya akan cek ketersediaan plat baja untuk Anda."
            )
        )
        return agent

@pytest.mark.asyncio
async def test_chat_agent_initialization(chat_agent):
    """Test chat agent initializes correctly"""
    assert chat_agent is not None
    assert chat_agent.product_service is not None
    assert chat_agent.SYSTEM_PROMPT is not None
    assert "PERKY" in chat_agent.SYSTEM_PROMPT

@pytest.mark.asyncio
async def test_chat_agent_run(chat_agent):
    """Test chat agent processes messages"""
    response = await chat_agent.run(
        message="Ada plat baja 5mm?",
        conversation_context={},
        session_id="test-session"
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_chat_agent_tools_registered(chat_agent):
    """Test that tools are properly registered"""
    # Check agent has tools registered
    # This would require accessing internal PydanticAI agent structure
    # For MVP, we verify tools exist through method presence
    assert hasattr(chat_agent, '_register_tools')

@pytest.mark.asyncio
async def test_chat_agent_error_handling(chat_agent):
    """Test chat agent handles errors gracefully"""
    # Make agent.run raise an exception
    chat_agent.agent.run.side_effect = Exception("API Error")

    response = await chat_agent.run(
        message="Test message",
        conversation_context={},
        session_id="test-session"
    )

    assert "Mohon maaf" in response
    assert "kesalahan" in response
```

### 5.2 Integration Tests

```python
# tests/integration/test_websocket_flow.py
import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.dependencies import container, configure_services

@pytest.fixture
async def configured_container():
    """Configure DI container for tests"""
    await configure_services(container)
    yield container
    container.clear_singletons()

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

def test_websocket_connection(client):
    """Test WebSocket connection establishment"""
    with client.websocket_connect("/api/v1/ws/test-session-123") as websocket:
        # Receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert data["event"] == "connected"
        assert "Selamat datang" in data["message"]

def test_websocket_message_flow(client):
    """Test complete message exchange"""
    with client.websocket_connect("/api/v1/ws/test-session-456") as websocket:
        # Skip welcome message
        websocket.receive_json()

        # Send user message
        websocket.send_json({
            "type": "user_message",
            "message": "Halo, ada plat baja?"
        })

        # Receive typing indicator
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert data["event"] == "typing"

        # Receive AI response
        data = websocket.receive_json()
        assert data["type"] == "ai_response"
        assert data["message"] is not None

def test_websocket_ping_pong(client):
    """Test heartbeat mechanism"""
    with client.websocket_connect("/api/v1/ws/test-session-789") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send ping
        websocket.send_json({"type": "ping"})

        # Receive pong
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_error_handling(client):
    """Test error handling for invalid messages"""
    with client.websocket_connect("/api/v1/ws/test-error") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send invalid JSON
        websocket.send_text("invalid json {]")

        # Receive error message
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid" in data["message"]
```

### 5.3 End-to-End Test Script

```bash
#!/bin/bash
# tests/e2e/test_mvp_flow.sh

echo "==================================="
echo "Steel Chat MVP E2E Test Suite"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local command=$2
    local expected=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}Running: $test_name${NC}"

    result=$(eval $command 2>&1)

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Expected: $expected"
        echo "Got: $result"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# Start application in background
echo "Starting application..."
python -m uvicorn src.main:app --port 8000 > /tmp/app.log 2>&1 &
APP_PID=$!
sleep 5

# Test 1: Health check
run_test "Health Check" \
    "curl -s http://localhost:8000/health" \
    "healthy"

# Test 2: API Documentation
run_test "API Documentation Available" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs" \
    "200"

# Test 3: WebSocket Connection
run_test "WebSocket Connection" \
    "echo '{\"type\":\"ping\"}' | websocat -t ws://localhost:8000/api/v1/ws/test-e2e-123 2>&1 | head -1" \
    "connected"

# Test 4: Product Search (using curl to test HTTP if available)
# For WebSocket testing, we'd use websocat or wscat

# Python test script for WebSocket
cat > /tmp/test_ws.py << 'EOF'
import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8000/api/v1/ws/test-python"
    async with websockets.connect(uri) as websocket:
        # Receive welcome
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)
        assert welcome_data["type"] == "system"

        # Send message
        await websocket.send(json.dumps({
            "type": "user_message",
            "message": "Ada plat baja 5mm?"
        }))

        # Receive typing
        typing = await websocket.recv()
        typing_data = json.loads(typing)

        # Receive response
        response = await websocket.recv()
        response_data = json.loads(response)
        assert response_data["type"] == "ai_response"

        print("WebSocket test passed!")
        return True

try:
    asyncio.run(test_chat())
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
EOF

run_test "WebSocket Chat Flow" \
    "python /tmp/test_ws.py" \
    "SUCCESS"

# Test 5: Multiple concurrent connections
echo "Testing concurrent connections..."
for i in {1..5}; do
    (echo '{"type":"ping"}' | websocat -t ws://localhost:8000/api/v1/ws/concurrent-$i 2>&1 > /tmp/concurrent-$i.log) &
done
wait
sleep 2

CONCURRENT_SUCCESS=0
for i in {1..5}; do
    if grep -q "pong" /tmp/concurrent-$i.log 2>/dev/null; then
        CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS + 1))
    fi
done

if [ $CONCURRENT_SUCCESS -eq 5 ]; then
    echo -e "${GREEN}✓ Concurrent connections test PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Concurrent connections test FAILED ($CONCURRENT_SUCCESS/5 succeeded)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Cleanup
echo ""
echo "Cleaning up..."
kill $APP_PID 2>/dev/null
rm /tmp/test_ws.py 2>/dev/null
rm /tmp/concurrent-*.log 2>/dev/null
rm /tmp/app.log 2>/dev/null

# Summary
echo ""
echo "==================================="
echo "Test Summary"
echo "==================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed! MVP is ready.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review.${NC}"
    exit 1
fi
```

---

## Integration & Convergence Points

### Convergence Point 1: Service Integration (Hour 3)

```python
# integration_test.py
"""
Integration point where all services come together
Run this after Track 1-3 complete
"""

async def test_service_integration():
    """Verify all services work together"""

    # Initialize container
    container = DIContainer()
    await configure_services(container)

    # Get services
    chat_agent = await container.resolve("chat_agent")
    product_service = await container.resolve("product_service")

    # Test chat agent with product service
    deps = ChatDependencies(
        product_service=product_service,
        conversation_repository=None,
        session_id="integration-test",
        user_metadata={}
    )

    # Test product search through agent
    result = await chat_agent.agent.run(
        "Cari plat baja 5mm",
        deps=deps
    )

    assert result is not None
    print("✓ Service integration successful")
```

### Convergence Point 2: Full System Integration (Hour 5)

```python
# full_integration_test.py
"""
Full system integration test
Run after all tracks complete
"""

async def test_full_integration():
    """Test complete flow from WebSocket to AI response"""

    # Start application
    app = create_app()

    # Create test client
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test health
        response = await client.get("/health")
        assert response.status_code == 200

        # Test WebSocket flow (requires WebSocket test client)
        # ... WebSocket testing code ...

    print("✓ Full integration successful")
```

---

## Quality Gates & Validation

### Gate 1: Unit Test Coverage

```bash
# Minimum 80% coverage required
pytest --cov=src --cov-report=html --cov-report=term
```

### Gate 2: Integration Tests

```bash
# All integration tests must pass
pytest tests/integration/ -v
```

### Gate 3: Linting & Type Checking

```bash
# Code quality checks
black src/ tests/ --check
flake8 src/ tests/
mypy src/
```

### Gate 4: E2E Tests

```bash
# End-to-end test suite
./tests/e2e/test_mvp_flow.sh
```

### Gate 5: Performance Validation

```python
# Performance benchmarks
async def test_performance():
    """Validate performance requirements"""

    # Response time < 2 seconds
    start = time.time()
    response = await chat_agent.run("Test query", {}, "perf-test")
    elapsed = time.time() - start
    assert elapsed < 2.0, f"Response too slow: {elapsed}s"

    # Concurrent users
    tasks = []
    for i in range(10):
        task = asyncio.create_task(
            chat_agent.run(f"Query {i}", {}, f"session-{i}")
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    assert all(r is not None for r in results)
```

---

## Risk Mitigation

### Technical Risks & Mitigations

| Risk | Impact | Mitigation | Fallback |
|------|--------|------------|----------|
| OpenAI API failure | High | Implement retry logic, timeout handling | Use mock responses |
| PydanticAI integration issues | High | Start with simple agent, iterate | Fallback to direct OpenAI |
| WebSocket instability | Medium | Heartbeat mechanism, reconnection | Polling fallback |
| Memory leaks | Medium | Limit conversation storage | Periodic cleanup |
| Slow responses | Medium | Implement caching | Timeout with error message |
| Indonesian NLP accuracy | Low | Collect feedback, tune prompts | Manual intervention option |

### Mitigation Implementation

```python
# src/infrastructure/ai/fallback_agent.py
class FallbackAgent:
    """Fallback agent when PydanticAI fails"""

    async def run(self, message: str, context: Dict) -> str:
        """Simple pattern-based responses"""

        message_lower = message.lower()

        if "harga" in message_lower or "price" in message_lower:
            return "Untuk informasi harga, silakan hubungi tim sales kami."
        elif "stok" in message_lower or "stock" in message_lower:
            return "Mohon maaf, sistem sedang maintenance. Silakan coba lagi nanti."
        else:
            return "Terima kasih telah menghubungi SMS Perkasa. Tim kami akan segera membantu Anda."
```

---

## Success Criteria

### Functional Requirements

- ✅ **Chat Flow**: User can connect, send messages, receive AI responses
- ✅ **Product Search**: Agent successfully searches and returns products
- ✅ **Indonesian Language**: All responses in proper Bahasa Indonesia
- ✅ **Context Maintenance**: Conversation history maintained across messages
- ✅ **Error Handling**: Graceful degradation with Indonesian error messages

### Performance Requirements

- ✅ **Response Time**: < 2 seconds for 90% of queries
- ✅ **Concurrent Users**: Support 10-20 simultaneous connections
- ✅ **Availability**: 99% uptime during demo period
- ✅ **Memory Usage**: < 500MB for application

### Quality Requirements

- ✅ **Test Coverage**: > 80% for critical paths
- ✅ **Code Quality**: Pass all linting and type checking
- ✅ **Documentation**: All key components documented
- ✅ **Security**: API keys secured, no sensitive data exposed

### Demo Scenarios

#### Scenario 1: Product Search

```text
User: "Ada plat baja 5mm?"
PERKY: "Baik, saya akan cek ketersediaan plat baja 5mm untuk Anda.
        Kami memiliki Plat Baja SS400 5mm dengan ukuran 4x8 feet.
        Stok tersedia: 150 lembar
        Harga: Rp 1.080.000 per lembar
        Minimum order: 3 lembar"
```

#### Scenario 2: Price Inquiry

```text
User: "Berapa harga besi beton D12?"
PERKY: "Untuk Besi Beton Ulir D12 SNI:
        Ukuran: 12mm x 12m
        Harga: Rp 135.000 per batang
        Minimum order: 10 batang
        Ada diskon 3% untuk pembelian di atas 50 batang"
```

#### Scenario 3: Stock Check

```text
User: "Stock H-beam 200x200 ada?"
PERKY: "Saya cek ketersediaan H-Beam 200x200 untuk Anda.
        H-Beam 200x200x8x12 SS400:
        Stok tersedia: 30 batang
        Harga: Rp 5.800.000 per batang
        Panjang standar: 12 meter
        Bisa dikirim dalam 2-3 hari kerja"
```

---

## Appendix: Quick Reference

### Environment Setup

```bash
# Clone repository
git clone [repo-url]
cd perky-ai-assistant-v2

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run application
python -m uvicorn src.main:app --reload
```

### Testing Commands

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
./tests/e2e/test_mvp_flow.sh

# Coverage report
pytest --cov=src --cov-report=html

# All quality checks
black src/ tests/ && flake8 src/ tests/ && mypy src/ && pytest
```

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| OpenAI API key error | Verify .env file has valid key |
| Import errors | Check virtual environment is activated |
| WebSocket connection fails | Ensure port 8000 is not in use |
| Tests fail | Run `pip install -r requirements/dev.txt` |
| CORS errors | Check CORS middleware configuration |

---

## Conclusion

This comprehensive workflow provides a systematic approach to implementing Phase 5 of
the Steel Chat MVP. With 5 parallel tracks, clear convergence points, and extensive
testing, the team can deliver a working internal MVP in 2 days
(Days 4-5 of the sprint).

Key success factors:
- **Parallel Execution**: 5 teams working simultaneously
- **Clear Dependencies**: Well-defined integration points
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Risk Mitigation**: Fallback mechanisms for all critical components
- **Quality Gates**: Validation at each stage

The workflow ensures that by the end of Day 5, the Steel Chat MVP will be ready for
internal stakeholder demonstration with all three core scenarios functioning properly.
