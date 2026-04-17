from datetime import datetime
from fastapi import HTTPException
from .config import settings
from .rate_limiter import get_redis


def get_monthly_key(user_key: str) -> str:
    month = datetime.utcnow().strftime("%Y-%m")
    return f"cost:{user_key}:{month}"


def check_budget(user_key: str) -> None:
    r = get_redis()
    key = get_monthly_key(user_key)
    spent = float(r.get(key) or 0)
    if spent >= settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget of ${settings.monthly_budget_usd} exceeded. Resets next month.",
        )


def record_usage(user_key: str, input_tokens: int, output_tokens: int) -> float:
    cost = (
        input_tokens / 1000 * settings.cost_per_1k_input_tokens
        + output_tokens / 1000 * settings.cost_per_1k_output_tokens
    )
    r = get_redis()
    key = get_monthly_key(user_key)
    r.incrbyfloat(key, cost)
    r.expire(key, 35 * 24 * 3600)  # keep for 35 days
    return cost
