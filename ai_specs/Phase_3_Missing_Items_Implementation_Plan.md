# Phase 3: Missing Items Implementation Plan

## Executive Summary

This document provides a focused implementation plan for completing the remaining 10%
of Phase 3: Mock Infrastructure. Based on the completion analysis, three key items
need implementation to achieve 100% completion.

**Timeline**: 4 hours
**Priority**: High (blocking Phase 4: WebSocket Integration)
**Dependencies**: Existing mock implementations

## Missing Items Overview

| Item | Priority | Estimated Time | Impact |
|------|----------|---------------|---------|
| MockInfrastructureContainer | CRITICAL | 2 hours | Enables dependency injection and environment-based switching |
| End-to-End Integration Tests | HIGH | 1.5 hours | Validates three core MVP scenarios |
| Error Simulation Capability | MEDIUM | 30 minutes | Enables resilience testing |

## Implementation Plan

### 1. MockInfrastructureContainer (2 hours)

**Location**: `src/infrastructure/container.py`

**Purpose**: Centralized dependency injection container for switching between mock and real implementations.

#### 1.1 Implementation Steps

```python
# src/infrastructure/container.py
from typing import Optional
import os
from dataclasses import dataclass

from src.infrastructure.mocks.mock_redis_client import MockRedisClient
from src.infrastructure.mocks.mock_conversation_repository import MockConversationRepository
from src.infrastructure.mocks.mock_product_repository import MockProductRepository
from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

@dataclass
class MockInfrastructureContainer:
    """
    Dependency container for mock implementations.
    Enables easy switching between mock and real implementations via environment flags.
    """

    def __init__(self, use_mocks: bool = True):
        """
        Initialize container with mock or real implementations.

        Args:
            use_mocks: If True, use mock implementations.
                      Can be overridden by USE_MOCK_MODE env var.
        """
        # Check environment override
        env_use_mocks = os.getenv("USE_MOCK_MODE", "").lower()
        if env_use_mocks in ["true", "1", "yes"]:
            self.use_mocks = True
        elif env_use_mocks in ["false", "0", "no"]:
            self.use_mocks = False
        else:
            self.use_mocks = use_mocks

        # Configuration from environment
        self.mock_response_delay_ms = int(os.getenv("MOCK_RESPONSE_DELAY_MS", "0"))
        self.mock_error_rate = float(os.getenv("MOCK_ERROR_RATE", "0.0"))
        self.mock_data_seed = int(os.getenv("MOCK_DATA_SEED", "42"))

        if self.use_mocks:
            self._setup_mocks()
        else:
            self._setup_real_implementations()

    def _setup_mocks(self):
        """Register all mock implementations."""
        # Initialize mock components
        self.redis_client = MockRedisClient()
        self.conversation_repo = MockConversationRepository()
        self.product_repo = MockProductRepository()
        self.query_analyzer = MockQueryAnalyzer()
        self.ai_agent = MockAIAgent()

        # Store initialization state
        self.initialized = True
        self.mode = "mock"

    def _setup_real_implementations(self):
        """
        Register real implementations.
        To be implemented in Phase 4-5.
        """
        # Placeholder for real implementations
        # Week 2 priorities:
        # - Real Redis client with connection pooling
        # - PerkyOSClient for PIM integration
        # - PydanticAI for real AI agent
        # - PostgreSQL with SQLAlchemy
        raise NotImplementedError(
            "Real implementations not yet available. "
            "Set USE_MOCK_MODE=true to use mocks."
        )

    def get_redis_client(self):
        """Get Redis client instance."""
        return self.redis_client

    def get_conversation_repository(self):
        """Get conversation repository instance."""
        return self.conversation_repo

    def get_product_repository(self):
        """Get product repository instance."""
        return self.product_repo

    def get_query_analyzer(self):
        """Get query analyzer instance."""
        return self.query_analyzer

    def get_ai_agent(self):
        """Get AI agent instance."""
        return self.ai_agent
```

#### 1.2 Environment Configuration

Add to `.env.example`:

```env
# Mock Mode Configuration
USE_MOCK_MODE=true
MOCK_RESPONSE_DELAY_MS=0  # Simulate network delay (milliseconds)
MOCK_ERROR_RATE=0.0       # Simulate errors for testing (0.0-1.0)
MOCK_DATA_SEED=42         # Random seed for consistent test data
```

#### 1.3 Integration with Application Layer

Update `src/application/container.py`:

