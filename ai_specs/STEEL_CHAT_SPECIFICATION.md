# Steel Product Inquiry Chat System - Technical Specification

# Sistem Chat Informasi Produk Baja - Spesifikasi Teknis

## Project Overview

### Executive Summary

A real-time chat backend service powered by PydanticAI for handling steel product inquiries in **Bahasa Indonesia**.
The system integrates with **PERKY OS PIM** (Product Information Management) service for real-time product data
retrieval. Built with FastAPI and Domain-Driven Design (DDD) principles, optimized for a cost-conscious startup
serving 10-20 concurrent users.

**Language Support**: The AI agent (GPT-4o-mini) automatically detects and responds in the user's language
(Bahasa Indonesia/English), including support for Indonesian slang and dialects.

### Core Business Value

- **Purpose**: Enable real-time steel product information queries via AI-powered chat in Bahasa Indonesia
- **Users**: Indonesian B2B customers inquiring about steel product pricing and availability
- **Language**: Bahasa Indonesia (auto-detected by LLM, supports standard Indonesian and local dialects/slang)
- **Scale**: 10-20 concurrent users (startup phase)
- **Deployment**: Containerized on DigitalOcean
- **PIM Integration**: PERKY OS for real-time product data
- **Multi-Turn Conversations**: Progressive variant clarification through contextual dialog

> **Important**: This PRD includes a comprehensive Product-Variant domain model refactoring.
> See [product-variant-refactoring-plan.md](./product-variant-refactoring-plan.md) for detailed implementation.

### Technical Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Framework | FastAPI | Async, WebSocket support, modern Python |
| AI Engine | PydanticAI + GPT-4o-mini | Structured AI responses, native language detection |
| Database | PostgreSQL | Structured data, full-text search, cost-effective |
| Cache | Redis | Session management, PIM data caching with TTL-based invalidation |
| Real-time | WebSocket | Low latency for chat interactions |
| Frontend | Svelte Widget | Lightweight, embeddable |
| Container | Docker | Easy deployment on DigitalOcean |
| PIM Integration | PERKY OS REST API | Product data source with JWT authentication |

## Architecture Design

### Domain-Driven Design Structure

```text
src/
├── domain/                    # Core Business Logic
│   ├── entities/
│   │   ├── conversation.py   # Aggregate root
│   │   ├── message.py        # Message entity with AI context
│   │   └── product_query.py  # Steel product query entity
│   │
│   ├── value_objects/
│   │   ├── product_info.py   # Product-level information
│   │   ├── variant_info.py   # SKU-specific details (price, stock)
│   │   ├── product_with_variants_info.py # Aggregate
│   │   ├── query_intent.py   # Enhanced with multi-turn support
│   │   └── message_content.py # Validated message text
│   │
│   ├── services/
│   │   ├── ai_agent.py       # PydanticAI business logic
│   │   ├── product_service.py # Product lookup domain service
│   │   └── pim_service.py    # PERKY OS integration service
│   │
│   └── repositories/          # Abstract interfaces
│       ├── conversation_repository.py
│       └── product_repository.py
│
├── application/               # Use Cases & Orchestration
│   ├── commands/             # Write operations (CQRS)
│   │   ├── send_message.py
│   │   ├── process_query.py
│   │   └── respond_message.py
│   │
│   ├── queries/              # Read operations (CQRS)
│   │   ├── get_conversation.py
│   │   ├── get_messages.py
│   │   └── search_history.py
│   │
│   └── services/
│       ├── chat_orchestrator.py
│       └── query_analyzer.py
│
├── infrastructure/           # Technical Implementation
│   ├── persistence/
│   │   ├── postgres/
│   │   │   ├── models.py    # SQLAlchemy ORM models
│   │   │   ├── repositories.py
│   │   │   └── migrations/  # Alembic migrations
│   │   │
│   │   └── redis/
│   │       ├── cache.py     # Query result caching
│   │       └── session.py   # WebSocket sessions
│   │
│   ├── ai/
│   │   ├── pydantic_agent.py # PydanticAI configuration
│   │   ├── prompts.py        # Indonesian prompts for steel products
│   │   ├── tools.py          # PIM integration tools
│   │   └── embeddings.py     # Vector search (future)
│   │
│   ├── pim/
│   │   ├── perky_client.py   # PERKY OS API client
│   │   ├── auth.py           # JWT authentication handler
│   │   ├── cache_manager.py  # PIM cache with TTL invalidation
│   │   └── models.py         # PIM response models
│   │
│   └── websocket/
│       ├── connection_manager.py
│       └── message_handler.py
│
├── presentation/             # API Layer
│   ├── api/
│   │   ├── v1/
│   │   │   ├── chat.py     # REST endpoints
│   │   │   ├── health.py   # Health checks
│   │   │   └── schemas.py  # Pydantic schemas
│   │   │
│   │   └── deps.py         # Dependencies injection
│   │
│   ├── websocket/
│   │   └── chat_ws.py      # WebSocket endpoint
│   │
│   └── middleware/
│       ├── cors.py         # CORS for Svelte widget
│       ├── auth.py         # JWT validation
│       └── error_handler.py
│
├── core/                    # Shared Kernel
│   ├── config.py           # Settings management
│   ├── constants.py        # Business constants
│   ├── events.py           # Domain events
│   └── exceptions.py       # Custom exceptions
│
├── tests/                   # Test Suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/                  # Containerization
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── scripts/                 # Utility Scripts
│   ├── seed_products.py
│   └── test_websocket.py
│
├── .env.example
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── main.py                 # Application entry point
```

