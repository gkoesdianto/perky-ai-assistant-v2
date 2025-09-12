"""Test factories for creating domain entities with sensible defaults."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from decimal import Decimal
from src.domain.entities.session import Session
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.value_objects.product_info import ProductInfo
from src.domain.value_objects.query_intent import QueryIntent
from src.domain.value_objects.variant_info import VariantInfo


class SessionFactory:
    """Factory for creating test sessions with sensible defaults."""

    @staticmethod
    def create(
        session_id: str = None,
        conversation_id: str = None,
        metadata: Dict[str, Any] = None,
        **kwargs,
    ) -> Session:
        """Create test session with sensible defaults."""
        defaults = {
            "session_id": session_id or f"session-{uuid.uuid4().hex[:8]}",
            "conversation_id": conversation_id,
            "metadata": metadata or {"test": True},
        }
        return Session(**{**defaults, **kwargs})

    @staticmethod
    def create_expired(ttl: int = 3600) -> Session:
        """Create an already-expired session."""
        session = SessionFactory.create()
        hours_ago = (ttl / 3600) + 1
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        return session

    @staticmethod
    def create_with_conversation(conversation_id: str = None) -> Session:
        """Create session with conversation attached."""
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
        return SessionFactory.create(conversation_id=conv_id)

    @staticmethod
    def create_with_metadata() -> Session:
        """Create session with realistic metadata."""
        metadata = {
            "browser": "Chrome",
            "browser_version": "120.0.0",
            "ip": "192.168.1.100",
            "location": "Jakarta",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "screen_resolution": "1920x1080",
        }
        return SessionFactory.create(metadata=metadata)


class ConversationFactory:
    """Factory for creating test conversations with sensible defaults."""

    @staticmethod
    def create(
        session_id: str = None, metadata: Dict[str, Any] = None, **kwargs
    ) -> Conversation:
        """Create test conversation with sensible defaults."""
        defaults = {
            "session_id": session_id or f"session-{uuid.uuid4().hex[:8]}",
            "metadata": metadata or {"test": True},
        }
        return Conversation(**{**defaults, **kwargs})

    @staticmethod
    def create_with_messages(num_messages: int = 5) -> Conversation:
        """Create conversation with pre-populated messages."""
        conversation = ConversationFactory.create()

        for i in range(num_messages):
            message = Message(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Test message {i}",
                detected_language="id",
            )
            conversation.add_message(message)

        return conversation

    @staticmethod
    def create_with_product_queries() -> Conversation:
        """Create conversation with product-related messages."""
        conversation = ConversationFactory.create()

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Berapa harga plat baja 5mm?",
                intent="price_check",
                detected_language="id",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Plat baja 5mm harga Rp 150.000 per lembar",
                detected_language="id",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Ada stok berapa lembar?",
                intent="stock_check",
                detected_language="id",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Stok tersedia 100 lembar",
                detected_language="id",
            ),
        ]

        for msg in messages:
            conversation.add_message(msg)

        return conversation

    @staticmethod
    def create_with_metadata() -> Conversation:
        """Create conversation with realistic metadata."""
        metadata = {
            "channel": "web",
            "locale": "id-ID",
            "browser": "Chrome",
            "device": "desktop",
            "referrer": "https://example.com",
            "user_preferences": {
                "theme": "light",
                "notifications": True,
                "language": "id",
            },
        }
        return ConversationFactory.create(metadata=metadata)


class MessageFactory:
    """Factory for creating test messages with sensible defaults."""

    @staticmethod
    def create_user_message(
        conversation_id: str = None, content: str = "Berapa harga plat baja?", **kwargs
    ) -> Message:
        """Create user message with Indonesian content."""
        defaults = {
            "conversation_id": conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
            "sender_type": "user",
            "content": content,
            "detected_language": "id",
        }
        return Message(**{**defaults, **kwargs})

    @staticmethod
    def create_ai_message(
        conversation_id: str = None, content: str = "Saya bisa membantu Anda", **kwargs
    ) -> Message:
        """Create AI agent message."""
        defaults = {
            "conversation_id": conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
            "sender_type": "ai_agent",
            "content": content,
            "detected_language": "id",
        }
        return Message(**{**defaults, **kwargs})

    @staticmethod
    def create_product_query(
        conversation_id: str = None, intent: str = "price_check"
    ) -> Message:
        """Create message with product query intent."""
        content_map = {
            "price_check": "Berapa harga plat baja 5mm?",
            "stock_check": "Ada stok plat baja SS400?",
            "product_inquiry": "Spesifikasi plat baja apa saja?",
        }

        return MessageFactory.create_user_message(
            conversation_id=conversation_id,
            content=content_map.get(intent, "Product query"),
            intent=intent,
        )


class ProductInfoFactory:
    @staticmethod
    def create(**kwargs) -> ProductInfo:
        defaults = {
            "sku": f"PROD-{uuid.uuid4().hex[:6].upper()}",
            "name": "Test Product",
            "unit": "lembar",
        }
        return ProductInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_steel_product(**kwargs) -> ProductInfo:
        defaults = {
            "sku": f"STEEL-{uuid.uuid4().hex[:6].upper()}",
            "name": "Plat Baja 5mm",
            "price": 150000.0,
            "stock": 100,
            "unit": "lembar",
            "specifications": {
                "thickness": "5mm",
                "width": "1200mm",
                "length": "2400mm",
            },
        }
        return ProductInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_with_required_fields_only(
        sku: str = None, name: str = None
    ) -> ProductInfo:
        return ProductInfo(
            sku=sku or f"MIN-{uuid.uuid4().hex[:6].upper()}",
            name=name or "Minimal Product",
        )

    @staticmethod
    def create_with_all_fields() -> ProductInfo:
        return ProductInfo(
            sku=f"FULL-{uuid.uuid4().hex[:6].upper()}",
            name="Plat Baja SS400",
            description="Plat baja kualitas tinggi untuk konstruksi",
            price=250000.0,
            stock=50,
            unit="lembar",
            specifications={
                "grade": "SS400",
                "thickness": "10mm",
                "width": "1500mm",
                "length": "3000mm",
                "weight": "117.75kg",
            },
            source="pim",
        )

    @staticmethod
    def create_from_cache(**kwargs) -> ProductInfo:
        defaults = {
            "sku": f"CACHE-{uuid.uuid4().hex[:6].upper()}",
            "name": "Cached Product",
            "source": "cache",
        }
        return ProductInfo(**{**defaults, **kwargs})


class QueryIntentFactory:
    @staticmethod
    def create(**kwargs) -> QueryIntent:
        defaults = {"type": "general", "confidence": 0.85}
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_product_inquiry(**kwargs) -> QueryIntent:
        defaults = {
            "type": "product_inquiry",
            "product_name": "plat baja",
            "confidence": 0.95,
        }
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_price_check(**kwargs) -> QueryIntent:
        defaults = {
            "type": "price_check",
            "product_name": "plat baja 5mm",
            "confidence": 0.98,
        }
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_stock_check(**kwargs) -> QueryIntent:
        defaults = {
            "type": "stock_check",
            "product_name": "plat baja SS400",
            "quantity": 10,
            "confidence": 0.92,
        }
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_general_query(**kwargs) -> QueryIntent:
        defaults = {"type": "general", "confidence": 0.85}
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_with_low_confidence(type: str = "general", **kwargs) -> QueryIntent:
        defaults = {"type": type, "confidence": 0.3}
        return QueryIntent(**{**defaults, **kwargs})

    @staticmethod
    def create_with_high_confidence(
        type: str = "product_inquiry", **kwargs
    ) -> QueryIntent:
        defaults = {"type": type, "confidence": 0.99}
        return QueryIntent(**{**defaults, **kwargs})


class VariantInfoFactory:
    """Factory for creating test VariantInfo instances with sensible defaults."""

    @staticmethod
    def create(**kwargs) -> VariantInfo:
        """Create basic variant with minimal required fields."""
        defaults = {
            "variant_id": f"var_{uuid.uuid4().hex[:8]}",
            "sku": f"SKU-{uuid.uuid4().hex[:6].upper()}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Test Variant",
            "price": Decimal("100000"),
            "stock_quantity": 10,
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_steel_variant(**kwargs) -> VariantInfo:
        """Create realistic steel product variant."""
        defaults = {
            "variant_id": f"var_steel_{uuid.uuid4().hex[:8]}",
            "sku": f"STEEL-{uuid.uuid4().hex[:6].upper()}",
            "product_id": "prod_plat_baja",
            "variant_name": "Plat Baja 5mm x 1200mm x 2400mm",
            "price": Decimal("500000"),
            "stock_quantity": 25,
            "stock_unit": "lembar",
            "specifications": {
                "thickness": "5mm",
                "width": "1200mm",
                "length": "2400mm",
                "grade": "SS400",
                "weight": "56.52kg",
            },
            "source": "pim",
            "is_available": True,
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_hollow_variant(
        material: str = "hitam", dimensions: str = "40x40", **kwargs
    ) -> VariantInfo:
        """Create hollow steel (besi hollow) variant."""
        defaults = {
            "variant_id": f"var_hollow_{uuid.uuid4().hex[:8]}",
            "sku": f"HOLLOW-{material.upper()}-{dimensions}",
            "product_id": "prod_hollow",
            "variant_name": f"Besi Hollow {material.title()} {dimensions}",
            "price": Decimal("750000"),
            "stock_quantity": 50,
            "stock_unit": "batang",
            "specifications": {
                "material": material,
                "dimensions": dimensions,
                "thickness": "2mm",
                "length": "6000mm",
                "type": "square",
            },
            "source": "pim",
            "is_available": True,
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_out_of_stock(**kwargs) -> VariantInfo:
        """Create variant with no stock."""
        defaults = {
            "variant_id": f"var_oos_{uuid.uuid4().hex[:8]}",
            "sku": f"OOS-{uuid.uuid4().hex[:6].upper()}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Out of Stock Variant",
            "price": Decimal("200000"),
            "stock_quantity": 0,
            "is_available": True,
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_unavailable(**kwargs) -> VariantInfo:
        """Create unavailable variant (discontinued/inactive)."""
        defaults = {
            "variant_id": f"var_unavail_{uuid.uuid4().hex[:8]}",
            "sku": f"UNAVAIL-{uuid.uuid4().hex[:6].upper()}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Unavailable Variant",
            "price": Decimal("150000"),
            "stock_quantity": 100,
            "is_available": False,
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_from_cache(**kwargs) -> VariantInfo:
        """Create variant from cache source."""
        defaults = {
            "variant_id": f"var_cache_{uuid.uuid4().hex[:8]}",
            "sku": f"CACHE-{uuid.uuid4().hex[:6].upper()}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Cached Variant",
            "price": Decimal("300000"),
            "stock_quantity": 15,
            "source": "cache",
        }
        return VariantInfo(**{**defaults, **kwargs})

    @staticmethod
    def create_with_specifications(specs: Dict[str, Any], **kwargs) -> VariantInfo:
        """Create variant with custom specifications."""
        defaults = {
            "variant_id": f"var_spec_{uuid.uuid4().hex[:8]}",
            "sku": f"SPEC-{uuid.uuid4().hex[:6].upper()}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Variant with Specifications",
            "price": Decimal("450000"),
            "stock_quantity": 30,
            "specifications": specs,
        }
        return VariantInfo(**{**defaults, **kwargs})
