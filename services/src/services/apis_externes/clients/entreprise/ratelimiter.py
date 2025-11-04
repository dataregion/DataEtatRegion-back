import redis
from datetime import datetime
from pyrate_limiter import Limiter, RequestRate, RedisBucket

from api_entreprise import JSON_RESOURCE_IDENTIFIER
from models.value_objects.ratelimiter_info import RateLimiterInfo


def make_rate_limiter(ratelimiter_info: RateLimiterInfo):
    limit = ratelimiter_info.limit
    duration = ratelimiter_info.duration

    redis_pool = redis.ConnectionPool(
        host=ratelimiter_info.redis.host,
        port=ratelimiter_info.redis.port,
        db=ratelimiter_info.redis.db,
    )

    rates = [RequestRate(limit, duration)]

    return Limiter(
        *rates,
        time_function=lambda: datetime.utcnow().timestamp(),
        bucket_class=RedisBucket,
        bucket_kwargs={
            "bucket_name": JSON_RESOURCE_IDENTIFIER,
            "expire_time": rates[-1].interval,
            "redis_pool": redis_pool,
        },
    )
