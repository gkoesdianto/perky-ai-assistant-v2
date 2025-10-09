"""Unit tests for InfrastructureContainer mode detection."""

import os

import pytest

from src.infrastructure.container import InfrastructureContainer


class TestModeDetection:
    """Test mode detection logic."""

    def setup_method(self):
        """Reset before each test."""
        InfrastructureContainer.reset()
        # Save original env var
        self.original_env = os.environ.get("USE_MOCK_MODE")

    def teardown_method(self):
        """Restore env after each test."""
        InfrastructureContainer.reset()
        if self.original_env is not None:
            os.environ["USE_MOCK_MODE"] = self.original_env
        elif "USE_MOCK_MODE" in os.environ:
            del os.environ["USE_MOCK_MODE"]

    def test_env_true_enables_mocks(self):
        """USE_MOCK_MODE=true enables mocks."""
        os.environ["USE_MOCK_MODE"] = "true"
        container = InfrastructureContainer.instance()
        assert container.mode == "mock"

    def test_env_false_enables_real(self):
        """USE_MOCK_MODE=false enables real."""
        os.environ["USE_MOCK_MODE"] = "false"
        container = InfrastructureContainer.instance()
        assert container.mode == "real"

    def test_env_1_enables_mocks(self):
        """USE_MOCK_MODE=1 enables mocks."""
        os.environ["USE_MOCK_MODE"] = "1"
        container = InfrastructureContainer.instance()
        assert container.mode == "mock"

    def test_default_is_real(self):
        """Default mode is real when env not set."""
        if "USE_MOCK_MODE" in os.environ:
            del os.environ["USE_MOCK_MODE"]
        container = InfrastructureContainer.instance()
        assert container.mode == "real"

    def test_explicit_overrides_env(self):
        """Explicit parameter overrides environment."""
        os.environ["USE_MOCK_MODE"] = "false"
        container = InfrastructureContainer.instance(use_mocks=True)
        assert container.mode == "mock"
