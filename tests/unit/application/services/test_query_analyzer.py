"""Unit tests for QueryAnalyzerService"""

from datetime import datetime, timezone

import pytest

from src.application.dto.message_dto import MessageDTO


class TestQueryAnalyzerService:
    """Test cases for QueryAnalyzerService"""

    @pytest.mark.asyncio
    async def test_analyze_with_no_context(
        self,
        query_analyzer_service,
        mock_query_analyzer,
        sample_query_intent_with_clarification,
    ):
        """Test analyzing query without conversation context"""
        # Arrange
        query = "Saya mencari besi hollow"
        mock_query_analyzer.analyze_mock.return_value = (
            sample_query_intent_with_clarification
        )

        # Act
        result = await query_analyzer_service.analyze(query)

        # Assert
        assert result == sample_query_intent_with_clarification
        mock_query_analyzer.analyze_mock.assert_called_once_with(query, None)

    @pytest.mark.asyncio
    async def test_analyze_with_context(
        self,
        query_analyzer_service,
        mock_query_analyzer,
        sample_query_analyzer_messages,
        sample_query_intent_with_clarification,
    ):
        """Test analyzing query with conversation context"""
        # Arrange
        query = "Yang ukuran 4x4"
        mock_query_analyzer.analyze_mock.return_value = (
            sample_query_intent_with_clarification
        )

        # Act
        result = await query_analyzer_service.analyze(
            query, conversation_context=sample_query_analyzer_messages
        )

        # Assert
        assert result == sample_query_intent_with_clarification
        mock_query_analyzer.analyze_mock.assert_called_once_with(
            query, sample_query_analyzer_messages
        )

    @pytest.mark.asyncio
    async def test_analyze_with_empty_context_list(
        self, query_analyzer_service, mock_query_analyzer, sample_query_intent_product
    ):
        """Test analyzing with empty conversation context list"""
        # Arrange
        query = "Saya mencari produk"
        mock_query_analyzer.analyze_mock.return_value = sample_query_intent_product

        # Act
        result = await query_analyzer_service.analyze(query, conversation_context=[])

        # Assert
        assert result == sample_query_intent_product
        mock_query_analyzer.analyze_mock.assert_called_once_with(query, [])

    @pytest.mark.asyncio
    async def test_analyze_error_handling(
        self, query_analyzer_service, mock_query_analyzer
    ):
        """Test error handling in analyze method"""
        # Arrange
        query = "Test query"
        mock_query_analyzer.analyze_mock.side_effect = Exception("Infrastructure error")

        # Act
        result = await query_analyzer_service.analyze(query)

        # Assert
        assert result.type == "general"
        assert result.clarification_stage == "initial"
        assert result.requires_human_intervention is True
        assert result.confidence == 0.0
        assert "kesulitan memahami" in result.suggested_response

    def test_prepare_conversation_context_with_messages(
        self, query_analyzer_service, sample_query_analyzer_messages
    ):
        """Test preparing conversation context with valid messages"""
        # Act
        result = query_analyzer_service._prepare_conversation_context(
            sample_query_analyzer_messages
        )

        # Assert
        assert result == sample_query_analyzer_messages
        assert len(result) == 3

    def test_prepare_conversation_context_with_none(self, query_analyzer_service):
        """Test preparing conversation context with None"""
        # Act
        result = query_analyzer_service._prepare_conversation_context(None)

        # Assert
        assert result is None

    def test_prepare_conversation_context_with_empty_list(self, query_analyzer_service):
        """Test preparing conversation context with empty list"""
        # Act
        result = query_analyzer_service._prepare_conversation_context([])

        # Assert
        assert result is None

    def test_enhance_query_intent(
        self,
        query_analyzer_service,
        sample_query_intent_product,
        sample_query_analyzer_messages,
    ):
        """Test enhancing query intent (currently passthrough)"""
        # Act
        result = query_analyzer_service._enhance_query_intent(
            sample_query_intent_product, sample_query_analyzer_messages
        )

        # Assert
        assert result == sample_query_intent_product

    def test_create_fallback_intent(self, query_analyzer_service):
        """Test creating fallback intent for errors"""
        # Arrange
        query = "Test query"
        error_message = "Test error"

        # Act
        result = query_analyzer_service._create_fallback_intent(query, error_message)

        # Assert
        assert result.type == "general"
        assert result.clarification_stage == "initial"
        assert result.query_level == "ambiguous"
        assert result.next_action == "provide_info"
        assert result.original_query == query
        assert result.current_query == query
        assert result.confidence == 0.0
        assert result.requires_human_intervention is True
        assert "Maaf" in result.suggested_response

    @pytest.mark.asyncio
    async def test_extract_conversation_history(
        self, query_analyzer_service, sample_query_analyzer_messages
    ):
        """Test extracting conversation history from messages"""
        # Act
        result = await query_analyzer_service.extract_conversation_history(
            sample_query_analyzer_messages
        )

        # Assert
        assert len(result) == 3
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Saya mencari besi hollow"
        assert result[0]["timestamp"] == "2024-01-01T10:00:00+00:00"

        assert result[1]["role"] == "ai_agent"
        assert result[1]["content"] == (
            "Kami memiliki berbagai ukuran besi hollow. " "Ukuran apa yang Anda cari?"
        )

        assert result[2]["role"] == "user"
        assert result[2]["content"] == "Yang ukuran 4x4"

    @pytest.mark.asyncio
    async def test_extract_conversation_history_with_no_timestamp(
        self, query_analyzer_service
    ):
        """Test extracting history when messages have no timestamp"""
        # Arrange
        messages = [
            MessageDTO(
                content="Test message",
                sender_type="user",
                session_id="session-123",
                timestamp=None,
            )
        ]

        # Act
        result = await query_analyzer_service.extract_conversation_history(messages)

        # Assert
        assert len(result) == 1
        assert result[0]["timestamp"] is None

    @pytest.mark.asyncio
    async def test_analyze_filters_invalid_sender_types(
        self, query_analyzer_service, mock_query_analyzer, sample_query_intent_product
    ):
        """Test that prepare_conversation_context filters out invalid sender types"""
        # Arrange
        messages_with_system = [
            MessageDTO(
                content="User message", sender_type="user", session_id="session-123"
            ),
            MessageDTO(
                content="System message",
                sender_type="system",  # Invalid type, should be filtered
                session_id="session-123",
            ),
            MessageDTO(
                content="AI message", sender_type="ai_agent", session_id="session-123"
            ),
        ]

        prepared = query_analyzer_service._prepare_conversation_context(
            messages_with_system
        )

        # Assert
        assert len(prepared) == 2  # System message filtered out
        assert all(msg.sender_type in ["user", "ai_agent"] for msg in prepared)
