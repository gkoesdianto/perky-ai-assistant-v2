"""Chat Orchestrator Service

This service orchestrates chat operations across use cases,
providing a single entry point for the presentation layer.
"""

import logging
from typing import Any, Dict, Optional

import logfire

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.session_dto import SessionDTO
from src.application.use_cases.interfaces import (
    GetConversationUseCase,
    ProcessUserMessageUseCase,
    StartChatSessionUseCase,
)

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """Orchestrates chat operations across use cases"""

    def __init__(
        self,
        start_session_use_case: StartChatSessionUseCase,
        process_message_use_case: ProcessUserMessageUseCase,
        get_conversation_use_case: GetConversationUseCase,
    ):
        """Initialize the orchestrator with use case dependencies

        Args:
            start_session_use_case: Use case for starting chat sessions
            process_message_use_case: Use case for processing messages
            get_conversation_use_case: Use case for retrieving conversations
        """
        self.start_session = start_session_use_case
        self.process_message = process_message_use_case
        self.get_conversation = get_conversation_use_case

    async def handle_new_connection(
        self,
        session_id: str,
        metadata: Dict[str, Any],
    ) -> SessionDTO:
        """Handle new WebSocket connection

        Args:
            session_id: Unique session identifier
            metadata: Connection metadata (user agent, origin, etc.)

        Returns:
            SessionDTO: The created or existing session

        Raises:
            Exception: If session creation fails
        """
        with logfire.span(
            "chat_orchestrator.handle_new_connection",
            session_id=session_id,
        ):
            logger.info(f"New connection: {session_id}")

            try:
                session = await self.start_session.execute(session_id, metadata)
                logfire.info(
                    "Session started successfully",
                    session_id=session.session_id,
                    is_active=session.is_active,
                )
                logger.info(
                    f"Session started: {session.session_id} at {session.started_at}"
                )
                return session
            except Exception as e:
                logfire.error(
                    "Session creation failed", session_id=session_id, error=str(e)
                )
                logger.error(f"Failed to start session: {e}", exc_info=True)
                raise

    async def handle_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageDTO:
        """Handle incoming user message

        Args:
            session_id: The session identifier
            content: The message content from the user
            metadata: Optional message metadata

        Returns:
            MessageDTO: The AI response message
        """
        with logfire.span(
            "chat_orchestrator.handle_user_message",
            session_id=session_id,
            message_length=len(content),
        ):
            logger.info(f"Processing message from session {session_id}")
            logger.debug(f"Message content: {content[:100]}...")  # Log first 100 chars

            try:
                with logfire.span("chat_orchestrator.process_message_use_case"):
                    response = await self.process_message.execute(
                        session_id=session_id,
                        content=content,
                        metadata=metadata,
                    )

                logfire.info(
                    "Message processed successfully",
                    session_id=session_id,
                    response_length=len(response.content) if response.content else 0,
                    sender_type=response.sender_type,
                )

                logger.info(
                    f"Response generated for session {session_id}, "
                    f"sender: {response.sender_type}"
                )
                return response

            except Exception as e:
                logfire.error(
                    "Message processing failed",
                    session_id=session_id,
                    error=str(e),
                )
                logger.error(
                    f"Failed to process message for session {session_id}: {e}",
                    exc_info=True,
                )
                # Return error message in Indonesian as per requirements
                return MessageDTO(
                    content="Maaf, terjadi kesalahan. Silakan coba lagi.",
                    sender_type="ai_agent",
                    session_id=session_id,
                    conversation_id=None,
                    timestamp=None,
                    metadata={"error": str(e), "error_type": "orchestration_error"},
                )

    async def get_conversation_history(
        self, session_id: str
    ) -> Optional[ConversationDTO]:
        """Get conversation history for session

        Args:
            session_id: The session identifier

        Returns:
            Optional[ConversationDTO]: The conversation if found, None otherwise
        """
        with logfire.span(
            "chat_orchestrator.get_conversation_history",
            session_id=session_id,
        ):
            try:
                logger.info(f"Retrieving conversation history for session {session_id}")
                conversation = await self.get_conversation.execute(session_id)

                if conversation:
                    logfire.info(
                        "Conversation retrieved",
                        session_id=session_id,
                        message_count=len(conversation.messages),
                    )
                    logger.info(
                        f"Retrieved conversation with "
                        f"{len(conversation.messages)} messages"
                    )
                else:
                    logfire.info("No conversation found", session_id=session_id)
                    logger.info(f"No conversation found for session {session_id}")

                return conversation

            except Exception as e:
                logfire.error(
                    "Failed to retrieve conversation",
                    session_id=session_id,
                    error=str(e),
                )
                logger.error(
                    f"Failed to get conversation for session {session_id}: {e}",
                    exc_info=True,
                )
                return None

    async def handle_session_end(self, session_id: str) -> None:
        """Handle session end/disconnect

        This method can be extended to perform cleanup operations
        when a session ends (user disconnects).

        Args:
            session_id: The session identifier
        """
        logger.info(f"Session ended: {session_id}")
        # TODO: Future implementation could include:
        # - Marking session as inactive in Redis
        # - Saving conversation to database
        # - Cleanup of temporary resources
        # - Analytics tracking
