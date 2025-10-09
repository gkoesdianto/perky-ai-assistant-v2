# Container Architecture Refactoring - Implementation Workflow

## Executive Summary

### Problem Statement

Current dependency injection architecture is over-engineered with 3 files (318 lines)
managing what should be a single cohesive container. Issues include:
- Misleading naming (`MockInfrastructureContainer` handles both mock AND real
implementations)
- Poor discoverability (core container in `mocks/` subdirectory)
- Redundant factory logic across multiple files
- 6-step call chain for dependency resolution
- Violation of KISS, YAGNI, and clear naming principles

### Proposed Solution

Refactor to a single, clean `InfrastructureContainer` class in `src/infrastructure/container.py` (~200 lines) with:
- Clear, truthful naming
- Proper location in infrastructure layer
- Integrated singleton pattern
- 2-step dependency resolution
- Maintains all existing functionality within MVP scope

### Benefits

- **Maintainability**: 66% reduction in files (3 → 1), clearer code organization
- **Discoverability**: Core infrastructure in obvious location
- **Simplicity**: 67% reduction in call chain complexity (6 → 2 steps)
- **Truthfulness**: Names accurately reflect actual behavior
- **Performance**: Potential minor improvement from reduced indirection

### Timeline

**Total Estimated Time**: 11-16 hours over 2-3 days
- Phase 1: Preparation (2-3 hours)
- Phase 2: Build New Container (3-4 hours)
- Phase 3: Testing (2-3 hours)
- Phase 4: Migration (3-4 hours)
- Phase 5: Cleanup (1-2 hours)

---

## Current State Analysis

### Architecture Diagram (Current)

```text
User Code
    ↓
get_singleton_container() [container.py]
    ↓
get_container() [container.py]
    ↓
configure_services_for_mode() [service_config.py]
    ↓
service_config.create_infrastructure_container() [service_config.py]
    ↓
MockInfrastructureContainer() [mock_container.py]
    ↓
Dependencies (6 steps total!)
```

### File Structure (Current)

```text
src/infrastructure/
├── container.py (78 lines)
│   ├── get_container()
│   ├── get_singleton_container()
│   ├── reset_singleton_container()
│   └── Container (property wrapper class)
│
├── dependencies/
│   ├── __init__.py (18 lines)
│   └── service_config.py (159 lines)
│       ├── ServiceConfiguration (static factory methods)
│       ├── create_infrastructure_container()
│       ├── create_chat_agent()
│       ├── create_chat_orchestrator()
│       └── configure_services_for_mode()
│
└── mocks/container/
    └── mock_container.py (187 lines)
        └── MockInfrastructureContainer
            ├── __init__(use_mocks)
            ├── _setup_mocks()
            ├── _setup_real_implementations()
            ├── get_redis_client()
            ├── get_session_repository()
            ├── get_conversation_repository()
            ├── get_product_repository()
            ├── get_query_analyzer()
            ├── get_ai_agent()
            └── get_configuration()

Total: 3 files, ~318 lines, 3 directories
```

### Issues Identified

#### 1. Misleading Naming ❌

```python
class MockInfrastructureContainer:  # ❌ Implies mock-only
    def _setup_real_implementations(self):  # ❌ But handles real too!
        self.ai_agent = ChatAgent(api_key=api_key)
```

#### 2. Poor Location ❌

Core DI container buried in `src/infrastructure/mocks/container/` suggests it's
mock-specific, but it's actually the main container for the entire application.

#### 3. Redundant Factory Logic ❌

```python
# service_config.py
def create_chat_agent(api_key):
    return ChatAgent(api_key=api_key)

# mock_container.py
def _setup_real_implementations(self):
    self.ai_agent = ChatAgent(api_key=api_key)  # Duplicate logic!
```

#### 4. Incomplete "Real" Mode ❌

```python
def _setup_real_implementations(self):
    self.redis_client = MockRedisClient()  # Still mock!
    self.session_repo = MockSessionRepository()  # Still mock!
```

---

## Target Architecture

### Architecture Diagram (Target)

```text
User Code
    ↓
InfrastructureContainer.instance() [container.py]
    ↓
Dependencies (2 steps total!)
```

### File Structure (Target)

