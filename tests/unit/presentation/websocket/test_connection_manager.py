"""Behavioral tests for WebSocket connection manager."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.presentation.websocket.connection_manager import ConnectionManager


@pytest.mark.asyncio
class TestConnectionManager:
    """Test connection manager behavior."""

    async def test_successful_connection_adds_to_active(self):
        """Successful connection should be added to active connections."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        connection_id = "test-connection-1"

        result = await manager.connect(websocket, connection_id)

        assert result is True
        assert manager.is_connected(connection_id)
        assert manager.get_connection_count() == 1
        websocket.accept.assert_called_once()

    async def test_failed_connection_returns_false(self):
        """Failed connection should return False and not be added."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.accept.side_effect = Exception("Connection failed")
        connection_id = "test-connection-2"

        result = await manager.connect(websocket, connection_id)

        assert result is False
        assert not manager.is_connected(connection_id)
        assert manager.get_connection_count() == 0

    async def test_disconnect_removes_connection(self):
        """Disconnect should remove connection from active connections."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        connection_id = "test-connection-3"

        await manager.connect(websocket, connection_id)
        assert manager.is_connected(connection_id)

        await manager.disconnect(connection_id)
        assert not manager.is_connected(connection_id)
        assert manager.get_connection_count() == 0

    async def test_disconnect_nonexistent_connection_safe(self):
        """Disconnecting non-existent connection should be safe."""
        manager = ConnectionManager()

        # Should not raise any exceptions
        await manager.disconnect("non-existent-id")
        assert manager.get_connection_count() == 0

    async def test_send_message_to_connected_client(self):
        """Should successfully send message to connected client."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        connection_id = "test-connection-4"
        message = {"type": "test", "data": "hello"}

        await manager.connect(websocket, connection_id)
        result = await manager.send_message(connection_id, message)

        assert result is True
        websocket.send_json.assert_called_once_with(message)

    async def test_send_message_to_disconnected_client_returns_false(self):
        """Sending message to disconnected client should return False."""
        manager = ConnectionManager()
        message = {"type": "test", "data": "hello"}

        result = await manager.send_message("non-existent", message)

        assert result is False

    async def test_send_message_failure_disconnects_client(self):
        """Failed message send should disconnect the client."""
        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.send_json.side_effect = Exception("Send failed")
        connection_id = "test-connection-5"

        await manager.connect(websocket, connection_id)
        result = await manager.send_message(connection_id, {"test": "data"})

        assert result is False
        assert not manager.is_connected(connection_id)

    async def test_broadcast_sends_to_all_connections(self):
        """Broadcast should send message to all active connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, "conn-1")
        await manager.connect(ws2, "conn-2")
        await manager.connect(ws3, "conn-3")

        message = {"type": "broadcast", "data": "hello all"}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

    async def test_broadcast_excludes_specified_connection(self):
        """Broadcast should exclude specified connection."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, "conn-1")
        await manager.connect(ws2, "conn-2")
        await manager.connect(ws3, "conn-3")

        message = {"type": "broadcast", "data": "hello"}
        await manager.broadcast(message, exclude_connection="conn-2")

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()
        ws3.send_json.assert_called_once_with(message)

    async def test_broadcast_handles_send_failures_gracefully(self):
        """Broadcast should handle individual send failures gracefully."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json.side_effect = Exception("Send failed")
        ws3 = AsyncMock()

        await manager.connect(ws1, "conn-1")
        await manager.connect(ws2, "conn-2")
        await manager.connect(ws3, "conn-3")

        message = {"type": "broadcast", "data": "hello"}
        await manager.broadcast(message)

        # ws1 and ws3 should receive message
        ws1.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

        # ws2 should be disconnected
        assert not manager.is_connected("conn-2")
        assert manager.get_connection_count() == 2

    async def test_concurrent_connections_handled_safely(self):
        """Concurrent connections should be handled safely with locks."""
        manager = ConnectionManager()
        connections = []

        # Create 10 concurrent connections
        for i in range(10):
            ws = AsyncMock()
            connections.append((ws, f"conn-{i}"))

        # Connect all concurrently
        tasks = [manager.connect(ws, cid) for ws, cid in connections]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert manager.get_connection_count() == 10

        # All should be connected
        for _, cid in connections:
            assert manager.is_connected(cid)
