"""Test environment configuration and fixtures.

This module provides environment-specific configurations for different test types:
- Unit tests: In-memory databases and mocks
- Integration tests: Test databases with transactions
- E2E tests: Full environment with external services
"""

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings


@dataclass
class TestEnvironment:
    """Test environment configuration."""

    # Database configuration
    db_url: str = field(default="")
    db_echo: bool = field(default=False)
    db_pool_size: int = field(default=5)
    db_use_memory: bool = field(default=False)

    # Redis configuration
    redis_url: str = field(default="")
    redis_use_mock: bool = field(default=False)
    redis_db: int = field(default=15)  # Use DB 15 for tests

    # External services
    mock_external_services: bool = field(default=True)
    external_service_timeout: float = field(default=5.0)

    # Test data paths
    test_data_dir: Optional[Path] = field(default=None)
    fixtures_dir: Optional[Path] = field(default=None)

    # Feature flags
    enable_performance_monitoring: bool = field(default=False)
    enable_coverage_tracking: bool = field(default=True)
    enable_test_isolation: bool = field(default=True)

    # Timeouts
    default_timeout: float = field(default=10.0)
    websocket_timeout: float = field(default=5.0)
    async_timeout: float = field(default=30.0)

    def __post_init__(self):
        """Initialize computed fields."""
        # Set default database URL if not provided
        if not self.db_url:
            if self.db_use_memory:
                self.db_url = "sqlite+aiosqlite:///:memory:"
            else:
                self.db_url = os.getenv(
                    "TEST_DATABASE_URL",
                    settings.DATABASE_URL.replace("/perky_db", "/test_perky_db"),
                )

        # Set default Redis URL if not provided
        if not self.redis_url and not self.redis_use_mock:
            self.redis_url = os.getenv(
                "TEST_REDIS_URL", f"redis://localhost:6379/{self.redis_db}"
            )

        # Set test data directories
        if not self.test_data_dir:
            self.test_data_dir = Path(__file__).parent.parent / "data"
        if not self.fixtures_dir:
            self.fixtures_dir = Path(__file__).parent

    @classmethod
    def for_unit_tests(cls) -> "TestEnvironment":
        """Create environment configuration for unit tests."""
        return cls(
            db_use_memory=True,
            redis_use_mock=True,
            mock_external_services=True,
            enable_test_isolation=True,
            enable_performance_monitoring=False,
        )

    @classmethod
    def for_integration_tests(cls) -> "TestEnvironment":
        """Create environment configuration for integration tests."""
        return cls(
            db_use_memory=False,
            redis_use_mock=False,
            mock_external_services=True,
            enable_test_isolation=True,
            enable_performance_monitoring=False,
        )

    @classmethod
    def for_e2e_tests(cls) -> "TestEnvironment":
        """Create environment configuration for E2E tests."""
        return cls(
            db_use_memory=False,
            redis_use_mock=False,
            mock_external_services=False,
            enable_test_isolation=False,
            enable_performance_monitoring=True,
            websocket_timeout=30.0,
            async_timeout=60.0,
        )

    @classmethod
    def for_performance_tests(cls) -> "TestEnvironment":
        """Create environment configuration for performance tests."""
        return cls(
            db_use_memory=False,
            redis_use_mock=False,
            mock_external_services=False,
            enable_test_isolation=False,
            enable_performance_monitoring=True,
            enable_coverage_tracking=False,
            db_pool_size=20,
            default_timeout=60.0,
            async_timeout=120.0,
        )


