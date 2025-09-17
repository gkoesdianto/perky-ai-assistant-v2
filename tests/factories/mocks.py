"""Consolidated mock implementations."""

from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
import asyncio
import json

from tests.factories.base import BaseFactory


class MockAIAgentFactory(BaseFactory):
    """Factory for mock AI agent adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock AI agent with preset responses."""

        # Create a class that holds both the mock and tracking data
        class TrackingMock:
            def __init__(self):
                self.mock = AsyncMock()
                self.call_count = 0
                self.last_message = None
                self.last_context = None

                # Set up default response
                response = kwargs.get("response", "Test AI response")
                self._return_value = response
                self._side_effect = None

                # Create generate_response with tracking
                self.generate_response = AsyncMock()

                # Set up the tracking wrapper
                async def tracking_wrapper(*args, **kwargs):
                    # Track the call
                    self.call_count += 1

                    # Handle both positional and keyword arguments for message
                    if args:
                        self.last_message = args[0]
                        if len(args) > 1:
                            self.last_context = args[1]
                    elif "message" in kwargs:
                        self.last_message = kwargs["message"]
                        if "conversation_context" in kwargs:
                            self.last_context = kwargs["conversation_context"]

                    # Also check for context in kwargs
                    if "context" in kwargs and self.last_context is None:
                        self.last_context = kwargs["context"]

                    # Use side_effect if present, otherwise return_value
                    if self._side_effect:
                        if callable(self._side_effect):
                            if asyncio.iscoroutinefunction(self._side_effect):
                                return await self._side_effect(*args, **kwargs)
                            else:
                                result = self._side_effect(*args, **kwargs)
                                if asyncio.iscoroutine(result):
                                    return await result
                                return result
                        elif self._side_effect_iter:
                            # It's a list/iterator - use the stored iterator
                            try:
                                return next(self._side_effect_iter)
                            except StopIteration:
                                raise StopIteration("Mock side_effect exhausted")
                        else:
                            # Shouldn't happen but fallback
                            return next(iter(self._side_effect))
                    else:
                        return self._return_value

                # Set our tracking wrapper
                self.generate_response.side_effect = tracking_wrapper

                # Store original property setters
                self._original_fset_return_value = type(
                    self.generate_response
                ).return_value.fset
                self._original_fset_side_effect = type(
                    self.generate_response
                ).side_effect.fset

                # Keep track of the side_effect iterator if it's a list
                self._side_effect_iter = None

                # Intercept return_value and side_effect setters
                def set_return_value(mock_self, value):
                    self._return_value = value

                def set_side_effect(mock_self, value):
                    if value is None:
                        self._side_effect = None
                        self._side_effect_iter = None
                        # Keep our tracking wrapper
                    else:
                        self._side_effect = value
                        # Create iterator if it's a list
                        if isinstance(value, (list, tuple)):
                            self._side_effect_iter = iter(value)
                        else:
                            self._side_effect_iter = None
                        # Keep our tracking wrapper active

                # Replace the property setters
                type(self.generate_response).return_value = property(
                    type(self.generate_response).return_value.fget, set_return_value
                )
                type(self.generate_response).side_effect = property(
                    type(self.generate_response).side_effect.fget, set_side_effect
                )

                # Add analyze_intent method
                self.analyze_intent = AsyncMock(
                    return_value=kwargs.get("intent", "general")
                )

                # Add reset method
                def reset():
                    self.call_count = 0
                    self.last_message = None
                    self.last_context = None
                    self._return_value = response
                    self._side_effect = None
                    self._side_effect_iter = None
                    self.generate_response.reset_mock()
                    # Re-apply tracking wrapper
                    self.generate_response.side_effect = tracking_wrapper
                    self.analyze_intent.reset_mock()

                self.reset = reset

                # Forward any other attributes to the underlying mock
                def __getattr__(self, name):
                    return getattr(self.mock, name)

        # Create and return the tracking mock
        return TrackingMock()

    # Presets
    @classmethod
    def product_specialist(cls, **kwargs) -> AsyncMock:
        """Create a mock that specializes in product responses."""
        defaults = {
            "response": "Kami memiliki berbagai jenis plat baja dengan "
            "berbagai ukuran.",
            "intent": "product_inquiry",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def price_advisor(cls, **kwargs) -> AsyncMock:
        """Create a mock that provides pricing information."""
        defaults = {
            "response": "Harga plat baja 5mm adalah Rp 750.000 per lembar.",
            "intent": "price_check",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def availability_checker(cls, **kwargs) -> AsyncMock:
        """Create a mock for stock availability responses."""
        defaults = {
            "response": "Stok plat baja tersedia dengan jumlah 50 lembar.",
            "intent": "availability_check",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class MockProductServiceFactory(BaseFactory):
    """Factory for mock product service adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock product service with proper signatures."""
        mock = AsyncMock()

        # Configure search_products method with proper signature
        products = kwargs.get("products", [])

        # Add tracking for test verification
        mock.call_count = {"search": 0, "get": 0, "get_variants": 0}
        mock.last_search_query = None
        mock.last_product_id = None

        # Create mocks with tracking via side_effect
        mock.search_products = AsyncMock(return_value=products)

        async def search_track(*args, **kwargs):
            mock.call_count["search"] += 1
            if args:
                mock.last_search_query = args[0]
            return mock.search_products.return_value

        mock.search_products.side_effect = search_track

        # Configure get_product method
        product = kwargs.get("product", None)
        mock.get_product = AsyncMock(return_value=product)

        async def get_track(*args, **kwargs):
            mock.call_count["get"] += 1
            if args:
                mock.last_product_id = args[0]
            return mock.get_product.return_value

        mock.get_product.side_effect = get_track

        # Configure get_product_with_variants method
        product_with_variants = kwargs.get("product_with_variants", None)
        mock.get_product_with_variants = AsyncMock(return_value=product_with_variants)

        async def get_variants_track(*args, **kwargs):
            mock.call_count["get_variants"] += 1
            if args:
                mock.last_product_id = args[0]
            return mock.get_product_with_variants.return_value

        mock.get_product_with_variants.side_effect = get_variants_track

        # Add reset method
        def reset():
            mock.call_count = {"search": 0, "get": 0, "get_variants": 0}
            mock.last_search_query = None
            mock.last_product_id = None
            mock.search_products.reset_mock()
            mock.get_product.reset_mock()
            mock.get_product_with_variants.reset_mock()
            # Re-apply side effects after reset
            mock.search_products.side_effect = search_track
            mock.get_product.side_effect = get_track
            mock.get_product_with_variants.side_effect = get_variants_track

        mock.reset = reset

        return mock

    @classmethod
    def with_products(cls, products: List, **kwargs) -> AsyncMock:
        """Create mock with specific product list."""
        kwargs["products"] = products
        return cls.create(**kwargs)

    @classmethod
    def empty_results(cls, **kwargs) -> AsyncMock:
        """Create mock that returns no products."""
        kwargs["products"] = []
        kwargs["product"] = None
        kwargs["product_with_variants"] = None
        return cls.create(**kwargs)


class MockRedisFactory(BaseFactory):
    """Factory for mock Redis clients."""

    @classmethod
    def create(cls, **kwargs) -> MagicMock:
        """Create mock Redis client with session storage."""
        mock = MagicMock()

        # Initialize storage
        mock._storage = kwargs.get("storage", {})

        # Implement Redis-like operations
        async def get(key):
            return mock._storage.get(key)

        async def set(key, value, ex=None):
            mock._storage[key] = value
            if ex:
                # Store expiry time for testing purposes
                mock._storage[f"_expiry_{key}"] = ex
            return True

        async def delete(key):
            if key in mock._storage:
                del mock._storage[key]
                # Also delete expiry if exists
                expiry_key = f"_expiry_{key}"
                if expiry_key in mock._storage:
                    del mock._storage[expiry_key]
                return 1
            return 0

        async def exists(key):
            return 1 if key in mock._storage else 0

        async def expire(key, seconds):
            if key in mock._storage:
                mock._storage[f"_expiry_{key}"] = seconds
                return True
            return False

        async def ttl(key):
            expiry_key = f"_expiry_{key}"
            if expiry_key in mock._storage:
                return mock._storage[expiry_key]
            return -1 if key in mock._storage else -2

        # JSON operations
        async def json_get(key, path="."):
            value = mock._storage.get(key)
            if value and isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    return None
            return value

        async def json_set(key, path, value):
            mock._storage[key] = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            return True

        # Attach methods to mock
        mock.get = AsyncMock(side_effect=get)
        mock.set = AsyncMock(side_effect=set)
        mock.delete = AsyncMock(side_effect=delete)
        mock.exists = AsyncMock(side_effect=exists)
        mock.expire = AsyncMock(side_effect=expire)
        mock.ttl = AsyncMock(side_effect=ttl)
        mock.json.get = AsyncMock(side_effect=json_get)
        mock.json.set = AsyncMock(side_effect=json_set)

        # Add reset method
        def reset():
            mock._storage.clear()
            mock.get.reset_mock()
            mock.set.reset_mock()
            mock.delete.reset_mock()
            mock.exists.reset_mock()
            mock.expire.reset_mock()
            mock.ttl.reset_mock()
            mock.json.get.reset_mock()
            mock.json.set.reset_mock()

        mock.reset = reset

        return mock

    # Presets
    @classmethod
    def with_session(cls, session_data: Optional[Dict] = None, **kwargs) -> MagicMock:
        """Create mock Redis with a pre-stored session."""
        if session_data is None:
            session_data = {
                "id": "test-session-123",
                "session_id": "test-session-123",
                "conversation_id": "conv-456",
                "started_at": "2024-01-01T00:00:00Z",
                "last_activity": "2024-01-01T00:00:00Z",
                "is_active": True,
            }

        storage = kwargs.get("storage", {})
        storage["session:test-session-123"] = json.dumps(session_data)
        kwargs["storage"] = storage
        return cls.create(**kwargs)

    @classmethod
    def with_conversation(
        cls, conversation_data: Optional[Dict] = None, **kwargs
    ) -> MagicMock:
        """Create mock Redis with a pre-stored conversation."""
        if conversation_data is None:
            conversation_data = {
                "id": "conv-456",
                "session_id": "test-session-123",
                "messages": [],
                "started_at": "2024-01-01T00:00:00Z",
                "last_activity": "2024-01-01T00:00:00Z",
            }

        storage = kwargs.get("storage", {})
        storage["conversation:conv-456"] = json.dumps(conversation_data)
        kwargs["storage"] = storage
        return cls.create(**kwargs)

    @classmethod
    def empty(cls, **kwargs) -> MagicMock:
        """Create an empty mock Redis instance."""
        kwargs["storage"] = {}
        return cls.create(**kwargs)
