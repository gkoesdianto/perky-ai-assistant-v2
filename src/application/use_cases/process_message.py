import logging
from typing import Any, Dict, Optional

from src.application.dto.message_dto import MessageDTO
from src.application.use_cases.interfaces import ProcessUserMessageUseCase
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message

logger = logging.getLogger(__name__)


class ProcessUserMessageUseCaseImpl(ProcessUserMessageUseCase):
    """Implementation of process user message use case with single agent"""

    def __init__(
        self,
        chat_agent,
        product_service,
        conversation_repository,
    ):
        self.chat_agent = chat_agent
        self.product_service = product_service
        self.conversation_repository = conversation_repository

    async def execute(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageDTO:
        """Process user message with single agent

        Args:
            session_id: The session identifier
            content: The user's message content
            metadata: Optional metadata for the message

        Returns:
            MessageDTO: The AI agent's response message
        """
        try:
            # 1. Get or create conversation
            conversation = await self.conversation_repository.get_by_session(session_id)
            if not conversation:
                conversation = Conversation(
                    session_id=session_id,
                    metadata=metadata or {},
                )

            # 2. Prepare conversation context BEFORE adding new message
            # (last 4 messages = 2 exchanges)
            context = {
                "conversation_history": [
                    {"sender": msg.sender_type, "content": msg.content}
                    for msg in conversation.get_context(limit=4)
                ],
                "session_id": session_id,
            }

            # 3. Create user message entity
            user_message = Message(
                conversation_id=conversation.id,
                sender_type="user",
                content=content,
                metadata=metadata or {},
            )

            # 4. Generate AI response using single agent with tools
            # The chat_agent can be either a PydanticAI agent or
            # AIAgentPort implementation
            if hasattr(self.chat_agent, "run"):
                # PydanticAI agent pattern
                response_content = await self.chat_agent.run(
                    message=content, conversation_context=context
                )
            else:
                # AIAgentPort pattern (for testing/mocking)
                # Convert existing messages (before adding new one) to DTOs for context
                message_dtos = [
                    MessageDTO(
                        content=msg.content,
                        sender_type=msg.sender_type,
                        session_id=session_id,
                        conversation_id=conversation.id,
                        timestamp=msg.created_at,
                        metadata=msg.metadata,
                    )
                    for msg in conversation.get_context(limit=4)
                    # Use same limit as PydanticAI pattern
                ]
                response_content = await self.chat_agent.generate_response(
                    message=content,
                    conversation_context=message_dtos if message_dtos else None,
                )

            # 5. NOW add the user message to conversation after getting context
            conversation.add_message(user_message)

            # 6. Create AI response message
            ai_message = Message(
                conversation_id=conversation.id,
                sender_type="ai_agent",
                content=response_content,
                metadata={
                    "model": "gpt-4o-mini",
                    "context_used": len(context["conversation_history"]),
                },
            )
            conversation.add_message(ai_message)

            # 7. Save conversation with both messages
            await self.conversation_repository.save(conversation)

            # 8. Return AI message as DTO
            # Note: We need to pass session_id separately since Message doesn't have it
            return MessageDTO(
                content=ai_message.content,
                sender_type=ai_message.sender_type,
                session_id=session_id,
                conversation_id=ai_message.conversation_id,
                timestamp=ai_message.created_at,
                metadata=ai_message.metadata,
            )

        except Exception as e:
            logger.error(f"Failed to process user message: {e}", exc_info=True)
            # Return error message in Indonesian as per requirements
            error_message = Message(
                conversation_id=conversation.id if conversation else "",
                sender_type="ai_agent",
                content=(
                    "Maaf, terjadi kesalahan dalam memproses pesan Anda. "
                    "Silakan coba lagi."
                ),
                metadata={"error": str(e), "error_type": type(e).__name__},
            )

            return MessageDTO(
                content=error_message.content,
                sender_type=error_message.sender_type,
                session_id=session_id,
                conversation_id=error_message.conversation_id,
                timestamp=error_message.created_at,
                metadata=error_message.metadata,
            )
