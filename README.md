# Munesh AI Platform

Munesh AI is now structured as a SaaS-ready multi-agent AI operating system with:

- **FastAPI backend** for auth, agent execution, lifecycle, and task APIs
- **Next.js frontend** for chat, dashboard, and task UX
- **Agent orchestration layer** with lifecycle manager + execution engine
- **Memory stack** with short-term context + long-term vector-like retrieval
- **Tool system** with registry and built-in web search, file reader, and API caller

## Repository Layout

- `backend/` - FastAPI services and AI runtime components
- `frontend/` - Next.js application (App Router)
- `docker-compose.yml` - local multi-service runtime

## Quickstart

### Option A: Docker Compose

```bash
docker compose up
```

- Backend: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

### Option B: Local Dev (without Docker)

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`
- `GET /api/v1/agents/tasks/{task_id}`

## Notes

This baseline is intentionally modular and ready for further enhancements:

- persistent DB integration (Postgres/Redis)
- production auth hardening
- real embedding/vector database integration (pgvector, Milvus, Pinecone)
- queue worker for asynchronous multi-step agent plans
