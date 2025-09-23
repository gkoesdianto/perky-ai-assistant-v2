"""Behavioral tests for WebSocket session manager."""

import pytest
import asyncio
from src.presentation.websocket.session_manager import SessionManager


@pytest.mark.asyncio
class TestSessionManager:
    """Test session manager behavior."""

    async def test_add_connection_to_new_session(self):
        """Adding connection to new session should create session."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")

        assert await manager.session_exists("session-1")
        assert await manager.get_connection_count("session-1") == 1
        connections = await manager.get_session_connections("session-1")
        assert "conn-1" in connections

    async def test_add_multiple_connections_to_session(self):
        """Session should support multiple connections."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-2")
        await manager.add_connection("session-1", "conn-3")

        assert await manager.get_connection_count("session-1") == 3
        connections = await manager.get_session_connections("session-1")
        assert connections == {"conn-1", "conn-2", "conn-3"}

    async def test_remove_connection_from_session(self):
        """Removing connection should update session."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-2")

        await manager.remove_connection("session-1", "conn-1")

        assert await manager.get_connection_count("session-1") == 1
        connections = await manager.get_session_connections("session-1")
        assert connections == {"conn-2"}

    async def test_remove_last_connection_removes_session(self):
        """Removing last connection should remove empty session."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        assert await manager.session_exists("session-1")

        await manager.remove_connection("session-1", "conn-1")

        assert not await manager.session_exists("session-1")
        assert await manager.get_connection_count("session-1") == 0

    async def test_remove_nonexistent_connection_safe(self):
        """Removing non-existent connection should be safe."""
        manager = SessionManager()

        # Should not raise exceptions
        await manager.remove_connection("non-existent-session", "conn-1")
        await manager.remove_connection("session-1", "non-existent-conn")

        assert not await manager.session_exists("non-existent-session")

    async def test_sessions_are_independent(self):
        """Different sessions should be independent."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-2")
        await manager.add_connection("session-2", "conn-3")
        await manager.add_connection("session-2", "conn-4")

        assert await manager.get_connection_count("session-1") == 2
        assert await manager.get_connection_count("session-2") == 2

        connections1 = await manager.get_session_connections("session-1")
        connections2 = await manager.get_session_connections("session-2")

        assert connections1 == {"conn-1", "conn-2"}
        assert connections2 == {"conn-3", "conn-4"}

    async def test_get_all_sessions_with_counts(self):
        """Should return all active sessions with connection counts."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-2")
        await manager.add_connection("session-2", "conn-3")
        await manager.add_connection("session-3", "conn-4")
        await manager.add_connection("session-3", "conn-5")
        await manager.add_connection("session-3", "conn-6")

        all_sessions = await manager.get_all_sessions()

        assert all_sessions == {"session-1": 2, "session-2": 1, "session-3": 3}

    async def test_get_connections_returns_copy(self):
        """Getting connections should return a copy, not reference."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        connections = await manager.get_session_connections("session-1")

        # Modify the returned set
        connections.add("fake-conn")

        # Original should be unchanged
        actual_connections = await manager.get_session_connections("session-1")
        assert actual_connections == {"conn-1"}

    async def test_concurrent_operations_handled_safely(self):
        """Concurrent operations should be handled safely with locks."""
        manager = SessionManager()
        session_id = "concurrent-session"

        # Add 10 connections concurrently
        tasks = [manager.add_connection(session_id, f"conn-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

        assert await manager.get_connection_count(session_id) == 10

        # Remove 5 connections concurrently
        remove_tasks = [
            manager.remove_connection(session_id, f"conn-{i}") for i in range(5)
        ]
        await asyncio.gather(*remove_tasks)

        assert await manager.get_connection_count(session_id) == 5
        connections = await manager.get_session_connections(session_id)
        assert connections == {f"conn-{i}" for i in range(5, 10)}

    async def test_duplicate_connection_adds_are_idempotent(self):
        """Adding same connection multiple times should be idempotent."""
        manager = SessionManager()

        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-1")
        await manager.add_connection("session-1", "conn-1")

        # Should still have only one connection
        assert await manager.get_connection_count("session-1") == 1
        connections = await manager.get_session_connections("session-1")
        assert connections == {"conn-1"}
