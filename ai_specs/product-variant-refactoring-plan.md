# Product-Variant Domain Model Refactoring Plan

## Executive Summary

This document outlines a comprehensive refactoring plan to properly model the
Product-Variant relationship in the PERKY AI Assistant chat system. The current
implementation lacks proper separation between product-level and variant-level
information, which is critical for handling user queries that may target either
products or specific SKUs.

**Key Changes:**
- Introduce separate value objects for `VariantInfo`, `ProductInfo`, and `ProductWithVariantsInfo`
- Enhance `QueryIntent` to distinguish between product-level and variant-level queries
- Maintain read-only nature of the domain model (no CUD operations)

---

## Current State Analysis

### Problem Statement

The existing `ProductInfo` value object conflates product and variant concepts:

```python
# Current ProductInfo (src/domain/value_objects/product_info.py)
class ProductInfo(BaseModel):
    sku: str          # This is variant-specific
    name: str         # Ambiguous: product or variant name?
    price: float      # Variant-specific
    stock: int        # Variant-specific
    # Missing: product_id, variant_id, clear relationship
```

**Issues:**
1. **No Product-Variant Distinction**: Cannot represent a product with multiple variants
2. **Ambiguous Queries**: Cannot handle "Show me product X" vs "Show me SKU Y"
3. **Lost Information**: No way to group variants under their parent product
4. **User Experience**: Cannot present variant selection when user queries a product

### PIM System Requirements

Based on the PIM integration requirements:
- **Product**: Has `product_id`, `product_name`, and contains 1+ variants
- **Variant**: Has `variant_id`, `sku`, `variant_name`, `price`, `stock`, `product_id` (FK)
- **Query Pattern**: Users may query by product name (return all variants) or specific SKU

---

## Proposed Domain Model

### 1. VariantInfo Value Object

**Purpose**: Represents a single sellable unit with specific SKU, pricing, and stock information.

```python
# src/domain/value_objects/variant_info.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from decimal import Decimal

class VariantInfo(BaseModel):
    """
    Read-only representation of a product variant from PIM.
    Each variant is a specific sellable configuration of a product.
    """

    # Identifiers
    variant_id: str = Field(..., description="Unique variant identifier from PIM")
    sku: str = Field(..., description="Stock Keeping Unit for inventory")
    product_id: str = Field(..., description="Parent product identifier")

    # Variant Details
    variant_name: str = Field(..., description="Variant description (e.g., 'Plat Baja 5mm x 1200mm x 2400mm')")

    # Commerce Information
    price: Decimal = Field(..., ge=0, description="Unit price in IDR")
    stock_quantity: int = Field(..., ge=0, description="Available stock")
    stock_unit: str = Field(default="lembar", description="Unit of measurement")

    # Variant Specifications
    specifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variant-specific attributes (thickness, dimensions, grade, etc.)"
    )

    # Metadata
    source: Literal["pim", "cache"] = Field(default="pim")
    is_available: bool = Field(default=True)

    class Config:
        frozen = True  # Immutable value object
```

### 2. ProductInfo Value Object

**Purpose**: Represents product-level information without variant details.

```python
# src/domain/value_objects/product_info.py (refactored)

from pydantic import BaseModel, Field
from typing import Optional, List

class ProductInfo(BaseModel):
    """
    Read-only representation of a product from PIM.
    A product is a category that contains one or more variants.
    """

    # Identifiers
    product_id: str = Field(..., description="Unique product identifier")

    # Product Details
    product_name: str = Field(..., description="Product category name (e.g., 'Plat Baja')")
    product_description: Optional[str] = Field(None, description="Product overview")

    # Product Metadata
    category: Optional[str] = Field(None, description="Product category in PIM")
    variant_count: int = Field(..., ge=1, description="Number of available variants")

    class Config:
        frozen = True  # Immutable value object
```

### 3. ProductWithVariantsInfo Aggregate Value Object

**Purpose**: Combines product information with all its variants for comprehensive queries.

