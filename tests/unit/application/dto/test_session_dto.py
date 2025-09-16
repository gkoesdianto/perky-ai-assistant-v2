from datetime import datetime, timezone

import pytest

from src.application.dto import SessionDTO


class TestSessionDTO:
    def test_create_session_dto_with_required_fields(self):
        now = datetime.now(timezone.utc)

        dto = SessionDTO(
            session_id="session-001",
            conversation_id="conv-001",
            started_at=now,
            last_activity=now,
            is_active=True,
        )

        assert dto.session_id == "session-001"
        assert dto.conversation_id == "conv-001"
        assert dto.started_at == now
        assert dto.last_activity == now
        assert dto.is_active is True
        assert dto.metadata == {}

    def test_create_session_dto_without_conversation(self):
        now = datetime.now(timezone.utc)

        dto = SessionDTO(
            session_id="session-002",
            conversation_id=None,
            started_at=now,
            last_activity=now,
            is_active=False,
        )

        assert dto.session_id == "session-002"
        assert dto.conversation_id is None
        assert dto.is_active is False

    def test_create_session_dto_with_metadata(self):
        now = datetime.now(timezone.utc)
        metadata = {
            "user_agent": "Mozilla/5.0",
            "ip_address": "192.168.1.1",
            "device": "desktop",
        }

        dto = SessionDTO(
            session_id="session-003",
            conversation_id="conv-003",
            started_at=now,
            last_activity=now,
            is_active=True,
            metadata=metadata,
        )

        assert dto.metadata == metadata
        assert dto.metadata["user_agent"] == "Mozilla/5.0"

    @pytest.mark.parametrize("is_active", [True, False])
    def test_session_active_states(self, is_active):
        now = datetime.now(timezone.utc)

        dto = SessionDTO(
            session_id="session-test",
            conversation_id=None,
            started_at=now,
            last_activity=now,
            is_active=is_active,
        )

        assert dto.is_active == is_active
