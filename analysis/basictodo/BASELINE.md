# Baseline: basicToDo backend on the legacy lock

_Phase 1 (pilot) oracle, recorded 2026-10-05. Required by `MODERNIZATION_BRIEF.md` §3 Phase 1 entry criteria and by `/modernize-uplift` Step 4.2._

This file is the **equivalence target**. The uplift has to reproduce every result here, including the quirks and the one skipped test. A difference is either classified below or it blocks the phase.

## What was measured

| Item | Value |
|---|---|
| Tree | `plugin/uplift-basictodo/phase-1` at `72cf484`: the seed `bd2a0b9` plus `61d37da` (builder-test rename) and `72cf484` (P0 contract tests). This is before commit 5 (`ddad5ec`). Recorded from a git worktree checked out at that SHA. |
| Application code | `backend/app`, `backend/scripts`, `pyproject.toml` and `uv.lock` are **byte-identical to `a2d59f1`** (checked with `git diff --quiet a2d59f1 HEAD -- …`) |
| Lock | `baseline/uv.legacy.lock`, sha256 `1887019c531d0e422c5ab1452f0d0a06164a46e47c8090fbcc970a71c90b19a2` |
| Key versions | fastapi 0.115.12, starlette 0.46.2, pydantic 2.11.5, sqlalchemy 2.0.43, pytest 8.4.2 |
| Runtime | Python 3.13.15, uv 0.7.15 (CI pins 0.7.16), Node 22.22.2 (CI uses 20), Playwright 1.57.0 with chromium-1200 |
| venv | built with `uv sync --frozen --all-extras --dev` outside the repository; every run uses it as-is, without re-syncing |

**How to reproduce:** see the scripts in `baseline/`. Each one is run from the repository root.
- `run_suite.sh <venv> <outdir>`: the `python-app.yml` gates (init_db, pytest with coverage, mypy). No `DATABASE_URL`, as in CI.
- `run_golden_master.sh <venv> <out.json>`: starts uvicorn on a fresh SQLite database on port 18765 and records the golden master.
- `golden_master.py diff <a.json> <b.json>` and `junit_table.py <junit.xml> --diff <table.tsv>` compare two runs.

**Provenance: which tree each process actually ran.** Each venv holds an editable install of the checkout it was synced from.
- Both run scripts put the current tree first on `PYTHONPATH`. Without that, `backend/scripts/init_db.py` started from another worktree imports `backend.app` from the synced checkout. The server (`python -m uvicorn`) and pytest resolve `cwd` or rootdir first anyway. This was verified on 2026-10-05; the negative test is below.
- `provenance.py` runs `init_db.py` and the uvicorn server. The `pytest_provenance` plugin runs inside pytest. **Each process records its own loaded `backend.*` and `app.*` modules**, relative to the tree, plus the tree SHA, the venv and the FastAPI version. It aborts with exit code 3 if any module came from outside the tree.
- The golden-master captures store the server and init_db records under `provenance`. `golden_master.py diff` prints them but never compares them.
- Negative test: in a worktree without `PYTHONPATH`, `init_db.py` stopped with exit 3 and listed `backend.app`, `backend.app.models` and `backend.app.models.todo` as outside the tree.

| Run | Tree | venv | `backend.app` loaded from | App modules outside the tree |
|---|---|---|---|---|
| golden master baseline: server, init_db (`baseline/legacy-lock.json`) | `72cf484` | legacy-lock | `backend/app/__init__.py` | none (33 server, 8 init_db) |
| pytest baseline (`baseline/provenance-pytest-72cf484.json`) | `72cf484` | legacy-lock | `backend/app/__init__.py` | none (51) |
| golden master neutrality (`baseline/legacy-lock-after-c6.json`) | `2713c3c` | legacy-lock | `backend/app/__init__.py` | none |
| pytest neutrality (`baseline/provenance-pytest-2713c3c.json`) | `2713c3c` | legacy-lock | `backend/app/__init__.py` | none (51) |
| golden master target (`baseline/target-lock.json`) | `0df26b9` | target-lock | `backend/app/__init__.py` | none |
| pytest target (`baseline/provenance-pytest-0df26b9.json`) | `0df26b9` | target-lock | `backend/app/__init__.py` | none (52) |

## pytest

| Tree | Passed | Skipped | Failed | Coverage |
|---|---|---|---|---|
| Seed `bd2a0b9` (unchanged tests) | 433 | 1 | 0 | 81.78% |
| `61d37da` (builder tests collected) | 442 | 1 | 0 | 81.78% |
| **`72cf484` (+ 12 P0 contract tests): the baseline** | **454** | **1** | **0** | **83.96%** (lines 484/572, branches 55/70) |

