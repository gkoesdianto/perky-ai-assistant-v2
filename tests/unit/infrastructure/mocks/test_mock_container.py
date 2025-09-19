"""Unit tests for MockInfrastructureContainer."""

import os
import pytest
from unittest.mock import patch

from src.infrastructure.mocks.container.mock_container import MockInfrastructureContainer
from src.infrastructure.mocks.mock_redis_client import MockRedisClient
from src.infrastructure.mocks.mock_conversation_repository import MockConversationRepository
from src.infrastructure.mocks.mock_product_repository import MockProductRepository
from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent


class TestMockInfrastructureContainer:
    """Test suite for MockInfrastructureContainer."""

    def test_mock_container_initialization(self):
        """Test that container initializes with mock implementations."""
        container = MockInfrastructureContainer(use_mocks=True)

        assert container.mode == "mock"
        assert container.use_mocks is True
        assert container.initialized is True

        # Verify all mock services are initialized
        assert container.get_redis_client() is not None
        assert container.get_conversation_repository() is not None
        assert container.get_product_repository() is not None
        assert container.get_query_analyzer() is not None
        assert container.get_ai_agent() is not None

    def test_mock_container_service_types(self):
        """Test that container returns correct mock service types."""
        container = MockInfrastructureContainer(use_mocks=True)

        assert isinstance(container.get_redis_client(), MockRedisClient)
        assert isinstance(container.get_conversation_repository(), MockConversationRepository)
        assert isinstance(container.get_product_repository(), MockProductRepository)
        assert isinstance(container.get_query_analyzer(), MockQueryAnalyzer)
        assert isinstance(container.get_ai_agent(), MockAIAgent)

    @patch.dict(os.environ, {"USE_MOCK_MODE": "true"})
    def test_environment_override_to_true(self):
        """Test that USE_MOCK_MODE=true overrides constructor parameter."""
        container = MockInfrastructureContainer(use_mocks=False)
        assert container.use_mocks is True
        assert container.mode == "mock"

    @patch.dict(os.environ, {"USE_MOCK_MODE": "false"})
    def test_environment_override_to_false(self):
        """Test that USE_MOCK_MODE=false overrides constructor parameter."""
        with pytest.raises(NotImplementedError) as exc_info:
            MockInfrastructureContainer(use_mocks=True)

        assert "Real implementations not yet available" in str(exc_info.value)

    @patch.dict(os.environ, {"USE_MOCK_MODE": "yes"})
    def test_environment_override_yes(self):
        """Test that USE_MOCK_MODE=yes is recognized."""
        container = MockInfrastructureContainer(use_mocks=False)
        assert container.use_mocks is True

    @patch.dict(os.environ, {"USE_MOCK_MODE": "1"})
    def test_environment_override_numeric(self):
        """Test that USE_MOCK_MODE=1 is recognized."""
        container = MockInfrastructureContainer(use_mocks=False)
        assert container.use_mocks is True

    @patch.dict(os.environ, {"USE_MOCK_MODE": "no"})
    def test_environment_override_no(self):
        """Test that USE_MOCK_MODE=no triggers real implementation."""
        with pytest.raises(NotImplementedError):
            MockInfrastructureContainer(use_mocks=True)

    @patch.dict(os.environ, {"USE_MOCK_MODE": "0"})
    def test_environment_override_zero(self):
        """Test that USE_MOCK_MODE=0 triggers real implementation."""
        with pytest.raises(NotImplementedError):
            MockInfrastructureContainer(use_mocks=True)

    @patch.dict(os.environ, {
        "MOCK_RESPONSE_DELAY_MS": "100",
        "MOCK_ERROR_RATE": "0.1",
        "MOCK_DATA_SEED": "123"
    })
    def test_mock_configuration_from_environment(self):
        """Test that mock configuration is loaded from environment."""
        container = MockInfrastructureContainer(use_mocks=True)

        assert container.mock_response_delay_ms == 100
        assert container.mock_error_rate == 0.1
        assert container.mock_data_seed == 123

    def test_default_mock_configuration(self):
        """Test default mock configuration values."""
        container = MockInfrastructureContainer(use_mocks=True)

        assert container.mock_response_delay_ms == 0
        assert container.mock_error_rate == 0.0
        assert container.mock_data_seed == 42

    def test_real_implementation_not_implemented(self):
        """Test that real implementation raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            MockInfrastructureContainer(use_mocks=False)

        assert "Real implementations not yet available" in str(exc_info.value)
        assert "USE_MOCK_MODE=true" in str(exc_info.value)

    def test_get_configuration(self):
        """Test that get_configuration returns current settings."""
        container = MockInfrastructureContainer(use_mocks=True)
        config = container.get_configuration()

        assert config["mode"] == "mock"
        assert config["use_mocks"] is True
        assert config["mock_response_delay_ms"] == 0
        assert config["mock_error_rate"] == 0.0
        assert config["mock_data_seed"] == 42
        assert config["initialized"] is True

    @patch.dict(os.environ, {"USE_MOCK_MODE": "invalid"})
    def test_invalid_environment_value_uses_constructor(self):
        """Test that invalid USE_MOCK_MODE value defaults to constructor parameter."""
        # Should use constructor parameter when env value is invalid
        container_true = MockInfrastructureContainer(use_mocks=True)
        assert container_true.use_mocks is True

        with pytest.raises(NotImplementedError):
            MockInfrastructureContainer(use_mocks=False)

    def test_singleton_behavior(self):
        """Test that services are singletons within a container instance."""
        container = MockInfrastructureContainer(use_mocks=True)

        # Get services twice and verify they're the same instance
        redis1 = container.get_redis_client()
        redis2 = container.get_redis_client()
        assert redis1 is redis2

        conv_repo1 = container.get_conversation_repository()
        conv_repo2 = container.get_conversation_repository()
        assert conv_repo1 is conv_repo2

        product_repo1 = container.get_product_repository()
        product_repo2 = container.get_product_repository()
        assert product_repo1 is product_repo2

        query_analyzer1 = container.get_query_analyzer()
        query_analyzer2 = container.get_query_analyzer()
        assert query_analyzer1 is query_analyzer2

        ai_agent1 = container.get_ai_agent()
        ai_agent2 = container.get_ai_agent()
        assert ai_agent1 is ai_agent2
