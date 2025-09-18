import pytest
from src.domain.entities.message import Message
from tests.factories import MessageFactory


class TestMessage:
    def test_message_creation(self):
        message = Message(
            conversation_id="conv-123",
            sender_type="user",
            content="Berapa harga plat baja 5mm?",
        )

        assert message.conversation_id == "conv-123"
        assert message.sender_type == "user"
        assert message.content == "Berapa harga plat baja 5mm?"
        assert message.id is not None
        assert message.created_at is not None
        assert message.is_active is True

    @pytest.mark.parametrize("sender_type", ["user", "ai_agent"])
    def test_sender_types(self, sender_type):
        message = Message(
            conversation_id="conv-123", sender_type=sender_type, content="Test message"
        )

        assert message.sender_type == sender_type

    def test_default_language(self):
        message = Message(
            conversation_id="conv-123", sender_type="user", content="Test content"
        )

        assert message.detected_language == "id"

    def test_intent_optional(self):
        message = Message(
            conversation_id="conv-123", sender_type="user", content="Test content"
        )

        assert message.intent is None

        message_with_intent = Message(
            conversation_id="conv-123",
            sender_type="user",
            content="Test content",
            intent="product_inquiry",
        )

        assert message_with_intent.intent == "product_inquiry"

    @pytest.mark.parametrize(
        "intent,expected",
        [
            ("product_inquiry", True),
            ("price_check", True),
            ("stock_check", True),
            ("general", False),
            (None, False),
            ("random_intent", False),
        ],
    )
    def test_is_product_query_detection(self, intent, expected):
        message = Message(
            conversation_id="conv-123",
            sender_type="user",
            content="Test message",
            intent=intent,
        )

        assert message.is_product_query() == expected

    def test_indonesian_content(self):
        indonesian_queries = [
            "Berapa harga plat baja 5mm?",
            "Apakah ada stok pipa besi 2 inch?",
            "Saya butuh informasi produk baja ringan",
            "Tolong info harga terbaru untuk wiremesh M8",
        ]

        for content in indonesian_queries:
            message = MessageFactory.create_user_message(
                conversation_id="conv-123",
                content=content,
            )

            assert message.content == content
            assert message.detected_language == "id"

    def test_message_state_transitions(self):
        message = Message(
            conversation_id="conv-123", sender_type="user", content="Initial message"
        )

        initial_created_at = message.created_at
        assert message.is_active is True

        message.intent = "product_inquiry"
        assert message.intent == "product_inquiry"
        assert message.is_product_query() is True

        message.intent = "general"
        assert message.intent == "general"
        assert message.is_product_query() is False

        message.is_active = False
        assert message.is_active is False

        assert message.created_at == initial_created_at

    def test_metadata_storage(self):
        metadata = {
            "source": "whatsapp",
            "user_agent": "mobile",
            "session_id": "sess-456",
            "confidence_score": 0.95,
            "extracted_entities": ["plat baja", "5mm"],
            "processing_time_ms": 150,
        }

        message = MessageFactory.create_user_message(
            conversation_id="conv-123",
            content="Test message",
            metadata=metadata,
        )

        assert message.metadata == metadata
        assert message.metadata["source"] == "whatsapp"
        assert message.metadata["confidence_score"] == 0.95
        assert "extracted_entities" in message.metadata
        assert len(message.metadata["extracted_entities"]) == 2

        message.metadata["new_field"] = "new_value"
        assert message.metadata["new_field"] == "new_value"

    def test_message_with_full_context(self):
        message = MessageFactory.create_user_message(
            conversation_id="conv-789",
            content="Saya ingin membeli plat baja 5mm sebanyak 10 lembar",
            intent="product_inquiry",
            metadata={"product_sku": "STEEL-001", "quantity": 10, "unit": "lembar"},
        )

        assert message.conversation_id == "conv-789"
        assert message.sender_type == "user"
        assert message.content == "Saya ingin membeli plat baja 5mm sebanyak 10 lembar"
        assert message.detected_language == "id"
        assert message.intent == "product_inquiry"
        assert message.is_product_query() is True
        assert message.metadata["quantity"] == 10
        assert message.metadata["unit"] == "lembar"

    def test_ai_agent_message(self):
        ai_response = MessageFactory.create_ai_message(
            conversation_id="conv-123",
            content="Plat baja 5mm tersedia dengan harga Rp 150.000 per lembar",
            metadata={
                "response_type": "product_info",
                "confidence": 0.98,
                "products_mentioned": ["plat baja 5mm"],
            },
        )

        assert ai_response.sender_type == "ai_agent"
        assert (
            ai_response.content
            == "Plat baja 5mm tersedia dengan harga Rp 150.000 per lembar"
        )
        assert ai_response.metadata["response_type"] == "product_info"
        assert ai_response.metadata["confidence"] == 0.98

        assert ai_response.is_product_query() is False

    def test_message_equality(self):
        message1 = Message(
            conversation_id="conv-123", sender_type="user", content="Test message"
        )

        message2 = Message(
            conversation_id="conv-123", sender_type="user", content="Test message"
        )

        assert message1.id != message2.id
        assert message1.conversation_id == message2.conversation_id
        assert message1.content == message2.content

    def test_message_serialization(self):
        message = MessageFactory.create_product_query(
            conversation_id="conv-123",
            intent="price_check",
        )
        message.content = "Test serialization"
        message.metadata = {"key": "value"}

        message_dict = message.model_dump()

        assert "id" in message_dict
        assert "conversation_id" in message_dict
        assert "sender_type" in message_dict
        assert "content" in message_dict
        assert "detected_language" in message_dict
        assert "intent" in message_dict
        assert "metadata" in message_dict
        assert "created_at" in message_dict
        assert "updated_at" in message_dict
        assert "is_active" in message_dict

        assert message_dict["conversation_id"] == "conv-123"
        assert message_dict["sender_type"] == "user"
        assert message_dict["content"] == "Test serialization"
        assert message_dict["detected_language"] == "id"
        assert message_dict["intent"] == "price_check"
        assert message_dict["metadata"] == {"key": "value"}
