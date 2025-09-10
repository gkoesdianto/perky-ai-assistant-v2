from pydantic import BaseModel, Field
from typing import Literal, Optional


class QueryIntent(BaseModel):
    """Classified user query intent"""

    type: Literal["product_inquiry", "price_check", "stock_check", "general"]
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)
