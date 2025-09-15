from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

from .message_dto import MessageDTO


@dataclass
class ConversationDTO:
    id: str
    session_id: str
    messages: List[MessageDTO]
    started_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
