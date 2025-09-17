"""Root test configuration with unified fixtures.

This file provides:
1. Pytest fixtures wrapping factories for convenience
2. Shared test utilities
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone

# Import all factories
from tests.factories import (
    SessionFactory,
    ConversationFactory,
    MessageFactory,
    ProductFactory,
    VariantFactory,
    QueryIntentFactory,
    MockAIAgentFactory,
    MockProductServiceFactory,
    MockRedisFactory,
    DTOFactory,
    ProductWithVariantsFactory,
    TestDataPresets,
)


# =============================================================================
# Domain Fixtures
# =============================================================================


@pytest.fixture
def session():
    """Create test session."""
    return SessionFactory.create()


@pytest.fixture
def expired_session():
    """Create expired session."""
    return SessionFactory.create(
        last_activity=datetime.now(timezone.utc) - timedelta(hours=25)
    )


@pytest.fixture
def session_with_metadata():
    """Create session with metadata."""
    return SessionFactory.create(
        metadata={
            "browser": "Chrome",
            "browser_version": "120.0.0",
            "ip": "192.168.1.100",
            "location": "Jakarta",
        }
    )


@pytest.fixture
def conversation():
    """Create test conversation."""
    return ConversationFactory.create()


@pytest.fixture
def conversation_with_messages():
    """Create conversation with messages."""
    return ConversationFactory.create_with_messages()


@pytest.fixture
def user_message():
    """Create user message."""
    return MessageFactory.create(sender_type="user")


@pytest.fixture
def ai_message():
    """Create AI message."""
    return MessageFactory.create(
        sender_type="ai_agent", content="Saya bisa membantu Anda"
    )


# =============================================================================
# Product Fixtures (Unified)
# =============================================================================


@pytest.fixture
def product():
    """Create test product (replaces multiple fixtures)."""
    return ProductFactory.create()


@pytest.fixture
def steel_product():
    """Create steel product."""
    return ProductFactory.create_steel_plate()


@pytest.fixture
def minimal_product():
    """Create minimal product."""
    return ProductFactory.create_minimal()


@pytest.fixture
def complete_product():
    """Create complete product."""
    return ProductFactory.create_complete()


@pytest.fixture
def variant():
    """Create test variant."""
    return VariantFactory.create()


@pytest.fixture
def steel_variant():
    """Create steel plate variant."""
    return VariantFactory.create_steel_plate_10mm()


@pytest.fixture
def product_with_variants():
    """Create product with variants."""
    return ProductWithVariantsFactory.create()


@pytest.fixture
def complete_product_with_variants():
    """Create complete product with variants."""
    return ProductWithVariantsFactory.create_complete_product()


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_agent():
    """Create mock AI agent."""
    return MockAIAgentFactory.create()


@pytest.fixture
def mock_product_service():
    """Create mock product service."""
    return MockProductServiceFactory.create()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedisFactory.create()


@pytest.fixture
def mock_redis_with_session():
    """Create mock Redis with existing session."""
    return MockRedisFactory.with_session()


@pytest.fixture
def mock_repository():
    """Create generic mock repository."""
    mock = AsyncMock()
    mock._storage = {}

    async def save(entity):
        mock._storage[entity.id] = entity
        return entity

    async def get(entity_id):
        return mock._storage.get(entity_id)

    mock.save = AsyncMock(side_effect=save)
    mock.get = AsyncMock(side_effect=get)
    mock.delete = AsyncMock(return_value=True)

    return mock


# =============================================================================
# DTO Fixtures
# =============================================================================


@pytest.fixture
def session_dto():
    """Create session DTO."""
    return DTOFactory.create_session_dto()


@pytest.fixture
def message_dto():
    """Create message DTO."""
    return DTOFactory.create_message_dto()


@pytest.fixture
def conversation_dto():
    """Create conversation DTO."""
    return DTOFactory.create_conversation_dto()


@pytest.fixture
def product_query_dto():
    """Create product query DTO."""
    return DTOFactory.create_product_query_dto()


@pytest.fixture
def product_response_dto():
    """Create product response DTO."""
    return DTOFactory.create_product_response_dto()


# =============================================================================
# Query Intent Fixtures
# =============================================================================


@pytest.fixture
def product_inquiry_intent():
    """Create product inquiry intent."""
    return QueryIntentFactory.product_inquiry()


@pytest.fixture
def price_check_intent():
    """Create price check intent."""
    return QueryIntentFactory.price_check()


@pytest.fixture
def availability_check_intent():
    """Create availability check intent."""
    return QueryIntentFactory.availability_check()


@pytest.fixture
def general_intent():
    """Create general query intent."""
    return QueryIntentFactory.create(confidence=0.85)


# =============================================================================
# Test Data Presets
# =============================================================================


@pytest.fixture(scope="session")
def test_data_presets():
    """Get test data presets."""
    return TestDataPresets


@pytest.fixture
def mock_conversation_repository():
    """Mock conversation repository with proper conversation handling."""
    mock = AsyncMock()
    mock._storage = {}
    mock._session_map = {}

    async def save(conversation):
        mock._storage[conversation.id] = conversation
        mock._session_map[conversation.session_id] = conversation
        return conversation

    async def get(conversation_id):
        return mock._storage.get(conversation_id)

    async def get_by_session(session_id):
        return mock._session_map.get(session_id)

    mock.save = AsyncMock(side_effect=save)
    mock.get = AsyncMock(side_effect=get)
    mock.get_by_session = AsyncMock(side_effect=get_by_session)
    mock.delete = AsyncMock(return_value=True)

    return mock


# =============================================================================
# Test Utilities
# =============================================================================


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure async backend for pytest-anyio."""
    return "asyncio"


@pytest.fixture(scope="function")
def reset_factories():
    """Reset factory counters between tests."""
    # Reset any factory state if needed
    yield
    # Cleanup after test


# =============================================================================
# Application-Specific Fixtures for Migration Compatibility
# =============================================================================


@pytest.fixture
def mock_message_repository(mock_repository):
    """Mock message repository for application layer tests."""
    return mock_repository


@pytest.fixture
def mock_product_repository():
    """Mock product repository for application layer tests."""
    mock = AsyncMock()
    mock.get_by_id = AsyncMock(return_value=ProductFactory.create_steel_plate())
    mock.search = AsyncMock(return_value=[ProductFactory.create_steel_plate()])
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock cache service for application layer tests."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock
