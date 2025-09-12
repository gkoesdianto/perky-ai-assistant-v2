"""
Abstract repository for product/variant queries.
Read-only operations against PIM system.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from src.domain.value_objects import ProductInfo, VariantInfo
from src.domain.value_objects.product_with_variants_info import ProductWithVariantsInfo


class ProductRepository(ABC):
    """
    Abstract repository for product/variant queries.
    Read-only operations against PIM system.
    """

    @abstractmethod
    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        """Fetch product with all its variants"""
        pass

    @abstractmethod
    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """Fetch specific variant by SKU"""
        pass

    @abstractmethod
    async def search_products(self, query: str) -> List[ProductInfo]:
        """Search products by name or description"""
        pass

    @abstractmethod
    async def get_variants_by_product(self, product_id: str) -> List[VariantInfo]:
        """Fetch all variants for a product"""
        pass
