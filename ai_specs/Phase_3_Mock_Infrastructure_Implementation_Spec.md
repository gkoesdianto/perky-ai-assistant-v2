# Phase 3: Mock Infrastructure Implementation Specification

## Executive Summary

This document provides a comprehensive implementation specification for Phase 3:
Mock Infrastructure of the Steel Chat MVP. This phase creates a complete in-memory
simulation layer that enables rapid development and testing of the application without
external dependencies.

**Timeline**: Day 2 (8 hours)
**Complexity**: Medium
**Dependencies**: Phase 1 (Application Layer) and Phase 2 (Single Agent Implementation) must be complete

## Objectives

1. Create mock implementations for all external dependencies
2. Enable end-to-end testing without external services
3. Provide realistic data for the three core MVP scenarios
4. Establish patterns for easy migration to real implementations

## Architecture Overview

```text
Application Layer
       ↓
    Ports (Interfaces)
       ↓
Mock Infrastructure Layer
├── Mock Redis Client (Session Management)
├── Mock Conversation Repository (In-Memory Storage)
├── Mock Product Repository (Hardcoded Catalog)
├── Mock Query Analyzer (Pattern Matching)
└── Mock AI Agent (Template Responses)
```

## Component Specifications

### 3.1 Mock Redis Client

**Purpose**: Simulate Redis operations for session management without actual Redis dependency

**Location**: `src/infrastructure/mocks/mock_redis_client.py`

**Implementation Requirements**:

```python
class MockRedisClient:
    """
    In-memory Redis simulation with TTL support
    Thread-safe for concurrent WebSocket connections
    """

    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()  # Thread safety

    async def get(self, key: str) -> Optional[Any]:
        """Get value with TTL checking"""
        # Check and remove expired keys
        # Deserialize JSON if needed
        # Return None if not found or expired

    async def set(self, key: str, value: Any) -> None:
        """Set value without expiry"""
        # Serialize complex objects to JSON
        # Store in memory

    async def setex(self, key: str, seconds: int, value: Any) -> None:
        """Set with TTL expiry"""
        # Calculate expiry datetime
        # Store value and expiry

    async def delete(self, key: str) -> None:
        """Delete key and expiry"""
        # Remove from both storage and expiry dicts
```

**Key Features**:
- Automatic JSON serialization/deserialization
- TTL expiry checking on get operations
- Thread-safe operations with asyncio.Lock
- Memory cleanup for expired keys
- Support for complex object storage

**Test Data**:
- Session objects with metadata
- Conversation IDs with TTL
- User preferences and state

### 3.2 Mock Product Repository

**Purpose**: Provide hardcoded Indonesian steel product catalog for MVP scenarios

**Location**: `src/infrastructure/mocks/mock_product_repository.py`

**Implementation Requirements**:

```python
class MockProductRepository(ProductRepository):
    """
    Hardcoded product catalog with realistic Indonesian steel data
    Implements domain ProductRepository interface
    """

    def __init__(self):
        self.products = self._create_mock_products()

    def _create_mock_products(self) -> Dict[str, ProductWithVariantsInfo]:
        """Initialize realistic product catalog"""
        return {
            "PROD-001": self._create_plat_baja(),
            "PROD-002": self._create_hollow_galvanis(),
            "PROD-003": self._create_h_beam(),
            "PROD-004": self._create_besi_beton(),
            "PROD-005": self._create_pipa_baja()
        }

    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search with Indonesian terminology support"""
        # Handle Indonesian steel terms: plat, besi, hollow, profil
        # Case-insensitive matching
        # Return top 5 relevant products

    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Get specific variant with pricing and stock"""
        # Direct SKU lookup across all products
        # Return full variant details
```

**Product Catalog Data**:

