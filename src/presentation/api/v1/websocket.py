"""WebSocket router for real-time chat communication."""

from fastapi import APIRouter, WebSocket, Depends, Query

from src.presentation.websocket.chat_ws import ChatWebSocket
from src.presentation.dependencies import get_chat_orchestrator
from src.application.services.chat_orchestrator import ChatOrchestrator

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """
    WebSocket endpoint for real-time chat communication.

    Path Parameters:
    - session_id: Unique session identifier

    Message Protocol:
    - Send: {"type": "user_message", "message": "content"}
    - Receive: {"type": "ai_response", "message": "content"}
    - System: {"type": "system", "event": "typing|connected|error"}
    - Heartbeat: {"type": "heartbeat"}
    """
    chat_ws = ChatWebSocket(chat_orchestrator)
    await chat_ws.websocket_endpoint(websocket, session_id)


@router.websocket("/ws")
async def websocket_endpoint_query(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID"),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Alternative WebSocket endpoint using query parameters"""
    chat_ws = ChatWebSocket(chat_orchestrator)
    await chat_ws.websocket_endpoint(websocket, session_id)
