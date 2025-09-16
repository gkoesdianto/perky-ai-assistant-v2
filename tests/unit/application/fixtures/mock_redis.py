"""Mock implementations for testing application layer components."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock


class MockRedisClient:
    """
    Mock Redis client that simulates Redis behavior for testing.

    This mock provides:
    - Key-value storage with JSON serialization
    - TTL support with expiration
    - Async interface matching the real Redis client
    """

    def __init__(self):
        """Initialize the mock Redis client with empty storage."""
        self._storage: Dict[str, str] = {}
        self._expiry: Dict[str, datetime] = {}
        self._get_client_mock = AsyncMock(return_value=self._create_redis_mock())

    def _create_redis_mock(self):
        """Create a mock Redis connection with bound methods."""
        mock = MagicMock()
        mock.get = AsyncMock(side_effect=self._get)
        mock.set = AsyncMock(side_effect=self._set)
        mock.setex = AsyncMock(side_effect=self._setex)
        mock.delete = AsyncMock(side_effect=self._delete)
        mock.exists = AsyncMock(side_effect=self._exists)
        return mock

    async def get_client(self):
        """Get the mock Redis client connection."""
        return self._create_redis_mock()

    async def _get(self, key: str) -> Optional[str]:
        """
        Get value by key, respecting TTL expiration.

        Args:
            key: The Redis key to retrieve

        Returns:
            The stored value as a JSON string, or None if not found/expired
        """
        # Check expiration
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                # Key has expired
                del self._storage[key]
                del self._expiry[key]
                return None

        return self._storage.get(key)

    async def _set(self, key: str, value: Any) -> None:
        """
        Set a key-value pair without expiration.

        Args:
            key: The Redis key
            value: The value to store (will be JSON serialized if dict/list)
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._storage[key] = value

    async def _setex(self, key: str, seconds: int, value: Any) -> None:
        """
        Set a key-value pair with TTL expiration.

        Args:
            key: The Redis key
            seconds: TTL in seconds
            value: The value to store (will be JSON serialized if dict/list)
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._storage[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=seconds)

    async def _delete(self, key: str) -> None:
        """
        Delete a key from storage.

        Args:
            key: The Redis key to delete
        """
        if key in self._storage:
            del self._storage[key]
        if key in self._expiry:
            del self._expiry[key]

    async def _exists(self, key: str) -> bool:
        """
        Check if a key exists and hasn't expired.

        Args:
            key: The Redis key to check

        Returns:
            True if the key exists and hasn't expired, False otherwise
        """
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                # Key has expired
                del self._storage[key]
                del self._expiry[key]
                return False

        return key in self._storage

    def reset(self):
        """Reset the mock storage and expiry tracking."""
        self._storage.clear()
        self._expiry.clear()

    def get_storage_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of current storage for test assertions.

        Returns:
            Dictionary of stored key-value pairs with JSON parsing
        """
        snapshot = {}
        for key, value in self._storage.items():
            try:
                snapshot[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                snapshot[key] = value
        return snapshot


class MockRedisAdapter:
    """
    Adapter that wraps MockRedisClient to match the interface of RedisClient.

    This adapter provides the same interface as the real RedisClient
    from infrastructure.cache.redis_client.
    """

    def __init__(self, mock_client: Optional[MockRedisClient] = None):
        """
        Initialize the adapter with a mock client.

        Args:
            mock_client: Optional pre-configured MockRedisClient instance
        """
        self.mock_client = mock_client or MockRedisClient()
        self.redis_client = None

    async def connect(self):
        """Connect to the mock Redis (no-op for mock)."""
        self.redis_client = await self.mock_client.get_client()
        return self.redis_client

    async def disconnect(self):
        """Disconnect from mock Redis (no-op for mock)."""
        self.redis_client = None

    async def get_client(self):
        """Get the mock Redis client connection."""
        if not self.redis_client:
            await self.connect()
        return self.redis_client

    def reset(self):
        """Reset the underlying mock client."""
        self.mock_client.reset()
        self.redis_client = None

    def get_storage_snapshot(self) -> Dict[str, Any]:
        """Get storage snapshot from the underlying mock."""
        return self.mock_client.get_storage_snapshot()
