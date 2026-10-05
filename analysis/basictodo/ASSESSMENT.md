# Modernization Assessment: basicToDo

_System: `legacy/basictodo` · branch `legacy` @ `a2d59f1` · Assessed 2026-10-03 · Inputs: [PREFLIGHT.md](PREFLIGHT.md), [ARCHITECTURE.mmd](ARCHITECTURE.mmd)_

## Executive Summary

basicToDo is a small single-user todo application: a FastAPI + SQLAlchemy + SQLite backend serving a React 19 single-page app. It has **1.7k lines of production code** and 2.6 times that in tests (4.5k lines). The stack is **already current** (Python 3.13, React 19, Vite 6), so the risk is not technology age.

The risk is correctness and security posture. Four user-visible defects were reproduced:

- Titles containing ordinary words like "or", "update" or "select" are rejected as SQL injection.
- Any todo beyond the first 10 never appears in the UI.
- An over-long title returns "409 ToDo already exists".
- Marking a todo done silently discards a rename sent in the same request.

On top of that, the API has **no authentication** and binds to `0.0.0.0`, and the pinned FastAPI 0.115 holds Starlette at a version with 7 open advisories.

**Recommendation: Refactor in place on the same stack (`/modernize-uplift`).** The order is: pin current behaviour, uplift the dependencies, consolidate the duplicated data layer, then fix each defect behind an explicit keep-or-fix decision. A rebuild is not warranted at this size on a modern stack.

## System Inventory

### Lines of code (`cloc` 2.10; `scc` not installed, per the fallback in Step 1)

`cloc legacy/basictodo`, excluding the two lockfiles (`package-lock.json` 9,306 lines, `uv.lock`):

| Language | Files | Blank | Comment | Code |
|---|---:|---:|---:|---:|
| Python | 68 | 1,527 | 823 | 4,827 |
| TypeScript (incl. TSX) | 38 | 253 | 219 | 1,281 |
| YAML (CI) | 6 | 54 | 72 | 295 |
| PlantUML | 2 | 28 | 0 | 164 |
| JSON | 5 | 6 | 0 | 113 |
| CSS | 2 | 21 | 0 | 112 |
| TOML | 1 | 8 | 0 | 91 |
| Markdown | 1 | 43 | 0 | 77 |
| JavaScript / HTML / SVG | 4 | 1 | 0 | 42 |
| **Total** | **127** | **1,941** | **1,114** | **7,002** |

| Slice | Code SLOC | Share |
|---|---:|---:|
| Backend production (`backend/app`, `backend/scripts`) | 710 | 11% |
| Frontend production (`frontend/src` excl. tests, plus root configs) | 1,037 | 17% |
| **Production total** | **1,747** | **28%** |
| Backend tests (`backend/tests`) | 4,117 | 66% |
| Frontend tests (vitest + Playwright) | 398 | 6% |
| **All source including tests** | **6,262** | 100% |

### Complexity (`lizard` 1.24, Python + TS + TSX, production only)

138 functions · mean CCN **1.9** · max CCN **7** · **0** functions over the CCN-15 threshold.

| CCN | Function | File |
|---:|---|---|
| 7 | `TodoList` | `frontend/src/components/todos/TodoList.tsx:8-47` |
| 6 | `TodoEditForm` (96 lines) | `frontend/src/components/todos/TodoEditForm.tsx:14-109` |
| 6 | `TodoForm` (96 lines, a near-copy of the above) | `frontend/src/components/todos/TodoForm.tsx:9-104` |
| 6 | toaster render callback | `frontend/src/components/ui/toaster.tsx:16-35` |
| 5 | `ErrorBoundary.render` | `frontend/src/components/errors/ErrorBoundary.tsx:32-52` |
| 5 | `handle_service_exceptions` async and sync wrappers (duplicated) | `backend/app/business_logic/decorators.py:22-35, 38-51` |
| 5 | `ToDoService.update_todo` | `backend/app/business_logic/todo_service.py:54-68` |
| 4 | `ToDoRepository.update_to_do` | `backend/app/data_access/repository.py:70-84` |
| 4 | `InputSanitizer.validate` | `backend/app/business_logic/validators/input_sanitizer.py:20-41` |

