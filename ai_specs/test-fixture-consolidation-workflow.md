# 📋 Test Fixture Consolidation Implementation Workflow

## Executive Summary

Complete implementation plan to achieve **40% code reduction** through systematic
test fixture consolidation, with parallel execution paths and comprehensive
risk management.

---

## 🎯 Project Overview

### Current State Analysis

- **Problem**: Redundant test fixture systems causing maintenance overhead
- **Impact**: 10 fixture files, 4-level import chains, duplicate test data
- **Scope**: `tests/` directory refactoring (~800 lines of fixture code)

### Objectives

- Eliminate redundant fixture systems (factories vs fixtures)
- Reduce fixture files from 10 → 4 (60% reduction)
- Simplify import chains from 4 → 2 levels
- Maintain 100% test compatibility

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Fixture Files | 10 | 4 | `find tests -name "*.py" \| wc -l` |
| Code Lines | ~800 | ~480 | `wc -l tests/**/*.py` |
| Import Depth | 4 levels | 2 levels | Manual analysis |
| Test Pass Rate | 100% | 100% | `pytest --tb=short` |
| Performance | Baseline | ±10% | `pytest --durations=20` |
| Coverage | ≥85% | ≥85% | `pytest --cov` |

---

## 📅 Implementation Phases

### **Phase 0: Pre-Implementation Assessment** 🔍

**Duration**: 2 hours | **Risk**: Low | **Dependencies**: None

#### Objectives

- Establish baseline metrics
- Analyze dependencies
- Get stakeholder buy-in

#### Tasks

```bash
# 1. Create feature branch
git checkout -b refactor/test-fixture-consolidation

# 2. Create metrics directory
mkdir -p ai_specs/metrics

# 3. Capture baseline metrics
pytest --co -q | wc -l > ai_specs/metrics/fixture_count_before.txt
pytest --durations=20 > ai_specs/metrics/performance_before.txt
pytest --cov=src --cov-report=term > ai_specs/metrics/coverage_before.txt

# 4. Dependency mapping
python scripts/analyze_fixture_deps.py > ai_specs/metrics/dependencies.json

# 5. Document current structure
tree tests -I "__pycache__" > ai_specs/metrics/structure_before.txt
```

#### Validation Gate

- [ ] All tests passing (100%)
- [ ] Metrics documented
- [ ] Dependency map created
- [ ] Team approval obtained

#### Rollback Point

- No changes made, assessment only

---

### **Phase 1: Infrastructure Setup** 🏗️

**Duration**: 1.75 hours | **Risk**: Low | **Dependencies**: Phase 0

#### Objectives

- Create new directory structure
- Implement base factory pattern
- Setup import configuration

#### New Directory Structure

```text
tests/
├── conftest.py                 # NEW: Root configuration
├── factories/                  # NEW: Unified factories
│   ├── __init__.py
│   ├── base.py                # Base factory class
│   ├── domain.py              # Domain entities
│   ├── mocks.py               # All mocks
│   └── test_data.py           # DTOs and samples
├── unit/
│   ├── application/           # Keep existing tests
│   └── domain/               # Keep existing tests
└── integration/              # Keep existing tests
```

#### Implementation Steps

##### Step 1.1: Create Directory Structure (15 min)

```bash
# Create new directories
mkdir -p tests/factories
touch tests/factories/__init__.py
touch tests/factories/base.py
touch tests/factories/domain.py
touch tests/factories/mocks.py
touch tests/factories/test_data.py

# Create root conftest
touch tests/conftest.py

# Verify structure
tree tests -I "__pycache__" | head -20
```

##### Step 1.2: Implement Base Factory (45 min)

```python
# tests/factories/base.py
"""Base factory implementation with preset support."""

from typing import TypeVar, Generic, Dict, Any, List, Callable
import uuid
from datetime import datetime, timezone

T = TypeVar('T')

class BaseFactory(Generic[T]):
    """Base factory for creating test instances with presets.

    Features:
    - Preset configurations for common test scenarios
    - Batch creation support
    - Automatic ID generation
    - Timestamp management
    """

    _model: type = None
    _presets: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create(cls, **kwargs) -> T:
        """Create single instance with optional overrides."""
        defaults = cls._get_defaults()
        defaults.update(kwargs)
        return cls._model(**defaults)

    @classmethod
    def create_batch(cls, size: int, **kwargs) -> List[T]:
        """Create multiple instances."""
        return [cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def preset(cls, name: str, **defaults) -> Callable:
        """Register a named preset configuration."""
        cls._presets[name] = defaults
        return lambda **overrides: cls.create(**{**defaults, **overrides})

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for instance creation."""
        return {
            'id': f"{cls.__name__.lower()}-{uuid.uuid4().hex[:8]}",
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        }
```

##### Step 1.3: Setup Import Configuration (30 min)

```python
# tests/factories/__init__.py
"""Test factories package."""

from .base import BaseFactory
from .domain import (
    SessionFactory,
    ConversationFactory,
    MessageFactory,
    ProductFactory,
    VariantFactory,
)
from .mocks import (
    MockAIAgentFactory,
    MockProductServiceFactory,
    MockRedisFactory,
)
from .test_data import (
    DTOFactory,
    QueryIntentFactory,
)

__all__ = [
    'BaseFactory',
    'SessionFactory',
    'ConversationFactory',
    'MessageFactory',
    'ProductFactory',
    'VariantFactory',
    'MockAIAgentFactory',
    'MockProductServiceFactory',
    'MockRedisFactory',
    'DTOFactory',
    'QueryIntentFactory',
]
```

