# PydanticAI Architecture Guide

## Overview

This guide provides an in-depth technical explanation of how PydanticAI powers the
Perky AI Assistant chat application, enabling intelligent, tool-enabled conversations
for Indonesian B2B steel product assistance.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Agent System](#agent-system)
4. [Tool System](#tool-system)
5. [Message Flow](#message-flow)
6. [Domain Integration](#domain-integration)
7. [Error Handling](#error-handling)
8. [Performance Optimizations](#performance-optimizations)
9. [Best Practices](#best-practices)

## Architecture Overview

### High-Level Flow

```text
User Message → ChatOrchestrator → ProcessUserMessage UseCase
→ ChatAgent (PydanticAI) → LLM + Tools → Response
```

The application uses **PydanticAI** as the core AI orchestration framework,
providing a type-safe, tool-enabled conversational AI system. PydanticAI acts as
the bridge between user messages and intelligent responses, with the ability to
call specialized tools for product information retrieval.

### Key Design Principles

1. **Type Safety**: All tool inputs/outputs use Pydantic models
2. **Clean Architecture**: Dependencies flow inward via interfaces
3. **Domain-Driven Design**: Business logic encoded in system prompts
4. **Testability**: Dependency injection enables comprehensive mocking
5. **Resilience**: Multi-layer error handling with graceful degradation

## Core Components

### 1. ChatAgent (`src/infrastructure/ai/chat_agent.py`)

The main PydanticAI agent implementation that orchestrates AI interactions.

**Initialization:**

```python
model = OpenAIChatModel("gpt-4o-mini")
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    deps_type=ChatDependencies,
    retries=2,
)
```

**Key Attributes:**

- **Model**: `OpenAIChatModel` with GPT-4o-mini for cost-effective inference
- **System Prompt**: 300+ line Indonesian prompt encoding business rules
- **Dependencies**: Type-safe `ChatDependencies` dataclass
- **Retry Logic**: Built-in retry mechanism for API resilience

### 2. ChatDependencies

Runtime dependencies injected into tool execution context.

```python
@dataclass
class ChatDependencies:
    product_service: ProductServicePort  # Domain service interface
    session_id: str                      # Session tracking
    user_metadata: Optional[Dict[str, Any]] = None
```

**Benefits:**

- Clean architecture compliance (depends on interfaces, not implementations)
- Easy testing (inject mocks)
- Session isolation (per-conversation dependencies)

### 3. ChatOrchestrator (`src/application/services/chat_orchestrator.py`)

Coordinates use cases and provides single entry point for presentation layer.

**Responsibilities:**

- Session lifecycle management
- Message processing coordination
- Conversation history retrieval
- Error handling and fallback responses
- Logfire observability integration

## Agent System

### Agent Configuration

**Model Selection:**

```python
# Uses OpenAIChatModel (not deprecated OpenAIModel)
from pydantic_ai.models.openai import OpenAIChatModel

model = OpenAIChatModel("gpt-4o-mini")
```

**API Key Management:**

```python
# Environment variable with explicit override support
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OpenAI API key is required")
```

**Agent Creation:**

```python
agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,  # 300+ line business logic
    deps_type=ChatDependencies,   # Type-safe dependencies
    retries=2,                    # Automatic retry for failures
)
```

### System Prompt Architecture

The system prompt is a critical component that encodes:

1. **Agent Identity**: PERKY assistant for SMS Perkasa Steel
2. **Personality Traits**: Professional, helpful, proactive
3. **Domain Model**: Product-Variant hierarchy understanding
4. **Tool Usage Guidelines**: When and how to use each tool
5. **Communication Templates**: Structured Indonesian responses
6. **Error Handling Instructions**: Fallback behavior specification

**Key Domain Concept Encoding:**

```text
KONSEP PRODUK PENTING:
1. PRODUK adalah kategori umum (contoh: "Plat Baja", "Hollow", "H-Beam")
2. VARIAN adalah item spesifik yang dijual dengan SKU, harga, dan stok
3. Harga dan stok SELALU ada di level varian, BUKAN di level produk
4. Satu produk bisa memiliki banyak varian dengan ukuran/spesifikasi berbeda
```

This prevents the LLM from:

- Asking for "price of Plat Baja" (category has no price)
- Checking stock at product level
- Confusing categories with sellable items

## Tool System

PydanticAI tools enable the agent to fetch real-time product data from external
services. The application implements **five specialized tools**.

### Tool Registration Pattern

```python
def _register_tools(self):
    @self.agent.tool  # Decorator registers at runtime
    async def search_products(
        ctx: RunContext[ChatDependencies],
        query: str
    ) -> ProductSearchResult:
        """Docstring becomes AI-visible tool description"""
        return await self._search_products_tool(ctx, query)
```

**Important Implementation Detail:**

- Decorated functions are **dynamically invoked** by PydanticAI framework
- IDE "not accessed" warnings are **false positives**
- Tool docstrings become LLM-visible descriptions for intelligent selection
- Functions are called by the framework, not directly by application code

### Available Tools

#### 1. search_products

**Purpose**: Category-level product search

**Returns**: Product categories (e.g., "Plat Baja", "H-Beam")

**Usage**: Entry point for product discovery

```python
@agent.tool
async def search_products(
    ctx: RunContext[ChatDependencies],
    query: str
) -> ProductSearchResult:
    """Search for steel product categories based on query."""
    products = await ctx.deps.product_service.search_products(query)
    # Returns ProductSearchResult with found categories
```

#### 2. get_product_variants

**Purpose**: Variant enumeration for a product category

**Returns**: All sellable items under a product category

**Usage**: After finding a category, list all specific items

```python
@agent.tool
async def get_product_variants(
    ctx: RunContext[ChatDependencies],
    product_id: str
) -> VariantSearchResult:
    """Get all variants for a specific product category."""
    # Returns variants with price ranges and total stock
```

#### 3. get_variant_details

**Purpose**: Detailed information for specific variant

**Returns**: Complete variant details (price, stock, specifications)

**Usage**: When customer wants specific item information

```python
@agent.tool
async def get_variant_details(
    ctx: RunContext[ChatDependencies],
    product_id: str,
    variant_id: str
) -> VariantDetails:
    """Get detailed information about a specific variant."""
    # Returns VariantDetails with formatted messages
```

#### 4. check_variant_stock

**Purpose**: Batch stock verification

**Returns**: Stock status for multiple variants

**Usage**: Real-time availability checking

```python
@agent.tool
async def check_variant_stock(
    ctx: RunContext[ChatDependencies],
    product_id: str,
    variant_ids: List[str]
) -> StockCheckResult:
    """Check stock availability for specific variants."""
    # Returns current stock levels
```

#### 5. find_variants_by_specification

**Purpose**: Specification-based filtering

**Returns**: Variants matching specific attributes

**Usage**: Find items by technical specs (thickness, dimensions)

```python
@agent.tool
async def find_variants_by_specification(
    ctx: RunContext[ChatDependencies],
    product_id: str,
    specifications: Dict[str, Any]
) -> VariantSearchResult:
    """Find variants that match specific specifications."""
    # Returns matching variants with pricing/stock
```

### Tool Response Enhancement

Tools return **pre-formatted Indonesian messages** for consistency:

```python
# Example from get_variant_details
specs = variant.specifications.copy()
specs["_formatted_stock"] = self._format_stock_message(variant)
specs["_formatted_price"] = self._format_price_message(variant)

return VariantDetails(
    variant_id=variant.variant_id,
    specifications=specs,  # Contains formatted messages
    # ...
)
```

**Template System:**

```python
def _format_stock_message(self, variant: Any) -> str:
    """Format stock information using templates."""
    if not variant.has_stock():
        return STOCK_MESSAGES["out_of_stock"].format(
            variant_name=variant.variant_name
        )
    elif variant.stock_quantity <= 10:
        return STOCK_MESSAGES["low_stock"].format(
            variant_name=variant.variant_name,
            stock_quantity=variant.stock_quantity,
            stock_unit=variant.stock_unit,
        )
    # ... etc
```

This ensures:

- Professional, consistent communication
- Correct price formatting (Indonesian Rupiah)
- Appropriate stock status messages
- LLM uses pre-formatted strings verbatim

## Message Flow

### Complete Request Cycle

1. **WebSocket receives message** → `ChatOrchestrator.handle_user_message()`
2. **Orchestrator delegates** → `ProcessUserMessageUseCase.execute()`
3. **Use case prepares context** → Fetches conversation history from repository
4. **ChatAgent invoked** → `generate_response()` with full context
5. **PydanticAI agent.run()** → LLM analyzes message + history + system prompt
6. **Tool selection** → LLM decides which tools to call (if any)
7. **Tool execution** → Async calls to product service via dependencies
8. **Response generation** → LLM synthesizes final response using tool results
9. **Response extraction** → `result.data` extracted and returned
10. **Persistence** → Response saved to conversation history
11. **WebSocket sends** → Response delivered to client

### Message History Management

**DTO to PydanticAI Conversion:**

```python
def _convert_dto_to_model_messages(
    self, conversation_context: List[MessageDTO]
) -> list[ModelMessage]:
    messages: list[ModelMessage] = []

    for msg in conversation_context[-10:]:  # Last 10 messages only
        if msg.sender_type == "user":
            messages.append(ModelRequest(
                parts=[UserPromptPart(
                    content=msg.content,
                    timestamp=msg.timestamp or datetime.now()
                )]
            ))
        else:  # ai_agent
            messages.append(ModelResponse(
                parts=[TextPart(content=msg.content)],
                timestamp=msg.timestamp or datetime.now()
            ))

    return messages
```

**Context Window Strategy:**

- Maintains last **10 messages** for context efficiency
- Converts domain DTOs to PydanticAI message format
- Preserves timestamps for temporal awareness
- Graceful degradation on malformed messages (skip, don't fail)

### Agent Execution

**Main Generate Response Method:**

```python
async def generate_response(
    self, message: str,
    conversation_context: Optional[List[MessageDTO]] = None,
    product_service: Optional[ProductServicePort] = None,
    session_id: Optional[str] = None
) -> str:
    # 1. Convert history to PydanticAI format
    message_history = None
    if conversation_context and len(conversation_context) > 0:
        message_history = self._convert_dto_to_model_messages(
            conversation_context
        )

    # 2. Prepare dependencies
    deps = ChatDependencies(
        product_service=product_service or self._create_mock_product_service(),
        session_id=session_id or "default",
        user_metadata={}
    )

    # 3. Execute agent with tools
    result = await self.agent.run(
        message,
        message_history=message_history,
        deps=deps
    )

    # 4. Extract response - CRITICAL: use .data not .output
    response_str: str = result.data if hasattr(result, 'data') else str(result)
    return response_str
```

**⚠️ Critical Implementation Note:**

```python
# WRONG - causes AttributeError
response = result.output  # ❌ Attribute doesn't exist

# CORRECT
response = result.data    # ✅ Proper extraction method
```

This was a discovered bug pattern documented in project memories. The PydanticAI
`AgentRunResult` object exposes results via `.data`, not `.output`.

## Domain Integration

### Product-Variant Hierarchy

The system implements a clear domain model:

- **Products**: Categories like "Plat Baja", "Hollow", "H-Beam"
- **Variants**: Specific sellable items with SKU, price, stock
- **Key Rule**: Prices and stock ONLY exist at variant level

**Domain Model Teaching:**

The system prompt explicitly teaches the LLM:

```text
1. PRODUK adalah kategori umum (contoh: "Plat Baja", "Hollow", "H-Beam")
2. VARIAN adalah item spesifik yang dijual dengan SKU, harga, dan stok
   (contoh: "Plat Baja 5mm x 1200mm x 2400mm" adalah varian dari produk "Plat Baja")
3. Harga dan stok SELALU ada di level varian, BUKAN di level produk
4. Satu produk bisa memiliki banyak varian dengan ukuran/spesifikasi berbeda
```

### Clean Architecture Compliance

**Port-Adapter Pattern:**

```python
# Domain Port (Interface)
class ProductServicePort(ABC):
    @abstractmethod
    async def search_products(self, query: str) -> List[ProductInfo]:
        pass

# Infrastructure Adapter (Implementation)
class HTTPProductService(ProductServicePort):
    async def search_products(self, query: str) -> List[ProductInfo]:
        # HTTP call to external PIM system
        pass

# ChatAgent depends on Port, not Adapter
deps = ChatDependencies(
    product_service=product_service,  # Interface type
    # ...
)
```

**Benefits:**

- Tools independent of external service implementation
- Easy to swap external services (HTTP → GraphQL → gRPC)
- Comprehensive testing with mock implementations

## Error Handling

### Multi-Layer Error Strategy

#### 1. Tool Level - Structured Error States

```python
async def _search_products_tool(
    self, ctx: RunContext[ChatDependencies], query: str
) -> ProductSearchResult:
    try:
        products = await ctx.deps.product_service.search_products(query)
        # ... success path
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return ProductSearchResult(
            products=[],
            query=query,
            count=0,
            success=False,
            message=f"Error searching products: {str(e)}"
        )
```

Tools return error states as structured data, allowing the LLM to handle
gracefully.

#### 2. Agent Level - Template-Based Fallback

```python
async def generate_response(...) -> str:
    try:
        result = await self.agent.run(...)
        return result.data
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        return ERROR_MESSAGES["system_error"]  # Indonesian template
```

Agent uses predefined Indonesian error messages from templates.

#### 3. Orchestrator Level - User-Friendly Messages

```python
async def handle_user_message(...) -> MessageDTO:
    try:
        response = await self.process_message.execute(...)
        return response
    except Exception as e:
        logfire.error("Message processing failed", error=str(e))
        return MessageDTO(
            content="Maaf, terjadi kesalahan. Silakan coba lagi.",
            sender_type="ai_agent",
            metadata={"error": str(e), "error_type": "orchestration_error"}
        )
```

Orchestrator ensures users always receive graceful error messages in Indonesian.

### Error Message Templates

**From `src/infrastructure/ai/prompts/indonesian_templates.py`:**

```python
ERROR_MESSAGES = {
    "variant_not_found": "Mohon maaf, {variant_spec} untuk {product_name} tidak ditemukan.",
    "system_error": "Maaf, saya mengalami kendala teknis. Silakan hubungi tim sales kami.",
}
```

Templates ensure:

- Consistent error communication
- Professional Indonesian language
- User-actionable messages
- No technical jargon exposure

## Performance Optimizations

### 1. Context Window Limiting

**Problem**: Long conversations can exceed token limits and increase costs.

**Solution**: Maintain only last 10 messages

```python
for msg in conversation_context[-10:]:  # Last 10 only
    # Convert to PydanticAI format
```

**Benefits:**

- Prevents token bloat in extended conversations
- Maintains relevance (recent context more important)
- Controls API costs
- Improves response latency

### 2. Retry Configuration

**Problem**: Transient API failures can disrupt conversations.

**Solution**: Built-in retry mechanism

```python
agent = Agent(
    model=model,
    retries=2,  # Automatic retry for failures
    # ...
)
```

**Benefits:**

- Handles transient network issues
- Improves reliability
- Transparent to users
- No application-level retry logic needed

### 3. Template Pre-Formatting

**Problem**: LLM regenerating similar messages increases costs.

**Solution**: Pre-format common responses in tools

```python
# Tool pre-formats messages
specs["_formatted_stock"] = self._format_stock_message(variant)
specs["_formatted_price"] = self._format_price_message(variant)

# LLM uses pre-formatted strings directly
# Reduces generation complexity and token usage
```

**Benefits:**

- Consistent formatting without LLM involvement
- Reduced token generation costs
- Faster response times
- Guaranteed professional quality

### 4. Async Throughout

**Implementation**: All I/O operations are async

```python
async def generate_response(...) -> str:
    # Async tool calls
    products = await ctx.deps.product_service.search_products(query)

    # Async agent execution
    result = await self.agent.run(...)

    # Async use case execution
    response = await self.process_message.execute(...)
```

**Benefits:**

- Non-blocking I/O operations
- Concurrent request handling
- Optimal resource utilization
- Improved scalability

## Best Practices

### ✅ Do's

1. **Use Dependency Injection**

   ```python
   # Inject dependencies, never hardcode
   deps = ChatDependencies(
       product_service=product_service,  # Injected
       session_id=session_id
   )
   ```

2. **Fetch Data Dynamically via Tools**

   ```python
   # Never hardcode product data in prompts
   @agent.tool
   async def search_products(...):
       return await ctx.deps.product_service.search_products(query)
   ```

3. **Use Template Messages**

   ```python
   # Pre-format for consistency
   specs["_formatted_stock"] = self._format_stock_message(variant)
   ```

4. **Encode Domain Rules in System Prompt**

   ```text
   Harga dan stok SELALU ada di level varian, BUKAN di level produk
   ```

5. **Return Structured Error States**

   ```python
   return ProductSearchResult(
       success=False,
       message="Error description"
   )
   ```

### ❌ Don'ts

1. **Don't Use Wrong Result Attribute**

   ```python
   response = result.output  # ❌ AttributeError
   response = result.data    # ✅ Correct
   ```

2. **Don't Ignore Tool Registration Warnings**

   ```python
   # IDE says "function not accessed" - this is FALSE POSITIVE
   @self.agent.tool  # ← This IS accessed at runtime by PydanticAI
   async def my_tool(...):
       pass
   ```

3. **Don't Hardcode Product Data**

   ```python
   # ❌ Wrong - data becomes stale
   SYSTEM_PROMPT = "We sell: Plat Baja (Rp 100.000), ..."

   # ✅ Correct - fetch dynamically
   @agent.tool
   async def search_products(...):
       return await product_service.search_products(...)
   ```

4. **Don't Test LLM Response Content**

   ```python
   # ❌ Wrong - LLM responses are non-deterministic
   assert response == "Halo! Saya PERKY..."

   # ✅ Correct - test our logic, not LLM output
   assert mock_agent.generate_response.called_with(message)
   ```

5. **Don't Violate Clean Architecture**

   ```python
   # ❌ Wrong - direct dependency on infrastructure
   from src.infrastructure.http.product_client import HTTPProductClient
   agent = ChatAgent(product_service=HTTPProductClient())

   # ✅ Correct - depend on interface
   from src.application.ports import ProductServicePort
   agent = ChatAgent(product_service=product_service)  # Interface type
   ```

### Testing Strategy

**What to Test:**

- ✅ Our code logic and business rules
- ✅ Error handling and fallback mechanisms
- ✅ Data transformation and formatting
- ✅ Configuration and initialization
- ✅ Tool parameter validation
- ✅ Message history conversion logic

**What NOT to Test:**

- ❌ Third-party library internals (PydanticAI, OpenAI)
- ❌ LLM response content (non-deterministic)
- ❌ Mock implementations of external services
- ❌ Tool registration mechanics (framework responsibility)

## Common Pitfalls & Solutions

### Pitfall 1: Wrong Result Extraction

**Problem:**

```python
response = result.output  # AttributeError: no 'output' attribute
```

**Solution:**

```python
response = result.data    # Correct attribute name
```

### Pitfall 2: Tool Not Being Called

**Problem**: LLM doesn't use tools even when needed.

**Solution**: Improve tool docstrings (LLM reads them)

```python
@agent.tool
async def search_products(
    ctx: RunContext[ChatDependencies],
    query: str
) -> ProductSearchResult:
    """Search for steel product categories based on query.

    This returns product categories (like "Plat Baja", "Hollow"),
    NOT specific variants. Use get_product_variants to see specific items.

    Args:
        ctx: Run context with dependencies
        query: Search query in Indonesian

    Returns:
        ProductSearchResult with found product categories
    """
```

### Pitfall 3: Context Window Overflow

**Problem**: Long conversations exceed token limits.

**Solution**: Limit message history

```python
for msg in conversation_context[-10:]:  # Last 10 only
    messages.append(...)
```

### Pitfall 4: LLM Confuses Products and Variants

**Problem**: LLM asks for "price of Plat Baja" (category has no price).

**Solution**: Explicitly teach domain model in system prompt

```text
KONSEP PRODUK PENTING:
1. PRODUK adalah kategori umum
2. VARIAN adalah item spesifik dengan harga dan stok
3. Harga dan stok SELALU ada di level varian, BUKAN di level produk
```

### Pitfall 5: Inconsistent Error Messages

**Problem**: Different error messages for same failure types.

**Solution**: Use centralized templates

```python
from src.infrastructure.ai.prompts.indonesian_templates import ERROR_MESSAGES

return ERROR_MESSAGES["system_error"]  # Consistent across all errors
```

## Monitoring & Observability

### Logfire Integration

The orchestrator layer integrates Logfire for comprehensive observability:

```python
with logfire.span(
    "chat_orchestrator.handle_user_message",
    session_id=session_id,
    message_length=len(content),
):
    response = await self.process_message.execute(...)

    logfire.info(
        "Message processed successfully",
        session_id=session_id,
        response_length=len(response.content),
        sender_type=response.sender_type,
    )
```

**Tracked Metrics:**

- Session lifecycle events
- Message processing duration
- Response generation success/failure
- Tool execution traces (via PydanticAI integration)
- Error types and frequencies

### Logging Strategy

**Application Level:**

```python
logger.info(f"Processing message from session {session_id}")
logger.debug(f"Message content: {content[:100]}...")  # Truncated
logger.error(f"Failed to process message: {e}", exc_info=True)
```

**Tool Level:**

```python
logger.error(f"Error searching products: {e}")  # Tool failures
logger.warning(f"Failed to convert message: {e}")  # Non-critical issues
```

## Future Enhancements

### Potential Improvements

1. **Streaming Responses**: Implement PydanticAI streaming for real-time output
2. **Advanced Context Management**: Summarization for very long conversations
3. **Multi-Modal Support**: Image inputs for product specifications
4. **Fine-Tuned Models**: Custom models trained on steel product domain
5. **Caching Layer**: Cache common queries (Redis integration)
6. **A/B Testing**: Multiple prompts/strategies for optimization
7. **Tool Chaining**: Complex multi-tool workflows
8. **Feedback Loop**: User ratings to improve responses

## Conclusion

PydanticAI provides a robust, type-safe foundation for the Perky AI Assistant,
enabling intelligent product assistance through:

- **Type-Safe Tool System**: Pydantic models prevent runtime errors
- **Domain-Aware Prompts**: Business logic encoded in system prompts
- **Clean Architecture**: Dependencies flow through interfaces
- **Comprehensive Error Handling**: Multi-layer fallback strategies
- **Performance Optimizations**: Context limiting, retries, pre-formatting
- **Observability**: Logfire integration for production monitoring

By following the patterns and best practices outlined in this guide, developers
can maintain and extend the chat system while preserving its reliability,
performance, and user experience.

## Additional Resources

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [Project Architecture Guide](../CLAUDE.md)
- [Domain Model Documentation](../src/domain/README.md)
- [Testing Guidelines](../tests/README.md)
- [API Documentation](../docs/api-documentation.md)