```python
# src/domain/value_objects/product_with_variants_info.py

from pydantic import BaseModel, Field
from typing import List, Optional
from .product_info import ProductInfo
from .variant_info import VariantInfo

class ProductWithVariantsInfo(BaseModel):
    """
    Read-only aggregate representing a product with all its variants.
    Used when users query for a product without specifying a variant.
    """

    product: ProductInfo = Field(..., description="Product-level information")
    variants: List[VariantInfo] = Field(..., min_items=1, description="All product variants")

    # Computed Properties
    @property
    def price_range(self) -> tuple[Decimal, Decimal]:
        """Min and max price across variants"""
        prices = [v.price for v in self.variants]
        return (min(prices), max(prices))

    @property
    def available_skus(self) -> List[str]:
        """List of all available SKUs"""
        return [v.sku for v in self.variants if v.is_available]

    def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Retrieve specific variant by SKU"""
        return next((v for v in self.variants if v.sku == sku), None)

    class Config:
        frozen = True  # Immutable value object
```

### 4. Enhanced QueryIntent Value Object for Conversational AI

**Purpose**: Enable progressive variant clarification through multi-turn conversations with Pydantic AI agent.

```python
# src/domain/value_objects/query_intent.py (enhanced for conversational AI)

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any

class ClarificationNeeded(BaseModel):
    """Represents an attribute that needs user clarification"""
    attribute_type: Literal[
        "product_type",     # e.g., hollow steel vs solid steel  
        "material",         # e.g., hitam (black) vs galvanis
        "dimensions",       # e.g., 20x20, 40x40, 100x100
        "thickness",        # e.g., 1.2mm, 2mm, 3mm
        "length",          # e.g., 6m, 12m
        "grade",           # e.g., grade A, grade B
        "finish"           # e.g., polished, raw
    ]

    question_template: str = Field(
        ...,
        description="Template for generating clarification question"
    )
    options: List[str] = Field(
        ...,
        description="Available options for this attribute"
    )
    priority: int = Field(
        ...,
        ge=1,
        description="Order of clarification (1 = ask first)"
    )
    depends_on: Optional[str] = Field(
        None,
        description="Attribute that must be resolved before this one"
    )

class ConversationContext(BaseModel):
    """Maintains state across conversation turns"""
    resolved_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attributes already clarified by user"
    )
    pending_clarifications: List[ClarificationNeeded] = Field(
        default_factory=list,
        description="Attributes still needing clarification"
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous turns in conversation"
    )
    attribute_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for resolved attributes"
    )

class QueryIntent(BaseModel):
    """
    Enhanced query intent for conversational product/variant discovery.
    Supports multi-turn clarification flow for Pydantic AI agent with ChatGPT 4o mini.
    """

    # Query Classification
    type: Literal[
        "product_inquiry",      # General product information
        "availability_check",   # Stock availability
        "price_check",         # Price inquiry
        "variant_selection",   # Specific variant query
        "general"             # Non-product queries
    ]

    # Conversation Stage
    clarification_stage: Literal[
        "initial",      # First user query
        "narrowing",    # Progressive clarification in progress
        "confirming",   # Final confirmation before selection
        "complete"      # All attributes resolved
    ] = Field(default="initial")

    # Query Resolution Level
    query_level: Literal["product", "variant", "ambiguous"] = Field(
        default="ambiguous",
        description="Whether query targets product or specific variant"
    )

    # Conversation Management
    conversation_context: ConversationContext = Field(
        default_factory=ConversationContext,
        description="Stateful conversation tracking"
    )
    conversation_turn: int = Field(
        default=1,
        description="Current turn number in conversation"
    )

    # Next Action Guidance
    next_action: Literal[
        "provide_info",           # Give requested information
        "request_clarification",  # Ask for more details
        "suggest_alternatives",   # Offer similar products
        "confirm_selection"       # Confirm final variant selection
    ] = Field(default="request_clarification")

    next_clarification: Optional[ClarificationNeeded] = Field(
        None,
        description="Next attribute to clarify if needed"
    )

    # Response Generation
    suggested_response: Optional[str] = Field(
        None,
        description="Suggested response for the agent"
    )
    response_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Data to include in response (products, variants, etc.)"
    )

    # Product/Variant Matching
    matched_products: List[str] = Field(
        default_factory=list,
        description="Product IDs that match current query state"
    )
    possible_variants: List[str] = Field(
        default_factory=list,
        description="Variant IDs that match resolved attributes"
    )

    # Query Context
    original_query: str = Field(
        ...,
        description="Original user query text"
    )
    current_query: str = Field(
        ...,
        description="Current query with accumulated context"
    )
    detected_attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attributes detected from user input"
    )

    # Confidence & Validation
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall classification confidence"
    )
    requires_human_intervention: bool = Field(
        default=False,
        description="Flag for edge cases needing human help"
    )

    class Config:
        frozen = True
```

