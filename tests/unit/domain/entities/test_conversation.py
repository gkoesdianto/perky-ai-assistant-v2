"""Unit tests for Conversation entity focusing on message management and context retrieval."""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.base import BaseEntity
from tests.factories import ConversationFactory, MessageFactory


class TestConversationCreation:
    """Test suite for conversation creation and initialization."""

    def test_conversation_creation(self):
        """
        Test creation with session_id.
        """
        conversation = Conversation(session_id="test-session-123")

        assert conversation.session_id == "test-session-123"
        assert conversation.messages == []
        assert conversation.metadata == {}
        assert isinstance(conversation.started_at, datetime)
        assert isinstance(conversation.last_activity, datetime)
        assert conversation.started_at <= conversation.last_activity

        assert hasattr(conversation, "id")
        assert hasattr(conversation, "created_at")
        assert hasattr(conversation, "is_active")
        assert conversation.is_active is True

    def test_empty_messages_list(self):
        """
        Verify messages list initializes empty.
        """
        conversation = Conversation(session_id="empty-messages-session")

        assert conversation.messages == []
        assert isinstance(conversation.messages, list)
        assert len(conversation.messages) == 0

    def test_conversation_with_metadata(self):
        """Test conversation creation with metadata."""
        metadata = {"channel": "web", "locale": "id-ID", "theme": "dark"}
        conversation = Conversation(session_id="metadata-session", metadata=metadata)

        assert conversation.metadata == metadata
        assert conversation.metadata["channel"] == "web"
        assert conversation.metadata["locale"] == "id-ID"
        assert conversation.metadata["theme"] == "dark"

    def test_conversation_inherits_base_entity(self):
        """Test that Conversation properly inherits from BaseEntity."""
        conversation = Conversation(session_id="inheritance-test")

        assert isinstance(conversation, Conversation)
        assert isinstance(conversation, BaseEntity)

        assert conversation.id is not None
        assert conversation.created_at is not None
        assert conversation.updated_at is None
        assert conversation.is_active is True


class TestMessageManagement:
    """Test suite for message management operations."""

    def test_add_single_message(self):
        """
        Test adding one message.
        """
        conversation = Conversation(session_id="single-message-session")
        initial_activity = conversation.last_activity

        time.sleep(0.01)

        message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Berapa harga plat baja 5mm?",
        )

        conversation.add_message(message)

        assert len(conversation.messages) == 1
        assert conversation.messages[0] == message
        assert conversation.messages[0].content == "Berapa harga plat baja 5mm?"
        assert conversation.last_activity > initial_activity

    def test_add_multiple_messages(self):
        """
        Test adding multiple messages.
        """
        conversation = Conversation(session_id="multi-message-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Halo, saya butuh informasi produk",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Selamat datang! Produk apa yang Anda cari?",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Saya cari plat baja tebal 5mm",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Baik, kami memiliki plat baja 5mm dengan berbagai ukuran",
            ),
        ]

        for msg in messages:
            time.sleep(0.01)
            conversation.add_message(msg)

        assert len(conversation.messages) == 4
        assert conversation.messages == messages
        assert conversation.messages[0].sender_type == "user"
        assert conversation.messages[1].sender_type == "ai_agent"
        assert conversation.messages[2].content == "Saya cari plat baja tebal 5mm"

    def test_last_activity_update(self):
        """
        Verify last_activity updates on add_message.
        """
        conversation = Conversation(session_id="activity-update-session")
        timestamps = [conversation.last_activity]

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content=f"Message {i}",
            )
            for i in range(5)
        ]

        for msg in messages:
            time.sleep(0.01)
            conversation.add_message(msg)
            timestamps.append(conversation.last_activity)

        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1]

        assert isinstance(conversation.last_activity, datetime)
        assert conversation.last_activity.tzinfo == timezone.utc

    def test_add_messages_with_intents(self):
        """Test adding messages with different intents."""
        conversation = Conversation(session_id="intent-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Berapa harga plat baja?",
                intent="price_check",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Ada stok plat baja 10mm?",
                intent="stock_check",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Spesifikasi plat baja SS400?",
                intent="product_inquiry",
            ),
        ]

        for msg in messages:
            conversation.add_message(msg)

        assert conversation.messages[0].intent == "price_check"
        assert conversation.messages[1].intent == "stock_check"
        assert conversation.messages[2].intent == "product_inquiry"

        assert conversation.messages[0].is_product_query() is True
        assert conversation.messages[1].is_product_query() is True
        assert conversation.messages[2].is_product_query() is True

    def test_add_messages_with_metadata(self):
        """Test adding messages with metadata."""
        conversation = Conversation(session_id="message-metadata-session")

        message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Saya butuh plat baja",
            metadata={"confidence": 0.95, "source": "web_chat"},
        )

        conversation.add_message(message)

        assert conversation.messages[0].metadata["confidence"] == 0.95
        assert conversation.messages[0].metadata["source"] == "web_chat"


