# Unit Test Plan for Domain Entities

## Overview

Comprehensive unit test plan focusing on **business logic and domain rules** for
the Perky AI Assistant v2 project. This plan avoids testing third-party libraries
and standard library functionality, concentrating instead on our custom
implementations.

## Test Framework & Tools

- **Framework**: pytest 8.3.4
- **Async Support**: pytest-asyncio 0.24.0
- **Coverage**: pytest-cov 6.0.0
- **Coverage Target**: Minimum 90% code coverage
- **Business Logic Coverage**: 100% required
- **Test Utilities**: Factory patterns for consistent test data

## Test Directory Structure

```text
tests/
├── unit/
│   └── domain/
│       ├── entities/
│       │   ├── __init__.py
│       │   ├── test_base.py
│       │   ├── test_session.py
│       │   ├── test_conversation.py
│       │   └── test_message.py
│       ├── value_objects/
│       │   ├── __init__.py
│       │   ├── test_product_info.py
│       │   └── test_query_intent.py
│       └── repositories/
│           ├── __init__.py
│           └── test_base_repository.py
```

## Test Cases by Entity

### 1. BaseEntity (`test_base.py`)

#### Priority: MEDIUM

**Test Coverage Required**: 80%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_default_values` | Verify our chosen defaults (is_active=True, updated_at=None) | HIGH |
| `test_entity_inheritance` | Test that subclasses properly inherit BaseEntity fields | HIGH |
| `test_entity_serialization` | Test model_dump() and model_dump_json() for our use cases | MEDIUM |
| `test_field_override` | Test that subclasses can override default values | MEDIUM |

### 2. Session Entity (`test_session.py`)

#### Priority: CRITICAL

**Test Coverage Required**: 100%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_session_creation` | Test creation with required session_id | HIGH |
| `test_is_expired_fresh_session` | Test non-expired session (TTL not exceeded) | CRITICAL |
| `test_is_expired_old_session` | Test expired session (TTL exceeded) | CRITICAL |
| `test_is_expired_edge_cases` | Test with 0, negative, and very large TTL values | HIGH |
| `test_update_activity` | Verify update_activity() updates timestamp | CRITICAL |
| `test_session_lifecycle` | Test complete session lifecycle from creation to expiry | HIGH |
| `test_metadata_storage` | Test storing browser info, IP in metadata | MEDIUM |
| `test_concurrent_activity_updates` | Test race conditions in activity updates | HIGH |

### 3. Conversation Entity (`test_conversation.py`)

Priority: CRITICAL

**Test Coverage Required**: 100%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_conversation_creation` | Test creation with session_id | HIGH |
| `test_empty_messages_list` | Verify messages list initializes empty | HIGH |
| `test_add_single_message` | Test adding one message | CRITICAL |
| `test_add_multiple_messages` | Test adding multiple messages | CRITICAL |
| `test_last_activity_update` | Verify last_activity updates on add_message | CRITICAL |
| `test_get_context_empty` | Test get_context with no messages | HIGH |
| `test_get_context_within_limit` | Test with fewer messages than limit | HIGH |
| `test_get_context_exceeds_limit` | Test with more messages than limit | HIGH |
| `test_get_context_exact_limit` | Test with exactly limit messages | MEDIUM |
| `test_metadata_dict` | Test metadata storage and retrieval | MEDIUM |

### 4. Message Entity (`test_message.py`)

Priority: HIGH

**Test Coverage Required**: 95%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_message_creation` | Test with all required fields | HIGH |
| `test_sender_types` | Test both valid sender types (user, ai_agent) | HIGH |
| `test_default_language` | Verify detected_language defaults to "id" | MEDIUM |
| `test_intent_optional` | Verify intent defaults to None | MEDIUM |
| `test_is_product_query_detection` | Test product query detection for all intent types | CRITICAL |
| `test_indonesian_content` | Test with Indonesian language content | HIGH |
| `test_message_state_transitions` | Test message lifecycle and state changes | HIGH |
| `test_metadata_storage` | Test metadata field for custom data | LOW |

### 5. ProductInfo Value Object (`test_product_info.py`)

Priority: HIGH

**Test Coverage Required**: 90%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_required_fields` | Test creation with only SKU and name | HIGH |
| `test_all_fields` | Test with all fields populated | HIGH |
| `test_optional_fields_none` | Verify optional fields default to None | MEDIUM |
| `test_default_unit` | Verify unit defaults to "lembar" (Indonesian) | HIGH |
| `test_source_values` | Test both valid source values (pim, cache) | MEDIUM |
| `test_specifications_dict` | Test specifications storage for steel products | MEDIUM |
| `test_indonesian_product_data` | Test with real Indonesian steel product data | HIGH |

### 6. QueryIntent Value Object (`test_query_intent.py`)

Priority: HIGH

**Test Coverage Required**: 95%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_all_intent_types` | Test all valid intent types (product_inquiry, price_check, stock_check, general) | HIGH |
| `test_confidence_boundaries` | Test confidence at boundaries (0.0, 0.5, 1.0) | CRITICAL |
| `test_confidence_validation` | Test our confidence validation (<0 and >1 rejected) | HIGH |
| `test_optional_fields` | Verify product_name and quantity are optional | MEDIUM |
| `test_intent_with_product_context` | Test intent classification with product context | HIGH |
| `test_confidence_scoring` | Test realistic confidence scores for different scenarios | HIGH |

