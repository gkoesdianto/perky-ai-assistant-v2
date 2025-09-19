import pytest
import os
from unittest.mock import patch
from src.infrastructure.mocks.mock_product_repository import MockProductRepository
from src.infrastructure.mocks.mock_ai_agent import MockAIAgent
from src.infrastructure.mocks.mock_error_simulator import MockException


class TestErrorSimulationIntegration:

    @pytest.mark.asyncio
    async def test_product_repository_with_error_simulation(self):
        """Test that MockProductRepository handles error simulation correctly."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "1.0", "MOCK_RESPONSE_DELAY_MS": "0"}
        ):
            repo = MockProductRepository()

            # Should raise error due to 100% error rate
            with pytest.raises(MockException) as exc_info:
                await repo.search_products("plat")

            assert "Simulated failure in search_products" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_product_repository_no_errors(self):
        """Test that MockProductRepository works normally with 0% error rate."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "0.0", "MOCK_RESPONSE_DELAY_MS": "0"}
        ):
            repo = MockProductRepository()

            # Should work normally
            results = await repo.search_products("plat")
            assert len(results) > 0
            assert any("plat" in p.product_name.lower() for p in results)

    @pytest.mark.asyncio
    async def test_ai_agent_with_error_simulation(self):
        """Test that MockAIAgent handles error simulation correctly."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "1.0", "MOCK_RESPONSE_DELAY_MS": "0"}
        ):
            agent = MockAIAgent()

            # Should raise error due to 100% error rate
            with pytest.raises(MockException) as exc_info:
                await agent.generate_response("Halo")

            assert "Simulated failure in generate_response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ai_agent_no_errors(self):
        """Test that MockAIAgent works normally with 0% error rate."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "0.0", "MOCK_RESPONSE_DELAY_MS": "0"}
        ):
            agent = MockAIAgent()

            # Should work normally
            response = await agent.generate_response("Halo")
            assert response is not None
            assert len(response) > 0
            assert "SMS Perkasa" in response or "PERKY" in response

    @pytest.mark.asyncio
    async def test_delay_simulation_in_repository(self):
        """Test that delay simulation works in MockProductRepository."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "0.0", "MOCK_RESPONSE_DELAY_MS": "100"}
        ):
            repo = MockProductRepository()

            import asyncio

            start_time = asyncio.get_event_loop().time()
            results = await repo.search_products("hollow")
            elapsed = asyncio.get_event_loop().time() - start_time

            # Should have delay
            assert elapsed >= 0.09  # At least 90ms
            assert len(results) > 0  # But still return results

    @pytest.mark.asyncio
    async def test_intermittent_errors(self):
        """Test that partial error rates work as expected."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "0.5", "MOCK_RESPONSE_DELAY_MS": "0"}
        ):
            repo = MockProductRepository()

            successes = 0
            failures = 0

            for _ in range(100):
                try:
                    results = await repo.search_products("besi")
                    successes += 1
                    assert len(results) > 0
                except MockException:
                    failures += 1

            # Should have both successes and failures
            assert successes > 20
            assert failures > 20
            # Total should be 100
            assert successes + failures == 100

    @pytest.mark.asyncio
    async def test_environment_variable_parsing(self):
        """Test that environment variables are parsed correctly."""
        with patch.dict(
            os.environ, {"MOCK_ERROR_RATE": "0.25", "MOCK_RESPONSE_DELAY_MS": "50"}
        ):
            repo = MockProductRepository()

            # Check that simulator is configured correctly
            assert repo.error_simulator.error_rate == 0.25
            assert repo.error_simulator.delay_ms == 50

            agent = MockAIAgent()
            assert agent.error_simulator.error_rate == 0.25
            assert agent.error_simulator.delay_ms == 50
