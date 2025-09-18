"""Unit tests for ChatOrchestrator service"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.session_dto import SessionDTO
from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.use_cases.interfaces import (
    GetConversationUseCase,
    ProcessUserMessageUseCase,
    StartChatSessionUseCase,
)


@pytest.fixture
def mock_start_session_use_case():
    """Create mock start session use case"""
    mock = create_autospec(StartChatSessionUseCase, spec_set=True)
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_process_message_use_case():
    """Create mock process message use case"""
    mock = create_autospec(ProcessUserMessageUseCase, spec_set=True)
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_get_conversation_use_case():
    """Create mock get conversation use case"""
    mock = create_autospec(GetConversationUseCase, spec_set=True)
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def chat_orchestrator(
    mock_start_session_use_case,
    mock_process_message_use_case,
    mock_get_conversation_use_case,
):
    """Create ChatOrchestrator instance with mocked dependencies"""
    return ChatOrchestrator(
        start_session_use_case=mock_start_session_use_case,
        process_message_use_case=mock_process_message_use_case,
        get_conversation_use_case=mock_get_conversation_use_case,
    )


@pytest.fixture
def sample_session_dto():
    """Create a sample SessionDTO for testing"""
    return SessionDTO(
        session_id="test-session-123",
        conversation_id="conv-456",
        started_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        metadata={"user_agent": "test-browser", "origin": "test-origin"},
    )


@pytest.fixture
def sample_message_dto():
    """Create a sample MessageDTO for testing"""
    return MessageDTO(
        content="This is an AI response",
        sender_type="ai_agent",
        session_id="test-session-123",
        conversation_id="conv-456",
        timestamp=datetime.now(timezone.utc),
        metadata={"model": "gpt-4o-mini"},
    )


@pytest.fixture
def sample_conversation_dto(sample_message_dto):
    """Create a sample ConversationDTO for testing"""
    user_message = MessageDTO(
        content="Hello, I need help",
        sender_type="user",
        session_id="test-session-123",
        conversation_id="conv-456",
        timestamp=datetime.now(timezone.utc),
        metadata={},
    )
    return ConversationDTO(
        id="conv-456",
        session_id="test-session-123",
        messages=[user_message, sample_message_dto],
        started_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
        metadata={"test": "data"},
    )


class TestChatOrchestrator:
    """Test suite for ChatOrchestrator"""

    @pytest.mark.asyncio
    async def test_handle_new_connection_success(
        self,
        chat_orchestrator,
        mock_start_session_use_case,
        sample_session_dto,
    ):
        """Test successful new connection handling"""
        # Arrange
        session_id = "test-session-123"
        metadata = {"user_agent": "test-browser", "origin": "test-origin"}
        mock_start_session_use_case.execute.return_value = sample_session_dto

        # Act
        result = await chat_orchestrator.handle_new_connection(session_id, metadata)

        # Assert
        assert result == sample_session_dto
        mock_start_session_use_case.execute.assert_called_once_with(
            session_id, metadata
        )

    @pytest.mark.asyncio
    async def test_handle_new_connection_failure(
        self,
        chat_orchestrator,
        mock_start_session_use_case,
    ):
        """Test new connection handling when session creation fails"""
        # Arrange
        session_id = "test-session-123"
        metadata = {"user_agent": "test-browser"}
        mock_start_session_use_case.execute.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await chat_orchestrator.handle_new_connection(session_id, metadata)

        assert str(exc_info.value) == "Database error"
        mock_start_session_use_case.execute.assert_called_once_with(
            session_id, metadata
        )

    @pytest.mark.asyncio
    async def test_handle_user_message_success(
        self,
        chat_orchestrator,
        mock_process_message_use_case,
        sample_message_dto,
    ):
        """Test successful user message handling"""
        # Arrange
        session_id = "test-session-123"
        content = "I need help with steel products"
        metadata = {"timestamp": "2024-01-01T10:00:00Z"}
        mock_process_message_use_case.execute.return_value = sample_message_dto

        # Act
        result = await chat_orchestrator.handle_user_message(
            session_id, content, metadata
        )

        # Assert
        assert result == sample_message_dto
        mock_process_message_use_case.execute.assert_called_once_with(
            session_id=session_id, content=content, metadata=metadata
        )

    @pytest.mark.asyncio
    async def test_handle_user_message_without_metadata(
        self,
        chat_orchestrator,
        mock_process_message_use_case,
        sample_message_dto,
    ):
        """Test user message handling without metadata"""
        # Arrange
        session_id = "test-session-123"
        content = "What products do you have?"
        mock_process_message_use_case.execute.return_value = sample_message_dto

        # Act
        result = await chat_orchestrator.handle_user_message(session_id, content)

        # Assert
        assert result == sample_message_dto
        mock_process_message_use_case.execute.assert_called_once_with(
            session_id=session_id, content=content, metadata=None
        )

    @pytest.mark.asyncio
    async def test_handle_user_message_failure_returns_error_message(
        self,
        chat_orchestrator,
        mock_process_message_use_case,
    ):
        """Test user message handling returns Indonesian error message on failure"""
        # Arrange
        session_id = "test-session-123"
        content = "Help me"
        mock_process_message_use_case.execute.side_effect = Exception("AI service down")

        # Act
        result = await chat_orchestrator.handle_user_message(session_id, content)

        # Assert
        assert result.content == "Maaf, terjadi kesalahan. Silakan coba lagi."
        assert result.sender_type == "ai_agent"
        assert result.session_id == session_id
        assert result.conversation_id is None
        assert result.metadata["error"] == "AI service down"
        assert result.metadata["error_type"] == "orchestration_error"

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(
        self,
        chat_orchestrator,
        mock_get_conversation_use_case,
        sample_conversation_dto,
    ):
        """Test successful conversation history retrieval"""
        # Arrange
        session_id = "test-session-123"
        mock_get_conversation_use_case.execute.return_value = sample_conversation_dto

        # Act
        result = await chat_orchestrator.get_conversation_history(session_id)

        # Assert
        assert result == sample_conversation_dto
        assert len(result.messages) == 2
        mock_get_conversation_use_case.execute.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_conversation_history_not_found(
        self,
        chat_orchestrator,
        mock_get_conversation_use_case,
    ):
        """Test conversation history retrieval when no conversation exists"""
        # Arrange
        session_id = "test-session-123"
        mock_get_conversation_use_case.execute.return_value = None

        # Act
        result = await chat_orchestrator.get_conversation_history(session_id)

        # Assert
        assert result is None
        mock_get_conversation_use_case.execute.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_conversation_history_failure_returns_none(
        self,
        chat_orchestrator,
        mock_get_conversation_use_case,
    ):
        """Test conversation history retrieval returns None on failure"""
        # Arrange
        session_id = "test-session-123"
        mock_get_conversation_use_case.execute.side_effect = Exception(
            "Repository error"
        )

        # Act
        result = await chat_orchestrator.get_conversation_history(session_id)

        # Assert
        assert result is None
        mock_get_conversation_use_case.execute.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_handle_session_end(self, chat_orchestrator):
        """Test session end handling"""
        # Arrange
        session_id = "test-session-123"

        # Act
        result = await chat_orchestrator.handle_session_end(session_id)

        # Assert
        assert result is None  # Method currently doesn't return anything

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(
        self,
        mock_start_session_use_case,
        mock_process_message_use_case,
        mock_get_conversation_use_case,
    ):
        """Test ChatOrchestrator initialization with dependencies"""
        # Act
        orchestrator = ChatOrchestrator(
            start_session_use_case=mock_start_session_use_case,
            process_message_use_case=mock_process_message_use_case,
            get_conversation_use_case=mock_get_conversation_use_case,
        )

        # Assert
        assert orchestrator.start_session == mock_start_session_use_case
        assert orchestrator.process_message == mock_process_message_use_case
        assert orchestrator.get_conversation == mock_get_conversation_use_case

    @pytest.mark.asyncio
    async def test_handle_user_message_with_long_content(
        self,
        chat_orchestrator,
        mock_process_message_use_case,
        sample_message_dto,
    ):
        """Test handling user message with long content (logging truncation)"""
        # Arrange
        session_id = "test-session-123"
        content = "A" * 200  # Long message
        mock_process_message_use_case.execute.return_value = sample_message_dto

        # Act
        result = await chat_orchestrator.handle_user_message(session_id, content)

        # Assert
        assert result == sample_message_dto
        mock_process_message_use_case.execute.assert_called_once_with(
            session_id=session_id, content=content, metadata=None
        )

    @pytest.mark.asyncio
    async def test_handle_user_message_with_different_error_types(
        self,
        chat_orchestrator,
        mock_process_message_use_case,
    ):
        """Test error handling for different exception types"""
        # Arrange
        session_id = "test-session-123"
        content = "Test message"
        test_cases = [
            (ValueError("Invalid input"), "ValueError"),
            (KeyError("Missing key"), "KeyError"),
            (RuntimeError("Runtime issue"), "RuntimeError"),
        ]

        for exception, expected_error_type in test_cases:
            # Arrange
            mock_process_message_use_case.execute.side_effect = exception

            # Act
            result = await chat_orchestrator.handle_user_message(session_id, content)

            # Assert
            assert result.content == "Maaf, terjadi kesalahan. Silakan coba lagi."
            assert result.metadata["error_type"] == "orchestration_error"
            assert str(exception) in result.metadata["error"]