---

## Query Flow Design with PIM Tool Integration

### Scenario 1: Multi-Turn Conversation with PIM Tool Orchestration

```text
graph TD
    A[User: "ada besi hollow?"] --> B[Pydantic AI Agent]
    B --> C{Analyze Query}
    C --> D[Detect: product_category=besi hollow]
    D --> E[PIM Tool: search_products('besi hollow')]
    E --> F[PIM Returns: Product variants with different materials]
    F --> G[QueryIntent: Build clarification_stage=narrowing]
    G --> H[Agent: "Kami ada besi hollow hitam dan galvanis.<br/>Manakah yang anda cari?"]

    H --> I[User: "besi hollow hitam"]
    I --> J[Update Context: material=hitam]
    J --> K[PIM Tool: get_variant_attributes(product='besi hollow', material='hitam')]
    K --> L[PIM Returns: Available dimensions list]
    L --> M[QueryIntent: next_clarification=dimensions]
    M --> N[Agent: "Kami ada beragam ukuran besi hollow hitam<br/>dari 20x20 sampai 200x200.<br/>Ukuran berapa yang anda cari?"]

    N --> O[User: "40x40"]
    O --> P[Update Context: dimensions=40x40]
    P --> Q[PIM Tool: get_variant_by_attributes(material='hitam', dimensions='40x40')]
    Q --> R[PIM Returns: Specific variant details]
    R --> S[QueryIntent: clarification_stage=complete]
    S --> T[Agent: "Besi hollow hitam 40x40 tersedia<br/>Stock: 50 lembar<br/>Harga: Rp 750.000 per batang"]
```

### Scenario 2: Agent Decision Flow with PIM Tool Usage

```yaml
Turn 1 - Initial Query Processing:
  User Input: "ada besi hollow?"

  Agent Analysis:
    1. Parse query → detect product mention
    2. Check if specific variant attributes present → No
    3. Decision: Need to query PIM for available options

  PIM Tool Call:
    tool: search_products
    params: {query: "besi hollow"}
    returns:
      products: [
        {id: "PROD_HOLLOW", name: "Besi Hollow",
         variant_groups: {material: ["hitam", "galvanis"]}}
      ]

  QueryIntent State:
    clarification_stage: "narrowing"
    query_level: "product"
    detected_attributes: {product_category: "besi hollow"}
    next_clarification:
      attribute_type: "material"
      options: ["hitam", "galvanis"]  # From PIM response
      question_template: "Kami ada besi hollow {options}. Manakah yang anda cari?"

  Agent Response: "Kami ada besi hollow hitam dan galvanis. Manakah yang anda cari?"

Turn 2 - Material Clarification:
  User Input: "besi hollow hitam"

  Agent Analysis:
    1. Extract new attribute: material="hitam"
    2. Check if enough to identify variant → No
    3. Decision: Query PIM for next level options

  PIM Tool Call:
    tool: get_variant_options
    params: {product_id: "PROD_HOLLOW", filters: {material: "hitam"}}
    returns:
      attribute_options: {
        dimensions: ["20x20", "40x40", "50x50", "100x100", "200x200"],
        next_required: "dimensions"
      }

  QueryIntent State:
    clarification_stage: "narrowing"
    conversation_turn: 2
    resolved_attributes: {material: "hitam"}
    next_clarification:
      attribute_type: "dimensions"
      options: ["20x20", "40x40", "50x50", "100x100", "200x200"]  # From PIM
      depends_on: "material"

  Agent Response: "Kami ada beragam ukuran besi hollow hitam dari 20x20 sampai 200x200, ukuran berapa yang anda cari?"

Turn 3 - Final Selection:
  User Input: "40x40"

  Agent Analysis:
    1. Extract dimension: "40x40"
    2. Check if enough to identify variant → Yes
    3. Decision: Fetch specific variant details

  PIM Tool Call:
    tool: get_variant_by_attributes
    params: {
      product_id: "PROD_HOLLOW",
      attributes: {material: "hitam", dimensions: "40x40"}
    }
    returns:
      variant: {
        variant_id: "VAR_HOLLOW_BLACK_40X40",
        sku: "HOLLOW-BLACK-40X40",
        price: 750000,
        stock_quantity: 50,
        stock_unit: "batang"
      }

  QueryIntent State:
    clarification_stage: "complete"
    conversation_turn: 3
    resolved_attributes: {material: "hitam", dimensions: "40x40"}
    possible_variants: ["VAR_HOLLOW_BLACK_40X40"]
    next_action: "provide_info"
    response_data: {price: 750000, stock: 50, unit: "batang"}

  Agent Response: "Besi hollow hitam 40x40 tersedia dengan stock 50 batang, harga Rp 750.000 per batang"
```