```python
# Plat Baja Hitam (Steel Plates)
{
    "product_id": "PROD-001",
    "name": "Plat Baja Hitam SS400",
    "category": "Plat",
    "variants": [
        {
            "sku": "PLT-5MM-4X8",
            "size": "5mm x 1200mm x 2400mm",
            "price": 125000.00,  # IDR
            "stock": 150,
            "unit": "lembar"
        },
        {
            "sku": "PLT-10MM-4X8",
            "size": "10mm x 1200mm x 2400mm",
            "price": 250000.00,
            "stock": 75,
            "unit": "lembar"
        }
    ]
}

# Hollow Galvanis (Galvanized Hollow)
{
    "product_id": "PROD-002",
    "name": "Besi Hollow Galvanis",
    "category": "Hollow",
    "variants": [
        {
            "sku": "HLW-40X40-GLV",
            "size": "40mm x 40mm x 6m",
            "material": "Galvanis",
            "price": 85000.00,
            "stock": 200,
            "unit": "batang"
        },
        {
            "sku": "HLW-50X50-GLV",
            "size": "50mm x 50mm x 6m",
            "price": 110000.00,
            "stock": 150,
            "unit": "batang"
        }
    ]
}

# H-Beam (Structural Steel)
{
    "product_id": "PROD-003",
    "name": "H-Beam WF",
    "category": "Profil",
    "variants": [
        {
            "sku": "HBEAM-200X200",
            "size": "200x200x8x12mm",
            "weight": "49.9kg/m",
            "price": 850000.00,
            "stock": 50,
            "unit": "batang"
        }
    ]
}
```

### 3.3 Mock Conversation Repository

**Purpose**: In-memory storage for conversation management

**Location**: `src/infrastructure/mocks/mock_conversation_repository.py`

**Implementation Requirements**:

```python
class MockConversationRepository(ConversationRepository):
    """
    Simple in-memory conversation storage
    No persistence required for MVP
    """

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self._lock = asyncio.Lock()

    async def save(self, conversation: Conversation) -> None:
        """Store or update conversation"""
        async with self._lock:
            self.conversations[conversation.session_id] = conversation

    async def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """Retrieve conversation by session ID"""
        return self.conversations.get(session_id)

    async def delete(self, session_id: str) -> None:
        """Remove conversation from memory"""
        async with self._lock:
            self.conversations.pop(session_id, None)

    async def cleanup_expired(self) -> None:
        """Remove inactive conversations (optional)"""
        # Cleanup conversations older than 1 hour
        # Based on last_activity timestamp
```

### 3.4 Mock Query Analyzer

**Purpose**: Pattern-based intent detection for Indonesian queries

**Location**: `src/infrastructure/mocks/mock_query_analyzer.py`

**Implementation Requirements**:

```python
class MockQueryAnalyzer(QueryAnalyzerPort):
    """
    Pattern matching for query intent analysis
    Indonesian language support
    """

    def __init__(self):
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

    async def analyze(
        self,
        query: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """
        Analyze query to determine intent
        Returns QueryIntent value object
        """
        query_lower = query.lower()

        # Pattern matching logic
        query_type = self._detect_query_type(query_lower)
        confidence = self._calculate_confidence(query_lower, query_type)
        attributes = self._extract_attributes(query_lower)

        # Determine clarification stage
        stage = self._determine_stage(
            confidence,
            conversation_context
        )

        return QueryIntent(
            type=query_type,
            clarification_stage=stage,
            detected_attributes=attributes,
            confidence=confidence,
            original_query=query,
            product_name=attributes.get("product_type"),
            quantity=self._extract_quantity(query_lower)
        )
```

**Pattern Categories**:

```python
# Indonesian Steel Terminology Mapping
TERMINOLOGY_MAP = {
    # Common products
    "plat": ["plate", "sheet", "plat baja"],
    "hollow": ["hollow", "kotak", "besi kotak"],
    "besi": ["iron", "steel", "besi baja"],
    "pipa": ["pipe", "tube", "pipa baja"],

    # Specific products
    "wf": ["wide flange", "h-beam", "profil wf"],
    "unp": ["channel", "kanal u", "profil u"],
    "siku": ["angle", "angle bar", "besi siku"],

    # Actions
    "beli": ["buy", "purchase", "order"],
    "pesan": ["order", "request", "book"],
    "cek": ["check", "verify", "confirm"]
}
```

### 3.5 Mock AI Agent

**Purpose**: Generate template-based Indonesian responses for chat

**Location**: `src/infrastructure/mocks/mock_ai_agent.py`

**Implementation Requirements**:

```python
class MockAIAgent(AIAgentPort):
    """
    Template-based response generation
    Indonesian B2B language style
    """

    RESPONSES = {
        "greeting": [
            "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
            "Halo! Saya PERKY, asisten produk baja Anda. Apa yang Anda cari?"
        ],
        "product_plat": [
            "Untuk plat baja, kami memiliki:\n"
            "• Plat hitam SS400: 2mm-20mm\n"
            "• Plat galvanis: 0.8mm-3mm\n"
            "• Plat bordes: 3mm-6mm\n"
            "Ukuran standar 4x8 feet. Ada spesifikasi khusus?"
        ],
        "product_hollow": [
            "Besi hollow tersedia dalam:\n"
            "• Hollow galvanis: 20x20 hingga 100x100\n"
            "• Hollow hitam: ukuran sama\n"
            "• Ketebalan: 1.2mm - 3.2mm\n"
            "Panjang standar 6 meter. Butuh ukuran apa?"
        ],
        "price_inquiry": [
            "Harga terkini {product}:\n"
            "• {variant1}: Rp {price1}/lembar\n"
            "• {variant2}: Rp {price2}/lembar\n"
            "Harga dapat berubah sewaktu-waktu. Mau pesan?"
        ],
        "stock_check": [
            "Stok {product} saat ini:\n"
            "• {variant}: {stock} {unit}\n"
            "Stok update realtime. Butuh berapa {unit}?"
        ],
        "order_flow": [
            "Untuk pemesanan {product}:\n"
            "1. Tentukan spesifikasi\n"
            "2. Konfirmasi jumlah\n"
            "3. Kami siapkan penawaran\n"
            "Silakan sebutkan jumlah yang dibutuhkan."
        ]
    }

    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        """
        Generate contextual response based on patterns
        Maintain conversation flow
        """
        message_lower = message.lower()

        # Greeting detection
        if self._is_greeting(message_lower):
            return random.choice(self.RESPONSES["greeting"])

        # Product inquiry
        product_type = self._detect_product(message_lower)
        if product_type:
            return self._format_product_response(product_type)

        # Price check
        if self._is_price_query(message_lower):
            return self._format_price_response(message_lower)

        # Stock availability
        if self._is_stock_query(message_lower):
            return self._format_stock_response(message_lower)

        # Default contextual response
        return self._generate_contextual_response(
            message_lower,
            conversation_context
        )
```

**Response Templates**:

```python
# Professional B2B Indonesian Templates
PROFESSIONAL_TEMPLATES = {
    "confirmation": "Baik, saya catat kebutuhan Anda: {requirement}",
    "clarification": "Mohon info lebih detail mengenai {aspect}",
    "recommendation": "Berdasarkan kebutuhan Anda, saya rekomendasikan {product}",
    "next_step": "Langkah selanjutnya: {action}",
    "closing": "Terima kasih. Tim sales kami akan follow up segera."
}

# Error/Fallback Responses
FALLBACK_RESPONSES = [
    "Mohon maaf, bisa tolong lebih spesifik produk yang Anda cari?",
    "Saya perlu informasi lebih detail. Produk apa yang Anda butuhkan?",
    "Maaf, bisa ulangi pertanyaan Anda dengan lebih jelas?"
]
```

## Integration Patterns

### Dependency Injection Configuration

```python
# src/infrastructure/container.py
class MockInfrastructureContainer:
    """
    Dependency container for mock implementations
    Easy switching via environment flags
    """

    def __init__(self, use_mocks: bool = True):
        self.use_mocks = use_mocks

        if use_mocks:
            self._setup_mocks()
        else:
            self._setup_real_implementations()

    def _setup_mocks(self):
        # Register all mock implementations
        self.redis_client = MockRedisClient()
        self.conversation_repo = MockConversationRepository()
        self.product_repo = MockProductRepository()
        self.query_analyzer = MockQueryAnalyzer()
        self.ai_agent = MockAIAgent()

    def _setup_real_implementations(self):
        # Future: Register real implementations
        pass
```

### Environment Configuration

```python
# .env configuration for mocks
USE_MOCK_MODE=true
MOCK_RESPONSE_DELAY_MS=0  # Simulate network delay
MOCK_ERROR_RATE=0.0       # Simulate errors for testing
MOCK_DATA_SEED=42         # Consistent random data
```

## Testing Strategy

### Unit Tests for Each Mock

