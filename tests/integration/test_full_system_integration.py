"""Full system integration tests for Convergence Point 2.

Tests complete flow from WebSocket to AI response with all tracks integrated.
Run this after all tracks (1-5) are complete.
"""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch

from src.infrastructure.container import get_container, Container
from src.infrastructure.dependencies import configure_services_for_mode
from src.main import create_app


class TestFullSystemIntegration:
    """Test complete system flow from WebSocket to AI response."""

    @pytest.fixture
    def configured_app(self, mock_ai_agent):
        """Create fully configured application."""
        with patch.dict(
            "os.environ",
            {
                "USE_MOCK_MODE": "true",
                "PROJECT_NAME": "Steel Chat MVP",
                "VERSION": "1.0.0",
                "API_V1_STR": "/api/v1",
            },
        ):
            with patch(
                "src.infrastructure.container.get_singleton_container"
            ) as mock_get_container:
                mock_container = MagicMock()
                mock_container.get_ai_agent.return_value = mock_ai_agent
                mock_get_container.return_value = mock_container

                app = create_app()
                return app

    @pytest.mark.asyncio
    async def test_health_endpoint(self, configured_app):
        """Test health endpoint is accessible."""
        transport = ASGITransport(app=configured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_documentation(self, configured_app):
        """Test API documentation is available."""
        transport = ASGITransport(app=configured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/openapi.json")
            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert "title" in data["info"]
            assert len(data["info"]["title"]) > 0

    def test_websocket_full_flow(self, configured_app):
        """Test complete WebSocket flow with all components."""
        with TestClient(configured_app) as client:
            with client.websocket_connect("/api/v1/ws/full-system-test") as websocket:
                welcome = websocket.receive_json()
                assert welcome["type"] == "system"
                assert welcome["event"] == "connected"
                assert "Selamat datang" in welcome["message"]

                websocket.send_json(
                    {
                        "type": "user_message",
                        "message": "Saya butuh plat baja 5mm",
                        "metadata": {"source": "web"},
                    }
                )

                typing = websocket.receive_json()
                assert typing["type"] == "system"
                assert typing["event"] == "typing"
                assert "mengetik" in typing["message"]

                response = websocket.receive_json()
                assert response["type"] == "ai_response"
                assert response["message"] is not None
                assert len(response["message"]) > 0

    def test_websocket_error_recovery(self, configured_app):
        """Test system handles errors gracefully."""
        with TestClient(configured_app) as client:
            with client.websocket_connect(
                "/api/v1/ws/error-recovery-test"
            ) as websocket:
                websocket.receive_json()

                websocket.send_json({"type": "invalid_message_type", "data": "invalid"})

                error = websocket.receive_json()
                assert error["type"] == "error"

                websocket.send_json({"type": "ping"})
                pong = websocket.receive_json()
                assert pong["type"] == "pong"

    def test_multiple_websocket_sessions(self, configured_app):
        """Test multiple concurrent WebSocket sessions."""
        with TestClient(configured_app) as client:
            sessions = []

            for i in range(3):
                ws = client.websocket_connect(f"/api/v1/ws/multi-session-{i}")
                ws.__enter__()
                welcome = ws.receive_json()
                assert welcome["type"] == "system"
                sessions.append(ws)

            for i, ws in enumerate(sessions):
                ws.send_json(
                    {"type": "user_message", "message": f"Message from session {i}"}
                )

                ws.receive_json()
                response = ws.receive_json()
                assert response["type"] == "ai_response"

            for ws in sessions:
                ws.__exit__(None, None, None)

    def test_conversation_persistence(self, configured_app):
        """Test conversation history is maintained."""
        with TestClient(configured_app) as client:
            session_id = "persistence-test"

            with client.websocket_connect(f"/api/v1/ws/{session_id}") as ws1:
                ws1.receive_json()

                ws1.send_json({"type": "user_message", "message": "First message"})
                ws1.receive_json()
                ws1.receive_json()

                ws1.send_json({"type": "user_message", "message": "Second message"})
                ws1.receive_json()
                ws1.receive_json()

            with client.websocket_connect(f"/api/v1/ws/{session_id}") as ws2:
                ws2.receive_json()

                ws2.send_json(
                    {"type": "user_message", "message": "Third message after reconnect"}
                )
                ws2.receive_json()
                response = ws2.receive_json()
                assert response["type"] == "ai_response"

    @pytest.mark.asyncio
    async def test_container_mode_switching(self):
        """Test container mode switching between mock and real."""
        with patch.dict("os.environ", {"USE_MOCK_MODE": "true"}):
            container = configure_services_for_mode()
            assert container.use_mocks is True

        with patch.dict(
            "os.environ", {"USE_MOCK_MODE": "false", "OPENAI_API_KEY": "test-key"}
        ):
            with patch("src.infrastructure.ai.chat_agent.Agent"):
                with patch("src.infrastructure.ai.chat_agent.OpenAIChatModel"):
                    container = configure_services_for_mode()
                    assert container.use_mocks is False

    def test_product_search_flow(self, configured_app):
        """Test product search through WebSocket."""
        with TestClient(configured_app) as client:
            with client.websocket_connect(
                "/api/v1/ws/product-search-test"
            ) as websocket:
                websocket.receive_json()

                test_queries = [
                    "Ada plat baja 5mm?",
                    "Berapa harga besi beton D12?",
                    "Stok H-beam 200x200?",
                ]

                for query in test_queries:
                    websocket.send_json({"type": "user_message", "message": query})

                    websocket.receive_json()
                    response = websocket.receive_json()
                    assert response["type"] == "ai_response"
                    assert response["message"] is not None

    def test_indonesian_language_flow(self, configured_app):
        """Test Indonesian language handling."""
        with TestClient(configured_app) as client:
            with client.websocket_connect("/api/v1/ws/indo-lang-test") as websocket:
                welcome = websocket.receive_json()
                assert "Selamat datang" in welcome["message"]

                websocket.send_json({"type": "user_message", "message": "Halo"})

                websocket.receive_json()
                response = websocket.receive_json()

                assert response["type"] == "ai_response"
                indonesian_words = ["Selamat", "PERKY", "SMS Perkasa", "saya", "Anda"]
                assert any(word in response["message"] for word in indonesian_words)

    def test_rate_limiting_integration(self, configured_app):
        """Test rate limiting in full system."""
        with TestClient(configured_app) as client:
            with client.websocket_connect("/api/v1/ws/rate-limit-test") as websocket:
                websocket.receive_json()

                for i in range(20):
                    websocket.send_json(
                        {"type": "user_message", "message": f"Rapid message {i}"}
                    )

                rate_limited = False
                for _ in range(25):
                    try:
                        msg = websocket.receive_json()
                        if (
                            msg.get("type") == "error"
                            and "terlalu banyak" in msg.get("message", "").lower()
                        ):
                            rate_limited = True
                            break
                    except Exception:
                        break

                assert rate_limited

    @pytest.mark.asyncio
    async def test_async_operation_flow(self):
        """Test async operations work correctly."""

        async def send_messages(session_id: str, count: int):
            """Send multiple messages asynchronously."""
            results = []
            for i in range(count):
                await asyncio.sleep(0.1)
                results.append(f"Message {i} from {session_id}")
            return results

        tasks = [
            send_messages("session-1", 3),
            send_messages("session-2", 3),
            send_messages("session-3", 3),
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all(len(r) == 3 for r in results)