- **The exit criteria compare against 454 / 1 / 83.96%.** The brief's "442 passed / 1 skipped" predates the P0 contract tests, which the brief itself requires in Phase 1 (§5). They add 12 tests and 2.18 coverage points.
- **The skipped test:**
  - `test_field_validator_integration.py::TestFieldValidatorOptionalRealWorld::test_validate_optional_multiline_description`;
  - the reason it gives is _"Bug: SQL regex too strict - rejects 'Execute' in normal text"_.
  - It stays skipped through Phase 4. The keyword blocklist is a Q6 topic.
- **Warnings (2):**
  - a pydantic class-based `config` deprecation;
  - SQLAlchemy `MovedIn20Warning` for `declarative_base()` at `database.py:17`.
- **The per-test table** is `baseline/pytest-legacy-lock.tsv`, with 455 rows (`<test id>\t<outcome>`). It is the reference for every later run.

## mypy (non-blocking in CI)

**3 errors in this venv:**
- `database.py:10`: no `registry` in `sqlalchemy.orm`;
- `database.py:52`: unused `type: ignore`;
- `main.py:10`: unused `type: ignore`.

**The mypy result is not stable across installs (D-04).** `sqlalchemy-stubs` and `sqlalchemy2-stubs` both ship `sqlalchemy-stubs/orm/__init__.pyi`, and whichever installs last wins.
- In three venvs built from these locks `sqlalchemy-stubs` won.
- In the target venv `sqlalchemy2-stubs` won. That one exports `registry`, so `database.py:10` and `main.py:10` disappear.

The error count therefore says nothing about equivalence until Phase 4 removes both stub packages. Here, and in CI, it is recorded but not compared.

**Superseded in Phase 3 (Q12):** D-04 removed both stub packages there, and D-05 fixed the remaining errors. mypy reports 0 errors in fresh venvs and is a blocking gate; see "CI pipeline (Phase 3)".

## Playwright e2e

**13 / 13 passed, 0 flaky, 0 retries.** The run took 17.8 s, under `CI=true`, against the legacy-lock backend started by the config's own `webServer` (`uv run python -m backend.app.main`, with `UV_PROJECT_ENVIRONMENT` pointing at the legacy venv).

<details><summary>Per-test results</summary>

| Test | Result | Attempts |
|---|---|---|
| smoke › should load the application | passed | 1 |
| smoke › should find the input field | passed | 1 |
| todo-crud › should create a new todo | passed | 1 |
| todo-crud › should update an existing todo | passed | 1 |
| todo-crud › should delete a todo | passed | 1 |
| todo-crud › should cancel todo edit | passed | 1 |
| todo-validation › should prevent creating empty todo | passed | 1 |
| todo-validation › should prevent creating whitespace-only todo | passed | 1 |
| todo-validation › should show character limit warning | passed | 1 |
| todo-validation › should prevent exceeding character limit | passed | 1 |
| todo-validation › should clear error when user starts typing | passed | 1 |
| todo-validation › should prevent updating todo to empty value | passed | 1 |
| todo-validation › should show visual error indicator on invalid input | passed | 1 |

</details>

## HTTP golden master

`baseline/legacy-lock.json` holds **83 request/response pairs** from a real uvicorn server, played by a stdlib-only client so that the client is identical for every lock.

| Status | 200 | 422 | 404 | 400 | 409 | 405 | 500 | 307 |
|---|---|---|---|---|---|---|---|---|
| Count | 40 | 20 | 9 | 5 | 4 | 3 | 1 | 1 |

**Coverage of the sequence:**
- the 60-request set from `DELTA_CATALOG.md` §D;
- every error path: 400, 404, 405, 409, 422, 500 and the 307 trailing-slash redirect;
- CORS preflight for allowed, disallowed and `127.0.0.1` origins, plus simple CORS requests on 200, 404 and 422;
- RULE-008 and RULE-031 end to end: duplicate, delete, delete again, GET, PUT and restore on a deleted id, and re-creating a deleted id;
- `/openapi.json`, `/docs`, `/redoc` and `/docs/oauth2-redirect`.

**What is recorded:**
- status and reason;
- **all** response headers, including `server`;
- the raw body;
- per response, the **timestamp basis** of every naive timestamp (see below).

**Normalization: timestamp values only.** Digits become format letters; separators, fraction length and offset stay literal. That keeps two current behaviours visible:
- `created_at` is serialized as `YYYY-MM-DDThh:mm:ss.ffffff` (6 fraction digits, naive, no offset);
- `updated_at` is serialized as `YYYY-MM-DDThh:mm:ss` (second precision, naive, no offset). SQLite's `CURRENT_TIMESTAMP` fills it.

