from typing import Protocol, Optional, List

from src.domain.value_objects import ProductInfo, ProductWithVariantsInfo


class ProductServicePort(Protocol):

    async def search_products(self, query: str) -> List[ProductInfo]: ...

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]: ...
