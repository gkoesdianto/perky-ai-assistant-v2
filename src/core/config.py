from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str

    # CORS - Allow Svelte widget to connect
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values) -> str:
        if isinstance(v, str) and v:
            return v
        # Get the values dict from the validation info
        postgres_server = values.data.get("POSTGRES_SERVER")
        postgres_user = values.data.get("POSTGRES_USER")
        postgres_password = values.data.get("POSTGRES_PASSWORD")
        postgres_db = values.data.get("POSTGRES_DB")

        # Create the database URL
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=postgres_user,
            password=postgres_password,
            host=postgres_server,
            port=5432,
            path=postgres_db,
        )

    # Redis - For session management and caching
    REDIS_URL: RedisDsn
    REDIS_SESSION_TTL: int  # 1 hour default in .env
    REDIS_CACHE_TTL: int  # 15 minutes for price/stock default in .env

    # PIM Integration
    PERKY_OS_API_URL: str
    PERKY_OS_JWT_SECRET: str
    PERKY_OS_TIMEOUT: int  # milliseconds

    # OpenAI for PydanticAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    OPENAI_TEMPERATURE: float
    OPENAI_MAX_RETRIES: int

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int
    WS_MAX_CONNECTIONS: int
    WS_MESSAGE_RATE_LIMIT: int

    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
