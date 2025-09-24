"""Infrastructure dependencies module - Phase 5 Track 3.

This module provides dependency injection and service configuration
for the infrastructure layer.
"""

from .service_config import (
    ServiceConfiguration,
    service_config,
    configure_services_for_mode,
)

__all__ = [
    "ServiceConfiguration",
    "service_config",
    "configure_services_for_mode",
]
