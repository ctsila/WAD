import redis.asyncio as redis

from app.config import settings


redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis_client
