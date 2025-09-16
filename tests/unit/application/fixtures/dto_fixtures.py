"""DTO fixtures for application layer testing.

This module contains fixtures for creating sample DTOs used in tests.
"""

from datetime import datetime, timezone

import pytest

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.session_dto import SessionDTO


@pytest.fixture
def sample_session_dto():
    """Create a sample SessionDTO for testing."""
    now = datetime.now(timezone.utc)
    return SessionDTO(
        session_id="test-session-123",
        conversation_id="conv-456",
        started_at=now,
        last_activity=now,
        is_active=True,
        metadata={"source": "test"},
    )


@pytest.fixture
def sample_message_dto():
    """Create a sample MessageDTO for testing."""
    now = datetime.now()
    return MessageDTO(
        content="Test message",
        sender_type="user",
        session_id="test-session-123",
        conversation_id="conv-456",
        timestamp=now,
        metadata={},
    )


@pytest.fixture
def sample_conversation_dto():
    """Create a sample ConversationDTO for testing."""
    now = datetime.now(timezone.utc)
    return ConversationDTO(
        id="conv-456",
        session_id="test-session-123",
        messages=[],
        started_at=now,
        last_activity=now,
        metadata={},
    )


@pytest.fixture
def sample_conversation_context():
    """Create sample conversation context for testing."""
    now = datetime.now()
    return [
        MessageDTO(
            content="Saya butuh plat baja tebal 10mm",
            sender_type="user",
            session_id="session-123",
            conversation_id="conv-1",
            timestamp=now,
            metadata={},
        ),
        MessageDTO(
            content="Baik, kami punya plat baja 10mm. Berapa lembar yang dibutuhkan?",
            sender_type="ai_agent",
            session_id="session-123",
            conversation_id="conv-1",
            timestamp=now,
            metadata={},
        ),
    ]


@pytest.fixture
def sample_query_analyzer_messages():
    """Create sample message DTOs for query analyzer testing."""
    return [
        MessageDTO(
            content="Saya mencari besi hollow",
            sender_type="user",
            session_id="session-123",
            conversation_id="conv-456",
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        MessageDTO(
            content=(
                "Kami memiliki berbagai ukuran besi hollow. "
                "Ukuran apa yang Anda cari?"
            ),
            sender_type="ai_agent",
            session_id="session-123",
            conversation_id="conv-456",
            timestamp=datetime(2024, 1, 1, 10, 0, 10, tzinfo=timezone.utc),
        ),
        MessageDTO(
            content="Yang ukuran 4x4",
            sender_type="user",
            session_id="session-123",
            conversation_id="conv-456",
            timestamp=datetime(2024, 1, 1, 10, 0, 20, tzinfo=timezone.utc),
        ),
    ]


__all__ = [
    "sample_session_dto",
    "sample_message_dto",
    "sample_conversation_dto",
    "sample_conversation_context",
    "sample_query_analyzer_messages",
]