Complexity is not where the risk lies. The risk is in semantics (see Technical Debt).

### Technology fingerprint

| Concern | Finding | Evidence |
|---|---|---|
| Backend language and runtime | Python ≥3.13 (CI pins 3.13) | `pyproject.toml:9`, `.github/workflows/python-app.yml:27` |
| Backend frameworks | FastAPI 0.115.12 (Starlette 0.46.2), Pydantic 2.11.5, SQLAlchemy 2.0.43, sqlalchemy-utils 0.42.0, Uvicorn 0.34.3 | `uv.lock` |
| Frontend | React 19.2.0, TypeScript 5.8.3, Vite 6.4.1, Chakra UI 3.28.0, TanStack Query 5.90.10 | `frontend/package-lock.json` |
| Build and dependency management | uv (CI pins 0.7.16), 71 locked PyPI packages; npm, 650 installed packages; public registries only | `uv.lock`, `frontend/package-lock.json` |
| CI | GitHub Actions, 6 workflows: backend tests and coverage gate, frontend build, Playwright e2e, CodeQL, dependency-review, super-linter | `.github/workflows/*.yml` |
| Data store | SQLite file; default path `backend/todo.db` relative to the working directory; one table, `toDo` (id, title, description, created_at, updated_at, deleted, done). **The table is defined twice** (declarative `ToDoORM` for DDL; imperative `to_do_table` for reads and writes). No migrations. | `backend/app/data_access/database.py:20-35, 68-100` |
| Integration points | One REST API with 6 routes (`GET /`, `POST /todo`, `GET/PUT/DELETE /todo/{id}`, `GET /todo?limit&page`); CORS pinned to `http://localhost:5173`; auto-generated `/docs` and `/openapi.json`. No queues, batch jobs or external services. | `backend/app/api/api.py:20-91` |
| Config | Env vars `DATABASE_URL` and `VITE_API_BASE_URL`; host, port and reload hardcoded in `main.py:11`. The `config.py` / `config_dummy.json` pair is dead. | `backend/app/main.py`, `frontend/src/config/env.ts:12` |
| Tests | pytest: 433 pass, 1 skipped, **81.78%** line+branch coverage (gate 80%); **9 more tests never run** (`tests_*.py` prefix not collected). vitest: 13 component tests. Playwright: 13 e2e tests that boot both tiers. All pass locally (preflight). | `pyproject.toml:58-62`, `backend/tests/test_builders/**/tests_*.py` |

## Architecture-at-a-Glance

This is a clean layered stack with three back-edges:

- The validators import the service's exception module.
- The repository imports a request DTO (`TodoUpdateScheme`).
- `api.py` builds the whole object graph when it is imported.

The full Mermaid diagram (12 domains, 40 edges) is in **[ARCHITECTURE.mmd](ARCHITECTURE.mmd)**.

