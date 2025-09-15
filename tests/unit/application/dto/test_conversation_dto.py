from datetime import datetime

import pytest

from src.application.dto import ConversationDTO, MessageDTO


class TestConversationDTO:
    def test_create_conversation_dto_with_required_fields(self):
        now = datetime.now()
        messages = [
            MessageDTO(
                content="First message", sender_type="user", session_id="session-123"
            ),
            MessageDTO(
                content="Second message",
                sender_type="ai_agent",
                session_id="session-123",
            ),
        ]

        dto = ConversationDTO(
            id="conv-001",
            session_id="session-123",
            messages=messages,
            started_at=now,
            last_activity=now,
        )

        assert dto.id == "conv-001"
        assert dto.session_id == "session-123"
        assert len(dto.messages) == 2
        assert dto.messages[0].content == "First message"
        assert dto.messages[1].content == "Second message"
        assert dto.started_at == now
        assert dto.last_activity == now
        assert dto.metadata == {}

    def test_create_conversation_dto_with_metadata(self):
        now = datetime.now()
        metadata = {"topic": "product inquiry", "resolved": False}

        dto = ConversationDTO(
            id="conv-002",
            session_id="session-456",
            messages=[],
            started_at=now,
            last_activity=now,
            metadata=metadata,
        )

        assert dto.id == "conv-002"
        assert dto.session_id == "session-456"
        assert dto.messages == []
        assert dto.metadata == metadata

    def test_conversation_dto_with_empty_messages(self):
        now = datetime.now()

        dto = ConversationDTO(
            id="conv-003",
            session_id="session-789",
            messages=[],
            started_at=now,
            last_activity=now,
        )

        assert dto.messages == []
        assert len(dto.messages) == 0

    def test_conversation_dto_time_progression(self):
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 30, 0)

        dto = ConversationDTO(
            id="conv-004",
            session_id="session-001",
            messages=[],
            started_at=start_time,
            last_activity=end_time,
        )

        assert dto.started_at < dto.last_activity
        assert (dto.last_activity - dto.started_at).seconds == 1800
