"""Unit tests for MockConversationRepository implementation.

Tests cover all functionality including thread-safety, CRUD operations,
and automatic cleanup of expired conversations.
"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from src.infrastructure.mocks.mock_conversation_repository import MockConversationRepository
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message

# Import factories from the consolidated test infrastructure
from tests.factories import ConversationFactory, MessageFactory


@pytest.fixture
def repository():
    """Create a MockConversationRepository instance."""
    return MockConversationRepository()


@pytest.fixture
def sample_conversation():
    """Create a sample conversation using factory."""
    conversation = ConversationFactory.create(
        session_id="test-session-123",
        metadata={"user_id": "user-456", "channel": "web"}
    )

    # Add some messages using factory
    message1 = MessageFactory.create(
        content="Hello, I need help with steel products",
        sender_type="user",
        conversation_id=conversation.id
    )
    message2 = MessageFactory.create(
        content="I can help you with steel products. What are you looking for?",
        sender_type="ai_agent",
        conversation_id=conversation.id
    )

    conversation.add_message(message1)
    conversation.add_message(message2)

    return conversation


@pytest.fixture
def expired_conversation():
    """Create an expired conversation (last activity > 1 hour ago)."""
    conversation = ConversationFactory.create(
        session_id="expired-session-789",
        metadata={"user_id": "user-old", "channel": "api"}
    )

    # Manually set last_activity to 2 hours ago
    conversation.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    return conversation


class TestMockConversationRepository:
    """Test suite for MockConversationRepository."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve_conversation(self, repository, sample_conversation):
        """Test saving and retrieving a conversation."""
        # Save conversation
        await repository.save(sample_conversation)

        # Retrieve conversation
        retrieved = await repository.get_by_session(sample_conversation.session_id)

        # Assertions
        assert retrieved is not None
        assert retrieved.session_id == sample_conversation.session_id
        assert retrieved.messages == sample_conversation.messages
        assert retrieved.metadata == sample_conversation.metadata

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, repository):
        """Test retrieving a conversation that doesn't exist."""
        result = await repository.get_by_session("nonexistent-session")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_existing_conversation(self, repository, sample_conversation):
        """Test updating an existing conversation."""
        # Save initial conversation
        await repository.save(sample_conversation)

        # Add a new message and update
        new_message = MessageFactory.create(
            content="I need plat baja 5mm",
            sender_type="user",
            conversation_id=sample_conversation.id
        )
        sample_conversation.add_message(new_message)

        # Save updated conversation
        await repository.save(sample_conversation)

        # Retrieve and verify
        retrieved = await repository.get_by_session(sample_conversation.session_id)
        assert retrieved is not None
        assert len(retrieved.messages) == 3
        assert retrieved.messages[-1].content == "I need plat baja 5mm"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, repository, sample_conversation):
        """Test deleting a conversation."""
        # Save conversation
        await repository.save(sample_conversation)

        # Verify it exists
        retrieved = await repository.get_by_session(sample_conversation.session_id)
        assert retrieved is not None

        # Delete conversation
        await repository.delete(sample_conversation.session_id)

        # Verify it's deleted
        retrieved = await repository.get_by_session(sample_conversation.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, repository):
        """Test deleting a conversation that doesn't exist (should not raise error)."""
        # This should not raise an error
        await repository.delete("nonexistent-session")

    @pytest.mark.asyncio
    async def test_cleanup_expired_conversations(self, repository, sample_conversation, expired_conversation):
        """Test cleanup of expired conversations."""
        # Save both conversations
        await repository.save(sample_conversation)
        await repository.save(expired_conversation)

        # Verify both exist
        assert await repository.get_by_session(sample_conversation.session_id) is not None
        assert await repository.get_by_session(expired_conversation.session_id) is not None

        # Run cleanup (default 1 hour)
        await repository.cleanup_expired()

        # Verify active conversation still exists
        assert await repository.get_by_session(sample_conversation.session_id) is not None

        # Verify expired conversation is removed
        assert await repository.get_by_session(expired_conversation.session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_with_custom_expiry_hours(self, repository):
        """Test cleanup with custom expiry hours."""
        # Create conversations with different ages using factory
        recent = ConversationFactory.create(session_id="recent")
        recent.last_activity = datetime.now(timezone.utc) - timedelta(minutes=30)

        one_hour_old = ConversationFactory.create(session_id="one-hour")
        one_hour_old.last_activity = datetime.now(timezone.utc) - timedelta(hours=1, minutes=30)

        three_hours_old = ConversationFactory.create(session_id="three-hours")
        three_hours_old.last_activity = datetime.now(timezone.utc) - timedelta(hours=3)

        # Save all conversations
        await repository.save(recent)
        await repository.save(one_hour_old)
        await repository.save(three_hours_old)

        # Cleanup with 2 hour expiry
        await repository.cleanup_expired(hours=2)

        # Verify results
        assert await repository.get_by_session("recent") is not None
        assert await repository.get_by_session("one-hour") is not None
        assert await repository.get_by_session("three-hours") is None

    @pytest.mark.asyncio
    async def test_thread_safety_concurrent_saves(self, repository):
        """Test thread-safety during concurrent save operations."""
        # Create multiple conversations using factory
        conversations = [
            ConversationFactory.create(
                session_id=f"session-{i}",
                metadata={"index": i}
            )
            for i in range(10)
        ]

        # Save them concurrently
        await asyncio.gather(*[
            repository.save(conv) for conv in conversations
        ])

        # Verify all were saved
        for conv in conversations:
            retrieved = await repository.get_by_session(conv.session_id)
            assert retrieved is not None
            assert retrieved.metadata["index"] == conv.metadata["index"]

    @pytest.mark.asyncio
    async def test_thread_safety_concurrent_reads(self, repository, sample_conversation):
        """Test thread-safety during concurrent read operations."""
        # Save a conversation
        await repository.save(sample_conversation)

        # Read it concurrently multiple times
        results = await asyncio.gather(*[
            repository.get_by_session(sample_conversation.session_id)
            for _ in range(10)
        ])

        # Verify all reads returned the same conversation
        for result in results:
            assert result is not None
            assert result.session_id == sample_conversation.session_id

    @pytest.mark.asyncio
    async def test_thread_safety_mixed_operations(self, repository):
        """Test thread-safety with mixed concurrent operations."""
        # Initial conversations using factory
        initial_convs = [
            ConversationFactory.create(session_id=f"init-{i}")
            for i in range(3)
        ]

        # Save initial conversations
        for conv in initial_convs:
            await repository.save(conv)

        async def mixed_operations():
            """Perform various operations concurrently."""
            tasks = []

            # Save new conversations
            for i in range(3, 6):
                conv = ConversationFactory.create(session_id=f"new-{i}")
                tasks.append(repository.save(conv))

            # Read existing conversations
            for i in range(3):
                tasks.append(repository.get_by_session(f"init-{i}"))

            # Delete a conversation
            tasks.append(repository.delete("init-0"))

            # Run cleanup
            tasks.append(repository.cleanup_expired())

            return await asyncio.gather(*tasks, return_exceptions=True)

        # Execute mixed operations
        results = await mixed_operations()

        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception)

        # Verify state after operations
        assert await repository.get_by_session("init-0") is None  # Deleted
        assert await repository.get_by_session("init-1") is not None  # Still exists
        assert await repository.get_by_session("new-3") is not None  # New conversation saved

    @pytest.mark.asyncio
    async def test_multiple_conversations_different_sessions(self, repository):
        """Test handling multiple conversations with different session IDs."""
        # Create conversations for different sessions using factory
        conversations = []
        for i in range(5):
            conv = ConversationFactory.create(
                session_id=f"session-{i}",
                metadata={"user_id": f"user-{i}", "index": i}
            )
            conversations.append(conv)
            await repository.save(conv)

        # Verify each can be retrieved independently
        for conv in conversations:
            retrieved = await repository.get_by_session(conv.session_id)
            assert retrieved is not None
            assert retrieved.session_id == conv.session_id
            assert retrieved.metadata["index"] == conv.metadata["index"]

    @pytest.mark.asyncio
    async def test_empty_repository_cleanup(self, repository):
        """Test cleanup on an empty repository doesn't cause errors."""
        # This should not raise any errors
        await repository.cleanup_expired()

        # Repository should still be functional
        conv = ConversationFactory.create(session_id="test")
        await repository.save(conv)
        retrieved = await repository.get_by_session("test")
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_conversation_with_many_messages(self, repository):
        """Test conversation with many messages."""
        conversation = ConversationFactory.create(session_id="many-messages")

        # Add many messages using factory
        for i in range(20):
            message = MessageFactory.create(
                content=f"Message {i}",
                sender_type="user" if i % 2 == 0 else "ai_agent",
                conversation_id=conversation.id
            )
            conversation.add_message(message)

        # Save and retrieve
        await repository.save(conversation)
        retrieved = await repository.get_by_session("many-messages")

        # Verify all messages are preserved
        assert retrieved is not None
        assert len(retrieved.messages) == 20
        assert retrieved.messages[0].content == "Message 0"
        assert retrieved.messages[-1].content == "Message 19"

    @pytest.mark.asyncio
    async def test_concurrent_cleanup_and_operations(self, repository):
        """Test cleanup running concurrently with other operations."""
        # Create some conversations
        active_conv = ConversationFactory.create(session_id="active")
        expired_conv = ConversationFactory.create(session_id="expired")
        expired_conv.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

        await repository.save(active_conv)
        await repository.save(expired_conv)

        # Run cleanup and other operations concurrently
        results = await asyncio.gather(
            repository.cleanup_expired(),
            repository.get_by_session("active"),
            repository.save(ConversationFactory.create(session_id="new-during-cleanup")),
            return_exceptions=True
        )

        # Verify no exceptions
        for result in results:
            assert not isinstance(result, Exception)

        # Verify final state
        assert await repository.get_by_session("active") is not None
        assert await repository.get_by_session("expired") is None
        assert await repository.get_by_session("new-during-cleanup") is not None
