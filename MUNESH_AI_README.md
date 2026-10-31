# Munesh AI - WhatsApp Business Automation Platform

An AI-powered WhatsApp business automation platform with multi-agent AI system, CRM dashboard, and SaaS-ready architecture.

## Architecture

```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── agents/       # Multi-agent AI system (Chat, Sales, Support, Booking)
│   │   ├── core/         # Config, database, logging
│   │   ├── models/       # SQLAlchemy models & Pydantic schemas
│   │   ├── routes/       # API endpoints (WhatsApp, CRM, Health)
│   │   ├── services/     # Business logic (LLM, WhatsApp, CRM, Memory)
│   │   ├── tests/        # Test suite
│   │   ├── tools/        # Tool registry & execution
│   │   └── main.py       # FastAPI application
│   ├── cli.py            # CLI management commands
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js dashboard
│   ├── app/              # App Router pages (Dashboard, Leads, Messages)
│   ├── lib/              # API client
│   └── package.json
└── docker-compose.yml
```

## Features

- **Multi-Agent System**: Chat, Sales, Support, and Booking agents with intent-based routing
- **WhatsApp Integration**: Webhook endpoint for WhatsApp Cloud API
- **CRM System**: Lead tracking with status lifecycle (new → contacted → demo_booked → closed)
- **Memory System**: Per-user conversation history (last 10 messages)
- **Tool Execution**: Modular tools (send_whatsapp_message, save_lead, update_crm, send_demo_link)
- **Dashboard**: Real-time metrics, lead management, message history
- **LLM Support**: Gemini, OpenAI, and Claude with automatic fallback
- **CLI Commands**: Start server, view leads, broadcast messages

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up -d
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | App info |
| GET | `/health` | Health check |
| GET | `/whatsapp/webhook` | WhatsApp verification |
| POST | `/whatsapp/webhook` | Receive WhatsApp messages |
| GET | `/api/leads` | List all leads |
| POST | `/api/update-status` | Update lead status |
| GET | `/api/metrics` | Dashboard metrics |
| GET | `/api/messages/{phone}` | Message history |
| POST | `/api/broadcast` | Broadcast message |

## Environment Variables

See `backend/.env.example` for all configuration options.

Key variables:
- `WHATSAPP_PHONE_NUMBER_ID` - WhatsApp Business phone number ID
- `WHATSAPP_ACCESS_TOKEN` - WhatsApp Cloud API token
- `GEMINI_API_KEY` - Google Gemini API key
- `LLM_PROVIDER` - LLM provider (gemini/openai/claude)

## Testing

```bash
cd backend
python -m pytest app/tests/ -v
```

## CLI Usage

```bash
cd backend
python cli.py start              # Start the server
python cli.py leads              # View all leads
python cli.py broadcast "Hello"  # Broadcast message
```
