from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Literal


@dataclass
class MessageDTO:
    content: str
    sender_type: Literal["user", "ai_agent"]
    session_id: str
    conversation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_entity(cls, message) -> "MessageDTO":
        return cls(
            content=message.content,
            sender_type=message.sender_type,
            session_id=message.session_id,
            conversation_id=message.conversation_id,
            timestamp=message.created_at,
            metadata=message.metadata or {},
        )
