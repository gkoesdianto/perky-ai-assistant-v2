# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Server

```bash
# Start the development server with hot reload
python -m uvicorn src.main:app --reload

# The API will be available at http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file or directory
pytest tests/unit/domain/
pytest tests/unit/domain/entities/test_session.py

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_product"
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Run linting
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks in sequence
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Environment Setup

```bash
# Activate virtual environment
source ~/.virtualenvs/perky-ai-assistant-v2/bin/activate

# Install development dependencies
pip install -r requirements/dev.txt

# Setup environment variables
cp .env.example .env
# Then edit .env with actual values
```

## Architecture

This application follows **Domain-Driven Design (DDD)** principles with clear separation of concerns:

### Layer Responsibilities

**Domain Layer** (`src/domain/`)
- Contains pure business logic and rules
- Entities inherit from `BaseEntity` (provides id, timestamps, is_active)
- Value Objects are immutable (frozen=True) data structures
- Repository interfaces define contracts for data access
- No dependencies on infrastructure or external libraries

**Application Layer** (`src/application/`)
- Orchestrates domain objects and infrastructure
- Contains use cases and application services
- DTOs for data transfer between layers
- Business workflow coordination

**Infrastructure Layer** (`src/infrastructure/`)
- External service integrations (PIM system via HTTP)
- Database access with SQLAlchemy async sessions
- Redis caching for sessions and product data
- Repository implementations

**Presentation Layer** (`src/presentation/`)
- FastAPI routers and endpoints
- Request/response schemas
- WebSocket handling for real-time chat
- Dependency injection setup

### Key Design Patterns

**Repository Pattern**: Abstract interfaces in domain layer, concrete implementations
in infrastructure. The `ProductRepository` is read-only,
fetching from external PIM system.

**Value Objects**: Immutable domain objects like `ProductInfo`, `VariantInfo`, and
 `ProductWithVariantsInfo` that encapsulate business logic
(price formatting, stock calculations).

**Entity Aggregates**: `Session` manages `Conversation` which contains `Message` entities, maintaining consistency boundaries.

**Async Throughout**: All database operations, external API calls, and repository methods are async for optimal performance.

### External Integrations

**PIM System (Perky OS)**: Product catalog data source accessed via HTTP API with
JWT authentication. Configuration in `PERKY_OS_*` environment variables.

**Redis**: Used for session management (TTL-based) and caching product/price data. Configured via `REDIS_URL` and TTL settings.

**OpenAI**: Integration via PydanticAI for natural language processing in
the chat assistant. Model and parameters configured in environment.

### Testing Strategy

Tests are organized by layer and type:
- `tests/unit/domain/` - Pure domain logic tests with factories for test data
- `tests/integration/` - Cross-layer integration tests
- All domain entities and value objects have comprehensive test coverage
- Test factories in `tests/unit/domain/factories.py` for consistent test data

### Configuration

Settings managed via Pydantic Settings in `src/core/config.py`:
- Database URL auto-assembled from components
- Validation for all configuration values
- Environment variables loaded from `.env` file
- Separate settings for security, API integration, WebSocket, and caching