### Scenario 3: PIM Tool Decision Logic

```python
# Agent's internal decision logic for PIM tool usage

def determine_pim_action(query_intent: QueryIntent) -> PIMAction:
    """
    Determines which PIM tool to call based on current conversation state
    """
    if query_intent.clarification_stage == "initial":
        # First query - search for products
        return PIMAction(
            tool="search_products",
            params={"query": query_intent.detected_attributes.get("product_category")}
        )

    elif query_intent.clarification_stage == "narrowing":
        # Need more attributes - get available options
        if len(query_intent.conversation_context.resolved_attributes) == 0:
            # No attributes resolved yet - get first level options
            return PIMAction(
                tool="get_product_attributes",
                params={"product_id": query_intent.matched_products[0]}
            )
        else:
            # Some attributes resolved - get next level options
            return PIMAction(
                tool="get_variant_options",
                params={
                    "product_id": query_intent.matched_products[0],
                    "filters": query_intent.conversation_context.resolved_attributes
                }
            )

    elif query_intent.clarification_stage == "confirming":
        # Almost complete - validate selection
        return PIMAction(
            tool="validate_variant_exists",
            params={"attributes": query_intent.conversation_context.resolved_attributes}
        )

    elif query_intent.clarification_stage == "complete":
        # All attributes resolved - get full details
        return PIMAction(
            tool="get_variant_by_attributes",
            params={"attributes": query_intent.conversation_context.resolved_attributes}
        )
```

---

## PIM Tool Integration for Pydantic AI Agent

### PIM Tool Functions

The Pydantic AI agent will have access to these PIM tool functions:

```python
# src/application/tools/pim_tools.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class PIMTools:
    """Tools for Pydantic AI agent to query PIM system"""

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for products matching the query.
        Returns product info with available variant groups.
        """
        # Returns: [{id, name, variant_groups: {attribute: [options]}}]
        pass

    async def get_product_attributes(self, product_id: str) -> Dict[str, List[str]]:
        """
        Get all available attributes and their options for a product.
        Used for initial clarification options.
        """
        # Returns: {material: ["hitam", "galvanis"], dimensions: [...]}
        pass

    async def get_variant_options(
        self,
        product_id: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get next level options based on already resolved attributes.
        Respects attribute dependencies.
        """
        # Returns: {attribute_options: {...}, next_required: "dimension"}
        pass

    async def get_variant_by_attributes(
        self,
        attributes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch specific variant when all required attributes are resolved.
        """
        # Returns: {variant_id, sku, price, stock_quantity, stock_unit}
        pass

    async def validate_variant_exists(
        self,
        attributes: Dict[str, Any]
    ) -> bool:
        """
        Check if a variant exists with given attributes.
        Used before final confirmation.
        """
        pass

    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get similar products when exact match not found.
        Used for alternative suggestions.
        """
        pass
```

