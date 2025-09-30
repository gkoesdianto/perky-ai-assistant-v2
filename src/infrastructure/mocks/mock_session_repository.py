"""Mock Session Repository implementation."""

from datetime import datetime
from typing import Dict, Optional

from src.domain.entities.session import Session


class MockSessionRepository:
    """Mock implementation of SessionRepository for MVP phase.

    Note: For MVP, sessions are primarily managed in Redis.
    This mock repository is a placeholder for future database-backed implementation.
    """

    def __init__(self):
        """Initialize the mock repository."""
        self.sessions: Dict[str, Session] = {}

    async def create(self, session: Session) -> Session:
        """
        Create a new session.

        Args:
            session: Session entity to create

        Returns:
            Created session entity
        """
        self.sessions[session.session_id] = session
        return session

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        return self.sessions.get(session_id)

    async def update(self, session: Session) -> Session:
        """
        Update an existing session.

        Args:
            session: Session entity with updates

        Returns:
            Updated session entity
        """
        if session.session_id in self.sessions:
            self.sessions[session.session_id] = session
        return session

    async def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def get_or_create(self, session_id: str) -> Session:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Session identifier

        Returns:
            Existing or newly created session
        """
        session = self.sessions.get(session_id)
        if not session:
            session = Session(
                session_id=session_id, started_at=datetime.now(), is_active=True
            )
            self.sessions[session_id] = session
        return session