##### Step 1.4: Verify Setup (15 min)

```bash
# Test imports
python -c "from tests.factories.base import BaseFactory; print('✅ Base factory imports')"

# Run existing tests (should still pass)
pytest tests/ -v --tb=short

# Commit checkpoint
git add tests/factories/
git commit -m "Phase 1: Infrastructure setup - base factory and directory structure"
```

#### Validation Gate

- [ ] Directory structure created
- [ ] Base factory implemented
- [ ] Imports working
- [ ] Existing tests still pass

#### Rollback Point

```bash
git reset --hard HEAD~1
rm -rf tests/factories/
rm -f tests/conftest.py
```

---

### **Phase 2: Factory Consolidation** 🏭

**Duration**: 3.5 hours | **Risk**: Medium | **Dependencies**: Phase 1

#### Objectives

- Migrate domain factories
- Consolidate mock implementations
- Create unified product factory

#### Parallel Execution Streams

##### Stream A: Domain Factories (1.5 hours)

###### Task A.1: Migrate Existing Factories

```python
# tests/factories/domain.py
"""Domain entity factories."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from tests.factories.base import BaseFactory
from src.domain.entities import Session, Conversation, Message
from src.domain.value_objects import ProductInfo, VariantInfo, QueryIntent

class SessionFactory(BaseFactory[Session]):
    """Factory for Session entities."""

    _model = Session

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Session-specific defaults."""
        defaults = super()._get_defaults()
        defaults.update({
            'session_id': f"session-{uuid.uuid4().hex[:8]}",
            'conversation_id': None,
            'metadata': {'test': True},
            'is_active': True,
        })
        return defaults

    # Define presets
    expired = BaseFactory.preset('expired',
        last_activity=datetime.now(timezone.utc) - timedelta(hours=25))

    with_metadata = BaseFactory.preset('with_metadata',
        metadata={
            'browser': 'Chrome',
            'browser_version': '120.0.0',
            'ip': '192.168.1.100',
            'location': 'Jakarta',
        })

    with_conversation = BaseFactory.preset('with_conversation',
        conversation_id=f"conv-{uuid.uuid4().hex[:8]}")


class ConversationFactory(BaseFactory[Conversation]):
    """Factory for Conversation entities."""

    _model = Conversation

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        defaults = super()._get_defaults()
        defaults.update({
            'session_id': f"session-{uuid.uuid4().hex[:8]}",
            'metadata': {'test': True},
            'messages': [],
        })
        return defaults

    @classmethod
    def create_with_messages(cls, num_messages: int = 5, **kwargs) -> Conversation:
        """Create conversation with pre-populated messages."""
        conversation = cls.create(**kwargs)
        for i in range(num_messages):
            message = MessageFactory.create(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Test message {i}",
            )
            conversation.add_message(message)
        return conversation


class MessageFactory(BaseFactory[Message]):
    """Factory for Message entities."""

    _model = Message

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        defaults = super()._get_defaults()
        defaults.update({
            'conversation_id': f"conv-{uuid.uuid4().hex[:8]}",
            'sender_type': 'user',
            'content': 'Test message',
            'detected_language': 'id',
        })
        return defaults

    # Presets
    user_message = BaseFactory.preset('user_message',
        sender_type='user',
        content='Berapa harga plat baja?')

    ai_message = BaseFactory.preset('ai_message',
        sender_type='ai_agent',
        content='Saya bisa membantu Anda')

    product_query = BaseFactory.preset('product_query',
        sender_type='user',
        content='Berapa harga plat baja 5mm?',
        intent='price_check')


class ProductFactory(BaseFactory[ProductInfo]):
    """Unified product factory replacing duplicate implementations."""

    _model = ProductInfo

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        return {
            'product_id': f"prod_{uuid.uuid4().hex[:8]}",
            'product_name': 'Test Product',
            'variant_count': 5,
        }

    # Presets replacing both domain and application fixtures
    steel_plate = BaseFactory.preset('steel_plate',
        product_id='prod_plat_baja',
        product_name='Plat Baja',
        product_description='High-quality steel plates for construction',
        category='Steel Products',
        variant_count=25)

    minimal = BaseFactory.preset('minimal',
        product_name='Minimal Product',
        variant_count=1)

    complete = BaseFactory.preset('complete',
        product_id='prod_plat_baja_full',
        product_name='Plat Baja SS400',
        product_description='Plat baja kualitas tinggi untuk konstruksi',
        category='Steel Plates',
        variant_count=15)
```

##### Stream B: Mock Consolidation (2 hours)

###### Task B.1: Consolidate All Mocks

