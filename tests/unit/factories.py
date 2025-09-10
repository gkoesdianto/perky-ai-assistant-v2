"""Test factories for creating domain entities with sensible defaults."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from src.domain.entities.session import Session
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message


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
