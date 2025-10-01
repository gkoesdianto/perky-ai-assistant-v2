import redis.asyncio as redis

from src.core.config import settings


class RedisClient:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        return self.redis_client

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    async def get_client(self):
        if not self.redis_client:
            await self.connect()
        return self.redis_client


redis_client = RedisClient()