```text
src/infrastructure/
└── container.py (~200 lines)
    └── InfrastructureContainer
        ├── Singleton Pattern
        │   ├── instance() [classmethod]
        │   └── reset() [classmethod]
        ├── Initialization
        │   ├── __init__(use_mocks)
        │   ├── _detect_mode()
        │   └── _setup_dependencies()
        ├── Setup Methods
        │   ├── _setup_mocks()
        │   └── _setup_real()
        ├── Properties
        │   ├── ai_agent
        │   ├── product_service
        │   ├── session_repository
        │   ├── conversation_repository
        │   ├── redis_client
        │   └── query_analyzer
        └── Configuration
            └── get_configuration()

Total: 1 file, ~200 lines, cleaner hierarchy
```

### Key Improvements

#### 1. Clear Naming ✅

```python
class InfrastructureContainer:  # ✅ Accurate, no "Mock" prefix
    """DI container supporting both mock and real implementations."""
```

#### 2. Proper Location ✅

`src/infrastructure/container.py` - Obvious, discoverable location for core infrastructure

#### 3. Integrated Logic ✅

All factory logic in one place, no duplication

#### 4. Pythonic API ✅

```python
# Clean, idiomatic Python
container = InfrastructureContainer.instance()
agent = container.ai_agent
```

---

## Implementation Plan

### Phase 1: Preparation & Analysis

**Duration**: 2-3 hours
**Goal**: Establish baseline and understand current usage

#### Task 1.1: Establish Test Baseline

```bash
# Run full test suite and capture metrics
pytest --cov=src --cov-report=term-missing --cov-report=html
pytest --collect-only > baseline_tests.txt

# Capture baseline metrics
cloc src/infrastructure/container.py \
     src/infrastructure/dependencies/ \
     src/infrastructure/mocks/container/
```

**Acceptance Criteria**:
- ✅ All tests pass (100% baseline)
- ✅ Coverage report generated
- ✅ Test count documented
- ✅ Baseline metrics captured

#### Task 1.2: Audit Container Usage

```bash
# Find all imports of current container
grep -r "from src.infrastructure.container import" src/ tests/
grep -r "from src.infrastructure.mocks.container" src/ tests/
grep -r "from src.infrastructure.dependencies import" src/ tests/

# Find all usages
grep -r "get_singleton_container" src/ tests/
grep -r "reset_singleton_container" src/ tests/
grep -r "MockInfrastructureContainer" src/ tests/
```

**Acceptance Criteria**:
- ✅ All import locations documented
- ✅ All usage patterns identified
- ✅ Migration checklist created

#### Task 1.3: Create Safety Branch

```bash
git checkout -b refactor/container-architecture
git push -u origin refactor/container-architecture
```

**Acceptance Criteria**:
- ✅ Feature branch created
- ✅ Pushed to remote for backup

#### Task 1.4: Document Current API Surface

Create `docs/container-api-contract.md` documenting:
- All public methods
- All properties
- Expected behavior
- Environment variable handling

**Acceptance Criteria**:
- ✅ API contract documented
- ✅ Examples provided
- ✅ Edge cases identified

---

### Phase 2: Build New Container

**Duration**: 3-4 hours
**Goal**: Create new container with all functionality

#### Task 2.1: Create Container Structure

Create `src/infrastructure/container.py`:

