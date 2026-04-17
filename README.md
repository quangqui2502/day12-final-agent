# Day 12 Final Agent — QuangQui

Production-ready AI agent with authentication, rate limiting, cost guard, and stateless scaling.

## Quick Start

```bash
cp .env.example .env.local
docker compose up
```

## Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | Liveness probe |
| `/ready` | GET | ❌ | Readiness probe |
| `/ask` | POST | ✅ | Ask the agent |
| `/history/{user_id}` | GET | ✅ | Get conversation history |
| `/history/{user_id}` | DELETE | ✅ | Clear history |

## Test

```bash
# Health
curl http://localhost/health

# Ask (requires API key)
curl http://localhost/ask -X POST \
  -H "X-Api-Key: dev-key-please-change" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "question": "What is Docker?"}'

# History
curl http://localhost/history/alice \
  -H "X-Api-Key: dev-key-please-change"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_API_KEY` | `dev-key-please-change` | API authentication key |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `RATE_LIMIT_PER_MINUTE` | `10` | Max requests per user per minute |
| `MONTHLY_BUDGET_USD` | `10.0` | Monthly cost limit per user |
| `ENVIRONMENT` | `development` | Environment name |
| `PORT` | `8000` | Server port |