**Zero microseconds.** Python drops the fraction when the microsecond is exactly 0. A JSON field value without a fraction is masked as `.ffffff` when every other distinct value of **the same field** in the capture has 6 digits. The rule is per field, not per response, so `updated_at` keeps showing second precision.

**Timestamp basis.** Masking hides which clock a naive timestamp came from. Before masking, each one is compared with the capture's time window on the local clock and on the UTC clock (tolerance 5 s), and the result is stored per JSON path as `local`, `utc`, `local=utc` or `neither`. The offset itself is never stored, so captures on both sides of a DST change stay comparable.

In the baseline, all 57 `created_at` values are **`local`** and all 57 `updated_at` values are **`utc`**.

**Determinism:** two consecutive captures of `72cf484` on the same lock differ in 0 of 83 responses. An earlier version of the script differed only in the 307 `location` header's random port, so the server now runs on a fixed port.

**History:**
- A first baseline was taken the same day with an earlier script that had neither the timestamp basis nor the zero-microsecond rule.
- The captures were then taken again with the provenance records. Against the captures without provenance, the responses are **byte-identical** in all three (baseline, neutrality, target), and pytest is identical per test, in versions, freeze, coverage totals and mypy errors.

**Pinned quirks** (they stay as they are until Phase 5):

| Request | Legacy response |
|---|---|
| `PUT {"done": null}` | **500**, `text/plain` "Internal Server Error" |
| `POST` with title "Todo to delete" | **400** `{"detail":"Bad request"}` (keyword blocklist) |
| `POST` re-creating a soft-deleted id | **409** `{"detail":"ToDo already exists"}` (RULE-008 and RULE-031) |

## Classification of differences (filled in during Phase 1 Gate C)

### Neutrality of commits 5 and 6 (legacy lock)

Recorded from a worktree at `2713c3c` (after commit 6), compared with this baseline from `72cf484` (before commit 5):

| Check | Result |
|---|---|
| Golden master | **0 of 83 responses differ** |
| pytest per test (`junit_table.py --diff`) | **0 of 455 differ** |
| mypy errors | identical |

Every difference between the legacy and target locks below therefore comes from commit 7 (`0df26b9`) alone.

### Target lock (`0df26b9`) vs legacy lock (`2713c3c`)

**pytest:**
- 456 passed / 1 skipped, coverage 83.96% (Δ 0.00).
- All 455 baseline tests keep their result.
- The 2 new tests are D-09's telemetry tests.

**Golden master:** 79 of 83 responses differ. There are no status changes and no timestamp-basis changes.