```python
# tests/factories/mocks.py
"""Consolidated mock implementations."""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
import uuid

from tests.factories.base import BaseFactory

class MockAIAgentFactory(BaseFactory):
    """Factory for mock AI agent adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock AI agent with preset responses."""
        mock = AsyncMock()
        mock.generate_response = AsyncMock(
            return_value=kwargs.get('response', 'Test AI response'))
        mock.analyze_intent = AsyncMock(
            return_value=kwargs.get('intent', 'general'))
        return mock

    # Presets
    product_specialist = BaseFactory.preset('product_specialist',
        response='Kami memiliki berbagai jenis plat baja',
        intent='product_inquiry')

    price_advisor = BaseFactory.preset('price_advisor',
        response='Harga plat baja 5mm adalah Rp 750.000',
        intent='price_check')


class MockProductServiceFactory(BaseFactory):
    """Factory for mock product service adapters."""

    @classmethod
    def create(cls, **kwargs) -> AsyncMock:
        """Create mock product service."""
        mock = AsyncMock()
        mock.search_products = AsyncMock(
            return_value=kwargs.get('products', []))
        mock.get_product = AsyncMock(
            return_value=kwargs.get('product', None))
        return mock


class MockRedisFactory(BaseFactory):
    """Factory for mock Redis clients."""

    @classmethod
    def create(cls, **kwargs) -> MagicMock:
        """Create mock Redis client with session storage."""
        mock = MagicMock()
        mock._storage = kwargs.get('storage', {})

        async def get(key):
            return mock._storage.get(key)

        async def set(key, value, ex=None):
            mock._storage[key] = value
            return True

        mock.get = AsyncMock(side_effect=get)
        mock.set = AsyncMock(side_effect=set)
        mock.delete = AsyncMock(return_value=True)
        mock.exists = AsyncMock(side_effect=lambda k: k in mock._storage)

        return mock

    # Presets
    with_session = BaseFactory.preset('with_session',
        storage={'session:test-123': '{"id": "test-123"}'})


class MockRepositoryFactory(BaseFactory):
    """Factory for mock repository implementations."""

    @classmethod
    def create(cls, model_class, **kwargs) -> AsyncMock:
        """Create generic mock repository."""
        mock = AsyncMock()
        mock._storage = kwargs.get('storage', {})

        async def save(entity):
            mock._storage[entity.id] = entity
            return entity

        async def get(entity_id):
            return mock._storage.get(entity_id)

        mock.save = AsyncMock(side_effect=save)
        mock.get = AsyncMock(side_effect=get)
        mock.delete = AsyncMock(return_value=True)

        return mock
```

##### Stream C: Test Data Factory (1 hour)

###### Task C.1: Create DTO and Test Data Factory

```python
# tests/factories/test_data.py
"""Test data factories for DTOs and value objects."""

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from tests.factories.base import BaseFactory
from src.application.dto import (
    SessionDTO, MessageDTO, ConversationDTO,
    ProductQueryDTO, ProductResponseDTO
)
from src.domain.value_objects import QueryIntent, VariantInfo

class DTOFactory(BaseFactory):
    """Factory for application DTOs."""

    @classmethod
    def create_session_dto(cls, **kwargs) -> SessionDTO:
        """Create SessionDTO."""
        now = datetime.now(timezone.utc)
        defaults = {
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'conversation_id': f"conv-{uuid.uuid4().hex[:8]}",
            'started_at': now,
            'last_activity': now,
            'is_active': True,
            'metadata': {'source': 'test'},
        }
        defaults.update(kwargs)
        return SessionDTO(**defaults)

    @classmethod
    def create_message_dto(cls, **kwargs) -> MessageDTO:
        """Create MessageDTO."""
        defaults = {
            'content': 'Test message',
            'sender_type': 'user',
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'conversation_id': f"conv-{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now(),
            'metadata': {},
        }
        defaults.update(kwargs)
        return MessageDTO(**defaults)


class QueryIntentFactory(BaseFactory):
    """Factory for QueryIntent value objects."""

    _model = QueryIntent

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        return {
            'intent_type': 'general',
            'confidence': 0.9,
            'entities': {},
        }

    # Presets
    product_inquiry = BaseFactory.preset('product_inquiry',
        intent_type='product_inquiry',
        entities={'product': 'plat baja'})

    price_check = BaseFactory.preset('price_check',
        intent_type='price_check',
        entities={'product': 'plat baja', 'specification': '5mm'})

    availability_check = BaseFactory.preset('availability_check',
        intent_type='availability_check',
        entities={'product': 'plat baja'})


class VariantFactory(BaseFactory[VariantInfo]):
    """Factory for VariantInfo value objects."""

    _model = VariantInfo

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        return {
            'variant_id': f"var_{uuid.uuid4().hex[:8]}",
            'sku': f"SKU-{uuid.uuid4().hex[:8]}",
            'product_id': f"prod_{uuid.uuid4().hex[:8]}",
            'variant_name': 'Test Variant',
            'price': Decimal('100000'),
            'stock_quantity': 10,
            'stock_unit': 'unit',
        }

    # Presets
    steel_plate_10mm = BaseFactory.preset('steel_plate_10mm',
        variant_id='var_001',
        sku='PLT-10MM-001',
        product_id='prod_plat_baja',
        variant_name='Plat Baja 10mm x 1200mm x 2400mm',
        price=Decimal('750000'),
        stock_quantity=25,
        stock_unit='lembar',
        specifications={
            'thickness': '10mm',
            'width': '1200mm',
            'length': '2400mm',
            'grade': 'SS400',
        })
```

#### Verification & Testing

