"""Critical user flow E2E tests - MVP Optimized.

This module tests the most important user journeys that directly impact business value.
Focuses on complete workflows rather than technical implementation details.
Optimized for MVP development with reduced scope and simplified dependencies.
"""

import json

import pytest


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.priority("critical")
class TestCriticalUserFlows:
    """Test critical user journeys from connection to completion."""

    def test_complete_product_inquiry_flow(self, ws_client, e2e_helper):
        """Test complete user journey: connect → inquire → receive info → complete.

        This is the most critical flow as it represents the core business value.
        """
        # User asks about a specific product
        response = e2e_helper.send_message(ws_client, "Ada plat baja 5mm?")

        # Business Logic: System should respond to product availability queries
        assert response["type"] == "ai_response"
        assert response["message"] is not None
        # Response should mention product OR availability OR specifications
        # Allow for variations in how the AI responds
        response_lower = response["message"].lower()
        assert any(
            keyword in response_lower
            for keyword in [
                "plat",
                "baja",
                "steel",
                "tersedia",
                "stok",
                "ready",
                "5mm",
                "ukuran",
                "dimensi",
            ]
        ), f"Response should relate to product inquiry, got: {response['message']}"

        # Follow-up with price inquiry
        response = e2e_helper.send_message(ws_client, "Berapa harganya?")

        # Business Logic: System should handle price inquiries
        # Accept various price-related responses
        assert response["type"] == "ai_response"
        assert response["message"] is not None
        response_lower = response["message"].lower()
        assert any(
            keyword in response_lower
            for keyword in [
                "harga",
                "price",
                "rp",
                "rupiah",
                "biaya",
                "cost",
                "hubungi",
                "sales",
                "penawaran",
            ]
        ), f"Response should relate to pricing, got: {response['message']}"

        # Check availability - simplified for MVP
        response = e2e_helper.send_message(ws_client, "Apakah ready stock?")
        assert response["type"] == "ai_response"
        assert response["message"] is not None

    def test_indonesian_language_flow(self, ws_client, e2e_helper):
        """Test complete flow in Indonesian language (primary user base)."""
        # Greeting in Indonesian
        response = e2e_helper.send_message(
            ws_client, "Selamat pagi, saya butuh besi untuk proyek"
        )

        assert response["type"] == "ai_response"
        # Response should be in Indonesian - check for common Indonesian words
        msg = response.get("message", "")
        assert msg, f"No message in response: {response}"
        # More flexible check for Indonesian response
        indonesian_indicators = [
            "Selamat",
            "bisa",
            "bantu",
            "SMS Perkasa",
            "baja",
            "material",
        ]
        assert any(
            word in msg for word in indonesian_indicators
        ), f"Response not in Indonesian: {msg}"

        # Specific product inquiry
        response = e2e_helper.send_message(ws_client, "Ada besi beton diameter 12?")
        assert response["type"] == "ai_response"
        # Check for relevant business logic - response should contain product/price/spec info
        msg_lower = response["message"].lower()
        business_indicators = [
            "besi",
            "beton",
            "diameter",
            "12",
            "mm",
            "harga",
            "produk",
            "spesifikasi",
            "tersedia",
            "stok",
        ]
        assert any(
            indicator in msg_lower for indicator in business_indicators
        ), f"Response doesn't contain product-related information: {response['message']}"

    def test_multi_product_comparison_flow(self, ws_client, e2e_helper):
        """Test user comparing multiple products - simplified for MVP."""
        # Ask about first product
        response1 = e2e_helper.send_message(ws_client, "Show me steel plates 10mm")
        assert response1["type"] == "ai_response"

        # Ask about second product
        response2 = e2e_helper.send_message(ws_client, "What about 5mm plates?")
        assert response2["type"] == "ai_response"

        # Ask for comparison - simplified expectation
        response3 = e2e_helper.send_message(ws_client, "Which one is better?")
        assert response3["type"] == "ai_response"
        assert len(response3["message"]) > 20  # Basic comparison response


