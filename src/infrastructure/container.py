"""
Infrastructure dependency injection container.

This module provides a unified container supporting both mock and real
implementations, enabling easy mode switching for testing and production.
"""

import os
from typing import Any, Optional


class InfrastructureContainer:
    """
    Dependency injection container supporting mock and real implementations.

    The container uses a singleton pattern to ensure consistent dependency
    instances across the application. Mode (mock vs real) can be configured
    via environment variable or explicit parameter.

    Usage:
        # Get singleton instance
        container = InfrastructureContainer.instance()

        # Access dependencies via properties
        agent = container.ai_agent
        products = container.product_service

        # Reset singleton (for testing)
        InfrastructureContainer.reset()

    Environment Variables:
        USE_MOCK_MODE: "true"/"1"/"yes" for mocks, "false"/"0"/"no" for real
        OPENAI_API_KEY: Required for real ChatAgent implementation
    """

    _instance: Optional["InfrastructureContainer"] = None

    # Private attributes for dependency instances
    _redis_client: Any
    _session_repository: Any
    _conversation_repository: Any
    _product_repository: Any
    _query_analyzer: Any
    _ai_agent: Any

    # === Singleton Pattern ===

    @classmethod
    def instance(cls, use_mocks: Optional[bool] = None) -> "InfrastructureContainer":
        """
        Get or create singleton container instance.

        Args:
            use_mocks: Override mode detection. If None, uses environment.

        Returns:
            Singleton container instance

        Example:
            >>> container = InfrastructureContainer.instance()
            >>> container.ai_agent
            <ChatAgent or MockAIAgent>
        """
        if cls._instance is None:
            cls._instance = cls(use_mocks=use_mocks)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset singleton instance.

        This should be called between tests to ensure clean state.

        Example:
            >>> InfrastructureContainer.reset()
            >>> # Next instance() call creates new container
        """
        cls._instance = None

    # === Initialization ===

    def __init__(self, use_mocks: Optional[bool] = None):
        """
        Initialize container with dependencies.

        Args:
            use_mocks: If True, use mock implementations.
                      If None, auto-detect from environment.
        """
        self.mode = self._detect_mode(use_mocks)
        self._setup_dependencies()
        self.initialized = True

    def _detect_mode(self, use_mocks: Optional[bool]) -> str:
        """
        Detect which mode to use (mock or real).

        Args:
            use_mocks: Explicit mode override

        Returns:
            "mock" or "real"
        """
        if use_mocks is not None:
            return "mock" if use_mocks else "real"

        # Check environment variable
        env_value = os.getenv("USE_MOCK_MODE", "false").lower()
        return "mock" if env_value in ["true", "1", "yes"] else "real"

    def _setup_dependencies(self) -> None:
        """Setup all dependencies based on mode."""
        if self.mode == "mock":
            self._setup_mocks()
        else:
            self._setup_real()

    # === Setup Methods ===

    def _setup_mocks(self) -> None:
        """Initialize all mock implementations."""
        from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
        from src.infrastructure.mocks.mock_conversation_repository import (
            MockConversationRepository,
        )
        from src.infrastructure.mocks.mock_product_repository import (
            MockProductRepository,
        )
        from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
        from src.infrastructure.mocks.mock_redis_client import MockRedisClient
        from src.infrastructure.mocks.mock_session_repository import (
            MockSessionRepository,
        )

        self._redis_client = MockRedisClient()
        self._session_repository = MockSessionRepository()
        self._conversation_repository = MockConversationRepository()
        self._product_repository = MockProductRepository()
        self._query_analyzer = MockQueryAnalyzer()
        self._ai_agent = MockAIAgent()

    def _setup_real(self) -> None:
        """Initialize real implementations (MVP: some still use mocks)."""
        from src.infrastructure.ai.chat_agent import ChatAgent
        from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
        from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
        from src.infrastructure.mocks.mock_redis_client import MockRedisClient
        from src.infrastructure.mocks.mock_session_repository import (
            MockSessionRepository,
        )
        from src.infrastructure.repositories.in_memory_conversation_repository import (
            InMemoryConversationRepository,
        )
        from src.infrastructure.services.mock_product_service import MockProductService

        # Redis client - MVP uses mock with Redis-like behavior
        self._redis_client = MockRedisClient()

        # Session repository - MVP uses mock
        self._session_repository = MockSessionRepository()

        # Conversation repository - use in-memory implementation
        self._conversation_repository = InMemoryConversationRepository()

        # Product service - mock with realistic data
        self._product_repository = MockProductService()

        # Query analyzer - MVP uses mock
        self._query_analyzer = MockQueryAnalyzer()

        # AI agent - use real PydanticAI implementation
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._ai_agent = ChatAgent(api_key=api_key)
            else:
                print("Warning: No OPENAI_API_KEY, using mock AI agent")
                self._ai_agent = MockAIAgent()
        except Exception as e:
            print(f"Warning: Failed to initialize ChatAgent: {e}")
            self._ai_agent = MockAIAgent()

    # === Property Accessors ===

    @property
    def redis_client(self):
        """Get Redis client instance."""
        return self._redis_client

    @property
    def session_repository(self):
        """Get session repository instance."""
        return self._session_repository

    @property
    def conversation_repository(self):
        """Get conversation repository instance."""
        return self._conversation_repository

    @property
    def product_service(self):
        """Get product service instance (alias for product_repository)."""
        return self._product_repository

    @property
    def ai_agent(self):
        """Get AI agent instance."""
        return self._ai_agent

    @property
    def query_analyzer(self):
        """Get query analyzer instance."""
        return self._query_analyzer

    # === Configuration ===

    def get_configuration(self) -> dict:
        """
        Get current container configuration for debugging.

        Returns:
            Configuration dictionary with mode and settings
        """
        return {
            "mode": self.mode,
            "initialized": self.initialized,
            "components": {
                "redis_client": type(self._redis_client).__name__,
                "session_repository": type(self._session_repository).__name__,
                "conversation_repository": type(self._conversation_repository).__name__,
                "product_repository": type(self._product_repository).__name__,
                "query_analyzer": type(self._query_analyzer).__name__,
                "ai_agent": type(self._ai_agent).__name__,
            },
        }


# Convenience functions for backward compatibility
def get_singleton_container() -> InfrastructureContainer:
    """
    Get singleton container instance.

    Returns:
        Shared infrastructure container instance
    """
    return InfrastructureContainer.instance()


def reset_singleton_container() -> None:
    """
    Reset the singleton container instance.

    This should be called between tests to ensure clean state.
    """
    InfrastructureContainer.reset()
