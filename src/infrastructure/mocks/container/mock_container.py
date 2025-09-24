"""
Mock Infrastructure Container for dependency injection.
Enables easy switching between mock and real implementations via environment flags.
"""

import os
from dataclasses import dataclass

from src.infrastructure.mocks.mock_redis_client import MockRedisClient
from src.infrastructure.mocks.mock_conversation_repository import (
    MockConversationRepository,
)
from src.infrastructure.mocks.mock_session_repository import MockSessionRepository
from src.infrastructure.mocks.mock_product_repository import MockProductRepository
from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

# Real implementation imports for Phase 5
from src.infrastructure.ai.chat_agent import ChatAgent
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository
)
from src.infrastructure.services.mock_product_service import MockProductService


@dataclass
class MockInfrastructureContainer:
    """
    Dependency container for mock implementations.
    Enables easy switching between mock and real implementations via environment flags.

    This container centralizes the creation and configuration of all mock
    infrastructure components, making it easy to switch between mock and real
    implementations for different environments (development, testing, production).
    """

    def __init__(self, use_mocks: bool = True):
        """
        Initialize container with mock or real implementations.

        Args:
            use_mocks: If True, use mock implementations.
                      Can be overridden by USE_MOCK_MODE env var.
        """
        # Check environment override
        env_use_mocks = os.getenv("USE_MOCK_MODE", "").lower()
        if env_use_mocks in ["true", "1", "yes"]:
            self.use_mocks = True
        elif env_use_mocks in ["false", "0", "no"]:
            self.use_mocks = False
        else:
            self.use_mocks = use_mocks

        # Configuration from environment
        self.mock_response_delay_ms = int(os.getenv("MOCK_RESPONSE_DELAY_MS", "0"))
        self.mock_error_rate = float(os.getenv("MOCK_ERROR_RATE", "0.0"))
        self.mock_data_seed = int(os.getenv("MOCK_DATA_SEED", "42"))

        # Initialize components based on mode
        if self.use_mocks:
            self._setup_mocks()
        else:
            self._setup_real_implementations()

    def _setup_mocks(self):
        """Register all mock implementations."""
        # Initialize mock components
        self.redis_client = MockRedisClient()
        self.session_repo = MockSessionRepository()
        self.conversation_repo = MockConversationRepository()
        self.product_repo = MockProductRepository()
        self.query_analyzer = MockQueryAnalyzer()
        self.ai_agent = MockAIAgent()

        # Store initialization state
        self.initialized = True
        self.mode = "mock"

    def _setup_real_implementations(self):
        """
        Register real implementations for Phase 5 integration.
        """
        # Real implementations (Phase 5 Track 3)
        # Note: Some still use mock/in-memory for MVP simplicity

        # Redis client - for MVP, use mock with Redis-like behavior
        self.redis_client = MockRedisClient()

        # Session repository - still using mock for MVP
        self.session_repo = MockSessionRepository()

        # Conversation repository - use in-memory implementation
        self.conversation_repo = InMemoryConversationRepository()

        # Product service - using mock with realistic data
        self.product_repo = MockProductService()

        # Query analyzer - still using mock for MVP
        self.query_analyzer = MockQueryAnalyzer()

        # AI agent - use real PydanticAI implementation
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.ai_agent = ChatAgent(api_key=api_key)
            else:
                # Fallback to mock if no API key
                print("Warning: No OPENAI_API_KEY found, using mock AI agent")
                self.ai_agent = MockAIAgent()
        except Exception as e:
            # Fallback to mock on any error
            print(f"Warning: Failed to initialize real ChatAgent: {e}")
            self.ai_agent = MockAIAgent()

        # Store initialization state
        self.initialized = True
        self.mode = "real"

    def get_redis_client(self):
        """
        Get Redis client instance.

        Returns:
            Redis client (mock or real based on configuration)
        """
        return self.redis_client

    def get_session_repository(self):
        """
        Get session repository instance.

        Returns:
            Session repository (mock or real based on configuration)
        """
        return self.session_repo

    def get_conversation_repository(self):
        """
        Get conversation repository instance.

        Returns:
            Conversation repository (mock or real based on configuration)
        """
        return self.conversation_repo

    def get_product_repository(self):
        """
        Get product repository instance.

        Returns:
            Product repository (mock or real based on configuration)
        """
        return self.product_repo

    def get_query_analyzer(self):
        """
        Get query analyzer instance.

        Returns:
            Query analyzer (mock or real based on configuration)
        """
        return self.query_analyzer

    def get_ai_agent(self):
        """
        Get AI agent instance.

        Returns:
            AI agent (mock or real based on configuration)
        """
        return self.ai_agent

    def get_configuration(self):
        """
        Get current container configuration for debugging and logging.

        Returns:
            Dictionary with current configuration settings
        """
        return {
            "mode": self.mode,
            "use_mocks": self.use_mocks,
            "mock_response_delay_ms": self.mock_response_delay_ms,
            "mock_error_rate": self.mock_error_rate,
            "mock_data_seed": self.mock_data_seed,
            "initialized": self.initialized,
        }