### Agent Orchestration Pattern

```python
# src/application/services/conversational_agent.py

class ConversationalAgent:
    """
    Pydantic AI agent orchestrating between ChatGPT 4o mini and PIM tools
    """

    def __init__(self, pim_tools: PIMTools, llm_client):
        self.pim_tools = pim_tools
        self.llm = llm_client
        self.cache = {}  # Cache PIM responses

    async def process_query(
        self,
        user_input: str,
        conversation_context: Optional[ConversationContext] = None
    ) -> QueryIntent:
        """
        Main orchestration logic
        """
        # Step 1: LLM analyzes user input
        detected_attributes = await self.llm.extract_attributes(
            user_input,
            conversation_context
        )

        # Step 2: Determine what PIM data is needed
        if not conversation_context:  # Initial query
            # Search for products
            products = await self._cached_call(
                self.pim_tools.search_products,
                detected_attributes.get("product_category", "")
            )

            # Get first-level options
            if products:
                options = await self.pim_tools.get_product_attributes(
                    products[0]["id"]
                )

                # Build initial QueryIntent with clarification
                return self._build_clarification_intent(
                    products, options, detected_attributes
                )

        else:  # Ongoing conversation
            # Update resolved attributes
            updated_context = self._update_context(
                conversation_context,
                detected_attributes
            )

            # Check if we have enough to identify variant
            if self._is_variant_identifiable(updated_context):
                # Fetch specific variant
                variant = await self.pim_tools.get_variant_by_attributes(
                    updated_context.resolved_attributes
                )
                return self._build_complete_intent(variant, updated_context)

            else:
                # Get next options based on current state
                next_options = await self.pim_tools.get_variant_options(
                    updated_context.matched_products[0],
                    updated_context.resolved_attributes
                )
                return self._build_narrowing_intent(
                    next_options, updated_context
                )

    async def _cached_call(self, func, *args, **kwargs):
        """Cache PIM responses to avoid redundant calls"""
        cache_key = f"{func.__name__}:{args}:{kwargs}"
        if cache_key not in self.cache:
            self.cache[cache_key] = await func(*args, **kwargs)
        return self.cache[cache_key]
```

### Caching Strategy

```yaml
Cache Levels:
  Product Search:
    TTL: 1 hour
    Key: "search:{query}"
    Rationale: Product catalog changes infrequently

  Attribute Options:
    TTL: 30 minutes
    Key: "attributes:{product_id}:{resolved_attrs}"
    Rationale: Options may change with stock updates

  Variant Details:
    TTL: 5 minutes
    Key: "variant:{attributes}"
    Rationale: Stock and price need fresher data

  Session Cache:
    TTL: Conversation duration
    Scope: Per user session
    Purpose: Avoid redundant calls within same conversation
```

### Error Handling Patterns

```python
class PIMErrorHandler:
    """Handle PIM tool failures gracefully"""

    async def handle_pim_error(
        self,
        error: Exception,
        query_intent: QueryIntent
    ) -> QueryIntent:
        """
        Graceful degradation when PIM is unavailable
        """
        if isinstance(error, PIMConnectionError):
            # Use cached data if available
            return self._fallback_to_cache(query_intent)

        elif isinstance(error, ProductNotFoundError):
            # Suggest alternatives
            query_intent.next_action = "suggest_alternatives"
            query_intent.suggested_response = (
                "Maaf, produk tersebut tidak ditemukan. "
                "Mungkin Anda mencari produk serupa?"
            )
            return query_intent

        elif isinstance(error, AttributeNotAvailableError):
            # Skip to next available attribute
            return self._skip_attribute(query_intent)

        else:
            # Flag for human intervention
            query_intent.requires_human_intervention = True
            return query_intent
```

