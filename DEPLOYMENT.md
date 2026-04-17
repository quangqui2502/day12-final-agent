# Deployment Information

## Public URL
https://day12-final-agent.onrender.com

## Platform
Render (Docker / Web Service) + Key Value (Redis)

## Test Commands

### Health Check
```bash
curl https://day12-final-agent.onrender.com/health
# {"status":"ok","version":"1.0.0","uptime_seconds":...}
```

### Without auth (401)
```bash
curl https://day12-final-agent.onrender.com/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# {"detail":"Missing or invalid API key. Add header: X-Api-Key: <key>"}
```

### Ask with API key (200)
```bash
curl https://day12-final-agent.onrender.com/ask -X POST \
  -H "X-Api-Key: dev-key-please-change" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","question":"What is Docker?"}'
```

### Conversation history
```bash
curl https://day12-final-agent.onrender.com/history/alice \
  -H "X-Api-Key: dev-key-please-change"
```

### Rate limit test (429 after 10 requests)
```bash
for i in {1..12}; do
  curl https://day12-final-agent.onrender.com/ask -X POST \
    -H "X-Api-Key: dev-key-please-change" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"tester","question":"Test '$i'"}'; echo ""
done
```

## Environment Variables
- `AGENT_API_KEY` = dev-key-please-change
- `REDIS_URL` = redis://red-d7gvggf7f7vs73dbvhhg:6379
- `ENVIRONMENT` = production
- `RATE_LIMIT_PER_MINUTE` = 10
- `MONTHLY_BUDGET_USD` = 10.0
