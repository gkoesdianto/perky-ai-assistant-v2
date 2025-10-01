"""WebSocket endpoint for real-time chat communication."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from src.application.services.chat_orchestrator import ChatOrchestrator
from src.core.config import settings
from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.message_handler import (
    MessageRateLimiter,
    MessageValidator,
)
from src.presentation.websocket.message_queue import MessageQueue
from src.presentation.websocket.rate_limiter import RateLimiter
from src.presentation.websocket.reconnection import ReconnectionManager
from src.presentation.websocket.session_manager import SessionManager
from src.presentation.websocket.types import MessageType, SystemEvent, WebSocketMessage

logger = logging.getLogger(__name__)


class ChatWebSocket:
    """WebSocket endpoint for real-time chat communication."""

    def __init__(
        self,
        chat_orchestrator: ChatOrchestrator,
        connection_manager: Optional[ConnectionManager] = None,
        session_manager: Optional[SessionManager] = None,
        message_queue: Optional[MessageQueue] = None,
        rate_limiter: Optional[RateLimiter] = None,
        message_validator: Optional[MessageValidator] = None,
        message_rate_limiter: Optional[MessageRateLimiter] = None,
        reconnection_manager: Optional[ReconnectionManager] = None,
    ):
        """
        Initialize ChatWebSocket handler.

        Args:
            chat_orchestrator: Chat orchestration service
            connection_manager: Optional connection manager (creates default if None)
            session_manager: Optional session manager (creates default if None)
            message_queue: Optional message queue (creates default if None)
            rate_limiter: Optional rate limiter (creates default if None)
            message_validator: Optional message validator (creates default if None)
            message_rate_limiter: Optional enhanced rate limiter
            reconnection_manager: Optional reconnection manager
        """
        self.chat_orchestrator = chat_orchestrator
        self.connection_manager = connection_manager or ConnectionManager()
        self.session_manager = session_manager or SessionManager()
        self.message_queue = message_queue or MessageQueue()
        self.rate_limiter = rate_limiter or RateLimiter(
            max_per_minute=settings.MAX_MESSAGES_PER_MINUTE or 10
        )
        self.message_validator = message_validator or MessageValidator()
        self.message_rate_limiter = message_rate_limiter or MessageRateLimiter(
            max_messages_per_minute=settings.MAX_MESSAGES_PER_MINUTE or 10,
            max_messages_per_hour=500,
            max_burst_size=5,
        )
        self.reconnection_manager = reconnection_manager or ReconnectionManager()
        self.last_activity: Dict[str, datetime] = {}

    async def websocket_endpoint(self, websocket: WebSocket, session_id: str):
        """
        Main WebSocket endpoint handler with reconnection support.

        Args:
            websocket: FastAPI WebSocket instance
            session_id: Unique session identifier
        """
        # Start reconnection manager if not already running
        await self.reconnection_manager.start()

        # Check for reconnection
        session_state = await self.reconnection_manager.handle_reconnection(
            session_id=session_id,
            new_connection_id=f"{session_id}-{uuid.uuid4().hex[:8]}",
        )

        # Generate connection ID (use reconnection ID if available)
        if session_state and session_state.connection_id:
            connection_id = session_state.connection_id
            is_reconnection = True
        else:
            connection_id = f"{session_id}-{uuid.uuid4().hex[:8]}"
            is_reconnection = False

        # Extract metadata from headers
        metadata = {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "origin": websocket.headers.get("origin", "unknown"),
            "accept_language": websocket.headers.get("accept-language", "en"),
            "is_reconnection": is_reconnection,
        }

        # Establish connection
        connected = await self.connection_manager.connect(
            websocket=websocket, connection_id=connection_id
        )

        if not connected:
            await websocket.close(code=1000)
            return

        # Register connection with session
        await self.session_manager.add_connection(session_id, connection_id)

        try:
            # Initialize session
            await self._handle_connection(
                connection_id=connection_id, session_id=session_id, metadata=metadata
            )

            # Start message queue worker if not already running
            if not self.message_queue.is_running:
                await self.message_queue.start_worker(
                    lambda msg: self._process_queued_message(msg)
                )

            # Start background tasks
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(connection_id, session_id)
            )
            health_check_task = asyncio.create_task(self._health_check_loop())

            # Main message loop
            await self._message_loop(
                websocket=websocket, connection_id=connection_id, session_id=session_id
            )

        except WebSocketDisconnect:
            logger.info(f"Client {connection_id} disconnected normally")

        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}", exc_info=True)
            await self._send_error(connection_id, str(e))

        finally:
            # Register disconnection for potential reconnection
            self.reconnection_manager.register_disconnection(
                session_id=session_id,
                connection_id=connection_id,
                state={
                    "last_activity": self.last_activity.get(connection_id),
                    "metadata": metadata,
                },
            )

            # Cleanup tasks
            if "heartbeat_task" in locals():
                heartbeat_task.cancel()
            if "health_check_task" in locals():
                health_check_task.cancel()

            # Disconnect client
            await self.connection_manager.disconnect(connection_id)
            await self.session_manager.remove_connection(session_id, connection_id)

            # Clean up activity tracker and rate limiter
            if connection_id in self.last_activity:
                del self.last_activity[connection_id]

            # Reset rate limits for disconnected connection
            self.message_rate_limiter.reset_connection(connection_id)

            # Notify other connections in session about disconnection
            await self.broadcast_to_session(
                message={
                    "type": MessageType.SYSTEM.value,
                    "event": SystemEvent.DISCONNECTED.value,
                    "message": f"Koneksi {connection_id[-8:]} terputus",
                },
                session_id=session_id,
                exclude_connection=connection_id,
            )

    async def _handle_connection(
        self, connection_id: str, session_id: str, metadata: dict
    ):
        """
        Handle new connection setup.

        Args:
            connection_id: Unique connection identifier
            session_id: Session identifier
            metadata: Connection metadata
        """
        # Start or resume session
        session_dto = await self.chat_orchestrator.handle_new_connection(
            session_id=session_id, metadata=metadata
        )

        # Send welcome message
        welcome_message = {
            "type": MessageType.SYSTEM.value,
            "event": SystemEvent.CONNECTED.value,
            "message": (
                "Selamat datang di SMS Perkasa Steel Chat! "
                "Ada yang bisa PERKY bantu?"
            ),
            "session": {
                "session_id": session_dto.session_id,
                "started_at": session_dto.started_at.isoformat(),
                "is_active": session_dto.is_active,
            },
            "timestamp": datetime.now().isoformat(),
        }

        await self.send_personal_message(welcome_message, connection_id)

        # Load conversation history if exists
        conversation = await self.chat_orchestrator.get_conversation_history(session_id)

        if conversation and conversation.messages:
            # Send last 10 messages as history
            history_messages = conversation.messages[-10:]

            for msg in history_messages:
                await self.send_personal_message(
                    {
                        "type": (
                            MessageType.USER_MESSAGE.value
                            if msg.sender_type == "user"
                            else MessageType.AI_RESPONSE.value
                        ),
                        "message": msg.content,
                        "timestamp": (msg.timestamp or datetime.now()).isoformat(),
                        "metadata": msg.metadata,
                    },
                    connection_id,
                )

        # Update activity tracker
        self.last_activity[connection_id] = datetime.now()

    async def _message_loop(
        self, websocket: WebSocket, connection_id: str, session_id: str
    ):
        """
        Handle incoming messages.

        Args:
            websocket: WebSocket connection
            connection_id: Connection identifier
            session_id: Session identifier
        """
        while True:
            try:
                # Receive message
                raw_data = await websocket.receive_text()

                # Process the received message
                await self._process_raw_message(
                    raw_data=raw_data,
                    connection_id=connection_id,
                    session_id=session_id,
                )

            except WebSocketDisconnect:
                break

            except Exception as e:
                logger.error(f"Message processing error: {e}", exc_info=True)
                await self._send_error(connection_id, "Terjadi kesalahan")

    async def _process_raw_message(
        self, raw_data: str, connection_id: str, session_id: str
    ):
        """
        Process raw message data.

        Args:
            raw_data: Raw message string
            connection_id: Connection identifier
            session_id: Session identifier
        """
        try:
            data = json.loads(raw_data)
            await self._route_message(
                data=data, connection_id=connection_id, session_id=session_id
            )
        except json.JSONDecodeError as e:
            await self._send_validation_error(
                connection_id, f"Format JSON tidak valid: {e}"
            )

    async def _route_message(self, data: dict, connection_id: str, session_id: str):
        """
        Route message based on type.

        Args:
            data: Parsed message data
            connection_id: Connection identifier
            session_id: Session identifier
        """
        message_type = data.get("type")

        if message_type == MessageType.USER_MESSAGE.value:
            await self._process_user_message(
                data=data, connection_id=connection_id, session_id=session_id
            )
        elif message_type == "ping":
            await self._handle_ping(connection_id)
        elif message_type == MessageType.HEARTBEAT.value:
            self.last_activity[connection_id] = datetime.now()
        else:
            await self._handle_unknown_message_type(
                connection_id=connection_id, message_type=message_type or "unknown"
            )

    async def _process_user_message(
        self, data: dict, connection_id: str, session_id: str
    ):
        """
        Process user message.

        Args:
            data: Message data
            connection_id: Connection identifier
            session_id: Session identifier
        """
        try:
            message = WebSocketMessage(**data)
            await self._handle_user_message(
                connection_id=connection_id,
                session_id=session_id,
                message=message,
            )
        except (ValueError, TypeError) as e:
            await self._send_validation_error(
                connection_id, f"Format pesan tidak valid: {e}"
            )

    async def _handle_unknown_message_type(self, connection_id: str, message_type: str):
        """
        Handle unknown message type.

        Args:
            connection_id: Connection identifier
            message_type: Unknown message type
        """
        await self._send_validation_error(
            connection_id,
            f"Validation error: Unknown message type '{message_type}'",
        )
        logger.warning(f"Unknown message type from {connection_id}: {message_type}")

    async def _handle_user_message(
        self, connection_id: str, session_id: str, message: WebSocketMessage
    ):
        """
        Process user message with enhanced validation and rate limiting.

        Args:
            connection_id: Connection identifier
            session_id: Session identifier
            message: WebSocket message
        """
        # Validate message content
        is_valid, error_msg = self.message_validator.validate_user_message(
            message.message if message.message else ""
        )
        if not is_valid:
            await self._send_validation_error(
                connection_id, error_msg or "Invalid message"
            )
            return

        # Check enhanced rate limit
        is_allowed, rate_error = self.message_rate_limiter.is_allowed(connection_id)
        if not is_allowed:
            await self._send_validation_error(
                connection_id, rate_error or "Rate limit exceeded"
            )
            return

        # Sanitize message for safe display
        sanitized_message = self.message_validator.sanitize_message(
            message.message or ""
        )

        # Send typing indicator
        typing_message = {
            "type": MessageType.SYSTEM.value,
            "event": SystemEvent.TYPING.value,
            "message": "PERKY sedang mengetik...",
            "timestamp": datetime.now().isoformat(),
        }

        await self.send_personal_message(typing_message, connection_id)

        # Broadcast to other connections in session
        await self.broadcast_to_session(
            message={
                "type": MessageType.USER_MESSAGE.value,
                "message": sanitized_message,
                "metadata": {"from_connection": connection_id[-8:]},
                "timestamp": datetime.now().isoformat(),
            },
            session_id=session_id,
            exclude_connection=connection_id,
        )

        # Queue message for processing
        message_data = {
            "connection_id": connection_id,
            "session_id": session_id,
            "content": message.message,
            "metadata": message.metadata,
        }

        queued = await self.message_queue.add_message(message_data)
        if not queued:
            await self._send_error(
                connection_id, "Sistem sedang sibuk. Silakan coba lagi."
            )

    async def _process_queued_message(self, message_data: Dict[str, Any]):
        """
        Process a queued message.

        Args:
            message_data: Message data from queue
        """
        connection_id = message_data["connection_id"]
        session_id = message_data["session_id"]
        content = message_data["content"]
        metadata = message_data.get("metadata")

        try:
            # Process message through orchestrator
            response = await self.chat_orchestrator.handle_user_message(
                session_id=session_id, content=content, metadata=metadata
            )

            # Send AI response
            response_message = {
                "type": MessageType.AI_RESPONSE.value,
                "message": response.content,
                "metadata": response.metadata,
                "timestamp": (response.timestamp or datetime.now()).isoformat(),
            }

            # Send to requester
            await self.send_personal_message(response_message, connection_id)

            # Broadcast to session
            await self.broadcast_to_session(
                response_message,
                session_id=session_id,
                exclude_connection=connection_id,
            )

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            await self._send_error(
                connection_id, "Maaf, terjadi kesalahan. Silakan coba lagi."
            )

    async def _handle_ping(self, connection_id: str):
        """
        Respond to ping with pong.

        Args:
            connection_id: Connection identifier
        """
        await self.send_personal_message(
            {"type": "pong", "timestamp": datetime.now().isoformat()},
            connection_id,
        )

    async def _send_error(self, connection_id: str, error_message: str):
        """
        Send error message to client.

        Args:
            connection_id: Connection identifier
            error_message: Error message to send
        """
        await self.send_personal_message(
            {
                "type": MessageType.ERROR.value,
                "event": SystemEvent.ERROR.value,
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
            },
            connection_id,
        )

    async def _send_validation_error(self, connection_id: str, error_message: str):
        """
        Send validation error message to client.

        Args:
            connection_id: Connection identifier
            error_message: Error message to send
        """
        await self.send_personal_message(
            {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
            },
            connection_id,
        )

    async def _heartbeat_loop(self, connection_id: str, session_id: str):
        """
        Send periodic heartbeat.

        Args:
            connection_id: Connection identifier
            session_id: Session identifier
        """
        heartbeat_interval = settings.WEBSOCKET_HEARTBEAT_INTERVAL or 30

        while True:
            try:
                await asyncio.sleep(heartbeat_interval)

                if self.connection_manager.is_connected(connection_id):
                    await self.send_personal_message(
                        {
                            "type": MessageType.HEARTBEAT.value,
                            "timestamp": datetime.now().isoformat(),
                        },
                        connection_id,
                    )
                else:
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _health_check_loop(self):
        """Periodic health check for all connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.check_connection_health()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def check_connection_health(self):
        """Check health of all connections."""
        now = datetime.now()
        stale_timeout = 120  # 2 minutes

        stale_connections = []
        for connection_id, last_seen in self.last_activity.items():
            if (now - last_seen).total_seconds() > stale_timeout:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            await self.connection_manager.disconnect(connection_id)
            if connection_id in self.last_activity:
                del self.last_activity[connection_id]

    async def send_personal_message(self, message: dict, connection_id: str) -> bool:
        """
        Send message to specific connection.

        Args:
            message: Message to send
            connection_id: Target connection

        Returns:
            True if sent successfully
        """
        return await self.connection_manager.send_message(connection_id, message)

    async def broadcast_to_session(
        self, message: dict, session_id: str, exclude_connection: Optional[str] = None
    ):
        """
        Broadcast message to all connections in a session.

        Args:
            message: Message to broadcast
            session_id: Target session
            exclude_connection: Optional connection to exclude
        """
        connections = await self.session_manager.get_session_connections(session_id)

        for conn_id in connections:
            if conn_id != exclude_connection:
                await self.connection_manager.send_message(conn_id, message)
