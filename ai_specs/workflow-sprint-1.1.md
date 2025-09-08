# Sprint 1.1: Project Setup Workflow

## Overview

Complete implementation guide for initializing a FastAPI project with Domain-Driven Design (DDD) architecture,
Docker environment, and database configurations.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL client tools
- Redis client tools
- Git

## Task 1: Initialize FastAPI Project with DDD Structure

### 1.1 Create Project Directory Structure

```bash
mkdir -p perky-ai-assistant-v2
cd perky-ai-assistant-v2

# Create DDD structure
mkdir -p src/{domain,application,infrastructure,presentation}
mkdir -p src/domain/{entities,value_objects,repositories,services}
mkdir -p src/application/{services,use_cases,dto}
mkdir -p src/infrastructure/{database,cache,external_services,repositories}
mkdir -p src/presentation/{api,schemas,dependencies}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts
mkdir -p migrations
mkdir -p docs
```

### 1.2 Initialize Python Project

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements files
touch requirements/base.txt
touch requirements/dev.txt
touch requirements/prod.txt
```

### 1.3 Install Core Dependencies

```text
# requirements/base.txt
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic==2.10.3
pydantic-settings==2.6.1
pydantic-ai==1.0.1
sqlalchemy==2.0.36
alembic==1.14.0
asyncpg==0.30.0
redis==5.2.0
python-multipart==0.0.7
python-jose[cryptography]==3.3.0
httpx==0.27.2
openai==1.57.0
```

```text
# requirements/dev.txt
-r base.txt
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
black==24.10.0
isort==5.13.2
flake8==7.1.1
mypy==1.13.0
pre-commit==4.0.1
```

### 1.4 Create Main Application File

```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.api import health, v1_router
from src.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(v1_router, prefix=settings.API_V1_STR)

    return app

app = create_app()
```

### 1.5 Create Configuration Module

```python
# src/core/config.py
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "Steel Chat API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS - Allow Svelte widget to connect
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None

    # Redis - For session management and caching
    REDIS_URL: RedisDsn
    REDIS_SESSION_TTL: int = 3600  # 1 hour
    REDIS_CACHE_TTL: int = 900  # 15 minutes for price/stock

    # PIM Integration
    PERKY_OS_API_URL: str = "https://api.perkyos.com/v1"
    PERKY_OS_JWT_SECRET: str
    PERKY_OS_TIMEOUT: int = 5000  # milliseconds

    # OpenAI for PydanticAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_RETRIES: int = 2

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    WS_MESSAGE_RATE_LIMIT: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Task 2: Setup Docker Development Environment

### Important Note on Authentication

This system uses **session-based anonymous chat** - no user authentication required:

- WebSocket sessions are tracked via `session_id`
- JWT is only used for PERKY OS API authentication (server-to-server)
- No user registration, login, or password management needed

