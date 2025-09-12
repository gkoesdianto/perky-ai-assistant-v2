from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal


class ProductInfo(BaseModel):
    """Product information from PIM"""

    sku: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    unit: str = "lembar"  # Default unit in Indonesian
    specifications: Dict[str, Any] = Field(default_factory=dict)
    source: Literal["pim", "cache"] = "pim"