## AI Agent Architecture

### Pydantic AI Integration

The system uses Pydantic AI with ChatGPT 4o-mini for natural language processing and
progressive variant clarification through multi-turn conversations.

#### DDD Layer Placement

##### Application Layer (Primary Location)

- AI Agent Orchestrator: Coordinates user input with domain logic
- Query Intent Analyzer: Classifies user queries with multi-turn context
- Conversation Flow Manager: Maintains state across conversation turns
- PIM Tool Decision Logic: Determines when to query PERKY OS

##### Infrastructure Layer

- ChatGPT 4o-mini Client: External LLM integration
- Pydantic AI Configuration: Response formatting and validation
- PIM API Client: PERKY OS integration with JWT auth
- Cache Manager: TTL-based caching for PIM responses

##### Domain Layer

- Clarification Rules Engine: Pure business logic for progressive clarification
- Product-Variant Relationship Rules: Variant selection logic
- Query Intent Classification Logic: Business rules for intent determination

### Progressive Variant Clarification

The AI agent supports multi-turn conversations to progressively clarify product variants:

```yaml
conversation_flow:
  1_initial_query: "ada besi hollow?"
  2_pim_search: Query PERKY OS for hollow steel products
  3_clarification: "Material apa yang Anda cari? (galvanis/hitam)"
  4_user_response: "galvanis"
  5_pim_filter: Query variants with material=galvanis
  6_clarification: "Ukuran berapa? (20x20, 30x30, 40x40)"
  7_user_response: "30x30"
  8_pim_lookup: Get specific SKU details
  9_final_response: Present variant with price and stock
```

### Caching Strategy

```yaml
cache_ttl:
  product_catalog: 24h    # Product structure rarely changes
  variant_details: 1h     # Specifications relatively stable
  price_stock: 15min      # Dynamic data needs freshness
  search_results: 5min    # Balance between performance and accuracy
```

> **Note**: For detailed Product-Variant domain model refactoring and enhanced QueryIntent design,
> see [product-variant-refactoring-plan.md](./product-variant-refactoring-plan.md)

## Technical Specifications

### 1. Database Schema

#### PostgreSQL Tables

```sql
-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Messages table with full-text search (Indonesian)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(50) NOT NULL CHECK (sender_type IN ('user', 'ai_agent')),
    content TEXT NOT NULL,
    detected_language VARCHAR(10) DEFAULT 'id', -- 'id' for Indonesian, 'en' for English
    intent VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('indonesian', content)) STORED
);

CREATE INDEX idx_messages_search ON messages USING GIN(search_vector);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);

-- Product queries table for analytics
CREATE TABLE product_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    product_name VARCHAR(255),
    quantity INTEGER,
    query_type VARCHAR(50),
    response_data JSONB,
    response_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_product_queries_product ON product_queries(product_name);
CREATE INDEX idx_product_queries_created ON product_queries(created_at DESC);
```