### 2.1 Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/base.txt requirements/dev.txt ./requirements/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 2.2 Create Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  app:
    build: .
    container_name: perky-api
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_SERVER=postgres
      - POSTGRES_USER=perky_user
      - POSTGRES_PASSWORD=perky_password
      - POSTGRES_DB=perky_db
      - REDIS_URL=redis://redis:6379/0
      - PERKY_OS_API_URL=https://api.perkyos.com/v1
      - PERKY_OS_JWT_SECRET=${PERKY_OS_JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-4o-mini
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
      - ./migrations:/app/migrations
    depends_on:
      - postgres
      - redis
    networks:
      - perky-network

  postgres:
    image: postgres:16-alpine
    container_name: perky-postgres
    environment:
      - POSTGRES_USER=perky_user
      - POSTGRES_PASSWORD=perky_password
      - POSTGRES_DB=perky_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - perky-network

  redis:
    image: redis:7-alpine
    container_name: perky-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - perky-network

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: perky-pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@perky.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - perky-network

volumes:
  postgres_data:
  redis_data:

networks:
  perky-network:
    driver: bridge
```

### 2.3 Create Environment File

```env
# .env.example
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=perky_user
POSTGRES_PASSWORD=perky_password
POSTGRES_DB=perky_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_TTL=3600
REDIS_CACHE_TTL=900

# PIM Integration
PERKY_OS_API_URL=https://api.perkyos.com/v1
PERKY_OS_JWT_SECRET=your-pim-jwt-secret
PERKY_OS_TIMEOUT=5000

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100
WS_MESSAGE_RATE_LIMIT=10
```

## Task 3: Configure PostgreSQL and Redis Connections

### 3.1 Database Connection Manager

```python
# src/infrastructure/database/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.unicode_string(),
    echo=True,
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 3.2 Redis Connection Manager

```python
# src/infrastructure/cache/redis_client.py
import redis.asyncio as redis
from src.core.config import settings

class RedisClient:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        return self.redis_client

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    async def get_client(self):
        if not self.redis_client:
            await self.connect()
        return self.redis_client

redis_client = RedisClient()
```

### 3.3 Application Lifecycle Management

```python
# src/core/events.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.database.session import engine
from src.infrastructure.cache.redis_client import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()
    await engine.dispose()
```

## Task 4: Implement Core Domain Entities

### 4.1 Base Entity

```python
# src/domain/entities/base.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid

class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True
```

### 4.2 Session Entity

```python
# src/domain/entities/session.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from src.domain.entities.base import BaseEntity

class Session(BaseEntity):
    """Anonymous session for chat interactions"""
    session_id: str  # Unique WebSocket session identifier
    conversation_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Browser info, IP, etc.

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if session has expired based on TTL"""
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds()
        return elapsed > ttl_seconds

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
```

### 4.3 Conversation Entity

```python
# src/domain/entities/conversation.py
from datetime import datetime
from typing import List, Dict, Any
from pydantic import Field
from src.domain.entities.base import BaseEntity
from src.domain.entities.message import Message

class Conversation(BaseEntity):
    """Aggregate root for chat conversations"""
    session_id: str  # Links to session, not user
    messages: List[Message] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message):
        """Add a message to the conversation"""
        self.messages.append(message)
        self.last_activity = datetime.utcnow()

    def get_context(self, limit: int = 10) -> List[Message]:
        """Get recent messages for context"""
        return self.messages[-limit:] if self.messages else []
```

### 4.4 Message Entity

```python
# src/domain/entities/message.py
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import Field
from src.domain.entities.base import BaseEntity

class Message(BaseEntity):
    """Individual chat message"""
    conversation_id: str
    sender_type: Literal["user", "ai_agent"]
    content: str
    detected_language: str = "id"  # Default to Indonesian
    intent: Optional[str] = None  # Product inquiry, price check, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_product_query(self) -> bool:
        """Check if message contains product query"""
        return self.intent in ["product_inquiry", "price_check", "stock_check"]
```

### 4.5 Value Objects

```python
# src/domain/value_objects/product_info.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal

class ProductInfo(BaseModel):
    """Product information from PIM"""
    sku: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    unit: str = "lembar"  # Default unit in Indonesian
    specifications: Dict[str, Any] = Field(default_factory=dict)
    source: Literal["pim", "cache"] = "pim"

# src/domain/value_objects/query_intent.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class QueryIntent(BaseModel):
    """Classified user query intent"""
    type: Literal["product_inquiry", "price_check", "stock_check", "general"]
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)
```

### 4.6 Repository Interface

```python
# src/domain/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> Optional[T]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
```

## Task 5: Setup Alembic Migrations

### 5.1 Initialize Alembic

```bash
# Run in project root
alembic init migrations
```

### 5.2 Configure Alembic

```python
# alembic.ini - Update the sqlalchemy.url
sqlalchemy.url = postgresql+asyncpg://perky_user:perky_password@localhost/perky_db
```

### 5.3 Update Alembic Environment

```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.database.session import Base
from src.core.config import settings

# Import all models
from src.infrastructure.database.models import *

config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.unicode_string())

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations(connectable):
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL.unicode_string()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    asyncio.run(run_async_migrations(connectable))

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 5.4 Create Initial Migration

```bash
# Create first migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 5.5 Database Models

```python
# src/infrastructure/database/models/conversation.py
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# src/infrastructure/database/models/message.py
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base
import enum

class SenderType(enum.Enum):
    USER = "user"
    AI_AGENT = "ai_agent"

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False, index=True)
    sender_type = Column(Enum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    detected_language = Column(String(10), default="id")
    intent = Column(String(100), nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# src/infrastructure/database/models/product_query.py
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class ProductQueryModel(Base):
    __tablename__ = "product_queries"

    id = Column(String, primary_key=True)
    message_id = Column(String, nullable=True)
    product_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=True)
    query_type = Column(String(50), nullable=True)
    response_data = Column(JSON, default={})
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Verification Commands

### Run Docker Environment

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### Test Database Connection

```bash
# Connect to PostgreSQL
docker exec -it perky-postgres psql -U perky_user -d perky_db

# Test Redis connection
docker exec -it perky-redis redis-cli ping
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

### Run Migrations

```bash
# Create new migration
docker exec -it perky-api alembic revision --autogenerate -m "Add new feature"

# Apply migrations
docker exec -it perky-api alembic upgrade head

# Check migration history
docker exec -it perky-api alembic history
```

## Project Structure After Completion

```text
perky-ai-assistant-v2/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── product_info.py
│   │   │   └── query_intent.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   └── services/
│   ├── application/
│   │   ├── services/
│   │   ├── use_cases/
│   │   └── dto/
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── conversation.py
│   │   │       ├── message.py
│   │   │       └── product_query.py
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis_client.py
│   │   ├── external_services/
│   │   └── repositories/
│   ├── presentation/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── schemas/
│   │   └── dependencies/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── events.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── migrations/
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── scripts/
│   └── init-db.sql
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

## Next Steps

1. **Add PydanticAI Integration**: Configure AI agent for Indonesian steel product inquiries
2. **Add WebSocket Endpoints**: Implement real-time chat with session management
3. **Add Testing**: Write unit tests for domain logic and integration tests for API endpoints
4. **Add CI/CD**: Setup GitHub Actions for automated testing and deployment
5. **Add Monitoring**: Integrate logging and monitoring tools like Sentry or DataDog

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check credentials in `.env` file
   - Verify network connectivity: `docker network ls`

2. **Redis Connection Error**
   - Check Redis is running: `docker exec -it perky-redis redis-cli ping`
   - Verify Redis URL format in configuration

3. **Migration Errors**
   - Ensure database is accessible before running migrations
   - Check for model import errors in `env.py`
   - Verify all models are imported in migrations/env.py

4. **Docker Build Issues**
   - Clear Docker cache: `docker-compose build --no-cache`
   - Check for port conflicts: `lsof -i :8000`
   - Verify Docker daemon is running

## Quality Checklist

- [ ] All services start successfully with `docker-compose up`
- [ ] FastAPI documentation available at `/docs`
- [ ] Database migrations run without errors
- [ ] Redis connection established
- [ ] Project structure follows DDD principles
- [ ] All configuration loaded from environment variables
- [ ] Health check endpoint responds with 200 OK
- [ ] PgAdmin accessible for database management
- [ ] Logging configured for debugging
- [ ] Error handling implemented globally
