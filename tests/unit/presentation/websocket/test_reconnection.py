"""Unit tests for WebSocket reconnection manager."""

import asyncio
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from src.presentation.websocket.reconnection import (
    ConnectionRecovery,
    ConnectionState,
    ReconnectionManager,
    SessionState,
)


class TestReconnectionManager:
    """Test cases for ReconnectionManager."""

    @pytest.mark.asyncio
    async def test_register_disconnection(self):
        """Test registering a disconnection."""
        manager = ReconnectionManager()
        await manager.start()

        session_id = "test-session-1"
        connection_id = "test-conn-1"
        state = {
            "last_activity": datetime.now(),
            "metadata": {"user_agent": "test"},
        }

        manager.register_disconnection(session_id, connection_id, state)

        # Check registration
        assert session_id in manager.disconnected_sessions
        session_state = manager.disconnected_sessions[session_id]
        assert session_state.connection_id == connection_id
        assert session_state.session_id == session_id
        assert session_state.metadata == state

        await manager.stop()

    def test_can_reconnect_new_session(self):
        """Test that new sessions can always connect."""
        manager = ReconnectionManager()

        can_reconnect, reason = manager.can_reconnect("new-session")
        assert can_reconnect
        assert reason is None

    @freeze_time("2024-01-01 12:00:00")
    def test_can_reconnect_within_window(self):
        """Test reconnection within allowed window."""
        manager = ReconnectionManager(reconnection_window=60)

        session_id = "test-session"
        manager.register_disconnection(session_id, "conn-1")

        # Should be able to reconnect immediately
        can_reconnect, reason = manager.can_reconnect(session_id)
        assert can_reconnect

        # Should be able to reconnect after 30 seconds
        with freeze_time("2024-01-01 12:00:30"):
            can_reconnect, reason = manager.can_reconnect(session_id)
            assert can_reconnect

        # Should NOT be able to reconnect after 61 seconds
        with freeze_time("2024-01-01 12:01:01"):
            can_reconnect, reason = manager.can_reconnect(session_id)
            assert not can_reconnect
            assert "window expired" in reason

    def test_can_reconnect_max_attempts(self):
        """Test reconnection attempt limits."""
        manager = ReconnectionManager(max_reconnect_attempts=2)

        session_id = "test-session"
        session_state = SessionState(
            connection_id="conn-1",
            session_id=session_id,
            disconnected_at=datetime.now(),
            reconnect_count=2,
        )
        manager.disconnected_sessions[session_id] = session_state

        can_reconnect, reason = manager.can_reconnect(session_id)
        assert not can_reconnect
        assert "Maximum reconnection attempts exceeded" in reason

    @pytest.mark.asyncio
    async def test_handle_reconnection_success(self):
        """Test successful reconnection handling."""
        manager = ReconnectionManager()
        await manager.start()

        session_id = "test-session"
        old_connection_id = "old-conn"
        new_connection_id = "new-conn"

        # Register disconnection
        manager.register_disconnection(session_id, old_connection_id)

        # Handle reconnection
        session_state = await manager.handle_reconnection(session_id, new_connection_id)

        assert session_state is not None
        assert session_state.connection_id == new_connection_id
        assert session_state.reconnect_count == 1
        # Should be removed from disconnected sessions
        assert session_id not in manager.disconnected_sessions

        await manager.stop()

    @pytest.mark.asyncio
    async def test_handle_reconnection_denied(self):
        """Test reconnection denial after window expires."""
        manager = ReconnectionManager(reconnection_window=1)
        await manager.start()

        session_id = "test-session"

        with freeze_time("2024-01-01 12:00:00"):
            manager.register_disconnection(session_id, "old-conn")

        # Try to reconnect after window expires
        with freeze_time("2024-01-01 12:00:02"):
            session_state = await manager.handle_reconnection(session_id, "new-conn")
            assert session_state is None

        await manager.stop()

    @pytest.mark.asyncio
    async def test_handle_new_session(self):
        """Test handling a completely new session."""
        manager = ReconnectionManager()
        await manager.start()

        session_state = await manager.handle_reconnection(
            "brand-new-session", "new-conn"
        )

        assert session_state is not None
        assert session_state.session_id == "brand-new-session"
        assert session_state.connection_id == "new-conn"
        assert session_state.reconnect_count == 0

        await manager.stop()

    def test_queue_message_for_reconnection(self):
        """Test queuing messages for disconnected sessions."""
        manager = ReconnectionManager()

        session_id = "test-session"
        manager.register_disconnection(session_id, "conn-1")

        # Queue a message
        message = {"type": "test", "data": "hello"}
        queued = manager.queue_message_for_reconnection(session_id, message)
        assert queued

        # Check message was queued
        session_state = manager.disconnected_sessions[session_id]
        assert len(session_state.pending_messages) == 1
        assert session_state.pending_messages[0]["message"] == message

        # Try to queue for non-existent session
        queued = manager.queue_message_for_reconnection("unknown", message)
        assert not queued

    def test_queue_message_size_limit(self):
        """Test that message queue has a size limit."""
        manager = ReconnectionManager()

        session_id = "test-session"
        manager.register_disconnection(session_id, "conn-1")

        # Queue more than max messages
        for i in range(105):
            message = {"id": i}
            manager.queue_message_for_reconnection(session_id, message)

        # Should only keep last 100 messages
        session_state = manager.disconnected_sessions[session_id]
        assert len(session_state.pending_messages) == 100
        # First message should be id=5 (0-4 were dropped)
        assert session_state.pending_messages[0]["message"]["id"] == 5

    @freeze_time("2024-01-01 12:00:00")
    def test_get_session_state(self):
        """Test retrieving session state."""
        manager = ReconnectionManager(state_ttl=60)

        session_id = "test-session"
        manager.register_disconnection(session_id, "conn-1")

        # Should get state within TTL
        state = manager.get_session_state(session_id)
        assert state is not None
        assert state.session_id == session_id

        # Should return None after TTL expires
        with freeze_time("2024-01-01 12:01:01"):
            state = manager.get_session_state(session_id)
            assert state is None
            # Should be cleaned up
            assert session_id not in manager.disconnected_sessions

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test automatic cleanup of expired sessions."""
        manager = ReconnectionManager(reconnection_window=10, state_ttl=20)
        await manager.start()

        with freeze_time("2024-01-01 12:00:00") as frozen_time:
            # Register some sessions
            manager.register_disconnection("session-1", "conn-1")
            manager.register_disconnection("session-2", "conn-2")

            # Move time forward to expire first session
            frozen_time.move_to("2024-01-01 12:00:21")

            # Register a new session
            manager.register_disconnection("session-3", "conn-3")

            # Call the synchronous cleanup method
            cleaned = manager._cleanup_expired_sessions_once()

            # Verify that sessions 1 and 2 were cleaned up
            assert cleaned == 2
            assert "session-1" not in manager.disconnected_sessions
            assert "session-2" not in manager.disconnected_sessions
            assert "session-3" in manager.disconnected_sessions

        await manager.stop()

    def test_get_statistics(self):
        """Test statistics generation."""
        manager = ReconnectionManager()

        # Register some sessions
        manager.register_disconnection("session-1", "conn-1")
        manager.register_disconnection("session-2", "conn-2")
        manager.active_reconnections.add("session-1")

        stats = manager.get_statistics()

        assert stats["disconnected_sessions"] == 2
        assert stats["active_reconnections"] == 1
        assert len(stats["sessions"]) == 2

        # Check individual session stats
        session_stats = stats["sessions"][0]
        assert "session_id" in session_stats
        assert "disconnected_seconds_ago" in session_stats
        assert "reconnect_attempts" in session_stats
        assert "pending_messages" in session_stats
        assert "can_reconnect" in session_stats


class TestConnectionRecovery:
    """Test cases for ConnectionRecovery."""

    def test_calculate_backoff(self):
        """Test exponential backoff calculation."""
        recovery = ConnectionRecovery(backoff_multiplier=2.0, max_backoff=30)

        session_id = "test-session"

        # Test exponential growth
        assert recovery.calculate_backoff(session_id, 0) == 1.0
        assert recovery.calculate_backoff(session_id, 1) == 2.0
        assert recovery.calculate_backoff(session_id, 2) == 4.0
        assert recovery.calculate_backoff(session_id, 3) == 8.0
        assert recovery.calculate_backoff(session_id, 4) == 16.0

        # Test max backoff limit
        assert recovery.calculate_backoff(session_id, 10) == 30.0  # capped at max

    @pytest.mark.asyncio
    async def test_wait_before_reconnect(self):
        """Test waiting with backoff."""
        recovery = ConnectionRecovery(backoff_multiplier=2.0)

        session_id = "test-session"

        # Test that it waits the correct amount of time
        # Note: This is a simple test, in reality we'd use a mock timer
        start = datetime.now()
        await recovery.wait_before_reconnect(session_id, 1)
        elapsed = (datetime.now() - start).total_seconds()

        # Should wait approximately 2 seconds (2^1)
        assert 1.8 < elapsed < 2.2

    def test_recovery_strategy_selection(self):
        """Test recovery strategy selection based on error type."""
        recovery = ConnectionRecovery()

        session_id = "test-session"

        # Test different error types
        assert (
            recovery.should_use_recovery_strategy(session_id, "network_error")
            == "exponential_backoff"
        )
        assert (
            recovery.should_use_recovery_strategy(session_id, "server_overload")
            == "linear_backoff"
        )
        assert (
            recovery.should_use_recovery_strategy(session_id, "authentication_failed")
            == "no_retry"
        )
        assert (
            recovery.should_use_recovery_strategy(session_id, None)
            == "exponential_backoff"
        )
        assert (
            recovery.should_use_recovery_strategy(session_id, "unknown_error")
            == "exponential_backoff"
        )
