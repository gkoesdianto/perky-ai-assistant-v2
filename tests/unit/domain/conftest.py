import pytest
from tests.unit.domain.factories import (
    SessionFactory,
    ConversationFactory,
    MessageFactory,
    ProductInfoFactory,
    QueryIntentFactory,
)


@pytest.fixture
def session():
    return SessionFactory.create()


@pytest.fixture
def expired_session():
    return SessionFactory.create_expired()


@pytest.fixture
def session_with_metadata():
    return SessionFactory.create_with_metadata()


@pytest.fixture
def conversation():
    return ConversationFactory.create()


@pytest.fixture
def conversation_with_messages():
    return ConversationFactory.create_with_messages()


@pytest.fixture
def conversation_with_product_queries():
    return ConversationFactory.create_with_product_queries()


@pytest.fixture
def user_message():
    return MessageFactory.create_user_message()


@pytest.fixture
def ai_message():
    return MessageFactory.create_ai_message()


@pytest.fixture
def product_query_message():
    return MessageFactory.create_product_query()


@pytest.fixture
def steel_product():
    return ProductInfoFactory.create_steel_product()


@pytest.fixture
def minimal_product():
    return ProductInfoFactory.create_with_required_fields_only()


@pytest.fixture
def complete_product():
    return ProductInfoFactory.create_with_all_fields()


@pytest.fixture
def product_inquiry_intent():
    return QueryIntentFactory.create_product_inquiry()


@pytest.fixture
def price_check_intent():
    return QueryIntentFactory.create_price_check()


@pytest.fixture
def availability_check_intent():
    return QueryIntentFactory.create_availability_check()


@pytest.fixture
def general_intent():
    return QueryIntentFactory.create_general_query()
