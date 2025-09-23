"""Type definitions for WebSocket communication."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class MessageType(Enum):
    """WebSocket message types."""

    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM = "system"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PING = "ping"
    PONG = "pong"


class SystemEvent(Enum):
    """System event types."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TYPING = "typing"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: MessageType
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(
        use_enum_values=True
    )
