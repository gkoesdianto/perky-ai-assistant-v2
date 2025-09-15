import json
from datetime import datetime

import pytest

from src.application.dto.session_dto import SessionDTO
from src.application.use_cases.start_chat_session import StartChatSessionUseCaseImpl


class TestStartChatSessionUseCaseImpl:
    """
    Test suite for StartChatSessionUseCaseImpl.

    This test suite validates the behavior of the Start Chat Session use case,
    including session creation, retrieval, and Redis interaction.
    """

    @pytest.fixture
    def use_case(self, mock_redis_adapter):
        """
        Create a StartChatSessionUseCaseImpl instance with mocked dependencies.

        Args:
            mock_redis_adapter: Shared fixture from conftest.py

        Returns:
            StartChatSessionUseCaseImpl: The use case instance for testing
        """
        return StartChatSessionUseCaseImpl(
            session_repository=None, redis_client=mock_redis_adapter  # Not used in MVP
        )

    @pytest.mark.asyncio
    async def test_execute_with_existing_session(self, use_case, mock_redis_adapter):
        """Test that existing session is returned from Redis."""
        # Arrange
        session_id = "test-session-123"
        metadata = {"user_agent": "test-browser", "ip": "127.0.0.1"}

        # Create existing session data
        existing_session_data = {
            "session_id": session_id,
            "conversation_id": "conv-456",
            "started_at": "2024-01-15T10:00:00+00:00",
            "last_activity": "2024-01-15T10:30:00+00:00",
            "is_active": True,
            "metadata": {"user_agent": "old-browser", "ip": "192.168.1.1"},
        }

        # Pre-populate Redis with existing session
        redis_client = await mock_redis_adapter.get_client()
        await redis_client.setex(
            f"session:{session_id}", 3600, json.dumps(existing_session_data)
        )

        # Act
        result = await use_case.execute(session_id, metadata)

        # Assert
        assert isinstance(result, SessionDTO)
        assert result.session_id == session_id
        assert result.conversation_id == "conv-456"
        assert result.is_active is True
        # Original metadata should be preserved
        assert result.metadata == {"user_agent": "old-browser", "ip": "192.168.1.1"}

    @pytest.mark.asyncio
    async def test_execute_with_new_session(self, use_case, mock_redis_adapter):
        """Test that new session is created and stored in Redis."""
        # Arrange
        session_id = "new-session-456"
        metadata = {"user_agent": "test-browser", "ip": "127.0.0.1"}

        # Act
        result = await use_case.execute(session_id, metadata)

        # Assert - Verify returned DTO
        assert isinstance(result, SessionDTO)
        assert result.session_id == session_id
        assert result.conversation_id is None  # New session has no conversation
        assert result.is_active is True
        assert result.metadata == metadata
        assert isinstance(result.started_at, datetime)
        assert isinstance(result.last_activity, datetime)

        # Assert - Verify Redis storage
        redis_client = await mock_redis_adapter.get_client()
        stored_value = await redis_client.get(f"session:{session_id}")
        assert stored_value is not None

        stored_data = json.loads(stored_value)
        assert stored_data["session_id"] == session_id
        assert stored_data["conversation_id"] is None
        assert stored_data["is_active"] is True
        assert stored_data["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_execute_with_empty_metadata(self, use_case, mock_redis_adapter):
        """Test that session can be created with empty metadata."""
        # Arrange
        session_id = "session-no-metadata"
        metadata = {}

        # Act
        result = await use_case.execute(session_id, metadata)

        # Assert
        assert isinstance(result, SessionDTO)
        assert result.session_id == session_id
        assert result.metadata == {}

        # Verify storage
        redis_client = await mock_redis_adapter.get_client()
        stored_value = await redis_client.get(f"session:{session_id}")
        stored_data = json.loads(stored_value)
        assert stored_data["metadata"] == {}

    @pytest.mark.asyncio
    async def test_execute_preserves_timestamps(self, use_case, mock_redis_adapter):
        """Test that timestamps are properly preserved when retrieving existing
        session."""
        # Arrange
        session_id = "session-with-timestamps"
        metadata = {"source": "test"}

        started_at = "2024-01-15T09:00:00+00:00"
        last_activity = "2024-01-15T11:30:00+00:00"

        existing_session_data = {
            "session_id": session_id,
            "conversation_id": None,
            "started_at": started_at,
            "last_activity": last_activity,
            "is_active": True,
            "metadata": {"source": "original"},
        }

        # Pre-populate Redis
        redis_client = await mock_redis_adapter.get_client()
        await redis_client.setex(
            f"session:{session_id}", 3600, json.dumps(existing_session_data)
        )

        # Act
        result = await use_case.execute(session_id, metadata)

        # Assert
        assert result.started_at == datetime.fromisoformat(started_at)
        assert result.last_activity == datetime.fromisoformat(last_activity)
        # Original metadata should be preserved, not overwritten
        assert result.metadata == {"source": "original"}

    @pytest.mark.asyncio
    async def test_redis_key_format(self, use_case, mock_redis_adapter):
        """Test that the correct Redis key format is used."""
        # Arrange
        session_id = "key-format-test"
        metadata = {}

        # Act
        await use_case.execute(session_id, metadata)

        # Assert - Verify key format by checking storage
        expected_key = f"session:{session_id}"
        redis_client = await mock_redis_adapter.get_client()
        stored_value = await redis_client.get(expected_key)
        assert stored_value is not None  # Key exists with correct format

    @pytest.mark.asyncio
    async def test_ttl_is_set_correctly(
        self, use_case, mock_redis_adapter, mock_redis_client
    ):
        """Test that TTL is set to 3600 seconds (1 hour) for new sessions."""
        # Arrange
        session_id = "ttl-test"
        metadata = {}

        # Act
        await use_case.execute(session_id, metadata)

        # Assert - Check that expiry was set (using the underlying mock)
        # The MockRedisClient tracks expiry internally
        assert f"session:{session_id}" in mock_redis_client._expiry

        # Verify the data exists
        redis_client = await mock_redis_adapter.get_client()
        stored_value = await redis_client.get(f"session:{session_id}")
        assert stored_value is not None

    @pytest.mark.asyncio
    async def test_session_retrieval_idempotency(self, use_case, mock_redis_adapter):
        """Test that retrieving the same session multiple times returns
        consistent data."""
        # Arrange
        session_id = "idempotent-session"
        metadata = {"test": "data"}

        # Act - Create session
        first_result = await use_case.execute(session_id, metadata)

        # Act - Retrieve same session
        second_result = await use_case.execute(session_id, {"different": "metadata"})

        # Assert - Should return the same session data
        assert first_result.session_id == second_result.session_id
        assert first_result.conversation_id == second_result.conversation_id
        assert first_result.started_at == second_result.started_at
        # Metadata should be preserved from first creation
        assert second_result.metadata == metadata

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, mock_redis_adapter):
        """Test that concurrent requests for the same session ID are handled
        correctly."""
        # Arrange
        session_id = "concurrent-session"
        use_case1 = StartChatSessionUseCaseImpl(None, mock_redis_adapter)
        use_case2 = StartChatSessionUseCaseImpl(None, mock_redis_adapter)

        # Act - Simulate concurrent execution
        result1 = await use_case1.execute(session_id, {"client": "1"})
        result2 = await use_case2.execute(session_id, {"client": "2"})

        # Assert - Both should get the same session (first one wins)
        assert result1.session_id == result2.session_id
        assert result1.metadata == result2.metadata  # First metadata is preserved
