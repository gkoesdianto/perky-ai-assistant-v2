"""Service configuration for dependency injection - Phase 5 Track 3.

This module configures services for the enhanced DI container,
following the patterns specified in the Phase 5 integration workflow.
"""

import os
from typing import Optional

from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl

# Import application layer components
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl
from src.core.config import settings

# Import real implementations
from src.infrastructure.ai.chat_agent import ChatAgent
from src.infrastructure.mocks.container.mock_container import (
    MockInfrastructureContainer,
)
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from src.infrastructure.services.mock_product_service import MockProductService


class ServiceConfiguration:
    """Configuration and factory methods for all services."""

    @staticmethod
    def create_infrastructure_container(
        use_mocks: Optional[bool] = None,
    ) -> MockInfrastructureContainer:
        """Create infrastructure container with appropriate mode.

        Args:
            use_mocks: If True, use mock implementations.
                      If None, determine from environment.

        Returns:
            Configured infrastructure container
        """
        if use_mocks is None:
            # Determine from environment
            use_mocks = os.getenv("USE_MOCK_MODE", "false").lower() in [
                "true",
                "1",
                "yes",
            ]

        return MockInfrastructureContainer(use_mocks=use_mocks)

    @staticmethod
    def create_chat_agent(api_key: Optional[str] = None) -> ChatAgent:
        """Create chat agent with PydanticAI.

        Args:
            api_key: OpenAI API key. If not provided, uses environment.

        Returns:
            Configured ChatAgent instance
        """
        if api_key is None:
            api_key = os.getenv(
                "OPENAI_API_KEY", getattr(settings, "OPENAI_API_KEY", None)
            )

        if not api_key:
            raise ValueError("OpenAI API key is required for ChatAgent")

        return ChatAgent(api_key=api_key)

    @staticmethod
    def create_chat_orchestrator(
        container: MockInfrastructureContainer,
    ) -> ChatOrchestrator:
        """Create chat orchestrator with all dependencies.

        Args:
            container: Infrastructure container with services

        Returns:
            Configured ChatOrchestrator instance
        """
        # Create use cases
        start_session_use_case = StartChatSessionUseCaseImpl(
            session_repository=None,  # Optional for MVP
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

        # Create and return orchestrator
        return ChatOrchestrator(
            start_session_use_case=start_session_use_case,
            process_message_use_case=process_message_use_case,
            get_conversation_use_case=get_conversation_use_case,
        )

    @staticmethod
    def create_mock_product_service() -> MockProductService:
        """Create mock product service with realistic steel data.

        Returns:
            Configured MockProductService instance
        """
        return MockProductService()

    @staticmethod
    def create_in_memory_conversation_repository() -> InMemoryConversationRepository:
        """Create in-memory conversation repository.

        Returns:
            Configured InMemoryConversationRepository instance
        """
        return InMemoryConversationRepository()


# Global service configuration instance
service_config = ServiceConfiguration()


def configure_services_for_mode(
    use_mocks: Optional[bool] = None,
) -> MockInfrastructureContainer:
    """Configure all services based on the specified mode.

    This is the main entry point for service configuration,
    following the Track 3 specification from Phase 5.

    Args:
        use_mocks: If True, use mock implementations.
                  If None, determine from environment.

    Returns:
        Configured infrastructure container with all services

    Example:
        >>> # For testing with mocks
        >>> container = configure_services_for_mode(use_mocks=True)
        >>>
        >>> # For production with real implementations
        >>> container = configure_services_for_mode(use_mocks=False)
        >>>
        >>> # Auto-detect from environment
        >>> container = configure_services_for_mode()
    """
    return service_config.create_infrastructure_container(use_mocks=use_mocks)