#### Redis Structure

```yaml
Sessions:
  key: "session:{session_id}"
  value: {
    "conversation_id": "uuid",
    "connected_at": "timestamp",
    "last_activity": "timestamp"
  }
  ttl: 3600 # 1 hour

PIM Product Cache:
  # General product info (rarely changes)
  key: "pim:product:{sku}"
  value: {
    "sku": "SKU123",
    "product_name": "Baja Lembaran",
    "description": "...",
    "specifications": {...}
  }
  ttl: 86400 # 24 hours

PIM Price/Stock Cache:
  # Volatile data (changes frequently)
  key: "pim:inventory:{sku}"
  value: {
    "price": 1234500,
    "stock": 150,
    "last_updated": "timestamp"
  }
  ttl: 900 # 15 minutes

Rate Limiting:
  key: "rate:{session_id}"
  value: counter
  ttl: 60 # 1 minute window
```

### 2. API Specifications

#### WebSocket Protocol

```typescript
// Client → Server
interface UserMessage {
  type: "user_message";
  message: string;  // Can be in Indonesian or English
  metadata?: {
    timestamp: string;
    client_id?: string;
  };
}

// Server → Client
interface AIResponse {
  type: "ai_response";
  message: string;  // Response in detected/preferred language
  metadata?: {
    detected_language: "id" | "en";
    intent?: string;
    products_mentioned?: Array<{
      sku: string;
      name: string;
      price?: number;
      stock?: number;
      source: "pim" | "cache";  // Indicates data source
    }>;
    processing_time_ms: number;
    pim_response_time_ms?: number;
  };
}

interface SystemMessage {
  type: "system";
  event: "connected" | "error" | "rate_limited" | "pim_error";
  message?: string;  // Error messages in Indonesian for customers
  message_dev?: string;  // Error messages in English for developers
}

interface PIMError {
  type: "pim_error";
  error_code: "UNAVAILABLE" | "TIMEOUT" | "AUTH_FAILED";
  message: string;  // Indonesian error message
  fallback_used: boolean;
}
```

#### REST Endpoints

```yaml
Health Check:
  GET /health
  Response: { status: "healthy", version: "1.0.0" }

Get Conversation:
  GET /api/v1/conversations/{session_id}
  Response: {
    id: "uuid",
    messages: [...],
    started_at: "timestamp"
  }

Search History:
  GET /api/v1/messages/search?q={query}&limit={limit}
  Response: {
    results: [...],
    total: 100
  }

Export Conversation:
  GET /api/v1/conversations/{session_id}/export
  Response: CSV or JSON format
```

### 3. PydanticAI Configuration

