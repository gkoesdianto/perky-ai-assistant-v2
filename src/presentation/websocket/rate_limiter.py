"""Rate limiting module for WebSocket connections."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List


class RateLimiter:
    """
    Token bucket rate limiter for WebSocket connections.
    Prevents abuse by limiting messages per time window.
    """

    def __init__(self, max_per_minute: int = 10):
        """
        Initialize rate limiter.

        Args:
            max_per_minute: Maximum messages allowed per minute per session
        """
        self.max_per_minute = max_per_minute
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self._cleanup_task = None
        self._lock = asyncio.Lock()

    async def is_allowed(self, session_id: str) -> bool:
        """
        Check if a message is allowed based on rate limits.

        Args:
            session_id: Session identifier to check

        Returns:
            True if message is allowed, False if rate limit exceeded
        """
        async with self._lock:
            now = datetime.now()

            # Initialize request list for new sessions
            if session_id not in self.requests:
                self.requests[session_id] = []

            # Clean up old entries (older than 1 minute)
            self.requests[session_id] = [
                timestamp
                for timestamp in self.requests[session_id]
                if now - timestamp < timedelta(minutes=1)
            ]

            # Check if limit is exceeded
            if len(self.requests[session_id]) >= self.max_per_minute:
                return False

            # Record this request
            self.requests[session_id].append(now)
            return True

    async def reset_session(self, session_id: str):
        """
        Reset rate limit tracking for a specific session.

        Args:
            session_id: Session identifier to reset
        """
        async with self._lock:
            if session_id in self.requests:
                del self.requests[session_id]

    async def get_remaining_quota(self, session_id: str) -> int:
        """
        Get remaining message quota for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages remaining in current window
        """
        async with self._lock:
            now = datetime.now()

            if session_id not in self.requests:
                return self.max_per_minute

            # Count recent requests
            recent_requests = [
                timestamp
                for timestamp in self.requests[session_id]
                if now - timestamp < timedelta(minutes=1)
            ]

            return max(0, self.max_per_minute - len(recent_requests))

    async def start_cleanup(self):
        """Start periodic cleanup task for old rate limit entries."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self):
        """Stop the periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Periodic cleanup of expired rate limit entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                async with self._lock:
                    now = datetime.now()
                    # Remove sessions with no recent activity
                    inactive_sessions = [
                        session_id
                        for session_id, timestamps in self.requests.items()
                        if not timestamps
                        or all(now - ts > timedelta(minutes=5) for ts in timestamps)
                    ]
                    for session_id in inactive_sessions:
                        del self.requests[session_id]
            except asyncio.CancelledError:
                break
            except Exception:
                # Silent cleanup - don't interrupt service
                pass
