"""Mock implementations for application ports.

This module contains mock implementations of all port interfaces
for testing purposes.
"""

from typing import List, Optional
from unittest.mock import AsyncMock

import pytest

from src.application.dto.message_dto import MessageDTO
from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo, QueryIntent


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


class MockQueryAnalyzerAdapter:
    """Mock implementation of QueryAnalyzerPort for testing."""

    def __init__(self):
        self.analyze_mock = AsyncMock()
        self.call_count = 0
        self.last_query = None
        self.last_context = None

    async def analyze(
        self, query: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        self.call_count += 1
        self.last_query = query
        self.last_context = conversation_context
        return await self.analyze_mock(query, conversation_context)

    def reset(self):
        self.analyze_mock.reset_mock()
        self.call_count = 0
        self.last_query = None
        self.last_context = None


# Fixtures
@pytest.fixture
def mock_ai_agent():
    """Fixture for AI agent port mock."""
    return MockAIAgentAdapter()


@pytest.fixture
def mock_product_service():
    """Fixture for product service port mock."""
    return MockProductServiceAdapter()


@pytest.fixture
def mock_query_analyzer():
    """Fixture for query analyzer port mock."""
    return MockQueryAnalyzerAdapter()


# PydanticAI Agent Fixture
@pytest.fixture
def mock_pydantic_ai_agent():
    """Create a mock PydanticAI agent with run method.

    This fixture is used to test the PydanticAI agent pattern
    where the agent has a 'run' method instead of 'generate_response'.
    """
    agent = AsyncMock()
    agent.run = AsyncMock(return_value="This is a PydanticAI response")
    return agent


__all__ = [
    "MockAIAgentAdapter",
    "MockProductServiceAdapter",
    "MockQueryAnalyzerAdapter",
    "mock_ai_agent",
    "mock_product_service",
    "mock_query_analyzer",
    "mock_pydantic_ai_agent",
]