```python
# Core AI Agent Setup with Indonesian Language
class SteelProductAgent:
    """
    PydanticAI agent specialized for Indonesian steel product inquiries
    Integrated with PERKY OS PIM for real-time product data
    """

    def __init__(self, pim_client):
        self.pim_client = pim_client
        self.agent = Agent(
            model="gpt-4o-mini",  # Auto-detects language
            system_prompt=INDONESIAN_STEEL_PROMPT,
            tools=[
                get_product_from_pim,
                check_stock_from_pim,
                get_price_from_pim,
            ],
            temperature=0.3,  # Lower for factual responses
            max_retries=2
        )

# Indonesian System Prompt
INDONESIAN_STEEL_PROMPT = """
Anda adalah PERKY, AI asisten spesialis produk baja dari SMS Perkasa, yang membantu pelanggan B2B Indonesia.

PETUNJUK PENTING:
1. SELALU jawab dalam Bahasa Indonesia, kecuali user bertanya dalam bahasa Inggris
2. Gunakan bahasa yang profesional namun ramah
3. Pahami istilah lokal/slang untuk produk baja (misal: "plat", "besi beton", "hollow")
4. Berikan informasi akurat dari sistem PIM PERKY OS
5. Jika data harga/stok tidak tersedia, informasikan dengan jelas

FORMAT JAWABAN:
- Salam pembuka yang sopan
- Informasi produk yang diminta (nama, SKU, spesifikasi)
- Harga dan ketersediaan stok dari PIM
- Tawaran bantuan lebih lanjut

CONTOH:
"Selamat pagi Pak/Bu! Untuk plat baja 5mm yang Bapak/Ibu tanyakan:
- Produk: HRC SS400 5mm x 4ft x 8ft
- SKU: PLT-5MM-SS400
- Harga: Rp 125.000/lembar
- Stok: Tersedia
Ada yang bisa saya bantu lagi?"
"""

    # Tools for PERKY OS PIM Integration
    @tool
    async def get_product_from_pim(
        self,
        product_query: str  # Can be in Indonesian or English
    ) -> ProductInfo:
        """Fetch product details from PERKY OS PIM"""
        # Search product by name/SKU in PIM
        product = await self.pim_client.search_product(product_query)
        return product

    @tool
    async def get_price_from_pim(
        self,
        sku: str,
        quantity: int = 1
    ) -> PriceInfo:
        """Get real-time pricing from PERKY OS"""
        try:
            price_data = await self.pim_client.get_price(sku, quantity)
            return price_data
        except PIMUnavailableError:
            # Return cached price if available
            cached = await cache.get(f"pim:inventory:{sku}")
            if cached:
                return PriceInfo(price=cached['price'], is_cached=True)
            raise

    @tool
    async def check_stock_from_pim(
        self,
        sku: str
    ) -> StockInfo:
        """Check real-time stock availability from PERKY OS"""
        try:
            stock_data = await self.pim_client.get_stock(sku)
            return stock_data
        except PIMUnavailableError:
            # No fallback for stock - must be real-time
            raise Exception("Maaf, informasi stok tidak tersedia saat ini.")
```

### 4. PERKY OS PIM Client Implementation

```python
# src/infrastructure/pim/perky_client.py
import httpx
import jwt
from typing import Optional, List
from datetime import datetime, timedelta

class PerkyOSClient:
    """
    Client for PERKY OS PIM REST API with JWT authentication
    """

    def __init__(self, config: Config, cache_manager: CacheManager):
        self.base_url = config.PERKY_OS_API_URL
        self.jwt_secret = config.PERKY_OS_JWT_SECRET
        self.timeout = config.PERKY_OS_TIMEOUT / 1000  # Convert to seconds
        self.cache = cache_manager
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Generate or refresh JWT token"""
        if self._token and self._token_expires > datetime.utcnow():
            return self._token

        # Generate new JWT token
        payload = {
            "iss": "steel-chat-service",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        self._token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        self._token_expires = datetime.utcnow() + timedelta(minutes=55)
        return self._token

    async def search_product(self, query: str) -> Optional[dict]:
        """
        Search product by name or SKU
        Supports Indonesian product names and slang
        """
        # Check cache first for product info
        cache_key = f"pim:search:{query.lower()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        try:
            token = await self._get_token()
            response = await self.client.get(
                f"{self.base_url}/products/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()

            product = response.json()

            # Cache product info (24 hours for general info)
            await self.cache.set(
                f"pim:product:{product['sku']}",
                product,
                ttl=86400
            )
            await self.cache.set(cache_key, product, ttl=3600)

            return product

        except httpx.TimeoutException:
            # Try to return cached data if available
            return await self._get_cached_product(query)
        except Exception as e:
            logger.error(f"PIM search error: {e}")
            return None

    async def get_price(self, sku: str, quantity: int = 1) -> dict:
        """
        Get real-time pricing from PERKY OS
        Returns cached price if PIM unavailable
        """
        try:
            token = await self._get_token()
            response = await self.client.get(
                f"{self.base_url}/products/{sku}/price",
                params={"quantity": quantity},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()

            price_data = response.json()

            # Cache price data (15 minutes)
            await self.cache.set(
                f"pim:inventory:{sku}",
                {"price": price_data['price'], "timestamp": datetime.utcnow()},
                ttl=900
            )

            return {"price": price_data['price'], "source": "pim"}

        except Exception:
            # Return cached price if available
            cached = await self.cache.get(f"pim:inventory:{sku}")
            if cached:
                return {"price": cached['price'], "source": "cache"}
            raise Exception("Harga tidak tersedia saat ini")

    async def get_stock(self, sku: str) -> dict:
        """
        Get real-time stock from PERKY OS
        No fallback for stock - must be real-time
        """
        token = await self._get_token()
        response = await self.client.get(
            f"{self.base_url}/products/{sku}/stock",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()

        stock_data = response.json()

        # Cache stock data (15 minutes)
        await self.cache.set(
            f"pim:stock:{sku}",
            stock_data,
            ttl=900
        )

        return {"stock": stock_data['stock'], "source": "pim"}
```