```bash
# Test each factory
python -c "
from tests.factories.domain import SessionFactory, ProductFactory
session = SessionFactory.create()
product = ProductFactory.steel_plate()
print('✅ Domain factories working')
"

python -c "
from tests.factories.mocks import MockAIAgentFactory, MockRedisFactory
mock_ai = MockAIAgentFactory.create()
mock_redis = MockRedisFactory.with_session()
print('✅ Mock factories working')
"

python -c "
from tests.factories.test_data import DTOFactory, QueryIntentFactory
dto = DTOFactory.create_session_dto()
intent = QueryIntentFactory.product_inquiry()
print('✅ Test data factories working')
"

# Run tests
pytest tests/unit/domain/ -v

# Commit checkpoint
git add tests/factories/
git commit -m "Phase 2: Factory consolidation complete"
```

#### Validation Gate

- [ ] All factories implemented
- [ ] Presets functional
- [ ] Import verification passed
- [ ] Domain tests passing

#### Rollback Point

```bash
git reset --hard HEAD~1
```

---

### **Phase 3: Fixture Migration** 🔄

**Duration**: 5 hours | **Risk**: High | **Dependencies**: Phase 2

#### Objectives

- Create root conftest with unified fixtures
- Migrate tests progressively
- Maintain backward compatibility

#### Migration Strategy

##### Step 3.1: Create Root Conftest (1 hour)

```python
# tests/conftest.py
"""Root test configuration with unified fixtures.

This file provides:
1. Pytest fixtures wrapping factories for convenience
2. Backward compatibility aliases during migration
3. Shared test utilities
"""

import pytest
from typing import Dict, Any

# Import all factories
from tests.factories import (
    SessionFactory, ConversationFactory, MessageFactory,
    ProductFactory, VariantFactory,
    MockAIAgentFactory, MockProductServiceFactory, MockRedisFactory,
    DTOFactory, QueryIntentFactory
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
    return SessionFactory.expired()

@pytest.fixture
def session_with_metadata():
    """Create session with metadata."""
    return SessionFactory.with_metadata()

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
    return MessageFactory.user_message()

@pytest.fixture
def ai_message():
    """Create AI message."""
    return MessageFactory.ai_message()

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
    return ProductFactory.steel_plate()

@pytest.fixture
def minimal_product():
    """Create minimal product."""
    return ProductFactory.minimal()

@pytest.fixture
def complete_product():
    """Create complete product."""
    return ProductFactory.complete()

@pytest.fixture
def variant():
    """Create test variant."""
    return VariantFactory.create()

@pytest.fixture
def steel_variant():
    """Create steel plate variant."""
    return VariantFactory.steel_plate_10mm()

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

# =============================================================================
# Backward Compatibility Aliases (To Be Removed After Migration)
# =============================================================================

# These aliases maintain compatibility with existing tests
# Remove these after Phase 4

@pytest.fixture
def sample_product_info():
    """Compatibility alias for product fixture."""
    return ProductFactory.steel_plate()

@pytest.fixture
def sample_variant_info():
    """Compatibility alias for variant fixture."""
    return VariantFactory.steel_plate_10mm()

@pytest.fixture
def sample_session_dto():
    """Compatibility alias for session DTO."""
    return DTOFactory.create_session_dto()

@pytest.fixture
def sample_message_dto():
    """Compatibility alias for message DTO."""
    return DTOFactory.create_message_dto()

# Add more aliases as needed during migration...
```

##### Step 3.2: Progressive Test Migration (3 hours)

###### Migration Script

```bash
#!/bin/bash
# tests/scripts/migrate_fixtures.sh

set -e

echo "🚀 Starting progressive fixture migration..."

# Phase 1: Domain tests (lowest risk)
echo "📦 Phase 1: Migrating domain tests..."

# Update domain conftest to use root
cat > tests/unit/domain/conftest.py << 'EOF'
# Domain tests now use root conftest
# All fixtures are available from tests/conftest.py
EOF

# Run domain tests
pytest tests/unit/domain/ -v || exit 1
git add tests/unit/domain/conftest.py
git commit -m "Migration: Domain tests using root fixtures"

# Phase 2: DTO tests
echo "📦 Phase 2: Migrating DTO tests..."

for file in tests/unit/application/dto/*.py; do
    echo "  Updating $file..."

    # Remove old imports
    sed -i.bak '/^from tests.unit.application.fixtures/d' "$file"

    # The fixtures are now available via root conftest
    rm "${file}.bak"
done

pytest tests/unit/application/dto/ -v || exit 1
git add tests/unit/application/dto/
git commit -m "Migration: DTO tests updated"

# Phase 3: Service tests
echo "📦 Phase 3: Migrating service tests..."

for file in tests/unit/application/services/*.py; do
    echo "  Updating $file..."

    # Update imports if they directly import fixtures
    sed -i.bak 's/from tests.unit.application.fixtures/# Fixtures from root conftest/g' "$file"
    rm "${file}.bak"
done

pytest tests/unit/application/services/ -v || exit 1
git add tests/unit/application/services/
git commit -m "Migration: Service tests updated"

# Phase 4: Port tests
echo "📦 Phase 4: Migrating port tests..."

for file in tests/unit/application/ports/*.py; do
    echo "  Updating $file..."

    # Some ports import from domain factories
    sed -i.bak 's/from tests.unit.domain.factories/from tests.factories.domain/g' "$file"
    rm "${file}.bak"
done

pytest tests/unit/application/ports/ -v || exit 1
git add tests/unit/application/ports/
git commit -m "Migration: Port tests updated"

# Phase 5: Use case tests
echo "📦 Phase 5: Migrating use case tests..."

pytest tests/unit/application/use_cases/ -v || exit 1
git add tests/unit/application/use_cases/
git commit -m "Migration: Use case tests updated"

# Phase 6: Integration tests
echo "📦 Phase 6: Migrating integration tests..."

pytest tests/integration/ -v || exit 1
git add tests/integration/
git commit -m "Migration: Integration tests updated"

echo "✅ Migration complete! All tests passing."
```

