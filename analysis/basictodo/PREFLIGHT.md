# Preflight — `legacy/basictodo`

_Run: 2026-10-03 · Source: branch `legacy` @ `a2d59f1` · Target stack: none passed_

## Check 0 — Human answers (verbatim)

| # | Question | Answer (verbatim) |
|---|---|---|
| 1 | **Scope** — Is `legacy/basictodo` the complete system, or one slice of a larger codebase? If a slice: what outside it depends on code inside it, and is breaking those consumers acceptable? | "Complete system. No external consumers." |
| 2 | **Build & test locally** — Can this environment restore, build, and run the tests? Roughly how long does the full CI pipeline take? | "Python/uv and Node available locally. CI: GitHub Actions, duration: don't know." |
| 3 | **Bespoke build infrastructure** — Is there organization-specific build or dependency-resolution machinery that someone new would not guess? Where is it documented? | "None." |
| 4 | **Prior attempts** — Has anyone tried to modernize any of this before? What went wrong? | "Yes, several manual refactors by the author, visible in the git history." |
| 5 | **Off limits** — Is anything under `legacy/basictodo` not allowed to change in this pass? | "Nothing." |

Open items: none. All five answered. Q2's CI duration is "don't know". The local run below suggests minutes, not hours: the whole pipeline ran in under 1 minute locally with warm caches. That is an inference, not a CI measurement.

## Check 6 — Scope boundary

**Standalone. No crossings in either direction.** This agrees with the answer to Q1.

- `legacy/basictodo` is a real directory, not a symlink, with its own full, non-shallow `.git`. There is no repository, workspace or solution root above it. The parent directories are only the eval harness. The sibling `ws-pdbsearch` is an unrelated workspace with zero references to `basictodo`.
- **Outbound:** none. The only path-sourced package in `uv.lock` is the project itself (`editable = "."`). Every frontend relative import resolves inside `frontend/`. No manifest points outside the tree.
- **Inbound:** none found, and the human confirms there are no external consumers. No transition decisions are needed for `/modernize-brief` or `/modernize-uplift`.

## Status

| Check | Status | Found | Fix |
|---|---|---|---|
| 0 Human answers | ✅ | 5/5 answered (above) | — |
| 1 Stack | ✅ | Python 3.13 FastAPI + SQLAlchemy 2 + Pydantic + SQLite backend, built with uv. TypeScript + React 19 + Chakra UI 3 + TanStack Query frontend, built with Vite 6. Tests: pytest, Vitest 4 and Playwright 1.57. | — |
| 2 Analysis tooling | ⚠️ | `scc`, `cloc`, `lizard`, `glow` and `delta` are **all missing** | install `cloc`, `glow` and `git-delta` with the system package manager, then `uv tool install lizard` (scc is not packaged for the local distribution; cloc covers it) |
| 3a Build definition | ✅ | 6 GitHub Actions workflows. Pins: Python **3.13**, uv **0.7.16**, Node **20**. Dependencies come from public PyPI (71 locked packages) and registry.npmjs.org (697 resolved entries). Nothing bespoke. | — |
| 3b Legacy smoke test | ✅ | **Level 2 passed end to end**, reproducing all CI jobs: backend 433 passed / 1 skipped, coverage 81.78% (gate 80%); frontend typecheck, 13 unit tests and the build pass; **e2e 13/13 passed** | Optional: `uv self update 0.7.16` to match CI exactly |
| 3c Target toolchain | ⚠️ | No `[target-stack]` passed, so not checked | Re-run `/modernize-preflight basictodo <target-stack>` once the target is chosen |
| 4 Source completeness | ✅ | 0 unresolved `backend.*` imports, 0 unresolved frontend relative imports, no binary-only artifacts. Schema comes from the SQLAlchemy models (no DDL or migrations). There are no deployment descriptors, which fits a dev-only app. | — |
| 5a Telemetry | ⚠️ (n/a) | No observability or APM MCP server connected, and no runtime logs. The README says the app is "not intended for production", so production telemetry probably doesn't exist. | None possible. Rely on e2e and characterization traces. |
| 5b Version control | ✅ | 210 commits, 2025-05-31 → 2025-11-29, one human author plus dependabot | Use rename-aware history for churn (see below) |
| 6 Scope boundary | ✅ | Standalone; no inbound or outbound crossings | — |

## Detail

### Check 1 — Stack fingerprint

157 files, excluding `.git`.

| Area | Files | Lines (wc) |
|---|---|---|
| Backend app (`backend/app`, `.py`) | 35 modules | 958 |
| Backend tests (`backend/tests`, `.py`) | 50+ | 6,143 |
| Frontend src, excluding tests (`.ts`/`.tsx`) | ~30 | 1,078 |
| Frontend unit + e2e tests | 9 | 580 |
| CI YAML / PlantUML / CSS | 6 / 3 / 2 | 421 / 190 / 133 |

