"""Query Analyzer Service

This service orchestrates query intent analysis by:
1. Preparing conversation context from DTOs
2. Delegating to infrastructure implementation
3. Enhancing results with application-level context
"""

import logging
from typing import Dict, List, Optional

from src.application.dto.message_dto import MessageDTO
from src.application.ports.query_analyzer_port import QueryAnalyzerPort
from src.domain.value_objects.query_intent import ConversationContext, QueryIntent

logger = logging.getLogger(__name__)


class QueryAnalyzerService:
    """Application service for query intent analysis

    This service acts as an orchestrator between the application layer
    and infrastructure implementation, handling context preparation
    and delegation.
    """

    def __init__(self, query_analyzer: QueryAnalyzerPort):
        """Initialize the service with infrastructure dependency

        Args:
            query_analyzer: Infrastructure implementation of QueryAnalyzerPort
        """
        self._query_analyzer = query_analyzer
        logger.info("QueryAnalyzerService initialized")

    async def analyze(
        self, query: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """Analyze query intent with conversation context

        Args:
            query: The user's query text to analyze
            conversation_context: Optional list of previous messages for context

        Returns:
            QueryIntent: The analyzed intent with clarification needs and context
        """
        logger.debug(f"Analyzing query: {query[:100]}...")

        # Prepare conversation context if provided
        prepared_context = self._prepare_conversation_context(conversation_context)

        # Log context info for debugging
        if prepared_context:
            logger.debug(
                f"Using conversation context with {len(prepared_context)} messages"
            )

        try:
            # Delegate to infrastructure implementation
            query_intent = await self._query_analyzer.analyze(
                query=query, conversation_context=conversation_context
            )

            # Enhance with application-level context if needed
            enhanced_intent = self._enhance_query_intent(query_intent, prepared_context)

            logger.info(
                f"Query analyzed - Type: {enhanced_intent.type}, "
                f"Stage: {enhanced_intent.clarification_stage}, "
                f"Confidence: {enhanced_intent.confidence}"
            )

            return enhanced_intent

        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}", exc_info=True)
            # Return a default intent for general handling
            return self._create_fallback_intent(query, str(e))

    def _prepare_conversation_context(
        self, messages: Optional[List[MessageDTO]]
    ) -> Optional[List[MessageDTO]]:
        """Prepare and validate conversation context

        Args:
            messages: Raw message DTOs from the application

        Returns:
            Prepared message list or None if empty/invalid
        """
        if not messages:
            return None

        # Filter out system messages and ensure proper ordering
        prepared = []
        for msg in messages:
            if msg.sender_type in ["user", "ai_agent"]:
                prepared.append(msg)

        # Return None if no valid messages after filtering
        return prepared if prepared else None

    def _enhance_query_intent(
        self,
        query_intent: QueryIntent,
        conversation_context: Optional[List[MessageDTO]],
    ) -> QueryIntent:
        """Enhance query intent with application-level context

        This method can add additional application-specific logic
        without modifying the infrastructure analysis.

        Args:
            query_intent: The intent from infrastructure analysis
            conversation_context: Prepared conversation context

        Returns:
            Enhanced QueryIntent
        """
        # For now, return as-is. This is where we could add:
        # - User preference tracking
        # - Session-specific context
        # - Business rule overrides
        # - A/B testing variations
        return query_intent

    def _create_fallback_intent(self, query: str, error_message: str) -> QueryIntent:
        """Create a fallback intent for error scenarios

        Args:
            query: Original query that failed
            error_message: Error details for logging

        Returns:
            Safe fallback QueryIntent
        """
        logger.warning(f"Creating fallback intent due to: {error_message}")

        return QueryIntent(
            type="general",
            clarification_stage="initial",
            query_level="ambiguous",
            conversation_context=ConversationContext(),
            next_action="provide_info",
            next_clarification=None,
            response_data=None,
            original_query=query,
            current_query=query,
            confidence=0.0,
            requires_human_intervention=True,
            suggested_response=(
                "Maaf, saya mengalami kesulitan memahami permintaan Anda. "
                "Bisakah Anda memberikan lebih banyak detail tentang produk "
                "yang Anda cari?"
            ),
        )

    async def extract_conversation_history(
        self, messages: List[MessageDTO]
    ) -> List[Dict[str, Optional[str]]]:
        """Extract conversation history for context building

        Args:
            messages: List of message DTOs

        Returns:
            Formatted conversation history
        """
        history = []
        for msg in messages:
            history.append(
                {
                    "role": msg.sender_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
            )
        return history