---

## Implementation Strategy

### Phase 1: Value Object Creation (Week 1)

1. **Create New Value Objects**
   - [ ] Implement `VariantInfo` value object
   - [ ] Refactor `ProductInfo` to product-level only
   - [ ] Implement `ProductWithVariantsInfo` aggregate
   - [ ] Enhance `QueryIntent` with query_level

2. **Testing**
   - [ ] Unit tests for each value object
   - [ ] Validation tests for business rules
   - [ ] Serialization/deserialization tests

### Phase 2: Repository Pattern Update (Week 1-2)

```python
# src/domain/repositories/product_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from ..value_objects import ProductInfo, VariantInfo, ProductWithVariantsInfo

class ProductRepository(ABC):
    """
    Abstract repository for product/variant queries.
    Read-only operations against PIM system.
    """

    @abstractmethod
    async def get_product_with_variants(self, product_id: str) -> Optional[ProductWithVariantsInfo]:
        """Fetch product with all its variants"""
        pass

    @abstractmethod
    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Fetch specific variant by SKU"""
        pass

    @abstractmethod
    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search products by name or description"""
        pass

    @abstractmethod
    async def get_variants_by_product(self, product_id: str) -> List[VariantInfo]:
        """Fetch all variants for a product"""
        pass
```

### Phase 3: Service Layer Adaptation (Week 2)

```python
# src/application/services/product_inquiry_service.py

class ProductInquiryService:
    """
    Application service for handling product/variant inquiries.
    Orchestrates between query intent and appropriate data fetching.
    """

    async def handle_product_query(self, intent: QueryIntent) -> InquiryResponse:
        """
        Route query based on intent classification.
        Returns either single variant or product with options.
        """
        if intent.query_level == "variant" and intent.sku:
            variant = await self.repo.get_variant_by_sku(intent.sku)
            return self._format_variant_response(variant)

        elif intent.query_level == "product":
            product_with_variants = await self.repo.get_product_with_variants(
                product_id=self._resolve_product_id(intent.product_name)
            )

            if len(product_with_variants.variants) == 1:
                # Single variant, return directly
                return self._format_variant_response(product_with_variants.variants[0])
            else:
                # Multiple variants, present options
                return self._format_selection_response(product_with_variants)

        return self._format_clarification_request(intent)
```

### Phase 4: Migration Strategy (Week 2-3)

1. **Backward Compatibility**
   - Keep old `ProductInfo` temporarily with deprecation warning
   - Create adapter to convert old format to new `VariantInfo`

2. **Data Migration**
   ```python
   # src/infrastructure/adapters/legacy_adapter.py

   def convert_legacy_product_info(old: LegacyProductInfo) -> VariantInfo:
       """Convert old ProductInfo to new VariantInfo format"""
       return VariantInfo(
           variant_id=f"var_{old.sku}",  # Generate if not available
           sku=old.sku,
           variant_name=old.name,
           price=Decimal(str(old.price)),
           stock_quantity=old.stock,
           product_id="unknown",  # Will need to resolve from PIM
           specifications=old.specifications
       )
   ```

3. **Gradual Rollout**
   - Feature flag for new domain model
   - A/B testing with subset of queries
   - Monitor and validate responses

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/domain/value_objects/test_variant_info.py

def test_variant_info_creation():
    """Test VariantInfo instantiation with valid data"""
    variant = VariantInfo(
        variant_id="var_123",
        sku="PLT-5MM-001",
        product_id="prod_plat_baja",
        variant_name="Plat Baja 5mm x 1200mm x 2400mm",
        price=Decimal("500000"),
        stock_quantity=25,
        specifications={
            "thickness": "5mm",
            "width": "1200mm",
            "length": "2400mm",
            "grade": "SS400"
        }
    )
    assert variant.sku == "PLT-5MM-001"
    assert variant.price == Decimal("500000")

