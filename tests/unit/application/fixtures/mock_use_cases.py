"""Mock implementations for application use cases.

This module contains mock implementations of all use case interfaces
for testing purposes.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock

import pytest

from src.application.dto.conversation_dto import ConversationDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.session_dto import SessionDTO
from src.application.use_cases.interfaces import (
    GetConversationUseCase,
    ProcessUserMessageUseCase,
    StartChatSessionUseCase,
)


class MockStartChatSessionUseCase(StartChatSessionUseCase):
    """Mock implementation of StartChatSessionUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        self.call_count += 1
        self.last_call_args = {"session_id": session_id, "metadata": metadata}
        return await self.execute_mock(session_id, metadata)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


class MockProcessUserMessageUseCase(ProcessUserMessageUseCase):
    """Mock implementation of ProcessUserMessageUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        self.call_count += 1
        self.last_call_args = {
            "session_id": session_id,
            "content": content,
            "metadata": metadata,
        }
        return await self.execute_mock(session_id, content, metadata)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


class MockGetConversationUseCase(GetConversationUseCase):
    """Mock implementation of GetConversationUseCase for testing."""

    def __init__(self):
        self.execute_mock = AsyncMock()
        self.call_count = 0
        self.last_call_args = None

    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        self.call_count += 1
        self.last_call_args = {"session_id": session_id}
        return await self.execute_mock(session_id)

    def reset(self):
        self.execute_mock.reset_mock()
        self.call_count = 0
        self.last_call_args = None


# Fixtures
@pytest.fixture
def mock_start_chat_session():
    """Fixture for start chat session use case mock."""
    return MockStartChatSessionUseCase()


@pytest.fixture
def mock_process_message():
    """Fixture for process message use case mock."""
    return MockProcessUserMessageUseCase()


@pytest.fixture
def mock_get_conversation():
    """Fixture for get conversation use case mock."""
    return MockGetConversationUseCase()


__all__ = [
    "MockStartChatSessionUseCase",
    "MockProcessUserMessageUseCase",
    "MockGetConversationUseCase",
    "mock_start_chat_session",
    "mock_process_message",
    "mock_get_conversation",
]