| Difference | Responses | Delta |
|---|---|---|
| `vary: Origin` added | 75 (every response that passes the CORS middleware without an allowed `Origin`) | **D-10** |
| Preflight `access-control-allow-methods` gains `QUERY`; preflight `vary` becomes `Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network` | 4 preflights | **D-10** |
| `uuid_parsing` `msg` and `ctx.error` shortened (and `content-length`) | 4: body id and the PUT/GET/DELETE path ids | **D-11** |
| OpenAPI `ValidationError` gains `ctx` and `input` (and `content-length`) | `/openapi.json` | **D-12** |
| `/docs` HTML gains `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (and `content-length`) | `/docs` | **D-28** |
| `/redoc` loads `redoc@2` instead of `redoc@next` from the CDN (and `content-length`) | `/redoc` | **D-28** |

The 4 unchanged responses are the 500 from `PUT {"done": null}`, which the error middleware answers outside CORS, and the three requests from the allowed origin, which already carried `vary: Origin`.

**Status: all 79 differing responses are classified; zero unclassified differences.** The two docs-page differences first stopped the phase, because D-10, D-11 and D-12 did not cover them. On 2026-10-05 the owner added them to the catalog as **D-28** and extended the exit criterion accordingly.

### Other exit checks on the target lock (`0df26b9`)

| Exit criterion (brief §3 Phase 1) | Legacy lock | Target lock | Met |
|---|---|---|---|
| Same suite: 442 passed / 1 skipped, coverage ≥ 80% and within 0.5 points of the baseline | 454 / 1, 83.96% | **456 / 1, 83.96%** (Δ 0.00). The +2 are the D-09 telemetry tests. 442 was the brief's count before the P0 tests. | ✅ |
| Golden master: every diff is D-10, D-11, D-12 or D-28; zero unclassified | — | 79 of 83 differ, all classified (above) | ✅ |
| P0 contract tests for RULE-008 and RULE-031 green on both locks | 12/12 | 12/12 | ✅ |
| Playwright e2e 13/13 against the upgraded backend | 13/13 | **13/13**, 0 flaky, 0 retries, 17.4 s | ✅ |
| `pip-audit` on the runtime dependencies reports 0 advisories | 22 in 9 packages at `72cf484` (69 pins, dev tools included); **19 in 7** at `ddad5ec` (44 pure runtime pins) | **0** (63 runtime pins; the 19 added pins all come from `fastapi[standard]` 0.142, see `UPLIFT_NOTES.md`) | ✅ |
| The telemetry choice (Q3) is proven by a test with `OTEL_EXPORTER_OTLP_ENDPOINT` set | — | `test_telemetry_export.py`. The app sends nothing to a local OTLP sink; a plain `FastAPI()` control does send `/v1/traces`. Before the fix, the app test failed with `/v1/traces` and `/v1/metrics` received. | ✅ |

**Which venv the e2e backend ran on.** Playwright starts the backend itself (`webServer`: `uv run python -m backend.app.main`). The runs set `UV_PROJECT_ENVIRONMENT` to the venv and `UV_NO_SYNC=1`. With exactly these variables, `uv run` resolves:
- `.envs/legacy-lock` → fastapi 0.115.12;
- `.envs/target-lock` → fastapi 0.142.2.

In both cases `backend.app` loads from the working copy.

**pip-audit** ran over `uv export --frozen --no-dev --no-hashes --no-emit-project --no-header --color never`. Without `--color never`, the header contains ANSI codes that pip-audit cannot parse. Three points were audited: `72cf484` (dev tools still in the runtime), `ddad5ec` (after the hygiene commit) and `0df26b9`. Advisory counts are unique IDs; pip-audit lists some IDs twice under aliases.

## CI (Q10)

Measured on draft PR #113 (`plugin/uplift-basictodo/phase-1` at `e445972` → `plugin/uplift-basictodo/base`), 2026-10-05. This closes the "don't know" from preflight Check 0.

**Pipeline duration:** about **3 minutes** of wall clock (180 s from the first run created to the last job finished), with 536 s of runner time across 10 jobs. The longest jobs are Super-Linter (176 s) and Playwright (104 s).

| Workflow | Job | Result | Duration |
|---|---|---|---|
| Python Application CI | Backend Tests & Quality Checks | ✅ | 36 s |
| | Lint the python code | ✅ | 25 s |
| | Comment coverage on PR | ✅ (comment posted) | 19 s |
| End-to-End Tests | Playwright E2E Tests | ✅ | 104 s |
| Frontend CI | Frontend Build & Lint | ✅ | 37 s |
| CodeQL Advanced | Analyze (actions / python / javascript-typescript) | ✅ ✅ ✅ | 35 / 51 / 41 s |
| Dependency review | dependency-review | ✅ | 12 s |
| Lint Code Base | run-lint (super-linter v4.10.0) | ❌ | 176 s |

The push to `phase-1` ran the three push-triggered workflows as well: Python 39 s, Frontend 123 s, E2E 141 s, all green.

**Exit criterion:** python-app and e2e are green ✅. The other four workflows are recorded here.

**Super-Linter, attributed.** `DEFAULT_BRANCH` resolved to `plugin/uplift-basictodo/base`, so only the files changed in phase-1 were linted, as intended. Six linters reported errors. They fall into three groups:

- **Pre-existing in legacy files** that phase-1 touches or renames: `backend/app/api/api.py`, `backend/app/business_logic/decorators.py`, and the two renamed builder tests (content unchanged).
  - black (multi-name import, single quotes, missing final newline);
  - flake8 W292;
  - isort with super-linter's default profile (the repo has no isort config at `a2d59f1`);
  - jscpd (the async/sync wrapper pair in `decorators.py`).
  - None of these is on a line phase-1 changed.
- **Phase-1 code:** `test_p0_contracts.py`, `test_telemetry_export.py` and `baseline/{golden_master,junit_table,provenance,pytest_provenance}.py`.
  - black (line wrapping) and flake8 E501 in `golden_master.py`.
  - **Fixed in `53b317d`** with super-linter's own versions (black 22.12.0 defaults, flake8 6.0.0 at 120 columns). The PR run on `53b317d` confirms it: black 10 → 4 files and flake8 5 → 4, all of them legacy files.
  - Still open: isort in `test_p0_contracts.py`, which uses the same default-profile ordering as the existing tests.
- **Analysis documents:** `DELTA_CATALOG.md`, `MODERNIZATION_BRIEF.md`, `PLAYBOOK.md`, `PREFLIGHT.md`, `BASELINE.md`, and the generated `legacy-vs-target.diff.txt`.
  - markdownlint: MD013 line length, MD049, MD007, MD040;
  - textlint terminology: "id" → "ID", "repo" → "repository", and so on;
  - jscpd on the generated diff text.

**Why all six linter statuses stay red.** Super-Linter posts one status per linter (`--> Linted: …`), all from the single `run-lint` job. Each of the six still has at least one finding in a legacy file or an analysis document, so each stays red even after `53b317d`.

On `main`, the owner has since disabled pylint, jscpd and isort in super-linter for the same reasons. The base branch keeps the `a2d59f1` configuration, and Phase 3 owns the linter setup.


## Frontend (Phase 2)

_Recorded 2026-10-05 for Phase 2 (brief §3, entry criterion "frontend section on legacy dependencies")._

**State measured: F0.** This is `frontend/` exactly as it stands at the `phase-1` tip `75e0fff`, with the legacy lock. It was recorded from a git worktree at that SHA. The backend for e2e and screens is the Phase 1 target (FastAPI 0.142, venv `target-lock`), so in Phase 2 only the frontend changes.

**Runtimes.** CI runs the legacy frontend on Node 20, which is not available locally. The local oracle is **Node 22.22.2 / npm 10.9.7**. F0 was also run on **Node 24.21.0 / npm 11.19.0**, to separate the runtime change from the dependency changes.

| Gate | Node 22 | Node 24 | Same? |
|---|---|---|---|
| `npm ci` | ✅ | ✅ | — |
| vitest | 13/13 | 13/13 | ✅ per test (`F0/vitest.tsv`) |
| `npm run build` (`tsc -b` + `vite build`) | ✅ JS 669.36 kB, CSS 1.59 kB | ✅ | ✅ **byte-identical `dist/`** (`F0/dist.sha256`) |
| ESLint (`continue-on-error` in CI) | 1 error: `e2e/smoke.spec.ts:89` `'e' is defined but never used` | same | ✅ |
| `npm audit` | 35: 1 critical (vitest), 24 high, 7 moderate, 3 low | same | ✅ |
| Playwright e2e (frontend's own 1.57, chromium-1200) | 13/13, 0 flaky | 13/13, 0 flaky | ✅ per test (`F0/e2e.tsv`) |
| Screenshots, 8 screens | captured | captured | ✅ **pixel-identical, computed styles identical** |

**Screenshots.** A fixed setup takes every capture in this phase (F0, F1, F2), so browser rendering cannot vary:
- **Browser:** Playwright **1.63.0** with Chromium headless shell **153.0.8010.12** (revision 1243). It is installed from `baseline/frontend/runner/` (exact pins, lockfile committed) **outside** `frontend/node_modules`. The frontend's own Playwright is used only for e2e.
- **Servers:**
  - `frontend/dist` is served by Python's stdlib HTTP server on `localhost:5173`, so Vite's `preview` is not in the path. Port 5173 is needed because the backend allows only that origin.
  - The backend runs on `127.0.0.1:8000` with a fresh SQLite database, started through `provenance.py`.
- **Browser context:** 1280×800 at 1×, `reducedMotion`, animations disabled, caret hidden, mouse parked in the corner, fonts and network idle awaited.
- **The 8 screens** follow the four persona flows (brief §4):
  - empty list;
  - title typed;
  - after create, with toast;
  - four todos;
  - edit form open;
  - after save, with toast;
  - after delete, with toast (`window.confirm` accepted);
  - validation error.
- **Each capture stores:**
  - the PNG;
  - the **computed styles of every rendered element**, keyed by DOM path (colours, borders, outline, shadow, font, spacing, box);
  - `capture.json` with the Playwright and browser version, the Chromium revision, Node, the runner lock hash and the SHA-256 of every `dist/` file.
- **Determinism:** two captures of the same build are pixel-identical in all 8 screens.
- `compare_screens.py` reports pixel share, bounding box, a diff image and every style change, and refuses to compare captures made with different setups.

**A legacy visual quirk** pinned by the screens: the Chakra buttons (Edit, Delete Todo, Save, Cancel) render white text on a near-white background and are barely legible.

**Tools,** in `baseline/frontend/`, all run from the repository root:
- `run_frontend_suite.sh <node-bin> <outdir> [backend-venv]`
- `run_screens.sh <backend-venv> <outdir> <runner-dir> <node-bin>`
- `capture_screens.mjs`
- `compare_screens.py`

### Frontend checkpoints after F0 (`phase-2`)

All later states were measured on **Node 24.21.0 / npm 11.19.0**. Screens were captured with the same runner and browser as F0; `capture.json` shows identical Playwright, browser, revision and runner lock for F0, F1 and F2.

| State | Commit | vitest | Build | e2e | `npm audit` | Screens vs F0 | `dist/` vs F0 |
|---|---|---|---|---|---|---|---|
| Prerequisites D-17, D-18 (legacy deps, Node 22) | `2dba37a` | 13/13, identical per test | ✅ | 13/13, identical | 35 | **pixel-identical, styles identical** | **byte-identical** |
| CI on Node 24 (D-15) | `d1709cb` | — (workflow change only) | | | | | |
| **F1** same-major refresh | `21a7337` | 13/13, identical per test | ✅ JS 699.17 kB, CSS 1.59 kB | 13/13 (Playwright 1.57), identical | **0** | **pixel-identical, styles identical** | JS and `index.html` differ, CSS byte-identical; see below |
| **F2** majors (C2) | `e0fc04c` | 13/13, identical per test | ✅ JS 563.36 kB, CSS 1.69 kB | 13/13 (**Playwright 1.63**), identical | **0** | **pixel-identical, styles identical** | all files differ (new toolchain) |

ESLint reports the same single pre-existing error in every state (`e2e/smoke.spec.ts:89`, an unused `e`). It is `continue-on-error` in CI.

**F1 stop rule, `dist/` differences classified.** `bundle_modules.py` rebuilt F0 and F1 with sourcemaps and compared the bundle module by module (`F0/bundle-modules.json`, `F1/bundle-modules.json`, `F1/bundle-modules-diff-vs-F0.txt`):
- **JS bundle:** module changes occur **only** in packages that F1 bumps:
  - `react` and `react-dom` 19.2.0 → 19.3.0;
  - `@tanstack/query-core`, `@tanstack/react-query` and `@tanstack/react-query-devtools` 5.90.10/5.91.0 → 5.104.1.
- **Identical modules:** all 22 app modules and the other 68 bundled packages, Chakra 3.28 and its `@ark-ui`/`@zag-js` subtree included.
- **`index.html`:** only the hashed bundle file name changes.

**F2 visual comparison** (`visual-review.html`, `F2/compare-screens-vs-F0.md`): **no screen differs from F0**, in pixels or in any computed style. The two expected visual deltas are present in the build but change no computed value in this app.
- **D-19:** the built CSS differs (`F2/css-diff-vs-F0.diff`, prettier-normalized). The changes are reordered declarations, `transparent` → `#0000`, the `color-scheme` lowering variables (only used by `light-dark()`, which is absent), vendor-prefix normalization and keyword case. All of them preserve computed values in Chromium.
- **D-24:** Chakra 3.37 changes the `outline` button's border to `var(--outline-color, var(--outline-color-legacy))` (layer `recipes`).
  - The app's unlayered `button { border: 1px solid transparent; … }` in `src/index.css` beats every cascade layer.
  - So the computed border of the Cancel button stays `rgba(0, 0, 0, 0)` in F0 and F2 (`F2/d24-cascade-probe.json`, from `probe_layers.mjs`).
  - The same unlayered rule causes the pre-existing white-on-light buttons.
