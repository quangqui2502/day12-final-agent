# Day 12 Lab - Mission Answers

**Student:** Quang Qui Tran  
**Date:** 2026-04-17

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. **API key hardcode** (line 17) - Secret key visible in code, will be exposed if pushed to GitHub
2. **Database URL hardcode** (line 18) - Password hardcoded, security risk
3. **Print() instead of logging** (line 33-34) - Unstructured logs, hard to parse by log aggregators
4. **No health check endpoint** - Platform (Kubernetes/Railway) can't detect crashes
5. **Debug=True + reload=True** - Slower, memory leak, insecure for production
6. **Port hardcoded to 8000** - On cloud platforms, PORT is injected via env var

### Exercise 1.2: Basic version runs ✅
```
curl http://localhost:8000/ask?question=Hello
→ {"answer": "Mock response"}
```

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config** | Hardcode in code | Environment variables (os.getenv) | Easy to change per env, no secrets in code |
| **Health check** | None | GET /health endpoint | Platform uses to auto-restart if fails |
| **Logging** | print() unstructured | JSON structured logs | Easier to parse by log aggregators (Datadog, CloudWatch) |
| **Shutdown** | Abrupt Ctrl+C | Graceful SIGTERM handler | Complete requests before shutdown, no data loss |
| **Debug mode** | DEBUG=True | DEBUG=False | Dev is slow + memory leaks, prod is fast + safe |
| **Security headers** | None | X-Content-Type-Options, X-Frame-Options | Prevent XSS, clickjacking attacks |

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile questions

1. **Base image:** `python:3.11-slim` - Linux OS with Python 3.11 pre-installed
2. **Working directory:** `/app` - Container's internal folder where code runs
3. **COPY requirements.txt first:** Dependencies rarely change, so Docker caches this layer (faster rebuilds)
4. **CMD vs ENTRYPOINT:**
   - CMD = default arguments (can be overridden)
   - ENTRYPOINT = the program that always runs (cannot override)

### Exercise 2.2: Build và run

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -p 8000:8000 my-agent:develop
curl http://localhost:8000/ask -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
# → {"answer": "Mock response: What is Docker?"}
```

**Image size:**
```
REPOSITORY       TAG       SIZE
my-agent         develop   1.66GB
```

### Exercise 2.3: Image size comparison

- **Develop:** 1.66 GB (full python:3.11 + all tools)
- **Production:** 262 MB (slim + multi-stage build)
- **Improvement:** 84% smaller ⚡

**Why?**
- Stage 1 (builder): python:3.11-slim + gcc + build tools → compile packages → creates .whl files
- Stage 2 (runtime): python:3.11-slim + copy .whl files → no gcc needed → much lighter

### Exercise 2.4: Docker Compose stack

**Architecture diagram:**
```
Internet
    │
    ▼
┌─────────┐  :80/:443
│  Nginx  │  reverse proxy + load balancer
└────┬────┘
     │  internal network
  ┌──┴──────────┐
  ▼             ▼
┌──────┐    ┌──────┐
│Agent │    │Agent │  (2 replicas)
└──┬───┘    └──┬───┘
   │            │
   └─────┬──────┘
         ▼
   ┌──────────┐
   │  Redis   │  session + rate limiting cache
   └──────────┘
         ▼
   ┌──────────┐
   │  Qdrant  │  vector database for RAG
   └──────────┘
```

**Services started:** nginx, agent (×2), redis, qdrant

**Communication:** All services on `internal` bridge network. Only nginx exposes port 80/443 externally. Agents không expose port trực tiếp.

```bash
curl http://localhost/health     # → {"status": "ok"}
curl http://localhost/ask -X POST -d '{"question": "Explain microservices"}'
# → {"answer": "Mock response: Explain microservices"}
```

---

## Part 3: Cloud Deployment

### Exercise 3.1: Render deployment

- **URL:** https://day12-agent.onrender.com
- **Platform:** Render (Docker / Web Service)
- **Screenshot:** [Render dashboard](screenshots/dashboard.png), [API test](screenshots/test.png)

**Verified working:**
```bash
curl https://day12-agent.onrender.com/health
→ {"status":"ok","version":"1.0.0","environment":"production",...}