```python
# tests/unit/infrastructure/mocks/test_mock_product_repository.py
class TestMockProductRepository:
    async def test_search_products_indonesian_terms(self):
        """Test search with Indonesian terminology"""
        repo = MockProductRepository()

        # Test Indonesian terms
        results = await repo.search_products("plat")
        assert len(results) > 0
        assert any("plat" in p.name.lower() for p in results)

        # Test partial matching
        results = await repo.search_products("hol")
        assert any("hollow" in p.name.lower() for p in results)

    async def test_get_variant_by_sku(self):
        """Test SKU lookup with pricing"""
        repo = MockProductRepository()

        variant = await repo.get_variant_by_sku("PLT-5MM-4X8")
        assert variant is not None
        assert variant.price == 125000.00
        assert variant.stock_quantity == 150
```

### Integration Tests

```python
# tests/integration/test_mock_chat_flow.py
class TestMockChatFlow:
    async def test_complete_product_inquiry_flow(self):
        """Test end-to-end chat flow with mocks"""
        # Setup mock infrastructure
        container = MockInfrastructureContainer()

        # Create chat orchestrator with mocks
        orchestrator = ChatOrchestrator(
            ai_agent=container.ai_agent,
            product_service=container.product_repo,
            conversation_repo=container.conversation_repo
        )

        # Test product inquiry
        response = await orchestrator.handle_user_message(
            session_id="test-123",
            content="Ada plat baja 5mm?"
        )

        assert "plat" in response.content.lower()
        assert "125000" in response.content or "125.000" in response.content
```

## Implementation Timeline

### Day 2 Schedule (8 hours)

| Time | Component | Deliverables |
|------|-----------|--------------|
| 09:00-10:00 | Mock Redis Client | Session storage with TTL |
| 10:00-11:00 | Mock Conversation Repo | In-memory conversation management |
| 11:00-13:00 | Mock Product Repository | Complete product catalog with Indonesian data |
| 14:00-16:00 | Mock Query Analyzer | Pattern-based intent detection |
| 16:00-17:30 | Mock AI Agent | Template response generation |
| 17:30-18:00 | Integration Testing | End-to-end flow validation |

### Parallel Development Opportunities

- **Team A**: Mock Redis + Conversation Repo (Infrastructure basics)
- **Team B**: Mock Product Repository (Business data)
- **Team C**: Mock Query Analyzer + AI Agent (NLP simulation)

## Quality Criteria

### Functional Requirements

- [ ] All repository interfaces properly implemented
- [ ] Async/await patterns consistently applied
- [ ] Indonesian language support throughout
- [ ] Three core scenarios fully supported
- [ ] Thread-safe for concurrent access

### Performance Requirements

- [ ] Mock response time < 10ms
- [ ] Support 10-20 concurrent sessions
- [ ] Memory usage < 100MB for typical load
- [ ] No memory leaks during extended operation

### Code Quality

- [ ] Type hints on all public methods
- [ ] Comprehensive docstrings
- [ ] 90%+ test coverage
- [ ] Logging for debugging
- [ ] Easy configuration via environment

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Mock data insufficient | Progressively add products based on testing feedback |
| Pattern matching too simple | Start simple, enhance based on actual user queries |
| Indonesian language accuracy | Review with native speakers, collect feedback |
| Performance under load | Profile and optimize hot paths |
| Integration complexity | Clear interfaces, comprehensive integration tests |

## Success Criteria

### Must Have (Day 2)

- ✅ All five mock components implemented
- ✅ Three core scenarios working end-to-end
- ✅ Basic Indonesian response templates
- ✅ Integration with application layer

### Should Have (If Time Permits)

- 🔄 Extended product catalog (10+ products)
- 🔄 Sophisticated query analysis
- 🔄 Conversation context awareness
- 🔄 Error simulation capabilities

### Nice to Have (Post-MVP)

- ⏳ Configuration UI for mock data
- ⏳ Response template editor
- ⏳ Mock data persistence
- ⏳ Performance profiling dashboard

## Migration Path to Real Implementations

### Week 2 Priorities

1. **Redis Integration**
   - Replace MockRedisClient with real Redis
   - Maintain same interface contract
   - Add connection pooling and retry logic

