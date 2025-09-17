"""Application layer test configuration.

This file is simplified - all fixtures are now in root conftest.
Kept for backward compatibility and layer-specific configuration.
"""

# Application-specific test configuration
import pytest

# ============================================================================
# The following fixtures are available from root conftest.py automatically:
# ============================================================================
# Domain entities:
# - session, expired_session, session_with_metadata
# - conversation, conversation_with_messages
# - user_message, ai_message
#
# Products and variants:
# - product, steel_product, minimal_product, complete_product
# - variant, steel_variant
# - product_with_variants, complete_product_with_variants
#
# Mocks:
# - mock_ai_agent, mock_product_service, mock_redis
# - mock_repository, mock_message_repository, mock_product_repository
# - mock_cache_service
#
# DTOs:
# - session_dto, message_dto, conversation_dto
# - product_query_dto, product_response_dto
#
# Query intents:
# - product_inquiry_intent, price_check_intent, availability_check_intent
# ============================================================================


# Most fixtures have been moved to root conftest.py
# Keeping this file for:
# 1. Backward compatibility during migration
# 2. Application-specific test configuration
# 3. Any application layer specific setup/teardown


@pytest.fixture(autouse=True)
def application_test_setup():
    """Setup for application layer tests."""
    # Any setup specific to application tests
    yield
    # Any teardown