curl https://day12-agent.onrender.com/ask -X POST \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello from Render"}'
→ {"question":"Hello from Render","answer":"Tôi là AI agent được deploy lên cloud...","model":"gpt-4o-mini"}
```

---

## Part 4: API Security

### Exercise 4.1: API Key Authentication

**Test results:**
```bash
# Without key → 401 Unauthorized ✅
curl http://localhost:8000/ask -X POST
→ {"detail":"Invalid or missing API key..."}

# With key → 200 OK ✅
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: dev-key-change-me-in-production"
→ {"question":"...","answer":"...","model":"gpt-4o-mini"}
```

**How it works:**
```python
def verify_api_key(api_key: str = Header(...)):
    if api_key != settings.AGENT_API_KEY:
        raise HTTPException(401, "Invalid key")
    return api_key
```

### Exercise 4.2: JWT Authentication

**JWT Flow:**
1. Client gửi `POST /token` với username + password
2. Server verify → trả về JWT token (signed với SECRET_KEY)
3. Client gửi request với `Authorization: Bearer <token>`
4. Server decode token → extract user_id, role → process request

**Lấy token:**
```bash
curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'
→ {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
```

**Dùng token:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
→ {"answer": "Mock response: Explain JWT"}
```

**JWT vs API Key:**
| | API Key | JWT |
|--|---------|-----|
| Stateless | ✅ | ✅ |
| Expiry | ❌ | ✅ (60 phút) |
| Contains claims | ❌ | ✅ (role, user_id) |
| Revocation | Hard | Hard |

### Exercise 4.3: Rate Limiting

**Algorithm:** Sliding Window Counter
- Mỗi user có deque lưu timestamps của requests trong 60 giây
- Mỗi request mới: xóa timestamps cũ hơn 60s, đếm còn lại
- Nếu ≥ limit → raise 429

**Rate tiers:**
- `user`: 10 req/min
- `admin`: 100 req/min

**Test output:**
```bash
for i in {1..12}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"question": "Test '$i'"}'; echo ""
done

# Request 1-10: 200 OK ✅
# Request 11:
→ {"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":58}}
# Status: 429 Too Many Requests
# Headers: X-RateLimit-Remaining: 0, Retry-After: 58
```

### Exercise 4.4: Cost Guard Implementation

**Logic:**
- Each user has monthly budget ($5-$10)
- Track spending in memory (daily_cost variable)
- Reset at midnight
- If spending > budget → return 402 Payment Required

**Code:**
```python
def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    
    # Reset if new day
    if today != _cost_reset_day:
        _daily_cost = 0.0
    
    # Check budget
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted")
    
    # Estimate cost: ~$0.00015 per 1k input tokens, $0.0006 per 1k output
    cost = (input_tokens/1000)*0.00015 + (output_tokens/1000)*0.0006
    _daily_cost += cost
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

**Implemented in main.py:**
```python
@app.get("/health")
def health():
    """Liveness probe - is container still alive?"""
    return {"status": "ok"}

@app.get("/ready")  
def ready():
    """Readiness probe - can accept traffic?"""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}
```

### Exercise 5.2: Graceful shutdown

Signal handler catches SIGTERM from container orchestrator, finishes current requests before exiting.

### Exercise 5.3: Stateless design

**Anti-pattern:**
```python
conversation_history = {}  # In memory

@app.post("/ask")
def ask(user_id: str):
    history = conversation_history.get(user_id, [])  # Fails on second instance!
```

**Correct:**
```python
@app.post("/ask")
def ask(user_id: str):
    history = redis.lrange(f"history:{user_id}", 0, -1)  # Works on any instance!
```

Why? When scaling to 3 instances, each has its own memory. Redis is shared.

### Exercise 5.4: Load Balancing

```bash
docker compose up --scale agent=3
```

**Observed:**
- 3 agent instances start: `agent-1`, `agent-2`, `agent-3`
- Nginx round-robin phân tán requests đều cho 3 instances
- Nếu 1 instance die → healthcheck fail → Nginx bỏ khỏi pool tự động

**Logs cho thấy traffic phân tán:**
```
agent-1  | GET /ask → 200
agent-3  | GET /ask → 200
agent-2  | GET /ask → 200
agent-1  | GET /ask → 200
```

**docker-compose.yml key config:**
```yaml
deploy:
  replicas: 3
