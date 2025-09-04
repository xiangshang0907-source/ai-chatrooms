# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Backend
  - Setup: cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
  - Run dev server: cd backend && source .venv/bin/activate && python -m app.main
  - Lint: cd backend && make lint
  - Format: cd backend && make format
  - Test (all): cd backend && source .venv/bin/activate && pytest -q
  - Test (single): cd backend && source .venv/bin/activate && pytest -q tests/test_health.py::test_health_endpoint
  - Test (with DB, manual): cd backend && source .venv/bin/activate && DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}_test pytest -q
    (Note: Construct DATABASE_URL from .env values - use individual POSTGRES_* fields from .env file)
  - Migrations (apply): cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_chatrooms python -m alembic upgrade head
  - Migrations (create): cd backend && python -m alembic revision --autogenerate -m "msg"

- Frontend
  - Dev: cd frontend && npm run dev
  - Build: cd frontend && npm run build
  - Start (production): cd frontend && npm run start
  - Preview: cd frontend && npm run preview

- Docker (Default)
  - Start services: docker-compose up -d postgres redis
  - Start backend via compose: docker-compose up -d backend

## Architecture overview

- Backend (Flask, Python 3.12)
  - Entry: backend/app/main.py loads app from backend/app/__init__.py
  - Config: backend/app/config.py pulls env (DB, Redis, JWT, LLM providers)
  - Extensions: CORS, SQLAlchemy (init_db), JWT (init_jwt)
  - Blueprints: health (backend/app/routes/health.py), auth, rooms, messages
  - Data models: SQLAlchemy models under backend/app/models (User, Room, Participant, Message, AgentProfile, ConversationRun)
  - Services: AI service (backend/app/services/ai_service.py) for non-streaming, StreamingService (backend/app/services/streaming_service.py) for SSE; AgentService handles default agent provisioning
  - Persistence: Alembic migrations (backend/alembic), PostgreSQL; tests configure DATABASE_URL
  - Tests: backend/tests with pytest; CI runs subset then full PG tests via .github/workflows/backend-ci.yml

- Frontend (React + Next.js + TS)
  - Entry: frontend/app/layout.tsx -> page.tsx
  - Components: Login/Register, RoomList, ChatRoom with SSE streaming
  - Dev server runs on :5173 with API proxy to backend:8000

## Notable endpoints

- GET /health
- Auth: POST /auth/register, POST /auth/login, POST /auth/refresh, GET/PATCH /auth/me
- Rooms and Messages: defined under /rooms/* with JWT; /rooms/<room_id>/messages and /rooms/<room_id>/messages/stream for SSE

## CI notes

- Workflow .github/workflows/backend-ci.yml installs backend deps, runs non-DB tests, provisions Postgres service, applies alembic migrations, then runs DB tests with DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_chatrooms_test

## Environment

- Required (common defaults in backend/app/config.py):
  - DATABASE_URL, REDIS_URL, SECRET_KEY, JWT_SECRET_KEY
  - LLM providers: QWEN_API_KEY/QWEN_API_BASE, OPENAI_API_KEY/OPENAI_API_BASE, AZURE_* or AWS_*
- IMPORTANT: Always check .env file for actual database credentials. Use the DATABASE_URL format from .env or construct it from POSTGRES_USER/POSTGRES_PASSWORD values when running alembic commands.

## Tips specific to this repo

- Use make targets in backend/Makefile for lint/format/test
- When developing streaming, prefer the SSE route: backend/app/routes/messages.py:116 and generate_ai_stream_response at backend/app/routes/messages.py:306
- For debugging auth in tests, see backend/tests/test_auth_simple.py and backend/tests/test_auth_full.py
- Frontend expects backend on 8000; frontend runs on :5173 with API proxy via next.config.js rewrites under /api/* (auth service uses /api/*, ChatRoom uses direct backend URLs)