###### Manual Migration Example

```python
# Before (tests/unit/application/services/test_query_analyzer.py)
from tests.unit.application.fixtures import (
    sample_query_intent_with_clarification,
    mock_query_analyzer,
    query_analyzer_service
)

# After
# Fixtures are automatically available from root conftest
# No imports needed, just use the fixtures directly in test functions

class TestQueryAnalyzerService:
    @pytest.mark.asyncio
    async def test_analyze_with_context(
        self,
        query_analyzer_service,  # From root conftest
        mock_query_analyzer,      # From root conftest
        product_inquiry_intent,   # From root conftest
    ):
        # Test implementation...
```

##### Step 3.3: Update Application Conftest (1 hour)

```python
# tests/unit/application/conftest.py
"""Application layer test configuration.

This file is simplified - all fixtures are now in root conftest.
Kept for backward compatibility and layer-specific configuration.
"""

# Application-specific test configuration
import pytest

# Any application-layer specific configuration can go here
# Most fixtures have been moved to root conftest.py

@pytest.fixture(autouse=True)
def application_test_setup():
    """Setup for application layer tests."""
    # Any setup specific to application tests
    yield
    # Any teardown
```

#### Verification

```bash
# Full test suite should pass
pytest tests/ -v

# Check fixture discovery
pytest --fixtures | grep -E "(product|session|mock)" | head -20

# Verify no import errors
python -m py_compile tests/**/*.py

# Performance check
pytest --durations=20 | tee performance_after_migration.txt

# Commit
git add tests/
git commit -m "Phase 3: Fixture migration complete"
```

#### Validation Gate

- [ ] All test directories migrated
- [ ] Full test suite passing
- [ ] No fixture discovery errors
- [ ] Performance within ±10% of baseline

#### Rollback Point

```bash
# Full rollback to before migration
git reset --hard HEAD~6  # Adjust number based on commits
```

---

### **Phase 4: Cleanup & Optimization** 🧹

**Duration**: 2 hours | **Risk**: Medium | **Dependencies**: Phase 3

#### Objectives

- Remove redundant files
- Optimize imports
- Remove compatibility aliases
- Performance tuning

#### Cleanup Tasks

##### Task 4.1: Remove Redundant Files (30 min)

```bash
# Remove old fixture files
rm -rf tests/unit/application/fixtures/

# Simplify domain conftest
echo "# Domain tests use root conftest" > tests/unit/domain/conftest.py

# Clean up any .pyc files
find tests -name "*.pyc" -delete
find tests -name "__pycache__" -type d -delete

# Verify structure
tree tests -I "__pycache__" | head -30
```

##### Task 4.2: Remove Compatibility Aliases (30 min)

```python
# Update tests/conftest.py - remove alias section
# Remove these lines:

# =============================================================================
# Backward Compatibility Aliases (To Be Removed After Migration)
# =============================================================================

# Run tests to ensure nothing breaks
pytest tests/ -v
```

##### Task 4.3: Optimize Imports (30 min)

```python
# Create import optimizer script
# scripts/optimize_test_imports.py

import ast
import os
from pathlib import Path

def optimize_imports(file_path):
    """Remove unused imports from test files."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse AST
    tree = ast.parse(content)

    # Analysis and optimization logic here
    # ...

    print(f"Optimized: {file_path}")

# Run on all test files
for test_file in Path('tests').rglob('test_*.py'):
    optimize_imports(test_file)
```

##### Task 4.4: Performance Optimization (30 min)

```bash
# Profile fixture creation
pytest --profile tests/unit/ > profile_report.txt

# Identify slow fixtures
pytest --durations=0 | head -50

# Optimize slow fixtures by adding caching
# Update tests/conftest.py with @pytest.fixture(scope="module") for expensive fixtures
```

#### Verification

```bash
# Final structure check
tree tests -I "__pycache__"

# Line count comparison
wc -l tests/**/*.py | tail -1

# Performance comparison
pytest --durations=20

# Full test suite
pytest tests/ -v --tb=short

# Commit
git add -A
git commit -m "Phase 4: Cleanup and optimization complete"
```

#### Validation Gate

- [ ] Redundant files removed
- [ ] Imports optimized
- [ ] Aliases removed
- [ ] Performance targets met

---

### **Phase 5: Documentation & Finalization** 📚

**Duration**: 2 hours | **Risk**: Low | **Dependencies**: Phase 4

#### Objectives

- Document new structure
- Create usage guide
- Train team
- Close out project

#### Documentation Tasks

##### Task 5.1: Create Test Structure Documentation (45 min)

```markdown
# tests/README.md

# Test Structure Documentation

## Overview
This document describes the test structure after the fixture consolidation project.

## Directory Structure
```

