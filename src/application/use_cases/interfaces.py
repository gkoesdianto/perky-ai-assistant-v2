from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from src.application.dto.session_dto import SessionDTO
from src.application.dto.message_dto import MessageDTO
from src.application.dto.conversation_dto import ConversationDTO


class StartChatSessionUseCase(ABC):

    @abstractmethod
    async def execute(self, session_id: str, metadata: Dict[str, Any]) -> SessionDTO:
        pass


class ProcessUserMessageUseCase(ABC):

    @abstractmethod
    async def execute(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDTO:
        pass


class GetConversationUseCase(ABC):

    @abstractmethod
    async def execute(self, session_id: str) -> Optional[ConversationDTO]:
        pass
