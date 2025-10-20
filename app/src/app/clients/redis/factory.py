from flask import current_app
from models.value_objects.redis_connection_info import RedisConnectionInfo

import redis
import functools

@functools.cache
def make_or_get_redis_client():
    return _make_redis_client()

def _make_redis_client():
    redis_dict = current_app.config.get("redis_applicatif", {})
    redis_info = RedisConnectionInfo.model_validate(redis_dict)
    return redis.Redis(
        host=redis_info.host,
        port=redis_info.port,
        db=redis_info.db,
    )