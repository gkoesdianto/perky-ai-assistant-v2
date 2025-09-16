from typing import Optional, Dict

from src.domain.entities.conversation import Conversation


class InMemoryConversationRepository:
    """In-memory conversation storage for MVP testing"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID

        Args:
            session_id: The session identifier

        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        return self.conversations.get(session_id)

    async def save(self, conversation: Conversation) -> None:
        """Save or update a conversation

        Args:
            conversation: The conversation entity to save
        """
        self.conversations[conversation.session_id] = conversation

    async def delete(self, session_id: str) -> None:
        """Delete a conversation by session ID

        Args:
            session_id: The session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
