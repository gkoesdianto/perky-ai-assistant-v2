"""
Mock product service implementing ProductServicePort for MVP.
Provides a service layer over MockProductRepository.
"""

import asyncio
import random
from typing import List, Optional

from src.application.ports import ProductServicePort
from src.domain.value_objects import ProductInfo
from src.domain.value_objects.product_with_variants_info import ProductWithVariantsInfo
from src.infrastructure.mocks.mock_product_repository import MockProductRepository


class MockProductService(ProductServicePort):
    """
    Mock product service with realistic steel industry data.
    Implements ProductServicePort interface for application layer.
    """

    def __init__(self):
        """Initialize with mock product repository."""
        self.repository = MockProductRepository()
        self._init_search_index()

    def _init_search_index(self):
        """Initialize search index for fast lookup."""
        self.search_index = {}

        for product_id, product_with_variants in self.repository.products.items():
            product = product_with_variants.product

            for word in product.product_name.lower().split():
                if word not in self.search_index:
                    self.search_index[word] = []
                if product_id not in self.search_index[word]:
                    self.search_index[word].append(product_id)

            category_key = (
                f"cat_{product.category.lower() if product.category else 'unknown'}"
            )
            if category_key not in self.search_index:
                self.search_index[category_key] = []
            self.search_index[category_key].append(product_id)

    async def search_products(self, query: str) -> List[ProductInfo]:
        """
        Search products by name or description with Indonesian terminology support.

        Args:
            query: Search query string

        Returns:
            List of matching product information
        """
        await asyncio.sleep(random.uniform(0.05, 0.15))

        results = set()
        query_lower = query.lower()

        for word in query_lower.split():
            if word in self.search_index:
                for product_id in self.search_index[word]:
                    results.add(product_id)

        normalized_queries = self._normalize_query(query_lower)
        for norm_query in normalized_queries:
            for word in norm_query.split():
                if word in self.search_index:
                    for product_id in self.search_index[word]:
                        results.add(product_id)

        product_list = []
        for product_id in results:
            if product_id in self.repository.products:
                product_list.append(self.repository.products[product_id].product)

        return product_list[:5]

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        """
        Get product with all its variants.

        Args:
            product_id: Product identifier

        Returns:
            Product with all variants if found, None otherwise
        """
        return await self.repository.get_product_with_variants(product_id)

    async def get_variant_by_sku(self, sku: str):
        """
        Get specific variant by SKU.

        Args:
            sku: Stock keeping unit code

        Returns:
            Variant information if found
        """
        return await self.repository.get_variant_by_sku(sku)

    async def get_variants_by_product(self, product_id: str):
        """
        Get all variants for a product.

        Args:
            product_id: Product identifier

        Returns:
            List of variants for the product
        """
        return await self.repository.get_variants_by_product(product_id)

    def _normalize_query(self, query: str) -> List[str]:
        """
        Normalize Indonesian terminology to include related terms.

        Args:
            query: Search query to normalize

        Returns:
            List of normalized search terms
        """
        normalized = [query]

        terminology_map = self.repository.terminology_map

        words = query.split()
        for word in words:
            if word in terminology_map:
                normalized.extend(terminology_map[word])

        if query in terminology_map:
            normalized.extend(terminology_map[query])

        seen = set()
        result = []
        for item in normalized:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result
