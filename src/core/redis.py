from functools import lru_cache

from redis.asyncio import Redis

from src.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis_client() -> None:
    await get_redis_client().aclose()
