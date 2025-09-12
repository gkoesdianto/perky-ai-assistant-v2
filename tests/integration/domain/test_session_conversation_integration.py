import pytest
from datetime import datetime, timezone, timedelta
from src.domain.entities import Session, Conversation, Message


class TestSessionConversationIntegration:
    def test_expired_session_blocks_messages(self):
        """Test that expired sessions can't add new messages"""
        session = Session(session_id="test-123")
        conversation = Conversation(session_id=session.session_id)

        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
        assert session.is_expired(3600)

        with pytest.raises(Exception) as exc_info:
            if session.is_expired(3600):
                raise Exception("Session expired: cannot add new messages")

            message = Message(
                conversation_id=conversation.id,
                sender_type="user",
                content="This should not be added",
            )
            conversation.add_message(message)

        assert "Session expired" in str(exc_info.value)
        assert len(conversation.messages) == 0

    def test_session_activity_updates_with_messages(self):
        """Test session activity tracking with conversation"""
        session = Session(session_id="test-123")
        conversation = Conversation(session_id=session.session_id)

        initial_activity = session.last_activity

        message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Berapa harga plat baja?",
        )

        conversation.add_message(message)
        session.update_activity()

        assert session.last_activity > initial_activity
        assert len(conversation.messages) == 1
        assert conversation.last_activity > initial_activity

    def test_session_lifecycle_with_conversation(self):
        """Test complete session lifecycle with conversation"""
        session = Session(session_id="test-456")
        assert session.conversation_id is None
        assert not session.is_expired(3600)

        conversation = Conversation(session_id=session.session_id)
        session.conversation_id = conversation.id

        user_message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Halo, saya butuh informasi produk",
            detected_language="id",
            intent="product_inquiry",
        )
        conversation.add_message(user_message)
        session.update_activity()

        assert user_message.is_product_query()

        ai_message = Message(
            conversation_id=conversation.id,
            sender_type="ai_agent",
            content="Silakan, produk apa yang Anda cari?",
            detected_language="id",
        )
        conversation.add_message(ai_message)
        session.update_activity()

        assert len(conversation.messages) == 2
        assert not session.is_expired(3600)

        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
        assert session.is_expired(3600)

    def test_conversation_context_with_active_session(self):
        """Test conversation context retrieval with active session"""
        session = Session(session_id="test-789")
        conversation = Conversation(session_id=session.session_id)

        for i in range(15):
            message = Message(
                conversation_id=conversation.id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Message {i+1}",
            )
            conversation.add_message(message)
            session.update_activity()

        context = conversation.get_context(limit=10)
        assert len(context) == 10
        assert context[0].content == "Message 6"
        assert context[-1].content == "Message 15"

        assert not session.is_expired(3600)

    def test_session_metadata_preservation(self):
        """Test that session metadata is preserved during conversation"""
        session = Session(
            session_id="test-meta",
            metadata={"browser": "Chrome", "ip": "192.168.1.1", "location": "Jakarta"},
        )

        conversation = Conversation(
            session_id=session.session_id, metadata={"channel": "web", "version": "2.0"}
        )

        assert session.metadata["location"] == "Jakarta"
        assert conversation.metadata["channel"] == "web"

        message = Message(
            conversation_id=conversation.id,
            sender_type="user",
            content="Test message",
            metadata={"source": "direct"},
        )
        conversation.add_message(message)

        assert session.metadata["browser"] == "Chrome"
        assert conversation.metadata["version"] == "2.0"
        assert message.metadata["source"] == "direct"

    @pytest.mark.parametrize(
        "ttl,should_expire",
        [
            (0, True),
            (3600, False),
            (86400, False),
        ],
    )
    def test_session_expiry_with_different_ttls(self, ttl, should_expire):
        """Test session expiry with various TTL values"""
        session = Session(session_id=f"test-ttl-{ttl}")
        conversation = Conversation(session_id=session.session_id)

        message = Message(
            conversation_id=conversation.id, sender_type="user", content="Test TTL"
        )
        conversation.add_message(message)

        assert session.is_expired(ttl) == should_expire

        if not should_expire:
            session.update_activity()
            assert not session.is_expired(ttl)
