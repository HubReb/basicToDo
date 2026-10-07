# Uplift notes: basicToDo, Phase 1 (backend pilot)

**Uplift:** `py3.13 + fastapi 0.115.12 + starlette 0.46.2 + sqlalchemy 2.0.43` → `py3.13 + fastapi 0.142.2 + starlette 1.7.0 + sqlalchemy 2.0.54`

**Branch:** `plugin/uplift-basictodo/phase-1`, based on `plugin/uplift-basictodo/base`.

**Plan:** `analysis/basictodo/MODERNIZATION_BRIEF.md` §3 Phase 1. The evidence is in `analysis/basictodo/BASELINE.md`, the recipe in `analysis/basictodo/PLAYBOOK.md`.

**Proof type: true dual-run.** Both lockfiles install and run on this machine (Python 3.13.15). The same pytest suite and the same 83-request HTTP golden master ran against a legacy-lock venv and a target-lock venv.

## Commits and delta → fix mapping

| Commit | Change | Deltas | How applied |
|---|---|---|---|
| `61d37da` | Rename the two `tests_*.py` builder modules so pytest collects them (+9 tests) | harness repair | by hand |
| `72cf484` | P0 contract tests for RULE-008 and RULE-031 against the real stack (+12 tests) | brief §5 | by hand |
| `ddad5ec` | Move the dev tools to `[dependency-groups].dev`. No version change. The runtime set drops from 69 to 44 packages, and runtime advisories from 22 to 19 (black and pytest leave the runtime). | TD-9, SEC-015 | by hand + `uv lock` |
| `2713c3c` | `inspect.iscoroutinefunction` instead of `asyncio.iscoroutinefunction` | D-07 | by hand |
| `0df26b9` | fastapi / starlette bump with advisory floors and the SQLAlchemy `<2.1` cap; `httpx2` (dev); `telemetry={"auto_configure": False}` plus a test proving that nothing is exported | D-01, D-02, Q4, D-06, D-09 | `uv lock --upgrade` + by hand |

**No ecosystem codemod was needed.** The Python version does not change. pyupgrade and ruff had already been run for the delta catalog and found only optional idioms.

## Dual-run result

| Measure | Legacy lock | Target lock |
|---|---|---|
| pytest | 454 passed / 1 skipped | 456 passed / 1 skipped (all 455 legacy tests keep their result; +2 telemetry tests) |
| Coverage | 83.96% | 83.96% |
| Golden master (83 requests) | baseline | 79 differ, **all classified**: D-10 (CORS `vary`, `QUERY` in preflight), D-11 (shorter `uuid_parsing` text), D-12 (OpenAPI `ctx`/`input`), D-28 (`/docs` viewport tag, `/redoc` on `redoc@2`) |
| Status codes, success bodies, timestamp clocks | — | unchanged |
| P0 contract tests | 12/12 | 12/12 |
| Playwright e2e | 13/13 | 13/13 |
| `pip-audit`, runtime dependencies | 19 advisories in 7 packages (after `ddad5ec`, 44 pins) | 0 (63 pins) |
| mypy (non-blocking) | 3 errors | 3 or 5 errors, depending on install order (D-04) |

**Neutrality of the non-bump commits:** the tree after `2713c3c` on the legacy lock reproduces the untouched baseline (`72cf484`) with 0 golden-master differences and 0 per-test differences. Every difference above therefore comes from `0df26b9`.

## Runtime advisories, step by step

`pip-audit` over the runtime dependencies only (`uv export --frozen --no-dev`), with unique advisory IDs:

| Commit | Runtime pins | Advisories | What changed |
|---|---|---|---|
| `72cf484` (legacy manifest) | 69, dev tools included | 22 in 9 packages | — |
| `ddad5ec` (dev tools moved out) | 44 | 19 in 7 packages | black (2) and pytest (1) leave the runtime: −3 |
| `0df26b9` (C1 bump) | 63 | **0** | anyio, click, idna, pygments, python-dotenv, python-multipart, starlette: −19 |

The "22 → 0" in the delta catalog compares the full legacy runtime set with the target. Of the 22, the hygiene commit removes 3 and the bump removes 19.

