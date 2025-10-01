"""Session management for WebSocket connections."""

import asyncio
from typing import Dict, Set


class SessionManager:
    """
    Manages session grouping for WebSocket connections.
    Single Responsibility: Session-connection mapping.
    """

    def __init__(self):
        """Initialize session manager."""
        self.session_connections: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def add_connection(self, session_id: str, connection_id: str):
        """
        Add a connection to a session.

        Args:
            session_id: Session identifier
            connection_id: Connection identifier to add
        """
        async with self._lock:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)

    async def remove_connection(self, session_id: str, connection_id: str):
        """
        Remove a connection from a session.

        Args:
            session_id: Session identifier
            connection_id: Connection identifier to remove
        """
        async with self._lock:
            if session_id in self.session_connections:
                self.session_connections[session_id].discard(connection_id)
                # Clean up empty sessions
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]

    async def get_session_connections(self, session_id: str) -> Set[str]:
        """
        Get all connections for a session.

        Args:
            session_id: Session identifier

        Returns:
            Set of connection IDs for the session
        """
        async with self._lock:
            return self.session_connections.get(session_id, set()).copy()

    async def get_connection_count(self, session_id: str) -> int:
        """
        Get number of connections for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of active connections for the session
        """
        async with self._lock:
            return len(self.session_connections.get(session_id, set()))

    async def get_all_sessions(self) -> Dict[str, int]:
        """
        Get all active sessions with connection counts.

        Returns:
            Dictionary of session IDs to connection counts
        """
        async with self._lock:
            return {
                session_id: len(connections)
                for session_id, connections in self.session_connections.items()
            }

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session has any active connections.

        Args:
            session_id: Session identifier

        Returns:
            True if session has active connections
        """
        async with self._lock:
            return session_id in self.session_connections and bool(
                self.session_connections[session_id]
            )
