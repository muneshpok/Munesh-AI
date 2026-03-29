.PHONY: backend frontend up

backend:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload

frontend:
	cd frontend && npm install && npm run dev

up:
	docker compose up