| # | Domain | Responsibility | Key files | Depends on |
|---|---|---|---|---|
| F1 | FE: App shell and shared UI | React root, provider stack, toasts, spinner, error boundary | `frontend/src/main.tsx`, `App.tsx`, `components/errors/*`, `components/common/*`, `components/ui/toaster.tsx`, `lib/toaster.ts`, `config/queryClient.ts` | F2 |
| F2 | FE: Todo feature UI | List (always page 1, size 10), create with a client-side UUID, edit title, delete after confirm; 255-character check on the client | `frontend/src/components/todos/*.tsx` | F3, F1 |
| F3 | FE: Server-state hooks | TanStack Query list query plus 3 optimistic mutations; cache key `['todos',{limit:10,page:1}]` hardcoded 9 times | `frontend/src/hooks/queries/*.ts` | F4 |
| F4 | FE: API client and contract types | `fetch` wrapper and error mapping; TypeScript types copied by hand from Pydantic | `frontend/src/services/api/*.ts`, `types/todo.ts`, `config/env.ts` | **B2 over HTTP** |
| B1 | BE: Bootstrap and composition root | `create_all`, then uvicorn on 0.0.0.0:8000 with reload; manual dependency injection; `init_db` script | `backend/app/main.py`, `factory.py`, `scripts/init_db.py` | B2, B4–B7 |
| B2 | BE: HTTP API | 6 routes; maps exceptions to 400/404/409/500 (inconsistently); module-level service singleton | `backend/app/api/api.py` | B1, B3, B4 |
| B3 | BE: Schemas (DTOs) | Create, update and read models; response envelopes (5 classes, 2 identical) | `backend/app/schemas/**` | — |
| B4 | BE: ToDo service | CRUD orchestration; `done=True` takes a different path; soft delete; exception-mapping decorator; entry builder | `backend/app/business_logic/{todo_service,decorators,exceptions}.py`, `builders/*` | B5, B6, B3, B7 |
| B5 | BE: Validation and sanitization | SQL-keyword blocklist (in practice a business rule), field and UUID validation | `backend/app/business_logic/validators/*` | B4 exceptions, B7 |
| B6 | BE: Persistence | Builds the DB URL, engine and session scope; **two table definitions**; repository filters `deleted=False` | `backend/app/data_access/*`, `backend/app/models/todo.py` | B3 (leak), B7 |
| B7 | BE: Platform logging | `CustomLogger` (miswired, see TD-3); dead `config.py` | `backend/app/logger.py`, `config.py` | stdlib |
| Q | Quality and tooling | pytest, vitest, Playwright, CI, PlantUML, README | `backend/tests/**`, `frontend/e2e/**`, `.github/workflows/**`, `documentation/**` | all |

**How each route is used:**

| Route | Caller |
|---|---|
| `POST /todo` | `useCreateTodo` → `TodoForm` |
| `PUT /todo/{id}` | `useUpdateTodo` → `TodoEditForm`. The UI never sends `done`. |
| `DELETE /todo/{id}` | `useDeleteTodo` → `TodoDeleteButton` (soft delete) |
| `GET /todo` | `useTodoList` → `TodoList` (page 1 only) |
| `GET /todo/{id}` | **No frontend caller** |
| `GET /` | **No frontend caller**. The e2e readiness check polls `/docs` instead. |

**Dangling or unused:**
- `backend/app/config.py` and `backend/config_dummy.json`
- `backend/app/services/` (empty)
- `backend/backend/tests/**` (9 empty `__init__.py` files)
- `hard_delete_to_do` (`repository.py:62`)
- `CustomLogger.log_*` helpers
- injected but unread `ToDoService.input_sanitizer`
- `todoApi.getById`
- `LoadingOverlay.tsx`
- `assets/react.svg`
- npm packages `add` and `snippet`
- `slowapi` (declared, never imported)

## Production Runtime Profile

**No telemetry is available.** No APM or observability source is connected, and there are no runtime logs. Production telemetry probably doesn't exist at all: the README says the app is "not intended for production". Step 4 was skipped. The closest stand-in for observed runtime behaviour is the Playwright e2e suite (13 tests, 18 s against live servers). It shows behaviour, not performance under load. Note that the miswired logger (TD-3) means even a running instance would emit no INFO-level logs to build a profile from.

## Technical Debt

Ranked by remediation value (modernization impact ÷ effort).

**How "verified" is used:** ✔ means reproduced against a live instance (FastAPI TestClient on a scratch copy) by this assessment. Other evidence comes from reading the code and from the analysis agents' probes.