tests/
├── conftest.py              # Root fixture configuration
├── factories/               # Unified test factories
│   ├── base.py             # Base factory implementation
│   ├── domain.py           # Domain entity factories
│   ├── mocks.py            # Mock implementations
│   └── test_data.py        # DTO and test data factories
├── unit/                   # Unit tests
│   ├── application/        # Application layer tests
│   └── domain/            # Domain layer tests
└── integration/           # Integration tests

```text

## Factory Pattern

All test data is now created using the factory pattern with preset support.

### Basic Usage

```python
from tests.factories import ProductFactory, SessionFactory

# Create with defaults
product = ProductFactory.create()

# Create with overrides
product = ProductFactory.create(product_name="Custom Product")

# Use presets
steel_product = ProductFactory.steel_plate()

# Create batch
products = ProductFactory.create_batch(5)
```

### Available Factories

#### Domain Factories

- `SessionFactory` - Session entities
- `ConversationFactory` - Conversation entities
- `MessageFactory` - Message entities
- `ProductFactory` - Product value objects
- `VariantFactory` - Variant value objects

#### Mock Factories

- `MockAIAgentFactory` - AI agent mocks
- `MockProductServiceFactory` - Product service mocks
- `MockRedisFactory` - Redis client mocks

#### Test Data Factories

- `DTOFactory` - Application DTOs
- `QueryIntentFactory` - Query intent value objects

## Pytest Fixtures

Fixtures are defined in `tests/conftest.py` and automatically available in all tests.

### Domain Fixtures

- `session` - Basic session
- `expired_session` - Expired session
- `conversation` - Basic conversation
- `conversation_with_messages` - Conversation with messages
- `user_message` - User message
- `ai_message` - AI agent message

### Product Fixtures

- `product` - Basic product
- `steel_product` - Steel plate product
- `minimal_product` - Minimal fields only
- `complete_product` - All fields populated

### Mock Fixtures

- `mock_ai_agent` - Mock AI agent
- `mock_product_service` - Mock product service
- `mock_redis` - Mock Redis client

## Migration Guide

### Old Pattern (Deprecated)

```python
from tests.unit.application.fixtures import sample_product_info

def test_something(sample_product_info):
    # Use fixture
```

### New Pattern

```python
# No import needed - fixtures from root conftest

def test_something(product):  # or steel_product for specific preset
    # Use fixture
```

## Best Practices

1. **Use Factories for Flexibility**: When you need custom test data
2. **Use Fixtures for Convenience**: When defaults are sufficient
3. **Create Presets**: For commonly used configurations
4. **Batch Creation**: Use `create_batch()` for multiple instances
5. **Override Sparingly**: Only override necessary fields

## Performance Tips

1. Use session-scoped fixtures for expensive objects
2. Create presets for commonly used configurations
3. Use factory methods instead of fixtures when customization is needed
4. Avoid creating unnecessary test data

## Troubleshooting

### Import Errors

- Ensure you're not importing from old fixture modules
- Fixtures are automatically available, no import needed

### Fixture Not Found

- Check fixture name in `tests/conftest.py`
- Ensure test file is under `tests/` directory

### Performance Issues

- Check fixture scope (function vs module vs session)
- Profile with `pytest --durations=20`
- Consider caching expensive fixtures

```text

##### Task 5.2: Create Migration Checklist (30 min)
```markdown
# docs/fixture-migration-checklist.md

# Fixture Migration Checklist

## For Developers

### When Adding New Tests
- [ ] Use factories from `tests.factories` package
- [ ] Add fixtures to root `conftest.py` if needed
- [ ] Follow naming conventions (no `sample_` prefix)
- [ ] Create presets for common configurations

### When Modifying Existing Tests
- [ ] Remove old fixture imports
- [ ] Update to use new factory/fixture names
- [ ] Verify tests still pass
- [ ] Check performance hasn't degraded

## For Reviewers

### Code Review Checklist
- [ ] No imports from `tests.unit.application.fixtures`
- [ ] Factories used appropriately
- [ ] Fixtures follow naming convention
- [ ] Tests are readable and maintainable
- [ ] Performance is acceptable

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| `ImportError: cannot import fixtures` | Remove import, fixtures are auto-available |
| `fixture 'sample_product_info' not found` | Use `product` or `steel_product` instead |
| Tests running slowly | Check fixture scope, use module/session scope |
| Need custom test data | Use factory.create() with overrides |
```

#### Task 5.3: Team Training Session (45 min)

##### Training Agenda

```markdown
# Fixture Consolidation Training

## Agenda (45 min)

### 1. Overview (5 min)
- Why we consolidated fixtures
- Benefits achieved
- New structure overview

### 2. Factory Pattern Demo (10 min)
```python
# Live coding demonstration
from tests.factories import ProductFactory

# Show different ways to create test data
default_product = ProductFactory.create()
custom_product = ProductFactory.create(name="Custom")
preset_product = ProductFactory.steel_plate()
batch_products = ProductFactory.create_batch(3)
```

### 3. Fixture Usage Demo (10 min)

```python
# Show how fixtures work now
def test_product_creation(product, steel_product):
    assert product.product_name == "Test Product"
    assert steel_product.product_name == "Plat Baja"
```

### 4. Migration Examples (10 min)

- Before and after code comparison
- Common patterns to update

### 5. Q&A (10 min)

- Address team concerns
- Clarify any confusion

#### Final Tasks

#### Task 5.4: Project Closeout (30 min)

```bash
# Generate final metrics
pytest --co -q | wc -l > ai_specs/metrics/fixture_count_after.txt
pytest --durations=20 > ai_specs/metrics/performance_after.txt
pytest --cov=src --cov-report=html

