"""Integration tests for mock services."""

import pytest
from datetime import datetime

from src.infrastructure.services.mock_product_service import MockProductService
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message


class TestMockProductService:
    """Test suite for MockProductService."""

    @pytest.mark.asyncio
    async def test_search_products(self):
        """Test product search functionality."""
        service = MockProductService()

        results = await service.search_products("plat baja")

        assert results is not None
        assert len(results) > 0
        assert any("plat" in p.product_name.lower() for p in results)

    @pytest.mark.asyncio
    async def test_search_products_indonesian(self):
        """Test search with Indonesian terminology."""
        service = MockProductService()

        results = await service.search_products("besi kotak")

        assert results is not None
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_product_with_variants(self):
        """Test getting product with variants."""
        service = MockProductService()

        product = await service.get_product_with_variants("PROD-001")

        assert product is not None
        assert product.product.product_id == "PROD-001"
        assert len(product.variants) > 0

    @pytest.mark.asyncio
    async def test_get_product_not_found(self):
        """Test getting non-existent product."""
        service = MockProductService()

        product = await service.get_product_with_variants("INVALID")

        assert product is None

    @pytest.mark.asyncio
    async def test_get_variant_by_sku(self):
        """Test getting variant by SKU."""
        service = MockProductService()

        variant = await service.get_variant_by_sku("PLT-5MM-4X8")

        assert variant is not None
        assert variant.sku == "PLT-5MM-4X8"
        assert variant.variant_name is not None

    @pytest.mark.asyncio
    async def test_get_variants_by_product(self):
        """Test getting all variants for a product."""
        service = MockProductService()

        variants = await service.get_variants_by_product("PROD-001")

        assert variants is not None
        assert len(variants) > 0
        assert all(v.product_id == "PROD-001" for v in variants)


class TestInMemoryConversationRepository:
    """Test suite for InMemoryConversationRepository."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve_conversation(self):
        """Test saving and retrieving a conversation."""
        repo = InMemoryConversationRepository()

        conversation = Conversation(session_id="test-123")
        message = Message(
            conversation_id=conversation.id, content="Test message", sender_type="user"
        )
        conversation.add_message(message)

        await repo.save(conversation)

        retrieved = await repo.get_by_session("test-123")
        assert retrieved is not None
        assert retrieved.session_id == "test-123"
        assert len(retrieved.messages) == 1

    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """Test deleting a conversation."""
        repo = InMemoryConversationRepository()

        conversation = Conversation(session_id="test-456")
        await repo.save(conversation)

        await repo.delete("test-456")

        retrieved = await repo.get_by_session("test-456")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_recent_messages(self):
        """Test getting recent messages."""
        repo = InMemoryConversationRepository()

        conversation = Conversation(session_id="test-789")
        for i in range(15):
            message = Message(
                conversation_id=conversation.id,
                content=f"Message {i}",
                sender_type="user",
            )
            conversation.add_message(message)

        await repo.save(conversation)

        recent = await repo.get_recent_messages("test-789", limit=10)
        assert len(recent) == 10
        assert recent[0].content == "Message 5"
        assert recent[-1].content == "Message 14"

    @pytest.mark.asyncio
    async def test_thread_safety(self):
        """Test thread-safe operations."""
        repo = InMemoryConversationRepository()

        async def save_conversation(session_id: str):
            conversation = Conversation(session_id=session_id)
            message = Message(
                conversation_id=conversation.id,
                content=f"Message for {session_id}",
                sender_type="user",
            )
            conversation.add_message(message)
            await repo.save(conversation)

        import asyncio

        tasks = [save_conversation(f"session-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

        stats = await repo.get_stats()
        assert stats["total_conversations"] == 10
        assert stats["total_messages"] == 10

    @pytest.mark.asyncio
    async def test_max_conversations_limit(self):
        """Test conversation limit enforcement."""
        repo = InMemoryConversationRepository()
        repo.max_conversations = 3

        for i in range(5):
            conversation = Conversation(session_id=f"session-{i}")
            conversation.created_at = datetime(2024, 1, 1, hour=i)
            await repo.save(conversation)

        stats = await repo.get_stats()
        assert stats["total_conversations"] == 3

        assert await repo.get_by_session("session-0") is None
        assert await repo.get_by_session("session-1") is None
        assert await repo.get_by_session("session-2") is not None

    @pytest.mark.asyncio
    async def test_max_messages_limit(self):
        """Test message limit per conversation."""
        repo = InMemoryConversationRepository()
        repo.max_messages_per_conversation = 5

        conversation = Conversation(session_id="test-limit")
        for i in range(10):
            message = Message(
                conversation_id=conversation.id,
                content=f"Message {i}",
                sender_type="user",
            )
            conversation.add_message(message)

        await repo.save(conversation)

        retrieved = await repo.get_by_session("test-limit")
        assert len(retrieved.messages) == 5
        assert retrieved.messages[0].content == "Message 5"
        assert retrieved.messages[-1].content == "Message 9"
