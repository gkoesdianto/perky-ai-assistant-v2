# Steel Chat MVP Implementation Plan

## Executive Summary

This document outlines a detailed implementation plan for the Steel Chat MVP,
focusing on building a **working end-to-end chat system in 5 days** using
a "walking skeleton" approach. The strategy prioritizes the Application Layer first
with mock infrastructure, enabling early validation and parallel development.

**Key Approach**: Application Layer → Mock Infrastructure → WebSocket → Real Implementation

**Timeline**: 5 days to working MVP (can demo to stakeholders)

**Core Principle**: Build thin vertical slice through all layers that actually works, then iterate.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Strategy](#development-strategy)
3. [Phase 1: Application Layer Foundation (Day 1)](#phase-1-application-layer-foundation-day-1)
4. [Phase 2: Core Use Cases (Day 2)](#phase-2-core-use-cases-day-2)
5. [Phase 3: Mock Infrastructure (Day 2-3)](#phase-3-mock-infrastructure-day-2-3)
6. [Phase 4: WebSocket Integration (Day 3-4)](#phase-4-websocket-integration-day-3-4)
7. [Phase 5: AI Agent Integration (Day 4-5)](#phase-5-ai-agent-integration-day-4-5)
8. [Testing Strategy](#testing-strategy)
9. [Deployment & Validation](#deployment--validation)
10. [Risk Mitigation](#risk-mitigation)
11. [Success Criteria](#success-criteria)

---

## Architecture Overview

### MVP Scope

The MVP implements a minimal but complete chat flow with dual-agent LLM architecture:

```text
User → WebSocket → Application Layer → Dual LLM Agents → PIM (Mock) → Response
                           ↓
              ┌────────────┴────────────┐
              │                         │
        Intent Analyzer          Response Generator
           Agent                     Agent
```

### Dual-Agent Architecture

The system employs two specialized LLM agents for optimal performance:

1. **Intent Analyzer Agent** (GPT-4o-mini):
   - Analyzes user queries to extract structured intent
   - Identifies product attributes and clarification needs
   - Manages conversation state and stage
   - Returns structured QueryIntent value objects

2. **Response Generator Agent** (GPT-4o-mini):
   - Generates natural language responses
   - Incorporates product information contextually
   - Maintains conversational coherence
   - Adapts tone based on conversation stage

### Layer Responsibilities

```yaml
Presentation Layer:
  - WebSocket endpoint for real-time communication
  - Request/response validation
  - Session management

Application Layer:
  - Use cases for business logic orchestration
  - DTOs for data transfer
  - Service ports (interfaces) for external services
  - Query analyzer and AI agent ports

Infrastructure Layer:
  - LLM implementations using PydanticAI
    - LLMQueryAnalyzer (Intent Analyzer Agent)
    - LLMResponseAgent (Response Generator Agent)
  - Mock implementations for development/testing
  - PIM client (mocked initially)
  - In-memory conversation storage

Domain Layer (Already Implemented):
  - Entities: Session, Conversation, Message
  - Value Objects: ProductInfo, VariantInfo, QueryIntent
  - Repository interfaces
```

---

## Development Strategy

### Walking Skeleton Approach

Build the thinnest possible slice that works end-to-end:

1. **Vertical Slice**: Touch all layers with minimal functionality
2. **Mock First**: Use mocks to validate flow before real implementations
3. **Iterate Quickly**: Get feedback early and often
4. **Parallel Development**: Teams can work on infrastructure while app layer uses mocks

### LLM-Based Approach Benefits

The dual-agent LLM architecture provides significant advantages over manual pattern matching:

1. **Intelligent Query Understanding**:
   - Handles complex, ambiguous queries with contextual understanding
   - Automatically adapts to mixed Indonesian/English terminology
   - Learns from conversation context without hardcoded rules

2. **Scalable Intent Classification**:
   - No need to maintain complex regex patterns
   - Easily extendable to new product types and attributes
   - Self-improving with better prompts, not code changes

3. **Natural Conversation Flow**:
   - Generates contextually appropriate responses
   - Maintains conversation coherence across multiple turns
   - Adapts tone and detail level based on query stage

4. **Reduced Maintenance**:
   - No brittle pattern matching code to update
   - Business logic changes via prompt engineering
   - Faster iteration on conversation quality

5. **Cost-Effective with GPT-4o-mini**:
   - Optimized for high-volume, low-latency operations
   - Significantly cheaper than GPT-4 while maintaining quality
   - Structured outputs ensure predictable response formats

### Dependency Order

```text
graph TD
    A[Application DTOs] --> B[Use Case Interfaces]
    B --> C[Mock Implementations]
    C --> D[Service Orchestration]
    D --> E[WebSocket Endpoint]
    E --> F[Integration Testing]
    F --> G[Real Implementations]
```

### Project Dependencies

The project already has all required dependencies configured:

```python
# requirements/base.txt (Existing)
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic==2.10.3
pydantic-settings==2.6.1

# LLM Integration (Already included)
pydantic-ai==1.0.1  # For structured LLM agent implementation
openai==1.57.0      # OpenAI client for GPT-4o-mini

# Infrastructure (Already included)
redis==5.2.0        # Session and cache management
httpx==0.27.2       # Async HTTP client for PIM integration
sqlalchemy==2.0.36  # Database persistence
asyncpg==0.30.0     # Async PostgreSQL adapter
alembic==1.14.0     # Database migrations

# Authentication & Security
python-jose[cryptography]==3.3.0
python-multipart==0.0.7

# requirements/dev.txt (Development & Testing)
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
black==24.10.0
isort==5.13.2
flake8==7.1.1
mypy==1.13.0
pre-commit==4.0.1
```

**Note**: All required dependencies for the dual-agent LLM architecture are already
present in the project. The versions are more recent than initially proposed,
which is beneficial for stability and features.

### Environment Configuration

Required environment variables for LLM integration and monitoring:

```bash
# .env file
# OpenAI Configuration
OPENAI_API_KEY=sk-...  # Required for LLM agents
OPENAI_MODEL=gpt-4o-mini  # Cost-effective model choice
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT_SECONDS=30  # API timeout
OPENAI_MAX_RETRIES=3  # Retry attempts before fallback

# Fallback Configuration
USE_FALLBACK_MODE=true  # Enable fallback mechanisms
CIRCUIT_BREAKER_THRESHOLD=3  # Failures before circuit opens
CIRCUIT_BREAKER_TIMEOUT_MINUTES=5  # Circuit reset time
USE_MOCK_FALLBACK=true  # Use mock analyzer as fallback

# Monitoring Configuration
ENABLE_LLM_MONITORING=true  # Enable performance monitoring
MONITORING_WINDOW_SIZE=100  # Metrics window size
ALERT_FAILURE_THRESHOLD=5  # Failures before alert
ALERT_RESPONSE_TIME_MS=5000  # Slow response threshold

# Testing Configuration
LLM_TEST_MODE=false  # Use mocks in test mode
MAX_TEST_COST_USD=1.00  # Maximum cost per test run
CACHE_TEST_RESPONSES=true  # Cache API responses for tests

# Feature Flags
USE_LLM_AGENTS=true  # Enable LLM-based intent analysis
ENABLE_MOCK_MODE=false  # Use mock implementations when no API key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_SECONDS=3600
```

---

## Phase 1: Application Layer Foundation (Day 1)

### Objectives

- Define data transfer objects (DTOs)
- Create use case interfaces
- Setup dependency injection structure
- Define service protocols

### 1.1 Data Transfer Objects

Create DTOs for transferring data between layers:

```python
# src/application/dto/message_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Literal

@dataclass
class MessageDTO:
    """Data transfer object for messages"""
    content: str
    sender_type: Literal["user", "ai_agent"]
    session_id: str
    conversation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    @classmethod
    def from_entity(cls, message: Message) -> 'MessageDTO':
        """Convert domain entity to DTO"""
        return cls(
            content=message.content,
            sender_type=message.sender_type,
            session_id=message.session_id,
            conversation_id=message.conversation_id,
            timestamp=message.created_at,
            metadata=message.metadata
        )
```

```python
# src/application/dto/conversation_dto.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ConversationDTO:
    """Data transfer object for conversations"""
    id: str
    session_id: str
    messages: List[MessageDTO]
    started_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = None
```

```python
# src/application/dto/session_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class SessionDTO:
    """Data transfer object for sessions"""
    session_id: str
    conversation_id: Optional[str]
    started_at: datetime
    last_activity: datetime
    is_active: bool
    metadata: Dict[str, Any] = None
```

```python
# src/application/dto/product_query_dto.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ProductQueryDTO:
    """DTO for product query requests"""
    query: str
    session_id: str
    include_variants: bool = True
    max_results: int = 10

@dataclass
class ProductResponseDTO:
    """DTO for product query responses"""
    products: List[Dict[str, Any]]  # Simplified for MVP
    query: str
    response_time_ms: int
    source: Literal["pim", "cache", "mock"]
```

### 1.2 Use Case Interfaces

Define interfaces using Python protocols:

```python
# src/application/use_cases/interfaces.py
from typing import Protocol, Optional
from abc import ABC, abstractmethod

class StartChatSessionUseCase(ABC):
    """Interface for starting a new chat session"""

    @abstractmethod
    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        """Start a new chat session"""
        pass

class ProcessUserMessageUseCase(ABC):
    """Interface for processing user messages"""

    @abstractmethod
    async def execute(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        """Process a user message and return AI response"""
        pass

class GetConversationUseCase(ABC):
    """Interface for retrieving conversation history"""

    @abstractmethod
    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        """Get conversation history for a session"""
        pass
```

### 1.3 Service Protocols

Define protocols for infrastructure services:

```python
# src/application/ports/ai_agent_port.py
from typing import Protocol

class AIAgentPort(Protocol):
    """Port for AI agent operations"""

    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        """Generate AI response for user message"""
        ...

# src/application/ports/product_service_port.py
class ProductServicePort(Protocol):
    """Port for product operations"""

    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search for products"""
        ...

    async def get_product_with_variants(self, product_id: str) -> Optional[ProductWithVariantsInfo]:
        """Get product with all variants"""
        ...
```

### 1.4 Dependency Injection Setup

```python
# src/application/container.py
from typing import Dict, Any

class DIContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, factory, singleton: bool = False):
        """Register a service factory"""
        self._services[name] = (factory, singleton)

    def resolve(self, name: str):
        """Resolve a service"""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")

        factory, is_singleton = self._services[name]

        if is_singleton:
            if name not in self._singletons:
                self._singletons[name] = factory()
            return self._singletons[name]

        return factory()

# Global container instance
container = DIContainer()
```

### Deliverables

- ✅ All DTOs created and documented
- ✅ Use case interfaces defined
- ✅ Service protocols established
- ✅ DI container setup

---

## Phase 2: Core Use Cases (Day 2)

### Objectives

- Implement concrete use cases
- Create chat orchestrator service
- Setup AI agent wrapper
- Implement query analyzer

### 2.1 Start Chat Session Use Case

```python
# src/application/use_cases/start_chat_session.py
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.domain.entities import Session
from src.application.dto import SessionDTO
from src.application.use_cases.interfaces import StartChatSessionUseCase

class StartChatSessionUseCaseImpl(StartChatSessionUseCase):
    """Implementation of start chat session use case"""

    def __init__(self, session_repository, redis_client):
        self.session_repository = session_repository
        self.redis_client = redis_client

    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        """Start a new chat session"""

        # Check if session already exists
        existing = await self.redis_client.get(f"session:{session_id}")
        if existing:
            return SessionDTO(**existing)

        # Create new session entity
        session = Session(
            session_id=session_id,
            started_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            metadata=metadata
        )

        # Store in Redis (for MVP, skip database)
        session_data = {
            "session_id": session.session_id,
            "conversation_id": session.conversation_id,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_active": True,
            "metadata": session.metadata
        }

        await self.redis_client.setex(
            f"session:{session_id}",
            3600,  # 1 hour TTL
            session_data
        )

        return SessionDTO(**session_data)
```

### 2.2 Process User Message Use Case

```python
# src/application/use_cases/process_message.py
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from src.domain.entities import Message, Conversation
from src.domain.value_objects import QueryIntent
from src.application.dto import MessageDTO
from src.application.ports import QueryAnalyzerPort, AIAgentPort
from src.application.use_cases.interfaces import ProcessUserMessageUseCase

class ProcessUserMessageUseCaseImpl(ProcessUserMessageUseCase):
    """Implementation of process user message use case with dual-agent architecture"""

    def __init__(
        self,
        query_analyzer_port: QueryAnalyzerPort,
        ai_agent_port: AIAgentPort,
        product_service,
        conversation_repository
    ):
        self.query_analyzer = query_analyzer_port
        self.ai_agent = ai_agent_port
        self.product_service = product_service
        self.conversation_repository = conversation_repository

    async def execute(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        """Process user message with dual-agent LLM architecture"""

        # 1. Get or create conversation
        conversation = await self.conversation_repository.get_by_session(session_id)
        if not conversation:
            conversation = Conversation(session_id=session_id)

        # 2. Prepare conversation context for intent analysis
        context = {
            "conversation_turn": len(conversation.messages) // 2 + 1,
            "resolved_attributes": conversation.metadata.get("resolved_attributes", {}),
            "conversation_history": [
                {"sender": msg.sender_type, "content": msg.content}
                for msg in conversation.messages[-6:]  # Last 3 exchanges
            ]
        }

        # 3. Analyze query intent using LLM Query Analyzer
        intent = await self.query_analyzer.analyze_intent(
            query=content,
            context=context
        )

        # 4. Create user message with intent metadata
        user_message = Message(
            content=content,
            sender_type="user",
            session_id=session_id,
            metadata={
                "intent": intent.dict(),
                "conversation_turn": context["conversation_turn"]
            }
        )
        conversation.add_message(user_message)

        # 5. Generate AI response using Response Generator Agent
        context_messages = [
            MessageDTO.from_entity(msg)
            for msg in conversation.messages[-10:]  # More context for response generation
        ]

        response_content = await self.ai_agent.generate_response(
            message=content,
            conversation_context=context_messages,
            intent=intent
        )

        # 6. Create AI response message
        ai_message = Message(
            content=response_content,
            sender_type="ai_agent",
            session_id=session_id,
            metadata={
                "responding_to": user_message.id,
                "intent_type": intent.type,
                "next_action": intent.next_action,
                "confidence": intent.confidence
            }
        )
        conversation.add_message(ai_message)

        # 7. Update conversation metadata with resolved attributes
        if intent.conversation_context.resolved_attributes:
            conversation.metadata["resolved_attributes"] = intent.conversation_context.resolved_attributes

        # 8. Save conversation
        await self.conversation_repository.save(conversation)

        return MessageDTO.from_entity(ai_message)
```

### 2.3 Get Conversation Use Case

```python
# src/application/use_cases/get_conversation.py
from typing import Optional, List
from src.application.dto import ConversationDTO, MessageDTO
from src.application.use_cases.interfaces import GetConversationUseCase

class GetConversationUseCaseImpl(GetConversationUseCase):
    """Implementation of get conversation use case"""

    def __init__(self, conversation_repository):
        self.conversation_repository = conversation_repository

    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        """Get conversation history for a session"""

        # 1. Retrieve conversation from repository
        conversation = await self.conversation_repository.get_by_session(session_id)

        if not conversation:
            return None

        # 2. Convert to DTO
        messages = [
            MessageDTO.from_entity(msg)
            for msg in conversation.messages
        ]

        return ConversationDTO(
            session_id=conversation.session_id,
            messages=messages,
            metadata=conversation.metadata,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
```

### 2.4 Chat Orchestrator Service

```python
# src/application/services/chat_orchestrator.py
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    """Orchestrates chat operations across use cases"""

    def __init__(
        self,
        start_session_use_case,
        process_message_use_case,
        get_conversation_use_case
    ):
        self.start_session = start_session_use_case
        self.process_message = process_message_use_case
        self.get_conversation = get_conversation_use_case

    async def handle_new_connection(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> SessionDTO:
        """Handle new WebSocket connection"""
        logger.info(f"New connection: {session_id}")

        try:
            session = await self.start_session.execute(session_id, metadata)
            return session
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise

    async def handle_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        """Handle incoming user message"""
        logger.info(f"Processing message from session {session_id}")

        try:
            response = await self.process_message.execute(
                session_id=session_id,
                content=content,
                metadata=metadata
            )
            return response
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Return error message in Indonesian
            return MessageDTO(
                content="Maaf, terjadi kesalahan. Silakan coba lagi.",
                sender_type="ai_agent",
                session_id=session_id,
                metadata={"error": str(e)}
            )

    async def get_conversation_history(
        self,
        session_id: str
    ) -> Optional[ConversationDTO]:
        """Get conversation history for session"""
        try:
            return await self.get_conversation.execute(session_id)
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
```

### 2.5 Query Analyzer Port and Service

```python
# src/application/ports/query_analyzer_port.py
from typing import Protocol, Optional, List
from src.domain.value_objects import QueryIntent
from src.application.dto import MessageDTO

class QueryAnalyzerPort(Protocol):
    """Port for query intent analysis"""

    async def analyze(
        self,
        query: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """Analyze query to determine intent"""
        ...
```

```python
# src/application/services/query_analyzer.py
from typing import Optional, List
from src.application.ports.query_analyzer_port import QueryAnalyzerPort
from src.domain.value_objects import QueryIntent
from src.application.dto import MessageDTO

class QueryAnalyzer:
    """Application service for query analysis"""

    def __init__(self, analyzer_port: QueryAnalyzerPort):
        self.analyzer_port = analyzer_port

    async def analyze(
        self,
        query: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """Delegate query analysis to infrastructure implementation"""
        return await self.analyzer_port.analyze(query, conversation_context)
```

### Deliverables

- ✅ All use cases implemented
- ✅ Chat orchestrator created
- ✅ Query analyzer service built
- ✅ Error handling added

---

## Phase 3: Mock Infrastructure (Day 2-3)

### Objectives

- Create mock implementations for testing
- Build in-memory storage
- Setup mock AI agent
- Create mock PIM client

### 3.1 Mock AI Agent

```python
# src/infrastructure/mocks/mock_ai_agent.py
import random
from typing import List, Optional
from src.application.ports import AIAgentPort
from src.application.dto import MessageDTO

class MockAIAgent(AIAgentPort):
    """Mock AI agent for testing"""

    RESPONSES = {
        "greeting": [
            "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
            "Halo! Saya PERKY, asisten produk baja Anda. Apa yang Anda cari?"
        ],
        "plat": [
            "Untuk plat baja, kami memiliki:\n"
            "- Plat hitam: 2mm-20mm\n"
            "- Plat galvanis: 0.8mm-3mm\n"
            "Ukuran standar 4x8 feet. Ada ukuran khusus yang Anda cari?"
        ],
        "hollow": [
            "Besi hollow tersedia dalam:\n"
            "- Hollow galvanis: 20x20, 30x30, 40x40, 50x50\n"
            "- Hollow hitam: ukuran sama\n"
            "Ketebalan 1.2mm - 3.2mm. Mau yang mana?"
        ],
        "price": [
            "Untuk informasi harga terkini:\n"
            "- Plat hitam 5mm: Rp 125.000/lembar\n"
            "- Hollow galvanis 40x40: Rp 85.000/batang\n"
            "Harga dapat berubah. Mau pesan berapa?"
        ],
        "stock": [
            "Stok tersedia:\n"
            "- Plat hitam 5mm: 150 lembar\n"
            "- Hollow galvanis 40x40: 200 batang\n"
            "Stok update realtime. Butuh berapa?"
        ],
        "default": [
            "Mohon maaf, bisa lebih spesifik produk apa yang Anda cari?",
            "Kami punya berbagai produk baja. Bisa sebutkan lebih detail?"
        ]
    }

    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        """Generate mock response based on keywords"""
        message_lower = message.lower()

        # Check for specific keywords
        if any(word in message_lower for word in ["halo", "hello", "hi"]):
            return random.choice(self.RESPONSES["greeting"])
        elif "plat" in message_lower:
            return self.RESPONSES["plat"][0]
        elif "hollow" in message_lower:
            return self.RESPONSES["hollow"][0]
        elif any(word in message_lower for word in ["harga", "price"]):
            return self.RESPONSES["price"][0]
        elif any(word in message_lower for word in ["stok", "stock"]):
            return self.RESPONSES["stock"][0]
        else:
            return random.choice(self.RESPONSES["default"])
```

### 3.2 Mock Product Repository

```python
# src/infrastructure/mocks/mock_product_repository.py
from typing import Optional, List
from src.domain.repositories import ProductRepository
from src.domain.value_objects import ProductInfo, VariantInfo, ProductWithVariantsInfo

class MockProductRepository(ProductRepository):
    """Mock product repository for testing"""

    def __init__(self):
        self.products = self._create_mock_products()

    def _create_mock_products(self) -> Dict[str, ProductWithVariantsInfo]:
        """Create mock product data"""

        # Plat Baja Product
        plat_product = ProductInfo(
            product_id="PROD-001",
            name="Plat Baja Hitam",
            description="Plat baja berkualitas tinggi",
            category="Plat",
            brand="SMS Perkasa",
            base_unit="lembar"
        )

        plat_variants = [
            VariantInfo(
                sku="PLT-5MM-4X8",
                product_id="PROD-001",
                name="Plat Hitam 5mm 4x8",
                size="5mm x 4ft x 8ft",
                material="Baja Hitam",
                price=125000.0,
                stock_quantity=150,
                unit="lembar"
            ),
            VariantInfo(
                sku="PLT-10MM-4X8",
                product_id="PROD-001",
                name="Plat Hitam 10mm 4x8",
                size="10mm x 4ft x 8ft",
                material="Baja Hitam",
                price=250000.0,
                stock_quantity=75,
                unit="lembar"
            )
        ]

        plat_with_variants = ProductWithVariantsInfo(
            product=plat_product,
            variants=plat_variants
        )

        # Hollow Product
        hollow_product = ProductInfo(
            product_id="PROD-002",
            name="Besi Hollow Galvanis",
            description="Besi hollow dengan lapisan galvanis",
            category="Hollow",
            brand="SMS Perkasa",
            base_unit="batang"
        )

        hollow_variants = [
            VariantInfo(
                sku="HLW-40X40-GLV",
                product_id="PROD-002",
                name="Hollow Galvanis 40x40",
                size="40mm x 40mm x 6m",
                material="Galvanis",
                price=85000.0,
                stock_quantity=200,
                unit="batang"
            )
        ]

        hollow_with_variants = ProductWithVariantsInfo(
            product=hollow_product,
            variants=hollow_variants
        )

        return {
            "PROD-001": plat_with_variants,
            "PROD-002": hollow_with_variants
        }

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        """Get product with all variants"""
        return self.products.get(product_id)

    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Get specific variant by SKU"""
        for product in self.products.values():
            for variant in product.variants:
                if variant.sku == sku:
                    return variant
        return None

    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search products by query"""
        query_lower = query.lower()
        results = []

        for product_with_variants in self.products.values():
            product = product_with_variants.product
            if (query_lower in product.name.lower() or
                query_lower in product.description.lower() or
                query_lower in product.category.lower()):
                results.append(product)

        return results

    async def get_variants_by_product(self, product_id: str) -> List[VariantInfo]:
        """Get all variants for a product"""
        product = self.products.get(product_id)
        return product.variants if product else []
```

### 3.3 In-Memory Conversation Repository

```python
# src/infrastructure/mocks/mock_conversation_repository.py
from typing import Optional, Dict
from src.domain.entities import Conversation

class MockConversationRepository:
    """In-memory conversation storage for testing"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}

    async def save(self, conversation: Conversation) -> None:
        """Save conversation in memory"""
        self.conversations[conversation.session_id] = conversation

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID"""
        return self.conversations.get(session_id)

    async def delete(self, session_id: str) -> None:
        """Delete conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
```

### 3.4 Mock Redis Client

```python
# src/infrastructure/mocks/mock_redis_client.py
from typing import Any, Optional
import json
from datetime import datetime, timedelta

class MockRedisClient:
    """Mock Redis client for testing"""

    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        # Check expiry
        if key in self.expiry:
            if datetime.now() > self.expiry[key]:
                del self.storage[key]
                del self.expiry[key]
                return None

        value = self.storage.get(key)
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return value
        return value

    async def set(self, key: str, value: Any) -> None:
        """Set value"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.storage[key] = value

    async def setex(self, key: str, seconds: int, value: Any) -> None:
        """Set with expiry"""
        await self.set(key, value)
        self.expiry[key] = datetime.now() + timedelta(seconds=seconds)

    async def delete(self, key: str) -> None:
        """Delete key"""
        if key in self.storage:
            del self.storage[key]
        if key in self.expiry:
            del self.expiry[key]
```

### 3.5 Mock Query Analyzer

```python
# src/infrastructure/mocks/mock_query_analyzer.py
from typing import Dict, Any, Optional, List
from src.application.ports import QueryAnalyzerPort
from src.domain.value_objects import QueryIntent, ClarificationNeeded, ConversationContext

class MockQueryAnalyzer(QueryAnalyzerPort):
    """Mock query analyzer for testing and development"""

    def __init__(self):
        # Predefined patterns for mock intent analysis
        self.patterns = {
            "product_inquiry": [
                "plat", "hollow", "besi", "pipa", "profil",
                "siku", "unp", "wf", "h-beam", "cnp"
            ],
            "price_check": [
                "harga", "price", "berapa", "cost", "biaya"
            ],
            "availability_check": [
                "stok", "stock", "tersedia", "ada", "available"
            ],
            "variant_selection": [
                "ukuran", "size", "tebal", "thickness", "dimensi"
            ]
        }

    async def analyze_intent(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryIntent:
        """Analyze query intent using pattern matching for mock implementation"""
        query_lower = query.lower()

        # Determine query type based on patterns
        query_type = "general"
        detected_attributes = {}
        confidence = 0.5

        # Check for product inquiries
        for product in self.patterns["product_inquiry"]:
            if product in query_lower:
                query_type = "product_inquiry"
                detected_attributes["product_type"] = product
                confidence = 0.8
                break

        # Check for price queries
        if any(word in query_lower for word in self.patterns["price_check"]):
            if query_type == "product_inquiry":
                query_type = "price_check"
                confidence = 0.9
            else:
                query_type = "price_check"
                confidence = 0.7

        # Check for availability
        if any(word in query_lower for word in self.patterns["availability_check"]):
            if query_type == "product_inquiry":
                query_type = "availability_check"
                confidence = 0.9
            else:
                query_type = "availability_check"
                confidence = 0.7

        # Check for variant selection
        if any(word in query_lower for word in self.patterns["variant_selection"]):
            query_type = "variant_selection"
            confidence = 0.85

        # Create mock conversation context
        conversation_context = ConversationContext(
            resolved_attributes=detected_attributes,
            pending_clarifications=[],
            conversation_history=[],
            attribute_confidence={"product_type": confidence} if "product_type" in detected_attributes else {}
        )

        # Determine clarification stage based on context
        clarification_stage = "initial"
        if context and context.get("conversation_turn", 1) > 1:
            if detected_attributes:
                clarification_stage = "narrowing"
            if confidence > 0.85:
                clarification_stage = "confirming"

        # Create QueryIntent
        return QueryIntent(
            type=query_type,
            clarification_stage=clarification_stage,
            query_level="product" if query_type == "product_inquiry" else "ambiguous",
            conversation_context=conversation_context,
            conversation_turn=context.get("conversation_turn", 1) if context else 1,
            next_action="provide_info" if confidence > 0.8 else "request_clarification",
            original_query=query,
            current_query=query,
            detected_attributes=detected_attributes,
            confidence=confidence,
            requires_human_intervention=False,
            product_name=detected_attributes.get("product_type"),
            quantity=self._extract_quantity(query_lower)
        )

    def _extract_quantity(self, query: str) -> Optional[int]:
        """Extract quantity from query if present"""
        import re
        numbers = re.findall(r'\d+', query)
        if numbers:
            # Simple heuristic: return first number found
            return int(numbers[0])
        return None
```

### Deliverables

- ✅ Mock AI agent with Indonesian responses
- ✅ Mock product repository with sample data
- ✅ In-memory conversation storage
- ✅ Mock Redis client
- ✅ Mock query analyzer for development

---

## Phase 4: WebSocket Integration (Day 3-4)

### Objectives

- Create WebSocket endpoint
- Implement connection management
- Handle message routing
- Add heartbeat mechanism

### 4.1 WebSocket Connection Manager

```python
# src/presentation/websocket/connection_manager.py
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store new connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(session_id)

        logger.info(f"Client {session_id} connected")

    def disconnect(self, session_id: str):
        """Remove connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        for sid, connections in self.session_connections.items():
            if session_id in connections:
                connections.remove(session_id)

        logger.info(f"Client {session_id} disconnected")

    async def send_personal_message(self, message: dict, session_id: str):
        """Send message to specific client"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict, session_id: str = None):
        """Broadcast message to all connections in a session"""
        if session_id and session_id in self.session_connections:
            for connection_id in self.session_connections[session_id]:
                if connection_id in self.active_connections:
                    await self.active_connections[connection_id].send_json(message)
```

### 4.2 WebSocket Endpoint

```python
# src/presentation/websocket/chat_ws.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import json
import asyncio
import logging
from src.application.services import ChatOrchestrator
from src.presentation.websocket import ConnectionManager

logger = logging.getLogger(__name__)

class ChatWebSocket:
    """WebSocket endpoint for chat"""

    def __init__(self, chat_orchestrator: ChatOrchestrator):
        self.chat_orchestrator = chat_orchestrator
        self.manager = ConnectionManager()

    async def websocket_endpoint(self, websocket: WebSocket, session_id: str):
        """Main WebSocket endpoint"""

        # Connect
        await self.manager.connect(websocket, session_id)

        # Start session
        try:
            metadata = {
                "user_agent": websocket.headers.get("user-agent", "unknown"),
                "origin": websocket.headers.get("origin", "unknown")
            }

            session_dto = await self.chat_orchestrator.handle_new_connection(
                session_id=session_id,
                metadata=metadata
            )

            # Send welcome message
            await self.manager.send_personal_message(
                {
                    "type": "system",
                    "event": "connected",
                    "message": "Selamat datang di SMS Perkasa Steel Chat!",
                    "session": session_dto.__dict__
                },
                session_id
            )

            # Start heartbeat
            heartbeat_task = asyncio.create_task(
                self._heartbeat(websocket, session_id)
            )

            # Message loop
            await self._message_loop(websocket, session_id)

        except WebSocketDisconnect:
            logger.info(f"Client {session_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup
            heartbeat_task.cancel()
            self.manager.disconnect(session_id)

    async def _message_loop(self, websocket: WebSocket, session_id: str):
        """Handle incoming messages"""

        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                if data.get("type") == "user_message":
                    # Process user message
                    content = data.get("message", "")
                    metadata = data.get("metadata", {})

                    # Send typing indicator
                    await self.manager.send_personal_message(
                        {
                            "type": "system",
                            "event": "typing",
                            "message": "PERKY sedang mengetik..."
                        },
                        session_id
                    )

                    # Process message
                    response = await self.chat_orchestrator.handle_user_message(
                        session_id=session_id,
                        content=content,
                        metadata=metadata
                    )

                    # Send response
                    await self.manager.send_personal_message(
                        {
                            "type": "ai_response",
                            "message": response.content,
                            "metadata": response.metadata
                        },
                        session_id
                    )

                elif data.get("type") == "ping":
                    # Respond to ping
                    await self.manager.send_personal_message(
                        {"type": "pong"},
                        session_id
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await self.manager.send_personal_message(
                    {
                        "type": "system",
                        "event": "error",
                        "message": "Maaf, terjadi kesalahan. Silakan coba lagi."
                    },
                    session_id
                )

    async def _heartbeat(self, websocket: WebSocket, session_id: str):
        """Send periodic heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                await self.manager.send_personal_message(
                    {"type": "heartbeat"},
                    session_id
                )
            except Exception:
                break
```

### 4.3 WebSocket Router

```python
# src/presentation/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, Depends
from src.presentation.websocket import ChatWebSocket
from src.presentation.dependencies import get_chat_orchestrator

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    chat_orchestrator = Depends(get_chat_orchestrator)
):
    """WebSocket endpoint for chat"""
    chat_ws = ChatWebSocket(chat_orchestrator)
    await chat_ws.websocket_endpoint(websocket, session_id)
```

### 4.4 Simple HTML Test Client

```text
<!-- test_client.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Steel Chat Test Client</title>
    <style>
        #messages {
            height: 400px;
            overflow-y: scroll;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
        }
        .user-message {
            text-align: right;
            color: blue;
            margin: 5px 0;
        }
        .ai-message {
            text-align: left;
            color: green;
            margin: 5px 0;
        }
        .system-message {
            text-align: center;
            color: gray;
            font-style: italic;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>Steel Chat Test Client</h1>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Ketik pesan Anda..." style="width: 70%">
    <button onclick="sendMessage()">Kirim</button>

    <script>
        const sessionId = 'test-session-' + Date.now();
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${sessionId}`);
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            let messageClass = 'system-message';
            let messageText = '';

            if (data.type === 'ai_response') {
                messageClass = 'ai-message';
                messageText = 'PERKY: ' + data.message;
            } else if (data.type === 'system') {
                messageText = data.message;
            }

            if (messageText) {
                const messageElement = document.createElement('div');
                messageElement.className = messageClass;
                messageElement.textContent = messageText;
                messagesDiv.appendChild(messageElement);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        };

        ws.onopen = function() {
            console.log('Connected to WebSocket');
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                // Display user message
                const messageElement = document.createElement('div');
                messageElement.className = 'user-message';
                messageElement.textContent = 'Anda: ' + message;
                messagesDiv.appendChild(messageElement);

                // Send to server
                ws.send(JSON.stringify({
                    type: 'user_message',
                    message: message,
                    metadata: {
                        timestamp: new Date().toISOString()
                    }
                }));

                messageInput.value = '';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }

        // Send message on Enter key
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

### Deliverables

- ✅ WebSocket connection manager
- ✅ WebSocket endpoint with chat handling
- ✅ Heartbeat mechanism
- ✅ Test HTML client

---

## Phase 5: AI Agent Integration (Day 4-5)

### Objectives

- Setup PydanticAI agent
- Create Indonesian prompts
- Implement PIM tools
- Test complete flow

### 5.1 Dual-Agent Architecture with PydanticAI

#### 5.1.1 LLM Query Analyzer Implementation

```python
# src/infrastructure/ai/llm_query_analyzer.py
from typing import List, Optional
from pydantic_ai import Agent
from src.application.ports.query_analyzer_port import QueryAnalyzerPort
from src.domain.value_objects import QueryIntent, ConversationContext
from src.application.dto import MessageDTO
import logging

logger = logging.getLogger(__name__)

class LLMQueryAnalyzer(QueryAnalyzerPort):
    """LLM-powered query intent analyzer using PydanticAI"""

    INTENT_ANALYSIS_PROMPT = """
    You are a query intent analyzer for SMS Perkasa steel products B2B marketplace.
    Analyze user queries in Indonesian/English and return structured intent classification.

    Context:
    - B2B steel products: plat (plates), hollow, pipa (pipes), besi beton (rebar), etc.
    - Users typically ask about: products, prices, availability, specifications
    - Multi-turn conversations often needed to clarify exact requirements
    - Indonesian market with mixed Indonesian/English terminology

    Your task:
    1. Classify intent type (product_inquiry, price_check, availability_check, variant_selection, general)
    2. Extract product mentions and attributes (dimensions, material, thickness)
    3. Determine clarification stage (initial, narrowing, confirming, complete)
    4. Identify what clarifications are needed
    5. Assess confidence in your classification

    Consider conversation context for multi-turn understanding.
    Return structured QueryIntent with all required fields.
    """

    def __init__(self, openai_api_key: str):
        self.agent = Agent(
            model="gpt-4o-mini",
            system_prompt=self.INTENT_ANALYSIS_PROMPT,
            result_type=QueryIntent,
            temperature=0.1,
            max_retries=2
        )

    async def analyze(
        self,
        query: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """Analyze query using LLM to determine intent"""
        try:
            context_str = ""
            if conversation_context:
                context_str = "Previous conversation:\n"
                for msg in conversation_context[-3:]:
                    context_str += f"{msg.sender_type}: {msg.content}\n"

            analysis_input = {
                "query": query,
                "context": context_str if context_str else "No previous context"
            }

            result = await self.agent.run(analysis_input)
            intent = result.data

            intent = self._post_process_intent(intent, query)
            logger.info(f"Query intent analyzed: {intent.type} with confidence {intent.confidence}")
            return intent

        except Exception as e:
            logger.error(f"LLM intent analysis failed: {e}")
            return self._create_fallback_intent(query)

    def _post_process_intent(self, intent: QueryIntent, original_query: str) -> QueryIntent:
        """Post-process LLM output for consistency"""
        if not intent.original_query:
            intent.original_query = original_query
        if not intent.current_query:
            intent.current_query = original_query

        if not intent.conversation_context:
            intent.conversation_context = ConversationContext()

        if intent.clarification_stage == "initial" and not intent.matched_products:
            intent.next_action = "request_clarification"
        elif intent.clarification_stage == "complete":
            intent.next_action = "provide_info"
        elif intent.clarification_stage == "confirming":
            intent.next_action = "confirm_selection"

        return intent

    def _create_fallback_intent(self, query: str) -> QueryIntent:
        """Create basic fallback intent when LLM fails"""
        return QueryIntent(
            type="general",
            clarification_stage="initial",
            query_level="ambiguous",
            conversation_context=ConversationContext(),
            next_action="request_clarification",
            original_query=query,
            current_query=query,
            confidence=0.3
        )
```

#### 5.1.2 LLM Response Generator Implementation

```python
# src/infrastructure/ai/llm_response_agent.py
from pydantic_ai import Agent
from typing import List, Optional
import logging
from src.application.ports import AIAgentPort
from src.domain.value_objects import QueryIntent
from src.application.dto import MessageDTO

logger = logging.getLogger(__name__)

class LLMResponseAgent(AIAgentPort):
    """LLM-powered response generator using PydanticAI"""

    RESPONSE_GENERATION_PROMPT = """
    You are PERKY, AI assistant for SMS Perkasa steel products, helping B2B customers in Indonesia.

    IMPORTANT INSTRUCTIONS:
    1. ALWAYS respond in Indonesian unless the user writes in English
    2. Use professional yet friendly language
    3. Understand local steel terminology (plat, besi beton, hollow, etc.)
    4. Provide accurate product, price, and stock information
    5. Clearly state if information is unavailable

    RESPONSE FORMAT:
    - Polite greeting
    - Product information (name, SKU, specifications)
    - Price and stock availability
    - Offer for further assistance

    Use the query intent analysis to guide your response:
    - For product_inquiry: Focus on product details and specifications
    - For price_check: Emphasize pricing information
    - For availability_check: Highlight stock levels
    - For clarification requests: Ask specific questions to narrow down requirements
    """

    def __init__(self, product_service, openai_api_key: str):
        self.product_service = product_service

        self.agent = Agent(
            model="gpt-4o-mini",
            system_prompt=self.RESPONSE_GENERATION_PROMPT,
            temperature=0.3,
            max_retries=2
        )

        self._register_tools()

    def _register_tools(self):
        """Register product-related tools for the agent"""

        @self.agent.tool
        async def search_products(query: str) -> List[dict]:
            """Search for products by query"""
            try:
                products = await self.product_service.search_products(query)
                return [
                    {
                        "product_id": p.product_id,
                        "name": p.name,
                        "description": p.description,
                        "category": p.category
                    }
                    for p in products
                ]
            except Exception as e:
                logger.error(f"Product search error: {e}")
                return []

        @self.agent.tool
        async def get_product_details(product_id: str) -> dict:
            """Get product with variants"""
            try:
                product_with_variants = await self.product_service.get_product_with_variants(product_id)
                if not product_with_variants:
                    return {}

                return {
                    "product": {
                        "name": product_with_variants.product.name,
                        "description": product_with_variants.product.description
                    },
                    "variants": [
                        {
                            "sku": v.sku,
                            "name": v.name,
                            "size": v.size,
                            "price": v.price,
                            "stock": v.stock_quantity
                        }
                        for v in product_with_variants.variants
                    ]
                }
            except Exception as e:
                logger.error(f"Product details error: {e}")
                return {}

        @self.agent.tool
        async def check_stock(sku: str) -> dict:
            """Check stock availability"""
            try:
                variant = await self.product_service.get_variant_by_sku(sku)
                if not variant:
                    return {"available": False}

                return {
                    "sku": variant.sku,
                    "available": variant.stock_quantity > 0,
                    "quantity": variant.stock_quantity,
                    "unit": variant.unit
                }
            except Exception as e:
                logger.error(f"Stock check error: {e}")
                return {"available": False}

    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None,
        query_intent: Optional[QueryIntent] = None
    ) -> str:
        """Generate AI response based on message and intent"""
        try:
            context = ""
            if conversation_context:
                context = "\n".join([
                    f"{msg.sender_type}: {msg.content}"
                    for msg in conversation_context[-3:]
                ])

            intent_info = ""
            if query_intent:
                intent_info = f"""
                Intent Type: {query_intent.type}
                Clarification Stage: {query_intent.clarification_stage}
                Next Action: {query_intent.next_action}
                Detected Products: {query_intent.matched_products}
                Confidence: {query_intent.confidence}
                """

            full_input = {
                "message": message,
                "context": context,
                "intent": intent_info
            }

            result = await self.agent.run(full_input)
            return result.data

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "Maaf, terjadi kesalahan sistem. Silakan coba beberapa saat lagi."
```

### 5.2 Dependency Injection Configuration

```python
# src/presentation/dependencies.py
from functools import lru_cache
from src.application.container import container
from src.application.services import ChatOrchestrator
from src.application.use_cases import (
    StartChatSessionUseCaseImpl,
    ProcessUserMessageUseCaseImpl,
    GetConversationUseCaseImpl
)
from src.infrastructure.mocks import (
    MockAIAgent,
    MockProductRepository,
    MockConversationRepository,
    MockRedisClient
)
from src.application.services import QueryAnalyzer
from src.core.config import settings

@lru_cache()
def get_container():
    """Get configured DI container"""

    # Register infrastructure services
    container.register("redis_client", MockRedisClient, singleton=True)
    container.register("product_repository", MockProductRepository, singleton=True)
    container.register("conversation_repository", MockConversationRepository, singleton=True)

    # Register LLM-based implementations (use mocks if OpenAI key not available)
    if settings.OPENAI_API_KEY:
        # Production: LLM-based dual agents
        from src.infrastructure.ai import LLMQueryAnalyzer, LLMResponseAgent

        container.register(
            "query_analyzer_port",
            lambda: LLMQueryAnalyzer(settings.OPENAI_API_KEY),
            singleton=True
        )

        container.register(
            "ai_agent",
            lambda: LLMResponseAgent(
                product_service=container.resolve("product_repository"),
                openai_api_key=settings.OPENAI_API_KEY
            ),
            singleton=True
        )
    else:
        # Development: Mock implementations
        container.register("ai_agent", MockAIAgent, singleton=True)
        container.register(
            "query_analyzer_port",
            MockQueryAnalyzer,  # Need to create mock that implements port
            singleton=True
        )

    # Register application services
    container.register(
        "query_analyzer",
        lambda: QueryAnalyzer(
            analyzer_port=container.resolve("query_analyzer_port")
        ),
        singleton=True
    )

    # Register use cases
    container.register(
        "start_session_use_case",
        lambda: StartChatSessionUseCaseImpl(
            session_repository=None,  # Not needed for MVP
            redis_client=container.resolve("redis_client")
        ),
        singleton=True
    )

    container.register(
        "process_message_use_case",
        lambda: ProcessUserMessageUseCaseImpl(
            ai_agent=container.resolve("ai_agent"),
            product_service=container.resolve("product_repository"),
            conversation_repository=container.resolve("conversation_repository"),
            query_analyzer=container.resolve("query_analyzer")
        ),
        singleton=True
    )

    container.register(
        "get_conversation_use_case",
        lambda: GetConversationUseCaseImpl(
            conversation_repository=container.resolve("conversation_repository")
        ),
        singleton=True
    )

    # Register orchestrator
    container.register(
        "chat_orchestrator",
        lambda: ChatOrchestrator(
            start_session_use_case=container.resolve("start_session_use_case"),
            process_message_use_case=container.resolve("process_message_use_case"),
            get_conversation_use_case=container.resolve("get_conversation_use_case")
        ),
        singleton=True
    )

    return container

def get_chat_orchestrator():
    """Get chat orchestrator instance"""
    container = get_container()
    return container.resolve("chat_orchestrator")
```

### 5.3 Main Application Update

```python
# src/main.py - Updated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.api import health
from src.presentation.api.v1 import websocket
from src.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(websocket.router, prefix=settings.API_V1_STR)

    # Serve test client at root
    @app.get("/")
    async def root():
        with open("test_client.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)

    return app

app = create_app()
```

### Deliverables

- ✅ PydanticAI agent configured
- ✅ Indonesian prompts created
- ✅ PIM tools implemented
- ✅ Dependency injection setup
- ✅ Complete flow working

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/application/test_process_message_use_case.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.use_cases import ProcessUserMessageUseCaseImpl

@pytest.mark.asyncio
async def test_process_user_message():
    """Test processing user message"""

    # Arrange
    mock_ai = AsyncMock()
    mock_ai.generate_response.return_value = "Test response"

    mock_product_service = AsyncMock()
    mock_conversation_repo = AsyncMock()
    mock_conversation_repo.get_by_session.return_value = None

    mock_analyzer = AsyncMock()
    mock_analyzer.analyze.return_value = Mock(
        type="product_inquiry",
        products=["plat"],
        to_dict=lambda: {"type": "product_inquiry"}
    )

    use_case = ProcessUserMessageUseCaseImpl(
        ai_agent=mock_ai,
        product_service=mock_product_service,
        conversation_repository=mock_conversation_repo,
        query_analyzer=mock_analyzer
    )

    # Act
    result = await use_case.execute(
        session_id="test-session",
        content="Ada plat baja 5mm?"
    )

    # Assert
    assert result.content == "Test response"
    assert result.sender_type == "ai_agent"
    mock_ai.generate_response.assert_called_once()
```

### Integration Tests

```python
# tests/integration/test_websocket_flow.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_websocket_connection():
    """Test WebSocket connection and message flow"""

    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert data["event"] == "connected"

        # Send user message
        websocket.send_json({
            "type": "user_message",
            "message": "Halo"
        })

        # Receive typing indicator
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert data["event"] == "typing"

        # Receive AI response
        data = websocket.receive_json()
        assert data["type"] == "ai_response"
        assert "Selamat datang" in data["message"]
```

### End-to-End Test Script

```bash
#!/bin/bash
# test_e2e.sh

echo "Starting Steel Chat MVP E2E Test"

# 1. Start the application
echo "Starting application..."
python -m uvicorn src.main:app --reload &
APP_PID=$!
sleep 5

# 2. Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | grep "healthy"

# 3. Test WebSocket with wscat
echo "Testing WebSocket..."
echo '{"type":"user_message","message":"Ada plat baja?"}' | \
  wscat -c ws://localhost:8000/api/v1/ws/test-session-123 -x '{"type":"ping"}' -w 5

# 4. Cleanup
echo "Cleaning up..."
kill $APP_PID

echo "E2E Test Complete"
```

---

## Deployment & Validation

### Local Development

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 2. Install dependencies
pip install -r requirements/base.txt

# 3. Run application
python -m uvicorn src.main:app --reload

# 4. Open browser
# Navigate to http://localhost:8000 for test client
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

COPY src/ ./src/
COPY test_client.html .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t steel-chat-mvp .
docker run -p 8000:8000 steel-chat-mvp
```

### Validation Checklist

- [ ] WebSocket connection establishes successfully
- [ ] User messages are received and processed
- [ ] AI responses are generated (mock or real)
- [ ] Indonesian language responses work correctly
- [ ] Product queries return relevant information
- [ ] Session management works (Redis or mock)
- [ ] Heartbeat keeps connection alive
- [ ] Error handling returns Indonesian messages
- [ ] Conversation context is maintained
- [ ] 5+ concurrent connections work smoothly

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PydanticAI integration issues | High | Start with mock AI, integrate incrementally |
| WebSocket stability | Medium | Implement reconnection logic, heartbeat |
| PIM API unavailable | High | Use mock data, implement caching |
| Performance issues | Medium | Start with in-memory storage, optimize later |
| Indonesian NLP accuracy | Medium | Collect feedback, fine-tune prompts |

### Mitigation Strategies

1. **Incremental Integration**: Replace mocks one component at a time
2. **Feature Flags**: Toggle between mock and real implementations
3. **Monitoring**: Add logging at every critical point
4. **Graceful Degradation**: Fallback to cached/mock data when services fail
5. **Testing**: Comprehensive test coverage before each integration

---

## Success Criteria

### Functional Requirements

- ✅ User can connect via WebSocket
- ✅ User can send messages in Indonesian
- ✅ System processes queries and returns responses
- ✅ Product information is displayed correctly
- ✅ Conversation context is maintained
- ✅ Multiple users can chat simultaneously

### Performance Requirements

- ✅ Response time < 2 seconds (mock)
- ✅ Support 10-20 concurrent users
- ✅ WebSocket connection stable for 1+ hour
- ✅ Memory usage < 500MB

### Quality Requirements

- ✅ 80% test coverage on application layer
- ✅ All critical paths have integration tests
- ✅ Error messages in Indonesian
- ✅ Graceful error handling

---

## Next Steps After MVP

### Week 2: Real Infrastructure

1. Implement PerkyOSClient with JWT
2. Create concrete ProductRepository
3. Setup PostgreSQL with SQLAlchemy
4. Implement real Redis caching

### Week 3: Production Features

1. Add authentication/authorization
2. Implement conversation persistence
3. Add analytics and monitoring
4. Create admin dashboard

### Week 4: Optimization

1. Performance tuning
2. Add comprehensive logging
3. Implement rate limiting
4. Setup CI/CD pipeline

---

## Phase 6: LLM Testing Strategy

### Objectives

- Define testing approach for LLM components
- Create test fixtures for AI agents
- Implement deterministic testing patterns
- Setup cost monitoring

### 6.1 LLM Component Testing Approaches

```python
# tests/integration/test_llm_agents.py
import pytest
from unittest.mock import AsyncMock, patch
from src.infrastructure.llm import LLMQueryAnalyzer, LLMResponseAgent
from src.domain.value_objects import QueryIntent

class TestLLMQueryAnalyzer:
    """Test strategies for LLM Query Analyzer"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for deterministic testing"""
        mock = AsyncMock()
        mock.chat.completions.create.return_value = AsyncMock(
            choices=[AsyncMock(
                message=AsyncMock(
                    content='{"type": "product_inquiry", "confidence": 0.9}'
                )
            )]
        )
        return mock

    @pytest.mark.asyncio
    async def test_intent_analysis_with_mock(self, mock_openai_client):
        """Test intent analysis with mocked responses"""
        analyzer = LLMQueryAnalyzer(client=mock_openai_client)

        intent = await analyzer.analyze_intent(
            query="I need steel plates",
            context={}
        )

        assert intent.type == "product_inquiry"
        assert intent.confidence >= 0.8

    @pytest.mark.asyncio
    @pytest.mark.integration  # Run only in integration tests
    async def test_intent_analysis_with_real_api(self):
        """Test with real API (expensive, run sparingly)"""
        analyzer = LLMQueryAnalyzer()  # Uses real client

        test_queries = [
            ("harga plat baja 5mm", "price_check"),
            ("stok hollow galvanis", "availability_check"),
            ("saya butuh besi siku", "product_inquiry")
        ]

        for query, expected_type in test_queries:
            intent = await analyzer.analyze_intent(query)
            assert intent.type == expected_type
```

### 6.2 Cost-Effective Testing Patterns

```python
# tests/fixtures/llm_fixtures.py
import json
from typing import Dict, Any

class LLMTestFixtures:
    """Reusable test fixtures for LLM testing"""

    @staticmethod
    def get_sample_intents() -> Dict[str, QueryIntent]:
        """Pre-analyzed intents for common queries"""
        return {
            "greeting": QueryIntent(
                type="general",
                confidence=0.95,
                original_query="hello",
                current_query="hello",
                clarification_stage="initial",
                query_level="ambiguous",
                next_action="provide_info"
            ),
            "product_inquiry": QueryIntent(
                type="product_inquiry",
                confidence=0.85,
                original_query="I need steel plates",
                current_query="I need steel plates",
                clarification_stage="narrowing",
                query_level="product",
                next_action="request_clarification",
                product_name="steel plates"
            )
        }

    @staticmethod
    def get_mock_responses() -> Dict[str, str]:
        """Mock AI responses for testing"""
        return {
            "greeting": "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
            "product_info": "Untuk plat baja, kami memiliki berbagai ukuran...",
            "clarification": "Bisa tolong sebutkan ukuran yang Anda butuhkan?"
        }
```

### 6.3 Testing Environment Configuration

```yaml
# tests/config/test_config.yaml
llm_testing:
  use_mocks: true  # Default to mocks for unit tests
  real_api_tests: false  # Enable for integration tests only
  max_test_cost_usd: 1.00  # Maximum cost per test run
  cache_responses: true  # Cache real API responses for reuse

  test_modes:
    unit:
      use_mocks: true
      timeout_seconds: 5
    integration:
      use_mocks: false
      timeout_seconds: 30
      rate_limit: 10  # requests per minute

  mock_response_patterns:
    - pattern: "price|harga"
      intent_type: "price_check"
      confidence: 0.9
    - pattern: "stock|stok"
      intent_type: "availability_check"
      confidence: 0.85
```

---

## Phase 7: Fallback Mechanisms and Error Recovery

### Objectives

- Implement graceful degradation
- Add circuit breaker patterns
- Create fallback responses
- Setup monitoring and alerting

### 7.1 API Failure Fallback Strategy

```python
# src/infrastructure/llm/fallback_handler.py
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from src.domain.value_objects import QueryIntent

logger = logging.getLogger(__name__)

class LLMFallbackHandler:
    """Handles failures and provides fallback mechanisms"""

    def __init__(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_open_until = None

    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_open and self.circuit_open_until:
            if datetime.now() > self.circuit_open_until:
                # Try to close circuit
                self.circuit_open = False
                self.failure_count = 0
                logger.info("Circuit breaker closed, retrying API")
        return self.circuit_open

    def record_failure(self):
        """Record API failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= 3:
            # Open circuit breaker for 5 minutes
            self.circuit_open = True
            self.circuit_open_until = datetime.now() + timedelta(minutes=5)
            logger.warning(f"Circuit breaker opened until {self.circuit_open_until}")

    def get_fallback_intent(self, query: str) -> QueryIntent:
        """Generate fallback intent using pattern matching"""
        logger.warning("Using fallback intent analysis")

        # Simple pattern-based fallback
        query_lower = query.lower()

        if any(word in query_lower for word in ["harga", "price", "cost"]):
            intent_type = "price_check"
        elif any(word in query_lower for word in ["stok", "stock", "available"]):
            intent_type = "availability_check"
        elif any(word in query_lower for word in ["plat", "hollow", "besi", "pipa"]):
            intent_type = "product_inquiry"
        else:
            intent_type = "general"

        return QueryIntent(
            type=intent_type,
            confidence=0.5,  # Lower confidence for fallback
            original_query=query,
            current_query=query,
            clarification_stage="initial",
            query_level="ambiguous",
            next_action="request_clarification",
            requires_human_intervention=True  # Flag for human review
        )

    def get_fallback_response(self, message: str, intent: Optional[QueryIntent] = None) -> str:
        """Generate fallback response when AI agent fails"""
        logger.warning("Using fallback response generation")

        if intent and intent.type == "product_inquiry":
            return (
                "Mohon maaf, sistem kami sedang mengalami gangguan. "
                "Untuk informasi produk, silakan hubungi customer service kami "
                "di nomor 021-1234567 atau email ke sales@smsperkasa.com"
            )
        elif intent and intent.type == "price_check":
            return (
                "Mohon maaf, sistem harga sedang tidak dapat diakses. "
                "Untuk informasi harga terkini, silakan hubungi tim sales kami."
            )
        else:
            return (
                "Mohon maaf, sistem sedang mengalami gangguan teknis. "
                "Silakan coba beberapa saat lagi atau hubungi customer service kami."
            )
```

### 7.2 Enhanced LLM Agents with Fallback

```python
# src/infrastructure/llm/query_analyzer_with_fallback.py
from typing import Optional, Dict, Any
from src.application.ports import QueryAnalyzerPort
from src.infrastructure.llm import LLMQueryAnalyzer
from src.infrastructure.llm.fallback_handler import LLMFallbackHandler
from src.infrastructure.mocks import MockQueryAnalyzer

class ResilientQueryAnalyzer(QueryAnalyzerPort):
    """Query analyzer with fallback mechanisms"""

    def __init__(self, primary_analyzer=None, use_mock_fallback=True):
        self.primary = primary_analyzer or LLMQueryAnalyzer()
        self.fallback_handler = LLMFallbackHandler()
        self.mock_analyzer = MockQueryAnalyzer() if use_mock_fallback else None

    async def analyze_intent(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryIntent:
        """Analyze with automatic fallback on failure"""

        # Check circuit breaker
        if self.fallback_handler.check_circuit_breaker():
            # Circuit is open, use fallback directly
            return await self._use_fallback(query, context)

        try:
            # Try primary LLM analyzer
            return await self.primary.analyze_intent(query, context)

        except Exception as e:
            logger.error(f"Primary analyzer failed: {e}")
            self.fallback_handler.record_failure()

            # Use fallback mechanism
            return await self._use_fallback(query, context)

    async def _use_fallback(self, query: str, context: Optional[Dict[str, Any]]) -> QueryIntent:
        """Use fallback mechanism"""
        if self.mock_analyzer:
            # Try mock analyzer first
            try:
                return await self.mock_analyzer.analyze_intent(query, context)
            except:
                pass

        # Last resort: pattern-based fallback
        return self.fallback_handler.get_fallback_intent(query)
```

### 7.3 Monitoring and Alerting Configuration

```python
# src/infrastructure/monitoring/llm_monitor.py
from typing import Dict, Any
import logging
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

class LLMMonitor:
    """Monitor LLM service health and performance"""

    def __init__(self, window_size: int = 100):
        self.api_calls = deque(maxlen=window_size)
        self.failures = deque(maxlen=window_size)
        self.response_times = deque(maxlen=window_size)
        self.fallback_uses = 0

    def record_api_call(self, success: bool, response_time_ms: float, used_fallback: bool = False):
        """Record API call metrics"""
        self.api_calls.append({
            "timestamp": datetime.now(),
            "success": success,
            "response_time_ms": response_time_ms,
            "used_fallback": used_fallback
        })

        if not success:
            self.failures.append(datetime.now())

        if used_fallback:
            self.fallback_uses += 1

        self.response_times.append(response_time_ms)

        # Check for alerting conditions
        self._check_alert_conditions()

    def _check_alert_conditions(self):
        """Check if alert conditions are met"""
        if len(self.failures) >= 5:
            # 5 failures in window
            logger.critical(f"HIGH FAILURE RATE: {len(self.failures)} failures in last {len(self.api_calls)} calls")

        if self.response_times and sum(self.response_times) / len(self.response_times) > 5000:
            # Average response time > 5 seconds
            logger.warning(f"SLOW API RESPONSE: Average {sum(self.response_times) / len(self.response_times):.0f}ms")

        if self.fallback_uses > 10:
            # High fallback usage
            logger.warning(f"HIGH FALLBACK USAGE: {self.fallback_uses} fallback responses used")

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        total_calls = len(self.api_calls)
        successful_calls = sum(1 for call in self.api_calls if call["success"])

        return {
            "status": "healthy" if successful_calls / max(total_calls, 1) > 0.8 else "degraded",
            "success_rate": successful_calls / max(total_calls, 1),
            "average_response_time_ms": sum(self.response_times) / max(len(self.response_times), 1),
            "fallback_uses": self.fallback_uses,
            "recent_failures": len(self.failures)
        }
```

---

## Appendix A: File Structure

```text
src/
├── application/
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── message_dto.py
│   │   ├── conversation_dto.py
│   │   ├── session_dto.py
│   │   └── product_query_dto.py
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── interfaces.py
│   │   ├── start_chat_session.py
│   │   ├── process_message.py
│   │   └── get_conversation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_orchestrator.py
│   │   └── query_analyzer.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── ai_agent_port.py
│   │   ├── query_analyzer_port.py
│   │   └── product_service_port.py
│   └── container.py
├── infrastructure/
│   ├── mocks/
│   │   ├── __init__.py
│   │   ├── mock_ai_agent.py
│   │   ├── mock_product_repository.py
│   │   ├── mock_conversation_repository.py
│   │   └── mock_redis_client.py
│   └── ai/
│       ├── __init__.py
│       └── pydantic_agent.py
├── presentation/
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── connection_manager.py
│   │   └── chat_ws.py
│   ├── api/
│   │   └── v1/
│   │       └── websocket.py
│   └── dependencies.py
└── main.py
```

---

## Appendix B: Environment Variables

```env
# .env file for MVP

# Application
PROJECT_NAME="Steel Chat MVP"
VERSION="0.1.0"
API_V1_STR="/api/v1"

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Database (not used in MVP)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=steel_chat

# Redis (mock for MVP)
REDIS_URL=redis://localhost:6379
REDIS_SESSION_TTL=3600
REDIS_CACHE_TTL=900

# PIM Integration (mock for MVP)
PERKY_OS_API_URL=https://api.perkyos.com/v1
PERKY_OS_JWT_SECRET=your-jwt-secret
PERKY_OS_TIMEOUT=5000

# OpenAI (optional for MVP)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_RETRIES=2

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_MESSAGE_RATE_LIMIT=10

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Conclusion

This MVP implementation plan provides a **working chat system in 5 days** that:

1. **Demonstrates core value**: Real-time chat with product inquiries
2. **Validates architecture**: DDD layers working together
3. **Enables parallel development**: Teams can work on infrastructure while app layer uses mocks
4. **Reduces risk**: Early integration testing and validation
5. **Provides feedback opportunity**: Stakeholders can test and provide input

The key is to **start with the application layer** using mocks, get everything working
end-to-end, then systematically replace mocks with real implementations. This approach
ensures you always have a working system and can demonstrate progress continuously.

**Remember**: The goal is not perfection, but a working prototype that validates the
approach and provides a foundation for iterative improvement.
