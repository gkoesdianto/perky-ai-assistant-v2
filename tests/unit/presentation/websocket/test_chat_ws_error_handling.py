"""
Unit tests for ChatWebSocket error handling and edge cases.

Tests the enhanced error handling, queue health checks, and rate limiting
implemented to fix the silent message failure bug.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.presentation.websocket.chat_ws import ChatWebSocket
from src.presentation.websocket.types import MessageType, WebSocketMessage


@pytest.fixture
def mock_chat_orchestrator():
    """Mock chat orchestrator."""
    orchestrator = AsyncMock()
    orchestrator.handle_user_message = AsyncMock()
    orchestrator.handle_new_connection = AsyncMock()
    orchestrator.get_conversation_history = AsyncMock(return_value=None)
    return orchestrator


@pytest.fixture
def mock_connection_manager():
    """Mock connection manager."""
    manager = Mock()
    manager.connect = AsyncMock(return_value=True)
    manager.disconnect = AsyncMock()
    manager.send_message = AsyncMock(return_value=True)
    manager.is_connected = Mock(return_value=True)
    return manager


@pytest.fixture
def mock_session_manager():
    """Mock session manager."""
    manager = AsyncMock()
    manager.add_connection = AsyncMock()
    manager.remove_connection = AsyncMock()
    manager.get_session_connections = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_message_queue():
    """Mock message queue."""
    queue = Mock()
    queue.add_message = AsyncMock(return_value=True)
    queue.is_running = True
    queue.is_full = Mock(return_value=False)
    queue.get_queue_size = Mock(return_value=0)
    queue.start_worker = AsyncMock()
    return queue


@pytest.fixture
def mock_message_validator():
    """Mock message validator."""
    validator = Mock()
    validator.validate_user_message = Mock(return_value=(True, None))
    validator.sanitize_message = Mock(side_effect=lambda x: x)
    return validator


@pytest.fixture
def mock_message_rate_limiter():
    """Mock message rate limiter."""
    limiter = Mock()
    limiter.is_allowed = Mock(return_value=(True, None))
    limiter.reset_connection = Mock()
    return limiter


@pytest.fixture
def chat_websocket(
    mock_chat_orchestrator,
    mock_connection_manager,
    mock_session_manager,
    mock_message_queue,
    mock_message_validator,
    mock_message_rate_limiter,
):
    """Create ChatWebSocket instance with mocked dependencies."""
    return ChatWebSocket(
        chat_orchestrator=mock_chat_orchestrator,
        connection_manager=mock_connection_manager,
        session_manager=mock_session_manager,
        message_queue=mock_message_queue,
        message_validator=mock_message_validator,
        message_rate_limiter=mock_message_rate_limiter,
    )


class TestErrorHandling:
    """Test error handling in message processing."""

    @pytest.mark.asyncio
    async def test_handle_user_message_validation_failure(
        self, chat_websocket, mock_message_validator
    ):
        """Test that validation failures send proper error messages."""
        # Setup: validation fails
        mock_message_validator.validate_user_message.return_value = (
            False,
            "Pesan terlalu pendek",
        )

        message = WebSocketMessage(type="user_message", message="hi")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent, message not queued
        chat_websocket.connection_manager.send_message.assert_called_once()
        error_call = chat_websocket.connection_manager.send_message.call_args[0]
        assert "Pesan terlalu pendek" in str(error_call)
        chat_websocket.message_queue.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_user_message_rate_limit_exceeded(
        self, chat_websocket, mock_message_rate_limiter
    ):
        """Test that rate limit rejections send proper error messages."""
        # Setup: rate limit exceeded
        mock_message_rate_limiter.is_allowed.return_value = (
            False,
            "Terlalu banyak pesan sekaligus",
        )

        message = WebSocketMessage(type="user_message", message="test message")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent, message not queued
        chat_websocket.connection_manager.send_message.assert_called()
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("Terlalu banyak pesan" in str(call) for call in error_calls)
        chat_websocket.message_queue.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_user_message_queue_full(
        self, chat_websocket, mock_message_queue
    ):
        """Test that queue full condition sends proper error message."""
        # Setup: queue is full
        mock_message_queue.is_full.return_value = True
        mock_message_queue.get_queue_size.return_value = 100

        message = WebSocketMessage(type="user_message", message="test message")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent, message not queued
        chat_websocket.connection_manager.send_message.assert_called()
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("sibuk" in str(call).lower() for call in error_calls)
        mock_message_queue.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_user_message_worker_not_running(
        self, chat_websocket, mock_message_queue
    ):
        """Test that stopped worker sends proper error message."""
        # Setup: worker is not running
        mock_message_queue.is_running = False

        message = WebSocketMessage(type="user_message", message="test message")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent, message not queued
        chat_websocket.connection_manager.send_message.assert_called()
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("pemeliharaan" in str(call).lower() for call in error_calls)
        mock_message_queue.add_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_user_message_unexpected_exception(
        self, chat_websocket, mock_message_validator
    ):
        """Test that unexpected exceptions are caught and error message sent."""
        # Setup: validator raises unexpected exception
        mock_message_validator.validate_user_message.side_effect = RuntimeError(
            "Unexpected error"
        )

        message = WebSocketMessage(type="user_message", message="test message")

        # Execute - should not raise exception
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent
        chat_websocket.connection_manager.send_message.assert_called()
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("kesalahan" in str(call).lower() for call in error_calls)

    @pytest.mark.asyncio
    async def test_handle_user_message_successful_path(
        self, chat_websocket, mock_message_queue
    ):
        """Test successful message handling path."""
        # Setup: all validations pass
        message = WebSocketMessage(type="user_message", message="test message")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Message queued successfully
        mock_message_queue.add_message.assert_called_once()
        message_data = mock_message_queue.add_message.call_args[0][0]
        assert message_data["connection_id"] == "test-conn"
        assert message_data["session_id"] == "test-session"
        assert message_data["content"] == "test message"

    @pytest.mark.asyncio
    async def test_handle_user_message_queue_add_fails(
        self, chat_websocket, mock_message_queue
    ):
        """Test handling when queue refuses to accept message."""
        # Setup: queue add fails
        mock_message_queue.add_message.return_value = False

        message = WebSocketMessage(type="user_message", message="test message")

        # Execute
        await chat_websocket._handle_user_message(
            connection_id="test-conn",
            session_id="test-session",
            message=message,
        )

        # Verify: Error message sent
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        # Should have typing indicator and error message
        assert len(error_calls) >= 2


class TestQueueProcessing:
    """Test queue message processing with error handling."""

    @pytest.mark.asyncio
    async def test_process_queued_message_success(
        self, chat_websocket, mock_chat_orchestrator
    ):
        """Test successful queue message processing."""
        # Setup
        mock_response = Mock()
        mock_response.content = "AI response"
        mock_response.metadata = {}
        mock_response.timestamp = datetime.now()
        mock_chat_orchestrator.handle_user_message.return_value = mock_response

        message_data = {
            "connection_id": "test-conn",
            "session_id": "test-session",
            "content": "test message",
            "metadata": {},
        }

        # Execute
        await chat_websocket._process_queued_message(message_data)

        # Verify: Response sent to connection
        chat_websocket.connection_manager.send_message.assert_called()
        response_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("AI response" in str(call) for call in response_calls)

    @pytest.mark.asyncio
    async def test_process_queued_message_orchestrator_failure(
        self, chat_websocket, mock_chat_orchestrator
    ):
        """Test error handling when orchestrator fails."""
        # Setup: orchestrator raises exception
        mock_chat_orchestrator.handle_user_message.side_effect = RuntimeError(
            "Processing failed"
        )

        message_data = {
            "connection_id": "test-conn",
            "session_id": "test-session",
            "content": "test message",
            "metadata": {},
        }

        # Execute - should not raise exception
        await chat_websocket._process_queued_message(message_data)

        # Verify: Error message sent to connection
        chat_websocket.connection_manager.send_message.assert_called()
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("kesalahan" in str(call).lower() for call in error_calls)


class TestRateLimiterEdgeCases:
    """Test rate limiter edge cases that could cause silent failures."""

    def test_rate_limiter_burst_limit_exactly_5_messages(self):
        """Test burst limit with exactly 5 messages in 5 seconds."""
        from src.presentation.websocket.message_handler import MessageRateLimiter

        limiter = MessageRateLimiter(max_burst_size=5)
        connection_id = "test-conn"

        # Send 5 messages
        for i in range(5):
            is_allowed, error = limiter.is_allowed(connection_id)
            assert is_allowed, f"Message {i+1} should be allowed"

        # 6th message should be rejected
        is_allowed, error = limiter.is_allowed(connection_id)
        assert not is_allowed, "6th message should be rejected by burst limit"
        assert "sekaligus" in error.lower()

    def test_rate_limiter_burst_limit_with_time_gaps(self):
        """Test burst limit with time gaps between messages."""
        from src.presentation.websocket.message_handler import MessageRateLimiter

        limiter = MessageRateLimiter(max_burst_size=5)
        connection_id = "test-conn"

        # Mock datetime to control timing
        with patch(
            "src.presentation.websocket.message_handler.datetime"
        ) as mock_datetime:
            base_time = datetime(2025, 1, 1, 12, 0, 0)

            # Send 6 messages with 5-second gaps
            for i in range(6):
                mock_datetime.now.return_value = base_time.replace(second=i * 5)
                is_allowed, error = limiter.is_allowed(connection_id)

                # All should be allowed because old messages are cleaned up
                assert is_allowed, (
                    f"Message {i+1} at {i*5}s should be allowed "
                    f"(burst window cleans up old messages)"
                )

    def test_rate_limiter_exception_handling(self):
        """Test that rate limiter exceptions don't cause silent failures."""
        from src.presentation.websocket.message_handler import MessageRateLimiter

        limiter = MessageRateLimiter()
        connection_id = "test-conn"

        # Corrupt internal state
        limiter.burst_tracker[connection_id] = "not a list"  # Invalid type

        # Should handle gracefully and fail open
        is_allowed, error = limiter.is_allowed(connection_id)

        # Should allow (fail open) but log error
        assert is_allowed, "Should fail open on internal error"


