"""Unit tests for Logfire configuration in Settings."""

import pytest
from pydantic import ValidationError

from src.core.config import Settings


def test_logfire_config_defaults(monkeypatch):
    """Test Logfire configuration with defaults"""
    # Clear LOGFIRE_TOKEN from environment to test default None value
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)

    # Also clear from .env file loading by using _env_file=None
    monkeypatch.setenv("LOGFIRE_SERVICE_NAME", "perky-ai-assistant")

    # Create settings with minimal required fields
    settings = Settings(
        PROJECT_NAME="Test",
        VERSION="1.0.0",
        API_V1_STR="/api/v1",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="test_db",
        REDIS_URL="redis://localhost:6379/0",
        REDIS_SESSION_TTL=3600,
        REDIS_CACHE_TTL=900,
        PERKY_OS_API_URL="https://api.test.com",
        PERKY_OS_JWT_SECRET="test_secret",
        PERKY_OS_TIMEOUT=5000,
        OPENAI_API_KEY="sk-test-key",
        OPENAI_MODEL="gpt-4o-mini",
        OPENAI_TEMPERATURE=0.3,
        OPENAI_MAX_RETRIES=2,
        WS_HEARTBEAT_INTERVAL=30,
        WS_MAX_CONNECTIONS=100,
        WS_MESSAGE_RATE_LIMIT=10,
        SECRET_KEY="test-secret-key",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        LOGFIRE_TOKEN=None,  # Explicitly set to None
    )

    # Verify Logfire defaults
    assert settings.LOGFIRE_SERVICE_NAME == "perky-ai-assistant"
    assert settings.LOGFIRE_SCRUBBING is True
    assert settings.LOGFIRE_SAMPLING_RATIO == 1.0
    assert settings.LOGFIRE_ENVIRONMENT == "development"
    assert settings.LOGFIRE_SEND_TO_LOGFIRE is True
    assert settings.LOGFIRE_CONSOLE is False
    assert settings.LOGFIRE_TOKEN is None


def test_sampling_ratio_validation_valid():
    """Test sampling ratio accepts valid values (0.0 to 1.0)"""
    for ratio in [0.0, 0.5, 1.0]:
        settings = Settings(
            PROJECT_NAME="Test",
            VERSION="1.0.0",
            API_V1_STR="/api/v1",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_DB="test_db",
            REDIS_URL="redis://localhost:6379/0",
            REDIS_SESSION_TTL=3600,
            REDIS_CACHE_TTL=900,
            PERKY_OS_API_URL="https://api.test.com",
            PERKY_OS_JWT_SECRET="test_secret",
            PERKY_OS_TIMEOUT=5000,
            OPENAI_API_KEY="sk-test-key",
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_TEMPERATURE=0.3,
            OPENAI_MAX_RETRIES=2,
            WS_HEARTBEAT_INTERVAL=30,
            WS_MAX_CONNECTIONS=100,
            WS_MESSAGE_RATE_LIMIT=10,
            SECRET_KEY="test-secret-key",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            LOGFIRE_SAMPLING_RATIO=ratio,
        )
        assert settings.LOGFIRE_SAMPLING_RATIO == ratio


def test_sampling_ratio_validation_invalid_high():
    """Test sampling ratio rejects values > 1.0"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            PROJECT_NAME="Test",
            VERSION="1.0.0",
            API_V1_STR="/api/v1",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_DB="test_db",
            REDIS_URL="redis://localhost:6379/0",
            REDIS_SESSION_TTL=3600,
            REDIS_CACHE_TTL=900,
            PERKY_OS_API_URL="https://api.test.com",
            PERKY_OS_JWT_SECRET="test_secret",
            PERKY_OS_TIMEOUT=5000,
            OPENAI_API_KEY="sk-test-key",
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_TEMPERATURE=0.3,
            OPENAI_MAX_RETRIES=2,
            WS_HEARTBEAT_INTERVAL=30,
            WS_MAX_CONNECTIONS=100,
            WS_MESSAGE_RATE_LIMIT=10,
            SECRET_KEY="test-secret-key",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            LOGFIRE_SAMPLING_RATIO=1.5,
        )

    assert "LOGFIRE_SAMPLING_RATIO must be between 0.0 and 1.0" in str(exc_info.value)


def test_sampling_ratio_validation_invalid_low():
    """Test sampling ratio rejects values < 0.0"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            PROJECT_NAME="Test",
            VERSION="1.0.0",
            API_V1_STR="/api/v1",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_DB="test_db",
            REDIS_URL="redis://localhost:6379/0",
            REDIS_SESSION_TTL=3600,
            REDIS_CACHE_TTL=900,
            PERKY_OS_API_URL="https://api.test.com",
            PERKY_OS_JWT_SECRET="test_secret",
            PERKY_OS_TIMEOUT=5000,
            OPENAI_API_KEY="sk-test-key",
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_TEMPERATURE=0.3,
            OPENAI_MAX_RETRIES=2,
            WS_HEARTBEAT_INTERVAL=30,
            WS_MAX_CONNECTIONS=100,
            WS_MESSAGE_RATE_LIMIT=10,
            SECRET_KEY="test-secret-key",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            LOGFIRE_SAMPLING_RATIO=-0.1,
        )

    assert "LOGFIRE_SAMPLING_RATIO must be between 0.0 and 1.0" in str(exc_info.value)


def test_logfire_environment_literal():
    """Test LOGFIRE_ENVIRONMENT accepts only valid literal values"""
    valid_environments = ["local", "development", "staging", "production"]

    for env in valid_environments:
        settings = Settings(
            PROJECT_NAME="Test",
            VERSION="1.0.0",
            API_V1_STR="/api/v1",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_DB="test_db",
            REDIS_URL="redis://localhost:6379/0",
            REDIS_SESSION_TTL=3600,
            REDIS_CACHE_TTL=900,
            PERKY_OS_API_URL="https://api.test.com",
            PERKY_OS_JWT_SECRET="test_secret",
            PERKY_OS_TIMEOUT=5000,
            OPENAI_API_KEY="sk-test-key",
            OPENAI_MODEL="gpt-4o-mini",
            OPENAI_TEMPERATURE=0.3,
            OPENAI_MAX_RETRIES=2,
            WS_HEARTBEAT_INTERVAL=30,
            WS_MAX_CONNECTIONS=100,
            WS_MESSAGE_RATE_LIMIT=10,
            SECRET_KEY="test-secret-key",
            ALGORITHM="HS256",
            ACCESS_TOKEN_EXPIRE_MINUTES=30,
            LOGFIRE_ENVIRONMENT=env,
        )
        assert settings.LOGFIRE_ENVIRONMENT == env
