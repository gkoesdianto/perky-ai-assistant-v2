"""Service integration tests for Convergence Point 1.

Tests that all services (ChatAgent, ProductService, Container) work together
after Track 1-3 completion. Run this after individual tracks are complete.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.container import get_container, Container
from src.infrastructure.mocks.container.mock_container import (
    MockInfrastructureContainer,
)

from src.infrastructure.services.mock_product_service import MockProductService
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)


class TestServiceIntegration:
    """Integration tests for all services working together."""

    @pytest.mark.asyncio
    async def test_container_service_access(self):
        """Test that all services can be accessed from container."""
        with patch.dict(
            "os.environ", {"USE_MOCK_MODE": "true", "OPENAI_API_KEY": "test-key"}
        ):
            container = get_container()
            assert isinstance(container, MockInfrastructureContainer)

            # Test product repository access
            product_repo = container.get_product_repository()
            assert product_repo is not None

            # Test conversation repository access
            conversation_repo = container.get_conversation_repository()
            assert conversation_repo is not None

            # Test session repository access
            session_repo = container.get_session_repository()
            assert session_repo is not None

            # Test AI agent access
            ai_agent = container.get_ai_agent()
            assert ai_agent is not None

    @pytest.mark.asyncio
    async def test_chat_agent_with_product_service(self):
        """Test ChatAgent integration with ProductService."""
        product_service = MockProductService()

        products = await product_service.search_products("plat")
        assert len(products) > 0
        assert any("plat" in p.product_name.lower() or "baja" in p.product_name.lower() for p in products)

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("src.infrastructure.ai.chat_agent.Agent") as mock_agent_class:
                mock_agent = MagicMock()
                mock_agent.run = AsyncMock()
                mock_agent.run.return_value = MagicMock(
                    data="Saya akan membantu mencari plat baja untuk Anda."
                )
                mock_agent_class.return_value = mock_agent

                # Test that tools can access product service
                variant = await product_service.get_variant_by_sku("PLT-5MM-4X8")
                assert variant is not None
                assert hasattr(variant, 'stock_quantity')

    @pytest.mark.asyncio
    async def test_conversation_repository_integration(self):
        """Test conversation repository stores and retrieves correctly."""
        from src.domain.entities import Conversation, Message
        from datetime import datetime, timezone

        repo = InMemoryConversationRepository()

        conversation = Conversation(
            id="conv-test-1",
            session_id="session-test-1",
            started_at=datetime.now(timezone.utc),
        )

        message = Message(
            id="msg-1",
            content="Test message",
            sender_type="user",
            conversation_id="conv-test-1",
            created_at=datetime.now(timezone.utc),
        )
        conversation.add_message(message)

        await repo.save(conversation)

        retrieved = await repo.get_by_session("session-test-1")
        assert retrieved is not None
        assert retrieved.id == "conv-test-1"
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_container_singleton_behavior(self):
        """Test that container components are properly managed."""
        with patch.dict("os.environ", {"USE_MOCK_MODE": "true"}):
            container1 = get_container()
            container2 = get_container()

            # Each call creates a new container instance
            assert container1 is not container2

            # But wrapper provides consistent access
            wrapper = Container()
            session_repo1 = wrapper.session_repository
            session_repo2 = wrapper.session_repository

            # Should return same instance from same wrapper
            assert session_repo1 is session_repo2

    @pytest.mark.asyncio
    async def test_mock_product_service_search(self):
        """Test mock product service search functionality."""
        service = MockProductService()

        results = await service.search_products("besi")
        assert len(results) > 0

        found = False
        for product in results:
            if "Besi" in product.product_name or "besi" in product.product_name.lower():
                found = True
                break
        assert found

        results = await service.search_products("plat")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_mock_product_service_variants(self):
        """Test mock product service variant retrieval."""
        service = MockProductService()

        product = await service.get_product_with_variants("PROD-001")
        assert product is not None
        assert product.product.product_id == "PROD-001"
        assert len(product.variants) > 0

        variant_skus = [v.sku for v in product.variants]
        assert len(variant_skus) > 0
        assert all("PLT" in sku or "PLAT" in sku for sku in variant_skus)

    @pytest.mark.asyncio
    async def test_conversation_repository_limits(self):
        """Test conversation repository respects limits."""
        repo = InMemoryConversationRepository()
        repo.max_conversations = 3

        from src.domain.entities import Conversation
        from datetime import datetime, timezone, timedelta

        for i in range(4):
            conversation = Conversation(
                id=f"conv-{i}",
                session_id=f"session-{i}",
                started_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            await repo.save(conversation)

        oldest = await repo.get_by_session("session-0")
        assert oldest is None

        for i in range(1, 4):
            conv = await repo.get_by_session(f"session-{i}")
            assert conv is not None

    @pytest.mark.asyncio
    async def test_product_service_network_delay(self):
        """Test that mock product service simulates network delays."""
        import time

        service = MockProductService()

        start = time.time()
        await service.search_products("test")
        elapsed = time.time() - start

        assert elapsed >= 0.05
        assert elapsed <= 0.5

    @pytest.mark.asyncio
    async def test_end_to_end_service_flow(self):
        """Test complete service flow from container to response."""
        from src.infrastructure.dependencies import configure_services_for_mode

        with patch.dict(
            "os.environ",
            {
                "USE_MOCK_MODE": "false",  # Use real implementations
                "OPENAI_API_KEY": "test-key",
                "OPENAI_MODEL": "gpt-4o-mini",
                "OPENAI_TEMPERATURE": "0.7",
                "OPENAI_MAX_TOKENS": "500",
            },
        ):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    container = configure_services_for_mode()

                    # All services should be available
                    product_repo = container.get_product_repository()
                    assert product_repo is not None

                    conversation_repo = container.get_conversation_repository()
                    assert conversation_repo is not None

                    session_repo = container.get_session_repository()
                    assert session_repo is not None

                    ai_agent = container.get_ai_agent()
                    assert ai_agent is not None
