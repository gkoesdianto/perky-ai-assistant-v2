from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field
from src.domain.entities.base import BaseEntity


class Session(BaseEntity):
    """Anonymous session for chat interactions"""

    session_id: str  # Unique WebSocket session identifier
    conversation_id: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Browser info, IP, etc.

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if session has expired based on TTL"""
        elapsed = (datetime.now(timezone.utc) - self.last_activity).total_seconds()
        return elapsed > ttl_seconds

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)