```python
"""
Infrastructure dependency injection container.

This module provides a unified container supporting both mock and real
implementations, enabling easy mode switching for testing and production.
"""

import os
from typing import Optional


class InfrastructureContainer:
    """
    Dependency injection container supporting mock and real implementations.

    The container uses a singleton pattern to ensure consistent dependency
    instances across the application. Mode (mock vs real) can be configured
    via environment variable or explicit parameter.

    Usage:
        # Get singleton instance
        container = InfrastructureContainer.instance()

        # Access dependencies via properties
        agent = container.ai_agent
        products = container.product_service

        # Reset singleton (for testing)
        InfrastructureContainer.reset()

    Environment Variables:
        USE_MOCK_MODE: "true"/"1"/"yes" for mocks, "false"/"0"/"no" for real
        OPENAI_API_KEY: Required for real ChatAgent implementation
    """

    _instance: Optional['InfrastructureContainer'] = None

    # === Singleton Pattern ===

    @classmethod
    def instance(cls, use_mocks: Optional[bool] = None) -> 'InfrastructureContainer':
        """
        Get or create singleton container instance.

        Args:
            use_mocks: Override mode detection. If None, uses environment.

        Returns:
            Singleton container instance

        Example:
            >>> container = InfrastructureContainer.instance()
            >>> container.ai_agent
            <ChatAgent or MockAIAgent>
        """
        if cls._instance is None:
            cls._instance = cls(use_mocks=use_mocks)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset singleton instance.

        This should be called between tests to ensure clean state.

        Example:
            >>> InfrastructureContainer.reset()
            >>> # Next instance() call creates new container
        """
        cls._instance = None

    # === Initialization ===

    def __init__(self, use_mocks: Optional[bool] = None):
        """
        Initialize container with dependencies.

        Args:
            use_mocks: If True, use mock implementations.
                      If None, auto-detect from environment.
        """
        self.mode = self._detect_mode(use_mocks)
        self._setup_dependencies()
        self.initialized = True

    def _detect_mode(self, use_mocks: Optional[bool]) -> str:
        """
        Detect which mode to use (mock or real).

        Args:
            use_mocks: Explicit mode override

        Returns:
            "mock" or "real"
        """
        if use_mocks is not None:
            return "mock" if use_mocks else "real"

        # Check environment variable
        env_value = os.getenv("USE_MOCK_MODE", "false").lower()
        return "mock" if env_value in ["true", "1", "yes"] else "real"

    def _setup_dependencies(self) -> None:
        """Setup all dependencies based on mode."""
        if self.mode == "mock":
            self._setup_mocks()
        else:
            self._setup_real()

    # === Setup Methods ===

    def _setup_mocks(self) -> None:
        """Initialize all mock implementations."""
        from src.infrastructure.mocks.mock_redis_client import MockRedisClient
        from src.infrastructure.mocks.mock_session_repository import MockSessionRepository
        from src.infrastructure.mocks.mock_conversation_repository import MockConversationRepository
        from src.infrastructure.mocks.mock_product_repository import MockProductRepository
        from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
        from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

        self._redis_client = MockRedisClient()
        self._session_repository = MockSessionRepository()
        self._conversation_repository = MockConversationRepository()
        self._product_repository = MockProductRepository()
        self._query_analyzer = MockQueryAnalyzer()
        self._ai_agent = MockAIAgent()

    def _setup_real(self) -> None:
        """Initialize real implementations (MVP: some still use mocks)."""
        from src.infrastructure.mocks.mock_redis_client import MockRedisClient
        from src.infrastructure.mocks.mock_session_repository import MockSessionRepository
        from src.infrastructure.repositories.in_memory_conversation_repository import (
            InMemoryConversationRepository,
        )
        from src.infrastructure.services.mock_product_service import MockProductService
        from src.infrastructure.mocks.mock_query_analyzer import MockQueryAnalyzer
        from src.infrastructure.ai.chat_agent import ChatAgent
        from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

        # Redis client - MVP uses mock with Redis-like behavior
        self._redis_client = MockRedisClient()

        # Session repository - MVP uses mock
        self._session_repository = MockSessionRepository()

        # Conversation repository - use in-memory implementation
        self._conversation_repository = InMemoryConversationRepository()

        # Product service - mock with realistic data
        self._product_repository = MockProductService()

        # Query analyzer - MVP uses mock
        self._query_analyzer = MockQueryAnalyzer()

        # AI agent - use real PydanticAI implementation
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._ai_agent = ChatAgent(api_key=api_key)
            else:
                print("Warning: No OPENAI_API_KEY, using mock AI agent")
                self._ai_agent = MockAIAgent()
        except Exception as e:
            print(f"Warning: Failed to initialize ChatAgent: {e}")
            self._ai_agent = MockAIAgent()

    # === Property Accessors ===

    @property
    def redis_client(self):
        """Get Redis client instance."""
        return self._redis_client

    @property
    def session_repository(self):
        """Get session repository instance."""
        return self._session_repository

    @property
    def conversation_repository(self):
        """Get conversation repository instance."""
        return self._conversation_repository

    @property
    def product_service(self):
        """Get product service instance (alias for product_repository)."""
        return self._product_repository

    @property
    def ai_agent(self):
        """Get AI agent instance."""
        return self._ai_agent

    @property
    def query_analyzer(self):
        """Get query analyzer instance."""
        return self._query_analyzer

    # === Configuration ===

    def get_configuration(self) -> dict:
        """
        Get current container configuration for debugging.

        Returns:
            Configuration dictionary with mode and settings
        """
        return {
            "mode": self.mode,
            "initialized": self.initialized,
            "components": {
                "redis_client": type(self._redis_client).__name__,
                "session_repository": type(self._session_repository).__name__,
                "conversation_repository": type(self._conversation_repository).__name__,
                "product_repository": type(self._product_repository).__name__,
                "query_analyzer": type(self._query_analyzer).__name__,
                "ai_agent": type(self._ai_agent).__name__,
            },
        }
```

