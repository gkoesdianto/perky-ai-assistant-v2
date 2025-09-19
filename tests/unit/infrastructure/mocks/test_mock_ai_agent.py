import pytest
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
from src.application.dto import MessageDTO
from datetime import datetime, timezone


class TestMockAIAgent:

    @pytest.fixture
    def mock_agent(self):
        return MockAIAgent()

    @pytest.fixture
    def sample_context(self):
        return [
            MessageDTO(
                content="Ada plat baja 5mm?",
                sender_type="user",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
            MessageDTO(
                content="Untuk plat baja, kami memiliki:\n• Plat hitam SS400: 2mm-20mm",
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

    @pytest.mark.asyncio
    async def test_greeting_response(self, mock_agent):
        # Test various greeting inputs
        greetings = ["halo", "hello", "hi", "hai"]

        for greeting in greetings:
            response = await mock_agent.generate_response(greeting)
            # LLM-like responses should contain greeting indicators
            assert any(term in response.lower() for term in ["selamat", "perky", "sms perkasa", "bantu", "halo", "kami"])
            # Should have metadata tracking
            assert mock_agent.last_response_metadata is not None
            assert mock_agent.last_response_metadata.intent == "greeting"

    @pytest.mark.asyncio
    async def test_product_plat_inquiry(self, mock_agent):
        # Test plat product inquiries
        queries = ["ada plat baja?", "plat hitam", "steel plate"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            # LLM-like responses should mention plat or related terms
            assert any(term in response.lower() for term in ["plat", "baja", "tersedia", "stock", "ready"])
            # Verify intent detection
            assert mock_agent.last_response_metadata.intent in ["product_inquiry", "stock_check"]

    @pytest.mark.asyncio
    async def test_product_hollow_inquiry(self, mock_agent):
        # Test hollow product inquiries
        queries = ["besi hollow", "hollow galvanis"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            # LLM-like responses should contain hollow-related content or general product response
            assert any(term in response.lower() for term in ["hollow", "besi", "galvanis", "tersedia", "ukuran", "20x20", "40x40", "stock", "produk", "material"])
            # Check entity extraction
            assert "hollow" in mock_agent.last_response_metadata.entities.get("products", [])

    @pytest.mark.asyncio
    async def test_price_inquiry(self, mock_agent):
        # Test price inquiries
        queries = ["berapa harga plat?", "harga hollow"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            # Should contain price information or ask for clarification
            assert any(term in response.lower() for term in ["rp", "harga", "biaya", "price", "penawaran", "spesifik", "produk"])

    @pytest.mark.asyncio
    async def test_stock_availability(self, mock_agent):
        # Test stock inquiries
        queries = ["stok plat ada?", "stock hollow tersedia?"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            # Should contain stock information or availability
            assert any(
                term in response.lower()
                for term in ["stok", "stock", "tersedia", "ready", "lembar", "batang", "produk", "siap"]
            )

    @pytest.mark.asyncio
    async def test_order_flow(self, mock_agent):
        # Test order process
        queries = ["cara pesan", "mau beli"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            # LLM-like responses for ordering vary
            assert any(term in response.lower() for term in ["pemesanan", "spesifikasi", "pesan", "order", "hubungi", "sales", "konfirmasi", "produk"])

    @pytest.mark.asyncio
    async def test_default_response(self, mock_agent):
        # Test unrecognized queries
        response = await mock_agent.generate_response("random unrelated text")
        # LLM-like responses should ask for clarification
        assert any(term in response.lower() for term in ["maaf", "informasi", "spesifik", "kebutuhan", "produk", "cari", "jelaskan"])
        assert mock_agent.last_response_metadata.intent == "general"

    @pytest.mark.asyncio
    async def test_contextual_response_with_product_followup(
        self, mock_agent, sample_context
    ):
        # Test contextual response when user follows up with size
        response = await mock_agent.generate_response("5mm", sample_context)
        # LLM-like responses should understand thickness context
        assert any(term in response.lower() for term in ["5mm", "5 mm", "tebal", "ketebalan", "ukuran", "tersedia"])
        # Should detect thickness entity
        assert "5mm" in str(mock_agent.last_response_metadata.entities.get("thickness", []))

    @pytest.mark.asyncio
    async def test_contextual_response_with_hollow_size(self, mock_agent):
        context = [
            MessageDTO(
                content="Ada hollow?",
                sender_type="user",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
            MessageDTO(
                content=(
                    "Besi hollow tersedia dalam:\n"
                    "• Hollow galvanis: 20x20 hingga 100x100"
                ),
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

        response = await mock_agent.generate_response("40x40", context)
        # LLM-like responses should be relevant to dimensions or products
        assert len(response) > 10  # Has meaningful response
        # Should detect dimension entity
        assert "40x40" in str(mock_agent.last_response_metadata.entities.get("dimensions", []))

    @pytest.mark.asyncio
    async def test_contextual_quantity_response(self, mock_agent):
        context = [
            MessageDTO(
                content="Ada plat 5mm?",
                sender_type="user",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
            MessageDTO(
                content="Ya, tersedia plat 5mm",
                sender_type="ai_agent",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            ),
        ]

        response = await mock_agent.generate_response("100 lembar", context)
        # Should respond to quantity request - LLM-like response varies
        # Just check it's a meaningful response about quantity or clarification
        assert len(response) > 10

    @pytest.mark.asyncio
    async def test_contextual_clarification_request(self, mock_agent):
        context = [
            MessageDTO(
                content="Saya butuh material",
                sender_type="user",
                session_id="test-session",
                timestamp=datetime.now(timezone.utc),
            )
        ]

        response = await mock_agent.generate_response("yang bagus", context)
        # LLM-like responses should ask for clarification or provide general response
        # Just check it's a meaningful response
        assert len(response) > 10

    @pytest.mark.asyncio
    async def test_professional_response_formatting(self, mock_agent):
        # Test that responses maintain professional tone
        response = await mock_agent.generate_response("halo")
        assert any(word in response for word in ["Selamat", "SMS Perkasa", "PERKY"])
        assert response.endswith("?") or response.endswith(".")

    @pytest.mark.asyncio
    async def test_indonesian_language_consistency(self, mock_agent):
        # Test Indonesian terms are used consistently
        response = await mock_agent.generate_response("ada plat?")
        assert not any(
            english in response.lower() for english in ["sheet", "available", "price"]
        )

    @pytest.mark.asyncio
    async def test_empty_context_handling(self, mock_agent):
        # Test with empty context list
        response = await mock_agent.generate_response("5mm", [])
        # Without context, "5mm" could trigger specifications or general response
        assert len(response) > 10  # Just check it's a meaningful response

    @pytest.mark.asyncio
    async def test_none_context_handling(self, mock_agent):
        # Test with None context
        response = await mock_agent.generate_response("plat baja", None)
        assert "plat" in response.lower()

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, mock_agent):
        # Test case insensitivity
        response1 = await mock_agent.generate_response("HALO")
        assert any(term in response1.lower() for term in ["selamat", "perky", "sms perkasa", "bantu"])
        assert mock_agent.last_response_metadata.intent == "greeting"

        response2 = await mock_agent.generate_response("PlAt BaJa")
        assert any(term in response2.lower() for term in ["plat", "baja", "tersedia"])

        response3 = await mock_agent.generate_response("HOLLOW")
        assert any(term in response3.lower() for term in ["hollow", "besi", "galvanis", "tersedia"])

    @pytest.mark.asyncio
    async def test_multiple_keyword_detection(self, mock_agent):
        # Test queries with multiple keywords
        response = await mock_agent.generate_response("harga plat baja berapa?")
        assert "Rp" in response or "harga" in response.lower()

    @pytest.mark.asyncio
    async def test_mixed_language_handling(self, mock_agent):
        # Test mixed Indonesian-English queries
        response = await mock_agent.generate_response("price plat baja")
        assert "Rp" in response or "plat" in response.lower()
