# Testing Munesh AI Platform

## Overview
Munesh AI is a WhatsApp business automation SaaS with FastAPI backend and Next.js frontend. Testing involves running both servers locally, seeding test data via webhook simulation, and verifying features through the browser UI.

## Server Setup

### Backend (FastAPI)
```bash
cd backend
nohup uvicorn app.main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
# Verify: curl -s http://localhost:8000/health
```

### Frontend (Next.js)
```bash
cd frontend
nohup npm run dev -- --port 3001 > /tmp/frontend.log 2>&1 &
# Verify: curl -s -o /dev/null -w "%{http_code}" http://localhost:3001
```

Wait ~5 seconds after starting each server before testing.

## Seeding Test Data

Seed leads via WhatsApp webhook simulation:
```bash
curl -s -X POST http://localhost:8000/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"1001","id":"msg_1","timestamp":"1712000000","type":"text","text":{"body":"I want to learn about AI automation"}}],"contacts":[{"profile":{"name":"Test Lead"}}]}}]}]}'
```

Repeat with different phone numbers and messages for multiple leads. Use buying-intent messages ("How much does it cost?") for sales agent routing, support messages for support agent, and "Can I book a demo?" for booking agent.

## Key API Endpoints
- `GET /health` — Health check
- `GET /api/leads` — List all CRM leads
- `GET /api/campaigns/templates` — Campaign templates (6 total)
- `GET /api/campaigns/audience-filters` — Audience filters (7 total)
- `GET /api/campaigns/` — List campaigns
- `POST /api/campaigns/run` — Run full campaign pipeline
- `GET /api/analytics/insights` — Analytics insights
- `GET /api/performance/metrics` — Performance metrics
- `GET /api/self-improvement/status` — Self-improvement status

## Feature Testing Guide

### Dashboard (`/`)
- Verify metric cards show correct counts (Total Leads, Contacted, Demo Booked, etc.)
- Check leads table with status filters
- Test status update via dropdown

### Campaign System (`/campaigns`)
- **Create tab**: 6 template cards should load, audience dropdown has 7 filters + default
- **Launch pipeline**: Select template → fill name/message → click "Launch Campaign (Full Pipeline)" → auto-switches to Campaigns tab
- **Verify**: Campaign card shows status "completed", metrics grid (Targeted, Sent, Delivered, Responded, Converted, Response %, Convert %), optimization suggestions
- **Pipeline Steps tab**: Shows 7 numbered API steps + Full Pipeline entry
- Note: Template selection auto-updates the audience dropdown to the template's default audience
- Note: The `{name}` placeholder in custom messages gets replaced with lead names

### Analytics (`/analytics`)
- 3 tabs: Live Insights, Daily Reports, Automation Logs
- "Run Daily Loop Now" button triggers the daily loop
- Verify funnel metrics match seeded data

### Self-Improvement (`/self-improvement`)
- 4 tabs: Overview, Prompts, Analysis, Strategy
- "Run Improvement Cycle" button triggers the cycle
- Verify status changes from "idle" to "running" to "completed"

### Performance (`/performance`)
- Metric cards, lead status breakdown, message activity
- "Run Analysis" button generates AI suggestions

### Pricing (`/pricing`)
- 4 tier cards: Free ($0), Starter ($49), Pro ($149), Enterprise ($499)
- Free card shows "Free forever" (not "$0/month")
- Pro card has "Most Popular" badge

## Common Issues
- Backend may fail to start if port 8000 is already in use — kill existing process first with `lsof -ti:8000 | xargs kill`
- Frontend default port is 3000 but we use 3001 to avoid conflicts — always pass `--port 3001`
- Campaign "Targeted" count includes ALL leads in DB, not just newly seeded ones
- WhatsApp messages show "sent" not "delivered" without real API credentials — this is expected
- The database is SQLite by default (munesh_ai.db in backend/) — data persists between server restarts
- If campaigns API returns empty templates, check that backend started without errors in /tmp/backend.log

## Unit Tests
```bash
cd backend && python -m pytest app/tests/ -v
```
Expected: 190 tests passing (as of Campaign System implementation).

## Devin Secrets Needed
No secrets required for local testing. For production WhatsApp integration:
- `WHATSAPP_ACCESS_TOKEN` — WhatsApp Cloud API access token
- `WHATSAPP_PHONE_NUMBER_ID` — WhatsApp phone number ID
- `GEMINI_API_KEY` or `OPENAI_API_KEY` — For AI-powered message generation
