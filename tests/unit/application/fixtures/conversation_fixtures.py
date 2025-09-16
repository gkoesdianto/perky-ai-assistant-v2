"""Conversation-related fixtures for application layer testing.

This module contains fixtures for creating sample conversations and related objects.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)


@pytest.fixture
def mock_conversation_repository():
    """Create an in-memory conversation repository for testing."""
    return InMemoryConversationRepository()


@pytest.fixture
def mock_conversation_repository_async():
    """Create a mock conversation repository with AsyncMock for unit testing."""
    repository = AsyncMock()
    repository.get_by_session = AsyncMock()
    repository.save = AsyncMock()
    repository.delete = AsyncMock()
    return repository


@pytest.fixture
def sample_conversation_with_messages():
    """Create a conversation with existing messages for testing.

    This fixture provides a conversation that already has a history
    of messages, useful for testing conversation context scenarios.
    """
    conversation = Conversation(
        session_id="test-session-123", metadata={"test": "data"}
    )

    # Add some existing messages
    conversation.add_message(
        Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Previous user message",
            metadata={},
        )
    )
    conversation.add_message(
        Message(
            conversation_id=conversation.id,
            sender_type="ai_agent",
            content="Previous AI response",
            metadata={},
        )
    )

    return conversation


@pytest.fixture
def sample_conversation_detailed():
    """Create a detailed conversation with all fields properly set for testing.

    This fixture provides a comprehensive conversation entity with
    explicit IDs, timestamps, and multiple messages.
    """
    conversation = Conversation(
        id="conv-123",
        session_id="session-456",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_activity=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        metadata={"source": "web", "user_agent": "test-browser"},
    )

    # Add messages with explicit IDs and timestamps
    message1 = Message(
        id="msg-1",
        content="Hello, I need help with steel products",
        sender_type="user",
        conversation_id="conv-123",
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        metadata={"language": "en"},
    )

    message2 = Message(
        id="msg-2",
        content="Hello! I'd be happy to help you with steel products.",
        sender_type="ai_agent",
        conversation_id="conv-123",
        created_at=datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc),
        metadata={"model": "gpt-4"},
    )

    conversation.messages = [message1, message2]
    return conversation


@pytest.fixture
def sample_conversation_empty():
    """Create an empty conversation for testing edge cases."""
    return Conversation(
        id="conv-empty",
        session_id="session-empty",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_activity=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        metadata={},
    )


@pytest.fixture
def sample_conversation_many_messages():
    """Create a conversation with many messages for testing ordering."""
    conversation = Conversation(id="conv-ordered", session_id="session-ordered")

    # Create multiple messages with specific order
    messages = []
    for i in range(5):
        msg = Message(
            id=f"msg-{i}",
            content=f"Message {i}",
            sender_type="user" if i % 2 == 0 else "ai_agent",
            conversation_id="conv-ordered",
        )
        messages.append(msg)

    conversation.messages = messages
    return conversation


__all__ = [
    "mock_conversation_repository",
    "mock_conversation_repository_async",
    "sample_conversation_with_messages",
    "sample_conversation_detailed",
    "sample_conversation_empty",
    "sample_conversation_many_messages",
]
