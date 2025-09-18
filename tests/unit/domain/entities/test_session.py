"""Unit tests for Session entity focusing on business logic and session management."""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from src.domain.entities.session import Session
from src.domain.entities.base import BaseEntity
from tests.factories import SessionFactory


class TestSessionCreation:
    """Test suite for session creation and initialization."""

    def test_session_creation(self):
        """Test creation with required session_id."""
        session = Session(session_id="test-123")

        assert session.session_id == "test-123"
        assert session.conversation_id is None
        assert session.metadata == {}
        assert isinstance(session.started_at, datetime)
        assert isinstance(session.last_activity, datetime)
        assert session.started_at <= session.last_activity

        assert hasattr(session, "id")
        assert hasattr(session, "created_at")
        assert hasattr(session, "is_active")
        assert session.is_active is True

    def test_session_creation_with_all_fields(self):
        """Test session creation with all optional fields."""
        metadata = {"browser": "Chrome", "ip": "192.168.1.1"}
        session = Session(
            session_id="test-456", conversation_id="conv-789", metadata=metadata
        )

        assert session.session_id == "test-456"
        assert session.conversation_id == "conv-789"
        assert session.metadata == metadata
        assert session.metadata["browser"] == "Chrome"
        assert session.metadata["ip"] == "192.168.1.1"

    def test_session_inherits_base_entity(self):
        """Test that Session properly inherits from BaseEntity."""
        session = Session(session_id="test-inheritance")

        assert isinstance(session, Session)
        assert isinstance(session, BaseEntity)

        assert session.id is not None
        assert session.created_at is not None
        assert session.updated_at is None
        assert session.is_active is True


class TestSessionExpiry:
    """Test suite for session expiry logic."""

    def test_is_expired_fresh_session(self):
        """
        Test non-expired session (TTL not exceeded).
        """
        session = Session(session_id="fresh-session")

        assert not session.is_expired(3600)
        assert not session.is_expired(60)
        assert not session.is_expired(10)

    def test_is_expired_old_session(self):
        """
        Test expired session (TTL exceeded).
        """
        session = Session(session_id="old-session")

        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        session.last_activity = two_hours_ago

        assert session.is_expired(3600)
        assert session.is_expired(60)
        assert session.is_expired(7200)
        assert not session.is_expired(10000)

    @pytest.mark.parametrize(
        "ttl,expected",
        [
            (0, True),
            (-1, True),
            (-100, True),
            (86400, False),
            (999999, False),
        ],
    )
    def test_is_expired_edge_cases(self, ttl, expected):
        """
        Test with 0, negative, and very large TTL values.
        """
        session = Session(session_id="edge-case-session")

        assert session.is_expired(ttl) == expected

    def test_is_expired_with_exact_boundary(self):
        """Test expiry at exact TTL boundary."""
        session = Session(session_id="boundary-session")

        one_hour_ago = datetime.now(timezone.utc) - timedelta(seconds=3600)
        session.last_activity = one_hour_ago

        assert session.is_expired(3599)
        assert session.is_expired(3600)
        assert not session.is_expired(3601)

    def test_is_expired_with_future_activity(self):
        """Test edge case with future last_activity timestamp."""
        session = Session(session_id="future-session")

        one_hour_future = datetime.now(timezone.utc) + timedelta(hours=1)
        session.last_activity = one_hour_future

        assert not session.is_expired(3600)
        assert not session.is_expired(0)


class TestSessionActivity:
    """Test suite for session activity tracking."""

    def test_update_activity(self):
        """
        Verify update_activity() updates timestamp.
        """
        session = Session(session_id="activity-session")
        initial_activity = session.last_activity

        time.sleep(0.01)

        session.update_activity()

        assert session.last_activity > initial_activity
        assert isinstance(session.last_activity, datetime)
        assert session.last_activity.tzinfo == timezone.utc

    def test_multiple_activity_updates(self):
        """Test multiple consecutive activity updates."""
        session = Session(session_id="multi-activity")
        timestamps = [session.last_activity]

        for _ in range(5):
            time.sleep(0.01)
            session.update_activity()
            timestamps.append(session.last_activity)

        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1]

    def test_update_activity_resets_expiry(self):
        """Test that updating activity resets expiry status."""
        session = Session(session_id="reset-expiry")

        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        session.last_activity = two_hours_ago
        assert session.is_expired(3600)

        session.update_activity()

        assert not session.is_expired(3600)


