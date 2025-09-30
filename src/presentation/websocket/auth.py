"""WebSocket authentication module with JWT support."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from src.core.config import settings


def create_websocket_token(session_id: str) -> str:
    """
    Create a JWT token for WebSocket authentication.

    Args:
        session_id: Unique session identifier

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    payload = {
        "session_id": session_id,
        "exp": now + timedelta(hours=1),
        "iat": now,
        "type": "websocket",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def validate_websocket_token(token: str) -> Optional[str]:
    """
    Validate a WebSocket JWT token and extract session ID.

    Args:
        token: JWT token string to validate

    Returns:
        Session ID if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "websocket":
            return None

        return payload.get("session_id")
    except JWTError:
        return None
    except Exception:
        return None