### 5. CQRS Implementation

```python
# Command Side (Write)
class SendMessageCommand:
    conversation_id: str
    content: str
    sender_type: Literal["user", "ai_agent"]

class SendMessageHandler:
    async def handle(self, command: SendMessageCommand) -> Message:
        # 1. Validate
        # 2. Save to database
        # 3. Publish event
        # 4. Return created message
        pass

# Query Side (Read)
class GetConversationQuery:
    session_id: str
    include_metadata: bool = False

class GetConversationHandler:
    async def handle(self, query: GetConversationQuery) -> Conversation:
        # 1. Fetch from read model
        # 2. Apply projections
        # 3. Return formatted data
        pass
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic working chat with AI integration

#### Sprint 1.1: Project Setup

- [ ] Initialize FastAPI project with DDD structure
- [ ] Setup Docker development environment
- [ ] Configure PostgreSQL and Redis connections
- [ ] Implement core domain entities
- [ ] Setup Alembic migrations

#### Sprint 1.2: PydanticAI Integration

- [ ] Configure PydanticAI agent
- [ ] Create steel product prompts
- [ ] Implement basic product lookup tools
- [ ] Test AI responses with mock data
- [ ] Setup error handling for AI failures

#### Sprint 1.3: WebSocket Foundation

- [ ] Implement WebSocket connection manager
- [ ] Create message handler
- [ ] Setup basic client-server communication
- [ ] Add connection/disconnection handling
- [ ] Implement heartbeat mechanism

**Deliverables**:

- Working WebSocket echo server with Indonesian language support
- AI agent responding to Indonesian queries with PERKY OS integration
- Docker development environment with Redis caching

### Phase 2: Core Features (Week 3)

**Goal**: Complete chat functionality with persistence

#### Sprint 2.1: Database Layer

- [ ] Implement SQLAlchemy models
- [ ] Create repository implementations
- [ ] Setup database migrations
- [ ] Implement message persistence
- [ ] Add conversation tracking

#### Sprint 2.2: CQRS Implementation

- [ ] Implement command handlers
- [ ] Create query handlers
- [ ] Setup event bus (simple in-memory)
- [ ] Add domain events
- [ ] Implement read/write separation

#### Sprint 2.3: Caching & Optimization

- [ ] Setup Redis caching layer
- [ ] Implement query result caching
- [ ] Add session management
- [ ] Optimize database queries
- [ ] Add connection pooling

**Deliverables**:

- Persistent message storage with language detection
- Searchable message history in Indonesian
- Cached PIM product queries with TTL-based invalidation

### Phase 3: Production Ready (Week 4)

**Goal**: Production deployment with monitoring

#### Sprint 3.1: Security & Auth

- [ ] Implement JWT token generation
- [ ] Add rate limiting
- [ ] Setup CORS for Svelte widget
- [ ] Add input validation
- [ ] Implement error boundaries

#### Sprint 3.2: Testing & Quality

- [ ] Unit tests for domain logic
- [ ] Integration tests for repositories
- [ ] E2E tests for WebSocket flow
- [ ] Load testing for 20 users
- [ ] Setup CI/CD pipeline

#### Sprint 3.3: Deployment

- [ ] Create production Dockerfile
- [ ] Setup DigitalOcean droplet
- [ ] Configure domain and SSL
- [ ] Setup monitoring (health checks)
- [ ] Create deployment scripts

**Deliverables**:

- Production-deployed service with Indonesian language support
- Monitoring dashboard with PIM integration metrics
- Deployment documentation in English (for developers)

### Phase 4: Enhancement (Optional)

**Goal**: Advanced features based on user feedback

- [ ] Vector search for similar queries
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Bulk query processing
- [ ] Export functionality

## Success Criteria

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time | <500ms | 95th percentile |
| WebSocket Latency | <100ms | Average RTT |
| Concurrent Users | 20 | Load test verified |
| Uptime | 99.9% | Monthly average |
| AI Response Accuracy | >90% | Manual validation |

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Query Success Rate | >95% | Successful responses/total |
| User Session Duration | >3 min | Average engagement |
| Cost per Query | <$0.02 | Including AI API costs |
| Deployment Time | <30 min | Full deployment cycle |
| PIM Response Time | <2s | 95th percentile |
| Cache Hit Rate | >60% | For product queries |
| Language Detection | >98% | Accuracy for ID/EN |

## Cost Analysis

### Monthly Infrastructure Costs (DigitalOcean)

| Component | Specification | Cost |
|-----------|--------------|------|
| App Droplet | 2GB RAM, 1 vCPU | $12 |
| Database | Managed PostgreSQL 1GB | $15 |
| Redis | Included in App Droplet | $0 |
| Backup Storage | 10GB | $1 |
| **Total** | | **$28/month** |

### API Costs

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI GPT-4o-mini | ~10K queries/month | ~$20 |
| **Total** | | **~$20/month** |

### Total Monthly Cost: ~$48

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AI API Downtime | Medium | High | Implement fallback responses, cache common queries |
| PIM Service Unavailable | Medium | High | Cache product info (24h), show error for price/stock |
| Database Overload | Low | High | Connection pooling, query optimization, caching |
| WebSocket Disconnections | Medium | Medium | Auto-reconnect logic, session recovery |
| Cost Overrun | Low | Medium | Rate limiting, query caching, monitoring |
| Security Breach | Low | High | JWT auth, input validation, rate limiting |
| Language Misdetection | Low | Low | LLM handles naturally, user can switch language |
| Cache Invalidation Issues | Medium | Medium | TTL-based expiry, manual cache flush endpoint |

## Development Guidelines

### Code Standards

- Python 3.11+ with type hints
- Black for formatting
- Pylint for linting
- 80% test coverage minimum
- Async/await for all I/O operations

### Git Workflow

- Feature branches from `develop`
- PR reviews required
- Semantic versioning
- Conventional commits

### Documentation Requirements

- API documentation via OpenAPI/Swagger
- README with setup instructions
- Inline code documentation
- Architecture decision records (ADRs)

## Appendix

### A. Environment Variables

```env
# Application
APP_NAME=steel-chat-api
APP_ENV=development
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/chat_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# AI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_RETRIES=2