class TestDatabaseManager:
    """Manages test database connections and transactions."""

    def __init__(self, env: TestEnvironment):
        self.env = env
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None

    async def setup(self):
        """Set up database connection and create tables."""
        # Create engine with appropriate configuration
        if self.env.db_use_memory:
            self.engine = create_async_engine(
                self.env.db_url,
                echo=self.env.db_echo,
                poolclass=NullPool,  # No pooling for in-memory DB
            )
        else:
            self.engine = create_async_engine(
                self.env.db_url,
                echo=self.env.db_echo,
                pool_size=self.env.db_pool_size,
                pool_pre_ping=True,
            )

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables if needed (for in-memory or test DB)
        if self.env.db_use_memory or self.env.enable_test_isolation:
            # Note: Database models not yet implemented in MVP phase
            # When implementing, uncomment and update import path:
            # from src.infrastructure.db.models import Base
            # async with self.engine.begin() as conn:
            #     await conn.run_sync(Base.metadata.create_all)
            pass

    async def teardown(self):
        """Clean up database connections."""
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self.session_factory:
            await self.setup()
        return self.session_factory()

    async def create_test_database(self):
        """Create test database (for PostgreSQL)."""
        if "postgresql" in self.env.db_url:
            # Create test database if it doesn't exist
            base_url = self.env.db_url.rsplit("/", 1)[0]
            async with create_async_engine(
                f"{base_url}/postgres", isolation_level="AUTOCOMMIT"
            ).connect() as conn:
                db_name = self.env.db_url.rsplit("/", 1)[1].split("?")[0]
                result = await conn.execute(
                    f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"
                )
                if not result.fetchone():
                    await conn.execute(f"CREATE DATABASE {db_name}")

    async def drop_test_database(self):
        """Drop test database (for PostgreSQL)."""
        if "postgresql" in self.env.db_url and self.env.enable_test_isolation:
            base_url = self.env.db_url.rsplit("/", 1)[0]
            async with create_async_engine(
                f"{base_url}/postgres", isolation_level="AUTOCOMMIT"
            ).connect() as conn:
                db_name = self.env.db_url.rsplit("/", 1)[1].split("?")[0]
                # Terminate connections
                await conn.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                    AND pid <> pg_backend_pid()
                    """
                )
                # Drop database
                await conn.execute(f"DROP DATABASE IF EXISTS {db_name}")


class TestRedisManager:
    """Manages test Redis connections."""

    def __init__(self, env: TestEnvironment):
        self.env = env
        self.client: Optional[redis.Redis] = None
        self.mock_client: Optional[AsyncMock] = None

    async def setup(self):
        """Set up Redis connection or mock."""
        if self.env.redis_use_mock:
            # Create mock Redis client
            self.mock_client = AsyncMock(spec=redis.Redis)
            self.mock_client.get.return_value = None
            self.mock_client.set.return_value = True
            self.mock_client.delete.return_value = 1
            self.mock_client.exists.return_value = 0
            self.mock_client.expire.return_value = True
            self.mock_client.ttl.return_value = -1
        else:
            # Create real Redis client
            self.client = redis.from_url(self.env.redis_url, decode_responses=True)
            # Test connection
            await self.client.ping()

    async def teardown(self):
        """Clean up Redis connections."""
        if self.client:
            await self.client.close()

    async def get_client(self) -> redis.Redis:
        """Get Redis client (real or mock)."""
        if not self.client and not self.mock_client:
            await self.setup()
        return self.mock_client if self.env.redis_use_mock else self.client

    async def flush_test_data(self):
        """Flush all data from test Redis database."""
        if self.client and self.env.enable_test_isolation:
            await self.client.flushdb()


# Environment fixtures
@pytest.fixture(scope="session")
def test_env_config(request) -> TestEnvironment:
    """Get test environment configuration based on test type.

    The test type is determined by markers or command-line options.
    """
    if request.config.getoption("--e2e", default=False):
        return TestEnvironment.for_e2e_tests()
    elif request.config.getoption("--performance", default=False):
        return TestEnvironment.for_performance_tests()
    elif request.config.getoption("--integration", default=False):
        return TestEnvironment.for_integration_tests()
    else:
        # Default to unit test configuration
        return TestEnvironment.for_unit_tests()


@pytest.fixture(scope="session")
async def db_manager(
    test_env_config: TestEnvironment,
) -> AsyncGenerator[TestDatabaseManager, None]:
    """Provide database manager for tests."""
    manager = TestDatabaseManager(test_env_config)
    await manager.create_test_database()
    await manager.setup()
    yield manager
    await manager.teardown()
    if test_env_config.enable_test_isolation:
        await manager.drop_test_database()


@pytest.fixture(scope="session")
async def redis_manager(
    test_env_config: TestEnvironment,
) -> AsyncGenerator[TestRedisManager, None]:
    """Provide Redis manager for tests."""
    manager = TestRedisManager(test_env_config)
    await manager.setup()
    yield manager
    await manager.teardown()


@pytest.fixture(scope="function")
async def db_session(
    db_manager: TestDatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with transaction rollback."""
    async with db_manager.get_session() as session:
        async with session.begin():
            yield session
            # Rollback transaction for test isolation
            await session.rollback()


@pytest.fixture(scope="function")
async def redis_client(
    redis_manager: TestRedisManager,
) -> AsyncGenerator[redis.Redis, None]:
    """Provide Redis client with automatic cleanup."""
    client = await redis_manager.get_client()
    yield client
    # Cleanup test keys if using real Redis
    if not redis_manager.env.redis_use_mock and redis_manager.env.enable_test_isolation:
        await redis_manager.flush_test_data()


# Mock service fixtures
@pytest.fixture
def mock_pim_service() -> AsyncMock:
    """Provide mock PIM service for testing."""
    mock = AsyncMock()
    mock.get_product.return_value = {
        "id": "test-product-1",
        "name": "Test Product",
        "price": 99.99,
        "stock": 100,
    }
    mock.search_products.return_value = [
        {"id": "test-product-1", "name": "Test Product 1"},
        {"id": "test-product-2", "name": "Test Product 2"},
    ]
    return mock


@pytest.fixture
def mock_openai_service() -> AsyncMock:
    """Provide mock OpenAI service for testing."""
    mock = AsyncMock()
    mock.chat_completion.return_value = {
        "choices": [{"message": {"content": "This is a test AI response."}}]
    }
    return mock


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Provide mock WebSocket for testing."""
    mock = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_json = AsyncMock(
        return_value={"type": "user_message", "message": "Test message"}
    )
    mock.close = AsyncMock()
    return mock


# Test directory fixtures
@pytest.fixture(scope="session")
def test_data_dir(test_env_config: TestEnvironment) -> Path:
    """Provide test data directory path."""
    test_env_config.test_data_dir.mkdir(parents=True, exist_ok=True)
    return test_env_config.test_data_dir


@pytest.fixture(scope="function")
def temp_dir() -> Path:
    """Provide temporary directory for test."""
    with tempfile.TemporaryDirectory() as temp:
        yield Path(temp)
