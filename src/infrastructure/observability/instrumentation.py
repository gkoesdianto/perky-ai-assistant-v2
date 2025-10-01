"""Centralized instrumentation setup for all integrations."""

import logging
from types import ModuleType
from typing import Optional

import logfire
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_instrumentation(app: FastAPI, logfire_instance: Optional[ModuleType] = None):
    """
    Set up all Logfire instrumentations.

    Args:
        app: FastAPI application instance
        logfire_instance: Configured logfire module (or None if disabled)
    """
    if not logfire_instance:
        logger.info("Skipping instrumentation (Logfire not configured)")
        return

    try:
        # Phase 1: FastAPI
        logger.info("Instrumenting FastAPI application...")
        logfire.instrument_fastapi(
            app,
            capture_headers=False,  # Privacy: don't capture headers
            excluded_urls="/health|/metrics",  # Exclude health checks from traces
        )

        # Phase 2: PydanticAI (AUTOMATIC LLM TRACING!)
        logger.info("Instrumenting PydanticAI agents...")
        logfire.instrument_pydantic_ai()

        # Phase 2: HTTPX (for external API calls)
        logger.info("Instrumenting HTTPX client...")
        logfire.instrument_httpx()

        logger.info("Instrumentation setup complete (Phase 2: + PydanticAI + HTTPX)")

    except Exception as e:
        logger.error(f"Failed to set up instrumentation: {e}", exc_info=True)
