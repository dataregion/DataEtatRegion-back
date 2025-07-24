from zoneinfo import ZoneInfo
import redis
from datetime import datetime
from pyrate_limiter import Limiter, RequestRate, RedisBucket

from api_entreprise import JSON_RESOURCE_IDENTIFIER

from apis.config import config


def _make_rate_limiter(config_path: str):
    config_rate_limiter = config[config_path]

    ratelimiter = config_rate_limiter["RATELIMITER"]
    ratelimiter_redis = ratelimiter["REDIS"]

    limit = ratelimiter["LIMIT"]
    duration = ratelimiter["DURATION"]

    redis_pool = redis.ConnectionPool(
        host=ratelimiter_redis["HOST"],
        port=ratelimiter_redis["PORT"],
        db=ratelimiter_redis["DB"],
    )

    rates = [RequestRate(limit, duration)]

    return Limiter(
        *rates,
        time_function=lambda: datetime.now(ZoneInfo("Europe/Paris")),
        bucket_class=RedisBucket,
        bucket_kwargs={
            "bucket_name": JSON_RESOURCE_IDENTIFIER,
            "expire_time": rates[-1].interval,
            "redis_pool": redis_pool,
        },
    )
