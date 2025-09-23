"""
WebSocket Reconnection Manager - Session continuity and recovery.

Manages WebSocket reconnection logic with state preservation,
allowing seamless recovery from temporary disconnections.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    EXPIRED = "expired"


@dataclass
class SessionState:
    """Preserved session state for reconnection."""

    connection_id: str
    session_id: str
    disconnected_at: datetime
    last_message_id: Optional[str] = None
    pending_messages: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reconnect_count: int = 0


class ReconnectionManager:
    """Manages WebSocket reconnection logic and state preservation."""

    def __init__(
        self,
        reconnection_window: int = 60,
        max_reconnect_attempts: int = 3,
        state_ttl: int = 300,
    ):
        """
        Initialize reconnection manager.

        Args:
            reconnection_window: Seconds allowed for reconnection
            max_reconnect_attempts: Maximum reconnection attempts
            state_ttl: Time to live for preserved state (seconds)
        """
        self.reconnection_window = reconnection_window
        self.max_reconnect_attempts = max_reconnect_attempts
        self.state_ttl = state_ttl
        self.disconnected_sessions: Dict[str, SessionState] = {}
        self.active_reconnections: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the reconnection manager with cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
            logger.info("Reconnection manager started")

    async def stop(self) -> None:
        """Stop the reconnection manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Reconnection manager stopped")

    def register_disconnection(
        self,
        session_id: str,
        connection_id: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a disconnection for potential reconnection.

        Args:
            session_id: Session identifier
            connection_id: Connection identifier
            state: Optional state to preserve
        """
        session_state = SessionState(
            connection_id=connection_id,
            session_id=session_id,
            disconnected_at=datetime.now(),
            metadata=state or {},
        )

        # Preserve any pending messages
        if state and "pending_messages" in state:
            session_state.pending_messages = state["pending_messages"]

        # Track last message ID for continuity
        if state and "last_message_id" in state:
            session_state.last_message_id = state["last_message_id"]

        self.disconnected_sessions[session_id] = session_state

        logger.info(
            f"Registered disconnection for session {session_id}, "
            f"connection {connection_id}"
        )

    def can_reconnect(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if session can reconnect.

        Args:
            session_id: Session to check

        Returns:
            Tuple of (can_reconnect, reason)
        """
        # New session is always allowed
        if session_id not in self.disconnected_sessions:
            return True, None

        session_state = self.disconnected_sessions[session_id]
        elapsed = datetime.now() - session_state.disconnected_at

        # Check reconnection window
        if elapsed.total_seconds() > self.reconnection_window:
            return False, "Reconnection window expired"

        # Check attempt limit
        if session_state.reconnect_count >= self.max_reconnect_attempts:
            return False, "Maximum reconnection attempts exceeded"

        # Check if already reconnecting
        if session_id in self.active_reconnections:
            return False, "Reconnection already in progress"

        return True, None

    async def handle_reconnection(
        self, session_id: str, new_connection_id: str
    ) -> Optional[SessionState]:
        """
        Handle reconnection attempt.

        Args:
            session_id: Session attempting to reconnect
            new_connection_id: New connection identifier

        Returns:
            Restored session state if successful
        """
        can_reconnect, reason = self.can_reconnect(session_id)

        if not can_reconnect:
            logger.warning(f"Reconnection denied for session {session_id}: {reason}")
            return None

        # Mark as actively reconnecting
        self.active_reconnections.add(session_id)

        try:
            if session_id in self.disconnected_sessions:
                session_state = self.disconnected_sessions[session_id]
                session_state.reconnect_count += 1
                session_state.connection_id = new_connection_id

                logger.info(
                    f"Session {session_id} reconnected "
                    f"(attempt {session_state.reconnect_count})"
                )

                # Clean up after successful reconnection
                del self.disconnected_sessions[session_id]

                return session_state
            else:
                # New session
                return SessionState(
                    connection_id=new_connection_id,
                    session_id=session_id,
                    disconnected_at=datetime.now(),
                )

        finally:
            # Remove from active reconnections
            self.active_reconnections.discard(session_id)

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """
        Get preserved session state.

        Args:
            session_id: Session to retrieve

        Returns:
            Session state if exists and valid
        """
        if session_id not in self.disconnected_sessions:
            return None

        session_state = self.disconnected_sessions[session_id]
        elapsed = datetime.now() - session_state.disconnected_at

        # Check if state is still valid
        if elapsed.total_seconds() > self.state_ttl:
            logger.info(f"Session state expired for {session_id}")
            del self.disconnected_sessions[session_id]
            return None

        return session_state

    def queue_message_for_reconnection(
        self, session_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Queue a message for delivery upon reconnection.

        Args:
            session_id: Target session
            message: Message to queue

        Returns:
            True if queued successfully
        """
        if session_id not in self.disconnected_sessions:
            return False

        session_state = self.disconnected_sessions[session_id]
        session_state.pending_messages.append(
            {"message": message, "queued_at": datetime.now().isoformat()}
        )

        # Limit queue size to prevent memory issues
        max_queue_size = 100
        if len(session_state.pending_messages) > max_queue_size:
            session_state.pending_messages = session_state.pending_messages[
                -max_queue_size:
            ]
            logger.warning(f"Message queue truncated for session {session_id}")

        return True

    def _cleanup_expired_sessions_once(self) -> int:
        """
        Perform a single cleanup of expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_sessions = []

        for session_id, session_state in self.disconnected_sessions.items():
            elapsed = now - session_state.disconnected_at

            # Check both reconnection window and state TTL
            if elapsed.total_seconds() > max(self.reconnection_window, self.state_ttl):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.disconnected_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    async def cleanup_expired_sessions(self) -> None:
        """Periodic cleanup of expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                self._cleanup_expired_sessions_once()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get reconnection manager statistics.

        Returns:
            Dictionary of statistics
        """
        now = datetime.now()
        stats: Dict[str, Any] = {
            "disconnected_sessions": len(self.disconnected_sessions),
            "active_reconnections": len(self.active_reconnections),
            "sessions": [],
        }

        for session_id, session_state in self.disconnected_sessions.items():
            elapsed = now - session_state.disconnected_at

            stats["sessions"].append(
                {
                    "session_id": session_id,
                    "disconnected_seconds_ago": elapsed.total_seconds(),
                    "reconnect_attempts": session_state.reconnect_count,
                    "pending_messages": len(session_state.pending_messages),
                    "can_reconnect": self.can_reconnect(session_id)[0],
                }
            )

        return stats


class ConnectionRecovery:
    """Handles connection recovery strategies."""

    def __init__(self, backoff_multiplier: float = 1.5, max_backoff: int = 30):
        """
        Initialize connection recovery.

        Args:
            backoff_multiplier: Exponential backoff multiplier
            max_backoff: Maximum backoff time in seconds
        """
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.recovery_strategies: Dict[str, int] = {}

    def calculate_backoff(self, session_id: str, attempt: int) -> float:
        """
        Calculate exponential backoff time.

        Args:
            session_id: Session identifier
            attempt: Reconnection attempt number

        Returns:
            Backoff time in seconds
        """
        base_delay = 1.0
        delay = base_delay * (self.backoff_multiplier**attempt)
        return min(delay, self.max_backoff)

    async def wait_before_reconnect(self, session_id: str, attempt: int) -> None:
        """
        Wait with exponential backoff before reconnection.

        Args:
            session_id: Session identifier
            attempt: Reconnection attempt number
        """
        delay = self.calculate_backoff(session_id, attempt)
        logger.info(
            f"Waiting {delay:.1f}s before reconnection attempt {attempt} "
            f"for session {session_id}"
        )
        await asyncio.sleep(delay)

    def should_use_recovery_strategy(
        self, session_id: str, error_type: Optional[str] = None
    ) -> str:
        """
        Determine which recovery strategy to use.

        Args:
            session_id: Session identifier
            error_type: Type of error that caused disconnection

        Returns:
            Recovery strategy name
        """
        # Determine strategy based on error type
        if error_type == "network_error":
            return "exponential_backoff"
        elif error_type == "server_overload":
            return "linear_backoff"
        elif error_type == "authentication_failed":
            return "no_retry"
        else:
            return "exponential_backoff"  # Default strategy
