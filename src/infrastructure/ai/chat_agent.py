"""PydanticAI-based chat agent implementation for Indonesian steel product assistant."""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel

from src.application.dto import MessageDTO
from src.application.ports import AIAgentPort, ProductServicePort
from src.core.formatting import format_rupiah
from src.infrastructure.ai.prompts.indonesian_templates import (
    ERROR_MESSAGES,
    GREETING_TEMPLATES,
    PRICE_TEMPLATES,
    STOCK_MESSAGES,
)

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

TEMPLATE RESPONSES - GUNAKAN KETIKA SESUAI:
1. Untuk sapaan awal, gunakan variasi waktu:
   - Pagi (05:00-10:59): "Selamat pagi! Saya PERKY..."
   - Siang (11:00-14:59): "Selamat siang! Saya PERKY..."
   - Sore (15:00-18:59): "Selamat sore! Saya PERKY..."
   - Malam/Default: "Halo! Saya PERKY..."

2. Untuk informasi harga varian:
   - Format: "{display_price} per {stock_unit}"
   - Contoh: "Rp 150.000 per lembar"

3. Untuk informasi stok:
   - Stok habis: "Mohon maaf, {variant_name} saat ini sedang kosong."
   - Stok rendah (≤10): "Stok {variant_name} terbatas, tersisa
     {stock_quantity} {stock_unit}."
   - Stok tersedia: "{variant_name} tersedia, stok {stock_quantity} {stock_unit}."

4. Untuk pesan error:
   - Varian tidak ditemukan: "Mohon maaf, {variant_spec} untuk
     {product_name} tidak ditemukan."
   - Error sistem: "Maaf, saya mengalami kendala teknis.
     Silakan hubungi tim sales kami."

CATATAN PENTING TENTANG TEMPLATES:
- Tool responses sudah menyediakan pesan terformat di field
  "_formatted_stock" dan "_formatted_price"
- GUNAKAN pesan terformat tersebut langsung dalam respons Anda
- Jangan format ulang atau ubah pesan yang sudah terformat
- Templates memastikan konsistensi komunikasi profesional

