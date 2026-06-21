import json
import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

REQUEST_CACHE_TTL = 30


def request_cache_key(request_id, user_id) -> str:
    return f"request:{request_id}:{user_id}"


def request_cache_index_key(request_id) -> str:
    return f"request:{request_id}:keys"


def get_cached_request(request_id, user_id) -> dict | None:
    try:
        cached = r.get(request_cache_key(request_id, user_id))
        if cached is not None:
            return json.loads(cached)
    except Exception as ex:
        logger.debug("request cache read failed: %s", ex)
    return None


def set_cached_request(request_id, user_id, payload: dict, ttl: int = REQUEST_CACHE_TTL) -> None:
    try:
        key = request_cache_key(request_id, user_id)
        r.setex(key, ttl, json.dumps(payload))
        r.sadd(request_cache_index_key(request_id), key)
    except Exception as ex:
        logger.debug("request cache write failed: %s", ex)


def invalidate_request_cache(request_id) -> None:
    try:
        index_key = request_cache_index_key(request_id)
        keys = r.smembers(index_key)
        if keys:
            r.delete(*keys)
        r.delete(index_key)
    except Exception as ex:
        logger.debug("request cache invalidation failed: %s", ex)
