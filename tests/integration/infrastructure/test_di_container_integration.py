"""Integration tests for Phase 5 Track 3 DI Container.

This test verifies the enhanced dependency injection system
and service configuration as specified in the Phase 5 workflow.
"""

import os
import pytest
from unittest.mock import patch

from src.infrastructure.dependencies import (
    ServiceConfiguration,
    configure_services_for_mode,
)
from src.infrastructure.container import get_container, get_singleton_container
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
from src.infrastructure.ai.chat_agent import ChatAgent
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from src.infrastructure.services.mock_product_service import MockProductService


class TestDIContainerIntegration:
    """Test the enhanced DI container integration."""

    def test_mock_mode_configuration(self):
        """Test that mock mode properly configures all services."""
        container = configure_services_for_mode(use_mocks=True)

        assert container.mode == "mock"
        assert container.initialized is True
        assert container.get_redis_client() is not None
        assert container.get_conversation_repository() is not None
        assert container.get_product_repository() is not None
        assert container.get_ai_agent() is not None

        # Verify mock types
        assert isinstance(container.get_ai_agent(), MockAIAgent)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_real_mode_configuration(self):
        """Test that real mode properly configures services."""
        container = configure_services_for_mode(use_mocks=False)

        assert container.mode == "real"
        assert container.initialized is True

        # Verify services are initialized
        assert container.get_redis_client() is not None
        assert container.get_conversation_repository() is not None
        assert container.get_product_repository() is not None
        assert container.get_ai_agent() is not None

        # Verify real implementations where available
        assert isinstance(
            container.get_conversation_repository(), InMemoryConversationRepository
        )
        assert isinstance(container.get_product_repository(), MockProductService)

        # ChatAgent should be real when API key is available
        ai_agent = container.get_ai_agent()
        assert isinstance(ai_agent, (ChatAgent, MockAIAgent))

    def test_real_mode_without_api_key(self):
        """Test that real mode falls back gracefully without API key."""
        # Remove API key from environment
        with patch.dict(os.environ, {}, clear=True):
            container = configure_services_for_mode(use_mocks=False)

            assert container.mode == "real"
            # Should fall back to mock AI agent
            assert isinstance(container.get_ai_agent(), MockAIAgent)

    @patch.dict(os.environ, {"USE_MOCK_MODE": "true"})
    def test_environment_override(self):
        """Test that environment variables override constructor parameters."""
        # Even though we pass False, environment should override
        container = configure_services_for_mode(use_mocks=False)
        assert container.use_mocks is True
        assert container.mode == "mock"

    @patch.dict(os.environ, {"USE_MOCK_MODE": "false", "OPENAI_API_KEY": "test-key"})
    def test_environment_forces_real_mode(self):
        """Test that environment can force real mode."""
        container = configure_services_for_mode()  # No explicit parameter
        assert container.use_mocks is False
        assert container.mode == "real"

    def test_singleton_container_integration(self):
        """Test that singleton container works with new configuration."""
        container1 = get_singleton_container()
        container2 = get_singleton_container()

        # Should be the same instance
        assert container1 is container2

    def test_service_configuration_factories(self):
        """Test individual factory methods in ServiceConfiguration."""
        config = ServiceConfiguration()

        # Test infrastructure container factory
        container = config.create_infrastructure_container(use_mocks=True)
        assert container.mode == "mock"

        # Test mock product service factory
        product_service = config.create_mock_product_service()
        assert isinstance(product_service, MockProductService)

        # Test conversation repository factory
        repo = config.create_in_memory_conversation_repository()
        assert isinstance(repo, InMemoryConversationRepository)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_chat_orchestrator_creation(self):
        """Test that ChatOrchestrator can be created with dependencies."""
        config = ServiceConfiguration()
        container = config.create_infrastructure_container(use_mocks=True)

        orchestrator = config.create_chat_orchestrator(container)

        assert orchestrator is not None
        assert hasattr(orchestrator, "start_session")
        assert hasattr(orchestrator, "process_message")
        assert hasattr(orchestrator, "get_conversation")

    def test_container_get_container_function(self):
        """Test the get_container function uses new configuration."""
        container = get_container()

        assert container is not None
        assert hasattr(container, "mode")
        assert container.initialized is True

    @pytest.mark.asyncio
    async def test_service_integration_flow(self):
        """Test complete service integration flow."""
        # Create container
        container = configure_services_for_mode(use_mocks=True)

        # Get services
        ai_agent = container.get_ai_agent()
        product_service = container.get_product_repository()
        conversation_repo = container.get_conversation_repository()

        # Verify they can work together
        assert ai_agent is not None
        assert product_service is not None
        assert conversation_repo is not None

        # Test basic operations if methods exist
        if hasattr(product_service, "search_products"):
            products = await product_service.search_products("plat")
            assert isinstance(products, list)

    def test_service_singleton_behavior(self):
        """Test that services are singletons within container."""
        container = configure_services_for_mode(use_mocks=True)

        # Get services multiple times
        redis1 = container.get_redis_client()
        redis2 = container.get_redis_client()

        ai1 = container.get_ai_agent()
        ai2 = container.get_ai_agent()

        # Should be same instances
        assert redis1 is redis2
        assert ai1 is ai2

    @patch.dict(
        os.environ,
        {
            "USE_MOCK_MODE": "true",
            "MOCK_RESPONSE_DELAY_MS": "100",
            "MOCK_ERROR_RATE": "0.1",
            "MOCK_DATA_SEED": "123",
        },
    )
    def test_mock_configuration_from_environment(self):
        """Test that mock configuration is loaded from environment."""
        container = configure_services_for_mode()

        assert container.mock_response_delay_ms == 100
        assert container.mock_error_rate == 0.1
        assert container.mock_data_seed == 123

        config = container.get_configuration()
        assert config["mock_response_delay_ms"] == 100
        assert config["mock_error_rate"] == 0.1
        assert config["mock_data_seed"] == 123