The test code is about 6× the size of the backend app code. Layering: `api/` → `business_logic/` (service, builders, validators, decorators) → `data_access/` (repository, database) → SQLite. Architecture diagrams exist in `documentation/*.puml` and `backend/architecture.puml`.

### Check 2 — Analysis tooling

| Tool | Status | Used by | Without it |
|---|---|---|---|
| `scc` / `cloc` | ❌ missing | assess | LOC and complexity fall back to `find`+`wc`; the COCOMO index gets coarser |
| `lizard` | ❌ missing | assess --portfolio | Complexity estimated from decision-keyword counts |
| `glow` | ❌ missing | all | Markdown renders as plain text |
| `delta` | ❌ missing | transform | Diffs fall back to `diff -y` |

Install `cloc`, `glow` and `git-delta` with the system package manager (cloc 2.06, glow 2.1.1 and git-delta 0.18.2 are all in the distribution's repositories). For lizard: `uv tool install lizard`.

SAST, relevant to `harden`: `semgrep`, `bandit`, `pip-audit` and `ruff` are missing; `npm audit` is built in. CI runs CodeQL (actions, JS/TS, Python) and dependency-review, but those results live on GitHub, not locally. Install: `uv tool install semgrep && uv tool install bandit && uv tool install pip-audit`.

### Check 3a — Build definition (ground truth)

| Workflow | What it does |
|---|---|
| `python-app.yml` | `uv sync --locked --all-extras --dev` → `python backend/scripts/init_db.py` → `mypy backend/app/` (continue-on-error) → `pytest backend/tests/ --cov-fail-under=80`. A separate Lint job runs `pylint app/*py --exit-zero`, so it never fails. |
| `frontend.yml` | `npm ci` → `tsc --noEmit` → `npm run lint` (continue-on-error) → `npm test` → `npm run build` |
| `e2e.yml` | uv sync + `npm ci` + `npx playwright install --with-deps chromium` → `npm run test:e2e`. Playwright's `webServer` starts the backend (`DATABASE_URL=sqlite:///test.db uv run python -m backend.app.main`, port 8000) and Vite (port 5173). 10-minute timeout. |
| `codeql.yml`, `dependency-review.yml`, `super-linter.yml` | Security and lint gates on `main` |

There is no organization-level config: no `.npmrc`, `pip.conf`, `uv.toml`, `.python-version` or `.nvmrc`. This confirms the answer to Q3.

Toolchain, local vs CI:

| | CI pins | Local | Effect |
|---|---|---|---|
| Python | 3.13 | 3.13.15 (system interpreter); **default `python3` is 3.14.7** | Verified on 3.13 only. Pass `--python 3.13` to uv, or it may pick 3.14 (untested). |
| uv | 0.7.16 | 0.7.15 | `uv sync --locked` succeeded, so the lockfile is compatible |
| Node / npm | 20 | 22.22.2 / 10.9.7 | Every frontend step passes on 22; Node 20 is not installed |
| Playwright Chromium | rev 1200 | rev 1200 cached in `<playwright-cache>` | Works. CI's `--with-deps` uses apt, which is not available locally, but it isn't needed here. |

### Check 3b — Smoke test

All builds ran on a **scratch copy** (`rsync` without `.git`), so `legacy/` was not modified: no `.venv`, `node_modules`, `todo.db` or coverage output was written there.

| Level | Command | Result | Time (warm cache) |
|---|---|---|---|
| 1 | `python3.13 -m py_compile backend/app/business_logic/todo_service.py` | OK | — |
| 2 | `uv sync --locked --all-extras --dev --python 3.13` | OK | 1.4 s |
| 2 | `uv run python backend/scripts/init_db.py` | exit 0; creates the `toDo` table (verified via `sqlite_master`) | — |
| 2 | `uv run mypy backend/app/` | "Success: no issues found in 35 source files" | — |
| 2 | `uv run pytest backend/tests/ --cov=backend/app --cov-fail-under=80` | **433 passed, 1 skipped**, 2 warnings; coverage **81.78%** | 3.8 s |
| 2 | `npm ci` | 650 packages | 4 s |
| 2 | `npx tsc --noEmit` | exit 0 | — |
| 2 | `npm run lint` | 1 error (`e2e/smoke.spec.ts:89` unused `e`); CI ignores it | — |
| 2 | `npx vitest --run` | **13 passed** (5 files) | 2.8 s |
| 2 | `npm run build` | OK; 669 kB JS chunk (size warning only) | 2.6 s |
| 2 | `CI=true npx playwright test` | **13 passed** | 19.4 s |

**Implication:** the legacy system runs fully here, both servers and the browser e2e suite. Dual execution (legacy and modernized side by side, compared over HTTP or the browser) is available for equivalence testing. You don't need to fall back to recorded traces.

Coverage hotspots worth shoring up with characterization tests before transforming: `data_access/repository.py` 54.84%, `data_access/database.py` 75.47%. The 81.78% total sits only 1.78 points above the CI gate.

### Check 4 — Source completeness

- **Unresolved includes / imports:** 0. All `backend.*` Python imports resolve to files. All frontend relative imports resolve. Third-party code comes from the two lockfiles.
- **Deployment / config descriptors:** none (no Dockerfile, compose file or service unit). That is expected for a dev playground. Entry points:
  - Backend: `backend/app/main.py` runs `create_all`, then `uvicorn backend.app.api.api:app` on 0.0.0.0:8000 with `reload=True`.
  - Frontend: Vite on port 5173.
  - Runtime config: env `DATABASE_URL` (accepts the `sqlite://`, `postgresql://` and `mysql://` prefixes), otherwise `backend/todo.db` relative to the working directory. Frontend env `VITE_API_BASE_URL`, otherwise `http://localhost:8000`.
- **Data definitions:** no DDL and no migrations (no Alembic). The schema is defined **twice** in `backend/app/data_access/database.py`. `create_all` builds the DDL from the declarative `ToDoORM` (`Base.metadata`), while reads and writes go through an imperative `to_do_table` mapped onto `ToDoEntryData`. `/modernize-map`'s data lineage should treat both as one table, `toDo`, and watch for drift. Pydantic request/response schemas are in `backend/app/schemas/`.
- **Binary-only artifacts:** none. The 4 PNGs are README screenshots, plus 2 SVG icons.

### Check 5 — Optional context

- **Telemetry:** no APM or observability MCP server is connected. There are no runtime logs in the tree. `/modernize-assess` Step 4's runtime overlay is unavailable. The e2e suite is the best stand-in for observed runtime behavior.
- **Git:** 210 commits over 6 months; branch `legacy`, history not shallow. **Caveat for churn ranking:** the top-churn paths no longer exist under those names, because the author's refactors moved them. Examples: `backend/app/database.py` (16 changes) is now `data_access/database.py`, `backend/app/api.py` / `webservice.py` is now `api/api.py`, and `frontend/src/components/Todos.tsx` was split up. Compute churn with rename detection (`git log -M --follow`), or hotspots will be undercounted. The refactor history the answer to Q4 refers to is mostly 2025-10-25 ("Clean architecture improvement") and 2025-11-23..29 ("first step of refactoring", "split components", "Add React query and refactoring").

## Verdict per command

| Command | Verdict | Why |
|---|---|---|
| `assess` + `map` + `extract-rules` | **Ready with gaps** | Stack is clear and nothing is missing from the source. The gap is Check 2: no `cloc`/`scc`/`lizard`, so metrics use `find`+`wc` and keyword counts. A single install command fixes it. |
| `brief` | **Ready** (after discovery) | Needs no tooling. It needs the assess, map and extract-rules artifacts, which don't exist yet. Check 0 and Check 6 inputs are complete. |
| `transform` + `reimagine` | **Ready with gaps** | The legacy side is fully green, including e2e, so **dual execution** is possible. The target toolchain is unverified because no target was passed. Re-run preflight with the target stack. |
| `harden` | **Ready with gaps** | No local SAST (`semgrep`, `bandit`, `pip-audit`). `npm audit` is available. CI's CodeQL results are on GitHub only. |
| `uplift` | **Ready with gaps** | No target version passed. Source runtimes are present: Python 3.13 and Node 22 (CI uses 20). Python 3.14.7 is also installed, so a 3.13 → 3.14 bump could **dual-run today**. A Node 20 → 22+ bump would compare against Node 22 only, unless Node 20 is installed. No migration tooling is installed (`pyupgrade`, `ruff`, `npm-check-updates`), so the delta catalog would come entirely from Claude. There are no inbound consumers, so no shared-node decisions are needed. |

## Noticed in passing (not blockers, for downstream commands)

1. **The sanitizer rejects ordinary words.** In the e2e run, the server logged `SQL injection attempt detected: Todo to delete` → `Validation error: Invalid characters or SQL keywords in input: 'Todo to delete'`. A legitimate title containing "delete" is rejected, and the e2e test still passes. `/modernize-extract-rules` should capture this as current behavior; `/modernize-brief` should decide whether it is a rule or a bug.
2. **`backend/app/config.py` is dead and broken.** It reads `self.config_file` before setting it, nothing imports it, and its coverage is 0%. `backend/config_dummy.json` is its only companion.
3. **Logging partly goes nowhere.** `CustomLogger` subclasses `Logger` but attaches its handler to a different `getLogger(name)` instance. Calls like `logger.info()` on the `CustomLogger` object therefore have no handler. INFO is dropped, and WARNING+ reaches stderr unformatted through Python's last-resort handler. For example, `init_db.py` runs silently. Recorded traces that rely on logs will miss INFO events.
4. **The README commands are stale.** It says `python -m app.main`; the real command is `uv run python -m backend.app.main` from the repo root. It also says `uv run pytest/backend .`; the real command is `uv run pytest backend/tests/`. The CI workflows above are the correct reference.
5. **`backend/backend/tests/**`** holds 9 empty `__init__.py` files, a stray copy of the tests package layout. It's harmless but will show up in inventories.