| # | Finding | Category | Evidence | Impact | Fix | Effort |
|---|---|---|---|---|---|---|
| TD-1 | **SQL-keyword blocklist rejects ordinary todo text.** Whole words `or`, `create`, `update`, `delete` and `select`, plus `;` and `--`, return 400. ✔ "Buy milk or bread" gets 400; "Buy milk" gets 200. The blocklist adds no protection: every query is an ORM bound-parameter query. | Wrong validation posing as security | `backend/app/business_logic/validators/input_sanitizer.py:13-15, 37-39`; called through `field_validator.py:31,39` | High: user-facing bug, and a "rule" a naive port would carry forward | Delete the blocklist; enforce length and blank checks in Pydantic | S |
| TD-2 | **Exception → HTTP mapping is wrong, incomplete and copy-pasted.** Every `IntegrityError` becomes "already exists". ✔ A 300-character title returns **409 "ToDo already exists"**. On PUT the same violation, or `title: null`, is an **unhandled 500**. The repository's `except IntegrityError` blocks can never fire, because the commit happens outside them. | Error handling / duplication | `backend/app/business_logic/decorators.py:22-51`; `backend/app/api/api.py:42-50, 62-72, 77-85, 88-91`; `repository.py:47-51, 79-83` | High: wrong client semantics, 500s | Register one set of `app.exception_handlers`; map by which constraint failed; delete the duplicate sync wrapper | S |
| TD-3 | **`CustomLogger` is miswired.** It subclasses `Logger` but puts its handler on a separate `getLogger(name)`. INFO is dropped and WARNING+ goes to Python's last-resort handler, unformatted. ✔ `init_db.py` prints nothing. | Defect / observability | `backend/app/logger.py:6-26`; all callers | Med-High: no usable logs to baseline legacy behaviour | `logging.getLogger(__name__)` plus one `dictConfig` at startup | S |
| TD-4 | **Pagination hides todos.** The UI only ever requests page 1 with size 10. There is no `ORDER BY`, and `results` is the page size, not a total. ✔ After 11 creates, the newest todo is not on page 1. `limit`/`page` are unbounded (see SEC-004). | Missing behaviour / hardcoded config | `frontend/src/components/todos/TodoList.tsx:9`; `repository.py:92-97`; `api.py:88-91` | High: silent data invisibility | `ORDER BY created_at DESC`; `Query(ge=1, le=100)`; return a total; add a pager | S-M |
| TD-5 | **Data layer: two table definitions on two MetaData objects, 1.x-era idioms, timestamp drift.** DDL comes from `ToDoORM`; reads and writes go through `to_do_table`. ✔ `created_at` is naive local time while `updated_at` is UTC set **at insert** by `func.now()` (14:02 vs 12:02 for one row), and it is never bumped on edit. Other issues: deprecated `sqlalchemy.ext.declarative`; `mapped_column` used as a dataclass default; sync DB calls inside `async def`; no migrations. | Duplication / deprecated API | `backend/app/data_access/database.py:9,17,68-100`; `models/todo.py:17`; `todo_entry_builder.py:30` | High: a port must first decide which definition is authoritative | One `DeclarativeBase`/`Mapped[]` model, an Alembic baseline, UTC `server_default`/`onupdate`, `def` handlers or `AsyncSession` | M |
| TD-6 | **`done=True` path drops the other fields.** ✔ A PUT with `{"title":"Renamed","done":true}` returns 200 with `done=true` and the old title. | Logic defect | `backend/app/business_logic/todo_service.py:55-57, 89-98` | Medium: latent (the UI never sends `done`) but part of the API contract | Apply all fields, then the done transition | S |
| TD-7 | **Dead and broken code.** `config.py` reads `self.config_file` before setting it. Also dead: `config_dummy.json`, empty `services/`, `backend/backend/tests/**`, unused `hard_delete_to_do`, the injected-but-unused sanitizer, `ValidationError(str)` (raises TypeError under Pydantic v2), and Vite template leftovers. | Dead code | `backend/app/config.py:8-11`; `todo_service.py:32,35`; `repository.py:62`; `frontend/src/App.css:8-42` | Medium: extra surface to read, port and test | Delete | S |
| TD-8 | **CI gates can't fail, and not everything runs.** mypy and ESLint are `continue-on-error`. pylint runs with `--exit-zero` over `app/*py`, which skips every subpackage. ✔ **9 builder tests are never collected** (`tests_*.py`). Production `safe_session_scope` and the sync decorator path are never exercised. Coverage is 81.78% against an 80% gate. | Process debt | `.github/workflows/python-app.yml:41-43, 104-107`; `frontend.yml:38-42`; `pyproject.toml:60` | Medium: the safety net for modernization is thinner than it looks | Make gates blocking; lint recursively (ruff); rename the two test files | S |
| TD-9 | **Dependency manifest hygiene.** black, mypy, pylint, pytest, pytest-asyncio, factory-boy and `types-*` are *runtime* dependencies. There are three overlapping SQLAlchemy stub mechanisms. `slowapi` is never imported. The frontend has the junk runtime deps `add` and `snippet`. | Dependency debt | `pyproject.toml:11-29`; `frontend/package.json:23,27` | Medium: bloated installs, wider supply-chain surface (see SEC-015) | Move tooling to `[dependency-groups].dev`; drop the stubs and slowapi; `npm uninstall add snippet` | S |
| TD-10 | **Hardcoded or CWD-relative config and import-time wiring; frontend duplication.** DB path relative to the working directory; engine and service built at import, so tests monkeypatch globals; host, port, reload and CORS origin hardcoded. Frontend issues: `TodoForm`/`TodoEditForm` near-copies; 3 copies of the optimistic-update code; the description is always saved as `"not implemented yet"`; Chakra v2 `colorScheme` prop (no effect in v3). | Hardcoded config / duplication | `database.py:26,38-48`; `api.py:25,31`; `main.py:11`; `TodoForm.tsx:51`; `TodoEditForm.tsx:51`; `hooks/queries/*.ts` | Med-High: blocks per-environment config and clean dependency injection | pydantic-settings, FastAPI lifespan plus `Depends`; shared title-field component and query-key factory; `colorPalette` | M |

