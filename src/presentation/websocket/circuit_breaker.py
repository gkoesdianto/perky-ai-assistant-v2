"""Circuit breaker pattern for WebSocket service resilience."""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded threshold
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for service resilience.
    Prevents cascading failures by temporarily blocking calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        expected_exception: type[BaseException] = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting reset after opening
            expected_exception: Exception type to catch (others are re-raised)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func if successful

        Raises:
            Exception: If circuit is open or func fails
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception(
                        f"Circuit breaker is OPEN. Service unavailable. "
                        f"Retry after {self.recovery_timeout} seconds."
                    )

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Success - update state
            async with self._lock:
                self._on_success()

            return result

        except self.expected_exception as e:
            # Expected failure - update state
            async with self._lock:
                self._on_failure()

            # Log the failure
            logger.warning(
                f"Circuit breaker caught exception: {e}. "
                f"Failure count: {self.failure_count}/{self.failure_threshold}"
            )

            raise e

        except Exception as e:
            # Unexpected exception - don't count as circuit failure
            logger.error(f"Unexpected exception in circuit breaker: {e}")
            raise e

    def _on_success(self):
        """Handle successful call (internal, must be called within lock)."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker closing after successful test")

        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call (internal, must be called within lock)."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure > timedelta(seconds=self.recovery_timeout)

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

    def get_failure_count(self) -> int:
        """Get current failure count."""
        return self.failure_count

    async def reset(self):
        """Manually reset the circuit breaker."""
        async with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker manually reset")

    async def force_open(self):
        """Manually open the circuit breaker (for testing/maintenance)."""
        async with self._lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = datetime.now()
            logger.warning("Circuit breaker manually opened")