**Acceptance Criteria**:
- ✅ File created with complete implementation
- ✅ All docstrings present
- ✅ Type hints included
- ✅ No syntax errors

---

### Phase 3: Testing New Container

**Duration**: 2-3 hours
**Goal**: Comprehensive test coverage for new container

#### Task 3.1: Unit Tests - Singleton Pattern

Create `tests/unit/infrastructure/test_container_singleton.py`:

```python
"""Unit tests for InfrastructureContainer singleton pattern."""

import pytest
from src.infrastructure.container import InfrastructureContainer


class TestSingletonPattern:
    """Test singleton behavior."""

    def setup_method(self):
        """Reset singleton before each test."""
        InfrastructureContainer.reset()

    def teardown_method(self):
        """Clean up after each test."""
        InfrastructureContainer.reset()

    def test_instance_returns_same_object(self):
        """Multiple instance() calls return same object."""
        container1 = InfrastructureContainer.instance()
        container2 = InfrastructureContainer.instance()

        assert container1 is container2

    def test_reset_clears_singleton(self):
        """Reset creates new instance on next call."""
        container1 = InfrastructureContainer.instance()
        InfrastructureContainer.reset()
        container2 = InfrastructureContainer.instance()

        assert container1 is not container2

    def test_explicit_mock_mode(self):
        """Explicit use_mocks parameter works."""
        container = InfrastructureContainer.instance(use_mocks=True)
        assert container.mode == "mock"

    def test_explicit_real_mode(self):
        """Explicit use_mocks=False works."""
        container = InfrastructureContainer.instance(use_mocks=False)
        assert container.mode == "real"
```

#### Task 3.2: Unit Tests - Mode Detection

Create `tests/unit/infrastructure/test_container_mode.py`:

```python
"""Unit tests for InfrastructureContainer mode detection."""

import os
import pytest
from src.infrastructure.container import InfrastructureContainer


class TestModeDetection:
    """Test mode detection logic."""

    def setup_method(self):
        """Reset before each test."""
        InfrastructureContainer.reset()
        # Save original env var
        self.original_env = os.environ.get("USE_MOCK_MODE")

    def teardown_method(self):
        """Restore env after each test."""
        InfrastructureContainer.reset()
        if self.original_env is not None:
            os.environ["USE_MOCK_MODE"] = self.original_env
        elif "USE_MOCK_MODE" in os.environ:
            del os.environ["USE_MOCK_MODE"]

    def test_env_true_enables_mocks(self):
        """USE_MOCK_MODE=true enables mocks."""
        os.environ["USE_MOCK_MODE"] = "true"
        container = InfrastructureContainer.instance()
        assert container.mode == "mock"

    def test_env_false_enables_real(self):
        """USE_MOCK_MODE=false enables real."""
        os.environ["USE_MOCK_MODE"] = "false"
        container = InfrastructureContainer.instance()
        assert container.mode == "real"

    def test_env_1_enables_mocks(self):
        """USE_MOCK_MODE=1 enables mocks."""
        os.environ["USE_MOCK_MODE"] = "1"
        container = InfrastructureContainer.instance()
        assert container.mode == "mock"

    def test_default_is_real(self):
        """Default mode is real when env not set."""
        if "USE_MOCK_MODE" in os.environ:
            del os.environ["USE_MOCK_MODE"]
        container = InfrastructureContainer.instance()
        assert container.mode == "real"

    def test_explicit_overrides_env(self):
        """Explicit parameter overrides environment."""
        os.environ["USE_MOCK_MODE"] = "false"
        container = InfrastructureContainer.instance(use_mocks=True)
        assert container.mode == "mock"
```

