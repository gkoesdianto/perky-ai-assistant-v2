"""Infrastructure container for dependency injection."""

from src.infrastructure.mocks.container.mock_container import (
    MockInfrastructureContainer,
)
from src.infrastructure.dependencies import configure_services_for_mode


def get_container() -> MockInfrastructureContainer:
    """
    Get the infrastructure container instance.

    Returns:
        Infrastructure container with all dependencies
    """
    # Phase 5 Track 3: Enhanced DI with real/mock mode selection
    # Automatically determines mode from environment
    return configure_services_for_mode()


# Global container instance (singleton pattern)
_container = None


def get_singleton_container() -> MockInfrastructureContainer:
    """
    Get singleton container instance.

    Returns:
        Shared infrastructure container instance
    """
    global _container
    if _container is None:
        _container = get_container()
    return _container


# Create convenience properties for the container
class Container:
    """Wrapper class to provide property-based access."""

    def __init__(self):
        self._container = get_singleton_container()

    @property
    def session_repository(self):
        return self._container.get_session_repository()

    @property
    def conversation_repository(self):
        return self._container.get_conversation_repository()

    @property
    def redis_client(self):
        return self._container.get_redis_client()

    @property
    def ai_agent(self):
        return self._container.get_ai_agent()

    @property
    def query_analyzer(self):
        return self._container.get_query_analyzer()

    @property
    def product_service(self):
        return self._container.get_product_repository()
