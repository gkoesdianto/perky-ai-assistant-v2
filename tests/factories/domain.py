"""Domain entity factories."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from tests.factories.base import BaseFactory
from src.domain.entities import Session, Conversation, Message
from src.domain.value_objects import ProductInfo, VariantInfo, QueryIntent


class SessionFactory(BaseFactory[Session]):
    """Factory for Session entities."""

    _model = Session

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Session-specific defaults."""
        defaults = super()._get_defaults()
        now = datetime.now(timezone.utc)
        defaults.update(
            {
                "session_id": f"session-{uuid.uuid4().hex[:8]}",
                "conversation_id": None,
                "started_at": now,
                "last_activity": now,
                "metadata": {"test": True},
                "is_active": True,
            }
        )
        return defaults

    # Define presets
    @classmethod
    def expired(cls, **kwargs) -> Session:
        """Create an expired session."""
        defaults = {"last_activity": datetime.now(timezone.utc) - timedelta(hours=25)}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def with_metadata(cls, **kwargs) -> Session:
        """Create a session with rich metadata."""
        defaults = {
            "metadata": {
                "browser": "Chrome",
                "browser_version": "120.0.0",
                "ip": "192.168.1.100",
                "location": "Jakarta",
                "test": True,
            }
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def with_conversation(cls, **kwargs) -> Session:
        """Create a session with a conversation ID."""
        defaults = {"conversation_id": f"conv-{uuid.uuid4().hex[:8]}"}
        defaults.update(kwargs)
        return cls.create(**defaults)


class ConversationFactory(BaseFactory[Conversation]):
    """Factory for Conversation entities."""

    _model = Conversation

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Conversation-specific defaults."""
        defaults = super()._get_defaults()
        now = datetime.now(timezone.utc)
        defaults.update(
            {
                "session_id": f"session-{uuid.uuid4().hex[:8]}",
                "messages": [],
                "started_at": now,
                "last_activity": now,
                "metadata": {"test": True},
            }
        )
        return defaults

    @classmethod
    def create_with_messages(cls, num_messages: int = 5, **kwargs) -> Conversation:
        """Create conversation with pre-populated messages."""
        conversation = cls.create(**kwargs)
        for i in range(num_messages):
            message = MessageFactory.create(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Test message {i}",
            )
            conversation.add_message(message)
        return conversation


class MessageFactory(BaseFactory[Message]):
    """Factory for Message entities."""

    _model = Message

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Message-specific defaults."""
        defaults = super()._get_defaults()
        defaults.update(
            {
                "conversation_id": f"conv-{uuid.uuid4().hex[:8]}",
                "sender_type": "user",
                "content": "Test message",
                "detected_language": "id",
                "intent": None,
                "metadata": {},
            }
        )
        return defaults

    # Presets
    @classmethod
    def user_message(cls, **kwargs) -> Message:
        """Create a user message."""
        defaults = {"sender_type": "user", "content": "Berapa harga plat baja?"}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def ai_message(cls, **kwargs) -> Message:
        """Create an AI agent message."""
        defaults = {
            "sender_type": "ai_agent",
            "content": "Saya bisa membantu Anda dengan informasi harga plat baja.",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def product_query(cls, **kwargs) -> Message:
        """Create a product query message."""
        defaults = {
            "sender_type": "user",
            "content": "Berapa harga plat baja 5mm?",
            "intent": "price_check",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class ProductFactory(BaseFactory[ProductInfo]):
    """Unified product factory replacing duplicate implementations."""

    _model = ProductInfo

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Product-specific defaults."""
        return {
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "product_name": "Test Product",
            "product_description": None,
            "category": None,
            "variant_count": 5,
        }

    # Presets replacing both domain and application fixtures
    @classmethod
    def steel_plate(cls, **kwargs) -> ProductInfo:
        """Create a steel plate product."""
        defaults = {
            "product_id": "prod_plat_baja",
            "product_name": "Plat Baja",
            "product_description": "High-quality steel plates for construction",
            "category": "Steel Products",
            "variant_count": 25,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def minimal(cls, **kwargs) -> ProductInfo:
        """Create a minimal product with only required fields."""
        defaults = {"product_name": "Minimal Product", "variant_count": 1}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def complete(cls, **kwargs) -> ProductInfo:
        """Create a complete product with all fields."""
        defaults = {
            "product_id": "prod_plat_baja_full",
            "product_name": "Plat Baja SS400",
            "product_description": "Plat baja kualitas tinggi untuk konstruksi",
            "category": "Steel Plates",
            "variant_count": 15,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class VariantFactory(BaseFactory[VariantInfo]):
    """Factory for VariantInfo value objects."""

    _model = VariantInfo

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Variant-specific defaults."""
        return {
            "variant_id": f"var_{uuid.uuid4().hex[:8]}",
            "sku": f"SKU-{uuid.uuid4().hex[:8]}",
            "product_id": f"prod_{uuid.uuid4().hex[:8]}",
            "variant_name": "Test Variant",
            "price": Decimal("100000"),
            "stock_quantity": 10,
            "stock_unit": "unit",
            "specifications": {},
            "source": "pim",
        }

    # Presets
    @classmethod
    def steel_plate_10mm(cls, **kwargs) -> VariantInfo:
        """Create a 10mm steel plate variant."""
        defaults = {
            "variant_id": "var_001",
            "sku": "PLT-10MM-001",
            "product_id": "prod_plat_baja",
            "variant_name": "Plat Baja 10mm x 1200mm x 2400mm",
            "price": Decimal("750000"),
            "stock_quantity": 25,
            "stock_unit": "lembar",
            "specifications": {
                "thickness": "10mm",
                "width": "1200mm",
                "length": "2400mm",
                "grade": "SS400",
            },
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def steel_plate_5mm(cls, **kwargs) -> VariantInfo:
        """Create a 5mm steel plate variant."""
        defaults = {
            "variant_id": "var_002",
            "sku": "PLT-5MM-001",
            "product_id": "prod_plat_baja",
            "variant_name": "Plat Baja 5mm x 1200mm x 2400mm",
            "price": Decimal("450000"),
            "stock_quantity": 50,
            "stock_unit": "lembar",
            "specifications": {
                "thickness": "5mm",
                "width": "1200mm",
                "length": "2400mm",
                "grade": "SS400",
            },
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class QueryIntentFactory(BaseFactory[QueryIntent]):
    """Factory for QueryIntent value objects."""

    _model = QueryIntent

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """QueryIntent-specific defaults."""
        return {
            "intent_type": "general",
            "confidence": 0.9,
            "entities": {},
        }

    # Presets
    @classmethod
    def product_inquiry(cls, **kwargs) -> QueryIntent:
        """Create a product inquiry intent."""
        defaults = {
            "intent_type": "product_inquiry",
            "confidence": 0.95,
            "entities": {"product": "plat baja"},
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def price_check(cls, **kwargs) -> QueryIntent:
        """Create a price check intent."""
        defaults = {
            "intent_type": "price_check",
            "confidence": 0.92,
            "entities": {"product": "plat baja", "specification": "5mm"},
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def availability_check(cls, **kwargs) -> QueryIntent:
        """Create an availability check intent."""
        defaults = {
            "intent_type": "availability_check",
            "confidence": 0.88,
            "entities": {"product": "plat baja"},
        }
        defaults.update(kwargs)
        return cls.create(**defaults)
