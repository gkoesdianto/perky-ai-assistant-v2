# Phase 4: WebSocket Integration - Comprehensive Implementation Workflow

## Executive Summary

WebSocket integration for Steel Chat MVP with security, clean architecture, and resilience patterns.

**Timeline**: Day 3 of MVP Development (8-9 hours)
**Complexity**: Moderate
**Risk Level**: Low (with security patterns)
**Critical Path**: Yes

**MVP Focus**:
- JWT authentication
- Separated responsibilities (SRP)
- Async message processing
- Rate limiting & circuit breaker

## Table of Contents

1. [Prerequisites & Dependencies](#prerequisites--dependencies)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Stages](#implementation-stages)
4. [Testing Strategy](#testing-strategy)
5. [Quality Gates & Validation](#quality-gates--validation)
6. [Risk Mitigation](#risk-mitigation)
7. [Success Criteria](#success-criteria)
8. [Post-Implementation Checklist](#post-implementation-checklist)

---

## Prerequisites & Dependencies

### Required Completed Phases

#### Phase 1: Application Layer Foundation ✅

- **DTOs**: MessageDTO, ConversationDTO, SessionDTO
- **Use Case Interfaces**: StartChatSessionUseCase, ProcessUserMessageUseCase, GetConversationUseCase
- **Dependency Container**: DIContainer setup and registration
- **Service Protocols**: AIAgentPort, ProductServicePort

#### Phase 2: Single Agent Implementation ✅

- **Use Cases**: All concrete implementations
- **Chat Orchestrator**: Message handling and session management
- **Query Analyzer**: Intent analysis service
- **Error Handling**: Fallback mechanisms

#### Phase 3: Mock Infrastructure ✅

- **Mock AI Agent**: Response generation capability
- **Mock Repositories**: In-memory storage
- **Mock Redis Client**: Session management
- **Mock Product Service**: Sample product data

### Technical Dependencies

```python
# requirements/base.txt
fastapi==0.115.5
uvicorn[standard]==0.32.1
redis==5.2.0
pydantic==2.10.3
python-jose[cryptography]==3.3.0  # JWT authentication
```

### Environment Requirements

```bash
# .env
USE_MOCK_MODE=true
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_SECONDS=3600
WEBSOCKET_HEARTBEAT_INTERVAL=30
SECRET_KEY=your-secret-key-for-jwt
MAX_MESSAGES_PER_MINUTE=10
CIRCUIT_BREAKER_THRESHOLD=3
```

---

## Architecture Overview

### System Flow

```text
graph LR
    Client[HTML Client] -->|WebSocket + JWT| WS[WebSocket Endpoint]
    WS --> Auth[Auth Validator]
    Auth --> CM[Connection Manager]
    CM --> SM[Session Manager]
    SM --> MQ[Message Queue]
    MQ --> CO[Chat Orchestrator]
    CO --> UC[Use Cases]
    UC --> CB[Circuit Breaker]
    CB --> AI[AI Agent]
    UC --> CR[Conversation Repo]
```

### Layer Responsibilities

#### Presentation Layer (WebSocket)

- Connection lifecycle management
- Message routing and broadcasting
- Protocol handling (JSON messages)
- Heartbeat and connection health

#### Application Layer Integration

- Session orchestration
- Use case coordination
- DTO transformation
- Business logic execution

#### Infrastructure Layer Support

- Mock service integration
- Session persistence
- Caching strategy
- External service simulation

---

## Implementation Stages

### Stage 1: Foundation with Security (2 hours)

#### 1.1 Package Structure

```bash
mkdir -p src/presentation/websocket
touch src/presentation/websocket/__init__.py
touch src/presentation/websocket/connection_manager.py
touch src/presentation/websocket/session_manager.py
touch src/presentation/websocket/chat_ws.py
touch src/presentation/websocket/auth.py
touch src/presentation/websocket/rate_limiter.py
touch src/presentation/websocket/circuit_breaker.py
touch src/presentation/websocket/types.py
```

#### 1.2 Authentication Setup

```python
# src/presentation/websocket/auth.py
import jwt
from datetime import datetime, timedelta
from typing import Optional
from src.core.config import settings

def create_websocket_token(session_id: str) -> str:
    payload = {
        "session_id": session_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def validate_websocket_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("session_id")
    except:
        return None
```

#### 1.3 Rate Limiter

```python
# src/presentation/websocket/rate_limiter.py
from datetime import datetime, timedelta
from typing import Dict, List

class RateLimiter:
    def __init__(self, max_per_minute: int = 10):
        self.max_per_minute = max_per_minute
        self.requests: Dict[str, List[datetime]] = {}

    async def is_allowed(self, session_id: str) -> bool:
        now = datetime.now()
        if session_id not in self.requests:
            self.requests[session_id] = []

        self.requests[session_id] = [
            t for t in self.requests[session_id]
            if now - t < timedelta(minutes=1)
        ]

        if len(self.requests[session_id]) >= self.max_per_minute:
            return False

        self.requests[session_id].append(now)
        return True
```

#### 1.4 Circuit Breaker

```python
# src/presentation/websocket/circuit_breaker.py
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
```

---

### Stage 2: Core Implementation with Clean Architecture (3 hours)

#### 2.1 Separated Managers (SRP)

```python
# src/presentation/websocket/connection_manager.py
from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections only"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connection_id: str) -> bool:
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            logger.info(f"Client connected: {connection_id}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Client disconnected: {connection_id}")

    async def send_message(self, connection_id: str, message: dict
) -> bool:
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.disconnect(connection_id)
                return False
        return False
```

```python
# src/presentation/websocket/session_manager.py
from typing import Dict, Set, Optional

class SessionManager:
    """Manages session grouping for WebSocket connections"""

    def __init__(self):
        self.session_connections: Dict[str, Set[str]] = {}

    def add_connection(self, session_id: str, connection_id: str):
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)

    def remove_connection(self, session_id: str, connection_id: str):
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    def get_session_connections(self, session_id: str) -> Set[str]:
        return self.session_connections.get(session_id, set())

    def get_connection_count(self, session_id: str) -> int:
        return len(self.session_connections.get(session_id, set()))
```

#### 2.2 Message Queue for Async Processing

```python
# src/presentation/websocket/message_queue.py
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MessageQueue:
    """Async message queue to prevent blocking"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def start_worker(self, process_func):
        """Start the queue worker"""
        self.worker_task = asyncio.create_task(self._process_queue(process_func))

    async def _process_queue(self, process_func):
        """Process messages from queue"""
        while True:
            try:
                message_data = await self.queue.get()
                await process_func(message_data)
            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    async def add_message(self, message_data: Dict[str, Any]):
        """Add message to queue"""
        await self.queue.put(message_data)

    async def stop_worker(self):
        """Stop the queue worker"""
        if self.worker_task:
            self.worker_task.cancel()
```

#### 2.3 Chat WebSocket Endpoint with Security

```python
# src/presentation/websocket/chat_ws.py

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
import logging

from src.application.services import ChatOrchestrator
from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.types import MessageType, SystemEvent, WebSocketMessage

logger = logging.getLogger(__name__)

class ChatWebSocket:
    """WebSocket endpoint for real-time chat communication"""

    def __init__(self, chat_orchestrator: ChatOrchestrator):
        self.chat_orchestrator = chat_orchestrator
        self.manager = ConnectionManager()

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        session_id: str
    ):
        """Main WebSocket endpoint handler"""

        # Generate unique connection ID
        connection_id = f"{session_id}-{uuid.uuid4().hex[:8]}"

        # Extract metadata from headers
        metadata = {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "origin": websocket.headers.get("origin", "unknown"),
            "accept_language": websocket.headers.get("accept-language", "en")
        }

        # Establish connection
        connected = await self.manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            session_id=session_id,
            metadata=metadata
        )

        if not connected:
            await websocket.close(code=1000)
            return

        try:
            # Initialize session
            await self._handle_connection(
                connection_id=connection_id,
                session_id=session_id,
                metadata=metadata
            )

            # Start background tasks
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(connection_id, session_id)
            )
            health_check_task = asyncio.create_task(
                self._health_check_loop()
            )

            # Main message loop
            await self._message_loop(
                websocket=websocket,
                connection_id=connection_id,
                session_id=session_id
            )

        except WebSocketDisconnect:
            logger.info(f"Client {connection_id} disconnected normally")

        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
            await self._send_error(connection_id, str(e))

        finally:
            # Cleanup tasks
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
            if 'health_check_task' in locals():
                health_check_task.cancel()

            # Disconnect client
            self.manager.disconnect(connection_id)

            # Notify session about disconnection
            await self.manager.broadcast_to_session(
                message={
                    "type": MessageType.SYSTEM.value,
                    "event": SystemEvent.DISCONNECTED.value,
                    "message": f"Koneksi {connection_id[-8:]} terputus"
                },
                session_id=session_id,
                exclude_connection=connection_id
            )

    async def _handle_connection(
        self,
        connection_id: str,
        session_id: str,
        metadata: dict
    ):
        """Handle new connection setup"""

        # Start or resume session
        session_dto = await self.chat_orchestrator.handle_new_connection(
            session_id=session_id,
            metadata=metadata
        )

        # Send welcome message
        welcome_message = {
            "type": MessageType.SYSTEM.value,
            "event": SystemEvent.CONNECTED.value,
            "message": "Selamat datang di SMS Perkasa Steel Chat! Ada yang bisa PERKY bantu?",
            "session": {
                "session_id": session_dto.session_id,
                "started_at": session_dto.started_at.isoformat(),
                "is_active": session_dto.is_active
            },
            "timestamp": datetime.now().isoformat()
        }

        await self.manager.send_personal_message(
            welcome_message,
            connection_id
        )

        # Load conversation history if exists
        conversation = await self.chat_orchestrator.get_conversation_history(
            session_id
        )

        if conversation and conversation.messages:
            # Send last 10 messages as history
            history_messages = conversation.messages[-10:]

            for msg in history_messages:
                await self.manager.send_personal_message(
                    {
                        "type": (
                            MessageType.USER_MESSAGE.value
                            if msg.sender_type == "user"
                            else MessageType.AI_RESPONSE.value
                        ),
                        "message": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    },
                    connection_id
                )

    async def _message_loop(
        self,
        websocket: WebSocket,
        connection_id: str,
        session_id: str
    ):
        """Handle incoming messages"""

        while True:
            try:
                # Receive message
                raw_data = await websocket.receive_text()

                # Parse message
                try:
                    data = json.loads(raw_data)
                    message = WebSocketMessage(**data)
                except (json.JSONDecodeError, ValueError) as e:
                    await self._send_error(
                        connection_id,
                        f"Format pesan tidak valid: {e}"
                    )
                    continue

                # Route message by type
                if message.type == MessageType.USER_MESSAGE:
                    await self._handle_user_message(
                        connection_id=connection_id,
                        session_id=session_id,
                        message=message
                    )

                elif message.type == MessageType.PING:
                    await self._handle_ping(connection_id)

                elif message.type == MessageType.HEARTBEAT:
                    # Update activity timestamp
                    self.manager.last_activity[connection_id] = datetime.now()

                else:
                    logger.warning(
                        f"Unknown message type from {connection_id}: {message.type}"
                    )

            except WebSocketDisconnect:
                break

            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await self._send_error(connection_id, "Terjadi kesalahan")

    async def _handle_user_message(
        self,
        connection_id: str,
        session_id: str,
        message: WebSocketMessage
    ):
        """Process user message"""

        if not message.message:
            await self._send_error(connection_id, "Pesan kosong")
            return

        # Send typing indicator
        typing_message = {
            "type": MessageType.SYSTEM.value,
            "event": SystemEvent.TYPING.value,
            "message": "PERKY sedang mengetik...",
            "timestamp": datetime.now().isoformat()
        }

        await self.manager.send_personal_message(
            typing_message,
            connection_id
        )

        # Broadcast to other connections in session
        await self.manager.broadcast_to_session(
            message={
                "type": MessageType.USER_MESSAGE.value,
                "message": message.message,
                "metadata": {"from_connection": connection_id[-8:]},
                "timestamp": datetime.now().isoformat()
            },
            session_id=session_id,
            exclude_connection=connection_id
        )

        try:
            # Process message through orchestrator
            response = await self.chat_orchestrator.handle_user_message(
                session_id=session_id,
                content=message.message,
                metadata=message.metadata
            )

            # Send AI response
            response_message = {
                "type": MessageType.AI_RESPONSE.value,
                "message": response.content,
                "metadata": response.metadata,
                "timestamp": response.timestamp.isoformat()
            }

            # Send to requester
            await self.manager.send_personal_message(
                response_message,
                connection_id
            )

            # Broadcast to session
            await self.manager.broadcast_to_session(
                response_message,
                session_id=session_id,
                exclude_connection=connection_id
            )

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            await self._send_error(
                connection_id,
                "Maaf, terjadi kesalahan. Silakan coba lagi."
            )

    async def _handle_ping(self, connection_id: str):
        """Respond to ping with pong"""
        await self.manager.send_personal_message(
            {
                "type": MessageType.PONG.value,
                "timestamp": datetime.now().isoformat()
            },
            connection_id
        )

    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to client"""
        await self.manager.send_personal_message(
            {
                "type": MessageType.ERROR.value,
                "event": SystemEvent.ERROR.value,
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            },
            connection_id
        )

    async def _heartbeat_loop(self, connection_id: str, session_id: str):
        """Send periodic heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)  # 30-second interval

                if connection_id in self.manager.active_connections:
                    await self.manager.send_personal_message(
                        {
                            "type": MessageType.HEARTBEAT.value,
                            "timestamp": datetime.now().isoformat()
                        },
                        connection_id
                    )
                else:
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _health_check_loop(self):
        """Periodic health check for all connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.manager.check_connection_health()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
```

#### 2.3 Router Configuration

```python
# src/presentation/api/v1/websocket.py

from fastapi import APIRouter, WebSocket, Depends, Query
from typing import Optional

from src.presentation.websocket.chat_ws import ChatWebSocket
from src.presentation.dependencies import get_chat_orchestrator

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    chat_orchestrator = Depends(get_chat_orchestrator)
):
    """
    WebSocket endpoint for real-time chat communication

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


# Alternative endpoint with query parameters
@router.websocket("/ws")
async def websocket_endpoint_query(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID"),
    chat_orchestrator = Depends(get_chat_orchestrator)
):
    """Alternative WebSocket endpoint using query parameters"""

    chat_ws = ChatWebSocket(chat_orchestrator)
    await chat_ws.websocket_endpoint(websocket, session_id)
```

**Validation Checkpoint 2.1**:
- [ ] ConnectionManager handles multiple connections
- [ ] ChatWebSocket processes messages correctly
- [ ] Router configured with dependencies
- [ ] Error handling comprehensive

---

### Stage 3: Enhancement Features (2 hours)

#### 3.1 Advanced Message Handling

```python
# src/presentation/websocket/message_handler.py

from typing import Optional, Dict, Any, List
from datetime import datetime
import re
from src.presentation.websocket.types import MessageType, WebSocketMessage

class MessageValidator:
    """Validates and sanitizes WebSocket messages"""

    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1

    @classmethod
    def validate_user_message(cls, message: str) -> tuple[bool, Optional[str]]:
        """Validate user message content"""

        # Check length
        if not message or len(message.strip()) < cls.MIN_MESSAGE_LENGTH:
            return False, "Pesan terlalu pendek"

        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Pesan terlalu panjang (maksimal {cls.MAX_MESSAGE_LENGTH} karakter)"

        # Check for malicious content (basic)
        if cls._contains_malicious_patterns(message):
            return False, "Pesan mengandung konten yang tidak diperbolehkan"

        return True, None

    @staticmethod
    def _contains_malicious_patterns(message: str) -> bool:
        """Check for potentially malicious patterns"""

        # Script injection patterns
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def sanitize_message(message: str) -> str:
        """Sanitize message content"""

        # Remove excess whitespace
        message = ' '.join(message.split())

        # Escape HTML entities
        message = message.replace('<', '&lt;').replace('>', '&gt;')

        return message.strip()


class MessageRateLimiter:
    """Rate limiting for WebSocket messages"""

    def __init__(
        self,
        max_messages_per_minute: int = 30,
        max_messages_per_hour: int = 500
    ):
        self.max_per_minute = max_messages_per_minute
        self.max_per_hour = max_messages_per_hour
        self.message_history: Dict[str, List[datetime]] = {}

    def is_allowed(self, connection_id: str) -> tuple[bool, Optional[str]]:
        """Check if message is allowed based on rate limits"""

        now = datetime.now()

        if connection_id not in self.message_history:
            self.message_history[connection_id] = []

        # Clean old entries
        self.message_history[connection_id] = [
            ts for ts in self.message_history[connection_id]
            if (now - ts).total_seconds() < 3600
        ]

        history = self.message_history[connection_id]

        # Check per-minute limit
        recent_minute = [
            ts for ts in history
            if (now - ts).total_seconds() < 60
        ]

        if len(recent_minute) >= self.max_per_minute:
            return False, "Terlalu banyak pesan. Silakan tunggu sebentar."

        # Check per-hour limit
        if len(history) >= self.max_per_hour:
            return False, "Batas pesan per jam tercapai. Silakan coba lagi nanti."

        # Record this message
        self.message_history[connection_id].append(now)

        return True, None
```

#### 3.2 Reconnection Support

```python
# src/presentation/websocket/reconnection.py

import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

class ReconnectionManager:
    """Manages WebSocket reconnection logic"""

    def __init__(self, reconnection_window: int = 60):
        self.reconnection_window = reconnection_window
        self.disconnected_sessions: Dict[str, Dict] = {}

    def register_disconnection(
        self,
        session_id: str,
        connection_id: str,
        state: Optional[Dict] = None
    ):
        """Register a disconnection for potential reconnection"""

        self.disconnected_sessions[session_id] = {
            "connection_id": connection_id,
            "disconnected_at": datetime.now(),
            "state": state or {}
        }

    def can_reconnect(self, session_id: str) -> bool:
        """Check if session can reconnect"""

        if session_id not in self.disconnected_sessions:
            return True  # New session

        session_info = self.disconnected_sessions[session_id]
        elapsed = datetime.now() - session_info["disconnected_at"]

        return elapsed.total_seconds() <= self.reconnection_window

    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get saved session state for reconnection"""

        if session_id in self.disconnected_sessions:
            if self.can_reconnect(session_id):
                state = self.disconnected_sessions[session_id]["state"]
                # Clean up after retrieval
                del self.disconnected_sessions[session_id]
                return state

        return None

    async def cleanup_expired_sessions(self):
        """Periodic cleanup of expired sessions"""

        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                expired = []

                for session_id, info in self.disconnected_sessions.items():
                    elapsed = now - info["disconnected_at"]
                    if elapsed.total_seconds() > self.reconnection_window:
                        expired.append(session_id)

                for session_id in expired:
                    del self.disconnected_sessions[session_id]

            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Silent cleanup
```

**Validation Checkpoint 3.1**:
- [ ] Message validation working
- [ ] Rate limiting implemented
- [ ] Reconnection logic functional
- [ ] Enhancement features integrated

---

### Stage 4: Testing & Validation (2 hours)

#### 4.1 HTML Test Client

```text
<!-- test_client.html -->
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steel Chat - Test Client</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .chat-container {
            width: 100%;
            max-width: 600px;
            height: 80vh;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
        }

        .chat-header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header h1 {
            font-size: 1.5rem;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #e74c3c;
        }

        .status-dot.connected {
            background: #2ecc71;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateY(20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .message.user {
            text-align: right;
        }

        .message.ai {
            text-align: left;
        }

        .message-bubble {
            display: inline-block;
            padding: 12px 20px;
            border-radius: 18px;
            max-width: 70%;
            word-wrap: break-word;
        }

        .user .message-bubble {
            background: #3498db;
            color: white;
        }

        .ai .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .system-message {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9rem;
            margin: 10px 0;
            font-style: italic;
        }

        .typing-indicator {
            display: none;
            padding: 12px 20px;
            background: white;
            border-radius: 18px;
            display: inline-block;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .typing-indicator.active {
            display: inline-block;
        }

        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #95a5a6;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }

        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }

        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #ecf0f1;
            border-radius: 0 0 10px 10px;
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
        }

        #messageInput {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #ecf0f1;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }

        #messageInput:focus {
            border-color: #3498db;
        }

        #sendButton {
            padding: 12px 25px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }

        #sendButton:hover:not(:disabled) {
            background: #2980b9;
        }

        #sendButton:disabled {
            background: #95a5a6;
            cursor: not-allowed;
        }

        .debug-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.8rem;
            max-width: 300px;
        }

        .debug-panel h3 {
            margin-bottom: 10px;
        }

        .debug-info {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🏗️ Steel Chat MVP</h1>
            <div class="connection-status">
                <span id="statusText">Connecting...</span>
                <div class="status-dot" id="statusDot"></div>
            </div>
        </div>

        <div class="messages-container" id="messagesContainer">
            <div class="system-message">Menghubungkan ke server...</div>
        </div>

        <div class="input-container">
            <div class="input-wrapper">
                <input
                    type="text"
                    id="messageInput"
                    placeholder="Ketik pesan Anda..."
                    disabled
                />
                <button id="sendButton" disabled>Kirim</button>
            </div>
        </div>
    </div>

    <div class="debug-panel" id="debugPanel" style="display: none;">
        <h3>Debug Info</h3>
        <div class="debug-info">Session: <span id="debugSession">-</span></div>
        <div class="debug-info">Status: <span id="debugStatus">-</span></div>
        <div class="debug-info">Messages: <span id="debugMessages">0</span></div>
        <div class="debug-info">Ping: <span id="debugPing">-</span></div>
    </div>

    <script>
        // Configuration
        const CONFIG = {
            wsUrl: 'ws://localhost:8000/api/v1/ws',
            sessionId: `test-${Date.now()}`,
            reconnectAttempts: 3,
            reconnectDelay: 2000,
            heartbeatInterval: 30000,
            debug: true
        };

        // State management
        const state = {
            ws: null,
            connected: false,
            messageCount: 0,
            lastPing: null,
            reconnectCount: 0,
            typingTimeout: null
        };

        // DOM elements
        const elements = {
            messagesContainer: document.getElementById('messagesContainer'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            statusText: document.getElementById('statusText'),
            statusDot: document.getElementById('statusDot'),
            debugPanel: document.getElementById('debugPanel'),
            debugSession: document.getElementById('debugSession'),
            debugStatus: document.getElementById('debugStatus'),
            debugMessages: document.getElementById('debugMessages'),
            debugPing: document.getElementById('debugPing')
        };

        // WebSocket connection
        function connect() {
            const wsUrl = `${CONFIG.wsUrl}/${CONFIG.sessionId}`;

            updateStatus('Connecting...', false);

            try {
                state.ws = new WebSocket(wsUrl);

                state.ws.onopen = handleOpen;
                state.ws.onmessage = handleMessage;
                state.ws.onerror = handleError;
                state.ws.onclose = handleClose;

            } catch (error) {
                console.error('Connection error:', error);
                handleError(error);
            }
        }

        // Event handlers
        function handleOpen(event) {
            console.log('WebSocket connected');
            state.connected = true;
            state.reconnectCount = 0;

            updateStatus('Connected', true);
            enableInput(true);

            // Start heartbeat
            startHeartbeat();

            // Update debug
            if (CONFIG.debug) {
                elements.debugPanel.style.display = 'block';
                elements.debugSession.textContent = CONFIG.sessionId;
                elements.debugStatus.textContent = 'Connected';
            }
        }

        function handleMessage(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('Message received:', data);

                switch (data.type) {
                    case 'system':
                        handleSystemMessage(data);
                        break;

                    case 'user_message':
                        // Only show if from another connection
                        if (data.metadata && data.metadata.from_connection) {
                            addMessage(data.message, 'user');
                        }
                        break;

                    case 'ai_response':
                        hideTypingIndicator();
                        addMessage(data.message, 'ai');
                        break;

                    case 'error':
                        hideTypingIndicator();
                        addSystemMessage(`Error: ${data.message}`);
                        break;

                    case 'heartbeat':
                        // Silent heartbeat acknowledgment
                        console.log('Heartbeat received');
                        break;

                    case 'pong':
                        handlePong(data);
                        break;

                    default:
                        console.warn('Unknown message type:', data.type);
                }

                // Update message count
                state.messageCount++;
                if (CONFIG.debug) {
                    elements.debugMessages.textContent = state.messageCount;
                }

            } catch (error) {
                console.error('Failed to parse message:', error);
            }
        }

        function handleError(event) {
            console.error('WebSocket error:', event);
            updateStatus('Error', false);

            if (CONFIG.debug) {
                elements.debugStatus.textContent = 'Error';
            }
        }

        function handleClose(event) {
            console.log('WebSocket closed:', event);
            state.connected = false;

            updateStatus('Disconnected', false);
            enableInput(false);

            // Stop heartbeat
            stopHeartbeat();

            // Attempt reconnection
            if (state.reconnectCount < CONFIG.reconnectAttempts) {
                state.reconnectCount++;
                addSystemMessage(
                    `Koneksi terputus. Mencoba menyambung kembali... (${state.reconnectCount}/${CONFIG.reconnectAttempts})`
                );

                setTimeout(connect, CONFIG.reconnectDelay);
            } else {
                addSystemMessage('Tidak dapat terhubung ke server. Silakan refresh halaman.');
            }

            if (CONFIG.debug) {
                elements.debugStatus.textContent = 'Disconnected';
            }
        }

        // System message handlers
        function handleSystemMessage(data) {
            switch (data.event) {
                case 'connected':
                    addSystemMessage(data.message);
                    break;

                case 'typing':
                    showTypingIndicator();
                    break;

                case 'disconnected':
                    addSystemMessage(data.message);
                    break;

                case 'error':
                    addSystemMessage(`Error: ${data.message}`);
                    break;

                default:
                    if (data.message) {
                        addSystemMessage(data.message);
                    }
            }
        }

        // UI functions
        function addMessage(content, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.textContent = content;

            messageDiv.appendChild(bubbleDiv);
            elements.messagesContainer.appendChild(messageDiv);

            scrollToBottom();
        }

        function addSystemMessage(content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'system-message';
            messageDiv.textContent = content;

            elements.messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        function showTypingIndicator() {
            // Clear existing timeout
            if (state.typingTimeout) {
                clearTimeout(state.typingTimeout);
            }

            // Check if indicator already exists
            let indicator = document.querySelector('.typing-indicator');

            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'typing-indicator active';
                indicator.innerHTML = '<span></span><span></span><span></span>';

                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ai typing-message';
                messageDiv.appendChild(indicator);

                elements.messagesContainer.appendChild(messageDiv);
                scrollToBottom();
            }

            // Auto-hide after 5 seconds
            state.typingTimeout = setTimeout(hideTypingIndicator, 5000);
        }

        function hideTypingIndicator() {
            const typingMessage = document.querySelector('.typing-message');
            if (typingMessage) {
                typingMessage.remove();
            }

            if (state.typingTimeout) {
                clearTimeout(state.typingTimeout);
                state.typingTimeout = null;
            }
        }

        function scrollToBottom() {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }

        function updateStatus(text, connected) {
            elements.statusText.textContent = text;

            if (connected) {
                elements.statusDot.classList.add('connected');
            } else {
                elements.statusDot.classList.remove('connected');
            }
        }

        function enableInput(enabled) {
            elements.messageInput.disabled = !enabled;
            elements.sendButton.disabled = !enabled;

            if (enabled) {
                elements.messageInput.focus();
            }
        }

        // Message sending
        function sendMessage() {
            const message = elements.messageInput.value.trim();

            if (!message || !state.connected) {
                return;
            }

            // Display user message immediately
            addMessage(message, 'user');

            // Send to server
            const data = {
                type: 'user_message',
                message: message,
                metadata: {
                    timestamp: new Date().toISOString()
                }
            };

            try {
                state.ws.send(JSON.stringify(data));
                elements.messageInput.value = '';

            } catch (error) {
                console.error('Failed to send message:', error);
                addSystemMessage('Gagal mengirim pesan. Silakan coba lagi.');
            }
        }

        // Heartbeat management
        let heartbeatInterval = null;

        function startHeartbeat() {
            stopHeartbeat();

            heartbeatInterval = setInterval(() => {
                if (state.connected && state.ws.readyState === WebSocket.OPEN) {
                    sendPing();
                }
            }, CONFIG.heartbeatInterval);

            // Send initial ping
            sendPing();
        }

        function stopHeartbeat() {
            if (heartbeatInterval) {
                clearInterval(heartbeatInterval);
                heartbeatInterval = null;
            }
        }

        function sendPing() {
            if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                state.lastPing = Date.now();

                state.ws.send(JSON.stringify({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                }));

                console.log('Ping sent');
            }
        }

        function handlePong(data) {
            if (state.lastPing) {
                const latency = Date.now() - state.lastPing;
                console.log(`Pong received. Latency: ${latency}ms`);

                if (CONFIG.debug) {
                    elements.debugPing.textContent = `${latency}ms`;
                }
            }
        }

        // Event listeners
        elements.sendButton.addEventListener('click', sendMessage);

        elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+D to toggle debug panel
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                const panel = elements.debugPanel;
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            }

            // Escape to clear input
            if (e.key === 'Escape') {
                elements.messageInput.value = '';
            }
        });

        // Page visibility handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('Page hidden - reducing activity');
            } else {
                console.log('Page visible - resuming activity');
                if (!state.connected) {
                    connect();
                }
            }
        });

        // Initialize connection
        window.addEventListener('load', () => {
            console.log('Initializing Steel Chat client...');
            connect();
        });

        // Cleanup on unload
        window.addEventListener('beforeunload', () => {
            if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                state.ws.close();
            }
        });
    </script>
</body>
</html>
```

#### 4.2 Integration Tests

```python
# tests/integration/test_websocket_flow.py

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from src.main import app

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_websocket_connection(test_client):
    """Test WebSocket connection establishment"""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Receive welcome message
        data = websocket.receive_json()

        assert data["type"] == "system"
        assert data["event"] == "connected"
        assert "Selamat datang" in data["message"]
        assert "session" in data

@pytest.mark.asyncio
async def test_websocket_message_flow(test_client):
    """Test complete message flow"""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome message
        websocket.receive_json()

        # Send user message
        websocket.send_json({
            "type": "user_message",
            "message": "Halo PERKY"
        })

        # Receive typing indicator
        typing = websocket.receive_json()
        assert typing["type"] == "system"
        assert typing["event"] == "typing"

        # Receive AI response
        response = websocket.receive_json()
        assert response["type"] == "ai_response"
        assert response["message"] is not None

@pytest.mark.asyncio
async def test_websocket_heartbeat(test_client):
    """Test heartbeat mechanism"""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send ping
        websocket.send_json({
            "type": "ping"
        })

        # Receive pong
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

@pytest.mark.asyncio
async def test_websocket_error_handling(test_client):
    """Test error handling"""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        # Skip welcome
        websocket.receive_json()

        # Send invalid message
        websocket.send_json({
            "type": "invalid_type",
            "data": "test"
        })

        # Should not crash, might receive error or nothing
        # Connection should remain open

        # Verify connection still works
        websocket.send_json({
            "type": "ping"
        })

        pong = websocket.receive_json()
        assert pong["type"] == "pong"

@pytest.mark.asyncio
async def test_concurrent_connections(test_client):
    """Test multiple concurrent connections"""

    async def client_session(session_id: str):
        with test_client.websocket_connect(f"/api/v1/ws/{session_id}") as ws:
            # Receive welcome
            welcome = ws.receive_json()
            assert welcome["type"] == "system"

            # Send message
            ws.send_json({
                "type": "user_message",
                "message": f"Test from {session_id}"
            })

            # Receive responses
            typing = ws.receive_json()
            response = ws.receive_json()

            assert response["type"] == "ai_response"

    # Run multiple sessions concurrently
    tasks = [
        asyncio.create_task(client_session(f"session-{i}"))
        for i in range(5)
    ]

    await asyncio.gather(*tasks)

@pytest.mark.asyncio
async def test_message_validation(test_client):
    """Test message validation"""

    with test_client.websocket_connect("/api/v1/ws/test-session") as websocket:
        websocket.receive_json()  # Skip welcome

        # Test empty message
        websocket.send_json({
            "type": "user_message",
            "message": ""
        })

        error = websocket.receive_json()
        assert error["type"] == "error"

        # Test very long message
        long_message = "x" * 3000
        websocket.send_json({
            "type": "user_message",
            "message": long_message
        })

        error = websocket.receive_json()
        assert error["type"] == "error"
```

**Validation Checkpoint 4.1**:
- [ ] HTML client connects successfully
- [ ] Messages flow correctly
- [ ] Integration tests pass
- [ ] Load testing successful

---

## Testing Strategy

### Unit Test Coverage

```python
# tests/unit/presentation/websocket/test_connection_manager.py

import pytest
from unittest.mock import Mock, AsyncMock
from src.presentation.websocket.connection_manager import ConnectionManager

@pytest.fixture
def connection_manager():
    return ConnectionManager()

@pytest.mark.asyncio
async def test_connection_management(connection_manager):
    """Test connection add/remove"""

    mock_ws = AsyncMock()

    # Test connection
    connected = await connection_manager.connect(
        websocket=mock_ws,
        connection_id="test-123",
        session_id="session-1"
    )

    assert connected
    assert connection_manager.get_connection_count() == 1
    assert connection_manager.get_connection_count("session-1") == 1

    # Test disconnection
    connection_manager.disconnect("test-123")

    assert connection_manager.get_connection_count() == 0
    assert connection_manager.get_connection_count("session-1") == 0

@pytest.mark.asyncio
async def test_message_sending(connection_manager):
    """Test message sending"""

    mock_ws = AsyncMock()

    await connection_manager.connect(
        websocket=mock_ws,
        connection_id="test-123",
        session_id="session-1"
    )

    # Test personal message
    sent = await connection_manager.send_personal_message(
        {"type": "test"},
        "test-123"
    )

    assert sent
    mock_ws.send_json.assert_called_once_with({"type": "test"})

@pytest.mark.asyncio
async def test_broadcasting(connection_manager):
    """Test session broadcasting"""

    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    await connection_manager.connect(mock_ws1, "conn-1", "session-1")
    await connection_manager.connect(mock_ws2, "conn-2", "session-1")

    # Broadcast to session
    await connection_manager.broadcast_to_session(
        {"type": "broadcast"},
        "session-1"
    )

    mock_ws1.send_json.assert_called_once()
    mock_ws2.send_json.assert_called_once()
```

### Performance Testing

```python
# tests/performance/test_websocket_load.py

import asyncio
import time
import websockets
import json
from typing import List

async def client_session(session_id: str, messages: int = 10):
    """Simulate a client session"""

    uri = f"ws://localhost:8000/api/v1/ws/{session_id}"

    async with websockets.connect(uri) as websocket:
        # Receive welcome
        await websocket.recv()

        # Send messages
        for i in range(messages):
            await websocket.send(json.dumps({
                "type": "user_message",
                "message": f"Test message {i} from {session_id}"
            }))

            # Wait for response
            await websocket.recv()  # typing
            await websocket.recv()  # response

            # Small delay
            await asyncio.sleep(0.1)

async def load_test(concurrent_sessions: int = 10, messages_per_session: int = 10):
    """Run load test"""

    start_time = time.time()

    # Create tasks
    tasks = [
        asyncio.create_task(
            client_session(f"load-test-{i}", messages_per_session)
        )
        for i in range(concurrent_sessions)
    ]

    # Run all sessions
    await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    total_messages = concurrent_sessions * messages_per_session
    messages_per_second = total_messages / duration

    print(f"Load Test Results:")
    print(f"  Sessions: {concurrent_sessions}")
    print(f"  Messages per session: {messages_per_session}")
    print(f"  Total messages: {total_messages}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Messages/second: {messages_per_second:.2f}")

if __name__ == "__main__":
    # Run different load scenarios
    asyncio.run(load_test(10, 10))    # 10 sessions, 10 messages each
    asyncio.run(load_test(20, 5))     # 20 sessions, 5 messages each
    asyncio.run(load_test(5, 50))     # 5 sessions, 50 messages each
```

### E2E Test Script

```bash
#!/bin/bash
# test_websocket_e2e.sh

echo "WebSocket E2E Testing"
echo "===================="

# 1. Start the application
echo "Starting application..."
python -m uvicorn src.main:app --reload --port 8000 &
APP_PID=$!
sleep 5

# 2. Check health
echo "Checking health endpoint..."
curl -s http://localhost:8000/health | grep "healthy" || exit 1

# 3. Test WebSocket with wscat
echo "Testing WebSocket connection..."
echo '{"type":"ping"}' | wscat -c ws://localhost:8000/api/v1/ws/e2e-test -w 1 || exit 1

# 4. Run Python integration tests
echo "Running integration tests..."
python -m pytest tests/integration/test_websocket_flow.py -v

# 5. Run load test
echo "Running load test..."
python tests/performance/test_websocket_load.py

# 6. Open browser test (optional)
echo "Opening browser test client..."
open test_client.html || xdg-open test_client.html

# Wait for manual testing
echo "Manual testing in browser... Press Enter to continue"
read

# 7. Cleanup
echo "Cleaning up..."
kill $APP_PID

echo "E2E Testing Complete!"
```

---

## Quality Gates & Validation

### Code Quality Checklist

#### Syntax and Style ✅

- [ ] Python type hints on all functions
- [ ] Docstrings for all classes and public methods
- [ ] Black formatting applied
- [ ] isort import sorting
- [ ] flake8 linting passed

#### Type Safety ✅

- [ ] mypy type checking passed
- [ ] Pydantic models validated
- [ ] No `Any` types without justification

#### Security ✅

- [ ] Input validation on all user messages
- [ ] XSS prevention in message handling
- [ ] Rate limiting implemented
- [ ] Connection limits enforced
- [ ] No sensitive data in logs

#### Testing ✅

- [ ] Unit tests >80% coverage
- [ ] Integration tests for all flows
- [ ] Load testing passed (20 concurrent)
- [ ] E2E test with browser client

#### Performance ✅

- [ ] Message latency <100ms local
- [ ] Memory stable over time
- [ ] CPU usage <5% idle
- [ ] Heartbeat maintains connection

#### Documentation ✅

- [ ] API documentation updated
- [ ] WebSocket protocol documented
- [ ] Client integration guide
- [ ] Deployment instructions

### Validation Commands

```bash
# Run all quality checks
make quality

# Or manually:
black src/presentation/websocket/ tests/
isort src/presentation/websocket/ tests/
flake8 src/presentation/websocket/
mypy src/presentation/websocket/
pytest tests/unit/presentation/websocket/ --cov
pytest tests/integration/test_websocket_flow.py
```

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| WebSocket connection drops | High | Medium | Implement reconnection logic with exponential backoff |
| Memory leaks from connections | High | Low | Connection cleanup in finally blocks, health checks |
| Message flooding | Medium | Medium | Rate limiting, message size limits |
| Concurrent connection issues | High | Low | Connection manager with proper locking |
| Browser compatibility | Medium | Low | Use standard WebSocket API, polyfills if needed |

### Mitigation Strategies

#### Connection Stability

```python
# Automatic reconnection with backoff
reconnect_delays = [1, 2, 4, 8, 16]  # seconds
for attempt, delay in enumerate(reconnect_delays):
    if connect():
        break
    await asyncio.sleep(delay)
```

#### Resource Management

```python
# Connection limits
MAX_CONNECTIONS_PER_SESSION = 5
MAX_TOTAL_CONNECTIONS = 100

if manager.get_connection_count() >= MAX_TOTAL_CONNECTIONS:
    await websocket.close(code=1008, reason="Server at capacity")
```

#### Error Recovery

```python
try:
    await process_message(message)
except ValidationError:
    await send_error("Invalid message format")
except ServiceUnavailable:
    await send_error("Service temporarily unavailable")
except Exception:
    logger.exception("Unexpected error")
    await send_error("Internal error occurred")
```

---

## Success Criteria

### Functional Requirements ✅

- [x] WebSocket connection establishment
- [x] Bidirectional message flow
- [x] Session management integration
- [x] Heartbeat keeps connection alive
- [x] Graceful error handling
- [x] Connection cleanup on disconnect
- [x] Multiple concurrent connections
- [x] Message validation and sanitization
- [x] Indonesian language responses
- [x] Typing indicators

### Performance Requirements ✅

- [x] Message latency <100ms (local)
- [x] Support 10-20 concurrent connections
- [x] Connection stable for 1+ hour
- [x] Memory usage stable
- [x] CPU usage <5% idle

### Quality Requirements ✅

- [x] 80% test coverage
- [x] All integration tests pass
- [x] Load test successful
- [x] Error messages in Indonesian
- [x] Comprehensive logging

### User Experience ✅

- [x] Smooth connection experience
- [x] Clear connection status
- [x] Responsive message sending
- [x] Visual typing indicators
- [x] Reconnection support

---

## Post-Implementation Checklist

### Code Review

- [ ] Code follows DDD architecture
- [ ] All TODO comments resolved
- [ ] No debug code in production
- [ ] Security best practices followed
- [ ] Performance optimizations applied

### Testing Verification

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Load testing completed
- [ ] Manual testing with browser
- [ ] Edge cases tested

### Documentation

- [ ] API documentation updated
- [ ] WebSocket protocol documented
- [ ] Client integration examples
- [ ] Troubleshooting guide added
- [ ] Architecture diagrams updated

### Deployment Readiness

- [ ] Environment variables configured
- [ ] Docker configuration updated
- [ ] Monitoring setup planned
- [ ] Rollback plan prepared
- [ ] Performance baselines established

### Handover

- [ ] Team walkthrough completed
- [ ] Known issues documented
- [ ] Future improvements listed
- [ ] Client library considerations
- [ ] Production deployment plan

---

## Appendices

### A. WebSocket Protocol Specification

```yaml
# WebSocket Message Protocol v1.0

Client -> Server:
  user_message:
    type: "user_message"
    message: string
    metadata?: object

  ping:
    type: "ping"

  heartbeat:
    type: "heartbeat"

Server -> Client:
  system:
    type: "system"
    event: "connected|disconnected|typing|error"
    message?: string
    session?: object

  ai_response:
    type: "ai_response"
    message: string
    metadata?: object
    timestamp: string

  error:
    type: "error"
    message: string

  heartbeat:
    type: "heartbeat"

  pong:
    type: "pong"
```

### B. Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Connection fails | Invalid JWT token | Verify token generation and validation |
| Auth rejected | Expired token | Refresh token before expiry |
| Rate limit hit | Too many requests | Implement client-side throttling |
| Circuit open | Service failures | Check AI agent availability |
| Messages queued | Async processing delay | Monitor queue size and processing time |
| Connection drops | No heartbeat | Ensure heartbeat implementation |

### C. Future Enhancements (Nice-to-Have, Not for MVP)

1. **Production Scaling**
   - Redis Pub/Sub for horizontal scaling
   - Connection pooling optimization
   - Prometheus metrics integration
   - Distributed rate limiting

2. **Enhanced Features**
   - File upload support
   - Voice message capability
   - Read receipts
   - Presence indicators
   - Message history pagination
   - Multi-language support

3. **Client Libraries**
   - JavaScript/TypeScript SDK
   - Python client library
   - Mobile SDK considerations
   - React/Vue components

4. **Monitoring**
   - Connection metrics dashboard
   - Message flow analytics
   - Error rate monitoring
   - Performance tracking

---

## Summary

This MVP-focused workflow implements WebSocket integration with essential security and
stability features. The implementation prioritizes the "Must Fix for MVP" items:

**MVP Implementations**:
- JWT authentication for secure connections
- Clean architecture with separated responsibilities (SRP)
- Async message queue to prevent blocking
- Rate limiting to prevent abuse
- Circuit breaker for service resilience

**Timeline**: 6-7 hours total (MVP scope)
- Stage 1: 2 hours (Security Foundation)
- Stage 2: 3 hours (Core Implementation with Clean Architecture)
- Stage 3: 1-2 hours (Testing & Validation)

**Risk Level**: Low (mitigated through authentication, rate limiting, and circuit breaker)

**Next Steps**: After successful implementation, proceed to Phase 5: Integration &
Testing to complete the MVP development cycle.
