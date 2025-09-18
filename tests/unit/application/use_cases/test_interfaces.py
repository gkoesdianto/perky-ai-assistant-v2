"""Tests for use case interfaces using centralized mock implementations from conftest."""

import pytest

from src.application.use_cases.interfaces import (
    GetConversationUseCase,
    ProcessUserMessageUseCase,
    StartChatSessionUseCase,
)


@pytest.mark.asyncio
class TestStartChatSessionUseCase:
    async def test_can_create_concrete_implementation(self, mock_start_chat_session):
        """Test that mock implementation is properly instantiated."""
        assert isinstance(mock_start_chat_session, StartChatSessionUseCase)

    async def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            StartChatSessionUseCase()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    async def test_execute_method_signature(
        self, mock_start_chat_session, sample_session_dto
    ):
        """Test execute method with proper signature."""
        mock_start_chat_session.execute_mock.return_value = sample_session_dto

        result = await mock_start_chat_session.execute("session-123", {"user": "test"})

        assert result == sample_session_dto
        mock_start_chat_session.execute_mock.assert_called_once_with(
            "session-123", {"user": "test"}
        )

    async def test_missing_execute_method_raises_error(self):
        """Test that missing execute method raises TypeError."""

        class IncompleteUseCase(StartChatSessionUseCase):
            pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteUseCase()
        assert "Can't instantiate abstract class" in str(exc_info.value)
        assert "execute" in str(exc_info.value)

    async def test_call_tracking(self, mock_start_chat_session, sample_session_dto):
        """Test that mock tracks calls properly."""
        mock_start_chat_session.execute_mock.return_value = sample_session_dto

        await mock_start_chat_session.execute("session-1", {"test": "data"})
        await mock_start_chat_session.execute("session-2", {"other": "data"})

        assert mock_start_chat_session.call_count == 2
        assert mock_start_chat_session.last_call_args["session_id"] == "session-2"


@pytest.mark.asyncio
class TestProcessUserMessageUseCase:
    async def test_can_create_concrete_implementation(self, mock_process_message):
        """Test that mock implementation is properly instantiated."""
        assert isinstance(mock_process_message, ProcessUserMessageUseCase)

    async def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            ProcessUserMessageUseCase()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    async def test_execute_method_with_metadata(
        self, mock_process_message, sample_message_dto
    ):
        """Test execute method with metadata."""
        mock_process_message.execute_mock.return_value = sample_message_dto

        result = await mock_process_message.execute(
            "session-123", "Hello", {"context": "product_inquiry"}
        )

        assert result == sample_message_dto
        mock_process_message.execute_mock.assert_called_once_with(
            "session-123", "Hello", {"context": "product_inquiry"}
        )

    async def test_execute_method_without_metadata(
        self, mock_process_message, sample_message_dto
    ):
        """Test execute method without metadata."""
        mock_process_message.execute_mock.return_value = sample_message_dto

        result = await mock_process_message.execute("session-123", "Hello")

        assert result == sample_message_dto
        mock_process_message.execute_mock.assert_called_once_with(
            "session-123", "Hello", None
        )

    async def test_execute_method_with_none_metadata(
        self, mock_process_message, sample_message_dto
    ):
        """Test execute method with explicit None metadata."""
        mock_process_message.execute_mock.return_value = sample_message_dto

        result = await mock_process_message.execute("session-123", "Hello", None)

        assert result == sample_message_dto
        mock_process_message.execute_mock.assert_called_once_with(
            "session-123", "Hello", None
        )

    async def test_call_tracking(self, mock_process_message, sample_message_dto):
        """Test that mock tracks calls properly."""
        mock_process_message.execute_mock.return_value = sample_message_dto

        await mock_process_message.execute("session-1", "Message 1")
        await mock_process_message.execute("session-2", "Message 2", {"meta": "data"})

        assert mock_process_message.call_count == 2
        assert mock_process_message.last_call_args["content"] == "Message 2"


@pytest.mark.asyncio
class TestGetConversationUseCase:
    async def test_can_create_concrete_implementation(self, mock_get_conversation):
        """Test that mock implementation is properly instantiated."""
        assert isinstance(mock_get_conversation, GetConversationUseCase)

    async def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            GetConversationUseCase()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    async def test_execute_returns_conversation(
        self, mock_get_conversation, sample_conversation_dto
    ):
        """Test execute returns conversation when found."""
        mock_get_conversation.execute_mock.return_value = sample_conversation_dto

        result = await mock_get_conversation.execute("session-123")

        assert result == sample_conversation_dto
        mock_get_conversation.execute_mock.assert_called_once_with("session-123")

    async def test_execute_returns_none_for_missing_conversation(
        self, mock_get_conversation
    ):
        """Test execute returns None when conversation not found."""
        mock_get_conversation.execute_mock.return_value = None

        result = await mock_get_conversation.execute("non-existent-session")

        assert result is None
        mock_get_conversation.execute_mock.assert_called_once_with(
            "non-existent-session"
        )

    async def test_call_tracking(self, mock_get_conversation, sample_conversation_dto):
        """Test that mock tracks calls properly."""
        mock_get_conversation.execute_mock.return_value = sample_conversation_dto

        await mock_get_conversation.execute("session-1")
        await mock_get_conversation.execute("session-2")
        await mock_get_conversation.execute("session-3")

        assert mock_get_conversation.call_count == 3
        assert mock_get_conversation.last_call_args["session_id"] == "session-3"


class TestUseCaseInterfaceIntegration:
    def test_all_use_cases_are_abstract(self):
        """Test that all use case classes are properly abstract."""
        abstract_classes = [
            StartChatSessionUseCase,
            ProcessUserMessageUseCase,
            GetConversationUseCase,
        ]

        for cls in abstract_classes:
            assert hasattr(cls, "__abstractmethods__")
            assert len(cls.__abstractmethods__) > 0
            assert "execute" in cls.__abstractmethods__

    def test_use_case_inheritance_chain(self):
        """Test that use cases inherit from ABC."""
        from abc import ABC

        assert issubclass(StartChatSessionUseCase, ABC)
        assert issubclass(ProcessUserMessageUseCase, ABC)
        assert issubclass(GetConversationUseCase, ABC)
