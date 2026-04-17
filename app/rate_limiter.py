import time
import redis as redis_lib
from fastapi import HTTPException
from .config import settings

_redis: redis_lib.Redis | None = None


def get_redis() -> redis_lib.Redis:
    global _redis
    if _redis is None:
        _redis = redis_lib.from_url(settings.redis_url, decode_responses=True)
    return _redis


def check_rate_limit(user_key: str) -> None:
    """
    Sliding window rate limiter backed by Redis sorted set.
    Key: ratelimit:<user_key>
    Members: timestamps of recent requests
    """
    r = get_redis()
    now = time.time()
    window_start = now - 60  # 60-second window
    redis_key = f"ratelimit:{user_key}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(redis_key, 0, window_start)   # remove old entries
    pipe.zcard(redis_key)                                # count current
    pipe.zadd(redis_key, {str(now): now})               # record this request
    pipe.expire(redis_key, 120)                         # auto-cleanup
    _, count, *_ = pipe.execute()

    limit = settings.rate_limit_per_minute
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests/minute. Try again later.",
            headers={"Retry-After": "60"},
        )