- **Positive control:** adding `body{letter-spacing:.5px}` to the F2 stylesheet changed all 8 screens (0.30–0.75 % of pixels, plus box changes in the styles). The capture detects even a one-line CSS change. The stylesheet was restored afterwards, and its hash matched the build again (`F2/positive-control.md`).

**Human review of the screenshot comparison:** accepted by the owner on 2026-10-05 (answer: "go"; Phase 2 exit criterion).

### Phase 2 CI (draft PR #114)

Measured on `plugin/uplift-basictodo/phase-2` at `7304a79` against `plugin/uplift-basictodo/base`, 2026-10-05. The workflows ran on **Node 24.21.0**, and e2e downloaded Chrome for Testing 153.0.8010.12 (chromium v1243), the same versions as the local measurements.

| Workflow | Result | Duration |
|---|---|---|
| Frontend CI | ✅ | 29 s |
| End-to-End Tests (Playwright 1.63) | ✅ | 75 s |
| Python Application CI (tests, lint, coverage comment) | ✅ | 56 s |
| CodeQL (actions / python / js-ts) | ✅ | 59 s |
| Dependency review | ✅ | 24 s |
| Super-Linter | ❌ | 257 s |

About 4¼ minutes of wall clock (256 s), 578 s of runner time.

**Exit criterion "frontend and e2e green": met ✅.**

