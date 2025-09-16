from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import pytest

from src.application.dto import MessageDTO


@dataclass
class MockMessage:
    content: str
    sender_type: str
    conversation_id: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]


class TestMessageDTO:
    def test_create_message_dto_with_required_fields(self):
        dto = MessageDTO(
            content="Hello, world!", sender_type="user", session_id="session-123"
        )

        assert dto.content == "Hello, world!"
        assert dto.sender_type == "user"
        assert dto.session_id == "session-123"
        assert dto.conversation_id is None
        assert dto.timestamp is None
        assert dto.metadata == {}

    def test_create_message_dto_with_all_fields(self):
        now = datetime.now()
        metadata = {"key": "value", "count": 42}

        dto = MessageDTO(
            content="Test message",
            sender_type="ai_agent",
            session_id="session-456",
            conversation_id="conv-789",
            timestamp=now,
            metadata=metadata,
        )

        assert dto.content == "Test message"
        assert dto.sender_type == "ai_agent"
        assert dto.session_id == "session-456"
        assert dto.conversation_id == "conv-789"
        assert dto.timestamp == now
        assert dto.metadata == metadata

    def test_from_entity_with_all_fields(self):
        now = datetime.now()
        metadata = {"processed": True}

        entity = MockMessage(
            content="Entity message",
            sender_type="user",
            conversation_id="conv-002",
            created_at=now,
            metadata=metadata,
        )

        dto = MessageDTO.from_entity(entity, session_id="session-001")

        assert dto.content == "Entity message"
        assert dto.sender_type == "user"
        assert dto.session_id == "session-001"
        assert dto.conversation_id == "conv-002"
        assert dto.timestamp == now
        assert dto.metadata == metadata

    def test_from_entity_with_none_metadata(self):
        now = datetime.now()

        entity = MockMessage(
            content="No metadata",
            sender_type="ai_agent",
            conversation_id=None,
            created_at=now,
            metadata=None,
        )

        dto = MessageDTO.from_entity(entity, session_id="session-003")

        assert dto.content == "No metadata"
        assert dto.sender_type == "ai_agent"
        assert dto.session_id == "session-003"
        assert dto.conversation_id is None
        assert dto.timestamp == now
        assert dto.metadata == {}

    @pytest.mark.parametrize("sender_type", ["user", "ai_agent"])
    def test_valid_sender_types(self, sender_type):
        dto = MessageDTO(
            content="Test", sender_type=sender_type, session_id="session-test"
        )
        assert dto.sender_type == sender_type