nginx:
  upstream agent { server agent:8000; }  # Docker DNS tự load balance
```

### Exercise 5.5: Test Stateless

```bash
python test_stateless.py
```

**Output:**
```
============================================================
Stateless Scaling Demo
============================================================

Session ID: session-abc123

Request 1: [agent-2]
  Q: What is Docker?
  A: Mock response: What is Docker?...

Request 2: [agent-1]
  Q: Why do we need containers?
  A: Mock response: Why do we need containers?...

Request 3: [agent-3]
  Q: What is Kubernetes?
  A: Mock response: What is Kubernetes?...

------------------------------------------------------------
Total requests: 5
Instances used: {'agent-1', 'agent-2', 'agent-3'}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 10
✅ Session history preserved across all instances via Redis!
```

**Kết luận:** Dù mỗi request đến instance khác nhau, conversation history vẫn nguyên vẹn vì state được lưu trong Redis (shared), không phải trong memory của từng instance.

---

## Part 6: Final Project — Production-Ready Agent (Built from Scratch)

**GitHub repo:** https://github.com/quangqui2502/day12-final-agent  
**Live URL:** https://day12-final-agent.onrender.com

### Architecture

```
Client
  │
  ▼
Nginx (port 80)
  │
  ▼
FastAPI Agent (Uvicorn)
  │
  ▼
Redis (Render Key Value)
  - rate limiting: sorted set sliding window
  - conversation history: list per user
  - cost tracking: monthly counter per user
```

### Key design decisions

**Rate limiter** — Redis sorted set (sliding window), không dùng in-memory để có thể scale ngang:
```python
pipe.zremrangebyscore(redis_key, 0, window_start)
pipe.zcard(redis_key)
pipe.zadd(redis_key, {str(now): now})
```

**Cost guard** — track per user per month trong Redis, auto-expire 35 ngày:
```python
key = f"cost:{user_key}:{month}"  # e.g. cost:alice:2026-04
r.incrbyfloat(key, cost)
r.expire(key, 35 * 24 * 3600)
```

**Conversation history** — lưu Redis list, load 10 messages gần nhất:
```python
r.rpush(f"history:{user_id}", json.dumps({"role": "user", "content": question}))
history = r.lrange(f"history:{user_id}", -10, -1)
```

### Live test results

```bash
# Health
curl https://day12-final-agent.onrender.com/health
→ {"status":"ok","version":"1.0.0","uptime_seconds":20.9}

# Ask (turn 1)
curl https://day12-final-agent.onrender.com/ask -X POST \
  -H "X-Api-Key: dev-key-please-change" \
  -d '{"user_id":"alice","question":"What is Docker?"}'
→ {"answer":"Docker is a containerization platform...","history_length":1}

# Ask (turn 2 — history preserved)
curl https://day12-final-agent.onrender.com/ask -X POST \
  -H "X-Api-Key: dev-key-please-change" \
  -d '{"user_id":"alice","question":"What is Redis?"}'
→ {"answer":"[Turn 2] Redis is an in-memory data store...","history_length":2}

# No auth → 401
curl https://day12-final-agent.onrender.com/ask -X POST
→ {"detail":"Missing or invalid API key. Add header: X-Api-Key: <key>"}
```

### Features checklist

- ✅ Multi-stage Dockerfile (builder + runtime, non-root user)
- ✅ Environment variables (no hardcoded secrets)
- ✅ API key authentication (X-Api-Key header)
- ✅ Rate limiting — Redis sorted set, 10 req/min
- ✅ Cost guard — Redis monthly counter, $10/month
- ✅ Conversation history — Redis list, stateless
- ✅ Health check `/health` + readiness `/ready`
- ✅ Graceful shutdown (SIGTERM handler)
- ✅ Structured JSON logging
- ✅ Deployed on Render with Redis

---

## Summary

✅ Understand dev vs production gaps  
✅ Multi-stage Docker reduces image size 86%  
✅ API key authentication prevents unauthorized access  
✅ Rate limiting + cost guard protect budget  
✅ Health checks enable auto-restart  
✅ Graceful shutdown prevents data loss  
✅ Stateless design enables horizontal scaling  