2. **PIM System Integration**
   - Replace MockProductRepository with PerkyOSClient
   - Implement caching layer
   - Handle API authentication

3. **Real AI Integration**
   - Replace MockAIAgent with PydanticAI
   - Implement proper NLP with GPT-4o-mini
   - Add conversation memory

4. **PostgreSQL Integration**
   - Replace MockConversationRepository
   - Implement SQLAlchemy models
   - Add database migrations

## Appendix A: Mock Data Structures

### Complete Product Catalog

```python
MOCK_PRODUCT_CATALOG = {
    "steel_plates": {
        "name": "Plat Baja",
        "products": [
            {"name": "Plat Hitam SS400", "thickness": ["2mm", "3mm", "4mm", "5mm", "6mm", "8mm", "10mm", "12mm", "15mm", "20mm"]},
            {"name": "Plat Galvanis", "thickness": ["0.4mm", "0.5mm", "0.6mm", "0.8mm", "1.0mm", "1.2mm"]},
            {"name": "Plat Bordes", "thickness": ["3mm", "4mm", "5mm", "6mm"]},
            {"name": "Plat Kapal", "grade": ["A", "AH32", "AH36"]}
        ]
    },
    "hollow_sections": {
        "name": "Hollow",
        "products": [
            {"name": "Hollow Galvanis", "sizes": ["20x20", "25x25", "30x30", "40x40", "50x50", "60x60", "75x75", "100x100"]},
            {"name": "Hollow Hitam", "sizes": ["20x20", "30x30", "40x40", "50x50", "60x60"]},
            {"name": "Hollow Rectangular", "sizes": ["20x40", "30x60", "40x80", "50x100"]}
        ]
    },
    "structural_steel": {
        "name": "Profil Baja",
        "products": [
            {"name": "H-Beam/WF", "sizes": ["100x100", "125x125", "150x150", "200x200", "250x250", "300x300"]},
            {"name": "Besi Siku", "sizes": ["30x30", "40x40", "50x50", "60x60", "70x70", "75x75"]},
            {"name": "UNP Channel", "sizes": ["50", "65", "80", "100", "120", "150"]},
            {"name": "CNP Channel", "sizes": ["75", "100", "125", "150"]}
        ]
    }
}
```

### Indonesian Business Phrases

```python
BUSINESS_PHRASES = {
    "greetings": [
        "Selamat pagi/siang/sore",
        "Terima kasih telah menghubungi SMS Perkasa",
        "Senang bisa membantu Anda hari ini"
    ],
    "product_inquiry": [
        "Kami memiliki stok lengkap untuk {product}",
        "Tersedia berbagai ukuran {product}",
        "Produk {product} ready stock dengan kualitas terjamin"
    ],
    "pricing": [
        "Harga {product} saat ini Rp {price}",
        "Untuk pembelian volume besar, tersedia harga khusus",
        "Harga belum termasuk PPN dan ongkir"
    ],
    "closing": [
        "Ada lagi yang bisa dibantu?",
        "Silakan hubungi tim sales untuk penawaran resmi",
        "Terima kasih atas kepercayaan Anda"
    ]
}
```

## Appendix B: Error Simulation

```python
class MockErrorSimulator:
    """
    Simulate errors for testing error handling
    Controlled via environment variables
    """

    def __init__(self, error_rate: float = 0.0):
        self.error_rate = error_rate

    async def maybe_fail(self, operation: str):
        """Randomly fail based on error rate"""
        if random.random() < self.error_rate:
            raise MockException(f"Simulated failure in {operation}")
```

## Conclusion

Phase 3: Mock Infrastructure provides a complete simulation layer that enables rapid
MVP development without external dependencies. The implementation focuses on supporting
the three core scenarios with realistic Indonesian B2B steel industry data and language
patterns. The modular design ensures easy migration to real implementations in
subsequent phases while maintaining the same interface contracts established by the
domain layer.

Key success factors:
1. Realistic mock data that covers actual business scenarios
2. Proper async/await implementation for WebSocket compatibility
3. Indonesian language support throughout
4. Clear separation between mock and real implementations
5. Comprehensive testing to ensure reliability

This specification provides the blueprint for implementing a functional mock
infrastructure in one day, enabling the team to proceed with Phase 4: WebSocket
Integration immediately upon completion.
