# Domain tests now use root conftest
# All fixtures are available from tests/conftest.py

# The following fixtures are defined but differ from root conftest:
# - conversation_with_product_queries: Not available in root conftest
# - product_query_message: Not available in root conftest
# - general_intent: Not available in root conftest

# These can be added here temporarily until migration is complete:

import pytest
from tests.factories import (
    ConversationFactory,
    MessageFactory,
    QueryIntentFactory,
)


@pytest.fixture
def conversation_with_product_queries():
    """Create conversation with product query messages."""
    conversation = ConversationFactory.create()
    # Add product query messages
    for i in range(3):
        message = MessageFactory.create(
            conversation_id=conversation.id,
            sender_type="user",
            content=f"Product query {i}",
            intent="product_inquiry",
        )
        conversation.add_message(message)
    return conversation


@pytest.fixture
def product_query_message():
    """Create a product query message."""
    return MessageFactory.create(
        sender_type="user", content="Berapa harga plat baja 5mm?", intent="price_check"
    )


@pytest.fixture
def general_intent():
    """Create general query intent."""
    return QueryIntentFactory.create(confidence=0.85)
