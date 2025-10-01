# Pydantic Logfire Implementation Workflow

**Project:** Perky AI Assistant v2 (Steel Chat MVP)
**Strategy:** Agile - Critical Path First + Thin Vertical Slice
**Depth:** Deep Analysis with Parallel Execution
**Status:** Implementation Ready
**Generated:** 2025-10-01

---

## 📋 Table of Contents

1. [Project Context Analysis](#project-context-analysis)
2. [Architecture Integration Points](#architecture-integration-points)
3. [Phase 1: Foundation Setup](#phase-1-foundation-setup)
4. [Phase 2: Critical Path Instrumentation](#phase-2-critical-path-instrumentation)
5. [Phase 3: Vertical Slice - Product Search Flow](#phase-3-vertical-slice---product-search-flow)
6. [Phase 4: Infrastructure & Data Layer](#phase-4-infrastructure--data-layer)
7. [Phase 5: Production Hardening](#phase-5-production-hardening)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Checklist](#deployment-checklist)
10. [Success Metrics & Monitoring](#success-metrics--monitoring)

---

## Project Context Analysis

### Current Architecture (DDD Pattern)

```text
src/
├── core/
│   └── config.py              # Settings with Pydantic BaseSettings
├── domain/                    # Pure business logic
├── application/               # Use cases & services
│   └── ports/
│       └── ai_agent_port.py   # PydanticAI integration point
├── infrastructure/            # External integrations
│   ├── ai/
│   │   └── chat_agent.py      # PydanticAI agent implementation
│   ├── cache/                 # Redis integration
│   ├── database/              # SQLAlchemy async
│   ├── external_services/     # PIM API client
│   └── container.py           # DI container
└── presentation/              # FastAPI routers
    └── api/v1/
        └── websocket.py       # WebSocket endpoint
```

### Key Integration Points Identified

1. **FastAPI Application:** `src/main.py` - Entry point for instrumentation
2. **PydanticAI Agent:** `src/infrastructure/ai/chat_agent.py` - LLM observability
3. **External Services:** `src/infrastructure/external_services/` - PIM API calls
4. **Database:** `src/infrastructure/database/` - SQLAlchemy async sessions
5. **Cache:** `src/infrastructure/cache/` - Redis operations
6. **WebSocket:** `src/presentation/api/v1/websocket.py` - Real-time chat

### Current Configuration Structure

**Settings Location:** `src/core/config.py` (Pydantic BaseSettings)

Existing configuration categories:
- Database (PostgreSQL)
- Redis (sessions + caching)
- PIM Integration (Perky OS)
- OpenAI (PydanticAI)
- WebSocket
- Security

**Strategy:** Extend existing `Settings` class with Logfire configuration section.

---

## Architecture Integration Points

### 1. Configuration Layer Extension

**File:** `src/core/config.py`

**Current Pattern:**

```python
class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    # ... existing settings
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
```

**Logfire Integration:**

```python
from typing import Literal

class Settings(BaseSettings):
    # ... existing settings ...

    # Logfire Observability (NEW)
    LOGFIRE_TOKEN: Optional[str] = None
    LOGFIRE_ENVIRONMENT: Literal["local", "development", "staging", "production"] = "development"
    LOGFIRE_SERVICE_NAME: str = "perky-ai-assistant"
    LOGFIRE_SEND_TO_LOGFIRE: bool = True
    LOGFIRE_CONSOLE: bool = False
    LOGFIRE_SCRUBBING: bool = True
    LOGFIRE_SAMPLING_RATIO: float = 1.0  # 1.0 = 100% in dev, 0.1 = 10% in prod

    model_config = ConfigDict(env_file=".env", case_sensitive=True)
```

### 2. Observability Module Structure

**New Module:** `src/infrastructure/observability/`

```text
src/infrastructure/observability/
├── __init__.py
├── config.py          # Logfire configuration logic
├── instrumentation.py # Centralized instrumentation setup
└── spans.py           # Custom span helpers
```

### 3. Dependency Injection Integration

**File:** `src/infrastructure/container.py`

**Current Pattern:** Singleton container with lazy initialization

**Integration Point:** Initialize Logfire during container setup, before services are created.

---

## Phase 1: Foundation Setup

**Duration:** 2-4 hours
**Priority:** Critical
**Prerequisites:** Logfire account created, API token obtained

### Tasks

#### 1.1 Environment Configuration

**File:** `.env`

```bash
# Add to .env
LOGFIRE_TOKEN=your_logfire_token_here
LOGFIRE_ENVIRONMENT=development
LOGFIRE_SERVICE_NAME=perky-ai-assistant
LOGFIRE_SEND_TO_LOGFIRE=true
LOGFIRE_CONSOLE=false
LOGFIRE_SCRUBBING=true
LOGFIRE_SAMPLING_RATIO=1.0
```

**File:** `.env.example`

Update with Logfire variables (without actual token):

```bash
# Logfire Observability
LOGFIRE_TOKEN=
LOGFIRE_ENVIRONMENT=development
LOGFIRE_SERVICE_NAME=perky-ai-assistant
LOGFIRE_SEND_TO_LOGFIRE=true
LOGFIRE_CONSOLE=false
LOGFIRE_SCRUBBING=true
LOGFIRE_SAMPLING_RATIO=1.0
```

**Verification:**

```bash
# Check environment variables are loaded
python -c "from src.core.config import settings; print(settings.LOGFIRE_TOKEN[:10] if settings.LOGFIRE_TOKEN else 'NOT SET')"
```

---

#### 1.2 Update Configuration Model

**File:** `src/core/config.py`

**Changes:**
1. Import Literal from typing
2. Add Logfire configuration fields to Settings class
3. Add field validators if needed (e.g., sampling ratio bounds)

**Implementation:**

```python
from typing import List, Literal, Optional
from pydantic import field_validator

class Settings(BaseSettings):
    # ... existing settings ...

    # Logfire Observability
    LOGFIRE_TOKEN: Optional[str] = None
    LOGFIRE_ENVIRONMENT: Literal["local", "development", "staging", "production"] = "development"
    LOGFIRE_SERVICE_NAME: str = "perky-ai-assistant"
    LOGFIRE_SEND_TO_LOGFIRE: bool = True
    LOGFIRE_CONSOLE: bool = False
    LOGFIRE_SCRUBBING: bool = True
    LOGFIRE_SAMPLING_RATIO: float = 1.0

    @field_validator("LOGFIRE_SAMPLING_RATIO", mode="before")
    @classmethod
    def validate_sampling_ratio(cls, v: float) -> float:
        """Ensure sampling ratio is between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("LOGFIRE_SAMPLING_RATIO must be between 0.0 and 1.0")
        return v

    model_config = ConfigDict(env_file=".env", case_sensitive=True)
```

**Testing:**

```python
# tests/unit/core/test_config_logfire.py
import pytest
from src.core.config import Settings

def test_logfire_config_defaults():
    """Test Logfire configuration with defaults"""
    settings = Settings(
        # Provide required fields
        PROJECT_NAME="Test",
        # ... other required fields
    )
    assert settings.LOGFIRE_SERVICE_NAME == "perky-ai-assistant"
    assert settings.LOGFIRE_SCRUBBING is True
    assert settings.LOGFIRE_SAMPLING_RATIO == 1.0

def test_sampling_ratio_validation():
    """Test sampling ratio bounds validation"""
    with pytest.raises(ValueError):
        Settings(LOGFIRE_SAMPLING_RATIO=1.5, ...)
```

---

#### 1.3 Create Observability Module

**File:** `src/infrastructure/observability/__init__.py`

```python
"""Observability module for Logfire integration."""

from src.infrastructure.observability.config import configure_logfire
from src.infrastructure.observability.instrumentation import setup_instrumentation

__all__ = ["configure_logfire", "setup_instrumentation"]
```

**File:** `src/infrastructure/observability/config.py`

```python
"""Logfire configuration and initialization."""

import logging
from typing import Optional

import logfire

from src.core.config import settings

logger = logging.getLogger(__name__)


def configure_logfire() -> Optional[logfire.Logfire]:
    """
    Configure Logfire with environment-specific settings.

    Returns:
        Configured Logfire instance or None if disabled.
    """
    if not settings.LOGFIRE_SEND_TO_LOGFIRE:
        logger.info("Logfire observability disabled (LOGFIRE_SEND_TO_LOGFIRE=false)")
        return None

    if not settings.LOGFIRE_TOKEN:
        logger.warning(
            "Logfire token not configured. Observability will be disabled. "
            "Set LOGFIRE_TOKEN environment variable."
        )
        return None

    try:
        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name=settings.LOGFIRE_SERVICE_NAME,
            environment=settings.LOGFIRE_ENVIRONMENT,
            console=settings.LOGFIRE_CONSOLE,
            scrubbing=settings.LOGFIRE_SCRUBBING,
        )

        logger.info(
            f"Logfire configured successfully "
            f"(service={settings.LOGFIRE_SERVICE_NAME}, "
            f"env={settings.LOGFIRE_ENVIRONMENT})"
        )

        return logfire

    except Exception as e:
        logger.error(f"Failed to configure Logfire: {e}", exc_info=True)
        return None
```

**File:** `src/infrastructure/observability/instrumentation.py`

```python
"""Centralized instrumentation setup for all integrations."""

import logging
from typing import Optional

import logfire
from fastapi import FastAPI

from src.core.config import settings

logger = logging.getLogger(__name__)


def setup_instrumentation(app: FastAPI, logfire_instance: Optional[logfire.Logfire] = None):
    """
    Set up all Logfire instrumentations.

    Args:
        app: FastAPI application instance
        logfire_instance: Configured Logfire instance (or None if disabled)
    """
    if not logfire_instance:
        logger.info("Skipping instrumentation (Logfire not configured)")
        return

    try:
        # Phase 1: FastAPI only
        logger.info("Instrumenting FastAPI application...")
        logfire.instrument_fastapi(
            app,
            capture_headers=False,  # Privacy: don't capture headers
            excluded_urls="/health|/metrics",  # Exclude health checks from traces
        )

        logger.info("Instrumentation setup complete (Phase 1: FastAPI only)")

    except Exception as e:
        logger.error(f"Failed to set up instrumentation: {e}", exc_info=True)
```

---

#### 1.4 Integrate with Application Lifecycle

**File:** `src/main.py`

**Changes:**
1. Import observability module
2. Configure Logfire in lifespan startup
3. Instrument FastAPI app after creation

**Implementation:**

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.infrastructure.container import get_singleton_container
from src.infrastructure.observability import configure_logfire, setup_instrumentation
from src.presentation.api import health
from src.presentation.api.v1 import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting Perky AI Assistant application...")

    # Configure Logfire FIRST (before any other services)
    logfire_instance = configure_logfire()

    # Initialize DI container
    get_singleton_container()
    logger.info("Services configured successfully")

    yield

    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Set up instrumentation (after app creation, before middleware)
    logfire_instance = configure_logfire()
    setup_instrumentation(app, logfire_instance)

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routers
    app.include_router(health.router, tags=["health"])
    app.include_router(websocket.router, prefix=settings.API_V1_STR, tags=["websocket"])

    # ... existing routes ...

    return app


app = create_app()
```

---

#### 1.5 Install Dependencies

**File:** `requirements/base.txt` or `pyproject.toml`

**Add:**

```text
logfire[fastapi]==0.53.0  # Or latest version
```

**Installation:**

```bash
# Activate virtual environment
source ~/.virtualenvs/perky-ai-assistant-v2/bin/activate

# Install Logfire with FastAPI extras
pip install 'logfire[fastapi]'

# Update requirements file
pip freeze | grep logfire >> requirements/base.txt
```

---

#### 1.6 Phase 1 Verification

**Manual Testing:**

```bash
# 1. Start application
python -m uvicorn src.main:app --reload

# 2. Check logs for Logfire initialization
# Expected: "Logfire configured successfully (service=perky-ai-assistant, env=development)"

# 3. Make test request
curl http://localhost:8000/health

# 4. Check Logfire dashboard
# Visit: https://logfire.pydantic.dev
# Verify: Health check request appears as trace
```

**Automated Testing:**

```python
# tests/integration/infrastructure/test_logfire_setup.py

import pytest
from fastapi.testclient import TestClient

from src.main import app


def test_app_starts_with_logfire():
    """Test that app starts successfully with Logfire configured"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_logfire_traces_health_check():
    """Test that health check endpoints are excluded from traces"""
    # This is a behavioral test - verify in Logfire dashboard
    # that /health is NOT creating traces
    pass  # Manual verification required
```

**Acceptance Criteria:**
- ✅ Application starts without errors
- ✅ Logfire initialization message in logs
- ✅ FastAPI requests visible in Logfire dashboard
- ✅ Health check endpoint excluded from traces
- ✅ No performance degradation (< 5ms overhead)

---

## Phase 2: Critical Path Instrumentation

**Duration:** 4-6 hours
**Priority:** Critical
**Goal:** Observe LLM behavior and external service calls

### Tasks

#### 2.1 PydanticAI Agent Instrumentation

**File:** `src/infrastructure/observability/instrumentation.py`

**Update `setup_instrumentation()` function:**

```python
def setup_instrumentation(app: FastAPI, logfire_instance: Optional[logfire.Logfire] = None):
    """Set up all Logfire instrumentations."""
    if not logfire_instance:
        logger.info("Skipping instrumentation (Logfire not configured)")
        return

    try:
        # Phase 1: FastAPI
        logger.info("Instrumenting FastAPI application...")
        logfire.instrument_fastapi(
            app,
            capture_headers=False,
            excluded_urls="/health|/metrics",
        )

        # Phase 2: PydanticAI (AUTOMATIC LLM TRACING!)
        logger.info("Instrumenting PydanticAI agents...")
        logfire.instrument_pydantic_ai()

        # Phase 2: HTTPX (for external API calls)
        logger.info("Instrumenting HTTPX client...")
        logfire.instrument_httpx()

        logger.info("Instrumentation setup complete (Phase 2: + PydanticAI + HTTPX)")

    except Exception as e:
        logger.error(f"Failed to set up instrumentation: {e}", exc_info=True)
```

**No code changes needed in chat_agent.py!** 🎉
- PydanticAI instrumentation is automatic
- All agent runs, tool calls, and LLM interactions are traced

**What you'll see in Logfire:**
- Agent execution spans
- LLM request/response with token counts
- Tool execution (product search, stock check)
- Retry attempts if LLM fails
- Cost per conversation (calculated from tokens)

---

#### 2.2 Manual Spans for Use Case Orchestration

**File:** `src/application/services/chat_service.py` (or similar)

**Goal:** Add business context to traces

**Before (example):**

```python
class ChatService:
    async def process_message(
        self,
        session_id: str,
        message: str,
    ) -> ChatResponse:
        # Get session
        session = await self.session_repo.get_by_id(session_id)

        # Run agent
        result = await self.agent.run(message, deps=session)

        # Save conversation
        await self.conversation_repo.save(result.conversation)

        return result.response
```

**After (with Logfire spans):**

```python
import logfire

class ChatService:
    async def process_message(
        self,
        session_id: str,
        message: str,
    ) -> ChatResponse:
        with logfire.span(
            "chat_service.process_message",
            session_id=session_id,
            message_length=len(message),
        ):
            # Get session
            with logfire.span("chat_service.get_session"):
                session = await self.session_repo.get_by_id(session_id)
                logfire.info("Session retrieved", session_language=session.language)

            # Run agent
            with logfire.span("chat_service.run_agent"):
                result = await self.agent.run(message, deps=session)
                logfire.info(
                    "Agent execution completed",
                    tool_calls=len(result.tool_calls),
                    response_length=len(result.response),
                )

            # Save conversation
            with logfire.span("chat_service.save_conversation"):
                await self.conversation_repo.save(result.conversation)

            return result.response
```

**Pattern:** Wrap significant operations in `logfire.span()` with business context.

---

#### 2.3 External Service Call Tracing

**File:** `src/infrastructure/external_services/pim_client.py` (or similar)

**HTTPX instrumentation is automatic!** No changes needed.

**But you can add business context:**

```python
import logfire
import httpx

class PIMClient:
    async def get_products(self, query: str, filters: dict = None):
        with logfire.span(
            "pim_client.get_products",
            query=query,
            has_filters=bool(filters),
        ):
            try:
                # HTTPX call is automatically traced!
                response = await self.client.get(
                    "/products/search",
                    params={"q": query, **(filters or {})},
                )
                response.raise_for_status()

                products = response.json()
                logfire.info("Products retrieved", count=len(products))

                return products

            except httpx.HTTPStatusError as e:
                logfire.error(
                    "PIM API error",
                    status_code=e.response.status_code,
                    error=str(e),
                )
                raise
```

---

#### 2.4 WebSocket Message Flow Tracking

**File:** `src/presentation/api/v1/websocket.py`

**Goal:** Track WebSocket connection lifecycle and message processing

**Before:**

```python
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            response = await process_chat_message(data)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
```

**After (with Logfire spans):**

```python
import logfire

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    with logfire.span(
        "websocket.connection",
        session_id=session_id,
    ):
        await websocket.accept()
        logfire.info("WebSocket connection accepted", session_id=session_id)

        try:
            message_count = 0
            while True:
                with logfire.span("websocket.receive_message"):
                    data = await websocket.receive_text()

                message_count += 1
                with logfire.span(
                    "websocket.process_message",
                    message_number=message_count,
                    message_length=len(data),
                ):
                    response = await process_chat_message(data)

                with logfire.span("websocket.send_response"):
                    await websocket.send_json(response)

        except WebSocketDisconnect:
            logfire.info(
                "WebSocket disconnected",
                session_id=session_id,
                messages_processed=message_count,
            )
```

---

#### 2.5 Phase 2 Verification

Test Scenario: Product Search Conversation

```bash
# 1. Connect to WebSocket
wscat -c ws://localhost:8000/api/v1/ws/test-session-123

# 2. Send product query (Indonesian)
> {"message": "Cari sepatu Nike untuk lari"}

# 3. Check Logfire dashboard for complete trace:
# Expected hierarchy:
# websocket.connection
#   └── websocket.receive_message
#   └── websocket.process_message
#       └── chat_service.process_message
#           └── chat_service.get_session
#           └── chat_service.run_agent
#               └── pydantic_ai.agent.run (AUTOMATIC)
#                   └── openai.chat.completion (AUTOMATIC)
#                       Token count: input=X, output=Y, cost=$Z
#                   └── tool.search_products (AUTOMATIC)
#                       └── httpx.request (AUTOMATIC)
#                           PIM API call details
#           └── chat_service.save_conversation
#   └── websocket.send_response
```

**Acceptance Criteria:**
- ✅ Complete end-to-end trace visible
- ✅ LLM token usage and cost tracked
- ✅ Tool execution success/failure visible
- ✅ PIM API call latency measured
- ✅ Business context (session_id, message_length) in spans

---

## Phase 3: Vertical Slice - Product Search Flow

**Duration:** 3-4 hours
**Priority:** High
**Goal:** Complete observability for critical user journey

### Flow Diagram

```text
User Query: "Cari sepatu Nike untuk lari"
    ↓
[1] WebSocket Receive (websocket.py)
    ↓
[2] Chat Service Orchestration (chat_service.py)
    ↓
[3] Session Retrieval (session_repo → SQLAlchemy → PostgreSQL)
    ↓
[4] PydanticAI Agent Execution (chat_agent.py)
    ↓
[5] Tool: Product Search (product_search_tool.py)
    ↓
[6] PIM API Call (pim_client.py → HTTPX → External API)
    ↓
[7] Redis Cache Check (cache_service.py → Redis)
    ↓
[8] Response Formatting
    ↓
[9] Conversation Save (conversation_repo → SQLAlchemy → PostgreSQL)
    ↓
[10] WebSocket Send Response
```

### Instrumentation Checklist

Each component should have:
- ✅ Automatic instrumentation (if available)
- ✅ Manual spans for business logic
- ✅ Error handling with Logfire logging
- ✅ Performance measurements

### Task 3.1: Repository Layer Instrumentation

**Goal:** Already covered by SQLAlchemy instrumentation (Phase 4), but add business context

**File:** `src/infrastructure/repositories/session_repository.py` (example)

```python
import logfire

class SessionRepository:
    async def get_by_id(self, session_id: str) -> Session:
        with logfire.span("session_repo.get_by_id", session_id=session_id):
            try:
                # SQLAlchemy query (automatically traced in Phase 4)
                result = await self.db.get(Session, session_id)

                if not result:
                    logfire.warning("Session not found", session_id=session_id)
                    raise SessionNotFoundError(session_id)

                logfire.debug("Session retrieved", language=result.language)
                return result

            except Exception as e:
                logfire.error("Session retrieval failed", error=str(e))
                raise
```

---

### Task 3.2: Create Custom Dashboard in Logfire

**Goal:** Product search success metrics dashboard

**Metrics to track:**
1. **Conversion Rate:** Product searches → Successful responses
2. **Average Latency:** End-to-end product search time
3. **Tool Usage:** How often product search tool is called
4. **PIM API Health:** Success rate, average latency
5. **LLM Cost:** Average cost per product search query

**Dashboard Queries (Logfire UI):**

```sql
-- Product search success rate
SELECT
  COUNT(*) FILTER (WHERE error IS NULL) as successful,
  COUNT(*) FILTER (WHERE error IS NOT NULL) as failed,
  (COUNT(*) FILTER (WHERE error IS NULL) * 100.0 / COUNT(*)) as success_rate
FROM spans
WHERE span_name = 'tool.search_products'
AND time > NOW() - INTERVAL '24 hours';

-- Average latency by component
SELECT
  span_name,
  AVG(duration_ms) as avg_latency_ms,
  P50(duration_ms) as p50_ms,
  P95(duration_ms) as p95_ms,
  P99(duration_ms) as p99_ms
FROM spans
WHERE span_name IN (
  'chat_service.process_message',
  'chat_service.run_agent',
  'tool.search_products',
  'httpx.request'
)
AND time > NOW() - INTERVAL '1 hour'
GROUP BY span_name;

-- LLM cost analysis
SELECT
  DATE_TRUNC('hour', time) as hour,
  SUM(attributes->>'input_tokens') as total_input_tokens,
  SUM(attributes->>'output_tokens') as total_output_tokens,
  -- OpenAI pricing: ~$0.01/1K input, ~$0.03/1K output for GPT-4
  (SUM(attributes->>'input_tokens') * 0.00001 +
   SUM(attributes->>'output_tokens') * 0.00003) as estimated_cost_usd
FROM spans
WHERE span_name LIKE '%openai%'
AND time > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

### Task 3.3: Phase 3 End-to-End Test

**File:** `tests/integration/test_product_search_observability.py`

```python
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.mark.integration
async def test_product_search_creates_complete_trace():
    """
    Test that product search flow creates expected Logfire trace structure.

    Manual verification required in Logfire dashboard.
    """
    client = TestClient(app)

    # Connect WebSocket and send product query
    with client.websocket_connect("/api/v1/ws/test-session") as websocket:
        websocket.send_json({"message": "Cari sepatu Nike"})
        response = websocket.receive_json()

        assert "products" in response or "response" in response

    # Check Logfire dashboard for trace with expected structure:
    # - websocket.connection
    #   - websocket.receive_message
    #   - websocket.process_message
    #     - chat_service.process_message
    #       - pydantic_ai.agent.run
    #         - openai.chat.completion
    #         - tool.search_products
    #           - httpx.request (PIM API)
    #   - websocket.send_response

    # This is a behavioral test requiring manual dashboard verification
    pass
```

**Acceptance Criteria:**
- ✅ Trace shows all 10 steps in flow diagram
- ✅ Each step has latency measurement
- ✅ Business context visible (session_id, query, product_count)
- ✅ Errors propagate up trace hierarchy
- ✅ Dashboard shows product search metrics

---

## Phase 4: Infrastructure & Data Layer

**Duration:** 3-4 hours
**Priority:** Medium
**Goal:** Database and cache performance insights

### Task 4.1: SQLAlchemy Instrumentation

**File:** `src/infrastructure/observability/instrumentation.py`

**Update:**

```python
from sqlalchemy.ext.asyncio import AsyncEngine

def setup_instrumentation(
    app: FastAPI,
    logfire_instance: Optional[logfire.Logfire] = None,
    db_engine: Optional[AsyncEngine] = None,
):
    """Set up all Logfire instrumentations."""
    if not logfire_instance:
        return

    try:
        # ... existing instrumentation ...

        # Phase 4: SQLAlchemy
        if db_engine:
            logger.info("Instrumenting SQLAlchemy engine...")
            logfire.instrument_sqlalchemy(
                engine=db_engine,
                enable_commenter=True,  # Adds trace context to SQL queries
            )

        # Phase 4: Redis
        logger.info("Instrumenting Redis...")
        logfire.instrument_redis()

        logger.info("Instrumentation complete (Phase 4: + SQLAlchemy + Redis)")

    except Exception as e:
        logger.error(f"Failed to set up instrumentation: {e}", exc_info=True)
```

**Integration Point:** Pass `db_engine` from container

**File:** `src/main.py`

```python
from src.infrastructure.database.session import get_engine

def create_app() -> FastAPI:
    # ... existing code ...

    # Get database engine for instrumentation
    db_engine = get_engine()

    # Set up instrumentation with DB engine
    logfire_instance = configure_logfire()
    setup_instrumentation(app, logfire_instance, db_engine)

    # ... rest of app setup ...
```

---

### Task 4.2: Redis Cache Observability

**File:** `src/infrastructure/cache/redis_client.py` (example)

**Automatic instrumentation via `logfire.instrument_redis()`**

Optional: Add business context

```python
import logfire

class RedisCache:
    async def get_product_cache(self, product_id: str):
        with logfire.span("cache.get_product", product_id=product_id):
            # Redis GET (automatically traced)
            cached = await self.redis.get(f"product:{product_id}")

            if cached:
                logfire.info("Cache hit", product_id=product_id)
            else:
                logfire.info("Cache miss", product_id=product_id)

            return cached
```

---

### Task 4.3: Database Performance Analysis

**Goal:** Identify N+1 queries and slow queries

**Logfire Dashboard Query:**

```sql
-- Identify potential N+1 query patterns
SELECT
  parent_span_name,
  COUNT(*) as db_query_count,
  AVG(duration_ms) as avg_query_time
FROM spans
WHERE span_name LIKE '%sqlalchemy%'
GROUP BY parent_span_name
HAVING COUNT(*) > 10  -- More than 10 queries in single operation
ORDER BY db_query_count DESC;

-- Slow queries (> 100ms)
SELECT
  attributes->>'statement' as sql_query,
  AVG(duration_ms) as avg_ms,
  COUNT(*) as execution_count
FROM spans
WHERE span_name LIKE '%sqlalchemy%'
AND duration_ms > 100
GROUP BY attributes->>'statement'
ORDER BY avg_ms DESC
LIMIT 20;
```

---

### Task 4.4: Phase 4 Verification

Test Scenario: Database Performance

```python
# Load test to identify N+1 queries
import asyncio

async def test_conversation_history_load():
    """Simulate loading conversation with message history"""
    # Expected: Single query with JOIN, not N queries
    session = await session_repo.get_with_messages(session_id)

    # Check Logfire for query count
    # Should see: 1-2 queries, not N queries where N = message count
```

**Acceptance Criteria:**
- ✅ SQL queries visible with execution time
- ✅ Query parameters visible (if safe/scrubbed)
- ✅ N+1 queries identified and documented
- ✅ Redis operations tracked (get/set/delete)
- ✅ Cache hit rate calculable from traces

---

## Phase 5: Production Hardening

**Duration:** 2-3 hours
**Priority:** High
**Goal:** Production-ready observability

### Task 5.1: Environment-Specific Configuration

**Goal:** Separate Logfire projects for dev/staging/prod

**Logfire Setup:**
1. Create 3 projects in Logfire dashboard:
   - `perky-ai-assistant-dev`
   - `perky-ai-assistant-staging`
   - `perky-ai-assistant-prod`
2. Generate separate API tokens for each
3. Store tokens in respective environment `.env` files

**Environment Files:**

```bash
# .env.development
LOGFIRE_TOKEN=dev_token_here
LOGFIRE_ENVIRONMENT=development
LOGFIRE_SAMPLING_RATIO=1.0  # 100% sampling in dev

# .env.staging
LOGFIRE_TOKEN=staging_token_here
LOGFIRE_ENVIRONMENT=staging
LOGFIRE_SAMPLING_RATIO=0.5  # 50% sampling in staging

# .env.production
LOGFIRE_TOKEN=prod_token_here
LOGFIRE_ENVIRONMENT=production
LOGFIRE_SAMPLING_RATIO=0.1  # 10% sampling in prod (cost optimization)
```

---

### Task 5.2: Sampling Strategy for Production

**File:** `src/infrastructure/observability/config.py`

**Update configuration to apply sampling:**

```python
def configure_logfire() -> Optional[logfire.Logfire]:
    """Configure Logfire with environment-specific settings."""
    # ... existing validation ...

    try:
        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name=settings.LOGFIRE_SERVICE_NAME,
            environment=settings.LOGFIRE_ENVIRONMENT,
            console=settings.LOGFIRE_CONSOLE,
            scrubbing=settings.LOGFIRE_SCRUBBING,
            # Apply sampling for production
            sampling_ratio=settings.LOGFIRE_SAMPLING_RATIO if settings.LOGFIRE_ENVIRONMENT == "production" else 1.0,
        )

        logger.info(
            f"Logfire configured "
            f"(env={settings.LOGFIRE_ENVIRONMENT}, "
            f"sampling={settings.LOGFIRE_SAMPLING_RATIO})"
        )

        return logfire

    except Exception as e:
        logger.error(f"Logfire configuration failed: {e}", exc_info=True)
        return None
```

---

### Task 5.3: Custom Scrubbing Rules

**Goal:** Remove product-specific PII if needed

**File:** `src/infrastructure/observability/config.py`

```python
def configure_logfire() -> Optional[logfire.Logfire]:
    """Configure Logfire with custom scrubbing."""
    # ... existing code ...

    # Custom scrubbing patterns for Indonesian e-commerce
    custom_patterns = [
        r'\b\d{16}\b',  # Credit card numbers
        r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email addresses
        r'\b08\d{8,11}\b',  # Indonesian phone numbers
        # Add more patterns as needed
    ]

    logfire.configure(
        # ... existing config ...
        scrubbing_patterns=custom_patterns if settings.LOGFIRE_SCRUBBING else [],
    )
```

---

### Task 5.4: Alert Configuration

**Goal:** Get notified of critical errors

**Logfire Dashboard Setup:**

1. **High Error Rate Alert**
   - Condition: Error rate > 5% over 5 minutes
   - Action: Email/Slack notification
   - Query:
     ```sql
     SELECT
       COUNT(*) FILTER (WHERE error IS NOT NULL) * 100.0 / COUNT(*) as error_rate
     FROM spans
     WHERE time > NOW() - INTERVAL '5 minutes'
     HAVING error_rate > 5;
     ```

2. **PIM API Downtime Alert**
   - Condition: PIM API error rate > 20% over 5 minutes
   - Action: Immediate notification
   - Query:
     ```sql
     SELECT COUNT(*) as failed_requests
     FROM spans
     WHERE span_name LIKE '%httpx.request%'
     AND attributes->>'url' LIKE '%perky-os%'
     AND error IS NOT NULL
     AND time > NOW() - INTERVAL '5 minutes'
     HAVING failed_requests > 10;
     ```

3. **Slow Response Alert**
   - Condition: P95 latency > 2 seconds
   - Action: Email notification
   - Query:
     ```sql
     SELECT P95(duration_ms) as p95_latency
     FROM spans
     WHERE span_name = 'chat_service.process_message'
     AND time > NOW() - INTERVAL '15 minutes'
     HAVING p95_latency > 2000;
     ```

---

### Task 5.5: Documentation for Team

**File:** `docs/observability-runbook.md`

Create comprehensive runbook covering:
- How to access Logfire dashboard
- Key dashboards and what they show
- How to investigate errors using traces
- Alert escalation procedures
- Cost management (staying within free tier)

**Content outline:**

```markdown
# Observability Runbook

## Accessing Logfire
- URL: https://logfire.pydantic.dev
- Login: Use team Google account
- Projects: dev / staging / prod

## Key Dashboards
### 1. Product Search Dashboard
- Metrics: Success rate, latency, LLM cost
- Use case: Monitor critical user flow

### 2. Error Tracking
- View: Errors grouped by type
- Use case: Daily error review

## Investigating Issues
### Slow Response
1. Find trace in Logfire
2. Identify slowest span
3. Check if DB query, external API, or LLM call
4. Optimize accordingly

### LLM Errors
1. Search for spans with `openai` in name
2. Check token limits, rate limits
3. Review error messages for retry logic

## Cost Management
- Free tier: 1GB/month
- Current usage: Check Logfire dashboard
- Optimization: Adjust sampling in production
```

---

### Task 5.6: Load Testing with Observability

**Goal:** Verify performance overhead under load

**File:** `scripts/load_test_with_observability.py`

```python
import asyncio
import httpx
import time

async def load_test():
    """Send 1000 requests to measure Logfire overhead"""
    async with httpx.AsyncClient() as client:
        start = time.time()

        tasks = [
            client.get("http://localhost:8000/health")
            for _ in range(1000)
        ]

        responses = await asyncio.gather(*tasks)

        elapsed = time.time() - start
        success_count = sum(1 for r in responses if r.status_code == 200)

        print(f"Requests: {len(responses)}")
        print(f"Successful: {success_count}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Requests/sec: {len(responses)/elapsed:.2f}")

if __name__ == "__main__":
    asyncio.run(load_test())
```

**Run test:**

```bash
# With Logfire enabled
LOGFIRE_SEND_TO_LOGFIRE=true python scripts/load_test_with_observability.py

# With Logfire disabled (baseline)
LOGFIRE_SEND_TO_LOGFIRE=false python scripts/load_test_with_observability.py

# Compare results - overhead should be < 5%
```

---

### Task 5.7: Phase 5 Verification Checklist

**Pre-Production Checklist:**
- [ ] Separate Logfire projects created for dev/staging/prod
- [ ] Production sampling configured (10%)
- [ ] Custom scrubbing rules tested
- [ ] Alerts configured and tested
- [ ] Team runbook documented
- [ ] Load test confirms < 5% overhead
- [ ] No sensitive data visible in traces (manual audit)
- [ ] Health check endpoints excluded from traces
- [ ] Free tier usage estimated (should be < 1GB/month)

---

## Testing Strategy

### Unit Tests

**File:** `tests/unit/infrastructure/observability/test_config.py`

```python
import pytest
from unittest.mock import patch

from src.infrastructure.observability.config import configure_logfire


def test_configure_logfire_disabled_when_no_token():
    """Test Logfire is disabled when token not configured"""
    with patch("src.core.config.settings.LOGFIRE_TOKEN", None):
        result = configure_logfire()
        assert result is None


def test_configure_logfire_respects_send_flag():
    """Test LOGFIRE_SEND_TO_LOGFIRE=false disables Logfire"""
    with patch("src.core.config.settings.LOGFIRE_SEND_TO_LOGFIRE", False):
        result = configure_logfire()
        assert result is None


@patch("logfire.configure")
def test_configure_logfire_applies_settings(mock_configure):
    """Test Logfire configuration applies all settings"""
    with patch("src.core.config.settings") as mock_settings:
        mock_settings.LOGFIRE_TOKEN = "test_token"
        mock_settings.LOGFIRE_SEND_TO_LOGFIRE = True
        mock_settings.LOGFIRE_SERVICE_NAME = "test-service"
        mock_settings.LOGFIRE_ENVIRONMENT = "development"
        mock_settings.LOGFIRE_SCRUBBING = True

        configure_logfire()

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]
        assert call_args["token"] == "test_token"
        assert call_args["service_name"] == "test-service"
        assert call_args["environment"] == "development"
        assert call_args["scrubbing"] is True
```

---

### Integration Tests

**File:** `tests/integration/infrastructure/test_logfire_integration.py`

```python
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.mark.integration
def test_fastapi_instrumentation_creates_traces():
    """Test that FastAPI requests create Logfire traces"""
    client = TestClient(app)

    # Make request
    response = client.get("/api")

    # Should succeed
    assert response.status_code == 200

    # Trace should be created in Logfire
    # (Manual verification in dashboard required)


@pytest.mark.integration
def test_health_check_excluded_from_traces():
    """Test that /health endpoint is excluded from Logfire traces"""
    client = TestClient(app)

    # Make health check request
    response = client.get("/health")
    assert response.status_code == 200

    # Verify in Logfire dashboard that no trace was created
    # (Manual verification required)
```

---

### End-to-End Tests

**File:** `tests/e2e/test_observability_e2e.py`

```python
import pytest


@pytest.mark.e2e
@pytest.mark.manual_verification
async def test_complete_product_search_trace():
    """
    E2E test for complete product search observability.

    This test requires manual verification in Logfire dashboard.

    Steps:
    1. Run test
    2. Open Logfire dashboard
    3. Find trace for session_id = 'e2e-test-session'
    4. Verify trace structure matches expected flow diagram

    Expected trace structure:
    - websocket.connection
      - websocket.receive_message
      - websocket.process_message
        - chat_service.process_message
          - chat_service.get_session
          - chat_service.run_agent
            - pydantic_ai.agent.run
              - openai.chat.completion
              - tool.search_products
                - httpx.request (PIM API)
          - chat_service.save_conversation
      - websocket.send_response
    """
    # Test implementation with WebSocket client
    # Send product search query
    # Verify response
    # Check Logfire dashboard manually
    pass
```

---

## Deployment Checklist

### Development Environment

- [ ] Install Logfire: `pip install 'logfire[fastapi]'`
- [ ] Configure `.env` with `LOGFIRE_TOKEN` (dev token)
- [ ] Set `LOGFIRE_ENVIRONMENT=development`
- [ ] Set `LOGFIRE_SAMPLING_RATIO=1.0` (100% sampling)
- [ ] Verify traces appear in Logfire dev project
- [ ] Run integration tests
- [ ] Verify no performance degradation

### Staging Environment

- [ ] Use separate Logfire staging token
- [ ] Set `LOGFIRE_ENVIRONMENT=staging`
- [ ] Set `LOGFIRE_SAMPLING_RATIO=0.5` (50% sampling)
- [ ] Deploy application
- [ ] Run load tests
- [ ] Verify alerts are working
- [ ] Review traces for sensitive data leakage

### Production Environment

- [ ] Use separate Logfire production token
- [ ] Set `LOGFIRE_ENVIRONMENT=production`
- [ ] Set `LOGFIRE_SAMPLING_RATIO=0.1` (10% sampling)
- [ ] Enable custom scrubbing rules
- [ ] Configure production alerts
- [ ] Deploy with gradual rollout (canary/blue-green)
- [ ] Monitor free tier usage (should be < 1GB/month)
- [ ] Document incident response procedures
- [ ] Train team on Logfire dashboard usage

---

## Success Metrics & Monitoring

### Technical Metrics

**Performance Overhead:**
- Target: < 5% latency increase
- Measurement: Compare P95 latency with/without Logfire
- Review: Weekly in dev, daily in production

**Data Volume:**
- Target: Stay within 1GB/month (free tier)
- Measurement: Logfire dashboard usage metrics
- Action: Adjust sampling if approaching limit

**Trace Coverage:**
- Target: >90% of critical paths instrumented
- Measurement: Manual audit of trace coverage
- Review: After each phase completion

---

### Business Metrics

**Debugging Efficiency:**
- Target: 50% reduction in mean time to resolution (MTTR)
- Measurement: Track incident resolution times
- Review: Monthly retrospective

**LLM Cost Visibility:**
- Target: Real-time token usage tracking
- Measurement: Logfire dashboard showing cost per conversation
- Action: Optimize prompts if cost exceeds budget

**Service Reliability:**
- Target: 99.5% uptime for PIM API calls
- Measurement: Error rate from Logfire traces
- Alert: Triggered at >0.5% error rate

**User Experience:**
- Target: P95 response time < 2 seconds
- Measurement: End-to-end latency from Logfire
- Action: Investigate and optimize slow queries

---

### Adoption Metrics

**Team Usage:**
- Target: All developers use Logfire for debugging
- Measurement: Logfire session logs, team survey
- Action: Training sessions, showcase debugging wins

**Dashboard Creation:**
- Target: 3+ custom dashboards created
- Measurement: Count in Logfire projects
- Example dashboards:
  1. Product Search Metrics
  2. LLM Cost Analysis
  3. Error Tracking

**Alert Effectiveness:**
- Target: <10% false positive rate
- Measurement: Alert logs vs actual incidents
- Action: Tune alert thresholds based on feedback

---

## Appendix A: Logfire Dashboard Examples

### Dashboard 1: Product Search Metrics

**Panels:**
1. **Success Rate** (gauge): % of successful product searches
2. **Average Latency** (time series): Latency over time
3. **Tool Usage** (bar chart): Count by tool type
4. **LLM Cost** (number): Total cost today
5. **Error Distribution** (pie chart): Errors by type

### Dashboard 2: Infrastructure Health

**Panels:**
1. **PIM API Latency** (time series): Response time
2. **Redis Hit Rate** (gauge): Cache effectiveness
3. **Database Query Performance** (table): Slowest queries
4. **WebSocket Connections** (number): Active connections

### Dashboard 3: LLM Analysis

**Panels:**
1. **Token Usage** (stacked area): Input vs output tokens
2. **Cost Breakdown** (pie chart): By model/operation
3. **Retry Rate** (time series): LLM call retries
4. **Response Quality** (custom metric): Tool success rate

---

## Appendix B: Common Debugging Scenarios

### Scenario 1: Slow API Response

**Symptom:** User reports slow chat responses

**Investigation Steps:**
1. Find trace in Logfire by session_id
2. Identify slowest span in trace hierarchy
3. Common culprits:
   - LLM call taking >1s → Check OpenAI API status
   - PIM API call >500ms → Check external service
   - Database query >100ms → Check for N+1 queries
   - Redis timeout → Check Redis connection

**Resolution Example:**
- Found: PIM API call taking 2.5s
- Action: Contact PIM team, add timeout, implement caching
- Result: Reduced to 300ms with cache

---

### Scenario 2: High LLM Costs

**Symptom:** Monthly OpenAI bill unexpectedly high

**Investigation Steps:**
1. Open LLM Cost dashboard in Logfire
2. Identify which conversations are expensive
3. Check token usage patterns:
   - Long input contexts → Optimize conversation history
   - Repeated tool calls → Improve agent logic
   - Large system prompts → Compress prompts

**Resolution Example:**
- Found: Sending entire product catalog in context
- Action: Implement semantic search, limit to 5 products
- Result: 70% reduction in input tokens

---

### Scenario 3: Intermittent Errors

**Symptom:** Random errors reported by users

**Investigation Steps:**
1. Search Logfire for error traces
2. Group by error type and frequency
3. Check error context:
   - User actions leading to error
   - System state at time of error
   - External service failures

**Resolution Example:**
- Found: 5% of requests failing with timeout
- Pattern: All during 2-3pm (peak hours)
- Action: Increase timeout, add retry logic
- Result: Error rate reduced to <1%

---

## Appendix C: Cost Optimization Strategies

### Free Tier Management

**Current Free Tier:**
- Unlimited traces and logs
- 1GB storage per month
- 30-day retention

**Estimated Usage (MVP):**
- 10K requests/day = ~300K/month
- Avg trace size: 2-3KB
- Monthly storage: 600-900MB
- **Verdict:** Fits within free tier

**If Approaching Limit:**
1. **Increase Sampling:**
   - Production: 10% → 5%
   - Trade-off: Less visibility, more savings

2. **Exclude Low-Value Traces:**
   - Health checks (already excluded)
   - Static file requests
   - Internal monitoring pings

3. **Reduce Trace Size:**
   - Disable capture_headers (already done)
   - Scrub large payloads
   - Limit context attributes

4. **Upgrade to Paid Tier:**
   - Cost: $20-50/month for startup
   - Benefits: Longer retention, more storage, team features

---

## Appendix D: Team Training Checklist

### Developer Onboarding

#### Session 1: Logfire Basics (30 min)

- [ ] Access Logfire dashboard
- [ ] Understand trace structure
- [ ] Navigate between spans
- [ ] Read attributes and context

#### Session 2: Debugging with Logfire (45 min)

- [ ] Find trace by session_id
- [ ] Identify slow operations
- [ ] Analyze error traces
- [ ] Use search and filters

#### Session 3: Creating Dashboards (30 min)

- [ ] Write basic queries
- [ ] Create custom panels
- [ ] Share dashboards with team

#### Session 4: Adding Instrumentation (45 min)

- [ ] Add manual spans with logfire.span()
- [ ] Log contextual information
- [ ] Follow instrumentation patterns
- [ ] Test local traces

### Ongoing Learning

**Weekly:**
- Review interesting traces in team meeting
- Share debugging wins using Logfire

**Monthly:**
- Analyze LLM cost trends
- Review and optimize slow queries
- Update dashboards based on new insights

---

## Next Steps

1. **Review this workflow** with team
2. **Create Task Master tasks** for systematic implementation
3. **Start Phase 1** (Foundation Setup)
4. **Iterate based on feedback** after each phase

**Estimated Total Effort:** 14-21 hours (2-3 developer days)
**Cost:** $0 (free tier)
**Expected ROI:** 50% faster debugging, real-time LLM cost visibility, proactive issue detection

---

**Document Status:** ✅ Implementation Ready
**Last Updated:** 2025-10-01
**Maintained By:** Development Team
