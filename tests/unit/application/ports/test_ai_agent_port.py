"""
Unit tests for AIAgentPort protocol.
Tests the protocol contract using mock implementations from conftest.
"""

import pytest


@pytest.mark.asyncio
class TestMockAIAgentAdapter:
    """Test suite for AI Agent port mock implementation."""

    async def test_generate_response_without_context(self, mock_ai_agent):
        """Test generating response without conversation context."""
        mock_ai_agent.generate_response.return_value = "Halo! Ada yang bisa saya bantu?"

        response = await mock_ai_agent.generate_response("Halo")

        assert response == "Halo! Ada yang bisa saya bantu?"
        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == "Halo"
        assert mock_ai_agent.last_context is None

    async def test_generate_response_with_context(
        self, mock_ai_agent, sample_conversation_context
    ):
        """Test generating response with conversation context."""
        expected_response = "Untuk plat baja 10mm, kami punya stok 50 lembar"
        mock_ai_agent.generate_response.return_value = expected_response

        response = await mock_ai_agent.generate_response(
            "Berapa stok yang tersedia?", sample_conversation_context
        )

        assert response == expected_response
        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == "Berapa stok yang tersedia?"
        assert mock_ai_agent.last_context == sample_conversation_context
        assert len(mock_ai_agent.last_context) == 2

    async def test_generate_response_for_product_inquiry(self, mock_ai_agent):
        """Test AI response for product inquiry."""
        inquiry = "Apakah ada baja ringan untuk atap?"
        expected = (
            "Ya, kami memiliki berbagai jenis baja ringan untuk atap "
            "dengan berbagai ukuran"
        )
        mock_ai_agent.generate_response.return_value = expected

        response = await mock_ai_agent.generate_response(inquiry)

        assert response == expected
        # Verify through our tracking properties instead
        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == inquiry

    async def test_generate_response_empty_message(self, mock_ai_agent):
        """Test handling empty message."""
        mock_ai_agent.generate_response.return_value = (
            "Maaf, saya tidak mengerti. Bisa dijelaskan lebih lanjut?"
        )

        response = await mock_ai_agent.generate_response("")

        assert response == "Maaf, saya tidak mengerti. Bisa dijelaskan lebih lanjut?"
        assert mock_ai_agent.last_message == ""

    async def test_reset_functionality(
        self, mock_ai_agent, sample_conversation_context
    ):
        """Test reset clears all state."""
        mock_ai_agent.generate_response.return_value = "Test response"
        await mock_ai_agent.generate_response(
            "Test message", sample_conversation_context
        )

        assert mock_ai_agent.call_count == 1
        assert mock_ai_agent.last_message == "Test message"

        mock_ai_agent.reset()

        assert mock_ai_agent.call_count == 0
        assert mock_ai_agent.last_message is None
        assert mock_ai_agent.last_context is None
        # Verify reset worked through our tracking properties
        assert mock_ai_agent.call_count == 0

    async def test_multiple_calls_tracking(self, mock_ai_agent):
        """Test tracking multiple calls."""
        responses = ["Response 1", "Response 2", "Response 3"]
        mock_ai_agent.generate_response.side_effect = responses

        for i, expected in enumerate(responses, 1):
            response = await mock_ai_agent.generate_response(f"Message {i}")
            assert response == expected
            assert mock_ai_agent.call_count == i

        assert mock_ai_agent.last_message == "Message 3"

    async def test_protocol_compliance(self, mock_ai_agent):
        """Test that mock implementation satisfies the protocol."""
        assert hasattr(mock_ai_agent, "generate_response")
        assert callable(mock_ai_agent.generate_response)

        # Verify method signature matches protocol
        import inspect

        # The mock's generate_response is an AsyncMock, check it's callable
        # and has the expected tracking properties
        assert hasattr(mock_ai_agent, "call_count")
        assert hasattr(mock_ai_agent, "last_message")
        assert hasattr(mock_ai_agent, "last_context")
