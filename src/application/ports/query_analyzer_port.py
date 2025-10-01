from typing import List, Optional, Protocol

from src.application.dto.message_dto import MessageDTO
from src.domain.value_objects.query_intent import QueryIntent


class QueryAnalyzerPort(Protocol):
    """Port for query intent analysis"""

    async def analyze(
        self, query: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """Analyze query to determine intent

        Args:
            query: The user's query text to analyze
            conversation_context: Optional list of previous messages for context

        Returns:
            QueryIntent: The analyzed intent with clarification needs and context
        """
        ...
