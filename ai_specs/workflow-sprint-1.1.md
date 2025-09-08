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
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
redis==5.0.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

```text
-r base.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==23.12.1
isort==5.13.2
flake8==7.0.0
mypy==1.8.0
pre-commit==3.6.0
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
    PROJECT_NAME: str = "Perky AI Assistant"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None

    # Redis
    REDIS_URL: RedisDsn

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Task 2: Setup Docker Development Environment

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
version: '3.8'

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
      - SECRET_KEY=your-secret-key-here-change-in-production
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
POSTGRES_SERVER=localhost
POSTGRES_USER=perky_user
POSTGRES_PASSWORD=perky_password
POSTGRES_DB=perky_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here-change-in-production
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

### 4.2 User Entity

```python
# src/domain/entities/user.py
from typing import Optional
from src.domain.entities.base import BaseEntity
from src.domain.value_objects.email import Email

class User(BaseEntity):
    email: Email
    username: str
    first_name: str
    last_name: str
    is_verified: bool = False
    is_superuser: bool = False
    hashed_password: Optional[str] = None

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def can_access_admin(self) -> bool:
        return self.is_superuser and self.is_verified
```

### 4.3 Value Objects

```python
# src/domain/value_objects/email.py
from pydantic import BaseModel, EmailStr, validator

class Email(BaseModel):
    value: EmailStr

    @validator('value')
    def validate_email(cls, v):
        # Add custom email validation if needed
        return v.lower()

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Email(value='{self.value}')"
```

### 4.4 Repository Interface

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
# src/infrastructure/database/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
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
│   │   │   └── user.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   └── email.py
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
│   │   │       └── user.py
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

1. **Add Authentication**: Implement JWT-based authentication using FastAPI security utilities
2. **Add API Endpoints**: Create CRUD endpoints for your domain entities
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
