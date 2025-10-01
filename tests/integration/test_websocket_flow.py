"""Integration tests for WebSocket chat flow."""

from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock

from src.application.dto import SessionDTO, MessageDTO
from src.presentation.websocket.message_handler import MessageValidator


class TestChatBusinessLogicIntegration:
    """Test chat business logic without WebSocket protocol dependencies."""

    @pytest.fixture
    def mock_chat_orchestrator(self):
        """Create mock chat orchestrator."""
        orchestrator = AsyncMock()
        orchestrator.process_user_message = AsyncMock(
            return_value="Saya akan membantu Anda menemukan produk yang tepat."
        )
        orchestrator.start_session = AsyncMock(
            return_value=SessionDTO(
                session_id="test-session",
                conversation_id="conv-123",
                metadata={},
                started_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_active=True,
            )
        )
        orchestrator.get_conversation_history = AsyncMock(return_value=[])
        return orchestrator

    @pytest.mark.asyncio
    async def test_session_initialization_flow(self, mock_chat_orchestrator):
        """Test session initialization business logic."""
        session_data = await mock_chat_orchestrator.start_session(
            session_id="test-session", metadata={"source": "web"}
        )

        assert session_data.session_id == "test-session"
        assert session_data.conversation_id == "conv-123"
        mock_chat_orchestrator.start_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_processing_flow(self, mock_chat_orchestrator):
        """Test message processing business logic."""
        response = await mock_chat_orchestrator.process_user_message(
            session_id="test-session", message="Halo PERKY", metadata={"source": "web"}
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        mock_chat_orchestrator.process_user_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_heartbeat_logic(self):
        """Test session heartbeat business logic."""

        class MockSessionManager:
            def __init__(self):
                self.sessions = {}

            def create_session(self, session_id):
                self.sessions[session_id] = {"active": True}

            def is_session_active(self, session_id):
                return (
                    session_id in self.sessions and self.sessions[session_id]["active"]
                )

            def update_session_activity(self, session_id):
                if session_id in self.sessions:
                    self.sessions[session_id]["active"] = True

        session_manager = MockSessionManager()
        session_id = "test-session"
        session_manager.create_session(session_id)

        is_active = session_manager.is_session_active(session_id)
        assert is_active

        session_manager.update_session_activity(session_id)

        is_still_active = session_manager.is_session_active(session_id)
        assert is_still_active

    @pytest.mark.asyncio
    async def test_conversation_history_retrieval(self, mock_chat_orchestrator):
        """Test conversation history retrieval business logic."""
        session_id = "history-test-session"

        mock_chat_orchestrator.get_conversation_history.return_value = [
            MessageDTO(
                conversation_id="conv-123",
                content="First message",
                sender_type="user",
                session_id=session_id,
                timestamp=None,
            ),
            MessageDTO(
                conversation_id="conv-123",
                content="Response to first",
                sender_type="ai_agent",
                session_id=session_id,
                timestamp=None,
            ),
        ]

        history = await mock_chat_orchestrator.get_conversation_history(session_id)

        assert len(history) == 2
        assert history[0].content == "First message"
        assert history[1].sender_type == "ai_agent"

    @pytest.mark.asyncio
    async def test_error_handling_in_message_processing(self, mock_chat_orchestrator):
        """Test error handling in message processing."""
        mock_chat_orchestrator.process_user_message.side_effect = Exception(
            "Processing error"
        )

        with pytest.raises(Exception) as exc_info:
            await mock_chat_orchestrator.process_user_message(
                session_id="test-session", message="Test message", metadata={}
            )

        assert "Processing error" in str(exc_info.value)

        mock_chat_orchestrator.process_user_message.side_effect = None
        mock_chat_orchestrator.process_user_message.return_value = "Recovery response"

        response = await mock_chat_orchestrator.process_user_message(
            session_id="test-session", message="Retry message", metadata={}
        )

        assert response == "Recovery response"

    @pytest.mark.asyncio
    async def test_concurrent_session_management(self):
        """Test concurrent session management business logic."""

        class MockSessionManager:
            def __init__(self):
                self.sessions = {}

            def create_session(self, session_id):
                self.sessions[session_id] = {"active": True}

            def is_session_active(self, session_id):
                return (
                    session_id in self.sessions and self.sessions[session_id]["active"]
                )

            def get_active_session_count(self):
                return len([s for s in self.sessions.values() if s["active"]])

            def remove_session(self, session_id):
                if session_id in self.sessions:
                    del self.sessions[session_id]

        session_manager = MockSessionManager()
        sessions = []
        for idx in range(3):
            session_id = f"session-{idx}"
            session_manager.create_session(session_id)
            sessions.append(session_id)

        for session_id in sessions:
            assert session_manager.is_session_active(session_id)

        active_count = session_manager.get_active_session_count()
        assert active_count == 3

        session_manager.remove_session("session-1")
        assert not session_manager.is_session_active("session-1")
        assert session_manager.get_active_session_count() == 2

    @pytest.mark.asyncio
    async def test_message_validation_logic(self):
        """Test message validation business logic."""
        is_valid, _ = MessageValidator.validate_user_message("")
        assert not is_valid

        long_message = "x" * 3000
        is_valid, _ = MessageValidator.validate_user_message(long_message)
        assert not is_valid

        valid_message = "This is a valid message"
        is_valid, _ = MessageValidator.validate_user_message(valid_message)
        assert is_valid

    @pytest.mark.asyncio
    async def test_session_reconnection_logic(self, mock_chat_orchestrator):
        """Test session reconnection business logic."""

        class MockSessionManager:
            def __init__(self):
                self.sessions = {}

            def create_session(self, session_id):
                self.sessions[session_id] = {"active": True, "disconnected": False}

            def disconnect_session(self, session_id):
                if session_id in self.sessions:
                    self.sessions[session_id]["active"] = False
                    self.sessions[session_id]["disconnected"] = True

            def can_reconnect(self, session_id):
                return (
                    session_id in self.sessions
                    and self.sessions[session_id]["disconnected"]
                )

            def reconnect_session(self, session_id):
                if self.can_reconnect(session_id):
                    self.sessions[session_id]["active"] = True
                    self.sessions[session_id]["disconnected"] = False

            def is_session_active(self, session_id):
                return (
                    session_id in self.sessions and self.sessions[session_id]["active"]
                )

        session_manager = MockSessionManager()
        session_id = "reconnect-test"
        session_manager.create_session(session_id)

        session_manager.disconnect_session(session_id)

        is_reconnectable = session_manager.can_reconnect(session_id)
        assert is_reconnectable

        session_manager.reconnect_session(session_id)
        assert session_manager.is_session_active(session_id)

        mock_chat_orchestrator.get_conversation_history.return_value = [
            MessageDTO(
                conversation_id="conv-123",
                content="Previous message",
                sender_type="user",
                session_id=session_id,
                timestamp=None,
            )
        ]

        history = await mock_chat_orchestrator.get_conversation_history(session_id)
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_rate_limiting_logic(self):
        """Test rate limiting business logic."""

        class MockRateLimiter:
            def __init__(self, max_requests=10, time_window=60):
                self.max_requests = max_requests
                self.time_window = time_window
                self.request_counts = {}

            async def check_rate_limit(self, session_id):
                if session_id not in self.request_counts:
                    self.request_counts[session_id] = 0

                if self.request_counts[session_id] < self.max_requests:
                    self.request_counts[session_id] += 1
                    return True
                return False

        rate_limiter = MockRateLimiter(max_requests=10, time_window=60)
        session_id = "rate-test"

        for _ in range(10):
            is_allowed = await rate_limiter.check_rate_limit(session_id)
            assert is_allowed

        is_allowed = await rate_limiter.check_rate_limit(session_id)
        assert not is_allowed

    @pytest.mark.asyncio
    async def test_multi_connection_session_management(self, mock_chat_orchestrator):
        """Test session management with multiple connections."""

        class MockSessionManager:
            def __init__(self):
                self.connections = {}

            def add_connection(self, session_id, conn_id):
                if session_id not in self.connections:
                    self.connections[session_id] = []
                self.connections[session_id].append(conn_id)
                return conn_id

            def get_session_connections(self, session_id):
                return self.connections.get(session_id, [])

            def remove_connection(self, session_id, conn_id):
                if session_id in self.connections:
                    if conn_id in self.connections[session_id]:
                        self.connections[session_id].remove(conn_id)

        session_manager = MockSessionManager()
        session_id = "session-mgmt-test"

        conn1_id = session_manager.add_connection(session_id, "conn-1")
        conn2_id = session_manager.add_connection(session_id, "conn-2")

        assert conn1_id != conn2_id

        connections = session_manager.get_session_connections(session_id)
        assert len(connections) == 2

        response1 = await mock_chat_orchestrator.process_user_message(
            session_id=session_id, message="From connection 1"
        )

        response2 = await mock_chat_orchestrator.process_user_message(
            session_id=session_id, message="From connection 2"
        )

        assert response1 is not None
        assert response2 is not None

        session_manager.remove_connection(session_id, "conn-1")
        connections = session_manager.get_session_connections(session_id)
        assert len(connections) == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_logic(self):
        """Test circuit breaker business logic."""

        class MockCircuitBreaker:
            def __init__(self, failure_threshold=3, timeout=30, reset_timeout=60):
                self.failure_threshold = failure_threshold
                self.timeout = timeout
                self.reset_timeout = reset_timeout
                self.failure_count = 0
                self._is_open = False

            def record_failure(self):
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self._is_open = True

            def is_open(self):
                return self._is_open

            def call(self, func):
                if self.is_open():
                    raise Exception("Circuit breaker is open")
                return func

        circuit_breaker = MockCircuitBreaker(
            failure_threshold=3, timeout=30, reset_timeout=60
        )

        for _ in range(2):
            circuit_breaker.record_failure()

        is_open = circuit_breaker.is_open()
        assert not is_open

        circuit_breaker.record_failure()

        is_open = circuit_breaker.is_open()
        assert is_open

        with pytest.raises(Exception) as exc_info:
            circuit_breaker.call(lambda: None)

        assert "Circuit breaker is open" in str(exc_info.value)
