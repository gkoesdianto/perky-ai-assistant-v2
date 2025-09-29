"""Test data lifecycle management.

This module provides comprehensive test data management including:
- Session-scoped setup and teardown
- Test isolation mechanisms
- Data factories for consistent test data
- Cleanup utilities for database, cache, and filesystem
"""

import asyncio
import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import pytest
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.domain.entities import Conversation, Message, Session
from src.infrastructure.mocks.mock_session_repository import (
    MockSessionRepository as SessionRepository,
)


class TestDataManager:
    """Manages test data lifecycle across different test scopes."""

    def __init__(self):
        self.created_sessions: List[str] = []
        self.created_files: List[Path] = []
        self.temp_dirs: List[Path] = []
        self.redis_keys: List[str] = []
        self.db_records: Dict[str, List[str]] = {
            "sessions": [],
            "conversations": [],
            "messages": [],
        }

    async def create_test_session(
        self,
        session_repo: SessionRepository,
        user_id: Optional[str] = None,
        with_messages: int = 0,
    ) -> Session:
        """Create a test session with optional messages.

        Args:
            session_repo: Repository for session operations
            user_id: User ID for the session
            with_messages: Number of messages to create in conversation

        Returns:
            Created session with conversation and messages
        """
        user_id = user_id or f"test-user-{uuid.uuid4()}"

        # Create session
        session = await session_repo.create(user_id=user_id)
        self.created_sessions.append(session.id)
        self.db_records["sessions"].append(session.id)

        # Add messages if requested
        if with_messages > 0:
            conversation = session.conversation
            for i in range(with_messages):
                role = "user" if i % 2 == 0 else "assistant"
                content = f"Test message {i+1}"
                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    role=role,
                    content=content,
                    created_at=datetime.utcnow(),
                )
                conversation.messages.append(message)
                self.db_records["messages"].append(message.id)

            # Update session
            await session_repo.update(session)

        return session

    async def create_redis_test_data(
        self, redis_client: redis.Redis, key_prefix: str = "test"
    ) -> Dict[str, Any]:
        """Create test data in Redis.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys

        Returns:
            Dictionary of created keys and values
        """
        test_data = {
            f"{key_prefix}:session:123": json.dumps(
                {"user_id": "test-user", "created_at": datetime.utcnow().isoformat()}
            ),
            f"{key_prefix}:product:456": json.dumps(
                {"name": "Test Product", "price": 100.00}
            ),
            f"{key_prefix}:cache:789": "cached_value",
        }

        # Store data in Redis
        for key, value in test_data.items():
            await redis_client.set(key, value, ex=3600)  # 1 hour TTL
            self.redis_keys.append(key)

        return test_data

    def create_temp_directory(self, base_path: Path, name: str) -> Path:
        """Create a temporary directory for testing.

        Args:
            base_path: Base path for temporary directory
            name: Name of the directory

        Returns:
            Path to created directory
        """
        temp_dir = base_path / f"temp_{name}_{uuid.uuid4()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def create_test_file(
        self, directory: Path, filename: str, content: str = ""
    ) -> Path:
        """Create a test file with optional content.

        Args:
            directory: Directory to create file in
            filename: Name of the file
            content: File content

        Returns:
            Path to created file
        """
        file_path = directory / filename
        file_path.write_text(content)
        self.created_files.append(file_path)
        return file_path

    async def cleanup_database(self, db_session: AsyncSession):
        """Clean up database records created during tests.

        Args:
            db_session: Database session for cleanup operations
        """
        # Delete messages first (foreign key constraint)
        if self.db_records["messages"]:
            await db_session.execute(
                text("DELETE FROM messages WHERE id = ANY(:ids)"),
                {"ids": self.db_records["messages"]},
            )

        # Delete conversations
        if self.db_records["conversations"]:
            await db_session.execute(
                text("DELETE FROM conversations WHERE id = ANY(:ids)"),
                {"ids": self.db_records["conversations"]},
            )

        # Delete sessions
        if self.db_records["sessions"]:
            await db_session.execute(
                text("DELETE FROM sessions WHERE id = ANY(:ids)"),
                {"ids": self.db_records["sessions"]},
            )

        await db_session.commit()

        # Clear records
        self.db_records = {"sessions": [], "conversations": [], "messages": []}

    async def cleanup_redis(self, redis_client: redis.Redis):
        """Clean up Redis keys created during tests.

        Args:
            redis_client: Redis client for cleanup operations
        """
        if self.redis_keys:
            await redis_client.delete(*self.redis_keys)
            self.redis_keys.clear()

    def cleanup_filesystem(self):
        """Clean up temporary files and directories."""
        # Remove files first
        for file_path in self.created_files:
            if file_path.exists():
                file_path.unlink()
        self.created_files.clear()

        # Remove directories
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()

    async def cleanup_all(
        self,
        db_session: Optional[AsyncSession] = None,
        redis_client: Optional[redis.Redis] = None,
    ):
        """Perform complete cleanup of all test data.

        Args:
            db_session: Optional database session for cleanup
            redis_client: Optional Redis client for cleanup
        """
        # Database cleanup
        if db_session:
            await self.cleanup_database(db_session)

        # Redis cleanup
        if redis_client:
            await self.cleanup_redis(redis_client)

        # Filesystem cleanup
        self.cleanup_filesystem()


