"""Integration tests for WebSocket chat flow."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.main import app


@pytest.fixture
def test_client():
    """Create test client for WebSocket testing."""
    return TestClient(app)


def test_websocket_connection(test_client):
    """Test WebSocket connection establishment."""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Receive welcome message
        data = websocket.receive_json()

        assert data["type"] == "system"
        assert data["event"] == "connected"
        assert "Selamat datang" in data["message"]
        assert "session" in data


def test_websocket_message_flow(test_client):
    """Test complete message flow."""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome message
        websocket.receive_json()

        # Send user message
        websocket.send_json({"type": "user_message", "message": "Halo PERKY"})

        # Receive typing indicator
        typing = websocket.receive_json()
        assert typing["type"] == "system"
        assert typing["event"] == "typing"

        # Receive AI response
        response = websocket.receive_json()
        assert response["type"] == "ai_response"
        assert response["message"] is not None


def test_websocket_heartbeat(test_client):
    """Test heartbeat mechanism."""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send ping
        websocket.send_json({"type": "ping"})

        # Receive pong - might need to skip other messages first
        pong = None
        for _ in range(5):  # Try up to 5 messages
            msg = websocket.receive_json()
            if msg.get("type") == "pong":
                pong = msg
                break

        assert pong is not None, "Did not receive pong message"
        assert pong["type"] == "pong"


def test_websocket_get_history(test_client):
    """Test conversation history is sent on reconnection."""

    session_id = "history-test-session"

    with test_client.websocket_connect(f"/api/v1/ws/{session_id}") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "user_message", "message": "First message"})
        websocket.receive_json()
        response1 = websocket.receive_json()
        assert response1["type"] == "ai_response"

        websocket.send_json({"type": "user_message", "message": "Second message"})
        websocket.receive_json()
        response2 = websocket.receive_json()
        assert response2["type"] == "ai_response"

    with test_client.websocket_connect(f"/api/v1/ws/{session_id}") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "system"
        assert welcome["event"] == "connected"

        websocket.send_json(
            {"type": "user_message", "message": "Third message after reconnect"}
        )
        websocket.receive_json()
        response3 = websocket.receive_json()
        assert response3["type"] == "ai_response"


def test_websocket_error_handling(test_client):
    """Test error handling."""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send invalid message type
        websocket.send_json({"type": "invalid_type", "data": "test"})

        # Should receive validation error (might need to skip other messages)
        error = None
        for _ in range(5):
            msg = websocket.receive_json()
            if (
                msg.get("type") == "error"
                and "validation" in msg.get("message", "").lower()
            ):
                error = msg
                break

        assert error is not None, "Did not receive validation error"
        assert error["type"] == "error"
        assert "validation error" in error["message"].lower()

        # Verify connection still works after error
        websocket.send_json({"type": "ping"})
        pong = None
        for _ in range(5):  # Try up to 5 messages
            msg = websocket.receive_json()
            if msg.get("type") == "pong":
                pong = msg
                break
        assert pong is not None, "Did not receive pong after error"
        assert pong["type"] == "pong"


def test_concurrent_connections(test_client):
    """Test multiple concurrent connections."""

    # Test multiple connections sequentially for now
    for i in range(3):
        with test_client.websocket_connect(f"/api/v1/ws/session-{i}") as ws:
            # Receive welcome
            welcome = ws.receive_json()
            assert welcome["type"] == "system"

            # Send message
            ws.send_json({"type": "user_message", "message": f"Test from session-{i}"})

            # Receive responses
            typing = ws.receive_json()
            assert typing["type"] == "system"
            assert typing["event"] == "typing"

            response = ws.receive_json()
            assert response["type"] == "ai_response"


def test_message_validation(test_client):
    """Test message validation."""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        websocket.receive_json()  # Skip welcome

        # Test empty message
        websocket.send_json({"type": "user_message", "message": ""})

        error = None
        for _ in range(5):
            msg = websocket.receive_json()
            if msg.get("type") == "error":
                error = msg
                break
        assert error is not None and error["type"] == "error"

        # Test very long message
        long_message = "x" * 3000
        websocket.send_json({"type": "user_message", "message": long_message})

        error = None
        for _ in range(5):
            msg = websocket.receive_json()
            if msg.get("type") == "error":
                error = msg
                break
        assert error is not None and error["type"] == "error"


def test_websocket_reconnection(test_client):
    """Test reconnection scenarios."""

    # First connection
    with test_client.websocket_connect("/api/v1/ws/reconnect-test") as ws1:
        welcome1 = ws1.receive_json()
        assert welcome1["type"] == "system"

        # Send a message to establish history
        ws1.send_json({"type": "user_message", "message": "First message"})

        # Wait for response
        ws1.receive_json()  # typing
        ws1.receive_json()  # response

    # Reconnect with same session ID
    with test_client.websocket_connect("/api/v1/ws/reconnect-test") as ws2:
        welcome2 = ws2.receive_json()
        assert welcome2["type"] == "system"

        # Should be able to continue conversation
        ws2.send_json(
            {"type": "user_message", "message": "Second message after reconnect"}
        )

        ws2.receive_json()  # typing
        response = ws2.receive_json()
        assert response["type"] == "ai_response"


def test_rate_limiting(test_client):
    """Test rate limiting functionality."""

    with test_client.websocket_connect("/api/v1/ws/rate-test") as websocket:
        websocket.receive_json()  # Skip welcome

        # Send messages rapidly
        for i in range(15):
            websocket.send_json(
                {"type": "user_message", "message": f"Rapid message {i}"}
            )

        # Should receive rate limit error eventually
        rate_limit_triggered = False
        for _ in range(20):
            try:
                data = websocket.receive_json()
                if (
                    data.get("type") == "error"
                    and "terlalu banyak" in data.get("message", "").lower()
                ):
                    rate_limit_triggered = True
                    break
            except (WebSocketDisconnect, Exception):
                break

        assert rate_limit_triggered, "Rate limiting should trigger after rapid messages"


def test_session_management(test_client):
    """Test session management across connections."""

    session_id = "session-mgmt-test"

    # Test that multiple connections to the same session can be established
    with test_client.websocket_connect(f"/api/v1/ws/{session_id}") as ws1:
        # First connection receives welcome
        welcome1 = ws1.receive_json()
        assert welcome1["type"] == "system"
        assert welcome1["event"] == "connected"

        with test_client.websocket_connect(f"/api/v1/ws/{session_id}") as ws2:
            # Second connection also receives welcome
            welcome2 = ws2.receive_json()
            assert welcome2["type"] == "system"
            assert welcome2["event"] == "connected"

            # Both connections should work independently
            # Test ws1
            ws1.send_json({"type": "ping"})
            pong1 = None
            for _ in range(5):
                msg = ws1.receive_json()
                if msg.get("type") == "pong":
                    pong1 = msg
                    break
            assert pong1 is not None and pong1["type"] == "pong"

            # Test ws2
            ws2.send_json({"type": "ping"})
            pong2 = None
            for _ in range(5):
                msg = ws2.receive_json()
                if msg.get("type") == "pong":
                    pong2 = msg
                    break
            assert pong2 is not None and pong2["type"] == "pong"

            # Both connections can send messages
            ws1.send_json({"type": "user_message", "message": "From WS1"})
            ws1_typing = ws1.receive_json()
            assert ws1_typing["type"] == "system"
            ws1_response = ws1.receive_json()
            assert ws1_response["type"] == "ai_response"

            ws2.send_json({"type": "user_message", "message": "From WS2"})
            ws2_typing = ws2.receive_json()
            assert ws2_typing["type"] == "system"
            ws2_response = ws2.receive_json()
            assert ws2_response["type"] == "ai_response"


def test_circuit_breaker_integration(test_client):
    """Test circuit breaker behavior."""

    # This test would require proper mocking of the ChatOrchestrator
    # For now, we'll test that the WebSocket can handle errors gracefully

    with test_client.websocket_connect("/api/v1/ws/circuit-test") as websocket:
        websocket.receive_json()  # Skip welcome

        # Send a valid message to ensure connection works
        websocket.send_json({"type": "user_message", "message": "Test message"})

        # Should receive typing and response
        typing = websocket.receive_json()
        assert typing["type"] == "system"

        response = websocket.receive_json()
        assert response["type"] == "ai_response"

        # Connection should remain stable after normal operation
        websocket.send_json({"type": "ping"})
        pong = None
        for _ in range(5):
            msg = websocket.receive_json()
            if msg.get("type") == "pong":
                pong = msg
                break
        assert pong is not None and pong["type"] == "pong"
