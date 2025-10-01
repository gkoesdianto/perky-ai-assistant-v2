"""Logfire configuration and initialization."""

import logging
from typing import Optional

import logfire

from src.core.config import settings

logger = logging.getLogger(__name__)


def configure_logfire() -> Optional[logfire.Logfire]:
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
        scrubbing_config = (
            logfire.ScrubbingOptions() if settings.LOGFIRE_SCRUBBING else False
        )

        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name=settings.LOGFIRE_SERVICE_NAME,
            console=settings.LOGFIRE_CONSOLE,
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