## Runtime footprint grows: 44 → 63 pins

**All 20 added packages come in through `fastapi[standard]` 0.142** (+20, −1: `sniffio` drops with anyio 4.14). Each was traced with `uv tree --invert`:

| Group | Packages | Path |
|---|---|---|
| OpenTelemetry (10) | `opentelemetry-sdk`, `-api`, `-proto`, `-semantic-conventions`, `-exporter-otlp-proto-http`, `-exporter-otlp-proto-common`, `-exporter-otlp-common`, `-exporter-http-transport`, `protobuf`, `googleapis-common-protos` | `fastapi[standard]` → `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http` |
| FastAPI Cloud CLI (6) | `fastapi-cloud-cli`, `sentry-sdk`, `urllib3`, `agent-detector`, `detect-installer`, `rignore` | `fastapi[standard]` → `fastapi-cli[standard]` → `fastapi-cloud-cli` |
| Other `[standard]` extras (3) | `fastar`, `pydantic-settings`, `pydantic-extra-types` | `fastapi[standard]` directly |
| FastAPI core (1) | `annotated-doc` | `fastapi` |

**The OpenTelemetry SDK and OTLP exporter are installed but switched off.** `telemetry={"auto_configure": False}` stops FastAPI from wiring them up, and `test_telemetry_export.py` proves that nothing is exported. The packages are still part of every runtime install, and so is `sentry-sdk`, which the Cloud CLI pulls in.

Trimming them would mean replacing `fastapi[standard]` with `fastapi` plus an explicit list of what the app actually needs. That is a manifest decision beyond the minimal uplift, so it was **not done** in this phase.

## Residual manual deltas (not handled in this phase)

- **D-04:** the two SQLAlchemy stub packages overwrite each other, which makes mypy nondeterministic. Phase 4 removes them, together with D-03b.
- **D-05:** two mypy 2.x errors in `repository.py` (`:73`, `:89`). The gate is non-blocking; this is mechanical work for Phase 3 or 4.
- The two remaining pytest warnings (pydantic class-based `config`, `declarative_base()` moved) are pre-existing deprecations. Phase 4 owns the data layer.

## Deferred modernization (kept out to keep the diff minimal)

- `slowapi` removal (Q8a, Phase 5);
- SQLAlchemy 2.1 and the `sqlalchemy.Uuid` swap (Q4, Phase 4);
- Python 3.14 (Q5);
- the frontend and CI uplifts (Phases 2 and 3);
- every Q6 behaviour fix, including the `PUT {"done": null}` → 500 quirk and the keyword blocklist that rejects "Todo to delete" (Phase 5);
- `backend/app/config.py` (dead code), the stray `backend/backend/` directory, and the README commands.

## Per unit

| Unit | Builds on target | Baseline reproduced |
|---|---|---|
| backend (`backend/`, `pyproject.toml`, `uv.lock`) | yes | yes: every difference classified (D-10, D-11, D-12, D-28) |

## Playbook

`analysis/basictodo/PLAYBOOK.md`, section "Backend", holds the ordered recipe, the environment facts and the error table from this pilot. Its gaps are the findings in `DELTA_CATALOG.md` §G.

---

# Uplift notes: basicToDo, Phase 2 (frontend)

**Uplift:** `node20/22 + vite 6.4 + vitest 4.0 + ts 5.8 + chakra 3.28 + playwright 1.57` → `node24 + vite 8.3 + vitest 5.0 + ts 6.0 + chakra 3.37 + playwright 1.63`

**Branch:** `plugin/uplift-basictodo/phase-2`, based on `phase-1`.

**Evidence:** `analysis/basictodo/BASELINE.md` ("Frontend") and `analysis/basictodo/baseline/frontend/`.

**Proof type:** dual run on Node 22 and Node 24 for F0, then per-checkpoint comparisons on Node 24. CI's legacy Node 20 is not available locally, so the legacy oracle is Node 22.

## Commits and delta → fix mapping

