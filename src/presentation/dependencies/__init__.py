"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl
from src.infrastructure.container import InfrastructureContainer


async def get_chat_orchestrator() -> AsyncGenerator[ChatOrchestrator, None]:
    """
    Get ChatOrchestrator with injected dependencies.

    Yields:
        ChatOrchestrator instance with all dependencies
    """
    container = InfrastructureContainer.instance()

    # Note: session_repository is optional for MVP (sessions stored in Redis)
    start_session_use_case = StartChatSessionUseCaseImpl(
        session_repository=None,  # Not used in MVP, sessions go directly to Redis
        redis_client=container.redis_client,
    )

    process_message_use_case = ProcessUserMessageUseCaseImpl(
        chat_agent=container.ai_agent,
        product_service=container.product_service,
        conversation_repository=container.conversation_repository,
    )

    get_conversation_use_case = GetConversationUseCaseImpl(
        conversation_repository=container.conversation_repository
    )

    orchestrator = ChatOrchestrator(
        start_session_use_case=start_session_use_case,
        process_message_use_case=process_message_use_case,
        get_conversation_use_case=get_conversation_use_case,
    )

    yield orchestrator
