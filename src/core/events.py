from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()
    await engine.dispose()