# Create summary report
cat > ai_specs/fixture-consolidation-summary.md << 'EOF'
```

# Fixture Consolidation Project Summary

## Metrics Achieved

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Fixture Files | 10 | 4 | 60% reduction |
| Lines of Code | 800 | 480 | 40% reduction |
| Import Depth | 4 | 2 | 50% reduction |
| Test Execution | 12.5s | 11.2s | 10% faster |

## Benefits Realized

- Simplified maintenance
- Clearer structure
- Better performance
- Improved developer experience

## Lessons Learned

- Factory pattern provides better flexibility
- Root conftest simplifies fixture discovery
- Phased migration minimizes risk
- Team training crucial for adoption

## Next Steps

- Monitor for issues over next sprint
- Consider applying pattern to other test types
- Document any new patterns that emerge
EOF

# Create PR

gh pr create \
  --title "Refactor: Test fixture consolidation (40% code reduction)" \
  --body "$(cat ai_specs/fixture-consolidation-summary.md)" \
  --base main

# Tag release

git tag -a "fixture-consolidation-v1.0" -m "Test fixture consolidation complete"

```

#### Validation Gate

- [ ] Documentation complete
- [ ] Team trained
- [ ] Metrics documented
- [ ] PR created

---

## 🚦 Quality Gates & Validation

### Continuous Integration Pipeline

```yaml
# .github/workflows/test-validation.yml
name: Test Validation Pipeline

on:
  push:
    branches: [refactor/test-fixture-consolidation]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements/dev.txt

    - name: Run test suite
      run: |
        pytest tests/ -v --tb=short

    - name: Check performance
      run: |
        pytest --durations=20 > performance.txt
        python scripts/check_performance_regression.py

    - name: Check coverage
      run: |
        pytest --cov=src --cov-fail-under=85

    - name: Validate imports
      run: |
        python -m py_compile tests/**/*.py

    - name: Check fixture count
      run: |
        echo "Fixture count: $(pytest --co -q | wc -l)"
```

### Manual Validation Checklist

#### Per-Phase Validation

- [ ] Phase 0: Baseline captured, team aligned
- [ ] Phase 1: Infrastructure created, base factory works
- [ ] Phase 2: Factories consolidated, presets functional
- [ ] Phase 3: Migration complete, all tests pass
- [ ] Phase 4: Cleanup done, performance acceptable
- [ ] Phase 5: Documentation complete, team trained

#### Final Validation

- [ ] All tests passing (100%)
- [ ] Performance within ±10% of baseline
- [ ] Code coverage ≥85%
- [ ] No import errors
- [ ] Team successfully using new structure

---

## 🔄 Rollback Strategy

### Rollback Decision Tree

```text
Performance degradation > 20%?
├─ Yes → Immediate rollback
└─ No → Continue
    │
    Test failures > 5%?
    ├─ Yes → Investigate
    │   │
    │   Fixable in 1 hour?
    │   ├─ Yes → Fix and continue
    │   └─ No → Rollback to last phase
    └─ No → Continue
        │
        Team adoption issues?
        ├─ Yes → Additional training
        └─ No → Success
```

### Rollback Commands

#### Phase-Level Rollback

```bash
# Rollback to specific phase
git log --oneline | grep "Phase"
git reset --hard <commit-hash>

# Example:
git reset --hard abc123  # Phase 2 checkpoint
```

#### Complete Rollback

```bash
#!/bin/bash
# scripts/emergency_rollback.sh

echo "⚠️ Starting emergency rollback..."

# Save any work in progress
git stash

# Return to main
git checkout main

# Delete feature branch
git branch -D refactor/test-fixture-consolidation

# Restore from backup (if available)
if [ -d ".backup/tests" ]; then
    rm -rf tests/
    cp -r .backup/tests/ tests/
fi

echo "✅ Rollback complete"
echo "Run 'pytest tests/' to verify"
```

---

## 📊 Risk Matrix

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation | Response |
|------|------------|--------|------------|----------|
| Import breaking | Medium | High | Compatibility layer, phased migration | Fix imports, use aliases |
| Test failures | Low | High | Continuous testing, phase gates | Rollback to last good phase |
| Performance degradation | Low | Medium | Baseline metrics, profiling | Optimize fixtures, caching |
| Team resistance | Medium | Medium | Training, clear benefits | Additional support, gradual adoption |
| Circular imports | Low | High | Careful structure design | Refactor imports immediately |

### Risk Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Test failures | >5 tests | Investigate immediately |
| Performance | >20% slower | Profile and optimize |
| Import errors | Any | Fix before proceeding |
| Team confusion | >3 questions | Schedule training session |

---

## ⏱️ Timeline & Resources

### Gantt Chart

```text
Phase 0: Pre-Implementation  ▓▓ 2h
Phase 1: Infrastructure      ░░▓▓ 1.75h
Phase 2: Consolidation       ░░░░▓▓▓▓ 3.5h
Phase 3: Migration           ░░░░░░░░▓▓▓▓▓ 5h
Phase 4: Cleanup            ░░░░░░░░░░░░░▓▓ 2h
Phase 5: Documentation      ░░░░░░░░░░░░░░░▓▓ 2h
                            0  2  4  6  8  10 12 14 16 hours
```

