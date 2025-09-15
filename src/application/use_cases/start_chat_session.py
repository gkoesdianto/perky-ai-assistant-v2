from typing import Dict, Any
from datetime import datetime, timezone
import json

from src.domain.entities.session import Session
from src.application.dto.session_dto import SessionDTO
from src.application.use_cases.interfaces import StartChatSessionUseCase


class StartChatSessionUseCaseImpl(StartChatSessionUseCase):
    """Implementation of start chat session use case"""

    def __init__(self, session_repository=None, redis_client=None):
        self.session_repository = session_repository
        self.redis_client = redis_client

    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        """Start a new chat session"""

        # Check if session already exists
        redis = await self.redis_client.get_client()
        existing = await redis.get(f"session:{session_id}")

        if existing:
            # Parse the JSON string back to dict
            session_data = json.loads(existing)
            return SessionDTO(
                session_id=session_data["session_id"],
                conversation_id=session_data.get("conversation_id"),
                started_at=datetime.fromisoformat(session_data["started_at"]),
                last_activity=datetime.fromisoformat(session_data["last_activity"]),
                is_active=session_data["is_active"],
                metadata=session_data.get("metadata", {}),
            )

        # Create new session entity
        session = Session(
            session_id=session_id,
            started_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            metadata=metadata,
        )

        # Store in Redis (for MVP, skip database)
        session_data = {
            "session_id": session.session_id,
            "conversation_id": session.conversation_id,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_active": True,
            "metadata": session.metadata,
        }

        await redis.setex(
            f"session:{session_id}", 3600, json.dumps(session_data)  # 1 hour TTL
        )

        return SessionDTO(
            session_id=session.session_id,
            conversation_id=session.conversation_id,
            started_at=session.started_at,
            last_activity=session.last_activity,
            is_active=True,
            metadata=session.metadata,
        )