**Below the cut:**
- The update path skips UUID validation.
- `ErrorBoundary` sits *outside* `ChakraProvider` but renders Chakra components, so its fallback may itself throw (`frontend/src/App.tsx:14-16`; medium confidence, not executed).
- The delete toast fires before the mutation runs (`TodoDeleteButton.tsx:15-20`).
- Explicit `QueuePool` on SQLite is redundant.

## Security Findings

**Scope and method:**
- The working tree and all 210 commits of history were scanned.
- `npm audit` and `pip-audit` ran live against the locked versions.
- ✔ marks items this assessment reproduced independently against a live instance.

**No hardcoded credentials were found in the tree or in git history.** The workflows use runtime-injected `${{ github.token }}` / `${{ secrets.GITHUB_TOKEN }}` only. The SQLite files committed earlier held empty tables. No `SECRETS.local.md` was created.

**Context for severity:** the README says this is a playground "not intended for production". Severities below are rated for that context. Anything deployed as-is moves SEC-001 to High at network scope.

| ID | Sev | CWE | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| SEC-001 | **High** | CWE-306, CWE-862 | **No authentication or authorization on any route.** No users, no ownership; anyone who reaches :8000 can list, edit or delete everything. ✔ `GET /todo?limit=-1` dumps every row. | `backend/app/api/api.py:40-91` | Bearer-token dependency on every route plus a `user_id` column, *if* multi-user is in scope (a decision for `/modernize-brief`) |
| SEC-002 | Medium | CWE-1327, CWE-489 | Uvicorn binds **`0.0.0.0` with `reload=True`**, hardcoded. This exposes SEC-001 to the LAN. The `RELOAD` toggle in `config.py` is dead code. | `backend/app/main.py:11` | Read host and reload from env; default to `127.0.0.1`, reload off |
| SEC-003 | Medium | CWE-352, CWE-346 | **Cross-site write.** FastAPI parses a POST body with no Content-Type as JSON, which makes it a CORS "simple request" with no preflight. ✔ A POST with `Origin: https://evil.example` and no Content-Type returned **200 and created the row**. No `TrustedHostMiddleware`, so DNS rebinding is open. | `backend/app/api/api.py:20-29, 40-50` | Reject anything other than `application/json` with 415; `TrustedHostMiddleware`; auth |
| SEC-004 | Medium | CWE-770 | **Unbounded resources.** ✔ `limit=-1` returns all rows; ✔ a huge `page` gives a 500. `slowapi` is declared but never wired, so there is no rate limiting. No body size cap. | `api.py:88-91`; `repository.py:92-97`; `pyproject.toml:19` | `Query(ge=1, le=100)`; wire the limiter; cap the body |
| SEC-005 | Medium | CWE-250 | The CI workflow grants `contents: write` and `pull-requests: write` at the top level, on push to any branch. The checkout leaves the token in `.git/config` while 71 third-party packages install and run. | `.github/workflows/python-app.yml:5, 9-11` | Top-level `contents: read`; a separate job for the coverage comment; `persist-credentials: false` |
| SEC-006 | Medium | CWE-829 | Third-party actions are pinned to mutable tags, some of which receive tokens: `setup-uv@v5`, `python-coverage-comment-action@v3`, `super-linter@v4` (deprecated), `setup-python@v3`. | `python-app.yml:30,78,92,97,101`; `super-linter.yml:30,34` | Pin to commit SHAs; add Dependabot for `github-actions` |
| SEC-007 | Medium | CWE-1395 | **Dev toolchain CVEs.** ✔ `npm audit`: **35 (1 critical, 24 high, 7 moderate, 3 low)**, all in dev dependencies. The critical is in vitest 4.0.13 (UI server); highs include vite 6.4.1 (dev-server file read) and rollup. Production-only audit: 2 moderate (uuid, yaml), neither reachable. | `frontend/package-lock.json` | `npm audit fix`; upgrade vitest, vite and rollup; fail CI on high |
| SEC-008 | Low | CWE-942 | CORS sets `allow_credentials=True` (no cookies are used) with wildcard methods and headers. The origin itself is pinned correctly. | `api.py:23-29` | Credentials off; explicit methods and headers; origin from config |
| SEC-009 | Low | CWE-20, CWE-1284 | No `max_length` at the API boundary; the only limit is a DB CHECK, which exists only on the DDL mapping. ✔ Misleading 409; null title on PUT gives a 500 (see TD-2). | `create_todo_schema.py:9-11`; `update_todo_schema.py:8-10` | `Field(min_length=1, max_length=255)`; reject explicit null |
| SEC-010 | Low | CWE-117 | Raw user input is logged with `%s`; the agent forged a log line with an embedded newline. | `input_sanitizer.py:38`; `uuid_validator.py:23` | Log `%r` or strip CR/LF, and truncate |
| SEC-011 | Low | CWE-1395 | **Runtime dependency advisories** (pip-audit): starlette 0.46.2 (7 advisories, fixed by 1.3.1), python-multipart 0.0.20 (6, by 0.0.31), anyio 4.9.0 (2), idna 3.10 (1). **Not reachable** with the current routes (no forms, files or static serving). FastAPI 0.115.x caps starlette below 0.47, so this needs a FastAPI uplift. | `uv.lock` | Uplift FastAPI and starlette together; this is the core of an uplift |
| SEC-012 | Low | CWE-532 | An invalid `DATABASE_URL` is echoed in full in the error, and `init_db.py` logs the URL. Harmless with SQLite; it would leak a password once Postgres is configured. | `database.py:33-34`; `scripts/init_db.py:18` | `make_url(...).render_as_string(hide_password=True)` |
| SEC-013 | Low | CWE-459 | Delete is soft and rows are never purged. The client chooses IDs, so re-creating a deleted ID returns 409 while GET returns 404, an existence oracle. | `repository.py:53-68`; `create_todo_schema.py:9` | Server-generated IDs; purge or retention; document the semantics |
| SEC-014 | Low | CWE-732 | The DB path is relative to the working directory, created with umask permissions, and **not covered by `.gitignore`**. DB files were committed before (empty tables). | `database.py:26-32`; `.gitignore:62-63` | Resolve the path from config; `chmod 600`; ignore `*.db` |
| SEC-015 | Low | CWE-1357 | Dev tools ship as runtime dependencies (black, pytest, … with their own advisories); unused `add` and `snippet` npm runtime deps. | `pyproject.toml:12-18`; `frontend/package.json:23,27` | See TD-9 |
| SEC-016 | Info | CWE-184 | **The input sanitizer is security theater.** All SQL is parameterized ORM (no `text()` or `.execute(` anywhere). The blocklist rejects legitimate input and would not stop `1' AND '1'='1` if a raw-SQL sink were ever added. Its docstring claims it prevents SQL injection. | `input_sanitizer.py:1-15` | Remove it; add a lint or test that bans raw SQL |
| SEC-017 | Info | CWE-79 | Stored HTML is accepted verbatim but rendered escaped by React. No `dangerouslySetInnerHTML` or `innerHTML` sinks. Not exploitable today. | `TodoItem.tsx:18` | Encode in any future non-React rendering path; add a CSP |
| SEC-018 | Info | CWE-200 | ✔ `/docs`, `/redoc` and `/openapi.json` are public. | `api.py:20` | Disable outside dev |
| SEC-019 | Info | CWE-755 | Errors do **not** leak internals to clients (generic 500). The status mapping is inconsistent (TD-2). | `api.py:53-59, 88-91` | Global exception handlers |
| SEC-020 | Info | — | `ReactQueryDevtools` is always rendered. It becomes a no-op in production builds. | `frontend/src/App.tsx:21` | Gate on `import.meta.env.DEV` |

