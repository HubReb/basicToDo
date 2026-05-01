# basicToDo

A learning project that grew into a spec-driven modernization playground. Started as a SQLAlchemy and React learning exercise, now used to explore async architecture patterns, ORM evolution, and AI-assisted development workflows.
## Why this exists
Most ToDo tutorials stop at CRUD. This repo continues past that line: how does a small full-stack project evolve when you take async I/O, type discipline, and architecture decisions seriously? What does spec-driven development look like when applied to a real (if small) codebase?

### Stack
* __Backend__ : Python 3.12+, FastAPI, async SQLAlchemy with aiosqlite, Pydantic for runtime validation, mypy for static guarantees, uv for reproducible environments.
* __Frontend__: TypeScript, React with React Query for server state, Vite for build tooling.

## Architecture decisions
Key choices documented inline as the project evolves:
* __Async-first backend__ aiosqlite + AsyncSession instead of sync SQLAlchemy. Trade-off: more complexity in session management, gain in I/O parallelism.
* __Single ORM mapping__ Earlier versions used dual mapping (declarative + imperative) — removed in favor of a single declarative pattern after the cost-benefit analysis showed the duality served no real purpose.
* __Soft-delete pattern__ Deletion marks records rather than removing them, with explicit restore and purge endpoints. Adds complexity but enables undo workflows.

## Functionality

* Add, update, delete (soft) ToDo items
* Restore deleted items
* Inline editing on update

![image](images/basicAppAddToDo.png)
![image](images/basicAppAddUpdateToDo.png)
![image](images/basicAppDeleteToDo.png)


## Setup

### Backend

Requires `uv`. Install per uv documentation.
```bash
uv sync
python -m app.main
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

For production build:
```bash
tsc -b && vite build
```

### Testing

Backend uses pytest, frontend uses vitest.
```bash
uv run pytest
cd frontend && npm test -- --run
```

## Roadmap
Active development focuses on backend refactoring and async pattern refinement. Planned next:

* Mark-as-done workflow with completion timestamps
* Subtask hierarchy
* Reminder/deadline tracking
* Light mode UI

__Future explorations:__ time-to-completion analysis for predictive estimation, AI-assisted ToDo suggestions.