class TestDataFactory:
    """Factory for creating consistent test data across different test types."""

    @staticmethod
    def create_product_data(
        product_id: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create test product data.

        Args:
            product_id: Product ID
            name: Product name
            price: Product price

        Returns:
            Product data dictionary
        """
        return {
            "id": product_id or f"prod-{uuid.uuid4()}",
            "name": name or "Test Product",
            "description": "Test product description",
            "price": price or 99.99,
            "stock": 100,
            "category": "test-category",
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_user_data(
        user_id: Optional[str] = None, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create test user data.

        Args:
            user_id: User ID
            name: User name

        Returns:
            User data dictionary
        """
        return {
            "id": user_id or f"user-{uuid.uuid4()}",
            "name": name or "Test User",
            "email": f"test-{uuid.uuid4()}@example.com",
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_message_data(
        role: str = "user", content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create test message data.

        Args:
            role: Message role (user/assistant/system)
            content: Message content

        Returns:
            Message data dictionary
        """
        return {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content or f"Test {role} message",
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_websocket_message(
        msg_type: str = "user_message", message: Optional[str] = None
    ) -> str:
        """Create test WebSocket message.

        Args:
            msg_type: Message type
            message: Message content

        Returns:
            JSON string of WebSocket message
        """
        return json.dumps(
            {
                "type": msg_type,
                "message": message or "Test WebSocket message",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# Pytest fixtures for test data management
@pytest.fixture(scope="session")
def test_data_manager() -> TestDataManager:
    """Provide test data manager for session scope."""
    return TestDataManager()


@pytest.fixture(scope="function")
async def isolated_test_data(
    test_data_manager: TestDataManager,
) -> AsyncGenerator[TestDataManager, None]:
    """Provide isolated test data manager with automatic cleanup.

    This fixture ensures complete cleanup after each test function.
    """
    yield test_data_manager

    # Cleanup after test
    await test_data_manager.cleanup_all()


@pytest.fixture(scope="session")
def test_factory() -> TestDataFactory:
    """Provide test data factory for creating consistent test data."""
    return TestDataFactory()


@pytest.fixture(scope="function")
def temp_test_dir(tmp_path: Path, test_data_manager: TestDataManager) -> Path:
    """Create a temporary directory for test with automatic cleanup.

    Args:
        tmp_path: Pytest's tmp_path fixture
        test_data_manager: Test data manager for tracking

    Returns:
        Path to temporary directory
    """
    test_dir = test_data_manager.create_temp_directory(tmp_path, "test")
    return test_dir


@pytest.fixture(scope="function")
async def test_session_with_history(
    test_data_manager: TestDataManager, session_repo: SessionRepository
) -> Session:
    """Create a test session with conversation history.

    Args:
        test_data_manager: Test data manager
        session_repo: Session repository

    Returns:
        Session with 5 messages in conversation
    """
    return await test_data_manager.create_test_session(
        session_repo, user_id="test-user-with-history", with_messages=5
    )


@pytest.fixture(scope="function")
async def multiple_test_sessions(
    test_data_manager: TestDataManager, session_repo: SessionRepository
) -> List[Session]:
    """Create multiple test sessions for concurrency testing.

    Args:
        test_data_manager: Test data manager
        session_repo: Session repository

    Returns:
        List of 3 test sessions
    """
    sessions = []
    for i in range(3):
        session = await test_data_manager.create_test_session(
            session_repo, user_id=f"concurrent-user-{i}", with_messages=2
        )
        sessions.append(session)
    return sessions


# Cleanup fixtures for different test scopes
@pytest.fixture(autouse=True, scope="function")
async def auto_cleanup_function(test_data_manager: TestDataManager):
    """Automatically cleanup after each test function."""
    yield
    # Cleanup is minimal for function scope
    test_data_manager.cleanup_filesystem()


@pytest.fixture(autouse=True, scope="module")
async def auto_cleanup_module(test_data_manager: TestDataManager):
    """Automatically cleanup after each test module."""
    yield
    # More thorough cleanup for module scope
    await test_data_manager.cleanup_all()


@pytest.fixture(autouse=True, scope="session")
async def auto_cleanup_session(test_data_manager: TestDataManager):
    """Final cleanup after entire test session."""
    yield
    # Complete cleanup after all tests
    await test_data_manager.cleanup_all()
