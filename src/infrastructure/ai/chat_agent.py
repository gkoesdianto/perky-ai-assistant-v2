"""PydanticAI-based chat agent implementation for Indonesian steel product assistant."""

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel

from src.application.dto import MessageDTO
from src.application.ports import AIAgentPort, ProductServicePort

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


# Indonesian language system prompt - behavioral only, no hardcoded data
SYSTEM_PROMPT = """Kamu adalah PERKY, asisten virtual untuk SMS Perkasa yang membantu
pelanggan B2B menemukan produk baja yang tepat.

IDENTITAS:
- Nama: PERKY (Perkasa Assistant)
- Perusahaan: SMS Perkasa Steel
- Fokus: Produk baja untuk konstruksi dan industri

KEPRIBADIAN:
- Profesional namun ramah
- Membantu dan informatif
- Proaktif dalam memberikan saran
- Responsif terhadap kebutuhan pelanggan B2B

KONSEP PRODUK PENTING:
1. PRODUK adalah kategori umum (contoh: "Plat Baja", "Hollow", "H-Beam")
2. VARIAN adalah item spesifik yang dijual dengan SKU, harga, dan stok
   (contoh: "Plat Baja 5mm x 1200mm x 2400mm" adalah varian dari produk "Plat Baja")
3. Harga dan stok SELALU ada di level varian, BUKAN di level produk
4. Satu produk bisa memiliki banyak varian dengan ukuran/spesifikasi berbeda

CARA KERJA:
1. Dengarkan kebutuhan pelanggan dengan seksama
2. Gunakan tools yang tersedia untuk:
   - Mencari produk berdasarkan kategori (search_products)
   - Mendapatkan semua varian dari suatu produk (get_product_variants)
   - Mendapatkan detail varian spesifik (get_variant_details)
   - Mengecek stok varian (check_variant_stock)
3. Berikan informasi akurat tentang:
   - Kategori produk yang tersedia
   - Varian spesifik dengan ukuran/spesifikasi
   - Harga per varian (bukan harga produk umum)
   - Stok per varian
4. Jangan mengarang informasi produk, harga, atau stok
5. Jika informasi tidak tersedia, arahkan ke tim sales

PANDUAN KOMUNIKASI:
1. Selalu sapa dengan ramah dan profesional
2. Tanyakan kebutuhan spesifik pelanggan:
   - Jenis produk yang dicari (kategori umum)
   - Spesifikasi yang dibutuhkan (untuk menentukan varian)
   - Jumlah/volume yang diperlukan
   - Timeline penggunaan
3. Ketika pelanggan menyebut produk umum:
   - Tampilkan varian-varian yang tersedia
   - Tanyakan spesifikasi mana yang sesuai kebutuhan
   - Berikan harga dan stok per varian
4. Berikan rekomendasi berdasarkan:
   - Data produk dan varian aktual dari sistem
   - Ketersediaan stok real-time per varian
   - Harga terkini per varian
5. Jika produk tidak ditemukan:
   - Minta klarifikasi kebutuhan
   - Tawarkan alternatif serupa
   - Arahkan ke tim sales untuk produk custom
6. Akhiri dengan tawaran bantuan lebih lanjut

PRINSIP PENTING:
- SELALU gunakan data dari tools, JANGAN mengarang informasi
- Bedakan dengan jelas antara produk (kategori) dan varian (item spesifik)
- Harga dan stok HANYA ada di level varian
- Jika tools gagal atau data tidak tersedia, jujur kepada pelanggan
- Fokus pada membantu pelanggan menemukan varian yang tepat
- Gunakan Bahasa Indonesia yang profesional dan mudah dipahami

LAYANAN YANG DAPAT DITAWARKAN (jika tersedia di sistem):
- Pemotongan sesuai ukuran
- Pengiriman ke lokasi proyek
- Konsultasi teknis
- Sertifikat mill test

Ingat: Kamu adalah asisten yang membantu berdasarkan data real dari sistem,
dengan pemahaman yang jelas tentang struktur produk-varian."""


@dataclass
class ChatDependencies:
    """Dependencies for the chat agent."""

    product_service: ProductServicePort
    session_id: str
    user_metadata: Optional[Dict[str, Any]] = None


class ProductSearchResult(BaseModel):
    """Result from product search tool."""

    products: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of product categories found"
    )
    query: str = Field(description="Original search query")
    count: int = Field(default=0, description="Number of products found")
    success: bool = Field(default=True, description="Whether the search was successful")
    message: Optional[str] = Field(
        default=None, description="Error or status message if any"
    )