| Commit | Change | Deltas | How applied |
|---|---|---|---|
| `2dba37a` | tsconfig `baseUrl` dropped, alias `./src/*`; `@testing-library/jest-dom/vitest` | D-17, D-18 | by hand, on legacy deps |
| `d1709cb` | `node-version: '24'` in `frontend.yml` and `e2e.yml` | D-15 | by hand |
| `21a7337` | **F1:** removes `add`, `snippet`, `textlint` and `framer-motion`; same-major refresh of all lock entries except Chakra's subtree; lock made by npm 11 | D-16, D-20, D-21 | `npm uninstall`, `npm update` |
| `e0fc04c` | **F2:** vite 8.3.2 + plugin-react 6.1.2; vitest 5.0.3 + jsdom 30.1.2 + jest-dom 7.0.1; typescript 6.0.3; Chakra 3.37.0; Playwright 1.63.0; vite-tsconfig-paths 6.1.1 | C2: D-16, D-19, D-22, D-23, D-24 | `npm install` |

## Result

| Measure | F0 (legacy) | F1 | F2 |
|---|---|---|---|
| vitest | 13/13 | 13/13, identical per test | 13/13, identical per test |
| Playwright e2e | 13/13 (1.57) | 13/13 (1.57) | 13/13 (**1.63**) |
| Build: JS / CSS | 669.36 / 1.59 kB | 699.17 / 1.59 kB | 563.36 / 1.69 kB |
| `npm audit` | 35 (1 critical, 24 high) | **0** | **0** |
| 8 persona-flow screens vs F0 | — | pixel-identical, styles identical | **pixel-identical, styles identical** |

- **`npm audit` 0 held when measured.** On 2026-10-05 two seroval advisories (through the react-query devtools) made it 5 critical; fixed in Phase 3 (`94e5c7d`).
- **F1's `dist/` change** is fully attributed. JS modules changed only in the bumped react/react-dom 19.3.0 and @tanstack 5.104.1. All app modules and the other 68 packages are identical, and the CSS is byte-identical.
- **D-19 and D-24 do not show** in this app. The CSS diff is serialization only. The Chakra outline token loses to the unlayered legacy `button` rule in `src/index.css`. A positive control proves that the screenshot setup detects a one-line CSS change.

## Residual and deferred

- **ESLint 10** and other lint-plugin majors are not part of Phase 2. ESLint stays 9.39.5, and its one pre-existing error (`e2e/smoke.spec.ts:89`, unused `e`) is unchanged.
- **TypeScript 7** is blocked by typescript-eslint's peer range (D-22).
- **Native `resolve.tsconfigPaths`** instead of vite-tsconfig-paths: optional, not done.
- **The unlayered `button` rules in `src/index.css`** (a Vite template leftover) override Chakra and make the buttons barely legible. This is pre-existing and left as is; it is a candidate for a later UI pass.
- **Visual review by the owner:** accepted on 2026-10-05.

# Uplift notes: basicToDo, Phase 3 (CI pipeline)

**Uplift:** GitHub Actions on node16/node20 majors with super-linter v4.10.0 → node24 majors pinned by SHA with super-linter v9.0.0; mypy and ESLint blocking.

**Branch:** `plugin/uplift-basictodo/phase-3`, based on `phase-2`.

**Evidence:** `analysis/basictodo/BASELINE.md` ("CI pipeline (Phase 3)") and `analysis/basictodo/baseline/ci/`.

**Proof type:** local checks before CI: actionlint, zizmor, Prettier, super-linter v9 in Podman with the workflow's env, and a positive control per blocking gate. Backend and frontend are compared with the Phase 3 before state.

## Commits and delta → fix mapping

