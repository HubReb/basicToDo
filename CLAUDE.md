# CLAUDE.md — basicToDo Agent Context

This file provides Claude Code with project-specific context for development assistance.

## Project Overview

Full-stack ToDo application. Backend: FastAPI + SQLAlchemy async + SQLite.
Frontend: React 19 + Chakra UI v3 + React Query v5 + TypeScript.

## Running the App

```bash
# Backend
uv run python -m backend.app.main

# Frontend
cd frontend && npm run dev

# Backend tests
uv run pytest backend/tests/

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend tests
cd frontend && npm run test
```

## Constitution

All work on this project MUST comply with `.specify/memory/constitution.md`.
Key non-negotiables:
- Async-only DB access (aiosqlite + AsyncSession)
- Backend coverage ≥ 80%
- No duplicate logic (single source of truth)
- Optimistic UI updates on all mutations
- API p95 < 200ms; bundle < 500 KB gzip

<!-- SPECKIT START -->
Active implementation plan: specs/002-modernize-fullstack/plan.md
<!-- SPECKIT END -->
