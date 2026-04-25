# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

basicToDo is a full-stack ToDo application serving as a learning playground for modern web technologies. It's in early beta with rapid development and is not intended for production use.

## Common Commands

### Backend (Python/FastAPI)

From project root:

```bash
# Install dependencies
uv sync --locked --all-extras --dev

# Run backend server (from project root)
python -m backend.app.main
# Server runs on http://0.0.0.0:8000 with hot reload enabled

# Run all tests (from project root - recommended for CI/coverage)
uv run pytest backend/tests/

# Run all tests (from backend directory)
cd backend && uv run pytest tests/

# Run specific test file
uv run pytest backend/tests/test_todo.py

# Run linting
cd backend && uv run pylint app/*.py

# Run type checking
cd backend && uv run mypy backend/app/

# Format code
cd backend && uv run black app/
```

### Frontend (React/TypeScript/Vite)

From frontend directory:

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Preview production build
npm run preview
```

### Database Setup

The SQLite database is auto-created on backend startup via SQLAlchemy's `create_all()`.

For manual initialization:
```bash
cd backend
uv run python scripts/init_db.py
```

Or programmatically:
```python
from backend.app.data_access.database import Base, engine
Base.metadata.create_all(bind=engine)
```

Note: The initialization script uses SQLAlchemy ORM to ensure the schema matches the model definitions exactly, avoiding drift between manual SQL and ORM definitions.

## Architecture

### Backend: Clean Architecture Pattern

The backend follows a strict layered architecture with clear separation of concerns:

```
API Layer (FastAPI Routes)
    ↓
Business Logic Layer (ToDoService)
    ↓
Data Access Layer (Repository)
    ↓
Database Layer (SQLAlchemy ORM)
```

**Key architectural principles:**

1. **Dependency Injection via Factory Pattern**: Services are created through `backend/app/factory.py:create_todo_service()`, which wires up the dependency chain (Repository → Service → API)

2. **Repository Pattern**: `backend/app/data_access/repository.py` implements both an abstract interface (`ToDoRepositoryInterface`) and concrete implementation (`ToDoRepository`) for database operations

3. **Layer Responsibilities**:
   - `backend/app/api/api.py`: HTTP routing, request/response handling, error mapping to status codes
   - `backend/app/business_logic/todo_service.py`: Business rules, validation (SQL injection protection, UUID validation), orchestration
   - `backend/app/data_access/repository.py`: Database queries, session management via context managers
   - `backend/app/data_access/database.py`: SQLAlchemy engine config, connection pooling

4. **Data Flow**:
   - Request schemas (`backend/app/schemas/`) validate incoming data via Pydantic
   - Service layer processes requests using domain models (`backend/app/models/ToDoEntryData`)
   - Repository layer persists to SQLite via SQLAlchemy ORM
   - Response schemas serialize data back to client

5. **Error Handling**: Custom exceptions in `backend/app/business_logic/exceptions.py` propagate through layers and are mapped to HTTP status codes at the API layer

### Frontend: React Component Architecture

- Component-based structure with Chakra UI for styling
- Context API for global state management (planned/in development)
- Direct REST API calls to backend (no state management library yet)
- Components in `frontend/src/components/` (e.g., Header, Todos)

### Database Schema

Single entity: **ToDo** table
- `id` (UUID, Primary Key)
- `title` (String, 255 chars, required)
- `description` (String, 255 chars, optional)
- `created_at` (TIMESTAMP, required)
- `updated_at` (TIMESTAMP, optional)
- `deleted` (Boolean, default: False) - supports soft deletes
- `done` (Boolean, default: False)
- Index on `title` field

## Technology Stack

**Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0, SQLite, Uvicorn, Pydantic
**Frontend**: React 19, TypeScript 5.8, Vite 6, Chakra UI 3, Emotion, Framer Motion
**Dev Tools**: MyPy (strict mode), Pylint, Black, Pytest, ESLint
**Package Managers**: UV (Python), NPM (JavaScript)

## Type Safety and Quality

- **MyPy strict mode enabled** in `pyproject.toml` with comprehensive checks:
  - `disallow_untyped_defs = true`
  - `strict_optional = true`
  - `warn_return_any = true`
  - All new Python code MUST have type annotations

- **Security**: Input sanitization with regex validation, UUID validation, SQL injection protection in service layer

## File Structure Notes

- Backend entry point: `backend/app/main.py` - initializes database schema and starts Uvicorn
- Dependency wiring: `backend/app/factory.py` - creates service instances with dependencies
- Logging: Custom logger implementation in `backend/app/logger.py`
- Configuration: `backend/app/config.py`
- Database session management: Use `safe_session_scope` context manager from `backend/app/data_access/database.py`

## Current Development Focus

Per README.md, the project is actively working on:
- UX improvements (soft delete UI, restore functionality, mark as done, light mode)
- New features (time tracking, AI suggestions, subtasks, reminders)
- Code refactoring for better modularity (both frontend and backend)

When making changes, align with the clean architecture pattern and maintain the separation of concerns across layers.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/001-modernize-fullstack/plan.md
<!-- SPECKIT END -->
