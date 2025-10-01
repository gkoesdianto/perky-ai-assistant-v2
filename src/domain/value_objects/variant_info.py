"""
VariantInfo value object representing a single sellable unit with specific
SKU, pricing, and stock information. Each variant is a specific configuration
of a product that can be sold independently.
"""

from decimal import Decimal
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VariantInfo(BaseModel):
    """
    Read-only representation of a product variant from PIM.
    Each variant is a specific sellable configuration of a product.

    This value object represents the atomic unit of sale - a specific
    SKU with its own pricing, stock levels, and specifications
    (e.g., "Plat Baja 5mm x 1200mm x 2400mm").
    """

    model_config = ConfigDict(frozen=True)  # Immutable value object

    # Identifiers
    variant_id: str = Field(..., description="Unique variant identifier from PIM")
    sku: str = Field(..., description="Stock Keeping Unit for inventory management")
    product_id: str = Field(
        ...,
        description=(
            "Parent product identifier linking this variant to its " "product category"
        ),
    )

    # Variant Details
    variant_name: str = Field(
        ...,
        description=(
            "Variant description " "(e.g., 'Plat Baja 5mm x 1200mm x 2400mm')"
        ),
    )

    # Commerce Information
    price: Decimal = Field(..., ge=0, description="Unit price in IDR")
    stock_quantity: int = Field(..., ge=0, description="Available stock units")
    stock_unit: str = Field(
        default="lembar",
        description="Unit of measurement (lembar, batang, kg, meter, roll)",
    )

    # Variant Specifications
    specifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variant-specific attributes (thickness, dimensions, grade, etc.)",
    )

    # Metadata
    source: Literal["pim", "cache"] = Field(
        default="pim", description="Data source indicator"
    )
    is_available: bool = Field(
        default=True, description="Availability flag for the variant"
    )

    @field_validator("price", mode="before")
    @classmethod
    def convert_price_to_decimal(cls, v):
        """Convert price to Decimal for financial precision."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @field_validator("stock_unit")
    @classmethod
    def validate_stock_unit(cls, v):
        """Validate stock unit is one of the accepted Indonesian units."""
        valid_units = ["lembar", "batang", "kg", "meter", "roll", "unit", "pcs"]
        if v.lower() not in valid_units:
            # Don't raise error, just use the value as-is for flexibility
            # But log warning in production
            pass
        return v

    @field_validator("specifications", mode="before")
    @classmethod
    def validate_specifications(cls, v):
        """Ensure specifications is always a dict."""
        if v is None:
            return {}
        return v

    def get_display_price(self) -> str:
        """Format price for display in Indonesian Rupiah."""
        price_str = f"{self.price:.0f}"
        formatted = ""
        for i, digit in enumerate(reversed(price_str)):
            if i > 0 and i % 3 == 0:
                formatted = "." + formatted
            formatted = digit + formatted
        return f"Rp {formatted}"

    def has_stock(self) -> bool:
        """Check if variant has available stock."""
        return self.stock_quantity > 0 and self.is_available

    def get_specification(self, key: str, default: Any = None) -> Any:
        """Safely get a specification value with optional default."""
        return self.specifications.get(key, default)

    def matches_attributes(self, attributes: Dict[str, Any]) -> bool:
        """
        Check if this variant matches the given attribute filters.
        Used for variant selection based on user requirements.
        """
        for key, value in attributes.items():
            spec_value = self.specifications.get(key)
            if spec_value is None:
                return False
            # Handle case-insensitive string comparison
            if isinstance(spec_value, str) and isinstance(value, str):
                if spec_value.lower() != value.lower():
                    return False
            elif spec_value != value:
                return False
        return True

    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Return a simplified dictionary for API responses.
        Excludes internal metadata and provides formatted values.
        """
        return {
            "variant_id": self.variant_id,
            "sku": self.sku,
            "name": self.variant_name,
            "price": float(self.price),
            "display_price": self.get_display_price(),
            "stock": self.stock_quantity,
            "unit": self.stock_unit,
            "available": self.has_stock(),
            "specifications": self.specifications,
        }
