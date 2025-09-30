from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Optional


@dataclass
class MessageDTO:
    content: str
    sender_type: Literal["user", "ai_agent"]
    session_id: str
    conversation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_entity(cls, message, session_id: Optional[str] = None) -> "MessageDTO":
        """Convert Message entity to MessageDTO.

        Args:
            message: The Message entity to convert
            session_id: The session ID (Message entity doesn't have this field)

        Returns:
            MessageDTO instance
        """
        return cls(
            content=message.content,
            sender_type=message.sender_type,
            session_id=session_id or "",  # Message entity doesn't have session_id
            conversation_id=message.conversation_id,
            timestamp=message.created_at,
            metadata=message.metadata or {},
        )
