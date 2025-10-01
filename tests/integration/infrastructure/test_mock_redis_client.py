"""
Integration tests for MockRedisClient.
Tests the MockRedisClient implementation to ensure it simulates Redis operations.
"""

import asyncio
import json
from datetime import datetime

import pytest

from src.infrastructure.mocks.mock_redis_client import MockRedisClient


@pytest.mark.asyncio
class TestMockRedisClient:
    """Test suite for MockRedisClient implementation."""

    @pytest.fixture
    def client(self):
        """Create a fresh MockRedisClient instance for each test."""
        return MockRedisClient()

    async def test_basic_get_set(self, client):
        """Test basic get and set operations."""
        # Test setting and getting a string value
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        assert value == "test_value"

        # Test getting non-existent key
        value = await client.get("non_existent")
        assert value is None

    async def test_set_with_different_types(self, client):
        """Test setting different data types."""
        # String
        await client.set("string_key", "string_value")
        assert await client.get("string_key") == "string_value"

        # Integer
        await client.set("int_key", 42)
        assert await client.get("int_key") == "42"

        # Float
        await client.set("float_key", 3.14)
        assert await client.get("float_key") == "3.14"

        # Dictionary (JSON serialization)
        test_dict = {"name": "Plat Baja", "price": 125000}
        await client.set("dict_key", test_dict)
        value = await client.get("dict_key")
        assert json.loads(value) == test_dict

        # List (JSON serialization)
        test_list = ["PLT-5MM", "PLT-10MM", "HLW-40X40"]
        await client.set("list_key", test_list)
        value = await client.get("list_key")
        assert json.loads(value) == test_list

    async def test_setex_with_ttl(self, client):
        """Test setex operation with TTL expiry."""
        await client.setex("ttl_key", 1, "ttl_value")

        value = await client.get("ttl_key")
        assert value == "ttl_value"

        await asyncio.sleep(1.1)

        value = await client.get("ttl_key")
        assert value is None

    async def test_delete_operations(self, client):
        """Test delete operations."""
        # Set multiple keys
        await client.set("key1", "value1")
        await client.set("key2", "value2")
        await client.set("key3", "value3")

        # Delete single key
        deleted = await client.delete("key1")
        assert deleted == 1
        assert await client.get("key1") is None

        # Delete multiple keys
        deleted = await client.delete("key2", "key3", "non_existent")
        assert deleted == 2
        assert await client.get("key2") is None
        assert await client.get("key3") is None

    async def test_exists_operation(self, client):
        """Test exists operation."""
        # Non-existent key
        exists = await client.exists("test_key")
        assert exists == 0

        # Existing key
        await client.set("test_key", "test_value")
        exists = await client.exists("test_key")
        assert exists == 1

        # Expired key
        await client.setex("ttl_key", 1, "ttl_value")
        exists = await client.exists("ttl_key")
        assert exists == 1
        await asyncio.sleep(1.1)
        exists = await client.exists("ttl_key")
        assert exists == 0

    async def test_expire_operation(self, client):
        """Test expire operation to set TTL on existing keys."""
        await client.set("test_key", "test_value")

        result = await client.expire("test_key", 1)
        assert result is True

        assert await client.get("test_key") == "test_value"

        await asyncio.sleep(1.1)

        assert await client.get("test_key") is None

        result = await client.expire("non_existent", 10)
        assert result is False

    async def test_ttl_operation(self, client):
        """Test TTL operation to get remaining time."""
        # Non-existent key
        ttl = await client.ttl("non_existent")
        assert ttl == -2

        # Key without TTL
        await client.set("no_ttl_key", "value")
        ttl = await client.ttl("no_ttl_key")
        assert ttl == -1

        # Key with TTL
        await client.setex("ttl_key", 10, "value")
        ttl = await client.ttl("ttl_key")
        assert 8 <= ttl <= 10  # Allow for some timing variance

    async def test_keys_pattern_matching(self, client):
        """Test keys operation with pattern matching."""
        # Set various keys for Indonesian product catalog
        await client.set("product:plat:1", "Plat Baja SS400")
        await client.set("product:plat:2", "Plat Galvanis")
        await client.set("product:hollow:1", "Hollow Galvanis 40x40")
        await client.set("session:user123", "session_data")

        # Get all keys
        all_keys = await client.keys("*")
        assert len(all_keys) == 4

        # Pattern with prefix (Indonesian product pattern)
        plat_keys = await client.keys("product:plat:*")
        assert len(plat_keys) == 2
        assert set(plat_keys) == {"product:plat:1", "product:plat:2"}

        # Pattern with prefix for hollow products
        hollow_keys = await client.keys("product:hollow:*")
        assert len(hollow_keys) == 1
        assert "product:hollow:1" in hollow_keys

    async def test_flushall_operation(self, client):
        """Test flushall operation to clear all data."""
        # Set multiple keys with and without TTL
        await client.set("product:1", "Plat Baja")
        await client.setex("session:123", 3600, "session_data")
        await client.set("cache:price", "125000")

        # Verify keys exist
        assert len(await client.keys("*")) == 3

        # Flush all
        await client.flushall()

        # Verify all cleared
        assert len(await client.keys("*")) == 0
        assert await client.get("product:1") is None
        assert await client.get("session:123") is None

    async def test_cleanup_expired(self, client):
        """Test cleanup_expired operation."""
        await client.setex("expire1", 1, "value1")
        await client.setex("expire2", 1, "value2")
        await client.setex("expire3", 10, "value3")
        await client.set("no_expire", "value4")

        assert len(await client.keys("*")) == 4

        await asyncio.sleep(1.1)

        cleaned = await client.cleanup_expired()
        assert cleaned == 2

        remaining_keys = await client.keys("*")
        assert len(remaining_keys) == 2
        assert set(remaining_keys) == {"expire3", "no_expire"}

    async def test_get_json_helper(self, client):
        """Test get_json helper method for Indonesian product data."""
        # Store Indonesian product data
        product_data = {
            "name": "Plat Baja Hitam SS400",
            "sizes": ["5mm", "10mm", "15mm"],
            "price": 125000,
            "unit": "lembar",
        }
        await client.set("product:plat:ss400", product_data)

        # Retrieve as JSON
        retrieved = await client.get_json("product:plat:ss400")
        assert retrieved == product_data

        # Non-JSON data
        await client.set("simple_key", "plain_string")
        retrieved = await client.get_json("simple_key")
        assert retrieved == "plain_string"

    async def test_info_operation(self, client):
        """Test info operation for storage statistics."""
        # Initial state
        info = await client.info()
        assert info["keys_count"] == 0
        assert info["keys_with_ttl"] == 0

        # Add some Indonesian product data
        await client.set("product:plat", "Plat Baja")
        await client.setex("session:user", 3600, "session_data")

        info = await client.info()
        assert info["keys_count"] == 2
        assert info["keys_with_ttl"] == 1
        assert info["memory_usage_bytes"] > 0

    async def test_concurrent_operations(self, client):
        """Test concurrent operations stability."""
        await client.set("counter", "0")

        async def increment_counter():
            """Increment counter operation."""
            for _ in range(10):
                current = await client.get("counter")
                if current:
                    new_value = str(int(current) + 1)
                    await client.set("counter", new_value)

        tasks = [increment_counter() for _ in range(3)]
        await asyncio.gather(*tasks)

        final_value = await client.get("counter")
        assert int(final_value) > 0

    async def test_session_management_scenario(self, client):
        """Test a realistic session management scenario for Indonesian B2B chat."""
        # Create a session with Indonesian metadata
        session_id = "session:user_jakarta_123"
        session_data = {
            "user_id": "user123",
            "company": "PT SMS Perkasa",
            "location": "Jakarta",
            "product_interest": ["plat", "hollow", "h-beam"],
            "created_at": datetime.now().isoformat(),
            "language": "id",
        }

        # Store session with 3600 second TTL (1 hour)
        await client.setex(session_id, 3600, session_data)

        # Retrieve session
        stored_data = await client.get_json(session_id)
        assert stored_data == session_data
        assert stored_data["company"] == "PT SMS Perkasa"

        # Check TTL
        ttl = await client.ttl(session_id)
        assert 3595 <= ttl <= 3600

        # Extend session TTL (user still active)
        await client.expire(session_id, 7200)
        ttl = await client.ttl(session_id)
        assert 7195 <= ttl <= 7200

        # Delete session (logout)
        deleted = await client.delete(session_id)
        assert deleted == 1
        assert await client.exists(session_id) is False

    async def test_product_cache_scenario(self, client):
        """Test product caching scenario for Indonesian steel products."""
        # Cache Indonesian steel product data
        products = [
            {"sku": "PLT-5MM-4X8", "name": "Plat Baja 5mm", "price": 125000},
            {"sku": "HLW-40X40-GLV", "name": "Hollow Galvanis 40x40", "price": 85000},
            {"sku": "HBEAM-200X200", "name": "H-Beam WF 200", "price": 850000},
        ]

        # Store products with 5-minute cache
        for product in products:
            cache_key = f"cache:product:{product['sku']}"
            await client.setex(cache_key, 300, product)

        # Also cache a product summary
        summary = {"total": 3, "categories": ["plat", "hollow", "h-beam"]}
        await client.setex("cache:product:summary", 300, summary)

        # Verify all products cached
        product_keys = await client.keys("cache:product:*")
        assert len(product_keys) == 4

        # Retrieve specific product
        plat_data = await client.get_json("cache:product:PLT-5MM-4X8")
        assert plat_data["price"] == 125000

        # Invalidate cache (when product updates)
        cache_keys = await client.keys("cache:product:*")
        if cache_keys:
            deleted = await client.delete(*cache_keys)
            assert deleted == 4

        # Verify cache cleared
        remaining = await client.keys("cache:product:*")
        assert len(remaining) == 0

    async def test_conversation_storage_scenario(self, client):
        """Test conversation storage for Indonesian B2B chat."""
        conversation_id = "conv:123"

        # Store conversation context
        context = {
            "messages": [
                {"role": "user", "content": "Ada plat baja 5mm?"},
                {
                    "role": "assistant",
                    "content": "Ya, kami memiliki Plat Baja SS400 5mm",
                },
            ],
            "product_discussed": ["PLT-5MM-4X8"],
            "intent": "product_inquiry",
            "language": "id",
        }

        # Store with 24-hour TTL
        await client.setex(conversation_id, 86400, context)

        # Retrieve and verify
        stored_context = await client.get_json(conversation_id)
        assert len(stored_context["messages"]) == 2
        assert stored_context["language"] == "id"

        # Check conversation exists
        assert await client.exists(conversation_id) is True

        # TTL should be close to 24 hours
        ttl = await client.ttl(conversation_id)
        assert 86395 <= ttl <= 86400