def test_product_with_variants_aggregation():
    """Test ProductWithVariantsInfo aggregate calculations"""
    product_with_variants = ProductWithVariantsInfo(
        product=ProductInfo(...),
        variants=[variant1, variant2, variant3]
    )
    assert product_with_variants.total_stock == 75
    assert product_with_variants.price_range == (Decimal("300000"), Decimal("850000"))
```

### Integration Tests

```python
# tests/integration/test_product_variant_flow.py

async def test_product_query_returns_all_variants():
    """Test that product query returns all variants for selection"""
    intent = QueryIntent(
        type="product_inquiry",
        query_level="product",
        product_name="plat baja"
    )

    response = await product_service.handle_product_query(intent)

    assert response.requires_selection == True
    assert len(response.variant_options) > 1
    assert all(v.product_id == "prod_plat_baja" for v in response.variant_options)
```

---

## Success Metrics

1. **Query Accuracy**
   - 95%+ correct classification of product vs variant queries
   - <2% queries requiring manual clarification

2. **User Experience**
   - Clear variant selection when querying products
   - Direct response for SKU-specific queries
   - Reduced conversation turns to get desired information

3. **Performance**
   - <100ms for query intent classification
   - <500ms for product with variants fetching
   - Efficient caching of product-variant relationships

---

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|-------------------|
| PIM API changes | High | Abstract repository pattern, versioned API contracts |
| Performance degradation | Medium | Redis caching, batch variant fetching |
| Backward compatibility | Medium | Adapter pattern, feature flags, gradual rollout |
| Data inconsistency | Low | Read-only model, PIM as single source of truth |

---

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Value Objects | New domain models, unit tests |
| 1-2 | Repository | Repository interfaces, PIM integration |
| 2 | Service Layer | Query routing, response formatting |
| 2-3 | Migration | Adapters, feature flags, rollout |
| 3 | Testing | Integration tests, performance validation |

---

## DDD Architecture for AI Agent Integration

### Layer Placement

```yaml
application_layer:
  primary_components:
    - AI Agent Orchestrator
    - Query Intent Analyzer
    - Conversation Flow Manager
    - PIM Tool Decision Logic

  responsibilities:
    - Coordinate between user input and domain logic
    - Manage multi-turn conversation state
    - Decide when to call PIM tools
    - Transform AI responses to domain events

infrastructure_layer:
  external_integrations:
    - ChatGPT 4o-mini Client
    - PIM API Client (PERKY OS)
    - Pydantic AI Configuration
    - Redis Cache Manager

  responsibilities:
    - Handle external API communication
    - Manage authentication and rate limiting
    - Cache external responses
    - Provide adapters to domain interfaces

domain_layer:
  pure_business_logic:
    - Clarification Rules Engine
    - Product-Variant Relationship Rules
    - Query Intent Classification Logic
    - Business Validation Rules

  responsibilities:
    - Define when clarification is needed
    - Determine variant selection rules
    - Maintain business invariants
    - No external dependencies
```

### Implementation Structure

```python
# src/application/services/ai_agent_orchestrator.py
class AIAgentOrchestrator:
    def __init__(
        self,
        ai_client: AIClient,
        pim_service: PIMService,
        intent_analyzer: IntentAnalyzer,
        conversation_manager: ConversationManager
    ):
        self.ai_client = ai_client
        self.pim_service = pim_service
        self.intent_analyzer = intent_analyzer
        self.conversation_manager = conversation_manager

    async def handle_user_query(
        self,
        user_input: str,
        conversation_id: str
    ) -> QueryResponse:
        context = await self.conversation_manager.get_context(conversation_id)
        intent = await self.intent_analyzer.analyze(user_input, context)

        if intent.needs_pim_data:
            pim_data = await self._fetch_pim_data(intent)
            intent = self._enrich_intent_with_pim(intent, pim_data)

        if intent.needs_clarification:
            return await self._request_clarification(intent, context)

        return await self._generate_response(intent, context)

    async def _fetch_pim_data(self, intent: QueryIntent) -> PIMData:
        if intent.query_level == "product":
            return await self.pim_service.get_product_variants(intent.product_name)
        elif intent.sku:
            return await self.pim_service.get_variant_by_sku(intent.sku)
        else:
            return await self.pim_service.search_products(intent.raw_query)

