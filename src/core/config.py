from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
    PROJECT_NAME: str = "Perky AI Assistant"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS
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

    # Redis
    REDIS_URL: RedisDsn

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
