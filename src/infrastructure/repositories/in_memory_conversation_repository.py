from typing import Optional, Dict, List, Any
from asyncio import Lock

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message


class InMemoryConversationRepository:
    """Thread-safe in-memory conversation storage for MVP testing"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.lock = Lock()
        self.message_count = 0
        self.max_conversations = 1000
        self.max_messages_per_conversation = 500

    async def save(self, conversation: Conversation) -> None:
        """Save conversation with thread safety

        Args:
            conversation: The conversation entity to save
        """
        async with self.lock:
            if len(self.conversations) >= self.max_conversations:
                oldest_id = min(
                    self.conversations.keys(),
                    key=lambda k: self.conversations[k].created_at,
                )
                del self.conversations[oldest_id]

            if len(conversation.messages) > self.max_messages_per_conversation:
                conversation.messages = conversation.messages[
                    -self.max_messages_per_conversation :
                ]

            self.conversations[conversation.session_id] = conversation
            self.message_count = sum(
                len(c.messages) for c in self.conversations.values()
            )

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID

        Args:
            session_id: The session identifier

        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        async with self.lock:
            return self.conversations.get(session_id)

    async def delete(self, session_id: str) -> None:
        """Delete conversation by session ID

        Args:
            session_id: The session identifier
        """
        async with self.lock:
            if session_id in self.conversations:
                del self.conversations[session_id]

    async def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> List[Message]:
        """Get recent messages for context

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        conversation = await self.get_by_session(session_id)
        if conversation:
            return conversation.messages[-limit:] if conversation.messages else []
        return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics

        Returns:
            Dictionary with statistics
        """
        async with self.lock:
            return {
                "total_conversations": len(self.conversations),
                "total_messages": self.message_count,
                "memory_usage_estimate": self.message_count * 500,
            }
