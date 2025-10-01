"""Mock error simulator for testing error handling and resilience.

This module provides error simulation capabilities for testing error handling
and resilience in the mock infrastructure.
"""

import asyncio
import functools
import random
from typing import Any, Callable


class MockException(Exception):
    """Custom exception for simulated errors."""

    pass


class MockErrorSimulator:
    """
    Simulate errors for testing error handling.
    Controlled via environment variables.
    """

    def __init__(self, error_rate: float = 0.0, delay_ms: int = 0):
        """
        Initialize error simulator.

        Args:
            error_rate: Probability of error (0.0-1.0)
            delay_ms: Simulated network delay in milliseconds
        """
        self.error_rate = min(max(error_rate, 0.0), 1.0)  # Clamp to [0, 1]
        self.delay_ms = max(delay_ms, 0)

    async def maybe_fail(self, operation: str) -> None:
        """
        Randomly fail based on error rate.

        Args:
            operation: Name of the operation for error message

        Raises:
            MockException: If random failure occurs
        """
        if random.random() < self.error_rate:
            raise MockException(f"Simulated failure in {operation}")

    async def maybe_delay(self) -> None:
        """Add simulated network delay if configured."""
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000.0)

    def wrap_operation(self, operation_name: str):
        """
        Decorator to wrap operations with error simulation.

        Usage:
            @error_simulator.wrap_operation("get_product")
            async def get_product(self, id):
                ...
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                await self.maybe_delay()
                await self.maybe_fail(operation_name)
                return await func(*args, **kwargs)

            return wrapper

        return decorator