# PIM Integration
PERKY_OS_API_URL=https://api.perkyos.com/v1
PERKY_OS_JWT_SECRET=your-jwt-secret
PERKY_OS_TIMEOUT=5000  # 5 seconds
PIM_CACHE_TTL_PRODUCT=86400  # 24 hours for product info
PIM_CACHE_TTL_INVENTORY=900  # 15 minutes for price/stock

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_MESSAGE_RATE_LIMIT=10

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### B. Docker Commands

```bash
# Development
docker-compose up -d
docker-compose logs -f app

# Production Build
docker build -t steel-chat:latest .
docker run -p 8000:8000 --env-file .env steel-chat:latest

# Database Migrations
docker-compose exec app alembic upgrade head
docker-compose exec app python scripts/seed_products.py
```

### C. Testing Commands

```bash
# Unit Tests
pytest tests/unit -v

# Integration Tests
pytest tests/integration -v

# E2E Tests
pytest tests/e2e -v

# Load Testing
locust -f tests/load/locustfile.py --users 20 --spawn-rate 2

# Coverage Report
pytest --cov=src --cov-report=html
```

## Contact & Support

- **Technical Lead**: [Your Name]
- **Repository**: [GitHub URL]
- **Documentation**: [Wiki URL]
- **Support**: [Email/Slack]

---

*Last Updated: [Current Date]*
*Version: 1.0.0*
