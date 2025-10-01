from typing import Any, Dict, Literal, Optional

from pydantic import Field

from src.domain.entities.base import BaseEntity


class Message(BaseEntity):
    """Individual chat message"""

    conversation_id: str
    sender_type: Literal["user", "ai_agent"]
    content: str
    detected_language: str = "id"  # Default to Indonesian
    intent: Optional[str] = None  # Product inquiry, price check, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_product_query(self) -> bool:
        """Check if message contains product query"""
        return self.intent in ["product_inquiry", "price_check", "stock_check"]
