# Container API Contract Documentation

## Current Container Architecture

### Public API Surface

#### Module: `src.infrastructure.container`

**Functions:**

1. **`get_singleton_container() -> Container`**
   - Returns the singleton container instance
   - Creates container if not exists using `configure_services_for_mode()`
   - Thread-safe singleton pattern
   - Environment: Respects `USE_MOCK_MODE` environment variable

2. **`reset_singleton_container() -> None`**
   - Resets the singleton container instance to None
   - Used in testing to ensure clean state between tests
   - No parameters, no return value

3. **`get_container() -> MockInfrastructureContainer`**
   - Internal function called by `get_singleton_container()`
   - Returns new MockInfrastructureContainer instance
   - Calls `configure_services_for_mode()` to configure

**Classes:**

1. **`Container`**
   - Property wrapper class providing access to container services
   - Properties:
     - `ai_agent` - Returns AI agent instance
     - `product_service` - Returns product service instance
     - `session_repository` - Returns session repository
     - `conversation_repository` - Returns conversation repository
     - `redis_client` - Returns Redis client
     - `query_analyzer` - Returns query analyzer

#### Module: `src.infrastructure.mocks.container.mock_container`

**Classes:**

1. **`MockInfrastructureContainer`**
   - Main DI container (despite "Mock" in name, handles both mock and real implementations)
   - Constructor: `__init__(self, use_mocks: bool = True)`
   - Methods:
     - `_setup_mocks()` - Initialize mock implementations
     - `_setup_real_implementations()` - Initialize real implementations
     - `get_redis_client()` - Returns Redis client instance
     - `get_session_repository()` - Returns session repository
     - `get_conversation_repository()` - Returns conversation repository
     - `get_product_repository()` - Returns product repository
     - `get_query_analyzer()` - Returns query analyzer
     - `get_ai_agent()` - Returns AI agent
     - `get_configuration()` - Returns configuration dict

#### Module: `src.infrastructure.dependencies.service_config`

**Classes:**

1. **`ServiceConfiguration`**
   - Static factory methods for service creation
   - Methods:
     - `create_infrastructure_container(use_mocks: bool) -> MockInfrastructureContainer`
     - `create_chat_agent(api_key: str) -> ChatAgent`
     - `create_chat_orchestrator(container: MockInfrastructureContainer) -> ChatOrchestrator`

**Functions:**

1. **`configure_services_for_mode() -> MockInfrastructureContainer`**
   - Detects mode from environment and creates appropriate container
   - Returns configured MockInfrastructureContainer instance

### Environment Variables

- **`USE_MOCK_MODE`**: Controls which implementations to use
  - Values: `"true"`, `"1"`, `"yes"` → Mock mode
  - Values: `"false"`, `"0"`, `"no"`, or unset → Real mode (default)
  - Case-insensitive

- **`OPENAI_API_KEY`**: Required for real ChatAgent implementation
  - If missing in real mode, falls back to MockAIAgent

### Current Behavior

#### Mock Mode (USE_MOCK_MODE=true)

- Redis: `MockRedisClient`
- Sessions: `MockSessionRepository`
- Conversations: `MockConversationRepository`
- Products: `MockProductRepository`
- Query Analyzer: `MockQueryAnalyzer`
- AI Agent: `MockAIAgent`

#### Real Mode (USE_MOCK_MODE=false or unset)

- Redis: `MockRedisClient` (MVP - still mock)
- Sessions: `MockSessionRepository` (MVP - still mock)
- Conversations: `InMemoryConversationRepository`
- Products: `MockProductService`
- Query Analyzer: `MockQueryAnalyzer` (MVP - still mock)
- AI Agent: `ChatAgent` (real PydanticAI) or `MockAIAgent` (fallback)

### Usage Patterns

#### Pattern 1: Singleton Access (Most Common)

```python
from src.infrastructure.container import get_singleton_container

container = get_singleton_container()
ai_agent = container.ai_agent
product_service = container.product_service
```

#### Pattern 2: Test Reset

```python
from src.infrastructure.container import reset_singleton_container

def setup_method(self):
    reset_singleton_container()
```

#### Pattern 3: Direct Container Creation (Less Common)

```python
from src.infrastructure.dependencies import configure_services_for_mode

container = configure_services_for_mode()
```

#### Pattern 4: Factory Pattern (Internal)

```python
from src.infrastructure.dependencies import ServiceConfiguration

container = ServiceConfiguration.create_infrastructure_container(use_mocks=True)
```

### Import Locations

**Primary Imports:**
- `src/main.py` - Application entry point
- `src/presentation/dependencies.py` - FastAPI dependencies
- `src/presentation/dependencies/__init__.py` - Dependency injection setup

**Test Imports:**
- `tests/e2e/conftest.py` - E2E test configuration
- `tests/integration/test_full_system_integration.py`
- `tests/integration/test_service_integration.py`
- `tests/integration/infrastructure/test_di_container_integration.py`
- `tests/unit/infrastructure/mocks/test_mock_container.py`
- `tests/integration/test_mock_chat_flow.py`

### Migration Requirements

#### Breaking Changes

None - API should remain backward compatible

#### Required Migrations

1. Import changes:
   - `get_singleton_container()` → `InfrastructureContainer.instance()`
   - `reset_singleton_container()` → `InfrastructureContainer.reset()`
   - `MockInfrastructureContainer` → `InfrastructureContainer`

2. Property access remains the same:
   - `container.ai_agent` ✅
   - `container.product_service` ✅
   - `container.session_repository` ✅
   - `container.conversation_repository` ✅
   - `container.redis_client` ✅
   - `container.query_analyzer` ✅

### Edge Cases

1. **Multiple Container Creation**
   - Current: Each `get_container()` creates new instance, but `get_singleton_container()` ensures single instance
   - Target: `InfrastructureContainer.instance()` always returns same instance until reset

2. **Environment Variable Changes**
   - Current: Changes to `USE_MOCK_MODE` only affect new container creation
   - Target: Same behavior - changes only affect next `instance()` call after `reset()`

3. **API Key Missing**
   - Current: Falls back to MockAIAgent with warning
   - Target: Same fallback behavior with warning

4. **Thread Safety**
   - Current: Singleton implementation is thread-safe
   - Target: Must maintain thread safety

### Success Criteria

✅ All existing tests pass without modification
✅ Same behavior in mock and real modes
✅ Environment variables work identically
✅ Fallback mechanisms preserved
✅ Thread safety maintained
✅ Property access unchanged
