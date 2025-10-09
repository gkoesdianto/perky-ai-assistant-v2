"""Unit tests for InfrastructureContainer singleton pattern."""

import pytest

from src.infrastructure.container import InfrastructureContainer


class TestSingletonPattern:
    """Test singleton behavior of InfrastructureContainer."""

    def setup_method(self):
        """Reset singleton before each test."""
        InfrastructureContainer.reset()

    def teardown_method(self):
        """Clean up after each test."""
        InfrastructureContainer.reset()

    def test_instance_returns_same_object(self):
        """Multiple instance() calls return same object."""
        container1 = InfrastructureContainer.instance()
        container2 = InfrastructureContainer.instance()

        assert container1 is container2

    def test_reset_clears_singleton(self):
        """Reset creates new instance on next call."""
        container1 = InfrastructureContainer.instance()
        InfrastructureContainer.reset()
        container2 = InfrastructureContainer.instance()

        assert container1 is not container2

    def test_explicit_mock_mode(self):
        """Explicit use_mocks parameter works."""
        container = InfrastructureContainer.instance(use_mocks=True)
        assert container.mode == "mock"

    def test_explicit_real_mode(self):
        """Explicit use_mocks=False works."""
        container = InfrastructureContainer.instance(use_mocks=False)
        assert container.mode == "real"
