from fastapi import Header, HTTPException
from .config import settings


def require_api_key(x_api_key: str = Header(default="")) -> str:
    if not x_api_key or x_api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Add header: X-Api-Key: <key>",
        )
    return x_api_key
