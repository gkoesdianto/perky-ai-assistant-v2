from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import Field

from src.domain.entities.base import BaseEntity

if TYPE_CHECKING:
    from src.domain.entities.message import Message


class Conversation(BaseEntity):
    """Aggregate root for chat conversations"""

    session_id: str  # Links to session, not user
    messages: List["Message"] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: "Message"):
        """Add a message to the conversation"""
        self.messages.append(message)
        self.last_activity = datetime.now(timezone.utc)

    def get_context(self, limit: int = 10) -> List["Message"]:
        """Get recent messages for context"""
        return self.messages[-limit:] if self.messages else []