Super-Linter fails for the reasons recorded for Phase 1 above:
- legacy files;
- analysis documents (markdownlint, textlint);
- jscpd on generated evidence. The F0 and F2 style captures are identical by design.

Phase 2's own new Python (`baseline/frontend/bundle_modules.py`, `compare_screens.py`) is not yet black/flake8-formatted for super-linter's configuration.

## CI pipeline (Phase 3)

_Recorded 2026-10-05 for Phase 3 (brief §3). Branch `plugin/uplift-basictodo/phase-3`, cut from the `phase-2` tip `e3ffd22`._

**Before state (`e3ffd22`, venv `target-lock`, clean tree):**
- pytest: 456 passed, 1 skipped, identical per test to `pytest-target-lock.tsv`;
- mypy: 3 errors, install-order dependent (D-04, see "mypy" above);
- CI: draft PR #114, see "Phase 2 CI" above;
- super-linter **v9.0.0**, run locally (Podman, image pinned by digest) with the old v4 configuration as far as v9 accepts it: 20 linters report findings. The list is in `baseline/ci/superlinter-v9-inventory-e3ffd22.txt`.

**Commits:**

| Commit | Subject |
|---|---|
| `2ee51ba` | ci: actions on their node24 majors, exact pins (D-25, D-26) |
| `d2e284b` | ci: super-linter v9 (D-27) |
| `f02e74d` | style(ci): format the workflows with Prettier (super-linter v9) |
| `fecb197` | ci: Dependabot codeql-action group, as on main (#108) |
| `36765cb` | build: drop the SQLAlchemy stub packages and the [mypy] extra (D-04) |
| `a268203` | fix(types): mypy clean without the SQLAlchemy stubs (D-05) |
| `f97dd49` | style: black 26.5.1 and flake8 7.3.0 for the Python files changed since base |
| `a752cf3` | test(e2e): drop the unused catch binding (ESLint) |
| `4112dc5` | ci: gates per Q9 |
| `5c46f21` | ci: dependency review gets pull-requests: write at job level (SEC-005) |

The commits from D-04 to `a752cf3` were each checked before they were committed, on the change on top of its parent. The table below and "Behaviour at the tip" are measured on committed, clean trees.

### mypy and the Q12 exit check

| State | venvs | mypy |
|---|---|---|
| Before (`e3ffd22`), both stub packages installed | `target-lock` | 3 errors; 3 or 5 depending on install order (D-04) |
| D-04: both stub packages and the `[mypy]` extra removed | two fresh venvs | 5 errors in each, the same 5: three stale `type: ignore`s and two instance-only attribute accesses (`repository.py`) |
| D-05 | two fresh venvs | 0 in each |
| **Tip `4112dc5`** | **two fresh venvs, each synced with CI's `uv sync --locked --all-extras --dev`** | **0 in each** ("no issues found in 35 source files"); `uv pip freeze` identical; mypy 2.4.0, SQLAlchemy 2.0.54, no stub package |

The mypy configuration references no SQLAlchemy plugin (checked before D-04, per Q12). The `[mypy]` extra only pulled in mypy, a direct dev dependency anyway. D-05 replaces the two instance-only accesses with `to_do_table.c.id`; the generated SQL text and bind parameters are identical.

### Behaviour at the tip

Measured on `4112dc5` (clean tree, venv synced as above). `5c46f21` changes only `dependency-review.yml`.
- **pytest:** 456 passed, 1 skipped, coverage 83.98 %. Identical per test to `pytest-target-lock.tsv` (457 rows, 0 changed). Provenance: `baseline/provenance-pytest-4112dc5.json`; nothing loaded from outside the tree.
- **Golden master:** 0 of 83 responses differ from the Phase 3 before-capture (`e3ffd22`) and from the committed Phase 1 target capture `target-lock.json` (`0df26b9`). Capture: `baseline/target-lock-4112dc5.json`.
- **Frontend on Node 24.21.0:** `npm ci`; `tsc -b` exit 0; vitest 13/13, identical per test to F2; `dist/` byte-identical to F2; ESLint 0 errors; `npm audit` 0; e2e 13/13.

### Gates (Q9)

| Gate | Before | After (`4112dc5`) |
|---|---|---|
| mypy | `continue-on-error: true` | **blocking**, 0 errors |
| ESLint | `continue-on-error: true`, 1 error (`e2e/smoke.spec.ts:89`) | **blocking**, 0 errors |
| Type check | `npx tsc --noEmit` on `tsconfig.json`, which has `"files": []` and only references: **0 project files** checked | **`npx tsc -b`**: builds `tsconfig.app.json` (31 project files) and `tsconfig.node.json` (1) |
| pylint | `cd backend && pylint app/*py`: 3 modules | `pylint backend/app`: 15 modules; still `--exit-zero` (report-only) |

No pylint configuration exists, so changing the working directory changes nothing but the scope.

**Positive control per blocking gate.** Each gate got a deliberate error and was run with the command its CI step runs. Logs: `baseline/ci/positive-controls.txt` and `baseline/ci/superlinter-control-9272b59.txt`.

| Gate | Deliberate error | Command | Exit | Reported | Revert |
|---|---|---|---|---|---|
| mypy | `MYPY_CONTROL: int = "a"` appended to `backend/app/config.py`, uncommitted | `uv run mypy backend/app/` | **1** | `config.py:28: error: Incompatible types in assignment … [assignment]` | `git checkout --`; `git status` clean; exit 0 |
| ESLint | `const eslintControl = 1;` appended to `frontend/src/App.tsx`, uncommitted | `cd frontend && npm run lint` | **1** | `28:7 error 'eslintControl' is assigned a value but never used @typescript-eslint/no-unused-vars` | as above; exit 0 |
| `tsc -b` | `export const tscControl: number = "a";` appended to `frontend/src/App.tsx`, uncommitted | `cd frontend && npx tsc -b` | **2** | `src/App.tsx(28,14): error TS2322: Type 'string' is not assignable to type 'number'.` | as above; exit 0 |

With the same deliberate type error, the **old** step `npx tsc --noEmit` exits **0**.

**super-linter v9.** With `VALIDATE_ALL_CODEBASE=false`, super-linter only sees committed changes, so this control is a commit on a throwaway branch:
- **Error:** `SUPERLINTER_CONTROL = 'black wants double quotes'` appended to `backend/app/main.py`, which is already black-clean and in the diff. Committed as `9272b59` on `tmp/superlinter-control`, off `4112dc5`.
- **Command:** `run_superlinter.sh plugin/uplift-basictodo/base`, with the workflow's env: `VALIDATE_ALL_CODEBASE=false`, `DEFAULT_BRANCH=plugin/uplift-basictodo/base` (its value on a PR into base).
- **Exit 2.** Only PYTHON_BLACK fails (`would reformat /tmp/lint/backend/app/main.py`); the other 14 linters pass.
- **Revert:** `git branch -D tmp/superlinter-control`. Afterwards `git branch --list 'tmp/*'`, `git branch -r --list 'origin/tmp/*'` and `git ls-remote --heads origin 'tmp/*'` (exit 0) are all empty. The branch was never pushed. The phase-3 tip lints green (below).

A failing command only turns the workflow red if the step does not swallow it. Parsed from the YAML at `4112dc5`: neither the mypy step, the type-check step nor the ESLint step, nor their jobs, carries `continue-on-error`. The only `continue-on-error` left in the workflows is `false`, on the pytest step.

### super-linter v9 (D-27)

Configured as on `main` (decision "Konfig wie main"), with the reasons as YAML comments in `super-linter.yml`. Findings of the before-run and how they were resolved:

| Linter (before-run findings) | Resolution |
|---|---|
| PYTHON_BLACK, PYTHON_FLAKE8 (the uplift's legacy and new Python files) | **Fixed** in `f97dd49` with black 26.5.1 and flake8 7.3.0 |
| PYTHON_MYPY (`repository.py`) | **Fixed** by D-04/D-05 |
| CHECKOV CKV2_GHA_1 (`codeql.yml`, `super-linter.yml`: no top-level permissions) | **Fixed** in `d2e284b`: top-level `contents: read` |
| YAML_PRETTIER (workflows) | **Fixed** in `f02e74d` (Prettier 3.9.8 from the image; parsed YAML identical) |
| PYTHON_PYLINT, JSCPD, PYTHON_ISORT | **Disabled, as on `main`:** pylint runs as its own report-only job; jscpd scans the whole codebase and flags pre-existing duplication; the repository has no isort configuration |
| PYTHON_RUFF, PYTHON_RUFF_FORMAT | **Disabled:** no ruff configuration; ruff's formatter conflicts with black. black and flake8 stay the Python style gates |
| BIOME_FORMAT, BIOME_LINT, TYPESCRIPT_PRETTIER (and the JS/JSX/TS ES and Prettier linters) | **Disabled:** the frontend is linted by its own ESLint configuration, now a blocking gate in `frontend.yml`; the repository has no Biome or Prettier configuration |
| MARKDOWN, MARKDOWN_PRETTIER, NATURAL_LANGUAGE, JSON_PRETTIER, HTML_PRETTIER, SHELL_SHFMT, SPELL_CODESPELL | **Excluded by path:** all their findings are in `analysis/` (modernization evidence and tools) or `UPLIFT_NOTES.md`, plus codespell on `uv.lock`. `FILTER_REGEX_EXCLUDE` covers these and both lockfiles. super-linter matches absolute paths, hence `(^\|/)` |

**Result at `5c46f21`:** exit 0, 15 linters run and pass (`baseline/ci/superlinter-5c46f21.txt`). black and mypy each see exactly the 10 Python files changed since base, and no file under `analysis/` or `UPLIFT_NOTES.md` is linted. Trivy scans the whole tree, including the screenshot runner's lockfile under `analysis/`, and reports 0 findings.

Tools: `baseline/ci/run_superlinter.sh <base-branch> <log> [image]` runs super-linter in Podman on a clean clone of HEAD, with the env read from the workflow file. `baseline/ci/superlinter_findings.py <log>` groups a log's findings by linter and mentioned path.

## Change log

_Empty. Phase 5 records each intentional behaviour change here, with its Q6 row ID._
