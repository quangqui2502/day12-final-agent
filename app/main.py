import json
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import require_api_key
from .config import settings
from .cost_guard import check_budget, record_usage
from .rate_limiter import check_rate_limit, get_redis
from utils.mock_llm import MockLLM

# ── Structured JSON logging ──────────────────────────────────
logging.basicConfig(level=settings.log_level, format="%(message)s")
logger = logging.getLogger(__name__)


def log(level: str, msg: str, **extra):
    record = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "msg": msg, **extra}
    print(json.dumps(record), flush=True)


# ── State ────────────────────────────────────────────────────
_ready = False
_start_time = time.time()
llm = MockLLM()


# ── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ready
    log("INFO", "startup", app=settings.app_name, env=settings.environment)

    # Verify Redis connection
    try:
        get_redis().ping()
        log("INFO", "redis connected", url=settings.redis_url)
    except Exception as e:
        log("WARNING", "redis unavailable", error=str(e))

    _ready = True

    def _shutdown(sig, frame):
        global _ready
        log("INFO", "shutdown signal received", signal=sig)
        _ready = False
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    yield

    log("INFO", "shutdown complete")


# ── App ──────────────────────────────────────────────────────
app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────
class AskRequest(BaseModel):
    user_id: str
    question: str


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    timestamp: str
    history_length: int


# ── Endpoints ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.version,
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


@app.get("/ready")
def ready():
    if not _ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    try:
        get_redis().ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    return {"ready": True}


@app.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    _key: str = Depends(require_api_key),
):
    check_rate_limit(body.user_id)
    check_budget(body.user_id)

    # Load conversation history from Redis
    r = get_redis()
    history_key = f"history:{body.user_id}"
    raw_history = r.lrange(history_key, -10, -1)  # last 10 messages
    history = [json.loads(h) for h in raw_history]

    # Call LLM
    answer = llm.chat(body.question, history=history)

    # Save to Redis
    r.rpush(history_key, json.dumps({"role": "user", "content": body.question}))
    r.rpush(history_key, json.dumps({"role": "assistant", "content": answer}))
    r.expire(history_key, 7 * 24 * 3600)  # keep 7 days

    # Estimate & record cost
    input_tokens = len(body.question.split()) * 2
    output_tokens = len(answer.split()) * 2
    record_usage(body.user_id, input_tokens, output_tokens)

    log("INFO", "request", user_id=body.user_id, q_len=len(body.question), a_len=len(answer))

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        timestamp=datetime.now(timezone.utc).isoformat(),
        history_length=r.llen(history_key) // 2,
    )


@app.get("/history/{user_id}")
def get_history(user_id: str, _key: str = Depends(require_api_key)):
    r = get_redis()
    raw = r.lrange(f"history:{user_id}", 0, -1)
    messages = [json.loads(m) for m in raw]
    return {"user_id": user_id, "count": len(messages), "messages": messages}


@app.delete("/history/{user_id}")
def clear_history(user_id: str, _key: str = Depends(require_api_key)):
    get_redis().delete(f"history:{user_id}")
    return {"user_id": user_id, "cleared": True}
