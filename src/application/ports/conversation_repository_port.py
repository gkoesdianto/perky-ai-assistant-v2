from typing import Optional, Protocol

from src.domain.entities.conversation import Conversation


class ConversationRepositoryPort(Protocol):
    """Port for conversation repository operations"""

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID

        Args:
            session_id: The session identifier

        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        ...

    async def save(self, conversation: Conversation) -> None:
        """Save or update a conversation

        Args:
            conversation: The conversation entity to save
        """
        ...

    async def delete(self, session_id: str) -> None:
        """Delete a conversation by session ID

        Args:
            session_id: The session identifier
        """
        ...
