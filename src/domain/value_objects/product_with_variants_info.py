"""
ProductWithVariantsInfo aggregate value object that combines product information with all its variants.
Used when users query for a product without specifying a variant.
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, ConfigDict

from .product_info import ProductInfo
from .variant_info import VariantInfo


class ProductWithVariantsInfo(BaseModel):
    """
    Read-only aggregate representing a product with all its variants.
    Used when users query for a product without specifying a variant.
    """

    model_config = ConfigDict(frozen=True)

    product: ProductInfo = Field(..., description="Product-level information")
    variants: List[VariantInfo] = Field(
        ..., min_length=1, description="All product variants"
    )

    @property
    def price_range(self) -> Tuple[Decimal, Decimal]:
        """Min and max price across variants"""
        prices = [v.price for v in self.variants]
        return (min(prices), max(prices))

    @property
    def available_skus(self) -> List[str]:
        """List of all available SKUs"""
        return [v.sku for v in self.variants if v.is_available]

    def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Retrieve specific variant by SKU"""
        return next((v for v in self.variants if v.sku == sku), None)

    def get_variant_by_id(self, variant_id: str) -> Optional[VariantInfo]:
        """Retrieve specific variant by variant ID"""
        return next((v for v in self.variants if v.variant_id == variant_id), None)

    def get_variants_by_attributes(self, attributes: dict) -> List[VariantInfo]:
        """Get all variants matching the specified attributes"""
        return [v for v in self.variants if v.matches_attributes(attributes)]

    def get_total_stock(self) -> int:
        """Calculate total stock across all variants"""
        return sum(v.stock_quantity for v in self.variants)

    def has_available_stock(self) -> bool:
        """Check if any variant has stock available"""
        return any(v.has_stock() for v in self.variants)

    def get_price_display_range(self) -> str:
        """Format price range for display in Indonesian Rupiah"""
        min_price, max_price = self.price_range
        if min_price == max_price:
            return self.variants[0].get_display_price()

        min_formatted = self._format_rupiah(min_price)
        max_formatted = self._format_rupiah(max_price)
        return f"{min_formatted} - {max_formatted}"

    def _format_rupiah(self, amount: Decimal) -> str:
        """Format amount as Indonesian Rupiah"""
        price_str = f"{amount:.0f}"
        formatted = ""
        for i, digit in enumerate(reversed(price_str)):
            if i > 0 and i % 3 == 0:
                formatted = "." + formatted
            formatted = digit + formatted
        return f"Rp {formatted}"

    def to_summary_dict(self) -> dict:
        """
        Return a simplified dictionary for API responses.
        Provides product overview with variant options.
        """
        return {
            "product_id": self.product.product_id,
            "product_name": self.product.product_name,
            "description": self.product.product_description,
            "category": self.product.category,
            "variant_count": len(self.variants),
            "price_range": self.get_price_display_range(),
            "total_stock": self.get_total_stock(),
            "has_stock": self.has_available_stock(),
            "variants": [v.to_summary_dict() for v in self.variants],
        }