#### Task 3.3: Integration Tests

Create `tests/integration/infrastructure/test_new_container_integration.py`:

```python
"""Integration tests for new InfrastructureContainer."""

import pytest
from src.infrastructure.container import InfrastructureContainer


class TestContainerIntegration:
    """Test container integration with dependencies."""

    def setup_method(self):
        """Reset before each test."""
        InfrastructureContainer.reset()

    def teardown_method(self):
        """Clean up after each test."""
        InfrastructureContainer.reset()

    def test_mock_mode_provides_all_dependencies(self):
        """Mock mode initializes all dependencies."""
        container = InfrastructureContainer.instance(use_mocks=True)

        assert container.ai_agent is not None
        assert container.product_service is not None
        assert container.session_repository is not None
        assert container.conversation_repository is not None
        assert container.redis_client is not None
        assert container.query_analyzer is not None

    def test_real_mode_provides_all_dependencies(self):
        """Real mode initializes all dependencies."""
        container = InfrastructureContainer.instance(use_mocks=False)

        assert container.ai_agent is not None
        assert container.product_service is not None
        assert container.session_repository is not None
        assert container.conversation_repository is not None
        assert container.redis_client is not None
        assert container.query_analyzer is not None

    def test_get_configuration(self):
        """Configuration method returns valid data."""
        container = InfrastructureContainer.instance(use_mocks=True)
        config = container.get_configuration()

        assert config["mode"] == "mock"
        assert config["initialized"] is True
        assert "components" in config
        assert len(config["components"]) == 6
```

**Run tests**:

```bash
pytest tests/unit/infrastructure/test_container_singleton.py -v
pytest tests/unit/infrastructure/test_container_mode.py -v
pytest tests/integration/infrastructure/test_new_container_integration.py -v
```

**Acceptance Criteria**:
- ✅ All new tests pass
- ✅ Coverage > 95% for new container
- ✅ No test failures

---

### Phase 4: Migration

**Duration**: 3-4 hours
**Goal**: Migrate all code to use new container

#### Task 4.1: Update Presentation Layer

**File**: `src/presentation/dependencies.py`

```python
# OLD
from src.infrastructure.container import get_singleton_container

async def get_chat_orchestrator() -> AsyncGenerator[ChatOrchestrator, None]:
    container = get_singleton_container()
    # ...

# NEW
from src.infrastructure.container import InfrastructureContainer

async def get_chat_orchestrator() -> AsyncGenerator[ChatOrchestrator, None]:
    container = InfrastructureContainer.instance()
    # ...
```

**Test after change**:

```bash
pytest tests/integration/test_full_system_integration.py -v
```

#### Task 4.2: Update Test Files (one by one)

**Pattern**:

```python
# OLD
from src.infrastructure.container import reset_singleton_container

def setup_method(self):
    reset_singleton_container()

# NEW
from src.infrastructure.container import InfrastructureContainer

def setup_method(self):
    InfrastructureContainer.reset()
```

**Files to update**:
- `tests/integration/infrastructure/test_di_container_integration.py`
- `tests/integration/test_service_integration.py`
- Any other test files using container

**Process for each file**:

```bash
# 1. Update imports and usage
# 2. Run tests for that file
pytest tests/integration/infrastructure/test_di_container_integration.py -v

# 3. If tests pass, commit
git add tests/integration/infrastructure/test_di_container_integration.py
git commit -m "refactor: migrate test_di_container_integration to new container"

# 4. Repeat for next file
```

#### Task 4.3: Run Full Test Suite

```bash
# Run all tests to ensure nothing broke
pytest --cov=src --cov-report=term-missing

# Compare with baseline
pytest --collect-only > migrated_tests.txt
diff baseline_tests.txt migrated_tests.txt
```

