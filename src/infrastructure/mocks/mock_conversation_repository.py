"""Mock Conversation Repository implementation for MVP testing

This module provides an in-memory conversation repository with
thread-safe operations and automatic cleanup of expired conversations,
following the Phase 3 Mock Infrastructure Implementation Specification.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from src.application.ports.conversation_repository_port import (
    ConversationRepositoryPort,
)
from src.domain.entities.conversation import Conversation


class MockConversationRepository(ConversationRepositoryPort):
    """
    In-memory conversation storage with thread-safe operations
    Implements domain ConversationRepository interface for MVP

    Features:
    - Thread-safe operations using asyncio.Lock
    - In-memory Dict storage for conversations
    - Automatic cleanup of expired conversations
    - No persistence (memory-only for MVP)
    """

    def __init__(self):
        """Initialize the mock conversation repository"""
        self.conversations: Dict[str, Conversation] = {}
        self._lock = asyncio.Lock()  # Thread safety for concurrent operations

    async def save(self, conversation: Conversation) -> None:
        """Save or update a conversation

        Thread-safe operation to store or update a conversation in memory.

        Args:
            conversation: The conversation entity to save
        """
        async with self._lock:
            self.conversations[conversation.session_id] = conversation

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID

        Thread-safe retrieval of a conversation by its session ID.

        Args:
            session_id: The session identifier

        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        async with self._lock:
            return self.conversations.get(session_id)

    async def delete(self, session_id: str) -> None:
        """Delete a conversation by session ID

        Thread-safe removal of a conversation from memory.

        Args:
            session_id: The session identifier
        """
        async with self._lock:
            self.conversations.pop(session_id, None)

    async def cleanup_expired(self, hours: int = 1) -> None:
        """Remove inactive conversations older than specified hours

        This optional method cleans up stale conversations to prevent memory leaks
        during long-running sessions. It removes conversations where the last_activity
        timestamp is older than the specified number of hours.

        Args:
            hours: Number of hours after which a conversation is considered expired
                  (default: 1 hour)
        """
        async with self._lock:
            current_time = datetime.now(timezone.utc)
            expiry_threshold = current_time - timedelta(hours=hours)

            # Find expired session IDs
            expired_sessions = [
                session_id
                for session_id, conversation in self.conversations.items()
                if conversation.last_activity < expiry_threshold
            ]

            # Remove expired conversations
            for session_id in expired_sessions:
                del self.conversations[session_id]
