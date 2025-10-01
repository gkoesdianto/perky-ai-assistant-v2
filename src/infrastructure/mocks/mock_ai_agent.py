import os
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.application.dto import MessageDTO
from src.application.ports import AIAgentPort
from src.infrastructure.mocks.mock_error_simulator import MockErrorSimulator


@dataclass
class ResponseMetadata:
    intent: str
    entities: Dict[str, Any]
    confidence: float
    context_used: bool


class MockAIAgent(AIAgentPort):
    def __init__(self):
        self.last_response_metadata: Optional[ResponseMetadata] = None

        # Initialize error simulator from environment
        error_rate = float(os.getenv("MOCK_ERROR_RATE", "0.0"))
        delay_ms = int(os.getenv("MOCK_RESPONSE_DELAY_MS", "0"))
        self.error_simulator = MockErrorSimulator(error_rate, delay_ms)

    async def generate_response(
        self, message: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        # Simulate potential errors and delays
        await self.error_simulator.maybe_delay()
        await self.error_simulator.maybe_fail("generate_response")

        message_lower = message.lower()

        intent = self._detect_intent(message_lower)
        entities = self._extract_entities(message_lower)
        context_relevant = self._check_context_relevance(conversation_context, intent)

        response = self._generate_by_intent(
            intent, entities, message_lower, conversation_context
        )

        self.last_response_metadata = ResponseMetadata(
            intent=intent,
            entities=entities,
            confidence=random.uniform(0.85, 0.99),
            context_used=context_relevant,
        )

        return response

    def _detect_intent(self, message: str) -> str:
        """Detect the primary intent from the message."""
        # Check intents in priority order
        if self._is_greeting(message):
            return "greeting"

        if self._is_price_inquiry(message):
            return "price_inquiry"

        if self._is_specification_query(message):
            return "specifications"

        if self._is_product_listing(message):
            return "product_listing"

        # Check stock queries about specific products first
        # "stok plat ada?" or "stock hollow tersedia?" should be stock_check
        if self._is_stock_check(message) and self._is_product_inquiry(message):
            return "stock_check"

        # Check product inquiry before stock check
        # "Ada plat baja 5mm?" should be product inquiry, not just stock check
        if self._is_product_inquiry(message):
            # If asking about specific product with "ada", treat as product inquiry
            return "product_inquiry"

        if self._is_stock_check(message):
            return "stock_check"

        if self._is_order_related(message):
            order_type = self._get_order_intent_type(message)
            if order_type:
                return order_type

        return "general"

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        greeting_pattern = r"\b(halo|hello|hi|hai|selamat\s+(pagi|siang|sore|malam))\b"
        return bool(re.search(greeting_pattern, message, re.IGNORECASE))

    def _is_price_inquiry(self, message: str) -> bool:
        """Check if message is asking about price."""
        return "harga" in message or (
            "berapa" in message and any(p in message for p in ["biaya", "price"])
        )

    def _is_specification_query(self, message: str) -> bool:
        """Check if message is asking about specifications."""
        spec_keywords = ["tebal", "ukuran", "dimensi", "spek", "8mm", "10mm", "5mm"]
        return any(word in message for word in spec_keywords)

    def _is_product_listing(self, message: str) -> bool:
        """Check if message is asking for product listing."""
        return "apa saja" in message and "tersedia" in message

    def _is_stock_check(self, message: str) -> bool:
        """Check if message is asking about stock."""
        stock_keywords = ["stok", "stock", "tersedia", "ada"]
        return any(word in message for word in stock_keywords)

    def _is_order_related(self, message: str) -> bool:
        """Check if message is related to ordering."""
        order_indicators = [
            "minimal",
            "pesan",
            "diskon",
            "potongan",
            "cara pesan",
            "bagaimana pesan",
            "order",
            "beli",
        ]
        return any(word in message for word in order_indicators)

    def _get_order_intent_type(self, message: str) -> Optional[str]:
        """Get specific order-related intent type."""
        if "minimal" in message and "pesan" in message:
            return "minimum_order"
        if "diskon" in message or "potongan" in message:
            return "discount_inquiry"
        if "cara pesan" in message or "bagaimana pesan" in message:
            return "order_method"
        if any(word in message for word in ["pesan", "order", "beli"]):
            return "order_intent"
        return None

    def _is_product_inquiry(self, message: str) -> bool:
        """Check if message is asking about specific products."""
        product_keywords = [
            "plat",
            "hollow",
            "beam",
            "pipa",
            "besi",
            "baja",
            "steel",
            "material",
        ]
        return any(word in message for word in product_keywords)

    def _extract_entities(self, message: str) -> Dict[str, Any]:
        entities = {}

        products = []
        if "plat" in message:
            products.append("plat")
        if "hollow" in message:
            products.append("hollow")
        if "beam" in message or "h-beam" in message:
            products.append("h-beam")
        if "pipa" in message:
            products.append("pipa")

        if products:
            entities["products"] = products

        thickness_pattern = r"\d+\s*mm"
        thickness = re.findall(thickness_pattern, message)
        if thickness:
            entities["thickness"] = thickness

        dimension_pattern = r"\d+x\d+"
        dimensions = re.findall(dimension_pattern, message)
        if dimensions:
            entities["dimensions"] = dimensions

        quantity_pattern = r"\d+\s*(lembar|batang|unit|pcs)"
        quantities = re.findall(quantity_pattern, message)
        if quantities:
            entities["quantities"] = quantities

        return entities

    def _check_context_relevance(
        self, context: Optional[List[MessageDTO]], intent: str
    ) -> bool:
        if not context:
            return False

        for msg in reversed(context):
            if msg.sender_type == "ai_agent":
                if intent in ["price_inquiry", "stock_check", "minimum_order"]:
                    return any(
                        p in msg.content.lower() for p in ["plat", "hollow", "beam"]
                    )
                break

        return False

    def _generate_by_intent(
        self,
        intent: str,
        entities: Dict[str, Any],
        message: str,
        context: Optional[List[MessageDTO]],
    ) -> str:
        """Generate response based on detected intent."""
        response_methods = {
            "greeting": self._generate_greeting_response,
            "product_listing": self._generate_product_listing_response,
            "price_inquiry": self._generate_price_response,
            "stock_check": self._generate_stock_response,
            "specifications": self._generate_specifications_response,
            "product_inquiry": self._generate_product_inquiry_response,
            "minimum_order": self._generate_minimum_order_response,
            "discount_inquiry": self._generate_discount_response,
            "order_method": self._generate_order_method_response,
            "order_intent": self._generate_order_intent_response,
        }

        method = response_methods.get(intent)
        if method:
            return method(entities, context)

        return self._generate_default_response()

    def _generate_greeting_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate greeting response."""
        return random.choice(
            [
                "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
                "Halo! Saya PERKY, asisten produk baja Anda. Apa yang Anda cari?",
                (
                    "Selamat datang di SMS Perkasa! "
                    "Kami siap membantu kebutuhan material baja Anda."
                ),
                (
                    "Halo! Selamat datang di SMS Perkasa. "
                    "Bagaimana kami bisa membantu Anda hari ini?"
                ),
                "Selamat datang! PERKY di sini, siap membantu kebutuhan baja Anda.",
            ]
        )

    def _generate_product_listing_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate product listing response."""
        variations = [
            "Kami menyediakan berbagai produk baja untuk kebutuhan Anda:\n"
            "• Plat baja dengan berbagai ketebalan\n• Hollow galvanis dan hitam\n"
            "• H-Beam/WF untuk konstruksi\n• Pipa baja berbagai ukuran",
            "Tersedia berbagai jenis produk baja:\n• Plat hitam dan galvanis\n"
            "• Besi hollow berbagai dimensi\n• H-Beam untuk struktur\n• Pipa baja",
            "Produk yang kami sediakan meliputi:\n• Plat baja (2mm-20mm)\n"
            "• Hollow (20x20-100x100)\n• H-Beam berbagai ukuran\n• Pipa baja",
        ]
        response = random.choice(variations)
        closing = random.choice(
            [
                "\nSilakan sebutkan produk yang Anda cari.",
                "\nAda yang Anda butuhkan?",
                "\nProduk mana yang Anda minati?",
            ]
        )
        return response + closing

    def _generate_price_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate price inquiry response."""
        products = entities.get("products", [])

        # If no products in current message, check context
        if not products and context:
            product_from_context = self._get_product_from_context(context)
            if product_from_context:
                products = [product_from_context]

        if "hollow" in products or "40x40" in str(entities.get("dimensions", [])):
            prices = [
                "Untuk harga hollow galvanis 40x40: Rp 85.000/batang",
                "Hollow galvanis 40x40 kami tawarkan Rp 85.000 per batang",
                "Harga hollow 40x40: Rp 85.000/batang. Tersedia juga ukuran lain.",
            ]
            base = random.choice(prices)
        elif "plat" in products:
            thickness = (
                entities.get("thickness", ["5mm"])[0]
                if entities.get("thickness")
                else "5mm"
            )
            prices = [
                f"Plat baja {thickness} harganya Rp 125.000 per lembar",
                f"Untuk plat {thickness}: Rp 125.000/lembar",
                f"Harga plat {thickness} kami Rp 125.000/lembar",
            ]
            base = random.choice(prices)
        else:
            # Provide generic price response with contact info
            base = random.choice(
                [
                    "Untuk informasi harga terbaru, " "silakan hubungi tim sales kami",
                    "Harga bervariasi tergantung spesifikasi. "
                    "Hubungi kami untuk penawaran terbaik",
                    "Kami berikan harga kompetitif. "
                    "Silakan kontak sales untuk detail",
                ]
            )

        if random.random() > 0.5:
            extras = [
                ". Kami juga ada diskon untuk pembelian banyak.",
                ". Silakan konfirmasi jumlah yang dibutuhkan.",
                ". Ada yang ingin Anda pesan?",
            ]
            base += random.choice(extras)

        return base

    def _generate_stock_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate stock check response."""
        products = entities.get("products", [])

        if products:
            product = products[0]
            responses = [
                f"Stok {product} tersedia dan ready untuk dikirim",
                f"{product.title()} ready stock di gudang kami",
                f"Ya, {product} ada stok dengan jumlah mencukupi",
            ]
        else:
            responses = [
                "Stok produk kami update real-time dan sebagian besar ready",
                "Kami memiliki stok yang cukup untuk berbagai produk",
                "Sebagian besar produk tersedia dan siap kirim",
            ]

        return random.choice(responses)

    def _generate_specifications_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate specifications response."""
        thickness = entities.get("thickness", [])

        if "8mm" in str(thickness):
            responses = [
                (
                    "Ya, untuk plat tebal 8mm kami ada ready stock. "
                    "Ukuran standar 4x8 feet."
                ),
                "Plat 8mm tersedia dengan ukuran 1200x2400mm. Ready stock.",
                "Untuk ketebalan 8mm ada stok. Ukuran standar tersedia.",
            ]
        else:
            responses = [
                "Kami ada berbagai ukuran dan ketebalan. "
                "Spesifikasi apa yang Anda cari?",
                "Tersedia berbagai dimensi. "
                "Silakan sebutkan ukuran yang dibutuhkan.",
                "Ukuran lengkap tersedia. Ada spesifikasi khusus?",
            ]

        return random.choice(responses)

    def _generate_product_inquiry_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate product inquiry response."""
        products = entities.get("products", [])

        if "plat" in products:
            if "5mm" in str(entities.get("thickness", [])):
                return (
                    "Ya, kami ada plat baja 5mm ready stock:\n"
                    "• Harga: Rp 125.000/lembar\n• Ukuran: 4x8 feet\n• Stok: tersedia"
                )
            else:
                return (
                    "Untuk plat baja, kami memiliki berbagai ketebalan "
                    "dari 2mm hingga 20mm. Ukuran standar 4x8 feet."
                )

        elif "hollow" in products:
            return (
                "Besi hollow tersedia dalam ukuran 20x20 hingga 100x100. "
                "Ada galvanis dan hitam. Panjang standar 6 meter."
            )

        elif "beam" in products or "h-beam" in products:
            return (
                "H-Beam/WF tersedia berbagai ukuran: "
                "100x100, 150x150, 200x200, dll. Semua ready stock."
            )

        else:
            return self._get_product_from_context_response(context)

    def _generate_minimum_order_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate minimum order response."""
        product_context = self._get_product_from_context(context)

        if "hollow" in product_context:
            responses = [
                "Minimal order hollow adalah 10 batang per ukuran.",
                (
                    "Untuk hollow, minimal pemesanan 10 batang. "
                    "Ada diskon untuk quantity besar."
                ),
                (
                    "Hollow minimal 10 batang. "
                    "Kami berikan harga khusus untuk pembelian banyak."
                ),
            ]
        elif "plat" in product_context:
            responses = [
                "Minimal order plat baja adalah 5 lembar per ukuran.",
                (
                    "Untuk plat, minimal 5 lembar. "
                    "Diskon khusus untuk pembelian >20 lembar."
                ),
                "Plat minimal pemesanan 5 lembar. Ada program diskon quantity.",
            ]
        else:
            responses = [
                (
                    "Minimal order bervariasi: "
                    "Plat 5 lembar, Hollow 10 batang, H-Beam 5 batang."
                ),
                (
                    "Setiap produk punya minimal berbeda. "
                    "Silakan tanyakan untuk produk spesifik."
                ),
                "Minimal pemesanan tergantung produk. Apa yang ingin Anda pesan?",
            ]

        return random.choice(responses)

    def _generate_discount_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate discount inquiry response."""
        return random.choice(
            [
                "Ya, kami ada program diskon untuk pembelian dalam jumlah banyak. "
                "Diskon 5-10% tergantung quantity.",
                "Tersedia diskon untuk pembelian banyak. "
                "Silakan hubungi sales untuk penawaran khusus.",
                "Kami berikan diskon menarik untuk pembelian quantity. "
                "Detail bisa didiskusikan dengan tim sales.",
            ]
        )

    def _generate_order_method_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate order method response."""
        return random.choice(
            [
                (
                    "Untuk pemesanan, Anda bisa hubungi sales kami "
                    "atau datang langsung ke showroom."
                ),
                (
                    "Cara pesan mudah: hubungi tim sales, "
                    "kami akan buatkan penawaran sesuai kebutuhan."
                ),
                (
                    "Silakan pesan melalui sales kami. "
                    "Kami siap membantu proses pemesanan Anda."
                ),
            ]
        )

    def _generate_order_intent_response(
        self, entities: Dict[str, Any], context: Optional[List[MessageDTO]]
    ) -> str:
        """Generate order intent response."""
        return random.choice(
            [
                (
                    "Baik, untuk pemesanan silakan konfirmasi "
                    "spesifikasi dan jumlah yang dibutuhkan."
                ),
                "Terima kasih atas minatnya. Mari kita diskusikan detail pesanan Anda.",
                (
                    "Siap membantu pemesanan Anda. "
                    "Mohon informasikan produk dan jumlah yang dibutuhkan."
                ),
            ]
        )

    def _generate_default_response(self) -> str:
        """Generate default response for unmatched intents."""
        return random.choice(
            [
                "Mohon maaf, bisa dijelaskan lebih detail kebutuhan Anda?",
                ("Saya perlu informasi lebih spesifik. " "Produk apa yang Anda cari?"),
                "Bisa tolong diperjelas pertanyaan atau kebutuhan Anda?",
            ]
        )

    def _get_product_from_context(self, context: Optional[List[MessageDTO]]) -> str:
        if not context:
            return ""

        for msg in reversed(context[-4:]):
            content = msg.content.lower()
            if "hollow" in content:
                return "hollow"
            elif "plat" in content:
                return "plat"
            elif "beam" in content:
                return "h-beam"

        return ""

    def _get_product_from_context_response(
        self, context: Optional[List[MessageDTO]]
    ) -> str:
        product = self._get_product_from_context(context)

        if product == "hollow":
            return (
                "Hollow yang Anda tanyakan tersedia dalam berbagai ukuran. "
                "Butuh dimensi berapa?"
            )
        elif product == "plat":
            return "Plat baja yang dimaksud tersedia. Butuh ketebalan berapa mm?"
        else:
            return "Produk tersedia. Mohon sebutkan spesifikasi yang Anda butuhkan."

    def get_last_response_metadata(self) -> Optional[ResponseMetadata]:
        return self.last_response_metadata
