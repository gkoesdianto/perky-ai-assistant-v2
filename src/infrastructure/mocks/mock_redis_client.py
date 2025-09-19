"""
Mock Redis Client implementation for testing and development.
Simulates Redis operations without requiring an actual Redis server.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union


class MockRedisClient:
    """
    In-memory Redis simulation with TTL support.
    Thread-safe for concurrent WebSocket connections.

    This mock client provides the essential Redis operations needed for
    session management and caching in the application, without requiring
    an actual Redis server connection.
    """

    def __init__(self):
        """Initialize the mock Redis client with storage and expiry tracking."""
        self.storage: Dict[str, str] = {}  # Store everything as JSON strings like Redis
        self.expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()  # Thread safety for concurrent operations

    async def get(self, key: str) -> Optional[str]:
        """
        Get value with TTL checking.

        Args:
            key: The key to retrieve

        Returns:
            The value if it exists and hasn't expired, None otherwise
        """
        async with self._lock:
            # Check if key exists
            if key not in self.storage:
                return None

            # Check if key has expiry and if it's expired
            if key in self.expiry:
                if datetime.now() > self.expiry[key]:
                    # Key has expired, remove it
                    del self.storage[key]
                    del self.expiry[key]
                    return None

            return self.storage.get(key)

    async def set(
        self, key: str, value: Union[str, bytes, int, float, dict, list]
    ) -> None:
        """
        Set value without expiry.

        Args:
            key: The key to set
            value: The value to store (will be JSON serialized if complex)
        """
        async with self._lock:
            # Serialize complex objects to JSON string
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            elif isinstance(value, bytes):
                # Store bytes as base64 encoded string for JSON compatibility
                import base64

                serialized_value = base64.b64encode(value).decode("utf-8")
            else:
                serialized_value = str(value)

            self.storage[key] = serialized_value

            # Remove any existing expiry for this key
            if key in self.expiry:
                del self.expiry[key]

    async def setex(
        self, key: str, seconds: int, value: Union[str, bytes, int, float, dict, list]
    ) -> None:
        """
        Set with TTL expiry.

        Args:
            key: The key to set
            seconds: TTL in seconds
            value: The value to store (will be JSON serialized if complex)
        """
        async with self._lock:
            # Serialize complex objects to JSON string
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            elif isinstance(value, bytes):
                # Store bytes as base64 encoded string for JSON compatibility
                import base64

                serialized_value = base64.b64encode(value).decode("utf-8")
            else:
                serialized_value = str(value)

            # Store value
            self.storage[key] = serialized_value

            # Calculate and store expiry
            self.expiry[key] = datetime.now() + timedelta(seconds=seconds)

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys and their expiry.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys that were deleted
        """
        async with self._lock:
            deleted_count = 0
            for key in keys:
                if key in self.storage:
                    del self.storage[key]
                    deleted_count += 1
                if key in self.expiry:
                    del self.expiry[key]

            return deleted_count

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists and hasn't expired.

        Args:
            key: The key to check

        Returns:
            True if key exists and hasn't expired, False otherwise
        """
        # Use get to leverage TTL checking
        result = await self.get(key)
        return result is not None

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set a timeout on key.

        Args:
            key: The key to set expiry on
            seconds: TTL in seconds

        Returns:
            True if timeout was set, False if key doesn't exist
        """
        async with self._lock:
            if key not in self.storage:
                return False

            self.expiry[key] = datetime.now() + timedelta(seconds=seconds)
            return True

    async def ttl(self, key: str) -> int:
        """
        Get the time to live for a key in seconds.

        Args:
            key: The key to check

        Returns:
            TTL in seconds, -2 if key doesn't exist, -1 if key exists but has no TTL
        """
        async with self._lock:
            if key not in self.storage:
                return -2

            if key not in self.expiry:
                return -1

            # Check if already expired
            ttl_delta = self.expiry[key] - datetime.now()
            if ttl_delta.total_seconds() <= 0:
                # Key has expired
                del self.storage[key]
                del self.expiry[key]
                return -2

            return int(ttl_delta.total_seconds())

    async def keys(self, pattern: str = "*") -> list[str]:
        """
        Find all keys matching the given pattern.

        Args:
            pattern: Pattern to match (simplified, only supports * wildcard)

        Returns:
            List of matching keys
        """
        async with self._lock:
            # Clean up expired keys first
            current_time = datetime.now()
            expired_keys = [
                key
                for key, expiry_time in self.expiry.items()
                if current_time > expiry_time
            ]
            for key in expired_keys:
                if key in self.storage:
                    del self.storage[key]
                del self.expiry[key]

            # Simple pattern matching (only supports * at start/end)
            if pattern == "*":
                return list(self.storage.keys())
            elif pattern.startswith("*"):
                suffix = pattern[1:]
                return [k for k in self.storage.keys() if k.endswith(suffix)]
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                return [k for k in self.storage.keys() if k.startswith(prefix)]
            else:
                # Exact match
                return [pattern] if pattern in self.storage else []

    async def flushall(self) -> None:
        """Clear all keys from the storage."""
        async with self._lock:
            self.storage.clear()
            self.expiry.clear()

    async def cleanup_expired(self) -> int:
        """
        Remove all expired keys from storage.

        Returns:
            Number of keys cleaned up
        """
        async with self._lock:
            current_time = datetime.now()
            expired_keys = [
                key
                for key, expiry_time in self.expiry.items()
                if current_time > expiry_time
            ]

            for key in expired_keys:
                if key in self.storage:
                    del self.storage[key]
                del self.expiry[key]

            return len(expired_keys)

    # Additional helper methods for testing and debugging

    async def get_json(self, key: str) -> Optional[Union[dict, list]]:
        """
        Get value and automatically deserialize from JSON.

        Args:
            key: The key to retrieve

        Returns:
            The deserialized value if it exists, None otherwise
        """
        value = await self.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def info(self) -> Dict[str, Any]:
        """
        Get information about the mock Redis instance.

        Returns:
            Dictionary with storage statistics
        """
        async with self._lock:
            # Clean up expired keys first (inline to avoid deadlock)
            current_time = datetime.now()
            expired_keys = [
                key
                for key, expiry_time in self.expiry.items()
                if current_time > expiry_time
            ]

            for key in expired_keys:
                if key in self.storage:
                    del self.storage[key]
                del self.expiry[key]

            return {
                "keys_count": len(self.storage),
                "keys_with_ttl": len(self.expiry),
                "memory_usage_bytes": sum(
                    len(k.encode()) + len(v.encode()) for k, v in self.storage.items()
                ),
            }
