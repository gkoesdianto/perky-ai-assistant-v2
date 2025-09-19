import random
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from src.application.ports import AIAgentPort
from src.application.dto import MessageDTO


@dataclass
class ResponseMetadata:
    intent: str
    entities: Dict[str, Any]
    confidence: float
    context_used: bool


class MockAIAgent(AIAgentPort):

    def __init__(self):
        self.last_response_metadata: Optional[ResponseMetadata] = None

    async def generate_response(
        self, message: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        message_lower = message.lower()

        intent = self._detect_intent(message_lower)
        entities = self._extract_entities(message_lower)
        context_relevant = self._check_context_relevance(conversation_context, intent)

        response = self._generate_by_intent(intent, entities, message_lower, conversation_context)

        self.last_response_metadata = ResponseMetadata(
            intent=intent,
            entities=entities,
            confidence=random.uniform(0.85, 0.99),
            context_used=context_relevant
        )

        return response

    def _detect_intent(self, message: str) -> str:
        # Check for greetings using word boundaries
        greeting_pattern = r'\b(halo|hello|hi|hai)\b'
        if re.search(greeting_pattern, message, re.IGNORECASE):
            return "greeting"

        # Price takes priority
        if "harga" in message or ("berapa" in message and any(p in message for p in ["biaya", "price"])):
            return "price_inquiry"

        # Check for specific thickness/specs BEFORE stock check
        if any(word in message for word in ["tebal", "ukuran", "dimensi", "spek", "8mm", "10mm", "5mm"]):
            return "specifications"

        # Product listing check
        if "apa saja" in message and "tersedia" in message:
            return "product_listing"

        # Stock check
        if any(word in message for word in ["stok", "stock", "tersedia", "ada"]):
            return "stock_check"

        if "minimal" in message and "pesan" in message:
            return "minimum_order"

        if "diskon" in message or "potongan" in message:
            return "discount_inquiry"

        if "cara pesan" in message or "bagaimana pesan" in message:
            return "order_method"

        if any(word in message for word in ["plat", "hollow", "beam", "pipa"]):
            return "product_inquiry"

        if any(word in message for word in ["pesan", "order", "beli"]):
            return "order_intent"

        return "general"

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

        thickness_pattern = r'\d+\s*mm'
        thickness = re.findall(thickness_pattern, message)
        if thickness:
            entities["thickness"] = thickness

        dimension_pattern = r'\d+x\d+'
        dimensions = re.findall(dimension_pattern, message)
        if dimensions:
            entities["dimensions"] = dimensions

        quantity_pattern = r'\d+\s*(lembar|batang|unit|pcs)'
        quantities = re.findall(quantity_pattern, message)
        if quantities:
            entities["quantities"] = quantities

        return entities

    def _check_context_relevance(self, context: Optional[List[MessageDTO]], intent: str) -> bool:
        if not context:
            return False

        for msg in reversed(context):
            if msg.sender_type == "ai_agent":
                if intent in ["price_inquiry", "stock_check", "minimum_order"]:
                    return any(p in msg.content.lower() for p in ["plat", "hollow", "beam"])
                break

        return False

    def _generate_by_intent(
        self, intent: str, entities: Dict[str, Any], message: str, context: Optional[List[MessageDTO]]
    ) -> str:

        if intent == "greeting":
            return random.choice([
                "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
                "Halo! Saya PERKY, asisten produk baja Anda. Apa yang Anda cari?",
                "Selamat datang! Kami siap membantu kebutuhan material baja Anda.",
                "Halo! Selamat datang di SMS Perkasa. Bagaimana kami bisa membantu Anda hari ini?",
                "Selamat datang! PERKY di sini, siap membantu kebutuhan baja Anda.",
            ])

        elif intent == "product_listing":
            variations = [
                "Kami menyediakan berbagai produk baja untuk kebutuhan Anda:\n• Plat baja dengan berbagai ketebalan\n• Hollow galvanis dan hitam\n• H-Beam/WF untuk konstruksi\n• Pipa baja berbagai ukuran",
                "Tersedia berbagai jenis produk baja:\n• Plat hitam dan galvanis\n• Besi hollow berbagai dimensi\n• H-Beam untuk struktur\n• Pipa baja",
                "Produk yang kami sediakan meliputi:\n• Plat baja (2mm-20mm)\n• Hollow (20x20-100x100)\n• H-Beam berbagai ukuran\n• Pipa baja",
            ]
            response = random.choice(variations)
            closing = random.choice([
                "\nSilakan sebutkan produk yang Anda cari.",
                "\nAda yang Anda butuhkan?",
                "\nProduk mana yang Anda minati?",
            ])
            return response + closing

        elif intent == "price_inquiry":
            products = entities.get("products", [])

            if "hollow" in products or "40x40" in str(entities.get("dimensions", [])):
                prices = [
                    "Untuk harga hollow galvanis 40x40: Rp 85.000/batang",
                    "Hollow galvanis 40x40 kami tawarkan Rp 85.000 per batang",
                    "Harga hollow 40x40: Rp 85.000/batang. Tersedia juga ukuran lain.",
                ]
                base = random.choice(prices)
            elif "plat" in products:
                thickness = entities.get("thickness", ["5mm"])[0] if entities.get("thickness") else "5mm"
                prices = [
                    f"Plat baja {thickness} harganya Rp 125.000 per lembar",
                    f"Untuk plat {thickness}: Rp 125.000/lembar",
                    f"Harga plat {thickness} kami Rp 125.000/lembar",
                ]
                base = random.choice(prices)
            else:
                base = "Harga bervariasi tergantung produk dan spesifikasi"

            if random.random() > 0.5:
                extras = [
                    ". Kami juga ada diskon untuk pembelian banyak.",
                    ". Silakan konfirmasi jumlah yang dibutuhkan.",
                    ". Ada yang ingin Anda pesan?",
                ]
                base += random.choice(extras)

            return base

        elif intent == "stock_check":
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

        elif intent == "specifications":
            thickness = entities.get("thickness", [])

            if "8mm" in str(thickness):
                responses = [
                    "Ya, untuk plat tebal 8mm kami ada ready stock. Ukuran standar 4x8 feet.",
                    "Plat 8mm tersedia dengan ukuran 1200x2400mm. Ready stock.",
                    "Untuk ketebalan 8mm ada stok. Ukuran standar tersedia.",
                ]
            else:
                responses = [
                    "Kami ada berbagai ukuran dan ketebalan. Spesifikasi apa yang Anda cari?",
                    "Tersedia berbagai dimensi. Silakan sebutkan ukuran yang dibutuhkan.",
                    "Ukuran lengkap tersedia. Ada spesifikasi khusus?",
                ]

            return random.choice(responses)

        elif intent == "product_inquiry":
            products = entities.get("products", [])

            if "plat" in products:
                if "5mm" in str(entities.get("thickness", [])):
                    return "Ya, kami ada plat baja 5mm ready stock:\n• Harga: Rp 125.000/lembar\n• Ukuran: 4x8 feet\n• Stok: tersedia"
                else:
                    return "Untuk plat baja, kami memiliki berbagai ketebalan dari 2mm hingga 20mm. Ukuran standar 4x8 feet."

            elif "hollow" in products:
                return "Besi hollow tersedia dalam ukuran 20x20 hingga 100x100. Ada galvanis dan hitam. Panjang standar 6 meter."

            elif "beam" in products or "h-beam" in products:
                return "H-Beam/WF tersedia berbagai ukuran: 100x100, 150x150, 200x200, dll. Semua ready stock."

            else:
                return self._get_product_from_context_response(context)

        elif intent == "minimum_order":
            product_context = self._get_product_from_context(context)

            if "hollow" in product_context:
                responses = [
                    "Minimal order hollow adalah 10 batang per ukuran.",
                    "Untuk hollow, minimal pemesanan 10 batang. Ada diskon untuk quantity besar.",
                    "Hollow minimal 10 batang. Kami berikan harga khusus untuk pembelian banyak.",
                ]
            elif "plat" in product_context:
                responses = [
                    "Minimal order plat baja adalah 5 lembar per ukuran.",
                    "Untuk plat, minimal 5 lembar. Diskon khusus untuk pembelian >20 lembar.",
                    "Plat minimal pemesanan 5 lembar. Ada program diskon quantity.",
                ]
            else:
                responses = [
                    "Minimal order bervariasi: Plat 5 lembar, Hollow 10 batang, H-Beam 5 batang.",
                    "Setiap produk punya minimal berbeda. Silakan tanyakan untuk produk spesifik.",
                    "Minimal pemesanan tergantung produk. Apa yang ingin Anda pesan?",
                ]

            return random.choice(responses)

        elif intent == "discount_inquiry":
            return random.choice([
                "Ya, kami ada program diskon untuk pembelian dalam jumlah banyak. Diskon 5-10% tergantung quantity.",
                "Tersedia diskon untuk pembelian banyak. Silakan hubungi sales untuk penawaran khusus.",
                "Kami berikan diskon menarik untuk pembelian quantity. Detail bisa didiskusikan dengan tim sales.",
            ])

        elif intent == "order_method":
            return random.choice([
                "Untuk pemesanan, Anda bisa hubungi sales kami atau datang langsung ke showroom.",
                "Cara pesan mudah: hubungi tim sales, kami akan buatkan penawaran sesuai kebutuhan.",
                "Silakan pesan melalui sales kami. Kami siap membantu proses pemesanan Anda.",
            ])

        elif intent == "order_intent":
            return random.choice([
                "Baik, untuk pemesanan silakan konfirmasi spesifikasi dan jumlah yang dibutuhkan.",
                "Terima kasih atas minatnya. Mari kita diskusikan detail pesanan Anda.",
                "Siap membantu pemesanan Anda. Mohon informasikan produk dan jumlah yang dibutuhkan.",
            ])

        else:
            return random.choice([
                "Mohon maaf, bisa dijelaskan lebih detail kebutuhan Anda?",
                "Saya perlu informasi lebih spesifik. Produk apa yang Anda cari?",
                "Bisa tolong diperjelas pertanyaan atau kebutuhan Anda?",
            ])

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

    def _get_product_from_context_response(self, context: Optional[List[MessageDTO]]) -> str:
        product = self._get_product_from_context(context)

        if product == "hollow":
            return "Hollow yang Anda tanyakan tersedia dalam berbagai ukuran. Butuh dimensi berapa?"
        elif product == "plat":
            return "Plat baja yang dimaksud tersedia. Butuh ketebalan berapa mm?"
        else:
            return "Produk tersedia. Mohon sebutkan spesifikasi yang Anda butuhkan."

    def get_last_response_metadata(self) -> Optional[ResponseMetadata]:
        return self.last_response_metadata
