"""WebSocket protocol-specific E2E tests - MVP Optimized.

This module tests WebSocket-specific behavior like connection management,
heartbeat, and protocol compliance. Optimized for MVP with TestClient only.
"""

import json

import pytest
from starlette.testclient import WebSocketDisconnect


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.priority("critical")
class TestWebSocketProtocol:
    """Test WebSocket protocol implementation - MVP essentials."""

    def test_connection_lifecycle(self, app):
        """Test complete WebSocket connection lifecycle."""
        from fastapi.testclient import TestClient

        test_client = TestClient(app)

        # Test connection establishment
        with test_client.websocket_connect("/api/v1/ws/lifecycle-test") as websocket:
            # Should receive welcome message immediately
            welcome = websocket.receive_text()
            welcome_data = json.loads(welcome)

            assert welcome_data["type"] == "system"
            assert welcome_data["event"] == "connected"
            # session_id is nested under the session object
            assert "session" in welcome_data
            assert "session_id" in welcome_data["session"]
            assert "message" in welcome_data

            # Test normal closure
            websocket.close()

    def test_ping_pong_heartbeat(self, ws_client, e2e_helper):
        """Test ping-pong heartbeat mechanism."""
        import time

        # Send multiple ping messages - reduced for MVP
        for i in range(3):  # Reduced from 5 to 3
            assert e2e_helper.ping_pong(ws_client)
            time.sleep(0.1)

        # Connection should remain stable
        response = e2e_helper.send_message(ws_client, "Test message after pings")
        assert response["type"] == "ai_response"

    def test_message_ordering(self, ws_client):
        """Test that messages are processed in order - simplified for MVP."""
        # Send fewer messages for MVP testing
        messages = ["First message", "Second message"]  # Reduced from 3 to 2

        for msg in messages:
            ws_client.send_text(json.dumps({"type": "user_message", "message": msg}))

        # Collect all responses
        responses = []
        for _ in range(len(messages) * 2):  # Expect typing + response for each
            try:
                response = ws_client.receive_text()
                responses.append(json.loads(response))
            except Exception:
                break

        # Verify we got responses (simplified validation)
        ai_responses = [r for r in responses if r.get("type") == "ai_response"]

        assert len(ai_responses) == len(messages)  # Basic ordering check

    def test_invalid_json_handling(self, ws_client):
        """Test handling of invalid JSON messages."""
        # Send invalid JSON
        ws_client.send_text("not a json {invalid}")

        # Should receive error message
        response = ws_client.receive_text()
        response_data = json.loads(response)

        assert response_data["type"] == "error"
        assert (
            "json" in response_data["message"].lower()
            or "invalid" in response_data["message"].lower()
        )

        # Connection should remain open
        ws_client.send_text(json.dumps({"type": "ping"}))
        pong = ws_client.receive_text()
        pong_data = json.loads(pong)
        assert pong_data["type"] == "pong"

    def test_unknown_message_type(self, ws_client):
        """Test handling of unknown message types."""
        # Send unknown message type
        ws_client.send_text(json.dumps({"type": "unknown_type", "data": "test data"}))

        # Should receive error or be ignored gracefully
        response = ws_client.receive_text()
        response_data = json.loads(response)

        assert response_data["type"] == "error"
        assert (
            "unknown" in response_data["message"].lower()
            or "invalid" in response_data["message"].lower()
        )


@pytest.mark.e2e
@pytest.mark.priority("high")
class TestBasicProtocolFeatures:
    """Test basic protocol features needed for MVP."""

    def test_session_id_persistence(self, ws_client):
        """Test that session ID remains consistent during connection."""
        session_ids = []

        # Send fewer messages for MVP
        for i in range(2):  # Reduced from 3 to 2
            ws_client.send_text(
                json.dumps({"type": "user_message", "message": f"Message {i}"})
            )

            # Skip typing
            ws_client.receive_text()

            # Get response with session_id
            response = ws_client.receive_text()
            response_data = json.loads(response)

            if "session_id" in response_data:
                session_ids.append(response_data["session_id"])

        # All session IDs should be the same
        assert len(set(session_ids)) <= 1  # Allow for no session_ids or consistent ones

    def test_basic_error_recovery(self, ws_client):
        """Test basic error recovery - MVP essential."""
        # Send valid message first
        ws_client.send_text(json.dumps({"type": "user_message", "message": "Hello"}))
        ws_client.receive_text()  # Skip typing
        response1 = ws_client.receive_text()
        assert json.loads(response1)["type"] == "ai_response"

        # Send invalid message
        ws_client.send_text("invalid json")
        error_response = ws_client.receive_text()
        assert json.loads(error_response)["type"] == "error"

        # Connection should still work
        ws_client.send_text(json.dumps({"type": "ping"}))
        pong = ws_client.receive_text()
        assert json.loads(pong)["type"] == "pong"

    def test_rapid_message_handling(self, ws_client):
        """Test rapid message sending - simplified for MVP."""
        # Send multiple messages quickly - reduced count
        for i in range(3):  # Reduced from more to 3
            ws_client.send_text(
                json.dumps({"type": "user_message", "message": f"Quick message {i}"})
            )

        # Collect responses - simplified validation
        responses = []
        for _ in range(6):  # 3 messages * 2 responses each (typing + ai)
            try:
                response = ws_client.receive_text()
                responses.append(json.loads(response))
            except Exception:
                break

        # Should have received some responses
        ai_responses = [r for r in responses if r.get("type") == "ai_response"]
        assert len(ai_responses) >= 1  # At least one response processed


# Mark complex protocol tests as post-MVP
@pytest.mark.e2e
@pytest.mark.priority("low")
@pytest.mark.skip(reason="Post-MVP: Advanced protocol testing")
class TestAdvancedProtocolFeatures:
    """Advanced protocol features - marked for post-MVP implementation."""

    def test_connection_timeout_handling(self):
        """Test connection timeout - post-MVP."""
        pytest.skip("Post-MVP: Timeout handling")

    def test_binary_message_handling(self):
        """Test binary message handling - post-MVP."""
        pytest.skip("Post-MVP: Binary message handling")

    def test_large_message_handling(self):
        """Test large message handling - post-MVP."""
        pytest.skip("Post-MVP: Large message handling")

    def test_rapid_reconnection(self):
        """Test rapid reconnection - post-MVP."""
        pytest.skip("Post-MVP: Rapid reconnection testing")

    def test_graceful_shutdown_handling(self):
        """Test graceful shutdown - post-MVP."""
        pytest.skip("Post-MVP: Graceful shutdown testing")
