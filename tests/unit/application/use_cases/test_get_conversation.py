"""Tests for GetConversationUseCaseImpl"""

import pytest

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.use_cases.get_conversation import GetConversationUseCaseImpl


class TestGetConversationUseCaseImpl:
    """
    Test suite for GetConversationUseCaseImpl.

    This test suite validates the behavior of the Get Conversation use case,
    including conversation retrieval, DTO conversion, and error handling.
    """

    @pytest.fixture
    def use_case(self, mock_conversation_repository_async):
        """
        Create a GetConversationUseCaseImpl instance with mocked dependencies.

        Args:
            mock_conversation_repository_async: Mock repository from conftest.py

        Returns:
            GetConversationUseCaseImpl: The use case instance for testing
        """
        return GetConversationUseCaseImpl(
            conversation_repository=mock_conversation_repository_async
        )

    @pytest.mark.asyncio
    async def test_execute_with_existing_conversation(
        self, use_case, mock_conversation_repository_async, sample_conversation_detailed
    ):
        """Test that existing conversation is retrieved and converted to DTO."""
        # Arrange
        session_id = "session-456"
        mock_conversation_repository_async.get_by_session.return_value = (
            sample_conversation_detailed
        )

        # Act
        result = await use_case.execute(session_id)

        # Assert - Verify returned DTO
        assert isinstance(result, ConversationDTO)
        assert result.id == "conv-123"
        assert result.session_id == session_id
        assert len(result.messages) == 2
        assert result.started_at == sample_conversation_detailed.started_at
        assert result.last_activity == sample_conversation_detailed.last_activity
        assert result.metadata == {"source": "web", "user_agent": "test-browser"}

        # Assert - Verify message conversion
        assert isinstance(result.messages[0], MessageDTO)
        assert result.messages[0].content == "Hello, I need help with steel products"
        assert result.messages[0].sender_type == "user"
        assert result.messages[0].session_id == session_id
        assert result.messages[0].conversation_id == "conv-123"
        assert result.messages[0].metadata == {"language": "en"}

        assert isinstance(result.messages[1], MessageDTO)
        assert (
            result.messages[1].content
            == "Hello! I'd be happy to help you with steel products."
        )
        assert result.messages[1].sender_type == "ai_agent"

        # Verify repository was called correctly
        mock_conversation_repository_async.get_by_session.assert_called_once_with(
            session_id
        )

    @pytest.mark.asyncio
    async def test_execute_with_no_conversation(
        self, use_case, mock_conversation_repository_async
    ):
        """Test that None is returned when no conversation exists."""
        # Arrange
        session_id = "non-existent-session"
        mock_conversation_repository_async.get_by_session.return_value = None

        # Act
        result = await use_case.execute(session_id)

        # Assert
        assert result is None
        mock_conversation_repository_async.get_by_session.assert_called_once_with(
            session_id
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_messages(
        self, use_case, mock_conversation_repository_async, sample_conversation_empty
    ):
        """Test conversation with no messages."""
        # Arrange
        session_id = "session-empty"
        mock_conversation_repository_async.get_by_session.return_value = (
            sample_conversation_empty
        )

        # Act
        result = await use_case.execute(session_id)

        # Assert
        assert isinstance(result, ConversationDTO)
        assert result.id == "conv-empty"
        assert result.session_id == session_id
        assert len(result.messages) == 0
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_execute_with_metadata_none(
        self, use_case, mock_conversation_repository_async
    ):
        """Test that None metadata is handled gracefully."""
        # Arrange
        from src.domain.entities.conversation import Conversation
        from datetime import datetime, timezone

        session_id = "session-no-metadata"
        conversation = Conversation(
            id="conv-no-meta",
            session_id=session_id,
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            last_activity=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        # Explicitly set metadata to None to test handling
        conversation.metadata = None
        mock_conversation_repository_async.get_by_session.return_value = conversation

        # Act
        result = await use_case.execute(session_id)

        # Assert
        assert isinstance(result, ConversationDTO)
        assert result.metadata == {}  # Should default to empty dict

    @pytest.mark.asyncio
    async def test_execute_repository_error_propagates(
        self, use_case, mock_conversation_repository_async
    ):
        """Test that repository errors are propagated correctly."""
        # Arrange
        session_id = "session-error"
        mock_conversation_repository_async.get_by_session.side_effect = Exception(
            "Database connection error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(session_id)

        assert str(exc_info.value) == "Database connection error"
        mock_conversation_repository_async.get_by_session.assert_called_once_with(
            session_id
        )

    @pytest.mark.asyncio
    async def test_message_conversion_preserves_all_fields(
        self, use_case, mock_conversation_repository_async
    ):
        """Test that all message fields are preserved during DTO conversion."""
        # Arrange
        from src.domain.entities.conversation import Conversation
        from src.domain.entities.message import Message
        from datetime import datetime, timezone

        session_id = "session-detailed"
        conversation = Conversation(
            id="conv-detailed",
            session_id=session_id,
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            last_activity=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        )

        message = Message(
            id="msg-detailed",
            content="Test message with all fields",
            sender_type="user",
            conversation_id="conv-detailed",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            metadata={"key1": "value1", "key2": 123, "key3": True},
        )
        conversation.messages = [message]
        mock_conversation_repository_async.get_by_session.return_value = conversation

        # Act
        result = await use_case.execute(session_id)

        # Assert - Verify all fields are preserved
        assert result.messages[0].content == "Test message with all fields"
        assert result.messages[0].sender_type == "user"
        assert result.messages[0].session_id == session_id
        assert result.messages[0].conversation_id == "conv-detailed"
        assert result.messages[0].timestamp == message.created_at
        assert result.messages[0].metadata == {
            "key1": "value1",
            "key2": 123,
            "key3": True,
        }

    @pytest.mark.asyncio
    async def test_multiple_messages_ordering(
        self,
        use_case,
        mock_conversation_repository_async,
        sample_conversation_many_messages,
    ):
        """Test that message ordering is preserved in the DTO."""
        # Arrange
        session_id = "session-ordered"
        mock_conversation_repository_async.get_by_session.return_value = (
            sample_conversation_many_messages
        )

        # Act
        result = await use_case.execute(session_id)

        # Assert - Verify ordering is preserved
        assert len(result.messages) == 5
        for i, msg_dto in enumerate(result.messages):
            assert msg_dto.content == f"Message {i}"
            assert msg_dto.sender_type == ("user" if i % 2 == 0 else "ai_agent")

    @pytest.mark.asyncio
    async def test_conversation_with_existing_messages(
        self,
        use_case,
        mock_conversation_repository_async,
        sample_conversation_with_messages,
    ):
        """Test using the standard conversation with messages fixture."""
        # Arrange
        session_id = "test-session-123"
        mock_conversation_repository_async.get_by_session.return_value = (
            sample_conversation_with_messages
        )

        # Act
        result = await use_case.execute(session_id)

        # Assert
        assert isinstance(result, ConversationDTO)
        assert result.session_id == session_id
        assert len(result.messages) == 2
        assert result.messages[0].content == "Previous user message"
        assert result.messages[1].content == "Previous AI response"
        assert result.metadata == {"test": "data"}
