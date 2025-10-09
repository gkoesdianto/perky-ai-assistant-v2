"""Observability module for Logfire integration."""

from src.infrastructure.observability.config import configure_logfire
from src.infrastructure.observability.instrumentation import setup_instrumentation

__all__ = ["configure_logfire", "setup_instrumentation"]
