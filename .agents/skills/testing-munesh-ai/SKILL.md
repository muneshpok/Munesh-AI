# Testing Munesh AI Platform

## Devin Secrets Needed
- No secrets required for local testing
- WhatsApp Cloud API token needed only for live message testing (not required for local)
- LLM API key (Gemini/OpenAI/Claude) needed only if testing AI-generated responses

## Local Dev Setup

### Start Backend
```bash
cd backend
fuser -k 8000/tcp 2>/dev/null  # Kill any existing process on port
uvicorn app.main:app --reload --port 8000 &
```

### Start Frontend
```bash
cd frontend
fuser -k 3001/tcp 2>/dev/null  # Kill any existing process on port
PORT=3001 npm run dev &
```

Note: Port 3000 may be occupied. Use 3001 as fallback. The `lsof` command might not be available — use `fuser -k <port>/tcp` instead.

### Verify Servers
```bash
curl -s http://localhost:8000/health  # Should return {"status":"healthy"}
curl -s http://localhost:3001 | head -5  # Should return HTML
```

## Test Data Seeding

### Create Leads via WhatsApp Webhook
```bash
curl -s -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"123","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"phone_number_id":"123"},"contacts":[{"profile":{"name":"Test User"}}],"messages":[{"from":"1234567890","type":"text","text":{"body":"Hello"},"id":"msg1","timestamp":"1700000001"}]},"field":"messages"}]}]}'
```

### Update Lead Status
```bash
curl -s -X POST http://localhost:8000/api/update-status \
  -H "Content-Type: application/json" \
  -d '{"phone":"1234567890","status":"contacted"}'
```

Valid statuses: `new`, `contacted`, `demo_booked`, `follow_up`, `closed`, `lost`

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/leads` | GET | All leads |
| `/api/metrics` | GET | Dashboard metrics |
| `/api/update-status` | POST | Update lead status |
| `/api/analytics/insights` | GET | Analytics insights |
| `/api/analytics/run-loop` | POST | Trigger Daily Loop |
| `/api/self-improvement/status` | GET | Self-Improvement status |
| `/api/self-improvement/run` | POST | Run improvement cycle |
| `/api/performance/metrics` | GET | Performance metrics |
| `/api/performance/analyze` | POST | Run performance analysis |
| `/api/follow-ups/sequences` | GET | Follow-up sequence definitions |
| `/api/follow-ups/status/{phone}` | GET | Per-lead sequence status |
| `/api/follow-ups/run` | POST | Trigger follow-up sequences |
| `/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=munesh_ai_verify_token_2024&hub.challenge=test123` | GET | Webhook verification |

## Frontend Pages

| Path | Page | Key Elements |
|------|------|--------------|
| `/` | Dashboard | 8 metric cards, Quick Actions |
| `/leads` | Leads Table | Status filters, inline status dropdown |
| `/messages` | Messages | Chat-style conversation history |
| `/analytics` | Analytics | 3 tabs: Live Insights, Daily Reports, Automation Logs |
| `/self-improvement` | Self-Improvement | 4 tabs: Overview, Agent Prompts, Strategy Config, History |
| `/performance` | Performance | Metric cards, lead breakdown, message activity, Run Analysis |
| `/pricing` | Pricing | 3 plan cards ($49/$149/$499), FAQs, social proof |

## Running Unit Tests
```bash
cd backend && python -m pytest app/tests/ -v
```

Expected: 150+ tests passing across 7 test files.

## Common Issues

- **Port already in use**: Use `fuser -k <port>/tcp` to kill stale processes
- **Daily Loop auto-runs**: The background scheduler runs 60s after startup and may modify lead data (e.g., nurturing new leads to contacted). Account for this when writing assertions.
- **Test database isolation**: API tests use separate SQLite files (e.g., `test_follow_up_api.db`) to avoid cross-test data leaks
- **LLM without API key**: AI features return generic/fallback responses. Tests should assert non-empty strings rather than specific content.
- **Vercel preview**: Frontend deploys but shows "Connection Issue" because there's no deployed backend. Only useful for static page verification (e.g., Pricing page).
