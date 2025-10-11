"""
WebSocket Message Handler - Advanced validation and sanitization.

Provides comprehensive message validation, sanitization, and rate limiting
for WebSocket communications with security-first approach.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.presentation.websocket.types import MessageType

logger = logging.getLogger(__name__)


class MessageValidator:
    """Validates and sanitizes WebSocket messages with security focus."""

    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1

    @classmethod
    def validate_user_message(cls, message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user message content.

        Args:
            message: The message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check length constraints
        if not message or len(message.strip()) < cls.MIN_MESSAGE_LENGTH:
            return False, "Pesan terlalu pendek"

        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return (
                False,
                f"Pesan terlalu panjang (maksimal {cls.MAX_MESSAGE_LENGTH} karakter)",
            )

        # Check for malicious content
        if cls._contains_malicious_patterns(message):
            return False, "Pesan mengandung konten yang tidak diperbolehkan"

        return True, None

    @staticmethod
    def _contains_malicious_patterns(message: str) -> bool:
        """
        Check for potentially malicious patterns.

        Args:
            message: Message to check

        Returns:
            True if malicious patterns detected
        """
        # Script injection patterns
        malicious_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<applet[^>]*>",
            r"<meta[^>]*http-equiv",
            r"<link[^>]*href.*javascript:",
            r"expression\s*\(",
            r"import\s*\(",
            r"vbscript:",
            r"data:text/html",
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Malicious pattern detected: {pattern[:20]}...")
                return True

        return False

    @staticmethod
    def sanitize_message(message: str) -> str:
        """
        Sanitize message content for safe display.

        Args:
            message: Message to sanitize

        Returns:
            Sanitized message
        """
        # Remove excess whitespace
        message = " ".join(message.split())

        # Escape HTML entities - IMPORTANT: & must be replaced first
        # to avoid double-escaping other entities
        message = message.replace("&", "&amp;")
        message = message.replace("<", "&lt;")
        message = message.replace(">", "&gt;")
        message = message.replace('"', "&quot;")
        message = message.replace("'", "&#x27;")
        message = message.replace("/", "&#x2F;")

        return message.strip()

    @classmethod
    def validate_message_structure(
        cls, data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate the overall message structure.

        Args:
            data: Message data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "type" not in data:
            return False, "Missing required field: type"

        # Validate message type
        valid_types = [t.value for t in MessageType]
        if data["type"] not in valid_types:
            return False, f"Invalid message type: {data['type']}"

        # Type-specific validation
        if data["type"] == MessageType.USER_MESSAGE.value:
            if "message" not in data:
                return False, "User message requires 'message' field"
            if not isinstance(data["message"], str):
                return False, "Message field must be a string"

        return True, None


class MessageRateLimiter:
    """Rate limiting for WebSocket messages with granular control."""

    def __init__(
        self,
        max_messages_per_minute: int = 30,
        max_messages_per_hour: int = 500,
        max_burst_size: int = 5,
    ):
        """
        Initialize rate limiter.

        Args:
            max_messages_per_minute: Maximum messages allowed per minute
            max_messages_per_hour: Maximum messages allowed per hour
            max_burst_size: Maximum burst messages allowed
        """
        self.max_per_minute = max_messages_per_minute
        self.max_per_hour = max_messages_per_hour
        self.max_burst_size = max_burst_size
        self.message_history: Dict[str, List[datetime]] = {}
        self.burst_tracker: Dict[str, List[datetime]] = {}

    def is_allowed(self, connection_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message is allowed based on rate limits.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Tuple of (is_allowed, rejection_reason)
        """
        try:
            now = datetime.now()

            # Initialize if new connection
            if connection_id not in self.message_history:
                self.message_history[connection_id] = []
                self.burst_tracker[connection_id] = []
                logger.debug(
                    f"Initialized rate tracking for new connection: {connection_id}"
                )

            # Clean old entries (older than 1 hour)
            self.message_history[connection_id] = [
                ts
                for ts in self.message_history[connection_id]
                if (now - ts).total_seconds() < 3600
            ]

            history = self.message_history[connection_id]

            # Check burst limit (messages in last 5 seconds)
            self.burst_tracker[connection_id] = [
                ts
                for ts in self.burst_tracker[connection_id]
                if (now - ts).total_seconds() < 5
            ]

            burst_count = len(self.burst_tracker[connection_id])
            logger.debug(
                f"Burst check for {connection_id}: "
                f"{burst_count}/{self.max_burst_size} messages in last 5s"
            )

            if burst_count >= self.max_burst_size:
                logger.warning(
                    f"Burst limit exceeded for {connection_id}: "
                    f"{burst_count} messages in 5 seconds"
                )
                return False, "Terlalu banyak pesan sekaligus. Harap tunggu sebentar."

            # Check per-minute limit
            recent_minute = [ts for ts in history if (now - ts).total_seconds() < 60]
            minute_count = len(recent_minute)
            logger.debug(
                f"Minute check for {connection_id}: "
                f"{minute_count}/{self.max_per_minute} messages"
            )

            if minute_count >= self.max_per_minute:
                wait_time = 60 - (now - recent_minute[0]).total_seconds()
                logger.warning(
                    f"Per-minute limit exceeded for {connection_id}: "
                    f"{minute_count} messages"
                )
                return (
                    False,
                    f"Batas pesan per menit tercapai. Tunggu {int(wait_time)} detik.",
                )

            # Check per-hour limit
            hour_count = len(history)
            logger.debug(
                f"Hour check for {connection_id}: "
                f"{hour_count}/{self.max_per_hour} messages"
            )

            if hour_count >= self.max_per_hour:
                wait_time = 3600 - (now - history[0]).total_seconds()
                minutes = int(wait_time / 60)
                logger.warning(
                    f"Per-hour limit exceeded for {connection_id}: "
                    f"{hour_count} messages"
                )
                return False, f"Batas pesan per jam tercapai. Tunggu {minutes} menit."

            # Record this message
            self.message_history[connection_id].append(now)
            self.burst_tracker[connection_id].append(now)

            logger.debug(
                f"Rate limit passed for {connection_id}: "
                f"burst={burst_count+1}/{self.max_burst_size}, "
                f"minute={minute_count+1}/{self.max_per_minute}, "
                f"hour={hour_count+1}/{self.max_per_hour}"
            )

            return True, None

        except Exception as e:
            logger.error(
                f"Rate limiter error for {connection_id}: {e}",
                exc_info=True,
            )
            # Fail open with warning - allow the message but log the error
            return True, None

    def get_rate_limit_headers(self, connection_id: str) -> Dict[str, str]:
        """
        Get rate limit headers for response.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Dictionary of rate limit headers
        """
        now = datetime.now()

        if connection_id not in self.message_history:
            remaining_minute = self.max_per_minute
            remaining_hour = self.max_per_hour
        else:
            history = self.message_history[connection_id]

            recent_minute = [ts for ts in history if (now - ts).total_seconds() < 60]
            recent_hour = history

            remaining_minute = max(0, self.max_per_minute - len(recent_minute))
            remaining_hour = max(0, self.max_per_hour - len(recent_hour))

        return {
            "X-RateLimit-Limit-Minute": str(self.max_per_minute),
            "X-RateLimit-Remaining-Minute": str(remaining_minute),
            "X-RateLimit-Limit-Hour": str(self.max_per_hour),
            "X-RateLimit-Remaining-Hour": str(remaining_hour),
        }

    def reset_connection(self, connection_id: str) -> None:
        """
        Reset rate limit tracking for a connection.

        Args:
            connection_id: Connection to reset
        """
        if connection_id in self.message_history:
            del self.message_history[connection_id]
        if connection_id in self.burst_tracker:
            del self.burst_tracker[connection_id]

        logger.info(f"Rate limits reset for connection: {connection_id}")

    def cleanup_old_connections(self, max_age_hours: int = 24) -> int:
        """
        Clean up old connection tracking data.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of connections cleaned up
        """
        now = datetime.now()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0

        connections_to_remove = []

        for connection_id, history in self.message_history.items():
            if not history:
                connections_to_remove.append(connection_id)
            elif (now - history[-1]).total_seconds() > max_age_seconds:
                connections_to_remove.append(connection_id)

        for connection_id in connections_to_remove:
            self.reset_connection(connection_id)
            cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old connections")

        return cleaned_count