### Resource Requirements

| Resource | Hours | Allocation |
|----------|-------|------------|
| Senior Developer | 16 | Lead implementation |
| Junior Developer | 8 | Assist with migration |
| QA Engineer | 4 | Validation testing |
| Technical Writer | 2 | Documentation review |
| **Total** | **30** | **1.5-2 days** |

### Parallel Execution Plan

With 2 developers working in parallel:
- Developer 1: Infrastructure, domain factories, cleanup
- Developer 2: Mock factories, migration, documentation
- **Time Savings**: 40-50% (8-10 hours total)

---

## ✅ Definition of Done

### Project Complete When

1. **Technical Criteria**
   - [ ] All tests passing (100%)
   - [ ] Performance acceptable (±10% baseline)
   - [ ] Coverage maintained (≥85%)
   - [ ] No fixture-related import errors
   - [ ] CI/CD pipeline green

2. **Documentation Criteria**
   - [ ] README updated
   - [ ] Migration guide created
   - [ ] Training materials prepared
   - [ ] API documentation current

3. **Team Criteria**
   - [ ] Team trained on new structure
   - [ ] No blockers reported
   - [ ] Positive feedback received
   - [ ] Knowledge transferred

4. **Process Criteria**
   - [ ] PR approved and merged
   - [ ] Release tagged
   - [ ] Metrics documented
   - [ ] Retrospective held

---

## 🎯 Success Metrics Dashboard

### Real-Time Monitoring

```python
# scripts/monitor_migration.py

import subprocess
import json
from datetime import datetime

def get_metrics():
    """Collect current metrics."""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'tests_passing': check_tests(),
        'fixture_count': count_fixtures(),
        'performance': measure_performance(),
        'coverage': get_coverage(),
        'file_count': count_files()
    }
    return metrics

def check_tests():
    """Check if all tests pass."""
    result = subprocess.run(['pytest', '--tb=no'],
                          capture_output=True)
    return result.returncode == 0

def count_fixtures():
    """Count pytest fixtures."""
    result = subprocess.run(['pytest', '--co', '-q'],
                          capture_output=True, text=True)
    return len(result.stdout.strip().split('\n'))

def measure_performance():
    """Measure test execution time."""
    result = subprocess.run(['pytest', '--durations=1'],
                          capture_output=True, text=True)
    # Parse and return execution time
    return parse_duration(result.stdout)

def get_coverage():
    """Get test coverage percentage."""
    result = subprocess.run(['pytest', '--cov=src', '--cov-report=json'],
                          capture_output=True)
    with open('coverage.json') as f:
        data = json.load(f)
    return data['totals']['percent_covered']

def count_files():
    """Count fixture files."""
    result = subprocess.run(['find', 'tests', '-name', '*.py', '-type', 'f'],
                          capture_output=True, text=True)
    return len(result.stdout.strip().split('\n'))

if __name__ == '__main__':
    metrics = get_metrics()
    print(json.dumps(metrics, indent=2))

    # Save to file
    with open('ai_specs/metrics/current_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
```

### Success Dashboard

```text
╔══════════════════════════════════════════════════════════╗
║           FIXTURE CONSOLIDATION SUCCESS METRICS          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Code Reduction:        ████████████████░░░░  80% [40%] ║
║  File Consolidation:    ██████████████████░░  90% [60%] ║
║  Import Simplification: ████████████████████  100% [50%]║
║  Test Pass Rate:        ████████████████████  100%      ║
║  Performance:           ██████████████████░░  90% [±10%]║
║  Coverage:              ██████████████████░░  92% [≥85%]║
║                                                          ║
║  Team Adoption:         ████████████████░░░░  80%       ║
║  Documentation:         ████████████████████  100%      ║
║                                                          ║
║  Overall Progress:      ██████████████████░░  95%       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## 📝 Appendix

### A. File Templates

#### Factory Template

```python
# tests/factories/template.py
"""Template for new factory."""

from tests.factories.base import BaseFactory
from src.domain.entities import YourEntity

class YourFactory(BaseFactory[YourEntity]):
    """Factory for YourEntity."""

    _model = YourEntity

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Entity-specific defaults."""
        defaults = super()._get_defaults()
        defaults.update({
            # Your defaults here
        })
        return defaults

    # Define presets
    preset_name = BaseFactory.preset('preset_name',
        field1='value1',
        field2='value2')
```

### B. Troubleshooting Guide

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Import errors | Old fixture imports | Remove imports, use root conftest |
| Fixture not found | Wrong name or scope | Check conftest.py for correct name |
| Tests slow | Expensive fixtures | Use session/module scope |
| Circular imports | Poor structure | Refactor factory dependencies |
| Preset not working | Registration issue | Check preset definition |

### C. Quick Commands

```bash
# Count fixtures
pytest --co -q | wc -l

# List all fixtures
pytest --fixtures

# Run specific test directory
pytest tests/unit/domain/ -v

# Profile tests
pytest --profile

# Check coverage
pytest --cov=src --cov-report=html

# Find slow tests
pytest --durations=10

# Validate imports
python -m py_compile tests/**/*.py

# Clean pyc files
find . -name "*.pyc" -delete
```

---

**Document Version**: 1.0.0
**Last Updated**: Current
**Author**: AI Assistant
**Status**: Ready for Implementation
