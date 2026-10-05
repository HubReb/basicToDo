# Delta Catalog: basicToDo same-stack uplift

_System: `legacy/basictodo` · Built 2026-10-03 for `/modernize-brief` by the version-delta-analyst agent · Consumed by `/modernize-uplift` Step 3 (reused if newer than the brief inputs)_

**Version pair:**
- **Source:** Python 3.13 · FastAPI 0.115.12 / Starlette 0.46.2 · SQLAlchemy 2.0.43 · pytest 8.4 · Node 20 (CI) · Vite 6.4 · Vitest 4.0 · TypeScript 5.8
- **Target:** Python 3.13 · FastAPI 0.142.2 / Starlette 1.7.0 · SQLAlchemy 2.0.54 (2.1 optional, later) · pytest 9.1 · Node 24 or 22 (decision in the brief §7) · Vite 8.3 · Vitest 5.0 · TypeScript 6.0

**Method:** empirical. The analyst upgraded a throwaway copy of the system, ran every CI gate on source and target, and diffed 60 characterization requests plus the OpenAPI document between the two stacks. Nothing under `legacy/` was modified.

**Re-verified in this session:** the resolved versions, plus three results on the target:
- **Backend:** 433 passed / 1 skipped, coverage 81.62% with `DATABASE_URL` set (the same as legacy).
- **Frontend:** `tsc -b` clean, vitest 13/13, build OK, `npm audit` 0.
- **The 9 uncollected `tests_*.py` builder tests:** pass on both stacks.

The probe copy lives at `<scratchpad>/uplift-probe/` and the evidence files at `<scratchpad>/uplift-probe-envs/`. Both are session scratch and not durable.

## A. Versions

### Backend (resolved by `uv lock --upgrade`)