class TestMultiTurnConversation:
    """Test multi-turn conversation scenarios."""

    @pytest.mark.asyncio
    async def test_six_messages_sequential(self, chat_websocket, mock_message_queue):
        """Test sending 6 messages sequentially doesn't cause silent failure."""
        messages = [
            "Test harga besi",
            "Plat baja 5mm",
            "Berapa harga hollow 4x4?",
            "H-Beam tersedia?",
            "CNP channel tersedia?",
            "Besi beton ukuran 10",
        ]

        for i, msg_content in enumerate(messages, 1):
            message = WebSocketMessage(type="user_message", message=msg_content)

            await chat_websocket._handle_user_message(
                connection_id="test-conn",
                session_id="test-session",
                message=message,
            )

            # Verify each message is queued (no silent failures)
            assert (
                mock_message_queue.add_message.call_count == i
            ), f"Message {i} should be queued"

    @pytest.mark.asyncio
    async def test_rapid_messages_with_rate_limit(
        self, chat_websocket, mock_message_rate_limiter, mock_message_queue
    ):
        """Test rapid messages trigger rate limit, not silent failure."""
        # After 5 messages, rate limiter rejects
        call_count = [0]

        def mock_is_allowed(conn_id):
            call_count[0] += 1
            if call_count[0] <= 5:
                return (True, None)
            else:
                return (False, "Terlalu banyak pesan sekaligus")

        mock_message_rate_limiter.is_allowed.side_effect = mock_is_allowed

        # Send 6 messages rapidly
        for i in range(6):
            message = WebSocketMessage(type="user_message", message=f"Message {i+1}")

            await chat_websocket._handle_user_message(
                connection_id="test-conn",
                session_id="test-session",
                message=message,
            )

        # Verify: 5 messages queued, 6th gets error message (not silent)
        assert mock_message_queue.add_message.call_count == 5

        # Check that error message was sent for 6th message
        error_calls = [
            call[0][1]
            for call in chat_websocket.connection_manager.send_message.call_args_list
        ]
        assert any("Terlalu banyak pesan" in str(call) for call in error_calls)