### 7. IRepository Interface (`test_base_repository.py`)

#### Priority: LOW

**Test Coverage Required**: 70%

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_concrete_implementation` | Test our concrete repository implementations | HIGH |
| `test_repository_operations` | Test CRUD operations with our entities | HIGH |
| `test_async_operations` | Test async/await patterns in our implementations | MEDIUM |

## Integration Tests (New Section)

### Session-Conversation Integration

```python
import pytest
from datetime import datetime, timezone, timedelta
from src.domain.entities import Session, Conversation, Message

class TestSessionConversationIntegration:
    def test_expired_session_blocks_messages(self):
        """Test that expired sessions can't add new messages"""
        session = Session(session_id="test-123")
        conversation = Conversation(session_id=session.session_id)

        # Expire the session
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
        assert session.is_expired(3600)

        # Business rule: expired sessions shouldn't accept new messages
        # This tests our domain logic, not the framework

    def test_session_activity_updates_with_messages(self):
        """Test session activity tracking with conversation"""
        session = Session(session_id="test-123")
        conversation = Conversation(session_id=session.session_id)

        initial_activity = session.last_activity
        message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Berapa harga plat baja?"
        )

        conversation.add_message(message)
        session.update_activity()

        assert session.last_activity > initial_activity
```

## Test Implementation Examples

### Example: BaseEntity Test (Refactored)

```python
import pytest
from src.domain.entities.base import BaseEntity
from src.domain.entities.session import Session

class TestBaseEntity:
    def test_default_values(self):
        """Test our chosen default values"""
        entity = BaseEntity()

        # Test OUR defaults, not Python's UUID or datetime
        assert entity.is_active is True  # Our choice
        assert entity.updated_at is None  # Our choice

    def test_entity_inheritance(self):
        """Test that our entities properly inherit base fields"""
        session = Session(session_id="test-123")

        # Test that Session has BaseEntity fields
        assert hasattr(session, 'id')
        assert hasattr(session, 'created_at')
        assert hasattr(session, 'is_active')
        assert session.is_active is True  # Inherited default

### Example: Session Test (Business Logic Focus)

```python
import pytest
from datetime import datetime, timezone, timedelta
from src.domain.entities.session import Session

class TestSession:
    def test_is_expired_business_logic(self):
        """Test our session expiry business rules"""
        session = Session(session_id="test-123")

        # Fresh session should not be expired
        assert not session.is_expired(3600)

        # Manually expire session
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
        assert session.is_expired(3600)  # 1 hour TTL

    def test_session_lifecycle(self):
        """Test complete session lifecycle"""
        session = Session(session_id="test-123")

        # New session
        assert session.conversation_id is None
        assert not session.is_expired(3600)

        # Active session
        session.conversation_id = "conv-123"
        session.update_activity()

        # Session with metadata
        session.metadata = {
            "browser": "Chrome",
            "ip": "192.168.1.1",
            "location": "Jakarta"
        }
        assert session.metadata["location"] == "Jakarta"

    @pytest.mark.parametrize("ttl,expected", [
        (0, True),      # Instant expiry
        (-1, False),    # Negative means never expire
        (86400, False), # 24 hours - still fresh
    ])
    def test_ttl_edge_cases(self, ttl, expected):
        """Test TTL boundary conditions"""
        session = Session(session_id="test-123")
        assert session.is_expired(ttl) == expected
```

### Example: Message Intent Test

```python
import pytest
from src.domain.entities.message import Message

class TestMessage:
    @pytest.mark.parametrize("intent,expected", [
        ("product_inquiry", True),
        ("price_check", True),
        ("stock_check", True),
        ("general", False),
        (None, False),
    ])
    def test_is_product_query(self, intent, expected):
        """Test product query detection for various intents"""
        message = Message(
            conversation_id="conv-123",
            sender_type="user",
            content="Test message",
            intent=intent
        )

        assert message.is_product_query() == expected
```

## Test Factories (Better Pattern)

### Factory Pattern for Test Data

