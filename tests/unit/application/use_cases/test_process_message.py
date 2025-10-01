"""Tests for ProcessUserMessageUseCaseImpl using centralized fixtures."""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.message_dto import MessageDTO
from src.application.use_cases.process_message import ProcessUserMessageUseCaseImpl
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)


class TestProcessUserMessageUseCaseImpl:
    """Test suite for ProcessUserMessageUseCaseImpl"""

    @pytest.mark.asyncio
    async def test_process_message_with_new_conversation(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test processing a message when no conversation exists."""
        # Setup mock AI agent response
        mock_ai_agent.generate_response.return_value = "This is an AI response"

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        result = await use_case.execute(
            session_id="test-session-123",
            content="Hello, I need help",
            metadata={"source": "web"},
        )

        # Assert
        assert isinstance(result, MessageDTO)
        assert result.content == "This is an AI response"
        assert result.sender_type == "ai_agent"
        assert result.session_id == "test-session-123"

        # Verify AI agent was called
        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == "Hello, I need help"

        # Verify conversation was saved
        saved_conversation = await mock_conversation_repository.get_by_session(
            "test-session-123"
        )
        assert saved_conversation is not None
        assert saved_conversation.session_id == "test-session-123"
        assert len(saved_conversation.messages) == 2  # User message + AI response

    @pytest.mark.asyncio
    async def test_process_message_with_existing_conversation(
        self,
        mock_ai_agent,
        mock_product_service,
        mock_conversation_repository,
        sample_conversation_with_messages,
    ):
        """Test processing a message with existing conversation history."""
        # Setup
        mock_ai_agent.generate_response.return_value = "This is an AI response"
        await mock_conversation_repository.save(sample_conversation_with_messages)

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        result = await use_case.execute(
            session_id="test-session-123", content="What about product pricing?"
        )

        # Assert
        assert result.content == "This is an AI response"
        assert result.sender_type == "ai_agent"

        # Verify agent was called with context
        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == "What about product pricing?"
        assert mock_ai_agent.last_context is not None
        assert len(mock_ai_agent.last_context) == 2  # Previous 2 messages

    @pytest.mark.asyncio
    async def test_process_message_with_pydantic_agent(
        self, mock_pydantic_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test processing a message with PydanticAI agent."""
        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_pydantic_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        result = await use_case.execute(
            session_id="test-session-123", content="Show me steel products"
        )

        # Assert
        assert result.content == "This is a PydanticAI response"
        assert result.sender_type == "ai_agent"

        # Verify PydanticAI agent's run method was called
        mock_pydantic_ai_agent.run.assert_called_once()
        call_args = mock_pydantic_ai_agent.run.call_args
        assert call_args[1]["message"] == "Show me steel products"
        assert "conversation_context" in call_args[1]

    @pytest.mark.asyncio
    async def test_process_message_with_error_returns_indonesian_message(
        self, mock_product_service, mock_conversation_repository
    ):
        """Test that errors return Indonesian error messages."""
        # Arrange - Create an agent that raises an error
        # (with no run attribute to trigger AIAgentPort path)
        mock_ai_agent = AsyncMock()
        mock_ai_agent.generate_response = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        # Ensure it doesn't have a run attribute so it uses the AIAgentPort path
        delattr(mock_ai_agent, "run")

        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        result = await use_case.execute(
            session_id="test-session-123", content="Test message"
        )

        # Assert
        assert (
            result.content
            == "Maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi."
        )
        assert result.sender_type == "ai_agent"
        assert "error" in result.metadata
        assert result.metadata["error"] == "Connection failed"
        assert result.metadata["error_type"] == "Exception"

    @pytest.mark.asyncio
    async def test_conversation_context_limits_to_4_messages(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test that conversation context is limited to last 4 messages."""
        # Setup mock
        mock_ai_agent.generate_response.return_value = "AI response"

        # Arrange - Create conversation with 6 messages
        conversation = Conversation(session_id="test-session-123")
        for i in range(6):
            sender_type = "user" if i % 2 == 0 else "ai_agent"
            conversation.add_message(
                Message(
                    conversation_id=conversation.id,
                    sender_type=sender_type,
                    content=f"Message {i}",
                    metadata={},
                )
            )
        await mock_conversation_repository.save(conversation)

        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        await use_case.execute(session_id="test-session-123", content="New message")

        # Assert
        assert mock_ai_agent.call_count == 1
        context = mock_ai_agent.last_context

        # Should have last 4 messages from the 6 existing ones
        assert len(context) == 4
        assert context[0].content == "Message 2"
        assert context[-1].content == "Message 5"

    @pytest.mark.asyncio
    async def test_metadata_is_preserved_in_messages(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test that metadata is properly preserved in messages."""
        # Setup
        mock_ai_agent.generate_response.return_value = "AI response"

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        test_metadata = {
            "user_agent": "test-browser",
            "ip": "192.168.1.1",
            "session_type": "web",
        }

        # Act
        result = await use_case.execute(
            session_id="test-session-123",
            content="Test with metadata",
            metadata=test_metadata,
        )

        # Assert
        assert result.sender_type == "ai_agent"

        # Check that AI response has metadata
        assert "model" in result.metadata
        assert result.metadata["model"] == "gpt-4o-mini"
        assert "context_used" in result.metadata

        # Verify conversation was saved with metadata
        saved_conversation = await mock_conversation_repository.get_by_session(
            "test-session-123"
        )
        assert saved_conversation is not None

        # Check user message has the original metadata
        user_message = saved_conversation.messages[0]
        assert user_message.metadata == test_metadata

    @pytest.mark.asyncio
    async def test_session_id_passed_correctly_to_dto(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test that session_id is correctly passed to MessageDTO."""
        # Setup
        mock_ai_agent.generate_response.return_value = "AI response"

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        test_session_id = "unique-session-456"

        # Act
        result = await use_case.execute(
            session_id=test_session_id, content="Check session handling"
        )

        # Assert
        assert result.session_id == test_session_id
        assert result.conversation_id is not None

    @pytest.mark.asyncio
    async def test_conversation_repository_save_called_after_processing(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test that conversation is saved after processing."""
        # Setup
        mock_ai_agent.generate_response.return_value = "AI response"

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        await use_case.execute(
            session_id="test-session-123", content="Test save operation"
        )

        # Assert - Retrieve the saved conversation
        saved_conversation = await mock_conversation_repository.get_by_session(
            "test-session-123"
        )
        assert saved_conversation is not None

        # Verify the conversation has both messages
        assert len(saved_conversation.messages) == 2
        assert saved_conversation.messages[0].content == "Test save operation"
        assert saved_conversation.messages[0].sender_type == "user"
        assert saved_conversation.messages[1].content == "AI response"
        assert saved_conversation.messages[1].sender_type == "ai_agent"

    @pytest.mark.asyncio
    async def test_ai_agent_port_pattern_with_message_dto_context(
        self, mock_ai_agent, mock_product_service, sample_conversation_with_messages
    ):
        """Test that AIAgentPort pattern correctly converts context to MessageDTOs."""
        # Setup
        mock_ai_agent.generate_response.return_value = "Test response"

        # Create repository and save existing conversation
        repository = InMemoryConversationRepository()
        await repository.save(sample_conversation_with_messages)

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=repository,
        )

        # Act
        await use_case.execute(
            session_id="test-session-123", content="New user message"
        )

        # Assert
        assert mock_ai_agent.call_count == 1

        # Verify context was converted to MessageDTOs
        context = mock_ai_agent.last_context
        assert context is not None
        assert all(isinstance(msg, MessageDTO) for msg in context)
        assert len(context) == 2  # Previous messages

        # Verify DTOs have correct data
        assert context[0].content == "Previous user message"
        assert context[0].sender_type == "user"
        assert context[1].content == "Previous AI response"
        assert context[1].sender_type == "ai_agent"

    @pytest.mark.asyncio
    async def test_no_metadata_provided_uses_empty_dict(
        self, mock_ai_agent, mock_product_service, mock_conversation_repository
    ):
        """Test that when no metadata is provided, empty dict is used."""
        # Setup
        mock_ai_agent.generate_response.return_value = "AI response"

        # Arrange
        use_case = ProcessUserMessageUseCaseImpl(
            chat_agent=mock_ai_agent,
            product_service=mock_product_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act - Call without metadata
        result = await use_case.execute(
            session_id="test-session-123", content="Message without metadata"
        )

        # Assert
        assert result.sender_type == "ai_agent"

        # Verify conversation was saved
        saved_conversation = await mock_conversation_repository.get_by_session(
            "test-session-123"
        )

        # Check user message has empty metadata dict
        user_message = saved_conversation.messages[0]
        assert user_message.metadata == {}