**Dependency audit raw counts:**
- `npm audit`: 35 (3 low, 7 moderate, 24 high, 1 critical).
- `npm audit --omit=dev`: 2 moderate.
- `pip-audit`: 40 findings in 9 packages (includes duplicate rows). These come from 8 dev or transitive packages plus starlette.

## Documentation Gaps

Header-comment coverage is **35 of 54 production files (65%)**. The least documented area is `frontend/src/components/**` (11 files without a header). The README covers installation and roadmap only. Top 5 behaviours a new engineer would have to discover from the code:

1. **Validation rules.** Nothing documents what input is rejected:
   - `or`, `select`, `update`, `delete`, `create` and others as whole words, plus `;` and `--`
   - 255-character limits, enforced only by a DB CHECK
   - a client-generated UUID `id` required on create (a create without one gets 422)

   The sanitizer's docstring claims SQL-injection prevention, which it does not provide (SEC-016).
2. **Data lifecycle semantics.**
   - **Soft delete** (`deleted=true`, never purged, re-create gives 409) and **mark as done** (`PUT` with `done:true`, API only, drops other fields) already exist, yet the README lists both as *future* features (`README.md:108-110`).
   - Every todo's description is silently saved as `"not implemented yet"`.
3. **API contract.**
   - 6 routes.
   - The `{success, data, message, error, results, todo_entries}` envelope.
   - `results` is the page size, not a total.
   - Default page size 10, and the UI shows only page 1.
   - Status-code mapping (400/404/409/500), including the wrong 409.

   All of this is only discoverable through `/docs`, which the README doesn't mention.