class VariantSearchResult(BaseModel):
    """Result from variant search for a product."""

    product_name: str = Field(description="Name of the product category")
    variants: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of variants with details"
    )
    count: int = Field(default=0, description="Number of variants found")
    price_range: Optional[str] = Field(
        default=None, description="Price range across variants"
    )
    total_stock: int = Field(default=0, description="Total stock across all variants")


class VariantDetails(BaseModel):
    """Detailed variant information."""

    variant_id: str = Field(description="Variant ID")
    sku: str = Field(description="SKU code")
    name: str = Field(description="Variant name with specifications")
    price: float = Field(description="Current price in IDR")
    display_price: str = Field(description="Formatted price")
    stock_quantity: int = Field(default=0, description="Available stock")
    stock_unit: str = Field(description="Stock unit (lembar, batang, etc)")
    specifications: Dict[str, Any] = Field(
        default_factory=dict, description="Technical specifications"
    )
    available: bool = Field(default=True, description="Whether variant is available")


class StockCheckResult(BaseModel):
    """Result from stock availability check."""

    variants: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Variant ID to stock info mapping"
    )
    checked_at: str = Field(description="Timestamp of check")
    success: bool = Field(default=True, description="Whether check succeeded")


class ChatAgent(AIAgentPort):
    """PydanticAI-based chat agent for Indonesian steel products."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat agent.

        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var.
        """
        # If api_key is provided explicitly, set it in environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Check that API key exists in environment
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key is required")

        # Initialize the PydanticAI agent
        self.agent = self._create_agent()

        # Register tools
        self._register_tools()

        logger.info("ChatAgent initialized with PydanticAI")

    def _create_agent(self) -> Agent:
        """Create the PydanticAI agent.

        Note: OpenAIChatModel uses OPENAI_API_KEY from environment automatically.
        """
        model = OpenAIChatModel("gpt-4o-mini")

        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            deps_type=ChatDependencies,
            result_type=str,
            retries=2,
        )

        return agent

    async def _search_products_tool(
        self, ctx: RunContext[ChatDependencies], query: str
    ) -> ProductSearchResult:
        """Search for steel product categories based on query."""
        try:
            # Search for products (categories)
            products = await ctx.deps.product_service.search_products(query)

            product_list = []
            for product in products:
                product_data = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "description": product.product_description,
                    "category": product.category,
                    "variant_count": product.variant_count,
                }
                product_list.append(product_data)

            return ProductSearchResult(
                products=product_list,
                query=query,
                count=len(product_list),
                success=True,
            )
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return ProductSearchResult(
                products=[],
                query=query,
                count=0,
                success=False,
                message=f"Error searching products: {str(e)}",
            )

    async def _get_variant_details_tool(
        self, ctx: RunContext[ChatDependencies], product_id: str, variant_id: str
    ) -> VariantDetails:
        """Get detailed information about a specific variant."""
        try:
            product_with_variants = (
                await ctx.deps.product_service.get_product_with_variants(product_id)
            )

            if product_with_variants:
                variant = product_with_variants.get_variant_by_id(variant_id)
                if variant:
                    return VariantDetails(
                        variant_id=variant.variant_id,
                        sku=variant.sku,
                        name=variant.variant_name,
                        price=float(variant.price),
                        display_price=variant.get_display_price(),
                        stock_quantity=variant.stock_quantity,
                        stock_unit=variant.stock_unit,
                        specifications=variant.specifications,
                        available=variant.has_stock(),
                    )

            # Return empty variant if not found
            return VariantDetails(
                variant_id=variant_id,
                sku="NOT_FOUND",
                name="Variant not found",
                price=0.0,
                display_price="Rp 0",
                stock_quantity=0,
                stock_unit="unit",
                available=False,
            )
        except Exception as e:
            logger.error(f"Error getting variant details: {e}")
            return VariantDetails(
                variant_id=variant_id,
                sku="ERROR",
                name="Error retrieving variant",
                price=0.0,
                display_price="Rp 0",
                stock_quantity=0,
                stock_unit="unit",
                available=False,
            )

    async def _check_variant_stock_tool(
        self, ctx: RunContext[ChatDependencies], product_id: str, variant_ids: List[str]
    ) -> StockCheckResult:
        """Check stock availability for specific variants."""
        from datetime import datetime

        try:
            stock_info = {}
            product_with_variants = (
                await ctx.deps.product_service.get_product_with_variants(product_id)
            )

            if product_with_variants:
                for variant_id in variant_ids:
                    variant = product_with_variants.get_variant_by_id(variant_id)
                    if variant:
                        stock_info[variant_id] = {
                            "sku": variant.sku,
                            "name": variant.variant_name,
                            "stock": variant.stock_quantity,
                            "unit": variant.stock_unit,
                            "available": variant.has_stock(),
                        }
                    else:
                        stock_info[variant_id] = {
                            "sku": "NOT_FOUND",
                            "name": "Variant not found",
                            "stock": 0,
                            "unit": "unit",
                            "available": False,
                        }

            return StockCheckResult(
                variants=stock_info,
                checked_at=datetime.now().isoformat(),
                success=True,
            )
        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            return StockCheckResult(
                variants={}, checked_at=datetime.now().isoformat(), success=False
            )

    async def _find_variants_by_specification_tool(
        self,
        ctx: RunContext[ChatDependencies],
        product_id: str,
        specifications: Dict[str, Any],
    ) -> VariantSearchResult:
        """Find variants that match specific specifications."""
        try:
            product_with_variants = (
                await ctx.deps.product_service.get_product_with_variants(product_id)
            )

            if not product_with_variants:
                return VariantSearchResult(
                    product_name="Unknown", variants=[], count=0, total_stock=0
                )

            # Find matching variants
            matching_variants = product_with_variants.get_variants_by_attributes(
                specifications
            )

            variants = []
            total_stock = 0
            for variant in matching_variants:
                variant_data = {
                    "variant_id": variant.variant_id,
                    "sku": variant.sku,
                    "name": variant.variant_name,
                    "price": float(variant.price),
                    "display_price": variant.get_display_price(),
                    "stock": variant.stock_quantity,
                    "stock_unit": variant.stock_unit,
                    "available": variant.has_stock(),
                    "specifications": variant.specifications,
                }
                variants.append(variant_data)
                total_stock += variant.stock_quantity

            # Calculate price range for matching variants
            if matching_variants:
                prices = [v.price for v in matching_variants]
                min_price = min(prices)
                max_price = max(prices)
                if min_price == max_price:
                    price_range = matching_variants[0].get_display_price()
                else:
                    min_p = self._format_rupiah(min_price)
                    max_p = self._format_rupiah(max_price)
                    price_range = f"{min_p} - {max_p}"
            else:
                price_range = None

            return VariantSearchResult(
                product_name=product_with_variants.product.product_name,
                variants=variants,
                count=len(variants),
                price_range=price_range,
                total_stock=total_stock,
            )
        except Exception as e:
            logger.error(f"Error finding variants by specification: {e}")
            return VariantSearchResult(
                product_name="Error", variants=[], count=0, total_stock=0
            )

    async def _get_product_variants_tool(
        self, ctx: RunContext[ChatDependencies], product_id: str
    ) -> VariantSearchResult:
        """Get all variants for a specific product category."""
        try:
            # Get product with all its variants
            product_with_variants = (
                await ctx.deps.product_service.get_product_with_variants(product_id)
            )

            if not product_with_variants:
                return VariantSearchResult(
                    product_name="Unknown", variants=[], count=0, total_stock=0
                )

            # Extract variant information
            variants = []
            for variant in product_with_variants.variants:
                variant_data = {
                    "variant_id": variant.variant_id,
                    "sku": variant.sku,
                    "name": variant.variant_name,
                    "price": float(variant.price),
                    "display_price": variant.get_display_price(),
                    "stock": variant.stock_quantity,
                    "stock_unit": variant.stock_unit,
                    "available": variant.has_stock(),
                    "specifications": variant.specifications,
                }
                variants.append(variant_data)

            return VariantSearchResult(
                product_name=product_with_variants.product.product_name,
                variants=variants,
                count=len(variants),
                price_range=product_with_variants.get_price_display_range(),
                total_stock=product_with_variants.get_total_stock(),
            )
        except Exception as e:
            logger.error(f"Error getting product variants: {e}")
            return VariantSearchResult(
                product_name="Error", variants=[], count=0, total_stock=0
            )

    def _register_tools(self):
        """Register tools with the agent."""

        @self.agent.tool
        async def search_products(
            ctx: RunContext[ChatDependencies], query: str
        ) -> ProductSearchResult:
            """Search for steel product categories based on query.

            This returns product categories (like "Plat Baja", "Hollow"),
            NOT specific variants. Use get_product_variants to see specific items.

            Args:
                ctx: Run context with dependencies
                query: Search query in Indonesian

            Returns:
                ProductSearchResult with found product categories
            """
            return await self._search_products_tool(ctx, query)

        @self.agent.tool
        async def get_product_variants(
            ctx: RunContext[ChatDependencies], product_id: str
        ) -> VariantSearchResult:
            """Get all variants for a specific product category.

            This returns specific sellable items (variants) with prices and stock.
            For example, for product "Plat Baja", returns all thickness/size combos.

            Args:
                ctx: Run context with dependencies
                product_id: Product identifier

            Returns:
                VariantSearchResult with all variants of the product
            """
            return await self._get_product_variants_tool(ctx, product_id)

        @self.agent.tool
        async def get_variant_details(
            ctx: RunContext[ChatDependencies], product_id: str, variant_id: str
        ) -> VariantDetails:
            """Get detailed information about a specific variant.

            This returns complete details for a specific sellable item including
            current price, stock, and specifications.

            Args:
                ctx: Run context with dependencies
                product_id: Product identifier
                variant_id: Variant identifier

            Returns:
                VariantDetails with complete variant information
            """
            return await self._get_variant_details_tool(ctx, product_id, variant_id)

        @self.agent.tool
        async def check_variant_stock(
            ctx: RunContext[ChatDependencies], product_id: str, variant_ids: List[str]
        ) -> StockCheckResult:
            """Check stock availability for specific variants.

            This checks current stock levels for specific variant IDs.
            Remember: stock is at variant level, not product level.

            Args:
                ctx: Run context with dependencies
                product_id: Product identifier
                variant_ids: List of variant identifiers to check

            Returns:
                StockCheckResult with current stock levels
            """
            return await self._check_variant_stock_tool(ctx, product_id, variant_ids)

        @self.agent.tool
        async def find_variants_by_specification(
            ctx: RunContext[ChatDependencies],
            product_id: str,
            specifications: Dict[str, Any],
        ) -> VariantSearchResult:
            """Find variants that match specific specifications.

            For example, find all "Plat Baja" variants with thickness "5mm".

            Args:
                ctx: Run context with dependencies
                product_id: Product identifier
                specifications: Specifications to match (e.g., {"thickness": "5mm"})

            Returns:
                VariantSearchResult with matching variants
            """
            return await self._find_variants_by_specification_tool(
                ctx, product_id, specifications
            )

    def _format_rupiah(self, amount: Decimal) -> str:
        """Format amount as Indonesian Rupiah."""
        price_str = f"{amount:.0f}"
        formatted = ""
        for i, digit in enumerate(reversed(price_str)):
            if i > 0 and i % 3 == 0:
                formatted = "." + formatted
            formatted = digit + formatted
        return f"Rp {formatted}"

    async def generate_response(
        self,
        message: str,
        conversation_context: Optional[List[MessageDTO]] = None,
        product_service: Optional[ProductServicePort] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate a response using the PydanticAI agent.

        Args:
            message: User message
            conversation_context: Previous messages in the conversation
            product_service: Product service for searching products
            session_id: Session identifier

        Returns:
            AI-generated response in Indonesian
        """
        try:
            # Build conversation history for the agent
            messages = []
            if conversation_context:
                for msg in conversation_context[-10:]:  # Last 10 messages for context
                    if msg.sender_type == "user":
                        messages.append(("user", msg.content))
                    else:
                        messages.append(("assistant", msg.content))

            # Add current message
            messages.append(("user", message))

            # Create dependencies
            deps = ChatDependencies(
                product_service=product_service or self._create_mock_product_service(),
                session_id=session_id or "default",
                user_metadata={},
            )

            # Run the agent
            result = await self.agent.run(
                message,
                message_history=messages[
                    :-1
                ],  # Don't include current message in history
                deps=deps,
            )

            # Extract response
            response = result.data if hasattr(result, "data") else str(result)

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback response in Indonesian
            return (
                "Mohon maaf, saya mengalami kesulitan memproses permintaan Anda. "
                "Silakan coba lagi atau hubungi tim sales kami."
            )

    def _create_mock_product_service(self) -> ProductServicePort:
        """Create a mock product service for testing."""
        from src.infrastructure.mocks.mock_product_repository import (
            MockProductRepository,
        )

        return MockProductRepository()

    @classmethod
    def create_with_fallback(cls) -> "ChatAgent":
        """Create a ChatAgent with fallback to mock if API key not available.

        Returns:
            ChatAgent instance or MockAIAgent if API key not configured
        """
        try:
            return cls()
        except ValueError as e:
            logger.warning(
                f"Failed to create ChatAgent: {e}. Using MockAIAgent instead."
            )
            from src.infrastructure.mocks.mock_ai_agent import MockAIAgent

            return MockAIAgent()
