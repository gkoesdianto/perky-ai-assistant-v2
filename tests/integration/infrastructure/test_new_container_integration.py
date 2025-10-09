"""Integration tests for new InfrastructureContainer."""

import pytest

from src.infrastructure.container import InfrastructureContainer


class TestContainerIntegration:
    """Test container integration with dependencies."""

    def setup_method(self):
        """Reset before each test."""
        InfrastructureContainer.reset()

    def teardown_method(self):
        """Clean up after each test."""
        InfrastructureContainer.reset()

    def test_mock_mode_provides_all_dependencies(self):
        """Mock mode initializes all dependencies."""
        container = InfrastructureContainer.instance(use_mocks=True)

        assert container.ai_agent is not None
        assert container.product_service is not None
        assert container.session_repository is not None
        assert container.conversation_repository is not None
        assert container.redis_client is not None
        assert container.query_analyzer is not None

    def test_real_mode_provides_all_dependencies(self):
        """Real mode initializes all dependencies."""
        container = InfrastructureContainer.instance(use_mocks=False)

        assert container.ai_agent is not None
        assert container.product_service is not None
        assert container.session_repository is not None
        assert container.conversation_repository is not None
        assert container.redis_client is not None
        assert container.query_analyzer is not None

    def test_get_configuration(self):
        """Configuration method returns valid data."""
        container = InfrastructureContainer.instance(use_mocks=True)
        config = container.get_configuration()

        assert config["mode"] == "mock"
        assert config["initialized"] is True
        assert "components" in config
        assert len(config["components"]) == 6
