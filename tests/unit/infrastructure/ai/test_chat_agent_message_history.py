"""Unit tests for ChatAgent message history conversion."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse

from src.application.dto import MessageDTO
from src.infrastructure.ai.chat_agent import ChatAgent

# Use chat_agent_with_mocked_llm fixture from conftest.py for ChatAgent instance
# Use mock_product_service fixture from conftest.py for product service


def test_convert_empty_context(chat_agent_with_mocked_llm):
    """Test conversion of empty conversation context."""
    chat_agent = chat_agent_with_mocked_llm
    result = chat_agent._convert_dto_to_model_messages([])
    assert result == []


def test_convert_single_user_message(chat_agent_with_mocked_llm):
    """Test conversion of single user message."""
    chat_agent = chat_agent_with_mocked_llm
    # Create MessageDTO directly (as production code does)
    dto = MessageDTO(
        content="Hello",
        sender_type="user",
        session_id="test-session",
        conversation_id="test-conv",
        timestamp=datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
    )

    result = chat_agent._convert_dto_to_model_messages([dto])

    assert len(result) == 1
    assert isinstance(result[0], ModelRequest)
    assert result[0].parts[0].content == "Hello"


def test_convert_single_ai_message(chat_agent_with_mocked_llm):
    """Test conversion of single AI message."""
    chat_agent = chat_agent_with_mocked_llm
    dto = MessageDTO(
        content="Hello! How can I help?",
        sender_type="ai_agent",
        session_id="test-session",
        conversation_id="test-conv",
        timestamp=datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
    )

    result = chat_agent._convert_dto_to_model_messages([dto])

    assert len(result) == 1
    assert isinstance(result[0], ModelResponse)
    assert result[0].parts[0].content == "Hello! How can I help?"


def test_convert_user_ai_sequence(chat_agent_with_mocked_llm):
    """Test conversion of user-AI message sequence."""
    chat_agent = chat_agent_with_mocked_llm
    # Create MessageDTO objects directly
    dtos = [
        MessageDTO(
            content="What is the weather?",
            sender_type="user",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        ),
        MessageDTO(
            content="It's sunny today.",
            sender_type="ai_agent",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=datetime(2025, 9, 30, 12, 1, 0, tzinfo=timezone.utc),
        ),
    ]

    result = chat_agent._convert_dto_to_model_messages(dtos)

    assert len(result) == 2
    assert isinstance(result[0], ModelRequest)
    assert isinstance(result[1], ModelResponse)
    assert result[0].parts[0].content == "What is the weather?"
    assert result[1].parts[0].content == "It's sunny today."


def test_limits_to_last_10_messages(chat_agent_with_mocked_llm):
    """Test that conversion limits to last 10 messages."""
    chat_agent = chat_agent_with_mocked_llm
    # Create 15 MessageDTO objects
    base_time = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    dtos = [
        MessageDTO(
            content=f"Message {i}",
            sender_type="user" if i % 2 == 0 else "ai_agent",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        )
        for i in range(15)
    ]

    result = chat_agent._convert_dto_to_model_messages(dtos)

    assert len(result) == 10
    # Should have last 10 messages (indices 5-14)
    assert result[0].parts[0].content == "Message 5"
    assert result[-1].parts[0].content == "Message 14"


def test_mixed_user_ai_messages(chat_agent_with_mocked_llm):
    """Test conversion of mixed user and AI messages."""
    chat_agent = chat_agent_with_mocked_llm
    base_time = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    dtos = [
        MessageDTO(
            content="User 1",
            sender_type="user",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
        MessageDTO(
            content="AI 1",
            sender_type="ai_agent",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
        MessageDTO(
            content="User 2",
            sender_type="user",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
        MessageDTO(
            content="AI 2",
            sender_type="ai_agent",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
    ]

    result = chat_agent._convert_dto_to_model_messages(dtos)

    assert len(result) == 4
    assert isinstance(result[0], ModelRequest)  # User 1
    assert isinstance(result[1], ModelResponse)  # AI 1
    assert isinstance(result[2], ModelRequest)  # User 2
    assert isinstance(result[3], ModelResponse)  # AI 2


def test_preserves_timestamps(chat_agent_with_mocked_llm):
    """Test that timestamps are preserved in conversion."""
    chat_agent = chat_agent_with_mocked_llm
    test_timestamp = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    dto = MessageDTO(
        content="Test message",
        sender_type="user",
        session_id="test-session",
        conversation_id="test-conv",
        timestamp=test_timestamp,
    )

    result = chat_agent._convert_dto_to_model_messages([dto])

    assert len(result) == 1
    assert result[0].parts[0].timestamp == test_timestamp


@pytest.mark.asyncio
async def test_multi_turn_conversation(
    chat_agent_with_mocked_llm, mock_product_service
):
    """Integration test: Multi-turn conversation works correctly."""
    chat_agent = chat_agent_with_mocked_llm

    # Configure mock to return proper result objects
    mock_result = MagicMock()
    mock_result.data = "Mock AI response"
    chat_agent.agent.run.return_value = mock_result

    # First message
    response1 = await chat_agent.generate_response(
        message="Hello",
        conversation_context=None,
        product_service=mock_product_service,
        session_id="test-session",
    )
    assert response1  # Should get greeting

    # Build conversation context using MessageDTO
    base_time = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    context = [
        MessageDTO(
            content="Hello",
            sender_type="user",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
        MessageDTO(
            content=response1,
            sender_type="ai_agent",
            session_id="test-session",
            conversation_id="test-conv",
            timestamp=base_time,
        ),
    ]

    # Second message - should NOT fail
    response2 = await chat_agent.generate_response(
        message="What products do you have?",
        conversation_context=context,
        product_service=mock_product_service,
        session_id="test-session",
    )
    assert response2
    assert isinstance(response2, str)
    assert "error" not in response2.lower()  # Should not be error message
    assert "sistem" not in response2.lower()  # Should not be system error


@pytest.mark.asyncio
async def test_three_turn_conversation(
    chat_agent_with_mocked_llm, mock_product_service
):
    """Test three-turn conversation to ensure context continuity."""
    chat_agent = chat_agent_with_mocked_llm
    conversation_history = []
    base_time = datetime(2025, 9, 30, 12, 0, 0, tzinfo=timezone.utc)

    # Configure mock to return proper result objects
    mock_result = MagicMock()
    mock_result.data = "Mock AI response for turn"
    chat_agent.agent.run.return_value = mock_result

    # Turn 1
    response1 = await chat_agent.generate_response(
        message="Hello",
        conversation_context=conversation_history,
        product_service=mock_product_service,
        session_id="test-session",
    )
    assert response1

    conversation_history.extend(
        [
            MessageDTO(
                content="Hello",
                sender_type="user",
                session_id="test-session",
                conversation_id="test-conv",
                timestamp=base_time,
            ),
            MessageDTO(
                content=response1,
                sender_type="ai_agent",
                session_id="test-session",
                conversation_id="test-conv",
                timestamp=base_time,
            ),
        ]
    )

    # Turn 2
    response2 = await chat_agent.generate_response(
        message="Do you have steel products?",
        conversation_context=conversation_history,
        product_service=mock_product_service,
        session_id="test-session",
    )
    assert response2
    assert isinstance(response2, str)
    assert "error" not in response2.lower()

    conversation_history.extend(
        [
            MessageDTO(
                content="Do you have steel products?",
                sender_type="user",
                session_id="test-session",
                conversation_id="test-conv",
                timestamp=base_time,
            ),
            MessageDTO(
                content=response2,
                sender_type="ai_agent",
                session_id="test-session",
                conversation_id="test-conv",
                timestamp=base_time,
            ),
        ]
    )

    # Turn 3
    response3 = await chat_agent.generate_response(
        message="Tell me more",
        conversation_context=conversation_history,
        product_service=mock_product_service,
        session_id="test-session",
    )
    assert response3
    assert isinstance(response3, str)
    assert "error" not in response3.lower()