# src/infrastructure/ai/pydantic_agent.py
class PydanticAIClient:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.model = "gpt-4o-mini"

    async def analyze_intent(
        self,
        user_input: str,
        context: ConversationContext
    ) -> QueryIntent:
        prompt = self._build_intent_prompt(user_input, context)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            response_format=QueryIntent
        )
        return QueryIntent.model_validate(response.choices[0].message.parsed)

# src/domain/services/clarification_rules.py
class ClarificationRulesEngine:
    @staticmethod
    def determine_needed_clarifications(
        intent: QueryIntent,
        available_options: List[Any]
    ) -> List[ClarificationNeeded]:
        clarifications = []

        if intent.product_name and not intent.material:
            if ClarificationRulesEngine._has_multiple_materials(available_options):
                clarifications.append(
                    ClarificationNeeded(
                        attribute="material",
                        reason="multiple_options",
                        options=ClarificationRulesEngine._extract_materials(available_options)
                    )
                )

        if intent.material and not intent.dimensions:
            if ClarificationRulesEngine._has_multiple_dimensions(available_options):
                clarifications.append(
                    ClarificationNeeded(
                        attribute="dimensions",
                        reason="multiple_options",
                        options=ClarificationRulesEngine._extract_dimensions(available_options)
                    )
                )

        return clarifications
```

### Anti-Patterns to Avoid

```yaml
avoid_these_patterns:
  domain_layer_violations:
    - Calling external APIs directly from domain
    - Importing infrastructure code
    - Using framework-specific annotations

  application_layer_violations:
    - Complex business logic (belongs in domain)
    - Direct database access (use repositories)
    - UI formatting (belongs in presentation)

  infrastructure_layer_violations:
    - Business rules (belongs in domain)
    - Orchestration logic (belongs in application)
    - Domain object creation (use factories)
```

---

## Appendix A: Example Responses

### Product Query Response

```json
{
  "query_type": "product_inquiry",
  "product": {
    "product_id": "prod_plat_baja",
    "product_name": "Plat Baja"
  },
  "message": "Produk Plat Baja tersedia dalam beberapa varian. Silakan pilih:",
  "variants": [
    {
      "variant_id": "var_001",
      "sku": "PLT-5MM-001",
      "variant_name": "Plat Baja 5mm x 1200mm x 2400mm",
      "price": 500000,
      "stock": 25
    },
    {
      "variant_id": "var_002",
      "sku": "PLT-10MM-001",
      "variant_name": "Plat Baja 10mm x 1200mm x 2400mm",
      "price": 850000,
      "stock": 15
    }
  ],
  "requires_selection": true
}
```

### Variant Query Response

```json
{
  "query_type": "variant_inquiry",
  "variant": {
    "variant_id": "var_001",
    "sku": "PLT-5MM-001",
    "variant_name": "Plat Baja 5mm x 1200mm x 2400mm",
    "price": 500000,
    "stock": 25,
    "specifications": {
      "thickness": "5mm",
      "dimensions": "1200mm x 2400mm",
      "grade": "SS400"
    }
  },
  "message": "SKU PLT-5MM-001 tersedia dengan stock 25 lembar, harga Rp 500.000 per lembar",
  "requires_selection": false
}
```

---

## Appendix B: Domain Glossary

| Term | Definition |
|------|------------|
| **Product** | A category of items (e.g., "Plat Baja") that groups related variants |
| **Variant** | A specific sellable configuration of a product with unique SKU |
| **SKU** | Stock Keeping Unit - unique identifier for inventory management |
| **PIM** | Product Information Management system (PERKY OS) |
| **Query Intent** | Classification of user's question to determine response strategy |
| **Value Object** | Immutable domain object representing descriptive aspects |

---

## Document Version

- **Version**: 1.0.0
- **Date**: 2025-09-11
- **Author**: System Architect
- **Status**: Draft for Review
- **Next Review**: After Phase 1 completion
