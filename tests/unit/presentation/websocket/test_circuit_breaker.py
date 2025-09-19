"""Behavioral tests for circuit breaker pattern."""

import pytest
import asyncio
from src.presentation.websocket.circuit_breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test circuit breaker behavior."""

    async def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        breaker = CircuitBreaker()
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.get_failure_count() == 0

    async def test_successful_calls_pass_through(self):
        """Successful calls should pass through when circuit is closed."""
        breaker = CircuitBreaker()

        async def successful_operation(x):
            return x * 2

        result = await breaker.call(successful_operation, 5)
        assert result == 10
        assert breaker.get_state() == CircuitState.CLOSED

    async def test_failures_increment_counter(self):
        """Failed calls should increment failure counter."""
        breaker = CircuitBreaker(failure_threshold=3)

        async def failing_operation():
            raise Exception("Service error")

        # First failure
        with pytest.raises(Exception, match="Service error"):
            await breaker.call(failing_operation)
        assert breaker.get_failure_count() == 1
        assert breaker.get_state() == CircuitState.CLOSED

        # Second failure
        with pytest.raises(Exception, match="Service error"):
            await breaker.call(failing_operation)
        assert breaker.get_failure_count() == 2
        assert breaker.get_state() == CircuitState.CLOSED

    async def test_circuit_opens_after_threshold(self):
        """Circuit should open after failure threshold is reached."""
        breaker = CircuitBreaker(failure_threshold=2)

        async def failing_operation():
            raise Exception("Service error")

        # Reach threshold
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_operation)

        assert breaker.get_state() == CircuitState.OPEN
        assert breaker.get_failure_count() == 2

    async def test_open_circuit_blocks_calls(self):
        """Open circuit should block calls immediately."""
        breaker = CircuitBreaker(failure_threshold=1)

        async def failing_operation():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(failing_operation)

        # Next call should be blocked
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_operation)

    async def test_circuit_enters_half_open_after_timeout(self):
        """Circuit should enter HALF_OPEN state after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

        async def operation():
            if breaker.get_state() == CircuitState.HALF_OPEN:
                return "success"
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(operation)

        # Wait a tiny bit for timeout
        await asyncio.sleep(0.01)

        # Should enter HALF_OPEN and allow test call
        result = await breaker.call(operation)
        assert result == "success"
        assert breaker.get_state() == CircuitState.CLOSED

    async def test_successful_call_in_half_open_closes_circuit(self):
        """Successful call in HALF_OPEN state should close the circuit."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return "success"

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(operation)

        await asyncio.sleep(0.01)  # Wait for recovery timeout

        # Successful call should close the circuit
        result = await breaker.call(operation)
        assert result == "success"
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.get_failure_count() == 0

    async def test_failed_call_in_half_open_reopens_circuit(self):
        """Failed call in HALF_OPEN state should reopen the circuit."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

        async def failing_operation():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(failing_operation)

        await asyncio.sleep(0.01)  # Wait for recovery timeout

        # Failed call in HALF_OPEN should reopen
        with pytest.raises(Exception, match="Service error"):
            await breaker.call(failing_operation)

        assert breaker.get_state() == CircuitState.OPEN

    async def test_manual_reset(self):
        """Manual reset should close the circuit and reset counters."""
        breaker = CircuitBreaker(failure_threshold=1)

        async def failing_operation():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(failing_operation)

        assert breaker.get_state() == CircuitState.OPEN

        # Manual reset
        await breaker.reset()

        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.get_failure_count() == 0

    async def test_force_open(self):
        """Force open should open the circuit manually."""
        breaker = CircuitBreaker()

        async def successful_operation():
            return "success"

        # Initially should work
        result = await breaker.call(successful_operation)
        assert result == "success"

        # Force open
        await breaker.force_open()
        assert breaker.get_state() == CircuitState.OPEN

        # Should block calls
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(successful_operation)

    async def test_unexpected_exceptions_dont_open_circuit(self):
        """Unexpected exception types should not open the circuit."""
        breaker = CircuitBreaker(failure_threshold=1, expected_exception=ValueError)

        async def operation_with_unexpected_error():
            raise TypeError("Unexpected error type")

        # This should not count toward opening the circuit
        with pytest.raises(TypeError):
            await breaker.call(operation_with_unexpected_error)

        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.get_failure_count() == 0