PRINSIP PENTING:
- SELALU gunakan data dari tools, JANGAN mengarang informasi
- GUNAKAN template responses yang sudah terformat dari tool results
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
dengan pemahaman yang jelas tentang struktur produk-varian dan penggunaan
template responses yang konsisten."""


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

    def _create_agent(self) -> Agent[ChatDependencies, str]:
        """Create the PydanticAI agent.

        Note: OpenAIChatModel uses OPENAI_API_KEY from environment automatically.
        """
        model = OpenAIChatModel("gpt-4o-mini")

        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            deps_type=ChatDependencies,
            retries=2,
        )

        return agent

    def _get_greeting(self) -> str:
        """Get appropriate greeting based on time of day."""
        hour = datetime.now().hour

        if 5 <= hour < 11:
            return GREETING_TEMPLATES["morning"]
        elif 11 <= hour < 15:
            return GREETING_TEMPLATES["afternoon"]
        elif 15 <= hour < 19:
            return GREETING_TEMPLATES["evening"]
        else:
            return GREETING_TEMPLATES["default"]

    def _convert_dto_to_model_messages(
        self, conversation_context: List[MessageDTO]
    ) -> list[ModelMessage]:
        """Convert MessageDTO objects to PydanticAI ModelMessage format.

        Args:
            conversation_context: List of MessageDTO from conversation history

        Returns:
            List of ModelMessage objects suitable for PydanticAI agent.run()
        """
        messages: list[ModelMessage] = []

        for msg in conversation_context[-10:]:  # Keep last 10 messages
            try:
                if msg.sender_type == "user":
                    # User message -> ModelRequest with UserPromptPart
                    messages.append(
                        ModelRequest(
                            parts=[
                                UserPromptPart(
                                    content=msg.content,
                                    timestamp=msg.timestamp or datetime.now(),
                                )
                            ]
                        )
                    )
                else:  # ai_agent
                    # AI response -> ModelResponse with TextPart
                    messages.append(
                        ModelResponse(
                            parts=[TextPart(content=msg.content)],
                            timestamp=msg.timestamp or datetime.now(),
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to convert message to ModelMessage format: {e}",
                    exc_info=True,
                )
                # Skip malformed messages rather than failing
                continue

        return messages

    def _format_stock_message(self, variant: Any) -> str:
        """Format stock information using templates."""
        if not variant.has_stock():
            return STOCK_MESSAGES["out_of_stock"].format(
                variant_name=variant.variant_name
            )
        elif variant.stock_quantity <= 10:
            return STOCK_MESSAGES["low_stock"].format(
                variant_name=variant.variant_name,
                stock_quantity=variant.stock_quantity,
                stock_unit=variant.stock_unit,
            )
        else:
            return STOCK_MESSAGES["in_stock"].format(
                variant_name=variant.variant_name,
                stock_quantity=variant.stock_quantity,
                stock_unit=variant.stock_unit,
            )

    def _format_price_message(self, variant: Any) -> str:
        """Format price information using templates."""
        return PRICE_TEMPLATES["unit_price"].format(
            display_price=variant.get_display_price(), stock_unit=variant.stock_unit
        )

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
                    # Create base response
                    specs = variant.specifications.copy()
                    # Add formatted messages to specifications for LLM to use
                    specs["_formatted_stock"] = self._format_stock_message(variant)
                    specs["_formatted_price"] = self._format_price_message(variant)

                    return VariantDetails(
                        variant_id=variant.variant_id,
                        sku=variant.sku,
                        name=variant.variant_name,
                        price=float(variant.price),
                        display_price=variant.get_display_price(),
                        stock_quantity=variant.stock_quantity,
                        stock_unit=variant.stock_unit,
                        specifications=specs,
                        available=variant.has_stock(),
                    )

            # Return empty variant if not found with error message
            return VariantDetails(
                variant_id=variant_id,
                sku="NOT_FOUND",
                name=ERROR_MESSAGES["variant_not_found"].format(
                    variant_spec=variant_id, product_name="Unknown"
                ),
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
                name=ERROR_MESSAGES["system_error"],
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
                    min_p = format_rupiah(min_price)
                    max_p = format_rupiah(max_price)
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
        """Register tools with the agent.

        Note: The tool functions below are decorated with @self.agent.tool,
        which registers them with PydanticAI for dynamic invocation at runtime.
        IDE warnings about "Function not accessed" are false positives - these
        functions are called by the PydanticAI agent framework when needed.
        """

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
            # Simple greeting detection for first message
            if not conversation_context or len(conversation_context) == 0:
                greeting_keywords = ["halo", "hai", "pagi", "siang", "sore"]
                if any(word in message.lower() for word in greeting_keywords):
                    return self._get_greeting()

            # Convert DTOs to PydanticAI ModelMessage format
            message_history = None
            if conversation_context and len(conversation_context) > 0:
                message_history = self._convert_dto_to_model_messages(
                    conversation_context
                )

            # Create dependencies
            deps = ChatDependencies(
                product_service=product_service or self._create_mock_product_service(),
                session_id=session_id or "default",
                user_metadata={},
            )

            # Run the agent with proper message history
            result = await self.agent.run(
                message,
                message_history=message_history,
                deps=deps,
            )

            # Extract response from PydanticAI AgentRunResult
            # Note: PydanticAI returns AgentRunResult with .output attribute, not .data
            response_str: str = (
                result.output if hasattr(result, "output") else str(result)
            )

            logger.debug(
                f"Agent response type: {type(result)}, extracted: {type(response_str)}"
            )

            return response_str

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            # Use template for error message
            return ERROR_MESSAGES["system_error"]

    def _create_mock_product_service(self) -> ProductServicePort:
        """Create a mock product service for testing."""
        from src.infrastructure.mocks.mock_product_repository import (
            MockProductRepository,
        )

        return MockProductRepository()

    @classmethod
    def create_with_fallback(cls) -> AIAgentPort:
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

            mock_agent: AIAgentPort = MockAIAgent()
            return mock_agent
