from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductInfo(BaseModel):
    """
    Read-only representation of a product from PIM.
    A product is a category that contains one or more variants.
    """

    model_config = ConfigDict(frozen=True)

    product_id: str = Field(..., min_length=1, description="Unique product identifier")

    product_name: str = Field(
        ..., min_length=1, description="Product category name (e.g., 'Plat Baja')"
    )
    product_description: Optional[str] = Field(None, description="Product overview")

    category: Optional[str] = Field(None, description="Product category in PIM")
    variant_count: int = Field(..., ge=1, description="Number of available variants")
