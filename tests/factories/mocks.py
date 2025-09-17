"""Consolidated mock implementations."""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
import uuid
import json

from tests.factories.base import BaseFactory


class MockAIAgentFactory(BaseFactory):
    """Factory for mock AI agent adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock AI agent with preset responses."""
        mock = AsyncMock()

        # Set up the main method with the response from kwargs
        response = kwargs.get('response', 'Test AI response')
        mock.generate_response = AsyncMock(return_value=response)

        # Add analyze_intent method for query analysis
        mock.analyze_intent = AsyncMock(
            return_value=kwargs.get('intent', 'general'))

        # Add tracking properties for test verification
        mock.call_count = 0
        mock.last_message = None
        mock.last_context = None

        # Track calls for generate_response
        async def generate_with_tracking(message, context=None):
            mock.call_count += 1
            mock.last_message = message
            mock.last_context = context
            return response

        mock.generate_response.side_effect = generate_with_tracking

        # Add reset method for test cleanup
        def reset():
            mock.call_count = 0
            mock.last_message = None
            mock.last_context = None
            mock.generate_response.reset_mock()
            mock.analyze_intent.reset_mock()

        mock.reset = reset

        return mock

    # Presets
    @classmethod
    def product_specialist(cls, **kwargs) -> AsyncMock:
        """Create a mock that specializes in product responses."""
        defaults = {
            'response': 'Kami memiliki berbagai jenis plat baja dengan berbagai ukuran.',
            'intent': 'product_inquiry'
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def price_advisor(cls, **kwargs) -> AsyncMock:
        """Create a mock that provides pricing information."""
        defaults = {
            'response': 'Harga plat baja 5mm adalah Rp 750.000 per lembar.',
            'intent': 'price_check'
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def availability_checker(cls, **kwargs) -> AsyncMock:
        """Create a mock for stock availability responses."""
        defaults = {
            'response': 'Stok plat baja tersedia dengan jumlah 50 lembar.',
            'intent': 'availability_check'
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class MockProductServiceFactory(BaseFactory):
    """Factory for mock product service adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock product service."""
        mock = AsyncMock()

        # Configure search_products method
        products = kwargs.get('products', [])
        mock.search_products = AsyncMock(return_value=products)

        # Configure get_product method
        product = kwargs.get('product', None)
        mock.get_product = AsyncMock(return_value=product)

        # Configure get_product_with_variants method
        product_with_variants = kwargs.get('product_with_variants', None)
        mock.get_product_with_variants = AsyncMock(return_value=product_with_variants)

        # Add tracking for test verification
        mock.call_count = {'search': 0, 'get': 0, 'get_variants': 0}
        mock.last_search_query = None
        mock.last_product_id = None

        # Add tracking side effects
        async def search_with_tracking(query):
            mock.call_count['search'] += 1
            mock.last_search_query = query
            return products

        async def get_with_tracking(product_id):
            mock.call_count['get'] += 1
            mock.last_product_id = product_id
            return product

        async def get_variants_with_tracking(product_id):
            mock.call_count['get_variants'] += 1
            mock.last_product_id = product_id
            return product_with_variants

        mock.search_products.side_effect = search_with_tracking
        mock.get_product.side_effect = get_with_tracking
        mock.get_product_with_variants.side_effect = get_variants_with_tracking

        # Add reset method
        def reset():
            mock.call_count = {'search': 0, 'get': 0, 'get_variants': 0}
            mock.last_search_query = None
            mock.last_product_id = None
            mock.search_products.reset_mock()
            mock.get_product.reset_mock()
            mock.get_product_with_variants.reset_mock()

        mock.reset = reset

        return mock

    @classmethod
    def with_products(cls, products: List, **kwargs) -> AsyncMock:
        """Create mock with specific product list."""
        kwargs['products'] = products
        return cls.create(**kwargs)

    @classmethod
    def empty_results(cls, **kwargs) -> AsyncMock:
        """Create mock that returns no products."""
        kwargs['products'] = []
        kwargs['product'] = None
        kwargs['product_with_variants'] = None
        return cls.create(**kwargs)


class MockRedisFactory(BaseFactory):
    """Factory for mock Redis clients."""

    @classmethod
    def create(cls, **kwargs) -> MagicMock:
        """Create mock Redis client with session storage."""
        mock = MagicMock()

        # Initialize storage
        mock._storage = kwargs.get('storage', {})

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
        async def json_get(key, path='.'):
            value = mock._storage.get(key)
            if value and isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return None
            return value

        async def json_set(key, path, value):
            mock._storage[key] = json.dumps(value) if not isinstance(value, str) else value
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
                'id': 'test-session-123',
                'session_id': 'test-session-123',
                'conversation_id': 'conv-456',
                'started_at': '2024-01-01T00:00:00Z',
                'last_activity': '2024-01-01T00:00:00Z',
                'is_active': True,
            }

        storage = kwargs.get('storage', {})
        storage['session:test-session-123'] = json.dumps(session_data)
        kwargs['storage'] = storage
        return cls.create(**kwargs)

    @classmethod
    def with_conversation(cls, conversation_data: Optional[Dict] = None, **kwargs) -> MagicMock:
        """Create mock Redis with a pre-stored conversation."""
        if conversation_data is None:
            conversation_data = {
                'id': 'conv-456',
                'session_id': 'test-session-123',
                'messages': [],
                'started_at': '2024-01-01T00:00:00Z',
                'last_activity': '2024-01-01T00:00:00Z',
            }

        storage = kwargs.get('storage', {})
        storage['conversation:conv-456'] = json.dumps(conversation_data)
        kwargs['storage'] = storage
        return cls.create(**kwargs)

    @classmethod
    def empty(cls, **kwargs) -> MagicMock:
        """Create an empty mock Redis instance."""
        kwargs['storage'] = {}
        return cls.create(**kwargs)
