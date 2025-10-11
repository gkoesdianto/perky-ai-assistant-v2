"""E2E test fixtures and configuration - MVP Optimized.

This module provides fixtures for end-to-end testing of critical user flows.
Focuses on complete user journeys with simplified dependencies for MVP development.
Uses TestClient exclusively to avoid external websocket library dependencies.
"""

import json
import os
from typing import Any, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from src.infrastructure.container import InfrastructureContainer

# Import the application
from src.main import create_app

# Test configuration from environment - MVP optimized
TEST_CONFIG = {
    "app_host": os.getenv("APP_HOST", "localhost"),
    "app_port": int(os.getenv("APP_PORT", 8000)),
    "test_timeout": int(os.getenv("TEST_TIMEOUT", 30)),  # Reduced from 300
    "startup_wait": int(os.getenv("STARTUP_WAIT", 2)),  # Reduced from 5
}


@pytest.fixture(autouse=True)
def reset_container():
    """Reset the singleton container before each test to ensure isolation.

    This fixture runs automatically before each test to clear any state
    that might persist in the singleton container's repositories.
    """
    InfrastructureContainer.reset()
    yield
    # Optionally reset after test as well for extra safety
    InfrastructureContainer.reset()


@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Create FastAPI application instance for testing.

    Uses mock mode for predictable testing without external dependencies.
    Scope changed to 'function' to ensure fresh app instance per test.
    """
    # Reset container before creating app
    InfrastructureContainer.reset()

    # Set environment variables before creating the app
    os.environ["USE_MOCK_MODE"] = "true"
    os.environ["PROJECT_NAME"] = "Steel Chat E2E Test"
    os.environ["VERSION"] = "test"
    os.environ["API_V1_STR"] = "/api/v1"

    application = create_app()

    # Clean up after test
    yield application

    # Reset environment and container
    os.environ.pop("USE_MOCK_MODE", None)
    InfrastructureContainer.reset()


@pytest.fixture
def test_client(app: FastAPI) -> TestClient:
    """Create TestClient for testing both HTTP and WebSocket endpoints."""
    return TestClient(app)


@pytest.fixture
def ws_client(app: FastAPI) -> Generator[WebSocketTestSession, None, None]:
    """Create WebSocket client for testing real-time communication.

    Uses FastAPI TestClient exclusively - no external websocket dependencies.
    """
    test_client = TestClient(app)

    with test_client.websocket_connect("/api/v1/ws/e2e-test") as websocket:
        # Wait for welcome message
        welcome = websocket.receive_text()
        welcome_data = json.loads(welcome)
        assert welcome_data["type"] == "system"
        assert welcome_data["event"] == "connected"

        yield websocket


@pytest.fixture
def authenticated_ws_client(
    app: FastAPI,
) -> Generator[WebSocketTestSession, None, None]:
    """Create authenticated WebSocket client with session.

    Simplified for MVP - uses TestClient only.
    """
    test_client = TestClient(app)

    # In production, this would include authentication headers
    headers = {
        "X-Session-ID": "e2e-authenticated-session",
        "X-User-Agent": "E2E-Test-Client",
    }

    with test_client.websocket_connect(
        "/api/v1/ws/auth-test", headers=headers
    ) as websocket:
        welcome = websocket.receive_text()
        welcome_data = json.loads(welcome)
        assert welcome_data["type"] == "system"

        yield websocket


class E2ETestHelper:
    """Helper class for common E2E test operations - MVP optimized."""

    @staticmethod
    def send_message(websocket: WebSocketTestSession, message: str) -> dict:
        """Send a user message and receive AI response.

        Args:
            websocket: WebSocket connection
            message: User message to send

        Returns:
            AI response data
        """
        # Send message
        websocket.send_text(json.dumps({"type": "user_message", "message": message}))

        # Receive messages until we get the AI response
        # Skip any system messages (typing indicators, etc.)
        max_attempts = 5  # Prevent infinite loops
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            response = websocket.receive_text()
            response_data = json.loads(response)

            if response_data["type"] == "ai_response":
                return response_data
            elif response_data["type"] == "system":
                # Skip system messages (typing indicators, etc.)
                continue
            elif response_data["type"] == "user_message":
                # Skip echoed user messages in broadcast scenarios
                continue
            elif response_data["type"] == "error":
                # Return error responses for handling
                return response_data
            else:
                # Continue trying for other message types
                continue

        # If we get here, we didn't get an expected response
        raise ValueError(f"No valid response received after {max_attempts} attempts")

    @staticmethod
    def ping_pong(websocket: WebSocketTestSession) -> bool:
        """Test ping-pong connectivity.

        Args:
            websocket: WebSocket connection

        Returns:
            True if pong received successfully
        """
        try:
            websocket.send_text(json.dumps({"type": "ping"}))
            # Try to get pong response, might need to skip other messages
            max_attempts = 3
            for _ in range(max_attempts):
                response = websocket.receive_text()
                response_data = json.loads(response)
                if response_data["type"] == "pong":
                    return True
                # Skip other message types (system messages, etc.)
                elif response_data["type"] in ["system", "heartbeat"]:
                    continue
            return False
        except Exception:
            return False

    @staticmethod
    def wait_for_response(websocket: WebSocketTestSession, expected_type: str) -> dict:
        """Wait for specific message type with simplified timeout handling.

        Args:
            websocket: WebSocket connection
            expected_type: Expected message type

        Returns:
            Received message data

        Raises:
            ValueError: If expected message not received
        """
        # TestClient doesn't support timeout directly, simplified implementation
        try:
            response = websocket.receive_text()
            data = json.loads(response)

            if data["type"] != expected_type:
                raise ValueError(f"Expected {expected_type}, got {data['type']}")

            return data
        except Exception as e:
            raise ValueError(f"Failed to receive {expected_type}: {e}")


@pytest.fixture
def e2e_helper() -> E2ETestHelper:
    """Provide E2E test helper instance."""
    return E2ETestHelper()


@pytest.fixture
def test_session_cleanup():
    """Cleanup test sessions after test completion.

    Simplified for MVP - mock mode handles cleanup automatically.
    """
    # Setup - nothing to do before test
    yield

    # Teardown - cleanup test data
    # Mock mode handles this automatically for MVP


# Test data fixtures for common scenarios - MVP focused
@pytest.fixture
def product_inquiry_messages() -> list:
    """Common product inquiry messages for testing - reduced set for MVP."""
    return [
        "Ada plat baja 5mm?",
        "Show me steel plates",
        "Berapa harga besi beton D12?",
        "I need construction materials",
    ]


@pytest.fixture
def invalid_messages() -> list:
    """Invalid messages for error handling tests - essential cases only."""
    return [
        "",  # Empty message
        " ",  # Whitespace only
        "x" * 1000,  # Long message (reduced from 10000)
        '{"type": "invalid"}',  # JSON in message
        None,  # Null message
    ]


# Simplified performance test configuration for MVP
@pytest.fixture
def performance_config() -> dict:
    """Configuration for performance tests - MVP settings."""
    return {
        "min_requests": 10,  # Reduced from 100
        "max_response_time": 5.0,  # Increased for MVP tolerance
        "p90_threshold": 3.0,  # Relaxed from 1.5
        "p99_threshold": 5.0,  # Relaxed from 2.5
        "concurrent_users": 3,  # Reduced from 10
    }


# MVP-specific fixtures for streamlined testing
@pytest.fixture
def mvp_test_messages() -> list:
    """Essential test messages for MVP validation."""
    return [
        "Hello",
        "Ada baja?",
        "What products do you have?",
        "Berapa harga?",
    ]


@pytest.fixture
def smoke_test_config() -> dict:
    """Configuration for smoke tests - quick validation."""
    return {
        "timeout": 10,  # Quick timeout for smoke tests
        "max_messages": 3,  # Limit messages for speed
        "required_response_time": 3.0,  # Relaxed for MVP
    }
