"""Behavioral tests for WebSocket JWT authentication."""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from src.presentation.websocket.auth import (
    create_websocket_token,
    validate_websocket_token,
)
from src.core.config import settings


class TestWebSocketAuthentication:
    """Test WebSocket JWT authentication behavior."""

    def test_create_token_contains_required_claims(self):
        """Token should contain session_id, exp, iat, and type claims."""
        session_id = "test-session-123"
        token = create_websocket_token(session_id)

        # Decode without verification to inspect claims
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert payload["session_id"] == session_id
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "websocket"

    def test_token_expires_after_one_hour(self):
        """Token should have 1-hour expiration time."""
        session_id = "test-session-456"
        token = create_websocket_token(session_id)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Check that expiration is approximately 1 hour after issuance
        time_diff = exp_time - iat_time
        assert timedelta(minutes=59) < time_diff < timedelta(minutes=61)

    def test_validate_valid_token_returns_session_id(self):
        """Valid token validation should return the session ID."""
        session_id = "test-session-789"
        token = create_websocket_token(session_id)

        validated_session_id = validate_websocket_token(token)

        assert validated_session_id == session_id

    def test_validate_expired_token_returns_none(self):
        """Expired token validation should return None."""
        # Create a token that's already expired
        now = datetime.now(timezone.utc)
        payload = {
            "session_id": "expired-session",
            "exp": now - timedelta(hours=1),  # Expired 1 hour ago
            "iat": now - timedelta(hours=2),
            "type": "websocket",
        }
        expired_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        result = validate_websocket_token(expired_token)

        assert result is None

    def test_validate_invalid_signature_returns_none(self):
        """Token with invalid signature should return None."""
        session_id = "test-session"
        token = create_websocket_token(session_id)

        # Tamper with the token
        tampered_token = token[:-10] + "tampered!!"

        result = validate_websocket_token(tampered_token)

        assert result is None

    def test_validate_wrong_token_type_returns_none(self):
        """Token with wrong type claim should return None."""
        now = datetime.now(timezone.utc)
        payload = {
            "session_id": "test-session",
            "exp": now + timedelta(hours=1),
            "iat": now,
            "type": "api",  # Wrong type
        }
        wrong_type_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        result = validate_websocket_token(wrong_type_token)

        assert result is None

    def test_validate_malformed_token_returns_none(self):
        """Malformed token should return None without raising exception."""
        malformed_tokens = [
            "not.a.token",
            "invalid",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Incomplete JWT
        ]

        for token in malformed_tokens:
            result = validate_websocket_token(token)
            assert result is None

    def test_tokens_are_unique_for_different_sessions(self):
        """Different sessions should generate different tokens."""
        token1 = create_websocket_token("session-1")
        token2 = create_websocket_token("session-2")

        assert token1 != token2

        # Verify each token contains correct session ID
        assert validate_websocket_token(token1) == "session-1"
        assert validate_websocket_token(token2) == "session-2"
