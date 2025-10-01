from dataclasses import dataclass
from typing import Any, Dict, List, Literal


@dataclass
class ProductQueryDTO:
    query: str
    session_id: str
    include_variants: bool = True
    max_results: int = 10


@dataclass
class ProductResponseDTO:
    products: List[Dict[str, Any]]
    query: str
    response_time_ms: int
    source: Literal["pim", "cache", "mock"]
