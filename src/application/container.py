"""
Application-level dependency container.
Integrates with infrastructure layer for dependency injection.
"""

from src.infrastructure.container import InfrastructureContainer


class ApplicationContainer:
    """Application-level dependency container."""

    def __init__(self):
        # Initialize infrastructure container
        self.infrastructure = InfrastructureContainer.instance(use_mocks=True)

        # Wire up application services
        self._setup_services()

    def _setup_services(self):
        """Setup application services with dependencies."""
        # Note: ChatOrchestrator requires use case implementations
        # which will be wired up in Phase 4 when implementing WebSocket integration.
        # For now, we're providing direct access to the mock services
        # so they can be used in integration tests.
        pass

    def get_redis_client(self):
        """Get Redis client from infrastructure."""
        return self.infrastructure.redis_client

    def get_conversation_repository(self):
        """Get conversation repository from infrastructure."""
        return self.infrastructure.conversation_repository

    def get_product_repository(self):
        """Get product repository from infrastructure."""
        return self.infrastructure.product_service

    def get_query_analyzer(self):
        """Get query analyzer from infrastructure."""
        return self.infrastructure.query_analyzer

    def get_ai_agent(self):
        """Get AI agent from infrastructure."""
        return self.infrastructure.ai_agent