```python
from src.infrastructure.container import MockInfrastructureContainer

class ApplicationContainer:
    """Application-level dependency container."""

    def __init__(self):
        # Initialize infrastructure container
        self.infrastructure = MockInfrastructureContainer(use_mocks=True)

        # Wire up application services
        self._setup_services()

    def _setup_services(self):
        """Setup application services with dependencies."""
        from src.application.services.chat_orchestrator import ChatOrchestrator

        self.chat_orchestrator = ChatOrchestrator(
            ai_agent=self.infrastructure.get_ai_agent(),
            product_service=self.infrastructure.get_product_repository(),
            conversation_repo=self.infrastructure.get_conversation_repository(),
            query_analyzer=self.infrastructure.get_query_analyzer()
        )
```

### 2. End-to-End Integration Tests (1.5 hours)

**Location**: `tests/integration/test_mock_chat_flow.py`

**Purpose**: Validate the three core MVP scenarios with complete chat flow.

#### 2.1 Test Implementation

```python
# tests/integration/test_mock_chat_flow.py
import pytest
from src.infrastructure.container import MockInfrastructureContainer
from src.application.services.chat_orchestrator import ChatOrchestrator
from src.application.dto.message_dto import MessageDTO

class TestMockChatFlow:
    """End-to-end tests for mock infrastructure chat flows."""

    @pytest.fixture
    async def setup_infrastructure(self):
        """Setup mock infrastructure for testing."""
        container = MockInfrastructureContainer(use_mocks=True)

        orchestrator = ChatOrchestrator(
            ai_agent=container.get_ai_agent(),
            product_service=container.get_product_repository(),
            conversation_repo=container.get_conversation_repository(),
            query_analyzer=container.get_query_analyzer()
        )

        return orchestrator

    @pytest.mark.asyncio
    async def test_scenario_1_product_inquiry_flow(self, setup_infrastructure):
        """
        Scenario 1: Product Inquiry
        User asks about steel plates, gets product info with prices.
        """
        orchestrator = setup_infrastructure
        session_id = "test-session-001"

        # User asks about plat baja
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Ada plat baja 5mm?"
        )

        # Verify response contains product information
        assert response is not None
        assert "plat" in response.content.lower()
        assert any(price_indicator in response.content
                  for price_indicator in ["125000", "125.000", "Rp"])

        # Follow-up about availability
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Berapa stoknya?"
        )

        assert "stok" in response.content.lower() or "stock" in response.content.lower()

    @pytest.mark.asyncio
    async def test_scenario_2_price_check_flow(self, setup_infrastructure):
        """
        Scenario 2: Price Check
        User asks about hollow prices, gets pricing information.
        """
        orchestrator = setup_infrastructure
        session_id = "test-session-002"

        # User asks about hollow prices
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Harga hollow galvanis 40x40?"
        )

        # Verify price information
        assert response is not None
        assert "hollow" in response.content.lower()
        assert any(term in response.content.lower()
                  for term in ["harga", "price", "rp", "85000", "85.000"])

    @pytest.mark.asyncio
    async def test_scenario_3_availability_check_flow(self, setup_infrastructure):
        """
        Scenario 3: Availability Check
        User checks stock availability for specific products.
        """
        orchestrator = setup_infrastructure
        session_id = "test-session-003"

        # User checks H-beam availability
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="H-beam 200x200 ada stok?"
        )

        # Verify stock information
        assert response is not None
        assert any(term in response.content.lower()
                  for term in ["stok", "stock", "tersedia", "available"])
        assert "200x200" in response.content or "h-beam" in response.content.lower()

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, setup_infrastructure):
        """Test a complete multi-turn conversation."""
        orchestrator = setup_infrastructure
        session_id = "test-session-004"

        # Turn 1: Greeting
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Halo"
        )
        assert "selamat" in response.content.lower() or "perky" in response.content.lower()

        # Turn 2: Product inquiry
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Saya butuh plat baja untuk proyek"
        )
        assert "plat" in response.content.lower()

        # Turn 3: Specific size
        response = await orchestrator.handle_user_message(
            session_id=session_id,
            content="Yang 10mm ada?"
        )
        assert "10mm" in response.content or "250000" in response.content

        # Verify conversation continuity
        conversation = await orchestrator.get_conversation(session_id)
        assert conversation is not None
        assert len(conversation.messages) >= 6  # 3 user + 3 assistant messages
```

### 3. Error Simulation Capability (30 minutes)

