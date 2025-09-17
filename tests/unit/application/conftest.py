"""Application layer test configuration.

This file is simplified - all fixtures are now in root conftest.
Kept for backward compatibility and layer-specific configuration.
"""

# Application-specific test configuration
import pytest

# Import application-specific fixtures that are not in root conftest
# These are layer-specific fixtures that don't belong in the root

# Query analysis fixtures
from tests.unit.application.fixtures.query_fixtures import (  # noqa: F401
    query_analyzer_service,
    sample_query_intent_with_clarification,
    sample_query_intent_product,
    sample_query_intent_price,
    sample_query_intent_availability,
    sample_query_intent_ambiguous,
)

# DTO fixtures for application layer
from tests.unit.application.fixtures.dto_fixtures import (  # noqa: F401
    sample_conversation_context,
    sample_query_analyzer_messages,
)

# Conversation fixtures for application layer
from tests.unit.application.fixtures.conversation_fixtures import (  # noqa: F401
    sample_conversation_with_messages,
    sample_conversation_detailed,
    sample_conversation_empty,
    sample_conversation_many_messages,
    mock_conversation_repository_async,
)

# Use case mocks
from tests.unit.application.fixtures.mock_use_cases import (  # noqa: F401
    mock_start_chat_session,
    mock_process_message,
    mock_get_conversation,
)

# Port mocks not in root conftest
from tests.unit.application.fixtures.mock_ports import (  # noqa: F401
    mock_pydantic_ai_agent,
    mock_query_analyzer,
)

# Redis-specific fixtures for application layer
from tests.unit.application.fixtures.redis_fixtures import (  # noqa: F401
    mock_redis_client,
    mock_redis_adapter,
    mock_redis_with_existing_session,
)

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
