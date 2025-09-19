"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl
from src.infrastructure.container import get_singleton_container


async def get_chat_orchestrator() -> AsyncGenerator[ChatOrchestrator, None]:
    """
    Get ChatOrchestrator with injected dependencies.

    Yields:
        ChatOrchestrator instance with all dependencies
    """
    container = get_singleton_container()

    # Note: session_repository is optional for MVP (sessions stored in Redis)
    start_session_use_case = StartChatSessionUseCaseImpl(
        session_repository=None,  # Not used in MVP, sessions go directly to Redis
        redis_client=container.get_redis_client(),
    )

    process_message_use_case = ProcessUserMessageUseCaseImpl(
        chat_agent=container.get_ai_agent(),
        product_service=container.get_product_repository(),
        conversation_repository=container.get_conversation_repository(),
    )

    get_conversation_use_case = GetConversationUseCaseImpl(
        conversation_repository=container.get_conversation_repository()
    )

    orchestrator = ChatOrchestrator(
        start_session_use_case=start_session_use_case,
        process_message_use_case=process_message_use_case,
        get_conversation_use_case=get_conversation_use_case,
    )

    yield orchestrator
