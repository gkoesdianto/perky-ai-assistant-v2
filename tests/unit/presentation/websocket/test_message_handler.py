"""Unit tests for WebSocket message handler."""

from datetime import datetime

import pytest
from freezegun import freeze_time

from src.presentation.websocket.message_handler import (
    MessageRateLimiter,
    MessageValidator,
)
from src.presentation.websocket.types import MessageType


class TestMessageValidator:
    """Test cases for MessageValidator."""

    def test_validate_empty_message(self):
        """Test validation of empty message."""
        validator = MessageValidator()

        is_valid, error = validator.validate_user_message("")
        assert not is_valid
        assert "Pesan terlalu pendek" in error

        is_valid, error = validator.validate_user_message("   ")
        assert not is_valid
        assert "Pesan terlalu pendek" in error

    def test_validate_message_too_long(self):
        """Test validation of message exceeding max length."""
        validator = MessageValidator()
        long_message = "x" * 2001

        is_valid, error = validator.validate_user_message(long_message)
        assert not is_valid
        assert "Pesan terlalu panjang" in error
        assert "2000" in error

    def test_validate_valid_message(self):
        """Test validation of valid message."""
        validator = MessageValidator()

        is_valid, error = validator.validate_user_message("Hello, how are you?")
        assert is_valid
        assert error is None

    def test_detect_script_injection(self):
        """Test detection of script injection attempts."""
        validator = MessageValidator()

        malicious_messages = [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<img onerror=alert(1) src=x>",
            "<iframe src='evil.com'></iframe>",
            "<object data='evil.swf'></object>",
            "expression(alert(1))",
            "<link href='javascript:alert(1)'>",
            "vbscript:msgbox('test')",
            "data:text/html,<script>alert(1)</script>",
        ]

        for message in malicious_messages:
            is_valid, error = validator.validate_user_message(message)
            assert not is_valid
            assert "konten yang tidak diperbolehkan" in error

    def test_sanitize_html_entities(self):
        """Test HTML entity sanitization."""
        validator = MessageValidator()

        test_cases = [
            ("<div>test</div>", "&lt;div&gt;test&lt;&#x2F;div&gt;"),
            ("alert('xss')", "alert(&#x27;xss&#x27;)"),
            ('test"quote', "test&quot;quote"),
            ("test&amp", "test&amp;amp"),
            ("normal text", "normal text"),
        ]

        for input_msg, expected in test_cases:
            sanitized = validator.sanitize_message(input_msg)
            assert sanitized == expected

    def test_sanitize_whitespace(self):
        """Test whitespace normalization."""
        validator = MessageValidator()

        input_msg = "  too    many     spaces   "
        expected = "too many spaces"

        sanitized = validator.sanitize_message(input_msg)
        assert sanitized == expected

    def test_validate_message_structure(self):
        """Test validation of message structure."""
        validator = MessageValidator()

        # Missing type field
        is_valid, error = validator.validate_message_structure({})
        assert not is_valid
        assert "Missing required field: type" in error

        # Invalid message type
        is_valid, error = validator.validate_message_structure({"type": "invalid_type"})
        assert not is_valid
        assert "Invalid message type" in error

        # Valid user message
        is_valid, error = validator.validate_message_structure(
            {"type": MessageType.USER_MESSAGE.value, "message": "test"}
        )
        assert is_valid
        assert error is None

        # User message without message field
        is_valid, error = validator.validate_message_structure(
            {"type": MessageType.USER_MESSAGE.value}
        )
        assert not is_valid
        assert "requires 'message' field" in error

        # Non-string message field
        is_valid, error = validator.validate_message_structure(
            {"type": MessageType.USER_MESSAGE.value, "message": 123}
        )
        assert not is_valid
        assert "must be a string" in error