4. **Runtime configuration and how to run.**
   - `DATABASE_URL` and the default DB path relative to the working directory.
   - `VITE_API_BASE_URL`.
   - CORS pinned to `:5173`.
   - Hardcoded host, port and reload.
   - The README commands are wrong: `python -m app.main` should be `uv run python -m backend.app.main` from the repo root, and `uv run pytest/backend .` should be `uv run pytest backend/tests/`.
5. **Architecture docs are stale or empty.**
   - `documentation/frontend.puml` is **0 bytes**.
   - `documentation/backend.puml` describes a `Webservice` class, a `Status` enum and `ToDo.update()`, none of which exist.
   - `backend/architecture.puml` omits `factory`, validators, builders and decorators.
   - Both PlantUML files have syntax errors (`@@startuml`; a stray line before `@startuml`).
   - Undocumented: the dual table mapping, the logging behaviour, and the optimistic-update cache coupling.

## Relative Scale

| Basis | KSLOC | COCOMO-II index = 2.94 × KSLOC^1.10 |
|---|---:|---:|
| **Production source** (backend app + scripts, frontend src excl. tests) | **1.747** | **5.43** |
| All source including tests (Py, TS/TSX, JS, CSS, HTML, SVG) | 6.262 | 22.12 |
| All counted code excluding lockfiles (adds CI YAML, PlantUML, JSON, TOML, MD) | 7.002 | 25.01 |

