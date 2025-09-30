from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class SessionDTO:
    session_id: str
    conversation_id: Optional[str]
    started_at: datetime
    last_activity: datetime
    is_active: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