class TestContextRetrieval:
    """Test suite for context retrieval functionality."""

    def test_get_context_empty(self):
        """
        Test get_context with no messages.
        """
        conversation = Conversation(session_id="empty-context-session")

        context = conversation.get_context()
        assert context == []
        assert isinstance(context, list)

        context_with_limit = conversation.get_context(limit=5)
        assert context_with_limit == []

    def test_get_context_within_limit(self):
        """
        Test with fewer messages than limit.
        """
        conversation = Conversation(session_id="within-limit-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Message {i}",
            )
            for i in range(5)
        ]

        for msg in messages:
            conversation.add_message(msg)

        context = conversation.get_context(limit=10)

        assert len(context) == 5
        assert context == messages
        assert context[0].content == "Message 0"
        assert context[-1].content == "Message 4"

    def test_get_context_exceeds_limit(self):
        """
        Test with more messages than limit.
        """
        conversation = Conversation(session_id="exceeds-limit-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Message {i}",
            )
            for i in range(20)
        ]

        for msg in messages:
            conversation.add_message(msg)

        context = conversation.get_context(limit=10)

        assert len(context) == 10
        assert context == messages[-10:]
        assert context[0].content == "Message 10"
        assert context[-1].content == "Message 19"

    def test_get_context_exact_limit(self):
        """
        Test with exactly limit messages.
        """
        conversation = Conversation(session_id="exact-limit-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Message {i}",
            )
            for i in range(10)
        ]

        for msg in messages:
            conversation.add_message(msg)

        context = conversation.get_context(limit=10)

        assert len(context) == 10
        assert context == messages
        assert context[0].content == "Message 0"
        assert context[-1].content == "Message 9"

    def test_get_context_with_limit_one(self):
        """Test get_context with limit=1."""
        conversation = Conversation(session_id="limit-one-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content=f"Message {i}",
            )
            for i in range(5)
        ]

        for msg in messages:
            conversation.add_message(msg)

        context = conversation.get_context(limit=1)

        assert len(context) == 1
        assert context[0] == messages[-1]
        assert context[0].content == "Message 4"

    def test_get_context_default_limit(self):
        """Test get_context with default limit of 10."""
        conversation = Conversation(session_id="default-limit-session")

        messages = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content=f"Message {i}",
            )
            for i in range(15)
        ]

        for msg in messages:
            conversation.add_message(msg)

        context = conversation.get_context()

        assert len(context) == 10
        assert context == messages[-10:]


class TestConversationLifecycle:
    """Test suite for conversation lifecycle and state management."""

    def test_conversation_lifecycle(self):
        """Test complete conversation lifecycle."""
        conversation = Conversation(session_id="lifecycle-session")

        assert len(conversation.messages) == 0
        assert conversation.is_active is True

        user_msg = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Halo, saya butuh bantuan",
            intent="general",
        )
        conversation.add_message(user_msg)

        assert len(conversation.messages) == 1

        ai_msg = Message(
            conversation_id=conversation.id,
            sender_type="ai_agent",
            content="Selamat datang! Bagaimana saya bisa membantu?",
        )
        conversation.add_message(ai_msg)

        assert len(conversation.messages) == 2

        conversation.metadata["status"] = "active"
        conversation.metadata["rating"] = 5
        assert conversation.metadata["status"] == "active"

        conversation.is_active = False
        assert conversation.is_active is False

    def test_conversation_with_product_queries(self):
        """Test conversation with product-related queries."""
        conversation = Conversation(session_id="product-query-session")

        product_queries = [
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Berapa harga plat baja SS400?",
                intent="price_check",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Plat baja SS400 harga Rp 150.000 per lembar",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="Ada stok untuk ukuran 5mm?",
                intent="stock_check",
            ),
            Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content="Stok tersedia 100 lembar",
            ),
        ]

        for msg in product_queries:
            conversation.add_message(msg)

        product_messages = [
            msg
            for msg in conversation.messages
            if hasattr(msg, "is_product_query") and msg.is_product_query()
        ]

        assert len(product_messages) == 2
        assert all(msg.sender_type == "user" for msg in product_messages)

    def test_conversation_timestamps(self):
        """Test timestamp management in conversation."""
        conversation = Conversation(session_id="timestamp-session")

        assert conversation.started_at <= conversation.last_activity

        initial_start = conversation.started_at
        initial_activity = conversation.last_activity

        time.sleep(0.01)

        message = Message(
            conversation_id=conversation.id, sender_type="user", content="Test message"
        )
        conversation.add_message(message)

        assert conversation.started_at == initial_start
        assert conversation.last_activity > initial_activity


