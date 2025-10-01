"""Centralized instrumentation setup for all integrations."""

import logging
from typing import Optional

import logfire
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_instrumentation(
    app: FastAPI, logfire_instance: Optional[logfire.Logfire] = None
):
    """
    Set up all Logfire instrumentations.

    Args:
        app: FastAPI application instance
        logfire_instance: Configured Logfire instance (or None if disabled)
    """
    if not logfire_instance:
        logger.info("Skipping instrumentation (Logfire not configured)")
        return

    try:
        # Phase 1: FastAPI only
        logger.info("Instrumenting FastAPI application...")
        logfire.instrument_fastapi(
            app,
            capture_headers=False,  # Privacy: don't capture headers
            excluded_urls="/health|/metrics",  # Exclude health checks from traces
        )

        logger.info("Instrumentation setup complete (Phase 1: FastAPI only)")

    except Exception as e:
        logger.error(f"Failed to set up instrumentation: {e}", exc_info=True)
