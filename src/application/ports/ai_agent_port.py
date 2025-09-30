from typing import List, Optional, Protocol

from src.application.dto.message_dto import MessageDTO


class AIAgentPort(Protocol):
    async def generate_response(
        self, message: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> str:
        ...