Inputs come from `cloc` 2.10 (above), with nominal scale factors. Rank this system against others on the **same basis row**; production source is recommended. For portfolio context, an index around 5 puts basicToDo at the very small end of the scale.

**This is a relative size signal, not a timeline or a cost.** The COCOMO figure assumes traditional human-team productivity curves, which agentic transformation does not follow. It must not be read or converted into how long modernization will take or what it will cost. No person-months, schedule, cost or date is implied.

## Recommended Modernization Pattern

**Refactor (in place, same stack, including a dependency uplift), routed to `/modernize-uplift`.**

The technology is not the problem:
- Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2, React 19 and Vite 6 are all current-generation.
- The architecture is a sensible layered design with low complexity (mean CCN 1.9).
- There is a strong safety net: 433 backend tests, 13 component tests, and 13 e2e tests that pass locally, which enables dual execution.

What needs work is a bounded set of defects and debts that a same-stack refactor fixes cheaply while keeping that safety net.

What makes this an *uplift*, not just cleanup: the most consequential change is version movement. FastAPI 0.115 → current, to release starlette from 0.46.2 (SEC-011); vitest, vite and rollup past their advisories (SEC-007); the data layer from 1.x-era SQLAlchemy idioms to 2.0 `DeclarativeBase`/`Mapped[]` plus Alembic (TD-5). `/modernize-uplift`'s pin-then-migrate-then-prove-equivalence loop fits exactly.

Suggested order for `/modernize-brief`:
1. Characterization tests that pin **current** behaviour, including the defects. Rename the 9 uncollected tests so they run.
2. Dependency uplift with dev tools moved out of runtime (TD-9, SEC-011, SEC-007, SEC-015).
3. Data-layer consolidation (TD-5).
4. Behaviour fixes, each needing an explicit keep-or-fix decision: TD-1 (blocklist), TD-2 (409/500), TD-4 (pagination), TD-6 (done plus rename), the description placeholder.
5. Posture (SEC-002/003/004/005/006) through `/modernize-harden`.

**Why not the alternatives:**
- **Rebuild** (`/modernize-reimagine`) is affordable at 1.7 KSLOC, but it would discard a large, passing test suite in exchange for very little architectural gain.
- **Rearchitect / cross-stack** (`/modernize-transform`) has no driver: nothing in the stack is end-of-life.

**Open decision for the brief:** whether multi-user authentication (SEC-001) is in scope. That turns a refactor into a feature addition, and only the owner can say whether this playground is meant to become multi-user.
