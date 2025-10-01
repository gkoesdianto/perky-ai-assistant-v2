"""Unit tests for ApplicationContainer."""

import os
from unittest.mock import patch

import pytest

from src.application.container import ApplicationContainer
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
from src.infrastructure.mocks.mock_conversation_repository import (
    MockConversationRepository,
)
from src.infrastructure.mocks.mock_product_repository import MockProductRepository
from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
from src.infrastructure.mocks.mock_redis_client import MockRedisClient


class TestApplicationContainer:
    """Test suite for ApplicationContainer."""

    def test_application_container_initialization(self):
        """Test that application container initializes with mock infrastructure."""
        container = ApplicationContainer()

        assert container.infrastructure is not None
        assert container.infrastructure.mode == "mock"
        assert container.infrastructure.use_mocks is True

    def test_get_redis_client(self):
        """Test that get_redis_client returns MockRedisClient."""
        container = ApplicationContainer()
        redis_client = container.get_redis_client()

        assert redis_client is not None
        assert isinstance(redis_client, MockRedisClient)

    def test_get_conversation_repository(self):
        """Test that get_conversation_repository returns MockConversationRepository."""
        container = ApplicationContainer()
        repo = container.get_conversation_repository()

        assert repo is not None
        assert isinstance(repo, MockConversationRepository)

    def test_get_product_repository(self):
        """Test that get_product_repository returns MockProductRepository."""
        container = ApplicationContainer()
        repo = container.get_product_repository()

        assert repo is not None
        assert isinstance(repo, MockProductRepository)

    def test_get_query_analyzer(self):
        """Test that get_query_analyzer returns MockQueryAnalyzer."""
        container = ApplicationContainer()
        analyzer = container.get_query_analyzer()

        assert analyzer is not None
        assert isinstance(analyzer, MockQueryAnalyzer)

    def test_get_ai_agent(self):
        """Test that get_ai_agent returns MockAIAgent."""
        container = ApplicationContainer()
        agent = container.get_ai_agent()

        assert agent is not None
        assert isinstance(agent, MockAIAgent)

    def test_services_are_singletons(self):
        """Test that services return the same instance on multiple calls."""
        container = ApplicationContainer()

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

        analyzer1 = container.get_query_analyzer()
        analyzer2 = container.get_query_analyzer()
        assert analyzer1 is analyzer2

        agent1 = container.get_ai_agent()
        agent2 = container.get_ai_agent()
        assert agent1 is agent2

    @patch.dict(os.environ, {"USE_MOCK_MODE": "true"})
    def test_mock_mode_from_environment(self):
        """Test that container respects USE_MOCK_MODE environment variable."""
        container = ApplicationContainer()

        assert container.infrastructure.use_mocks is True
        assert container.infrastructure.mode == "mock"

    @patch.dict(
        os.environ,
        {
            "MOCK_RESPONSE_DELAY_MS": "100",
            "MOCK_ERROR_RATE": "0.1",
            "MOCK_DATA_SEED": "123",
        },
    )
    def test_mock_configuration_propagation(self):
        """Test that mock configuration is properly propagated from environment."""
        container = ApplicationContainer()
        config = container.infrastructure.get_configuration()

        assert config["mock_response_delay_ms"] == 100
        assert config["mock_error_rate"] == 0.1
        assert config["mock_data_seed"] == 123

    def test_multiple_containers_share_same_infrastructure_config(self):
        """Test that multiple container instances can coexist."""
        container1 = ApplicationContainer()
        container2 = ApplicationContainer()

        # Each container has its own infrastructure instance
        assert container1.infrastructure is not container2.infrastructure

        # But they have the same configuration
        config1 = container1.infrastructure.get_configuration()
        config2 = container2.infrastructure.get_configuration()

        assert config1["mode"] == config2["mode"]
        assert config1["use_mocks"] == config2["use_mocks"]

    def test_all_services_available(self):
        """Test that all expected services are available from the container."""
        container = ApplicationContainer()

        # List of expected service getter methods
        expected_services = [
            "get_redis_client",
            "get_conversation_repository",
            "get_product_repository",
            "get_query_analyzer",
            "get_ai_agent",
        ]

        for service_getter in expected_services:
            assert hasattr(container, service_getter)
            service = getattr(container, service_getter)()
            assert service is not None