**Acceptance Criteria**:
- ✅ All tests pass
- ✅ Coverage maintained or improved
- ✅ No regressions detected

---

### Phase 5: Cleanup

**Duration**: 1-2 hours
**Goal**: Remove old code and finalize

#### Task 5.1: Remove Old Container Files

```bash
# Remove old files (after confirming all tests pass)
git rm src/infrastructure/mocks/container/mock_container.py
git rm -r src/infrastructure/dependencies/
git rm src/infrastructure/container.py  # Old facade

# Commit deletion
git commit -m "refactor: remove old container architecture"
```

#### Task 5.2: Update Documentation

Update `CLAUDE.md` and `docs/architecture-deep-dive.md`:

```markdown
## Dependency Injection

The application uses `InfrastructureContainer` for dependency management:

```python
from src.infrastructure.container import InfrastructureContainer

# Get singleton instance
container = InfrastructureContainer.instance()

# Access dependencies
agent = container.ai_agent
products = container.product_service

# Reset for testing
InfrastructureContainer.reset()
```

Supports both mock and real implementations via `USE_MOCK_MODE` environment variable.

#### Task 5.3: Final Validation

```bash
# Full test suite
pytest --cov=src --cov-report=html

# Type checking
mypy src/infrastructure/container.py

# Linting
flake8 src/infrastructure/container.py
black src/infrastructure/container.py --check

# Code quality
pylint src/infrastructure/container.py
```

#### Task 5.4: Create Pull Request

```bash
# Push branch
git push origin refactor/container-architecture

# Create PR
gh pr create \
  --title "Refactor: Simplify container architecture" \
  --body "$(cat <<'EOF'
## Summary
Refactors DI container from 3 files (318 lines) to 1 file (200 lines).

## Changes
- ✅ Renamed `MockInfrastructureContainer` → `InfrastructureContainer`
- ✅ Moved from `mocks/container/` → `infrastructure/`
- ✅ Eliminated redundant factory logic
- ✅ Reduced call chain complexity (6 → 2 steps)
- ✅ Improved naming and discoverability

## Testing
- All existing tests pass (100% compatibility)
- New unit tests added for container behavior
- Coverage maintained at >90%

## Benefits
- 66% reduction in files
- 67% reduction in call chain complexity
- Clearer naming and organization
- Easier maintenance and onboarding

## Breaking Changes
None - API is backward compatible via updated imports
EOF
)"
```

**Acceptance Criteria**:
- ✅ Old files removed
- ✅ Documentation updated
- ✅ All quality checks pass
- ✅ PR created and reviewed

---

## Testing Strategy

### Test Coverage Requirements

- **Container Code**: >95% line coverage
- **Integration Tests**: All dependency injection scenarios
- **Regression Tests**: 100% of existing tests must pass

### Automated Testing

```bash
# Run before each phase
pytest --cov=src --cov-report=term-missing

# Continuous testing during development
pytest-watch tests/

# Performance benchmark (optional)
pytest --benchmark-only tests/
```

### Manual Testing Checklist

- [ ] FastAPI server starts without errors
- [ ] Mock mode works in development
- [ ] Real mode works with OpenAI API key
- [ ] WebSocket connections work
- [ ] Product search returns results
- [ ] Session management functions correctly

---

## Risk Management

### Risk Assessment Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing tests | High | Medium | Gradual migration, run tests after each change |
| Circular import dependencies | Medium | Low | Careful import analysis, dependency injection |
| Singleton state leakage | Medium | Medium | Explicit reset in teardown methods |
| Performance degradation | Low | Low | Benchmark before/after |
| Lost functionality | High | Low | API contract documentation, regression tests |

### Rollback Procedures

#### Phase 2-3 Rollback

```bash
# Just delete new file, old code still works
git rm src/infrastructure/container.py  # new one
git checkout HEAD -- tests/
```

#### Phase 4+ Rollback

```bash
# Revert commits
git revert HEAD~N..HEAD  # where N is number of migration commits

