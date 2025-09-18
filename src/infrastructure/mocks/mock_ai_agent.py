import random
from typing import List, Optional
from src.application.ports import AIAgentPort
from src.application.dto import MessageDTO


class MockAIAgent(AIAgentPort):

    RESPONSES = {
        "greeting": [
            "Selamat datang di SMS Perkasa! Ada yang bisa saya bantu?",
            "Halo! Saya PERKY, asisten produk baja Anda. Apa yang Anda cari?",
        ],
        "product_plat": [
            "Untuk plat baja, kami memiliki:\n"
            "• Plat hitam SS400: 2mm-20mm\n"
            "• Plat galvanis: 0.8mm-3mm\n"
            "• Plat bordes: 3mm-6mm\n"
            "Ukuran standar 4x8 feet. Ada spesifikasi khusus?"
        ],
        "product_hollow": [
            "Besi hollow tersedia dalam:\n"
            "• Hollow galvanis: 20x20 hingga 100x100\n"
            "• Hollow hitam: ukuran sama\n"
            "• Ketebalan: 1.2mm - 3.2mm\n"
            "Panjang standar 6 meter. Butuh ukuran apa?"
        ],
        "price_inquiry": [
            "Harga terkini produk baja:\n"
            "• Plat hitam 5mm: Rp 125.000/lembar\n"
            "• Hollow galvanis 40x40: Rp 85.000/batang\n"
            "Harga dapat berubah sewaktu-waktu. Mau pesan?"
        ],
        "stock_check": [
            "Stok produk saat ini:\n"
            "• Plat hitam 5mm: 150 lembar\n"
            "• Hollow galvanis 40x40: 200 batang\n"
            "Stok update realtime. Butuh berapa unit?"
        ],
        "order_flow": [
            "Untuk pemesanan:\n"
            "1. Tentukan spesifikasi\n"
            "2. Konfirmasi jumlah\n"
            "3. Kami siapkan penawaran\n"
            "Silakan sebutkan jumlah yang dibutuhkan."
        ],
        "default": [
            "Mohon maaf, bisa tolong lebih spesifik produk yang Anda cari?",
            "Saya perlu informasi lebih detail. Produk apa yang Anda butuhkan?",
            "Maaf, bisa ulangi pertanyaan Anda dengan lebih jelas?",
        ],
    }

    PROFESSIONAL_TEMPLATES = {
        "confirmation": "Baik, saya catat kebutuhan Anda: {requirement}",
        "clarification": "Mohon info lebih detail mengenai {aspect}",
        "recommendation": "Berdasarkan kebutuhan Anda, saya rekomendasikan {product}",
        "next_step": "Langkah selanjutnya: {action}",
        "closing": "Terima kasih. Tim sales kami akan follow up segera.",
    }

    async def generate_response(
        self, message: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:

        message_lower = message.lower()

        # Greeting detection - check first to avoid conflict
        if self._is_greeting(message_lower):
            return random.choice(self.RESPONSES["greeting"])

        # Price inquiry
        price_response = self._check_price_inquiry(message_lower)
        if price_response:
            return price_response

        # Stock availability
        stock_response = self._check_stock_inquiry(message_lower)
        if stock_response:
            return stock_response

        # Product inquiry
        product_response = self._check_product_inquiry(message_lower)
        if product_response:
            return product_response

        # Order process
        if self._is_order_request(message_lower):
            return random.choice(self.RESPONSES["order_flow"])

        # Context-aware response
        if conversation_context:
            return self._generate_contextual_response(
                message_lower, conversation_context
            )

        # Default response
        return random.choice(self.RESPONSES["default"])

    def _is_greeting(self, message: str) -> bool:
        greeting_words = [
            "halo",
            "hello",
            "hi",
            "selamat",
            "pagi",
            "siang",
            "sore",
            "malam",
            "hai",
            "hey",
        ]
        # Use word boundaries to avoid false matches
        words = message.split()
        return any(word in greeting_words for word in words) or message.startswith(
            "selamat"
        )

    def _check_price_inquiry(self, message_lower: str) -> Optional[str]:
        """Check if message is a price inquiry and return appropriate response."""
        price_keywords = ["harga", "price", "berapa", "cost", "biaya"]
        product_keywords = ["plat", "hollow", "besi", "pipa"]

        if not any(word in message_lower for word in price_keywords):
            return None

        # Check if it's about specific products
        has_product = any(prod in message_lower for prod in product_keywords)
        if "plat" in message_lower or "hollow" in message_lower or not has_product:
            return random.choice(self.RESPONSES["price_inquiry"])

        return None

    def _check_stock_inquiry(self, message_lower: str) -> Optional[str]:
        """Check if message is a stock inquiry and return appropriate response."""
        stock_keywords = ["stok", "stock", "tersedia", "ada", "available"]
        product_keywords = ["plat", "hollow", "besi", "pipa"]

        if not any(word in message_lower for word in stock_keywords):
            return None

        # Check if it's about specific products
        has_product = any(prod in message_lower for prod in product_keywords)
        if "plat" in message_lower or "hollow" in message_lower or not has_product:
            return random.choice(self.RESPONSES["stock_check"])

        return None

    def _check_product_inquiry(self, message_lower: str) -> Optional[str]:
        """Check if message is a product inquiry and return appropriate response."""
        if "plat" in message_lower or "plate" in message_lower:
            return random.choice(self.RESPONSES["product_plat"])

        if "hollow" in message_lower or "kotak" in message_lower:
            return random.choice(self.RESPONSES["product_hollow"])

        return None

    def _is_order_request(self, message_lower: str) -> bool:
        """Check if message is an order request."""
        order_keywords = ["pesan", "order", "beli", "purchase"]
        return any(word in message_lower for word in order_keywords)

    def _generate_contextual_response(
        self, message: str, conversation_context: List[MessageDTO]
    ) -> str:

        # Check if user is following up on a product inquiry
        if conversation_context:
            last_message = conversation_context[-1] if conversation_context else None

            if last_message and last_message.sender_type == "ai_agent":
                # Check if last AI message was about products
                if "plat" in last_message.content.lower():
                    if any(word in message for word in ["5mm", "10mm", "15mm", "20mm"]):
                        return self.PROFESSIONAL_TEMPLATES["confirmation"].format(
                            requirement=f"plat baja {message}"
                        )

                if "hollow" in last_message.content.lower():
                    if any(
                        word in message for word in ["40x40", "50x50", "60x60", "20x20"]
                    ):
                        return self.PROFESSIONAL_TEMPLATES["confirmation"].format(
                            requirement=f"hollow {message}"
                        )

            # Check for quantity mentions
            if any(char.isdigit() for char in message):
                if any(word in message for word in ["lembar", "batang", "unit", "pcs"]):
                    return self.PROFESSIONAL_TEMPLATES["next_step"].format(
                        action="Kami akan buatkan penawaran untuk Anda"
                    )

        # If we can't generate contextual response, ask for clarification
        return self.PROFESSIONAL_TEMPLATES["clarification"].format(
            aspect="produk dan ukuran yang Anda butuhkan"
        )
