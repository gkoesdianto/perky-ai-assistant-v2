"""Redis-related fixtures for application layer testing.

This module contains fixtures for creating mock Redis clients and adapters.
"""

import asyncio
import json

import pytest

from tests.unit.application.fixtures.mock_redis import (
    MockRedisAdapter,
    MockRedisClient,
)


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing.

    Returns:
        MockRedisClient: A mock Redis client with storage and TTL support
    """
    return MockRedisClient()


@pytest.fixture
def mock_redis_adapter(mock_redis_client):
    """Create a mock Redis adapter that matches the RedisClient interface.

    Args:
        mock_redis_client: The underlying mock Redis client

    Returns:
        MockRedisAdapter: An adapter matching the RedisClient interface
    """
    return MockRedisAdapter(mock_redis_client)


@pytest.fixture
def mock_redis_with_existing_session(mock_redis_adapter):
    """Create a mock Redis adapter with a pre-existing session.

    This fixture is useful for testing scenarios where a session
    already exists in Redis.

    Returns:
        tuple: (MockRedisAdapter, session_data) for testing
    """
    session_data = {
        "session_id": "existing-session-123",
        "conversation_id": "conv-456",
        "started_at": "2024-01-15T10:00:00+00:00",
        "last_activity": "2024-01-15T10:30:00+00:00",
        "is_active": True,
        "metadata": {"source": "test", "user_agent": "test-browser"},
    }

    # Pre-populate the mock with existing session
    async def setup():
        client = await mock_redis_adapter.get_client()
        await client.setex(
            f"session:{session_data['session_id']}", 3600, json.dumps(session_data)
        )

    # Run the async setup
    asyncio.run(setup())

    return mock_redis_adapter, session_data


__all__ = [
    "mock_redis_client",
    "mock_redis_adapter",
    "mock_redis_with_existing_session",
]