class TestMessageRateLimiter:
    """Test cases for MessageRateLimiter."""

    @freeze_time("2024-01-01 12:00:00")
    def test_rate_limit_per_minute(self):
        """Test per-minute rate limiting."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=5, max_messages_per_hour=100, max_burst_size=10
        )

        connection_id = "test-conn-1"

        # Send 5 messages (should all pass)
        for _ in range(5):
            is_allowed, error = limiter.is_allowed(connection_id)
            assert is_allowed
            assert error is None

        # 6th message should be blocked
        is_allowed, error = limiter.is_allowed(connection_id)
        assert not is_allowed
        assert "Batas pesan per menit tercapai" in error

    @freeze_time("2024-01-01 12:00:00")
    def test_rate_limit_per_hour(self):
        """Test per-hour rate limiting."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=100, max_messages_per_hour=10, max_burst_size=15
        )

        connection_id = "test-conn-2"

        # Send 10 messages (should all pass)
        for _ in range(10):
            is_allowed, error = limiter.is_allowed(connection_id)
            assert is_allowed

        # 11th message should be blocked
        is_allowed, error = limiter.is_allowed(connection_id)
        assert not is_allowed
        assert "Batas pesan per jam tercapai" in error

    @freeze_time("2024-01-01 12:00:00")
    def test_burst_limit(self):
        """Test burst rate limiting."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=100, max_messages_per_hour=1000, max_burst_size=3
        )

        connection_id = "test-conn-3"

        # Send 3 messages quickly (should pass)
        for _ in range(3):
            is_allowed, error = limiter.is_allowed(connection_id)
            assert is_allowed

        # 4th message in burst should be blocked
        is_allowed, error = limiter.is_allowed(connection_id)
        assert not is_allowed
        assert "Terlalu banyak pesan sekaligus" in error

    def test_multiple_connections(self):
        """Test rate limiting for multiple connections."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=2, max_messages_per_hour=100
        )

        # Each connection should have its own limit
        conn1 = "conn-1"
        conn2 = "conn-2"

        # Send 2 messages from each connection
        for _ in range(2):
            is_allowed, _ = limiter.is_allowed(conn1)
            assert is_allowed

        for _ in range(2):
            is_allowed, _ = limiter.is_allowed(conn2)
            assert is_allowed

        # 3rd message from each should be blocked
        is_allowed, _ = limiter.is_allowed(conn1)
        assert not is_allowed

        is_allowed, _ = limiter.is_allowed(conn2)
        assert not is_allowed

    def test_reset_connection(self):
        """Test resetting rate limits for a connection."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=1, max_messages_per_hour=100
        )

        connection_id = "test-conn-reset"

        # Send one message
        is_allowed, _ = limiter.is_allowed(connection_id)
        assert is_allowed

        # Second should be blocked
        is_allowed, _ = limiter.is_allowed(connection_id)
        assert not is_allowed

        # Reset connection
        limiter.reset_connection(connection_id)

        # Should be allowed again
        is_allowed, _ = limiter.is_allowed(connection_id)
        assert is_allowed

    def test_rate_limit_headers(self):
        """Test rate limit header generation."""
        limiter = MessageRateLimiter(
            max_messages_per_minute=10, max_messages_per_hour=100
        )

        connection_id = "test-headers"

        # Initial state
        headers = limiter.get_rate_limit_headers(connection_id)
        assert headers["X-RateLimit-Limit-Minute"] == "10"
        assert headers["X-RateLimit-Remaining-Minute"] == "10"
        assert headers["X-RateLimit-Limit-Hour"] == "100"
        assert headers["X-RateLimit-Remaining-Hour"] == "100"

        # After sending messages
        for _ in range(3):
            limiter.is_allowed(connection_id)

        headers = limiter.get_rate_limit_headers(connection_id)
        assert headers["X-RateLimit-Remaining-Minute"] == "7"
        assert headers["X-RateLimit-Remaining-Hour"] == "97"

    @freeze_time("2024-01-01 12:00:00")
    def test_cleanup_old_connections(self):
        """Test cleanup of old connection data."""
        limiter = MessageRateLimiter()

        # Add some connections
        limiter.is_allowed("conn-old")
        limiter.is_allowed("conn-recent")

        # Age the first connection
        with freeze_time("2024-01-02 13:00:00"):  # 25 hours later
            limiter.is_allowed("conn-recent")  # Update recent activity

            # Cleanup connections older than 24 hours
            cleaned = limiter.cleanup_old_connections(max_age_hours=24)
            assert cleaned == 1

            # Old connection should be gone
            assert "conn-old" not in limiter.message_history
            assert "conn-recent" in limiter.message_history
