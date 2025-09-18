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
        greetings = ["halo", "hello", "selamat pagi", "hai"]

        for greeting in greetings:
            response = await mock_agent.generate_response(greeting)
            assert response in MockAIAgent.RESPONSES["greeting"]
            assert "SMS Perkasa" in response or "PERKY" in response

    @pytest.mark.asyncio
    async def test_product_plat_inquiry(self, mock_agent):
        # Test plat product inquiries
        queries = ["ada plat baja?", "plat hitam", "steel plate"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            assert "plat" in response.lower()
            assert "SS400" in response or "galvanis" in response

    @pytest.mark.asyncio
    async def test_product_hollow_inquiry(self, mock_agent):
        # Test hollow product inquiries
        queries = ["besi hollow", "hollow galvanis", "besi kotak"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            assert "hollow" in response.lower()
            assert "galvanis" in response or "20x20" in response

    @pytest.mark.asyncio
    async def test_price_inquiry(self, mock_agent):
        # Test price inquiries
        queries = ["berapa harga plat?", "price list", "biaya hollow"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            assert "Rp" in response or "harga" in response.lower()

    @pytest.mark.asyncio
    async def test_stock_availability(self, mock_agent):
        # Test stock inquiries
        queries = ["stok plat ada?", "stock available", "tersedia?"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            assert (
                "stok" in response.lower()
                or "lembar" in response
                or "batang" in response
            )

    @pytest.mark.asyncio
    async def test_order_flow(self, mock_agent):
        # Test order process
        queries = ["cara pesan", "order process", "mau beli"]

        for query in queries:
            response = await mock_agent.generate_response(query)
            assert "pemesanan" in response.lower() or "spesifikasi" in response.lower()

    @pytest.mark.asyncio
    async def test_default_response(self, mock_agent):
        # Test unrecognized queries
        response = await mock_agent.generate_response("random unrelated text")
        assert response in MockAIAgent.RESPONSES["default"]

    @pytest.mark.asyncio
    async def test_contextual_response_with_product_followup(
        self, mock_agent, sample_context
    ):
        # Test contextual response when user follows up with size
        response = await mock_agent.generate_response("5mm", sample_context)
        assert "plat baja 5mm" in response
        assert "Baik, saya catat" in response

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
        assert "hollow 40x40" in response
        assert "Baik, saya catat" in response

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
        assert "penawaran" in response.lower()

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
        assert "Mohon info lebih detail" in response

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
        assert response in MockAIAgent.RESPONSES["default"]

    @pytest.mark.asyncio
    async def test_none_context_handling(self, mock_agent):
        # Test with None context
        response = await mock_agent.generate_response("plat baja", None)
        assert "plat" in response.lower()

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, mock_agent):
        # Test case insensitivity
        response1 = await mock_agent.generate_response("HALO")
        assert response1 in MockAIAgent.RESPONSES["greeting"]

        response2 = await mock_agent.generate_response("PlAt BaJa")
        assert "plat" in response2.lower()

        response3 = await mock_agent.generate_response("HOLLOW")
        assert "hollow" in response3.lower()

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