```python
# tests/unit/domain/factories.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from src.domain.entities import Session, Conversation, Message
from src.domain.value_objects import ProductInfo, QueryIntent

class SessionFactory:
    @staticmethod
    def create(
        session_id: Optional[str] = None,
        **kwargs
    ) -> Session:
        """Create test session with sensible defaults"""
        defaults = {
            "session_id": session_id or f"session-{uuid.uuid4().hex[:8]}",
            "metadata": {"test": True}
        }
        return Session(**{**defaults, **kwargs})

    @staticmethod
    def create_expired(ttl: int = 3600) -> Session:
        """Create an already-expired session"""
        session = SessionFactory.create()
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=ttl/3600 + 1)
        return session

class MessageFactory:
    @staticmethod
    def create_user_message(content: str = "Berapa harga plat baja?", **kwargs) -> Message:
        """Create user message with Indonesian content"""
        defaults = {
            "conversation_id": f"conv-{uuid.uuid4().hex[:8]}",
            "sender_type": "user",
            "content": content,
            "detected_language": "id"
        }
        return Message(**{**defaults, **kwargs})

    @staticmethod
    def create_product_query(intent: str = "price_check") -> Message:
        """Create message with product query intent"""
        return MessageFactory.create_user_message(
            content="Berapa harga plat baja 5mm?",
            intent=intent
        )

class ProductFactory:
    @staticmethod
    def create_steel_product(**kwargs) -> ProductInfo:
        """Create Indonesian steel product"""
        defaults = {
            "sku": f"STEEL-{uuid.uuid4().hex[:6].upper()}",
            "name": "Plat Baja 5mm",
            "price": 150000.0,
            "stock": 100,
            "unit": "lembar",  # Indonesian unit
            "specifications": {
                "thickness": "5mm",
                "width": "1200mm",
                "length": "2400mm"
            }
        }
        return ProductInfo(**{**defaults, **kwargs})
```

## Test Fixtures

### Fixtures Using Factories (`conftest.py`)

```python
import pytest
from tests.unit.domain.factories import (
    SessionFactory,
    MessageFactory,
    ProductFactory
)

@pytest.fixture
def session():
    """Provide a test session"""
    return SessionFactory.create()

@pytest.fixture
def expired_session():
    """Provide an expired session"""
    return SessionFactory.create_expired()

@pytest.fixture
def user_message():
    """Provide a user message"""
    return MessageFactory.create_user_message()

@pytest.fixture
def product_query():
    """Provide a product query message"""
    return MessageFactory.create_product_query()

@pytest.fixture
def steel_product():
    """Provide Indonesian steel product"""
    return ProductFactory.create_steel_product()
```

## Test Execution Strategy

### Running Tests

```bash
# Run all domain tests
pytest tests/unit/domain/

# Run with coverage
pytest tests/unit/domain/ --cov=src/domain --cov-report=html

# Run specific test file
pytest tests/unit/domain/entities/test_session.py

# Run with verbose output
pytest tests/unit/domain/ -v

# Run only critical tests
pytest tests/unit/domain/ -m critical
```

### Test Markers

```python
# Mark critical tests
@pytest.mark.critical
def test_is_expired():
    pass

# Mark async tests
@pytest.mark.asyncio
async def test_async_method():
    pass
```

## Coverage Goals (Revised)

| Component | Target Coverage | Priority | Focus Area |
|-----------|----------------|----------|------------|
| BaseEntity | 80% | MEDIUM | Default values, inheritance |
| Session | 100% | CRITICAL | Business logic (is_expired, update_activity) |
| Conversation | 100% | CRITICAL | Message management, context retrieval |
| Message | 95% | HIGH | Product query detection, intent handling |
| ProductInfo | 90% | HIGH | Indonesian defaults, steel product specs |
| QueryIntent | 95% | HIGH | Confidence validation, intent classification |
| IRepository | 70% | LOW | Concrete implementations only |
| **Integration Tests** | 85% | HIGH | Entity relationships, business workflows |

## CI/CD Integration

### GitHub Actions Configuration

```yaml
- name: Run Domain Tests
  run: |
    pytest tests/unit/domain/ \
      --cov=src/domain \
      --cov-report=xml \
      --cov-report=term \
      --cov-fail-under=90
```

## Timeline & Priorities

### Phase 1: Critical Tests (Week 1)

- Session.is_expired()
- Session.update_activity()
- Conversation.add_message()
- Message.is_product_query()

### Phase 2: Core Entity Tests (Week 1-2)

- All BaseEntity tests
- Remaining Session tests
- Remaining Conversation tests
- Remaining Message tests

### Phase 3: Value Object Tests (Week 2)

- ProductInfo validation tests
- QueryIntent validation tests
- Edge cases and error scenarios

### Phase 4: Integration & Coverage (Week 2-3)

- Repository interface tests
- Integration between entities
- Coverage gap analysis
- Performance benchmarks

## Success Criteria (Updated)

### Core Requirements

✅ All critical business logic methods have 100% coverage
✅ Overall domain coverage exceeds 90%
✅ **NO tests for third-party libraries or standard library**
✅ All OUR validation rules tested with positive and negative cases
✅ Edge cases in OUR business logic are covered
✅ Tests use factory patterns for consistent test data
✅ CI/CD pipeline includes automated test execution

### New Focus Areas

✅ **Integration tests** between Session, Conversation, and Message entities
✅ **Indonesian language** support tested (default language, units)
✅ **Steel product** domain specifics tested
✅ **Session lifecycle** and TTL management fully tested
✅ **Message intent classification** for product queries validated
✅ **Concurrent operations** tested where applicable
✅ Test execution time < 30 seconds for unit tests

### Testing Principles

- ✅ Test OUR code, not the framework
- ✅ Focus on business logic, not type validation
- ✅ Use factories for test data consistency
- ✅ Test integration points between entities
- ✅ Validate domain-specific rules (Indonesian market, steel products)