| Component | Source | Target | Note |
|---|---|---|---|
| Python | 3.13 | **3.13** (3.14.7 also green) | 3.13 is security-only now (EOL 2029-10); 3.14 EOL 2030-10. The local default `python3` is already 3.14. |
| uv | 0.7.16 (CI pin) | 0.7.16 works; latest 0.12.22 | `uv lock --check` passes on both against the new lock |
| fastapi[standard] | 0.115.12 | **0.142.2** | 0.133.0 is the first release that allows Starlette 1.x. 0.142 adds native OpenTelemetry (D-09). |
| starlette | 0.46.2 | **1.7.0** | Clears 7 advisories (fix floor 1.3.1) |
| pydantic / core | 2.11.5 / 2.33.2 | 2.13.5 / 2.46.5 | |
| sqlalchemy | 2.0.43 | **2.0.54** now; 2.1.3 is GA but blocked by sqlalchemy-utils (D-03) | 2.1 drops greenlet as a default dependency and removes `sqlalchemy.ext.mypy` |
| sqlalchemy-utils | 0.42.0 | 0.42.1 | Fails to import under SA 2.1 (upstream #829 / PR #831 still open) |
| uvicorn | 0.34.3 | 0.54.0 | |
| pytest / pytest-asyncio / pytest-cov | 8.4.2 / 1.2.0 / 7.0.0 | **9.1.1** / 1.4.0 / 7.1.0 | |
| python-multipart / anyio | 0.0.20 / 4.9.0 | 0.0.32 / 4.15.1 | Advisory fixes |
| mypy / pylint / black | 1.17.1 / 3.3.8 / 25.1.0 | 2.4.0 / 4.1.2 / 26.5.1 | |
| sqlalchemy-stubs / sqlalchemy2-stubs | 0.4 / 0.0.2a38 | (none newer) | Obsolete; they overwrite each other (D-04) |
| httpx (+ httpx2) | 0.28.1 | 0.28.1 + **httpx2 2.13.1** for TestClient | D-06 |
| **pip-audit** | **22 advisories / 9 packages** | **0** | |

### Frontend

| Component | Source | Target | Note |
|---|---|---|---|
| Node (CI) | 20 (**EOL 2026-04-30**) | 24 ≥24.15 **or** 22 ≥22.22.2 | Even a same-major refresh excludes Node 20 (D-15) |
| vite / @vitejs/plugin-react | 6.4.1 / 4.7.0 | **8.3.2 / 6.1.1** (same-major alternative: vite 6.4.3) | Vite 8 uses Rolldown and Lightning CSS; rollup and esbuild leave the tree |
| vitest | 4.0.13 | **5.0.3** (4.1.11 also works) | Engines: Node ^22.12, ^24 or ≥26 |
| typescript | 5.8.3 | **6.0.3** | TS 7.0.2 is blocked by typescript-eslint (D-22) |
| typescript-eslint / eslint | 8.46.2 / 9.38.0 | 8.71.0 / 10.12.0 | |
| react / react-dom | 19.2.0 | 19.3.0 | |
| @chakra-ui/react | 3.28.0 | 3.37.0 | |
| @tanstack/react-query | 5.90.10 | 5.104.1 | |
| @playwright/test | 1.57.0 (chromium-1200) | 1.63.0 (needs chromium-1243) | Browser not cached locally (D-23) |
| jsdom / jest-dom | 27.2.0 / 6.9.1 | 30.1.1 / 7.0.1 | jest-dom ≥6.10 already requires Node ≥22 |
| vite-tsconfig-paths | 5.1.4 | 6.1.1, or remove it (Vite 8 has native `resolve.tsconfigPaths`) | |
| **npm audit** | **35 (1 critical, 24 high)** | **0**, already with the same-major refresh "F1" | |

### GitHub Actions

| Action | Now | Target | Note |
|---|---|---|---|
| actions/checkout | v4 | v7.0.1 | node24 |
| actions/setup-python | v5 and **v3** (python-app.yml:101) | v7.0.0 | |
| actions/setup-node | v4 | v7.0.0 | |
| actions/upload-artifact | v4 | v7.0.1 | |
| astral-sh/setup-uv | v5 | **v10.2.0** | No floating `@vN` tags since v8 (D-26) |
| py-cov-action/python-coverage-comment-action | v3 | **v4.5** | No `@v4` tag exists |
| github/super-linter | v4 | **super-linter/super-linter v9.0.0** | Moved to a new organisation (D-27) |
| github/codeql-action | v3 | v4 | |
| actions/dependency-review-action | v4 | v5.0.0 | |

## B. Test-harness verdict: can the existing suites run on the target?

| Suite | Source | Target, suite unchanged |
|---|---|---|
| pytest, Py 3.13 + SA 2.0.54 | 433 passed / 1 skipped / 81.78% | **433 / 1 / 81.78%, identical** (1 new StarletteDeprecationWarning, D-06) |
| pytest, Py 3.14.7 | — | 433 / 1 / **81.40%** (D-07, D-08) |
| pytest, SA 2.1.3 | — | **0 collected** (import error in product code, D-03). With the D-03b fix: 433 / 1. |
| mypy gate (non-blocking) | already red: 3 errors | 4 errors (5 once the stubs are removed). All mechanical (D-04, D-05). **Pilot correction:** the count is install-order dependent (D-04). On the same tree and target lock, two fresh venvs gave 5 and 3 errors. |
| vitest | 13/13 | **13/13** on Vitest 4.1.11 and on 5.0.3. Test-file *types* break the build on Vitest 5 until D-18 lands. |
| Playwright e2e | 13/13 (runner 1.57) | **13/13** on runner 1.57 against the fully upgraded app. Runner 1.63 was not run (browser not cached). |

**Verdict: the test-framework migration is NOT its own Phase 1 (override 1 does not trigger).** The suites run on the target. Three small changes make them clean:
- **D-17:** frontend tsconfig `baseUrl`.
- **D-18:** frontend jest-dom import.
- **D-06:** backend `httpx2`.

All three are backward-compatible: D-17 and D-18 were verified on the legacy dependencies, D-06 on the target. They land as a prerequisite step inside their unit's phase.

**Pilot correction for D-06:** it is compatible with the code but **not lock-neutral**. On the legacy lock, `httpx2` 2.13 raises anyio and idna. It therefore lands with C1, not as a prerequisite.

## C. Deltas that touch this code

| ID | Area | Upstream change | Evidence here | Severity | Coordinated cut | Fix |
|---|---|---|---|---|---|---|
| D-01 | BE deps | Starlette security fixes need Starlette 1.x; FastAPI 0.115 caps <0.47 | `pyproject.toml:14`; 7 Starlette advisories | security | **Yes**: fastapi + starlette in one lock bump; no code change | `fastapi[standard]>=0.142.2`, `starlette>=1.3.1`. Verified 433/1. |
| D-02 | BE deps | Transitive advisories | multipart (6), anyio (2), black (2), pytest, click, idna, pygments, python-dotenv | security | No | Floors `python-multipart>=0.0.31`, `anyio>=4.14.2`, `pytest>=9.0.3` → 22 advisories go to 0 |
| D-03 | BE deps | SA 2.1 privatised `ScalarAttributeImpl`; sqlalchemy-utils subclasses it at import | `database.py:13` (UUIDType, used at :71, :92) | breaking (SA 2.1 only) | Inside one file | (a) cap `sqlalchemy<2.1` (verified), or **(b)** use `sqlalchemy.Uuid()` and drop sqlalchemy-utils. (b) was verified on SA 2.0.43 and 2.1.3, Py 3.13 and 3.14. Storage is identical (`CHAR(32)` hex) and reads work in both directions (SQLite only). |
| D-04 | BE tooling | sqlalchemy-stubs and sqlalchemy2-stubs install into the same directory and shadow SA 2.x's inline types | `pyproject.toml:20-23`; `registry` attr-defined at `database.py:10` | tooling | With D-03b | Remove both stub packages and the `[mypy]` extra. **Pilot finding:** both packages own `sqlalchemy-stubs/orm/__init__.pyi` (both RECORDs list it), so the one installed last wins. Which one that is varies between fresh `uv sync` runs, and so does the mypy result: `database.py:10` and `main.py:10` come and go. mypy is not a stable gate until this is fixed. |
| D-05 | BE tooling | mypy 2.x: instance-only attribute on class object | `repository.py:73, :89`; stale ignores `database.py:52`, `main.py:10`, `models/todo.py:5` | tooling (gate is non-blocking) | No | Mechanical ignores / cleanup |
| D-06 | Test harness | Starlette 1.7 TestClient prefers `httpx2`; with plain httpx it warns (a UserWarning subclass) | `tests/test_api/test_setup_for_api_endpoins.py:6, :22` | deprecation | No | Add the `httpx2` dev dependency (verified, zero warnings). **Pilot finding:** not lock-neutral on the legacy lock (anyio 4.9.0 → 4.14.2, idna 3.10 → 3.20, sniffio dropped), so it belongs in C1. |
| D-07 | Py 3.14 | `asyncio.iscoroutinefunction` deprecated (removal in 3.16) | `business_logic/decorators.py:2, :53` | deprecation | No | `inspect.iscoroutinefunction` (verified on 3.14 with deprecation warnings as errors) |
| D-08 | Py 3.14 | Lazy annotations change which lines coverage counts | coverage 81.78% → 81.40% (gate 80%) | measurement | No | None. Note the shrinking margin. |
| D-09 | BE behaviour | FastAPI 0.142 ships native OpenTelemetry; `[standard]` grows from 71 to 92 pins | `api.py:20`. Dormant by default; **setting `OTEL_EXPORTER_OTLP_ENDPOINT` alone starts span export.** | behavioural (env-dependent) | No | Keep legacy behaviour: `FastAPI(..., telemetry={"auto_configure": False})`, or pin `<0.142`. Brief §7. |
| D-10 | BE behaviour | Starlette 1.x CORSMiddleware | `api.py:23-29`: `Vary: Origin` on every response; preflight `Allow-Methods` adds `QUERY`; preflight `Vary` expanded | behavioural | No | None (e2e green). Re-baseline the header snapshots. |
| D-11 | BE behaviour | pydantic-core shortened the `uuid_parsing` message | body `id` (`create_todo_schema.py:9`); path `todo_id` (`api.py:54, 63, 76`). `msg`/`ctx.error` shorter; `type`/`loc`/`input` unchanged. | behavioural | No | None. Re-baseline the 422 bodies. |
| D-12 | BE behaviour | OpenAPI `ValidationError` gains `ctx` and `input` | `/openapi.json` diff (8 lines) | docs | No | None |
| D-13 | BE deprecation | `sqlalchemy.ext.declarative.declarative_base` (MovedIn20Warning; still present in 2.1.3) | `database.py:9, :17` | deprecation | No | `sqlalchemy.orm` import, or move to `DeclarativeBase` (Phase 4) |
| D-14 | BE deprecation | Pydantic class-based `Config` (removal planned for V3) | `schemas/data_schemes/todo_schema.py:27` | deprecation | No | `model_config = ConfigDict(...)`. This is the only reason `-W error` fails collection. |
| D-15 | FE / CI | Engine floors exclude Node 20, even for the same-major refresh | `frontend.yml:24`, `e2e.yml:39` | **breaking (CI)** | **Yes**: the Node bump precedes or accompanies any frontend lock change | `node-version` 24 or 22 in both workflows |
| D-16 | FE tooling | npm major ↔ lockfile coupling | npm 10 crashed on the F1 set; an npm-11-made F2 lock fails `npm ci` on npm 10 (`Missing: typescript@5.9.3`, via vite-tsconfig-paths 6 → tsconfck) | **breaking (CI install)** | With D-15 | Generate the lock with the npm major the CI Node ships (Node 24 → npm 11 everywhere), or remove vite-tsconfig-paths |
| D-17 | FE build | TS 6.0 errors on `baseUrl` (TS5101) | `tsconfig.app.json:20` → `tsc -b` exits 2, so **`npm run build` fails** | **breaking** | With the TS bump | Delete `baseUrl`; `"@/*": ["./src/*"]`. Verified on TS 5.8/6.0/7.0. Can land first. |
| D-18 | FE test types | Vitest 5 removed the global `jest.Matchers` bridge | `src/test/setup.ts:1` → 15× TS2339 `toBeInTheDocument`; build fails (runtime still 13/13) | **breaking (build)** | With Vitest 5 | `import '@testing-library/jest-dom/vitest'`. Verified on legacy deps. Can land first. |
| D-19 | FE build | Vite 8: Rolldown plus Lightning CSS; plugin-react 6 needs vite ^8 | Build green. JS 669 → 563 KB. Lightning CSS rewrites `index.css` (lowers `color-scheme: light dark` at :6, reorders declarations, `transparent` → `#0000`). | behavioural (CSS); breaking if the pair is split | **Yes**: vite 8 + plugin-react 6 together | Bump together; optionally native `resolve.tsconfigPaths` |
| D-20 | FE security | rollup ≥4.58 (path traversal) | Baseline 4.52.5 | security | No | Met on a Vite 6/7 path; moot on Vite 8 (no rollup) |
| D-21 | FE security | npm advisories | 35 at baseline (includes `@modelcontextprotocol/sdk` via the **unused** `textlint`) | security | No | Same-major refresh F1 → 0; F2 → 0 |
| D-22 | FE tooling | typescript-eslint 8.71 has peer `typescript <6.1` | ESLint crashes under TS 7 | breaking (TS 7 only) | Yes | Target TS 6.0.3; defer TS 7 |
| D-23 | FE e2e | Playwright 1.63 needs chromium-1243 | Only chromium-1200 is cached locally; CI installs its own | gap (local) | No | Download the browser for local validation |
| D-24 | FE UI | Chakra 3.29–3.37: outline-variant border token changed | `TodoEditForm.tsx:105`; `lib/toaster.ts:3` still type-compatible | behavioural (visual) | No | Visual re-baseline |
| D-25 | CI | node16/node20 actions → node24 majors | All `uses:` lines; `setup-python@v3` at `python-app.yml:101` | deprecation | No | Bump per §A |
| D-26 | CI | Immutable tags (no `@v10` for setup-uv, no `@v4` for coverage-comment) | `python-app.yml:30, 78, 92, 97`; `e2e.yml:28` | **breaking if bumped naively** | No | Pin exact versions or SHAs. setup-uv v6–v10 changed cache and activation defaults; the workflows set `enable-cache: true` explicitly. |
| D-27 | CI | super-linter v4 → v9: `*_STANDARD` linters removed; many more linters enabled by default | `super-linter.yml:30` + env | breaking-likely **(inferred)** | No | `super-linter/super-linter@v9.0.0`; drop the removed env vars; expect new findings |
| D-28 | BE behaviour | FastAPI 0.115 → 0.142 changed its built-in docs pages: Swagger UI HTML gains `<meta name="viewport" content="width=device-width, initial-scale=1.0">`; ReDoc loads `redoc@2` instead of `redoc@next` from the CDN | `/docs` and `/redoc` (FastAPI defaults; the app does not customize them). **Found by the Phase 1 golden master**, not by the catalog run. | behavioural (docs UI only; the API is unchanged) | With C1 | None. Re-baseline the two pages. `redoc@2` pins a major instead of the moving pre-release tag. Decided by the owner on 2026-10-05: classify, do not reproduce the legacy HTML. |

**Checked, not applicable:**
- **SQLAlchemy 2.1:** autoflush change, greenlet, mypy plugin, mapped-dataclass defaults, legacy Query API.
- **FastAPI:** `on_event`, `regex=`/`example=`, `@app.route`.
- **Pydantic v1 idioms:** none present.
- **Chakra v2 props:** none present. The 4 existing `colorScheme=` props are already a no-op on v3 and stay unchanged.
- **React 19 removals; Vite `rollupOptions`/babel; the uuid v3/v5/v6 advisory** (only v4 is used).
- **pytest 9 config, pytest-asyncio strict mode, uvicorn `reload=True`.**
- **ESLint 10 / react-hooks 7:** lint output identical.
- **Pydantic lax bool coercion for `done`:** unchanged on the target.

## D. Behavioural deltas (tests pass, observable output changes)

1. **CORS headers (D-10):** `Vary: Origin` on every response; preflight adds `QUERY` and an expanded `Vary`.
2. **422 bodies (D-11):** shorter `uuid_parsing` message text (333 → 195 bytes for a bad body id).
3. **OpenAPI (D-12):** `ValidationError` gains `ctx` and `input`.
4. **Telemetry (D-09):** span export auto-activates if `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
5. **Coverage accounting on Python 3.14 (D-08).**
6. **Shipped CSS (D-19) and the Chakra outline border (D-24):** visual only; **not yet visually verified.**
7. **Docs pages (D-28):** `/docs` gains a viewport meta tag; `/redoc` loads `redoc@2` instead of `redoc@next`. Found by the Phase 1 golden master.

**Unchanged** (60-request characterization diff): every status code, every success body, `done` coercion, the 404/405/409/400 bodies, the 307 trailing-slash redirect, and the disallowed-origin 400. Two quirks are identical on both stacks and belong in the baseline:
- `PUT {"done": null}` returns **500**.
- The e2e test "should delete a todo" posts "Todo to delete", which the keyword blocklist rejects with 400, yet the test passes.

## E. Ordering constraints (order and dependency only, no durations)

- **Prerequisites (backward-compatible, can land before any bump):**
  - **P-BE:** D-07 (`inspect.iscoroutinefunction`). D-06 (`httpx2`) moved into C1, because it changes the legacy lock (pilot finding).
  - **P-FE:** D-17 (tsconfig), D-18 (`setup.ts`).
  - **P-BE, SA 2.1 path only:** D-03b + D-04.
  - **P-CI:** D-15. The Node bump precedes or accompanies *any* frontend lock change.
- **Coordinated cuts:**
  - **C1 (backend, one lock bump):** fastapi + starlette + floors. No source change; independent of the frontend.
  - **C2 (frontend):** vite 8 + plugin-react 6 together; Vitest 5 / jsdom 30 / jest-dom 7 after the Node bump and P-FE; TS 6 after D-17. TS 7 is deferred.
  - **C3 (optional, later):** SQLAlchemy 2.1, gated on D-03b.
  - **C4 (CI):** action majors with exact-version pins. Independent of code, **except** that `e2e.yml`'s Node version moves with the frontend lock (D-16).
- **Independent units:** backend, frontend and CI. Within the frontend, **F1** (same-major refresh) clears all 35 advisories with zero code change and depends only on the Node bump. It is a natural checkpoint before the F2 majors.
- **Python 3.14:** a separate optional step. Its only code delta is D-07.
- **Node 22 vs 24:**
  - **Node 22:** EOL 2027-04-30; ships npm 10 (D-16 applies); **fully validated here**.
  - **Node 24:** EOL 2028-04-30; ships npm 11; **not installed locally**, so its first real validation would be CI unless it is installed first.
  - Node 26 becomes LTS on 2026-10-28.

## F. Confidence & gaps

- **Verified by running:** all test counts, coverage, mypy and init_db results (Py 3.13/3.14 × SA 2.0.54/2.1.3); pip-audit 22 → 0; npm audit 35 → 0; the characterization and OpenAPI diffs; UUID storage round-trip (SQLite); engines scans; npm 10 vs 11 lock behaviour; the TS 6/7 probes; the Vitest 5 type-bridge root cause; e2e 13/13 on runner 1.57; telemetry activation; `uv lock --check`.
- **Inferred or not run:**
  - the Playwright 1.63 runner;
  - the Node 24 runtime;
  - GitHub Actions behaviour (D-25 to D-27, from release notes and `action.yml` only);
  - UUID equivalence on PostgreSQL/MySQL;
  - visual equivalence after Lightning CSS and Chakra 3.37.
- **Migration tooling that actually ran:**
  - **ruff 0.16** (UP, FAST, ASYNC, B, DTZ; report-only): 51 optional idiom findings, none a removed API. It did not catch D-07; the 3.14 runtime did.
  - **pyupgrade `--py313-plus`:** cosmetic rewrites only.
  - No OpenRewrite or `ng update` equivalent exists for this stack.
- **Existing gate holes (not deltas, but they shape validation):**
  - `npx tsc --noEmit` in CI checks **0 files** (`tsconfig.json` has `"files": []`). The real type gate is `tsc -b` inside `npm run build`.
  - mypy and ESLint are `continue-on-error`, and pylint runs with `--exit-zero`.
  - `python_files = "test_*.py"` skips the two `tests_*.py` builder files (9 tests, which pass on both stacks).

## G. Pilot findings (Phase 1, 2026-10-05)

The backend pilot surfaced the following. The rows above carry the corrections; this section is the summary.

| # | Finding | Effect |
|---|---|---|
| 1 | **D-28 (new):** FastAPI's own `/docs` (viewport meta tag) and `/redoc` (`redoc@2` instead of `redoc@next`) pages change. The catalog run had compared only the `/docs` status. | The owner classified it as a delta and extended the Phase 1 exit criterion. |
| 2 | **D-06 is not lock-neutral:** `httpx2` raises anyio and idna on the legacy lock. | Moved from the prerequisites into C1. |
| 3 | **D-04 makes mypy nondeterministic:** the two stub packages overwrite one shared file, and install order decides the winner. | The mypy count is not a stable comparison or gate before Phase 4. This affects Q9 (mypy blocking in Phase 3); see the brief. |
| 4 | **The test count grows:** 442 → 454 with the P0 contract tests (brief §5) → 456 with the D-09 telemetry tests. | Exit criteria compare per test against `BASELINE.md`, not against the old count. |
| 5 | **Environment facts:** | See `PLAYBOOK.md`. |
|   | - `python3` is 3.14 locally and `.python-version` is gitignored, so uv needs `UV_PYTHON=3.13`. | |
|   | - `uv sync` puts an editable install of the checkout into the venv. A script run (`backend/scripts/init_db.py`) from another worktree would then import `backend.app` from that checkout. | |
|   | - `uv export` writes ANSI codes into its header unless `--color never` is set. | |
|   | - `backend/todo.db`, `test.db`, `frontend/playwright-report/` and `frontend/test-results/` are not gitignored. | |

