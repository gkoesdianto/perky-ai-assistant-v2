"""Centralized fixtures for application layer tests."""

import pytest
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from decimal import Decimal

from src.application.dto.session_dto import SessionDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.conversation_dto import ConversationDTO
from src.application.use_cases.interfaces import (
    StartChatSessionUseCase,
    ProcessUserMessageUseCase,
    GetConversationUseCase,
)
from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo, VariantInfo


# Mock Use Case Implementations
class MockStartChatSessionUseCase(StartChatSessionUseCase):
    """Mock implementation of StartChatSessionUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        self.call_count += 1
        self.last_call_args = {"session_id": session_id, "metadata": metadata}
        return await self.execute_mock(session_id, metadata)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


class MockProcessUserMessageUseCase(ProcessUserMessageUseCase):
    """Mock implementation of ProcessUserMessageUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        self.call_count += 1
        self.last_call_args = {
            "session_id": session_id,
            "content": content,
            "metadata": metadata,
        }
        return await self.execute_mock(session_id, content, metadata)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


class MockGetConversationUseCase(GetConversationUseCase):
    """Mock implementation of GetConversationUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        self.call_count += 1
        self.last_call_args = {"session_id": session_id}
        return await self.execute_mock(session_id)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


# Mock Port Implementations
class MockAIAgentAdapter:
    """Mock implementation of AIAgentPort for testing."""

    def __init__(self):
        self.generate_response_mock = AsyncMock()
        self.call_count = 0
        self.last_message = None
        self.last_context = None

    async def generate_response(
        self, message: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        self.call_count += 1
        self.last_message = message
        self.last_context = conversation_context
        return await self.generate_response_mock(message, conversation_context)

    def reset(self):
        self.generate_response_mock.reset_mock()
        self.call_count = 0
        self.last_message = None
        self.last_context = None


class MockProductServiceAdapter:
    """Mock implementation of ProductServicePort for testing."""

    def __init__(self):
        self.search_products_mock = AsyncMock()
        self.get_product_with_variants_mock = AsyncMock()
        self.call_count = {"search": 0, "get_variants": 0}
        self.last_search_query = None
        self.last_product_id = None

    async def search_products(self, query: str) -> List[ProductInfo]:
        self.call_count["search"] += 1
        self.last_search_query = query
        return await self.search_products_mock(query)

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        self.call_count["get_variants"] += 1
        self.last_product_id = product_id
        return await self.get_product_with_variants_mock(product_id)

    def reset(self):
        self.search_products_mock.reset_mock()
        self.get_product_with_variants_mock.reset_mock()
        self.call_count = {"search": 0, "get_variants": 0}
        self.last_search_query = None
        self.last_product_id = None


# Use Case Fixtures
@pytest.fixture
def mock_start_chat_session():
    """Fixture for start chat session use case mock."""
    return MockStartChatSessionUseCase()


@pytest.fixture
def mock_process_message():
    """Fixture for process message use case mock."""
    return MockProcessUserMessageUseCase()


@pytest.fixture
def mock_get_conversation():
    """Fixture for get conversation use case mock."""
    return MockGetConversationUseCase()


# Port Fixtures
@pytest.fixture
def mock_ai_agent():
    """Fixture for AI agent port mock."""
    return MockAIAgentAdapter()


@pytest.fixture
def mock_product_service():
    """Fixture for product service port mock."""
    return MockProductServiceAdapter()


# DTO Fixtures
@pytest.fixture
def sample_session_dto():
    """Create a sample SessionDTO for testing."""
    now = datetime.now(timezone.utc)
    return SessionDTO(
        session_id="test-session-123",
        conversation_id="conv-456",
        started_at=now,
        last_activity=now,
        is_active=True,
        metadata={"source": "test"},
    )


@pytest.fixture
def sample_message_dto():
    """Create a sample MessageDTO for testing."""
    now = datetime.now()
    return MessageDTO(
        content="Test message",
        sender_type="user",
        session_id="test-session-123",
        conversation_id="conv-456",
        timestamp=now,
        metadata={},
    )


@pytest.fixture
def sample_conversation_dto():
    """Create a sample ConversationDTO for testing."""
    now = datetime.now(timezone.utc)
    return ConversationDTO(
        id="conv-456",
        session_id="test-session-123",
        messages=[],
        started_at=now,
        last_activity=now,
        metadata={},
    )


@pytest.fixture
def sample_conversation_context():
    """Create sample conversation context for testing."""
    now = datetime.now()
    return [
        MessageDTO(
            content="Saya butuh plat baja tebal 10mm",
            sender_type="user",
            session_id="session-123",
            conversation_id="conv-1",
            timestamp=now,
            metadata={},
        ),
        MessageDTO(
            content="Baik, kami memiliki plat baja 10mm. Berapa lembar yang Anda butuhkan?",
            sender_type="ai_agent",
            session_id="session-123",
            conversation_id="conv-1",
            timestamp=now,
            metadata={},
        ),
    ]


# Product Value Object Fixtures
@pytest.fixture
def sample_product_info():
    """Create sample ProductInfo for testing."""
    return ProductInfo(
        product_id="prod_plat_baja",
        product_name="Plat Baja",
        product_description="High-quality steel plates for construction",
        category="Steel Products",
        variant_count=3,
    )


@pytest.fixture
def sample_variant_info():
    """Create sample VariantInfo for testing."""
    return VariantInfo(
        variant_id="var_001",
        sku="PLT-10MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 10mm x 1200mm x 2400mm",
        price=Decimal("750000"),
        stock_quantity=25,
        stock_unit="lembar",
        specifications={
            "thickness": "10mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )


@pytest.fixture
def sample_product_with_variants(sample_product_info, sample_variant_info):
    """Create sample ProductWithVariantsInfo for testing."""
    variant2 = VariantInfo(
        variant_id="var_002",
        sku="PLT-5MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 5mm x 1200mm x 2400mm",
        price=Decimal("450000"),
        stock_quantity=40,
        stock_unit="lembar",
        specifications={
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400",
        },
    )

    return ProductWithVariantsInfo(
        product=sample_product_info, variants=[sample_variant_info, variant2]
    )