class TestConversationMetadata:
    """Test suite for conversation metadata management."""

    def test_metadata_dict(self):
        """
        Test metadata storage and retrieval.
        """
        conversation = Conversation(session_id="metadata-test-session")

        assert conversation.metadata == {}

        conversation.metadata["channel"] = "web"
        conversation.metadata["locale"] = "id-ID"
        conversation.metadata["user_preferences"] = {
            "theme": "dark",
            "notifications": True,
        }

        assert conversation.metadata["channel"] == "web"
        assert conversation.metadata["locale"] == "id-ID"
        assert conversation.metadata["user_preferences"]["theme"] == "dark"
        assert conversation.metadata["user_preferences"]["notifications"] is True

    def test_metadata_update(self):
        """Test updating metadata after creation."""
        conversation = Conversation(session_id="update-metadata-session")

        conversation.metadata["key1"] = "value1"
        assert conversation.metadata["key1"] == "value1"

        conversation.metadata.update({"key2": "value2", "key3": 3, "key4": [1, 2, 3]})

        assert conversation.metadata["key2"] == "value2"
        assert conversation.metadata["key3"] == 3
        assert conversation.metadata["key4"] == [1, 2, 3]

        conversation.metadata = {"new": "metadata"}
        assert conversation.metadata == {"new": "metadata"}
        assert "key1" not in conversation.metadata

    def test_metadata_complex_types(self):
        """Test storing complex types in metadata."""
        metadata = {
            "list": [1, 2, 3],
            "dict": {"nested": "value", "level2": {"deep": True}},
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "mixed_list": [1, "two", {"three": 3}, None],
        }

        conversation = Conversation(
            session_id="complex-metadata-session", metadata=metadata
        )

        assert conversation.metadata["list"] == [1, 2, 3]
        assert conversation.metadata["dict"]["nested"] == "value"
        assert conversation.metadata["dict"]["level2"]["deep"] is True
        assert conversation.metadata["number"] == 42
        assert conversation.metadata["float"] == 3.14
        assert conversation.metadata["boolean"] is True
        assert conversation.metadata["null"] is None
        assert conversation.metadata["mixed_list"][2]["three"] == 3


class TestConversationConcurrency:
    """Test suite for concurrent operations on conversation."""

    def test_concurrent_message_additions(self):
        """Test concurrent addition of messages."""
        conversation = Conversation(session_id="concurrent-messages")

        def add_messages(start_idx: int):
            for i in range(start_idx, start_idx + 5):
                message = Message(
                    conversation_id=conversation.id,
                    sender_type="user",
                    content=f"Concurrent message {i}",
                )
                conversation.add_message(message)
                time.sleep(0.001)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(add_messages, i * 5) for i in range(3)]
            for future in futures:
                future.result()

        assert len(conversation.messages) == 15

        contents = [msg.content for msg in conversation.messages]
        for i in range(15):
            assert f"Concurrent message {i}" in contents

    def test_concurrent_context_retrieval(self):
        """Test concurrent context retrieval operations."""
        conversation = Conversation(session_id="concurrent-context")

        for i in range(20):
            message = Message(
                conversation_id=conversation.id,
                sender_type="user",
                content=f"Message {i}",
            )
            conversation.add_message(message)

        contexts = []

        def get_context_multiple_times(limit: int):
            for _ in range(10):
                context = conversation.get_context(limit=limit)
                contexts.append(len(context))
                time.sleep(0.001)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(get_context_multiple_times, limit)
                for limit in [5, 10, 15, 10, 5]
            ]
            for future in futures:
                future.result()

        assert all(isinstance(ctx_len, int) for ctx_len in contexts)
        assert 5 in contexts
        assert 10 in contexts
        assert 15 in contexts


class TestConversationSerialization:
    """Test suite for conversation serialization."""

    def test_conversation_model_dump(self):
        """Test serialization to dictionary."""
        metadata = {"test": "data", "channel": "web"}
        conversation = Conversation(session_id="serialize-session", metadata=metadata)

        message = Message(
            conversation_id=conversation.id, sender_type="user", content="Test message"
        )
        conversation.add_message(message)

        conv_dict = conversation.model_dump()

        assert isinstance(conv_dict, dict)
        assert conv_dict["session_id"] == "serialize-session"
        assert conv_dict["metadata"] == metadata
        assert len(conv_dict["messages"]) == 1
        assert "started_at" in conv_dict
        assert "last_activity" in conv_dict
        assert "id" in conv_dict
        assert "created_at" in conv_dict
        assert "is_active" in conv_dict

    def test_conversation_model_dump_json(self):
        """Test serialization to JSON."""
        import json

        conversation = Conversation(session_id="json-session")

        message = Message(
            conversation_id=conversation.id, sender_type="user", content="JSON test"
        )
        conversation.add_message(message)

        conv_json = conversation.model_dump_json()

        assert isinstance(conv_json, str)

        parsed = json.loads(conv_json)
        assert parsed["session_id"] == "json-session"
        assert len(parsed["messages"]) == 1
        assert isinstance(parsed["started_at"], str)
        assert isinstance(parsed["last_activity"], str)

    def test_conversation_copy(self):
        """Test creating a copy of conversation with modifications."""
        original = Conversation(
            session_id="original-session", metadata={"key": "value"}
        )

        message = Message(
            conversation_id=original.id, sender_type="user", content="Original message"
        )
        original.add_message(message)

        modified = original.model_copy(update={"session_id": "modified-session"})

        assert modified.session_id == "modified-session"
        assert modified.metadata == {"key": "value"}
        assert len(modified.messages) == 1
        assert modified.id == original.id

        assert original.session_id == "original-session"
