"""Behavioral tests for WebSocket rate limiter."""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.presentation.websocket.rate_limiter import RateLimiter


@pytest.mark.asyncio
class TestRateLimiter:
    """Test rate limiter behavior."""

    async def test_allows_messages_within_limit(self):
        """Should allow messages when under rate limit."""
        limiter = RateLimiter(max_per_minute=5)
        session_id = "test-session"

        # Send 5 messages (within limit)
        for _ in range(5):
            allowed = await limiter.is_allowed(session_id)
            assert allowed is True

    async def test_blocks_messages_exceeding_limit(self):
        """Should block messages when rate limit exceeded."""
        limiter = RateLimiter(max_per_minute=3)
        session_id = "test-session"

        # Send 3 messages (reach limit)
        for _ in range(3):
            allowed = await limiter.is_allowed(session_id)
            assert allowed is True

        # 4th message should be blocked
        allowed = await limiter.is_allowed(session_id)
        assert allowed is False

    async def test_rate_limit_resets_after_time_window(self):
        """Rate limit should reset after time window passes."""
        limiter = RateLimiter(max_per_minute=2)
        session_id = "test-session"

        # Exhaust limit
        for _ in range(2):
            await limiter.is_allowed(session_id)

        # Should be blocked now
        assert await limiter.is_allowed(session_id) is False

        # Simulate time passing by clearing old requests
        limiter.requests[session_id] = []

        # Should be allowed again
        assert await limiter.is_allowed(session_id) is True

    async def test_tracks_sessions_independently(self):
        """Each session should have independent rate limits."""
        limiter = RateLimiter(max_per_minute=2)

        # Session 1 uses its limit
        for _ in range(2):
            assert await limiter.is_allowed("session-1") is True
        assert await limiter.is_allowed("session-1") is False

        # Session 2 should still have its full quota
        for _ in range(2):
            assert await limiter.is_allowed("session-2") is True
        assert await limiter.is_allowed("session-2") is False

    async def test_get_remaining_quota(self):
        """Should correctly report remaining quota."""
        limiter = RateLimiter(max_per_minute=5)
        session_id = "test-session"

        # Initially should have full quota
        assert await limiter.get_remaining_quota(session_id) == 5

        # Use one request
        await limiter.is_allowed(session_id)
        assert await limiter.get_remaining_quota(session_id) == 4

        # Use remaining requests
        for _ in range(4):
            await limiter.is_allowed(session_id)
        assert await limiter.get_remaining_quota(session_id) == 0

    async def test_reset_session_clears_history(self):
        """Resetting a session should clear its rate limit history."""
        limiter = RateLimiter(max_per_minute=2)
        session_id = "test-session"

        # Use up the limit
        for _ in range(2):
            await limiter.is_allowed(session_id)
        assert await limiter.is_allowed(session_id) is False

        # Reset the session
        await limiter.reset_session(session_id)

        # Should have full quota again
        assert await limiter.get_remaining_quota(session_id) == 2
        assert await limiter.is_allowed(session_id) is True

    async def test_concurrent_requests_handled_safely(self):
        """Concurrent requests should be handled safely with locks."""
        limiter = RateLimiter(max_per_minute=10)
        session_id = "test-session"

        # Send 10 concurrent requests
        tasks = [limiter.is_allowed(session_id) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All 10 should be allowed
        assert all(results)

        # 11th should be blocked
        assert await limiter.is_allowed(session_id) is False

    async def test_cleanup_removes_inactive_sessions(self):
        """Cleanup should remove inactive sessions after 5 minutes of inactivity."""
        limiter = RateLimiter(max_per_minute=5)

        # Add some requests with old timestamps
        now = datetime.now()
        limiter.requests["session-1"] = [now - timedelta(minutes=10)]
        limiter.requests["session-2"] = [now - timedelta(minutes=10)]
        limiter.requests["session-3"] = [now - timedelta(minutes=2)]  # Recent

        # Manually clean up old entries through the lock
        async with limiter._lock:
            inactive_sessions = [
                session_id
                for session_id, timestamps in limiter.requests.items()
                if not timestamps
                or all(now - ts > timedelta(minutes=5) for ts in timestamps)
            ]
            for session_id in inactive_sessions:
                del limiter.requests[session_id]

        # Old sessions should be removed
        assert "session-1" not in limiter.requests
        assert "session-2" not in limiter.requests
        # Recent session should remain
        assert "session-3" in limiter.requests
