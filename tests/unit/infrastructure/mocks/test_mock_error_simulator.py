import pytest
import asyncio
from src.infrastructure.mocks.mock_error_simulator import (
    MockErrorSimulator,
    MockException,
)


class TestMockErrorSimulator:

    @pytest.mark.asyncio
    async def test_no_error_with_zero_rate(self):
        """Test that no errors occur when error rate is 0."""
        simulator = MockErrorSimulator(error_rate=0.0, delay_ms=0)

        # Should not raise any exception
        for _ in range(100):
            await simulator.maybe_fail("test_operation")

    @pytest.mark.asyncio
    async def test_always_error_with_one_rate(self):
        """Test that errors always occur when error rate is 1.0."""
        simulator = MockErrorSimulator(error_rate=1.0, delay_ms=0)

        with pytest.raises(MockException) as exc_info:
            await simulator.maybe_fail("test_operation")

        assert "Simulated failure in test_operation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_rate_clamping(self):
        """Test that error rate is clamped between 0 and 1."""
        simulator_negative = MockErrorSimulator(error_rate=-0.5, delay_ms=0)
        assert simulator_negative.error_rate == 0.0

        simulator_high = MockErrorSimulator(error_rate=1.5, delay_ms=0)
        assert simulator_high.error_rate == 1.0

    @pytest.mark.asyncio
    async def test_delay_simulation(self):
        """Test that delay is applied when configured."""
        simulator = MockErrorSimulator(error_rate=0.0, delay_ms=100)

        start_time = asyncio.get_event_loop().time()
        await simulator.maybe_delay()
        elapsed = asyncio.get_event_loop().time() - start_time

        # Allow some tolerance for timing
        assert elapsed >= 0.09  # At least 90ms
        assert elapsed <= 0.15  # But not more than 150ms

    @pytest.mark.asyncio
    async def test_no_delay_when_zero(self):
        """Test that no delay occurs when delay_ms is 0."""
        simulator = MockErrorSimulator(error_rate=0.0, delay_ms=0)

        start_time = asyncio.get_event_loop().time()
        await simulator.maybe_delay()
        elapsed = asyncio.get_event_loop().time() - start_time

        assert elapsed < 0.01  # Should be near instant

    @pytest.mark.asyncio
    async def test_wrap_operation_decorator(self):
        """Test the wrap_operation decorator functionality."""
        simulator = MockErrorSimulator(error_rate=0.0, delay_ms=50)

        @simulator.wrap_operation("test_func")
        async def test_function():
            return "success"

        start_time = asyncio.get_event_loop().time()
        result = await test_function()
        elapsed = asyncio.get_event_loop().time() - start_time

        assert result == "success"
        assert elapsed >= 0.04  # At least 40ms due to delay

    @pytest.mark.asyncio
    async def test_wrap_operation_with_error(self):
        """Test that wrap_operation raises errors when configured."""
        simulator = MockErrorSimulator(error_rate=1.0, delay_ms=0)

        @simulator.wrap_operation("failing_func")
        async def test_function():
            return "should not return"

        with pytest.raises(MockException) as exc_info:
            await test_function()

        assert "Simulated failure in failing_func" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_statistical_error_rate(self):
        """Test that error rate is statistically correct."""
        simulator = MockErrorSimulator(error_rate=0.5, delay_ms=0)

        errors = 0
        runs = 1000

        for _ in range(runs):
            try:
                await simulator.maybe_fail("test_op")
            except MockException:
                errors += 1

        error_ratio = errors / runs
        # Should be close to 0.5, with some statistical variance
        assert 0.4 <= error_ratio <= 0.6
