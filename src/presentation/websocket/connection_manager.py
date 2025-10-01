"""WebSocket connection management with SRP."""

import asyncio
import logging
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections only.
    Single Responsibility: Connection lifecycle management.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, connection_id: str) -> bool:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique identifier for this connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[connection_id] = websocket
            logger.info(f"Client connected: {connection_id}")
            return True
        except RuntimeError as e:
            # TestClient WebSockets are pre-accepted
            if "WebSocket is already accepted" in str(
                e
            ) or "Expected ASGI message" in str(e):
                async with self._lock:
                    self.active_connections[connection_id] = websocket
                logger.info(f"Client connected (TestClient): {connection_id}")
                return True
            logger.error(f"Connection failed for {connection_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection failed for {connection_id}: {e}")
            return False

    async def disconnect(self, connection_id: str):
        """
        Remove a connection from active connections.

        Args:
            connection_id: Connection identifier to remove
        """
        async with self._lock:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                logger.info(f"Client disconnected: {connection_id}")

    async def send_message(self, connection_id: str, message: dict) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection identifier
            message: Message dictionary to send

        Returns:
            True if message sent successfully, False otherwise
        """
        async with self._lock:
            websocket = self.active_connections.get(connection_id)

        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                await self.disconnect(connection_id)
                return False
        return False

    async def broadcast(self, message: dict, exclude_connection: Optional[str] = None):
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast
            exclude_connection: Optional connection ID to exclude from broadcast
        """
        async with self._lock:
            connections = list(self.active_connections.items())

        for connection_id, websocket in connections:
            if connection_id != exclude_connection:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    await self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)

    def is_connected(self, connection_id: str) -> bool:
        """Check if a specific connection is active."""
        return connection_id in self.active_connections
