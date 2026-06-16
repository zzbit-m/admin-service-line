from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings


async def create_arq_pool():
    return await create_pool(
        RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT, database=0)
    )