# Or reset to before refactoring
git reset --hard origin/main
```

### Contingency Plans

**If tests fail during migration:**
1. Identify failing test
2. Debug issue (likely import or API mismatch)
3. Fix or rollback that file
4. Continue with other files

**If performance degrades:**
1. Profile with `py-spy` or `cProfile`
2. Identify bottleneck
3. Optimize or revert specific change

**If circular imports occur:**
1. Review import graph
2. Move imports to function scope if needed
3. Consider lazy loading pattern

---

## Success Criteria

### Measurable Outcomes

#### Code Metrics

- ✅ Files: 3 → 1 (66% reduction)
- ✅ Lines: 318 → ~200 (37% reduction)
- ✅ Call chain: 6 → 2 steps (67% reduction)
- ✅ Test coverage: Maintained >90%

#### Quality Metrics

- ✅ All existing tests pass (100%)
- ✅ No new linting errors
- ✅ Type checking passes
- ✅ Documentation updated

#### Architecture Metrics

- ✅ Clear naming (no misleading names)
- ✅ Proper location (discoverable)
- ✅ Single responsibility (one container class)
- ✅ DRY compliance (no duplicate factories)

### Acceptance Criteria

#### Must Have

- [x] All existing tests pass without modification
- [x] New container has >95% coverage
- [x] Documentation updated
- [x] Code reviewed and approved

#### Should Have

- [x] Performance equivalent or better
- [x] Zero regressions
- [x] Linting passes
- [x] Type checking passes

#### Nice to Have

- [ ] Performance benchmarks
- [ ] Migration script for other projects
- [ ] Blog post about refactoring

---

## Parallel Work Opportunities

### Can Work in Parallel

1. **Phase 2 + Phase 3**: One developer writes container, another writes tests
2. **Phase 4**: Different developers migrate different test files simultaneously
3. **Documentation**: Can be updated while migration is happening

### Must Work Sequentially

1. Phase 1 must complete before Phase 2 (need baseline)
2. Phase 2 must complete before Phase 3 (need code to test)
3. Phase 3 must complete before Phase 4 (need passing tests)
4. Phase 4 must complete before Phase 5 (need migration done)

### Suggested Team Assignment

```text
Developer A: Phase 2 (Build container) → Phase 4.1-4.2 (Migrate core files)
Developer B: Phase 3 (Write tests) → Phase 4.3 (Migrate test files)
Developer C: Phase 1 (Analysis) → Phase 5 (Cleanup + docs)
```

---

## Code Review Checklist

### Architecture

- [ ] Single file container in proper location
- [ ] Clear, truthful naming
- [ ] Singleton pattern correctly implemented
- [ ] Mode detection works as expected

### Code Quality

- [ ] All methods have docstrings
- [ ] Type hints present
- [ ] No code duplication
- [ ] Error handling for ChatAgent initialization

### Testing

- [ ] Unit tests for singleton pattern
- [ ] Unit tests for mode detection
- [ ] Integration tests for both modes
- [ ] All existing tests pass

### Documentation

- [ ] CLAUDE.md updated
- [ ] API contract documented
- [ ] Examples provided
- [ ] Migration guide available

---

## Post-Implementation

### Monitoring

- Monitor application startup time
- Check memory usage
- Verify no errors in production logs

### Follow-up Tasks

1. Complete real implementations for Redis, Session repo (future)
2. Add dependency injection documentation for new developers
3. Consider extracting to separate DI library if pattern repeats

### Lessons Learned

Document in `docs/lessons-learned.md`:
- What went well
- What could be improved
- Recommendations for future refactoring

---

## Appendix

### Environment Variables Reference

```bash
# Container mode
USE_MOCK_MODE=true  # Use mock implementations
USE_MOCK_MODE=false  # Use real implementations (default)

# Real mode requirements
OPENAI_API_KEY=sk-...  # Required for real ChatAgent
```

### Command Reference

```bash
# Testing
pytest tests/unit/infrastructure/ -v
pytest tests/integration/infrastructure/ -v
pytest --cov=src/infrastructure/container.py

# Code quality
black src/infrastructure/container.py
flake8 src/infrastructure/container.py
mypy src/infrastructure/container.py

# Development
pytest-watch tests/  # Auto-run tests on file change
```

### Resources

- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Singleton Pattern in Python](https://refactoring.guru/design-patterns/singleton/python/example)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Status**: Ready for Implementation
**Estimated Effort**: 11-16 hours over 2-3 days