| Commit | Change | Deltas | How applied |
|---|---|---|---|
| `2ee51ba` | Every action on its node24 major, pinned to the release SHA with the version as a comment; one setup-uv step in the Lint job | D-25, D-26 | by hand, SHAs from the release tags |
| `d2e284b` | `super-linter/super-linter` v9.0.0; removed variables dropped; linters disabled or paths excluded, each with a reason; top-level `contents: read` in `codeql.yml` and `super-linter.yml` | D-27 | by hand, iterated with the local super-linter run |
| `f02e74d` | Workflows formatted with Prettier 3.9.8 (parsed YAML identical) | D-27 | `prettier --write` from the v9 image |
| `fecb197` | Dependabot `codeql-action` group, as on `main` | — | copied from `main` |
| `36765cb` | `sqlalchemy-stubs`, `sqlalchemy2-stubs` and the `[mypy]` extra removed | D-04 (Q12) | `pyproject.toml`, `uv lock` without upgrade |
| `a268203` | Three stale `type: ignore`s removed; `repository.py` filters on `to_do_table.c.id` | D-05 (Q12) | by hand |
| `f97dd49` | black 26.5.1 / flake8 7.3.0 on the 10 Python files changed since base | D-27 | black; F841 and targeted `noqa` by hand |
| `a752cf3` | `catch (e)` → `catch` in `e2e/smoke.spec.ts` | — (ESLint) | by hand |
| `4112dc5` | mypy and ESLint blocking; `tsc -b`; pylint over `backend/app` | Q9 | by hand |
| `5c46f21` | `pull-requests: write` of dependency review moved to job level | SEC-005 | by hand |
| `94e5c7d` | npm `overrides`: `seroval` and `seroval-plugins` 1.5.6 → 1.6.8 | — (GHSA-p6vx-979v-rg4c, GHSA-jp82-f5mq-hwhp) | `package.json` by hand, `npm install`; two lock entries |

## Result

| Measure | Before (`e3ffd22`) | After (`4112dc5`/`5c46f21`) |
|---|---|---|
| mypy | 3 errors, install-order dependent; non-blocking | **0** in two fresh venvs; **blocking** |
| ESLint | 1 error; non-blocking | **0**; **blocking** |
| Type check in CI | `tsc --noEmit`: 0 files checked | `tsc -b`: 32 project files |
| pylint (report-only) | 3 modules | 15 modules |
| super-linter | v4.10.0, red | v9.0.0, **green** locally and on PR #115 |
| pytest per test, golden master, frontend gates, e2e | — | identical to the before state |
| CI on the draft PR | #114: 5 of 6 green, Node 20 deprecation warning in all 10 jobs | **#115: 6 of 6 green** at `5dadbcd`, no Node 20 warning; 151 s wall clock, 474 s runner time. On `dfb46a5` Dependency review and Trivy red on new seroval advisories, fixed in `94e5c7d`; **6 of 6 green again at `a51d618`** (141 s, 468 s) |
| npm audit (frontend) | 0 when measured; 5 critical after the seroval advisories of 2026-10-05 | **0** (`94e5c7d`) |

- Each blocking gate (mypy, ESLint, `tsc -b`, super-linter) failed on a deliberate error and passed again after the revert.
- On PR #115 the mypy and ESLint steps run clean, and nothing swallows their exit code any more. On #114 both exited 1 and were still reported as success (`baseline/ci/ci-gates-pr114-pr115.txt`).

## Residual and deferred

- **pylint** stays report-only (`--exit-zero`, Q9). Over all of `backend/app` it rates 8.35/10. It reports `E1102 func.now is not callable` on `database.py`, a known false positive for SQLAlchemy's `func`.
- **Disabled super-linter linters** (Biome, Prettier for TS/JS, ruff, isort, jscpd, pylint) need a repository configuration before they can be turned on.
- **`analysis/` and `UPLIFT_NOTES.md` are excluded from super-linter.** They are modernization evidence, not product code.
- **uv stays 0.7.16** in CI, and ESLint stays on major 9.
- **The super-linter image is pinned by tag, not by digest.** The action at the pinned SHA references `ghcr.io/super-linter/super-linter:v9.0.0`, a mutable tag. On PR #115 it resolved to the image the local runs used. A digest pin would need `uses: docker://ghcr.io/super-linter/super-linter@sha256:…`, which is not part of this phase.
- **The seroval override** in `frontend/package.json` goes outside the `~1.5.4` range of solid-js 1.9.15, the latest release. Only solid-js's SSR build uses seroval, and this app does no server-side rendering. Remove the override once solid-js depends on a fixed seroval. Evidence: `analysis/basictodo/BASELINE.md` ("seroval advisories") and `analysis/basictodo/baseline/ci/ci-seroval-dfb46a5.txt`.
- **#114 (Phase 2) is affected as well.** It brought seroval in, and its last green run predates the advisories. The fix is on `phase-3` only.

