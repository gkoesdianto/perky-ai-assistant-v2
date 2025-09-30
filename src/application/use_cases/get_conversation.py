"""Get Conversation Use Case Implementation"""

import logging
from typing import Optional

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.ports.conversation_repository_port import (
    ConversationRepositoryPort,
)
from src.application.use_cases.interfaces import GetConversationUseCase

logger = logging.getLogger(__name__)


class GetConversationUseCaseImpl(GetConversationUseCase):
    """Implementation of get conversation use case"""

    def __init__(self, conversation_repository: ConversationRepositoryPort):
        """Initialize the use case with repository dependency

        Args:
            conversation_repository: Repository for conversation operations
        """
        self.conversation_repository = conversation_repository

    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        """Get conversation history for a session

        Args:
            session_id: The session identifier

        Returns:
            Optional[ConversationDTO]: The conversation DTO if found, None otherwise
        """
        logger.info(f"Getting conversation for session: {session_id}")

        try:
            # 1. Retrieve conversation from repository
            conversation = await self.conversation_repository.get_by_session(session_id)

            # 2. Handle missing conversations gracefully
            if not conversation:
                logger.info(f"No conversation found for session: {session_id}")
                return None

            # 3. Convert messages to DTOs
            messages = [
                MessageDTO.from_entity(msg, session_id=conversation.session_id)
                for msg in conversation.messages
            ]

            # 4. Create and return ConversationDTO
            conversation_dto = ConversationDTO(
                id=conversation.id,
                session_id=conversation.session_id,
                messages=messages,
                started_at=conversation.started_at,
                last_activity=conversation.last_activity,
                metadata=conversation.metadata or {},
            )

            logger.info(
                f"Retrieved conversation {conversation.id} "
                f"with {len(messages)} messages"
            )

            return conversation_dto

        except Exception as e:
            logger.error(f"Failed to get conversation for session {session_id}: {e}")
            raise