**Location**: `src/infrastructure/mocks/mock_error_simulator.py`

**Purpose**: Simulate errors for testing error handling and resilience.

#### 3.1 Implementation

```python
# src/infrastructure/mocks/mock_error_simulator.py
import random
import asyncio
from typing import Optional

class MockException(Exception):
    """Custom exception for simulated errors."""
    pass

class MockErrorSimulator:
    """
    Simulate errors for testing error handling.
    Controlled via environment variables.
    """

    def __init__(self, error_rate: float = 0.0, delay_ms: int = 0):
        """
        Initialize error simulator.

        Args:
            error_rate: Probability of error (0.0-1.0)
            delay_ms: Simulated network delay in milliseconds
        """
        self.error_rate = min(max(error_rate, 0.0), 1.0)  # Clamp to [0, 1]
        self.delay_ms = max(delay_ms, 0)

    async def maybe_fail(self, operation: str) -> None:
        """
        Randomly fail based on error rate.

        Args:
            operation: Name of the operation for error message

        Raises:
            MockException: If random failure occurs
        """
        if random.random() < self.error_rate:
            raise MockException(f"Simulated failure in {operation}")

    async def maybe_delay(self) -> None:
        """Add simulated network delay if configured."""
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000.0)

    def wrap_operation(self, operation_name: str):
        """
        Decorator to wrap operations with error simulation.

        Usage:
            @error_simulator.wrap_operation("get_product")
            async def get_product(self, id):
                ...
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                await self.maybe_delay()
                await self.maybe_fail(operation_name)
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

#### 3.2 Integration with Mock Components

Update mock components to use error simulation:

```python
# Example integration in MockProductRepository
class MockProductRepository(ProductRepository):
    def __init__(self):
        # ... existing init code ...

        # Initialize error simulator from environment
        import os
        error_rate = float(os.getenv("MOCK_ERROR_RATE", "0.0"))
        delay_ms = int(os.getenv("MOCK_RESPONSE_DELAY_MS", "0"))
        self.error_simulator = MockErrorSimulator(error_rate, delay_ms)

    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search products with error simulation."""
        # Simulate potential errors and delays
        await self.error_simulator.maybe_delay()
        await self.error_simulator.maybe_fail("search_products")

        # ... existing search logic ...
```

## Testing Strategy

### Unit Tests for Container

```python
# tests/unit/infrastructure/test_container.py
def test_mock_container_initialization():
    container = MockInfrastructureContainer(use_mocks=True)
    assert container.mode == "mock"
    assert container.get_redis_client() is not None
    assert container.get_ai_agent() is not None

def test_environment_override():
    os.environ["USE_MOCK_MODE"] = "true"
    container = MockInfrastructureContainer(use_mocks=False)
    assert container.use_mocks == True
```

### Integration Test Command

```bash
# Run new integration tests
pytest tests/integration/test_mock_chat_flow.py -v

# Run with error simulation
USE_MOCK_MODE=true MOCK_ERROR_RATE=0.1 pytest tests/integration/ -v
```

## Success Criteria

### Must Complete

- [ ] MockInfrastructureContainer fully implemented
- [ ] All three MVP scenarios pass integration tests
- [ ] Error simulator integrated with at least one mock component
- [ ] Environment configuration documented

### Validation Steps

1. Run `pytest tests/integration/test_mock_chat_flow.py` - All tests pass
2. Set `USE_MOCK_MODE=false` - System raises NotImplementedError (expected)
3. Set `MOCK_ERROR_RATE=0.5` - Errors occur ~50% of the time
4. Container properly initializes all mock components

## Timeline

| Time | Task | Deliverable |
|------|------|-------------|
| 0:00-2:00 | MockInfrastructureContainer | Dependency injection working |
| 2:00-3:30 | Integration Tests | Three scenarios tested |
| 3:30-4:00 | Error Simulation | Error handling validated |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ChatOrchestrator not ready | Create minimal implementation for testing |
| Environment config conflicts | Use clear prefixes (MOCK_*) |
| Test flakiness | Use fixed seeds and deterministic mocks |

## Conclusion

This implementation plan addresses the remaining 10% of Phase 3, focusing on:
1. **Dependency Injection** - Essential for Phase 4 WebSocket integration
2. **Integration Testing** - Validates MVP scenarios work end-to-end
3. **Error Simulation** - Enables resilience testing

Completing these items will bring Phase 3 to 100% completion and unblock Phase 4 development.