# Uplift notes: basicToDo, Phase 4 (data layer)

**Uplift:** the doubly defined `toDo` table (a declarative `ToDoORM` for the DDL, an imperative `Table` mapped onto the `ToDoEntryData` dataclass for every read and write) → one `MappedAsDataclass` model on a `DeclarativeBase`. `sqlalchemy.Uuid` replaces `sqlalchemy-utils`, and there is an Alembic baseline revision. SQLAlchemy stays 2.0.54 (`<2.1`, Q4).

**Branch:** `plugin/uplift-basictodo/phase-4`, based on `phase-3`.

**Evidence:** `analysis/basictodo/BASELINE.md` ("Data layer (Phase 4)") and `analysis/basictodo/baseline/db/`.

**Proof type:**
- characterization tests and properties written first and run on the legacy mapping and both locks;
- per-commit pytest tables and golden master against the Phase 1 target;
- the repository's SQL captured before and after;
- the legacy sample database read and written by the legacy code (`a2d59f1`, legacy lock) and the new code, in both directions, each in its own process and venv;
- a positive control for every new guard.

## Commits and delta → fix mapping

| Commit | Change | Deltas | How applied |
|---|---|---|---|
| `5cc9e06` | Characterization tests: RULE-034, RULE-035, RULE-037, id binding, DDL snapshot | (entry criterion) | by hand; green on both locks before any change |
| `1944856` | `hypothesis` (dev) and 4 storage round-trip properties | (validation strategy) | `uv add --dev`; lock adds 2 packages, moves none |
| `a803365` | Schema snapshot, sample legacy DB, before state | (entry criterion) | `make_sample_db.sh` on the legacy code |
| `2ae6942` | black 26.5.1 on `conftest.py`, `todo_schema.py`, `init_db.py`; unused imports removed | — | black; ASTs identical |
| `7b54c2e` | One declarative model; `ToDoORM`, `Table`, registry mapping and `sqlalchemy-utils` removed | TD-5, D-03b, D-13 | by hand; `uv lock` without upgrade removes one package |
| `15d0044` | `init_db.py` imports `backend.app.*` from its own checkout | (import root, brief scope) | by hand |
| `d7f9092` | `ConfigDict` instead of `class Config` | D-14 | by hand |
| `053a4f3` | Alembic baseline revision `0001`, `[tool.alembic]` in `pyproject.toml`, `check_baseline.py` before stamping | (brief scope; the owner's decisions) | revision written by hand; `alembic` in the dev group |
| `5ffc86b` | super-linter: `backend/migrations/script.py.mako` excluded (that file only) | — (scope exception, the owner) | `FILTER_REGEX_EXCLUDE`; actionlint, zizmor, Prettier clean |

## Result

| Measure | Before (`c30b4da`) | After (`053a4f3`) |
|---|---|---|
| Definitions of `toDo` | 2 (`ToDoORM` and an imperative `Table`) plus an imperative mapping | **1** (`ToDoEntryData`) |
| DDL of a fresh database | snapshot | **byte-identical** (`create_all`, `init_db.py`, `alembic upgrade head`) |
| Repository SQL (7 operations) | — | **identical**, parameters included |
| pytest | 456 passed, 1 skipped | 483 passed, 1 skipped: **27 new tests, 0 changed** against the Phase 1 target |
| Golden master | 0 of 83 against the Phase 1 target | **0 of 83** against the Phase 1 target and Phase 3 |
| Legacy sample DB | written by the legacy code | read identically by both codes, written by both, and readable by the legacy code after the new code wrote to it |
| mypy | 0 | **0** in two fresh venvs synced like CI, identical freezes |
| Deprecation warnings in pytest | 2 (MovedIn20Warning D-13, PydanticDeprecatedSince20 D-14) | **0**; `pytest -W error` collects |
| Runtime pins / `pip-audit` | 63 / 0 | **62** (no `sqlalchemy-utils`) / **0** |
| Coverage | 83.98 % | 83.47 %: removed always-executed statements left the denominator; the 88 missed statements are unchanged |
| e2e | 13/13 | **13/13** |
| super-linter v9 (local) | green (`5c46f21`) | red at `053a4f3` only on `backend/migrations/script.py.mako` (Alembic's Mako template, parsed as Python); **green at `5ffc86b`** with that file excluded |
| CI on the draft PR | #115: 6 of 6 green (141 s, 468 s) | **#116: 6 of 6 green** at `031731c`, plus 3 push runs; 145 s wall clock, 496 s runner time |

**Two behaviours changed on purpose.** Their characterization tests were replaced, not edited, so the per-test table shows them as 4 rows out and 4 in.
- **RULE-037:** an entry built without `deleted` now gets `False`. The legacy dataclass default was a `MappedColumn`, and storing it failed with `OperationalError: no such column: deleted`. All 65 existing constructions pass `deleted`, so no caller changes behaviour.
- **D-03b:** the repository binds `uuid.UUID` only, and a `str` id raises `StatementError`; `UUIDType` used to convert strings. This is unreachable over HTTP (typed path parameters and schemas; `UUIDValidator` returns `UUID`).

## Residual and deferred

- **Alembic is not used at runtime** (the owner's decision). `main.py` and `init_db.py` keep `create_all`. An existing database is stamped by hand, after `check_baseline.py` accepts it (`analysis/basictodo/PLAYBOOK.md`). Alembic moves to the runtime and into the runtime dependencies in Phase 5, with the Q6.6 data migration.
- **Scope exception:** Phase 4 touches `.github/workflows/super-linter.yml` once (`5ffc86b`) to exclude the Alembic template, by the owner's decision (noted in the brief). The pattern matches that file only.
- **The legacy Query API** (`session.query`) stays; `select()` is not part of this pass.
- **SQLAlchemy 2.1 (C3)** is now possible from the data layer's side, because `sqlalchemy-utils` is gone. It stays deferred (Q4).
- **pylint's `E1102 func.now is not callable`** (report-only, a known false positive) now points at `models/todo.py`.
- **Aware timestamps lose their offset** when stored, and the wall clock is kept (pinned by a property test). Q6.6 in Phase 5 builds on this.

# Uplift notes: basicToDo, Phase 5 (hardening and approved behaviour changes)

**Change:** the owner's Q6 fixes (6.1 to 6.7, 6.9) with the keeps 6.8 and 6.10; UTC timestamps with a data migration of existing rows and Alembic at startup; the security items Q8 put in scope (SEC-002, -003, -004 with Q8b, -008, -010, -014); `slowapi` removed (Q8a); TD-3, TD-7; README, PlantUML and API descriptions (Q7).

**Branch:** `plugin/uplift-basictodo/phase-5`, based on `phase-4`.

**Evidence:** `analysis/basictodo/BASELINE.md` ("Hardening and behaviour changes (Phase 5)" and the change log), `analysis/basictodo/SECURITY_FINDINGS.md`, `analysis/basictodo/baseline/p5/`, `analysis/basictodo/baseline/frontend/P5/` and `p5-review.html`.

**Proof type:**
- the behaviours to change pinned first (`test_legacy_*`), then replaced in the commit that changes them;
- per-commit pytest tables and golden master, every difference attributed to a commit and a decision ID;
- the data migration on both sample databases row by row, on Europe/Berlin fixtures across both DST changes, with downgrade, backup, WAL and atomicity tests;
- Q8b against a real uvicorn;
- a positive control for every new guard;
- an independent hardening verify on the tip.

## Commits and decision → fix mapping

| Commit | Change | Decisions | How applied |
|---|---|---|---|
| `e791a9c` | Golden master (+21 requests, offset timestamps), screens by title; P4 captures | (entry) | by hand |
| `72baf56` | Keeps pinned (RULE-024, RULE-052); seven legacy pins | Q6.8, Q6.10 | by hand |
| `7f2e89d` | Hardening pass, P5 sample DB, the owner's decisions in the brief | (entry) | security-auditor, separate reviewer |
| `cf4e345` | One configured logger, neutralised messages | TD-3, SEC-010 | by hand |
| `a0244c2` | Blocklist removed | Q6.1 | by hand |
| `0d03cef` | Length and control-character rules in the API; 422 for every validation error | Q6.2, Q6.3 | by hand |
| `ddf6d70` | done plus edits in one write | Q6.5 | by hand |
| `7f203ca` | Bounded pagination, newest first, `total` | Q6.4, SEC-004 | by hand |
| `2c8cb68` | No placeholder description from the UI | Q6.7 | by hand |
| `7158735` | UTC timestamps, revision `0002`, Alembic at startup with backup, `alembic` at runtime | Q6.6, Q6.7 | by hand; `uv lock` regroups only |
| `2e55652` | Delete toasts on the server's answer, readable 422, code-point counting | Q6.9, Q6.3, Q6.2 | by hand |
| `8f5bf11` | Local bind, Host check, JSON only, CORS, 16 KiB cap, owner-only DB file | SEC-002, -003, -008, -014, Q8b | the reviewed patch, R2 and R4 |
| `42c8deb` | `slowapi` removed | Q8a | `uv lock`, no upgrade |
| `e7fa753` | Dead code removed | TD-7 | `git rm` |
| `47877f8` | README, PlantUML, route descriptions | Q7 | by hand |
| `eb178e3` | super-linter findings (README, codespell) | — | Prettier 3.9.8, by hand |

Plus five `style:` commits (black 26.5.1, flake8 7.3.0) before the files they prepare.

## Result

| Measure | Before (`7e6ae13`) | After (`eb178e3`) |
|---|---|---|
| pytest | 483 passed, 1 skipped | **736 passed**; 103 tests replaced, 355 new, every one attributed |
| Golden master (104 requests) | P4 capture | **68 differ**, all attributed to a decision; keeps unchanged |
| Timestamps | `created_at` server-local, `updated_at` the database's UTC clock, never refreshed | both UTC with `Z`; `updated_at` refreshed on every change; existing rows converted |
| Database at startup | `create_all` | Alembic, one transaction, checked backup, baseline check, zone check |
| Default bind | `0.0.0.0` with reload | `127.0.0.1` without reload |
| Request checks | none | Host, JSON only (415), 16 KiB (413), CORS without credentials |
| Runtime pins / `pip-audit` | 62 / 0 | **59** / **0** |
| mypy | 0 | **0** in two fresh venvs |
| Coverage | 84.1 % | 92.2 % |
| Frontend | vitest 13, e2e 13 | **vitest 32, e2e 16** |
| super-linter v9 (local) | green | **green** at `eb178e3` (18 linters) |

## Residual and deferred

- **Out of scope by decision:** authentication and multi-user (SEC-001, Q8); rate limiting (Q8a); purge and restore of deleted todos (Q7); SQLAlchemy 2.1 and Python 3.14; a UI pager; `select()` instead of `session.query`.
- **Security residuals below Medium** (`SECURITY_FINDINGS.md`):
  - blocking database calls in async routes (F-07);
  - database errors log SQL and parameters, cut to 200 characters (F-09);
  - a credential-bearing `DATABASE_URL` is echoed in an error (F-10, SEC-012);
  - uv 0.7.16 in CI (F-18);
  - `/docs` loads scripts from a CDN without SRI (F-21);
  - local e2e can reuse a running backend and clean up its todos (F-22);
  - bidi characters (Cf) stay accepted (F-13);
  - test databases remain in the git history (F-15);
  - `extra="forbid"` not adopted (F-06).
  - five Informational observations from the verify on the tip (N-1 to N-5): identifier quoting in the backup check, the backup reopened by name, the log filter's fallback, unescaped operator-side text from `init_db.py`, duplicate Host headers past Starlette's Host check.
- **Frontend:** mutations keep `retry: 1`, so a 4xx is sent twice; there is no UI to mark a todo as done or to edit its description; `frontend/src/lib/` is ignored by the Python template's `lib/` rule (new files need `git add -f`).
- **Backend:** `hard_delete_to_do` stays unused (the brief's TD-7 list did not name it); responses keep the unused `data`, `message` and `error` fields; `DATABASE_URL` still accepts `postgresql://` and `mysql://` prefixes, although startup prepares SQLite files only.
- **Migration:** a `created_at` in the spring gap hour comes back one hour later after a downgrade; the placeholder description cannot be restored.