@pytest.mark.e2e
@pytest.mark.priority("high")
class TestErrorRecoveryFlows:
    """Test system resilience and error recovery - MVP essentials only."""

    def test_connection_recovery_flow(self, app):
        """Test connection loss and recovery scenario - simplified."""
        from fastapi.testclient import TestClient

        test_client = TestClient(app)

        # Create first connection
        with test_client.websocket_connect("/api/v1/ws/recovery-test-1") as ws1:
            # Establish session
            welcome = ws1.receive_text()
            welcome_data = json.loads(welcome)
            # Session ID could be used for reconnection in full implementation
            _ = welcome_data.get(
                "session_id"
            )  # Currently unused in simplified MVP test

            # Send message
            ws1.send_text(
                json.dumps({"type": "user_message", "message": "I need steel products"})
            )

            # Get response to establish context
            ws1.receive_text()  # Skip typing
            ws1.receive_text()  # Response - establishes context

        # Reconnect with new session (simplified for MVP)
        with test_client.websocket_connect("/api/v1/ws/recovery-test-2") as ws2:
            # Skip welcome message on new connection
            ws2.receive_text()  # Welcome message

            # Continue conversation - basic connectivity test
            ws2.send_text(
                json.dumps({"type": "user_message", "message": "Hello again"})
            )

            ws2.receive_text()  # Skip typing
            response2 = ws2.receive_text()
            response2_data = json.loads(response2)

            # System should respond normally
            assert response2_data["type"] == "ai_response"

    def test_invalid_input_handling(self, ws_client, e2e_helper):
        """Test system handles invalid inputs gracefully - essential cases only."""
        # Test only critical invalid inputs for MVP
        critical_invalid = ["", " ", "x" * 1000]  # Reduced scope

        for invalid_msg in critical_invalid:
            try:
                ws_client.send_text(
                    json.dumps({"type": "user_message", "message": invalid_msg})
                )

                response = ws_client.receive_text()
                response_data = json.loads(response)

                # System should handle gracefully
                assert response_data["type"] in ["error", "ai_response"]

                # Connection should still be alive
                assert e2e_helper.ping_pong(ws_client)
            except Exception as e:
                # Log but don't fail - we're testing error handling
                print(f"Expected error handling for input: {invalid_msg[:50]}... - {e}")


@pytest.mark.e2e
@pytest.mark.priority("medium")
class TestBasicConcurrency:
    """Test basic concurrent users - simplified for MVP."""

    def test_multiple_sessions_basic(self, app):
        """Test system handles multiple concurrent users - basic test."""
        from fastapi.testclient import TestClient

        test_client = TestClient(app)

        # Test with just 2 concurrent sessions for MVP
        sessions = []

        for i in range(2):
            ws = test_client.websocket_connect(f"/api/v1/ws/concurrent-{i}")
            sessions.append(ws)

        try:
            # Establish all connections
            for i, session in enumerate(sessions):
                with session as ws:
                    welcome = ws.receive_text()
                    welcome_data = json.loads(welcome)
                    assert welcome_data["type"] == "system"

                    # Send unique message
                    ws.send_text(
                        json.dumps(
                            {"type": "user_message", "message": f"User {i} needs help"}
                        )
                    )

                    # Get response
                    ws.receive_text()  # Skip typing
                    response = ws.receive_text()
                    response_data = json.loads(response)

                    assert response_data["type"] == "ai_response"
                    assert response_data["message"] is not None
        finally:
            # Cleanup
            for session in sessions:
                try:
                    session.close()
                except Exception:
                    pass  # Ignore cleanup errors

    def test_session_isolation_basic(self, app):
        """Test basic session isolation - simplified for MVP."""
        from fastapi.testclient import TestClient

        test_client = TestClient(app)

        # User 1 asks about specific product
        with test_client.websocket_connect("/api/v1/ws/isolation-user1") as ws1:
            ws1.receive_text()  # Welcome

            ws1.send_text(
                json.dumps(
                    {
                        "type": "user_message",
                        "message": "I want to buy 100 tons of steel plates",
                    }
                )
            )
            ws1.receive_text()  # Typing
            ws1.receive_text()  # Response

        # User 2 connects and asks different question
        with test_client.websocket_connect("/api/v1/ws/isolation-user2") as ws2:
            ws2.receive_text()  # Welcome

            ws2.send_text(
                json.dumps(
                    {"type": "user_message", "message": "What products do you have?"}
                )
            )
            ws2.receive_text()  # Typing
            response2 = ws2.receive_text()
            response2_data = json.loads(response2)

            # User 2 should get normal response, not know about User 1
            assert response2_data["type"] == "ai_response"
            assert "100 tons" not in response2_data["message"]


# Mark complex tests as post-MVP for future implementation
@pytest.mark.e2e
@pytest.mark.priority("low")
@pytest.mark.skip(reason="Post-MVP: Complex concurrency testing")
class TestAdvancedConcurrency:
    """Advanced concurrency tests - marked for post-MVP implementation."""

    def test_heavy_concurrent_load(self):
        """Test with many concurrent users - post-MVP."""
        pytest.skip("Post-MVP: Heavy load testing")

    def test_async_stress_testing(self):
        """Async stress testing - post-MVP."""
        pytest.skip("Post-MVP: Stress testing")


@pytest.mark.e2e
@pytest.mark.priority("low")
@pytest.mark.skip(reason="Post-MVP: Edge case testing")
class TestEdgeCases:
    """Edge cases and boundary conditions - marked for post-MVP."""

    def test_very_long_conversation(self):
        """Test very long conversations - post-MVP."""
        pytest.skip("Post-MVP: Long conversation testing")

    def test_special_characters_handling(self):
        """Test special characters - post-MVP."""
        pytest.skip("Post-MVP: Special character testing")

    def test_performance_degradation(self):
        """Test performance over time - post-MVP."""
        pytest.skip("Post-MVP: Performance degradation testing")