class TestSessionLifecycle:
    """Test suite for complete session lifecycle."""

    def test_session_lifecycle(self):
        """
        Test complete session lifecycle from creation to expiry.
        """
        session = Session(session_id="lifecycle-session")

        assert session.conversation_id is None
        assert not session.is_expired(3600)
        assert session.is_active is True

        session.conversation_id = "conv-123"
        assert session.conversation_id == "conv-123"

        session.update_activity()

        session.metadata = {
            "browser": "Chrome",
            "ip": "192.168.1.1",
            "location": "Jakarta",
        }
        assert session.metadata["location"] == "Jakarta"

        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        session.last_activity = old_time
        assert session.is_expired(3600)

        session.is_active = False
        assert session.is_active is False

    def test_session_state_transitions(self):
        """Test various state transitions in session lifecycle."""
        session = Session(session_id="state-transition")

        assert session.is_active
        assert session.conversation_id is None

        session.conversation_id = "conv-1"
        session.update_activity()
        assert session.conversation_id == "conv-1"
        assert not session.is_expired(60)

        session.conversation_id = "conv-2"
        assert session.conversation_id == "conv-2"

        session.is_active = False
        assert not session.is_active

        session.is_active = True
        assert session.is_active


class TestSessionMetadata:
    """Test suite for session metadata storage."""

    def test_metadata_storage(self):
        """
        Test storing browser info, IP in metadata.
        """
        metadata = {
            "browser": "Firefox",
            "browser_version": "120.0",
            "ip": "10.0.0.1",
            "user_agent": "Mozilla/5.0",
            "referrer": "https://example.com",
        }

        session = Session(session_id="metadata-session", metadata=metadata)

        assert session.metadata == metadata
        assert session.metadata["browser"] == "Firefox"
        assert session.metadata["ip"] == "10.0.0.1"

    def test_metadata_update(self):
        """Test updating metadata after creation."""
        session = Session(session_id="update-metadata")

        assert session.metadata == {}

        session.metadata["key1"] = "value1"
        assert session.metadata["key1"] == "value1"

        session.metadata.update({"key2": "value2", "key3": 3})
        assert session.metadata["key2"] == "value2"
        assert session.metadata["key3"] == 3

        session.metadata = {"new": "metadata"}
        assert session.metadata == {"new": "metadata"}
        assert "key1" not in session.metadata

    def test_metadata_complex_types(self):
        """Test storing complex types in metadata."""
        metadata = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "number": 42,
            "boolean": True,
            "null": None,
        }

        session = Session(session_id="complex-metadata", metadata=metadata)

        assert session.metadata["list"] == [1, 2, 3]
        assert session.metadata["dict"]["nested"] == "value"
        assert session.metadata["number"] == 42
        assert session.metadata["boolean"] is True
        assert session.metadata["null"] is None


class TestSessionConcurrency:
    """Test suite for concurrent session operations."""

    def test_concurrent_activity_updates(self):
        """
        Test race conditions in activity updates.
        """
        session = Session(session_id="concurrent-session")
        initial_activity = session.last_activity

        def update_activity_multiple_times():
            for _ in range(10):
                session.update_activity()
                time.sleep(0.001)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_activity_multiple_times) for _ in range(5)
            ]
            for future in futures:
                future.result()

        assert session.last_activity > initial_activity
        assert isinstance(session.last_activity, datetime)

    def test_concurrent_metadata_updates(self):
        """Test concurrent updates to metadata."""
        session = Session(session_id="concurrent-metadata")

        def update_metadata(key: str, value: Any):
            session.metadata[key] = value
            time.sleep(0.001)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                futures.append(
                    executor.submit(update_metadata, f"key_{i}", f"value_{i}")
                )

            for future in futures:
                future.result()

        assert len(session.metadata) == 10
        for i in range(10):
            assert f"key_{i}" in session.metadata


class TestSessionSerialization:
    """Test suite for session serialization."""

    def test_session_model_dump(self):
        """Test serialization to dictionary."""
        metadata = {"test": "data"}
        session = Session(
            session_id="serialize-session",
            conversation_id="conv-123",
            metadata=metadata,
        )

        session_dict = session.model_dump()

        assert isinstance(session_dict, dict)
        assert session_dict["session_id"] == "serialize-session"
        assert session_dict["conversation_id"] == "conv-123"
        assert session_dict["metadata"] == metadata
        assert "started_at" in session_dict
        assert "last_activity" in session_dict
        assert "id" in session_dict
        assert "created_at" in session_dict
        assert "is_active" in session_dict

    def test_session_model_dump_json(self):
        """Test serialization to JSON."""
        import json

        session = Session(session_id="json-session")
        session_json = session.model_dump_json()

        assert isinstance(session_json, str)

        parsed = json.loads(session_json)
        assert parsed["session_id"] == "json-session"
        assert parsed["conversation_id"] is None
        assert isinstance(parsed["started_at"], str)
        assert isinstance(parsed["last_activity"], str)

    def test_session_copy(self):
        """Test creating a copy of session with modifications."""
        original = Session(
            session_id="original", conversation_id="conv-1", metadata={"key": "value"}
        )

        modified = original.model_copy(
            update={"session_id": "modified", "conversation_id": "conv-2"}
        )

        assert modified.session_id == "modified"
        assert modified.conversation_id == "conv-2"
        assert modified.metadata == {"key": "value"}
        assert modified.id == original.id

        assert original.session_id == "original"
        assert original.conversation_id == "conv-1"
