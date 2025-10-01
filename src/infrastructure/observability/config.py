"""Logfire configuration and initialization."""

import logging
from typing import Literal, Optional

import logfire

from src.core.config import settings

logger = logging.getLogger(__name__)


def configure_logfire() -> Optional["logfire.Logfire"]:
    """
    Configure Logfire with environment-specific settings.

    Returns:
        Configured Logfire instance or None if disabled.
    """
    if not settings.LOGFIRE_SEND_TO_LOGFIRE:
        logger.info("Logfire observability disabled (LOGFIRE_SEND_TO_LOGFIRE=false)")
        return None

    if not settings.LOGFIRE_TOKEN:
        logger.warning(
            "Logfire token not configured. Observability will be disabled. "
            "Set LOGFIRE_TOKEN environment variable."
        )
        return None

    try:
        # Configure scrubbing: use ScrubbingOptions for True, or False to disable
        scrubbing_config: logfire.ScrubbingOptions | Literal[False] = (
            logfire.ScrubbingOptions() if settings.LOGFIRE_SCRUBBING else False
        )

        # Configure console: convert bool to ConsoleOptions or False
        console_config: logfire.ConsoleOptions | Literal[False] = (
            logfire.ConsoleOptions() if settings.LOGFIRE_CONSOLE else False
        )

        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name=settings.LOGFIRE_SERVICE_NAME,
            console=console_config,
            scrubbing=scrubbing_config,
        )

        logger.info(
            f"Logfire configured successfully "
            f"(service={settings.LOGFIRE_SERVICE_NAME})"
        )

        return logfire

    except Exception as e:
        logger.error(f"Failed to configure Logfire: {e}", exc_info=True)
        return None
