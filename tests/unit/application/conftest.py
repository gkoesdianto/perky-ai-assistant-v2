"""Centralized fixtures for application layer tests.

This file now acts as a facade that imports fixtures from modular files
to maintain backward compatibility with existing tests.
"""

# Import all fixtures from modular files to maintain backward compatibility
# The fixtures package re-exports everything, so we just import from there
from tests.unit.application.fixtures import *  # noqa: F401, F403

# Note: The following fixtures are now organized in separate modules:
#
# - fixtures/mock_use_cases.py: Mock implementations of use cases
#   * MockStartChatSessionUseCase, MockProcessUserMessageUseCase, MockGetConversationUseCase
#   * mock_start_chat_session, mock_process_message, mock_get_conversation
#
# - fixtures/mock_ports.py: Mock implementations of ports/adapters
#   * MockAIAgentAdapter, MockProductServiceAdapter, MockQueryAnalyzerAdapter
#   * mock_ai_agent, mock_product_service, mock_query_analyzer
#   * mock_pydantic_ai_agent
#
# - fixtures/dto_fixtures.py: DTO fixtures
#   * sample_session_dto, sample_message_dto, sample_conversation_dto
#   * sample_conversation_context, sample_query_analyzer_messages
#
# - fixtures/product_fixtures.py: Product value object fixtures
#   * sample_product_info, sample_variant_info, sample_product_with_variants
#
# - fixtures/query_fixtures.py: Query intent fixtures
#   * query_analyzer_service
#   * sample_query_intent_with_clarification, sample_query_intent_product
#   * sample_query_intent_price, sample_query_intent_availability
#   * sample_query_intent_ambiguous
#
# - fixtures/conversation_fixtures.py: Conversation fixtures
#   * mock_conversation_repository, mock_conversation_repository_async
#   * sample_conversation_with_messages, sample_conversation_detailed
#   * sample_conversation_empty, sample_conversation_many_messages
#
# - fixtures/redis_fixtures.py: Redis mock fixtures
#   * mock_redis_client, mock_redis_adapter, mock_redis_with_existing_session
