# Playbook: basicToDo same-stack uplift

_The proven recipe. Written from the Phase 1 pilot (backend, 2026-10-05) for an engineer who has not seen that session. Later phases add their own sections._

## Backend: dependency uplift with a dual-lock proof

**Proven on:** FastAPI 0.115.12 / Starlette 0.46.2 / SQLAlchemy 2.0.43 → FastAPI 0.142.2 / Starlette 1.7.0 / SQLAlchemy 2.0.54, Python 3.13 on both sides.

**Result:** branch `plugin/uplift-basictodo/phase-1`, commits `61d37da` to `0df26b9`.

**Idea:** the code barely changes and the dependencies move. So the proof is differential: the **same test suite** and the **same HTTP request sequence** run against a venv built from the old lock and one built from the new lock, and every difference is either a catalogued delta or a stop.

### Environment facts you would otherwise discover the hard way

| Fact | Consequence |
|---|---|
| `python3` is 3.14 on this machine, and `.python-version` is gitignored | Prefix every `uv` call with `UV_PYTHON=3.13`, or uv picks 3.14 |
| Local uv is 0.7.15; CI pins 0.7.16 | Locks written by 0.7.15 pass CI's `uv sync --locked` |
| `uv run` re-syncs the venv to the current `uv.lock` | Never run gates through `uv run` against a legacy venv after the lock has changed. Call `<venv>/bin/python` directly, or set `UV_NO_SYNC=1`. |
| `uv sync` installs the project editable; the finder points at the checkout that was synced | In another worktree, a **script** entry point (`backend/scripts/init_db.py`) imports `backend.app` from that other checkout; `python -m …` and pytest resolve `cwd` first. Set `PYTHONPATH=$PWD` (the scripts below do), and let each process record what it loaded (`provenance.py`), not a separate probe. |
| CI sets no `DATABASE_URL`; the app then uses `backend/todo.db` under `cwd` and `init_db.py` must run first | `run_suite.sh` reproduces exactly that |
| Not gitignored: `backend/todo.db`, `test.db`, `frontend/playwright-report/`, `frontend/test-results/` | Delete or move them after every run, or they show up in `git status` |
| pytest's `addopts` always write `backend/htmlcov` and `backend/coverage.xml` | These two are gitignored |
| e2e needs ports 8000 and 5173 free; the golden master uses 18765 | Check with `ss -ltn` first |
| `uv export` writes ANSI colour codes into its header | Use `--no-header --color never` before feeding the result to `pip-audit` |
| An in-memory SQLite engine plus `TestClient` gives every thread its own empty database | End-to-end tests need a file-backed SQLite in `tmp_path` (see `test_p0_contracts.py`) |

### Tools

All of these live in `analysis/basictodo/baseline/` and run from the repository root.

| Tool | What it does |
|---|---|
| `run_suite.sh <venv> <outdir>` | `python-app.yml`'s gates against a venv **as-is**: `init_db.py`, pytest with coverage and junit, mypy. Also writes versions and freeze. |
| `junit_table.py <junit.xml> [--diff <table.tsv>]` | Per-test outcome table. `--diff` exits 1 on any changed outcome. |
| `run_golden_master.sh <venv> <out.json> [server-log]` | Starts uvicorn on a fresh SQLite database on port 18765 and records 83 requests, with the provenance of the server and init_db processes. |
| `provenance.py`, `pytest_provenance.py` | Used by both run scripts. Each process records which tree its `backend.*` modules came from and aborts (exit 3) if any came from outside `cwd`. `provenance.py show <record.json>` prints a record. |
| `golden_master.py diff <a.json> <b.json>` | Lists every status, header, body and timestamp-basis difference. Exits 1 on any. |

### Recipe

**0. Working copy and the legacy venv**

```bash
git clone --branch plugin/uplift-basictodo/base https://github.com/HubReb/basicToDo.git modernized/basictodo-uplifted
cd modernized/basictodo-uplifted && git switch -c plugin/uplift-basictodo/phase-N
UV_PYTHON=3.13 UV_PROJECT_ENVIRONMENT=../.envs/legacy-lock uv sync --frozen --all-extras --dev
```

Keep `uv.lock` from the seed commit as `analysis/basictodo/baseline/uv.legacy.lock`.

**1. Make the suite complete before you trust it.** Here, two builder test files were named `tests_*.py` and never collected. Renaming them is a commit of its own.

**2. Pin the P0 rules with real-stack tests.** Use no mocks: real service, real repository, file-backed SQLite. Assert on the contract fields and the stored rows, not on the whole response body (the delete response carries `data: null, error: null`, for example).

**3. Record the baseline on the untouched code**, from a worktree at that SHA:

```bash
git worktree add --detach ../wt-<sha> <sha> && cd ../wt-<sha>
git diff --quiet <legacy-sha> HEAD -- backend/app backend/scripts pyproject.toml uv.lock   # must be empty
run_suite.sh ../.envs/legacy-lock <runs>/baseline
junit_table.py <runs>/baseline/junit.xml > analysis/basictodo/baseline/pytest-legacy-lock.tsv
run_golden_master.sh ../.envs/legacy-lock analysis/basictodo/baseline/legacy-lock.json
```

- Capture the golden master **twice** and diff the two captures. They must not differ, or the capture is not a usable oracle.
- Run e2e as CI does:

```bash
cd frontend && npm ci
CI=true UV_PYTHON=3.13 UV_PROJECT_ENVIRONMENT=<venv> UV_NO_SYNC=1 npx playwright test
```

**4. Manifest changes without version changes.** Commit 5 moved the dev tools to `[dependency-groups].dev`. After `uv lock` (no `--upgrade`), prove three things:
- `git diff uv.lock | grep -c -E '^[-+](version|source|sdist|wheels) '` is 0;
- a fresh `uv sync --frozen --all-extras --dev` gives the same freeze as the legacy venv;
- `junit_table.py --diff` shows 0.

**5. Prerequisites must be lock-neutral.** Before you call a new dependency a prerequisite, run `uv lock` on the **legacy** lock and read the diff. If any existing package moves, it is not a prerequisite; it belongs in the bump. `httpx2` (D-06) failed this test. Code-only prerequisites (D-07) are fine.

**6. Neutrality proof before the bump.**
- Take a worktree at the last commit before the bump.
- Its golden master against the baseline: **0 differences**.
- Its `junit_table.py --diff` against the baseline: **0 differences**.

Only then is every later difference attributable to the bump commit alone.

**7. The bump (C1), one commit.**
- In `pyproject.toml`:
  - `fastapi[standard]>=0.142.2`, `starlette>=1.3.1`;
  - advisory floors `anyio>=4.14.2`, `python-multipart>=0.0.31`, `pytest>=9.0.3`;
  - `sqlalchemy>=2.0.54,<2.1`, both runtime and dev;
  - `httpx2>=2.13.1` (dev).
- Run `UV_PYTHON=3.13 uv lock --upgrade`.
- `FastAPI(..., telemetry={"auto_configure": False})`. **Write `test_telemetry_export.py` first and watch it fail on the new lock** (the sink receives `/v1/traces` and `/v1/metrics`), then add the argument.

**8. Prove the target.**

```bash
UV_PYTHON=3.13 UV_PROJECT_ENVIRONMENT=../.envs/target-lock uv sync --frozen --all-extras --dev
run_suite.sh ../.envs/target-lock <runs>/target
junit_table.py <runs>/target/junit.xml --diff analysis/basictodo/baseline/pytest-legacy-lock.tsv
```

The only allowed `+` lines are new tests.

- Golden master from a worktree at the bump SHA, against the neutrality capture from step 6.
- **Classify every difference.** Group the diff by kind first; one header can account for most responses (D-10's `vary: Origin` touched 75 of 83).
- An unclassified difference stops the phase until the owner decides.
- Then run e2e against the target venv.
- Then `pip-audit` on `uv export --frozen --no-dev --no-hashes --no-emit-project --no-header --color never`.

### Done means

| Check | Expected (Phase 1) |
|---|---|
| `junit_table.py --diff` target vs baseline | 0 missing or changed; new tests only |
| Coverage | ≥ 80% and within 0.5 points of the baseline (83.96% → 83.96%) |
| Golden master | every difference is D-10, D-11, D-12 or D-28 |
| P0 contract tests | green on both venvs |
| Playwright | 13/13 against the target backend |
| `pip-audit`, runtime | 0 |

### Errors hit, and what resolved them

| Symptom | Cause | Resolution |
|---|---|---|
| Two golden-master captures of the same tree differ | The 307 `location` header carries a random port | Fixed port 18765 |
| Logs suddenly contain ANSI codes | `FORCE_COLOR` is set in the calling shell | The run scripts unset it and set `NO_COLOR=1 PY_COLORS=0` |
| Timestamps look identical after masking although they come from different clocks | Masking hides the clock | Store a per-path `local` / `utc` basis before masking (not the offset, so DST does not matter) |
| `httpx2` "prerequisite" changes anyio and idna on the legacy lock | It needs newer versions | Move it into the bump |
| mypy reports 5 errors in one venv and 3 in another, same tree and lock | `sqlalchemy-stubs` and `sqlalchemy2-stubs` overwrite the same file | Do not compare mypy counts until D-04 removes both packages |
| `pip-audit -r` rejects the export | ANSI codes in the uv header | `--no-header --color never` |
| P0 test with `sqlite:///:memory:` sees no tables | `SingletonThreadPool`: one database per thread, and `TestClient` runs the app in another thread | File-backed SQLite in `tmp_path` |
| `/docs` and `/redoc` differ after the bump | FastAPI changed its built-in pages | Catalogued as D-28 by owner decision |

### Not part of this recipe

Deferred on purpose, with the phase that owns each item:
- removing `slowapi` (Phase 5);
- removing the stub packages, D-03b and D-04 (Phase 4);
- the mypy fixes for D-05;
- Python 3.14;
- every Q6 behaviour fix (Phase 5).

## Frontend: Node and toolchain uplift with a visual proof

**Proven on:** Node 20/22 + Vite 6.4 / Vitest 4.0 / TypeScript 5.8 / Chakra 3.28 / Playwright 1.57 → Node 24 + Vite 8.3 / Vitest 5.0 / TypeScript 6.0 / Chakra 3.37 / Playwright 1.63.

**Result:** branch `plugin/uplift-basictodo/phase-2`, commits `2dba37a` to `e0fc04c`.

**Idea:** the same chain as the backend, with screenshots and computed styles as the behavioural oracle:
- F0, the legacy dependencies, on the old and the new Node;
- prerequisites, which must not change anything;
- **F1**, a same-major refresh, which must not change anything visible;
- **F2**, the majors, where every visual difference needs a delta and evidence.

### Environment facts

| Fact | Consequence |
|---|---|
| The distribution's `nodejs24` (24.14.1) is below jsdom 30's floor (`^24.15.0`) | Install Node with `analysis/basictodo/env/install_node24.sh`. It downloads a nodejs.org build, verifies the GPG signature against pinned release keys and the SHA-256, and installs to `$HOME/.local/opt` without sudo. The system Node stays the default. |
| Node 22 (system) and Node 24 must coexist | Choose per command via `PATH="<node24>/bin:$PATH"`, and record `node -v` / `npm -v` in every run |
| npm 11.19 holds back non-allow-listed install scripts | Expected. Only esbuild's postinstall was held (F1), and Vite 8 drops esbuild |
| The backend allows only the origin `http://localhost:5173`, and the bundle calls `http://localhost:8000` | Screens need exactly these ports. In Chromium, map `localhost` to `127.0.0.1` (`--host-resolver-rules`) |
| The legacy `src/index.css` has unlayered global `button` rules | They beat Chakra 3's cascade layers. Any Chakra button style change is invisible until those rules go |

### Tools (`analysis/basictodo/baseline/frontend/`, run from the repository root)

| Tool | What it does |
|---|---|
| `run_frontend_suite.sh <node-bin> <outdir> [backend-venv]` | The `frontend.yml`/`e2e.yml` gates on a chosen Node: `npm ci`, vitest (junit), build plus `dist/` SHA-256 and sizes, lint, `npm audit`, and Playwright e2e with the backend venv |
| `run_screens.sh <backend-venv> <outdir> <runner-dir> <node-bin>` | Serves `frontend/dist` with Python's stdlib server, starts the backend through `provenance.py`, and captures the 8 persona-flow screens |
| `capture_screens.mjs` | Uses **only** the runner's Playwright 1.63.0 and Chromium (`runner/package*.json`, installed outside `frontend/node_modules`). Writes PNG, computed styles of every rendered element and `capture.json` |
| `compare_screens.py` (`uvx --with pillow`) | Pixel share, bounding box, diff image and style changes per screen. Exit 2 if the capture setups differ |
| `bundle_modules.py list` / `diff` | Attributes a JS bundle change to modules, packages and versions through sourcemaps (`vite build --sourcemap`) |
| `probe_layers.mjs` | CSSOM probe that lists every rule matching an element, with its cascade layer |

### Recipe

1. **Runner:** `npm install` in `modernized/.tools/screens/` from `runner/package.json` (exact pins), then `npx playwright install chromium` with Node 24.
2. **F0** from a worktree at the base SHA. Run `run_frontend_suite.sh` on Node 22 **and** Node 24, plus `run_screens.sh` on each build. Capture twice and compare. Everything must be identical: per test, `dist/` hashes, e2e and screens. That separates the runtime from the dependency changes.
3. **Prerequisites** (D-17 `baseUrl`, D-18 `jest-dom/vitest`) on the legacy dependencies. Proof: everything is identical to F0.
4. **CI Node switch** (`node-version: '24'`) as its own commit, before any lockfile change.
5. **F1** with Node 24 / npm 11:
   - `npm uninstall add snippet textlint framer-motion`.
   - `npm update` over **all** lock entries except Chakra's subtree. Only direct dependencies is not enough; transitive advisories remain.
   - Stop rule: screens and styles identical. Every `dist/` difference must be traced to a bumped package with `bundle_modules.py`.
6. **F2:** `npm install` the majors (vite + plugin-react together; vitest + jsdom + jest-dom; typescript ~6.0.3; Chakra ^3.37; @playwright/test ^1.63; vite-tsconfig-paths ^6.1). Then a fresh `npm ci`, build, vitest, e2e on Playwright 1.63 and `npm audit`.
7. **Visual proof:**
   - `compare_screens.py F0 F2`.
   - For each difference, give the evidence: the prettier-normalized CSS diff for D-19, the recipe diff plus `probe_layers.mjs` for D-24.
   - Run a **positive control** (one deliberate CSS change must show up) whenever the result is "no difference".
   - `visual-review.html` for the human review.

### Done means (Phase 2)

| Check | Expected |
|---|---|
| vitest and e2e per test against F0 | identical; e2e on Playwright 1.63 |
| `npm ci` on a fresh `node_modules`, npm 11 | ✅ |
| `npm run build` (`tsc -b` + `vite build`) | ✅ |
| `npm audit` | 0 |
| Screens F0 → F2 | every difference attributed with evidence; here, none |
| Human review of `visual-review.html` | accepted |

### Errors hit, and what resolved them

| Symptom | Cause | Resolution |
|---|---|---|
| `ERR_PACKAGE_PATH_NOT_EXPORTED` when reading `playwright/package.json` | Not an exported package path | Read the JSON from the runner's `node_modules` on disk |
| The capture waits forever for a todo title | The title shares its element with the Edit and Delete buttons, so an exact text match fails | Substring match with titles that do not contain one another. Toast titles still match exactly |
| A failing step leaves no diagnostics | A top-level `await` error in an ES module is not an `unhandledRejection` | `try`/`catch` around the flow, writing `error.png` and the browser log |
| Every app module looks "added/removed" in the bundle diff | Sourcemap paths are relative to the output directory and contain the checkout name | Key modules relative to the frontend directory |
| F1 left 11 advisories | `npm update <direct deps>` does not reach transitive packages | Update every lock entry except Chakra's subtree |
| Expected D-19/D-24 visuals do not appear | Serialization-only CSS changes, and an unlayered legacy rule that overrides Chakra's layers | Prove it: CSS diff, CSSOM layer probe, positive control |

## CI: Actions majors, blocking gates and super-linter v9

**Proven on:** GitHub Actions on node16/node20 majors with super-linter v4.10.0 → node24 majors pinned by SHA with super-linter v9.0.0.

**Result:** branch `plugin/uplift-basictodo/phase-3`, commits `2ee51ba` to `5c46f21`.

**Idea:** every CI change is checked locally before CI sees it:
- actionlint, zizmor and Prettier on the workflow files;
- super-linter itself in Podman, with the workflow's own env;
- a gate becomes blocking only after the code passes it, and only with a positive control that shows it fails on a deliberate error.

### Environment facts

| Fact | Consequence |
|---|---|
| super-linter v9 matches `FILTER_REGEX_EXCLUDE` against **absolute** paths (`/github/workspace/…`, locally `/tmp/lint/…`) | Anchor directory excludes with `(^\|/)`, not `^` |
| With `VALIDATE_ALL_CODEBASE: false`, super-linter lints the files changed in **commits** since `DEFAULT_BRANCH`. jscpd, Biome and Trivy scan the whole tree anyway | Uncommitted changes are invisible to a local run, so a super-linter control needs a commit. `DEFAULT_BRANCH: ${{ github.base_ref \|\| 'main' }}` keeps PRs into the uplift base linting only their own changes |
| Workflow YAML booleans reach the container as the strings `true`/`false`; Python's YAML loader gives `True` | The local runner lowercases them; otherwise super-linter stops with FATAL "Set … to either true or false" |
| A local run on the working tree also lints ignored files (`node_modules`, `dist`, `htmlcov`) | Lint a clean clone of HEAD, with the base branch created in it |
| super-linter pins its own black and flake8: v4.10.0 has black 22.12.0 / flake8 6.0.0, v9.0.0 has black 26.5.1 / flake8 7.3.0. black 26 reformats black 22 output | Format with the versions of the super-linter on the branch being committed to; see the pre-commit rule below |
| `frontend/tsconfig.json` has `"files": []` and only project references | `tsc --noEmit` on it checks 0 files and passes any type error; `tsc -b` checks both referenced projects |
| setup-uv has no floating major tags since v8; coverage-comment has no `@v4` | Pin every `uses:` to the release commit SHA with the exact version as a comment |
| CodeQL `init` and `analyze` must run the same version; a split Dependabot bump fails the analyze post step ("configuration file for version 3.x, but running version 4.x") | Dependabot groups `github/codeql-action` |
| The mypy result depended on which SQLAlchemy stub package installed last (D-04) | Remove both stub packages before making mypy blocking (Q12), and prove 0 errors in two fresh venvs |

### Tools

| Tool | What it does |
|---|---|
| `baseline/ci/run_superlinter.sh <base-branch> <log> [image]` | super-linter in Podman (image pinned by digest) on a clean clone of HEAD, with the env of the workflow's super-linter step; `DEFAULT_BRANCH` becomes `<base-branch>` |
| `baseline/ci/superlinter_findings.py <log>` | Groups a log's findings by linter and mentioned path, split into `analysis/` and everything else |
| `uvx --from actionlint-py actionlint` | Workflow syntax and expression checks |
| `uvx zizmor --offline .github/workflows/ .github/dependabot.yml` | Workflow security audit (pins, permissions, credentials) |
| `podman run --rm --entrypoint sh <image> -c 'prettier --check …'` | Prettier in super-linter's own version (YAML_PRETTIER) |

### Recipe

1. **Before state:** CI of the previous phase, the local backend and frontend gates, and a local super-linter run of the **new** version on the unchanged branch. That run is the inventory of what the upgrade will flag.
2. **Actions majors** as one commit: release SHAs with version comments; download-artifact and upload-artifact together; CodeQL `init` and `analyze` on the same SHA. Check: actionlint and zizmor clean, `persist-credentials: false` and the permission blocks intact.
3. **super-linter major** as its own commit: drop removed variables; keep `DEFAULT_BRANCH` on the PR target; disable or exclude per linter, with the reason as a YAML comment next to it.
4. **Make the code pass before making the gate blocking:** D-04/D-05 for mypy, the single ESLint error, black/flake8 in the linter's versions. Formatting goes in its own commit; prove it with identical ASTs, identical pytest tables and a 0-difference golden master.
5. **Gates commit:** remove `continue-on-error`; fix the type-check command.
6. **Run `run_superlinter.sh`** until it exits 0. Triage every remaining finding: fix it in files the uplift touches anyway, or disable or exclude with a reason. Anything that needs changes outside the uplift's scope stops the phase.
7. **Positive control per blocking gate:** a deliberate error, the exact CI command, a non-zero exit, then the revert. super-linter's control is a commit on a throwaway branch that is deleted afterwards and never pushed. Also check from the parsed YAML that no step or job swallows the exit code.

### Before every commit (from Phase 3 on)

- **black and flake8, in the branch's super-linter versions** (v9: `uvx --python 3.13 black==26.5.1`, `uvx --from flake8==7.3.0 flake8` with `max-line-length = 120`, `extend-ignore = E203`), on every new or changed Python file, including tools under `analysis/`.
- **Markdown:** every line of a new or changed file is at most 400 characters.
- **Workflows:** actionlint, zizmor and Prettier as above.

### Done means (Phase 3)

| Check | Expected |
|---|---|
| Every `uses:` | pinned to a commit SHA with the exact version as a comment |
| Top-level `permissions` | read-only in every workflow; write grants only at job level |
| mypy in two fresh venvs synced like CI | 0 errors in both, identical freezes |
| pytest per test, golden master, frontend gates and e2e | identical to the before state |
| Positive controls | non-zero exit for mypy, ESLint, `tsc -b` and super-linter |
| `run_superlinter.sh` at the tip | exit 0 |
| Draft PR | all six workflows green, duration recorded |
| Gate steps in the job log | the command's own output is clean. Don't rely on the step conclusion: the Actions API reports a step with `continue-on-error: true` as success even when its command exits 1 (#114) |

### Errors hit, and what resolved them

| Symptom | Cause | Resolution |
|---|---|---|
| FATAL "Set VALIDATE_JAVASCRIPT_ES to either true or false" | YAML `false` became Python `False` | Lowercase booleans in the env file |
| Local run lints `node_modules` and `dist` | It ran on the working tree | Clean clone of HEAD |
| `^analysis/` excludes nothing | v9 matches absolute paths | `(^\|/)analysis/` |
| Checkov CKV2_GHA_1 on `codeql.yml` and `super-linter.yml` | No top-level `permissions` | Top-level `contents: read` |
| black 26 reformats files formatted with black 22 | super-linter v9 bundles black 26.5.1 | Format with the branch linter's versions |
| flake8 E501 on a `noqa` comment carrying its own reason | The reason made the line too long | Reason on comment lines above; bare `# noqa: <code>` on the reported line |
| zizmor clean, but the exit criterion "top-level read-only" failed for `dependency-review.yml` | `pull-requests: write` at workflow level | Moved to the job (`5c46f21`) |
| Dependency review and Trivy red on a docs-only commit | Advisories published after the last green run (seroval, 2026-10-05) | Compare the advisory's publish date with the last green run. If the parent package's range excludes the fixed version, use npm `overrides`, prove a lock diff limited to the advisory's packages and identical gates (`94e5c7d`) |

## Data layer: one declarative model, `sqlalchemy.Uuid`, Alembic baseline

**Proven on:** SQLAlchemy 2.0.54, with a declarative `ToDoORM` for the DDL plus an imperative `Table` mapped onto a dataclass, plus `sqlalchemy-utils`. Moved to one `MappedAsDataclass` model on a `DeclarativeBase`, `sqlalchemy.Uuid`, and an Alembic 1.20 baseline revision. SQLite only.

**Result:** branch `plugin/uplift-basictodo/phase-4`, commits `5cc9e06` to `053a4f3`.

**Idea:** the code that touches stored data changes, so the proof is about **storage**, not only behaviour:
- pin what is stored (raw, through `sqlite3`) before the change;
- keep the DDL byte-identical;
- let the old and the new code read and write the same database file in both directions.

### Environment facts

| Fact | Consequence |
|---|---|
| CI runners use UTC | A test for "`created_at` is local, `updated_at` is UTC" proves nothing there. Force a zone without DST (`TZ=Etc/GMT-5`, then `time.tzset()`) in the test, and restore it. |
| On insert, SQLAlchemy omits a column whose value is `None` if it has a default, so `func.now()` fills it; `RETURNING` sends the value back | The stored `updated_at` is the database's UTC clock, and so is the create **response**. Assert both. |
| The legacy `ToDoEntryData` dataclass declared `deleted: Mapped[bool] = mapped_column(default=False)` | Its dataclass default was the `MappedColumn` object. Storing an entry without `deleted` failed with `OperationalError: no such column: deleted` (the object is rendered as SQL). With `MappedAsDataclass`, `default=` is a real dataclass default. |
| `sqlalchemy_utils.UUIDType` converted strings; `sqlalchemy.Uuid` binds `uuid.UUID` only (`'str' object has no attribute 'hex'`) | Check every caller passes `UUID`. Here, every path is typed and the HTTP API cannot reach it. |
| The API stores an omitted description as `''`, not NULL | NULL only comes from `PUT {"description": null}`. A sample database needs both. |
| `init_db.py` imported `app.*` after putting `backend/` on `sys.path` | In a second checkout, the model came from the venv's editable install. Put the repository root on `sys.path` and import `backend.app.*`. |
| Alembic's autogenerate compare does **not** see CHECK constraints, and renders them alphabetically | Write the baseline revision by hand and compare `sqlite_master` byte for byte. |
| Alembic ≥ 1.16 reads `[tool.alembic]` from `pyproject.toml` without `alembic.ini` | `env.py` must not call `fileConfig(config.config_file_name)` or `get_main_option("sqlalchemy.url")`. Take the URL from the application at run time, with its own `NullPool` engine. |
| A test that runs Alembic on a shared connection must commit it | Use `engine.begin()`, not `connect()`. Otherwise the DDL lands (pysqlite) but `alembic_version` stays empty. |
| hypothesis with `tmp_path` inside `@given` fails the function-scoped-fixture health check | Use a module-scoped file (`tmp_path_factory`); `derandomize=True, database=None, deadline=None` keeps the per-test table stable |
| super-linter v9 lints Alembic's `script.py.mako` as Python and fails (E999); mypy then stops | Exclude that file only in `FILTER_REGEX_EXCLUDE` (`(^\|/)backend/migrations/script\.py\.mako$`); the migrations stay linted. Phase 4 did so as a scope exception (`5ffc86b`). |

### Tools (`analysis/basictodo/baseline/db/`, run as noted)

| Tool | What it does |
|---|---|
| `make_sample_db.sh <venv> <out-dir>` | From the root of the tree to run: a fresh database through `init_db.py`, then rows written through the HTTP API (`make_sample_db.py`), with provenance, a dump, `schema.json` and sha256 |
| `sample_db_roundtrip.sh <legacy-tree> <legacy-venv> <new-tree> <new-venv> <out-dir>` | The sample database read and written by both codes, each in its own process (`sample_db_io.py`, through `provenance.py`). Compares the reads, the write outcomes and every stored value's format. |
| `backend/migrations/check_baseline.py <db>` | Product tool. Before stamping, compares an existing database's `sqlite_master` with the baseline, read-only. Exits 0 on a match, 1 on a difference (with a diff), 2 if the file is missing or already versioned. |

### Recipe

1. **Before state** at the previous phase's tip: per-test pytest table, golden master, mypy, e2e.
2. **Characterization first, on the old mapping and both locks:** the stored values per rule, read raw; the DDL as a literal snapshot; round-trip properties. Name the tests that pin behaviour the phase will change on purpose, and **replace** them in the change commit rather than editing them. The per-test table then shows exactly those rows.
3. **Sample database from the untouched legacy code**, through its own API, in a worktree at the legacy SHA (`PYTHONDONTWRITEBYTECODE=1`, so the tree stays clean). Commit it with its sha256.
4. **Formatting of the touched legacy files in its own commit** (ASTs compared).
5. **The model swap:** one model whose DDL is the old DDL model's and whose insert defaults are the old imperative table's. Capture the repository's SQL (`before_cursor_execute`) before and after; it must be identical, parameters included.
6. **Alembic last:** the revision by hand; tests for `upgrade head == create_all == snapshot`, downgrade, stamp-then-upgrade as a no-op, and the CLI once in a subprocess.
7. **Both directions** with `sample_db_roundtrip.sh`, and a positive control for every new guard.

### Stamping an existing database

Since Phase 5 the application does this itself at startup (`init_db.py`, `main.py`; `backend/app/data_access/schema.py`): in one transaction it backs the file up to `<db>.pre-<revision>.bak`, checks the schema against the baseline, stamps `0001` and upgrades.
`DATABASE_URL=sqlite:///<db> python backend/scripts/init_db.py` runs exactly that. By hand, from the repository root, on the venv of this checkout:

1. Back up the database with SQLite's backup API (`sqlite3 <db> ".backup <db>.bak"`), not a file copy: changes still in a `-wal` file are not in the `.db` file.
2. `python backend/migrations/check_baseline.py <db>`. Continue **only on exit 0**. On exit 1 the database was made by an older model, for example without the CHECK constraints or with an id index; it needs its own migration, not a stamp.
3. `DATABASE_URL=sqlite:///<db> python -m alembic stamp 0001`. **Never `stamp head`** (Phase 4 did, when `0001` was the head): it would mark the data migration `0002` as done without running it.
4. `BASICTODO_LEGACY_TZ=<zone> DATABASE_URL=sqlite:///<db> python -m alembic upgrade head`, with the IANA zone the old code wrote `created_at` in (default: the system zone).
5. `DATABASE_URL=sqlite:///<db> python -m alembic current` shows `0002 (head)`.

### Done means (Phase 4)

| Check | Expected |
|---|---|
| DDL from `create_all`, `init_db.py`, `alembic upgrade head` | byte-identical to the snapshot |
| pytest per test | new tests, plus exactly the replaced rows of the intended changes |
| Repository SQL | identical, parameters included |
| Golden master | 0 of 83 against the Phase 1 target |
| Sample database | read identically by both codes; written by both; same storage format |
| mypy in two fresh venvs; `pip-audit` | 0; 0 |
| Positive controls | the DDL guard, the revision comparison and `check_baseline.py` each fail on a deliberate error |

### Errors hit, and what resolved them

| Symptom | Cause | Resolution |
|---|---|---|
| `init_db.py` in a worktree: provenance exit 3, `backend.app.models.todo` outside the tree | `app.*` import root plus the editable install of another checkout | Import root normalised (`15d0044`) |
| `python -W error -m pytest` stops with INTERNALERROR | pytest-asyncio's own configuration warning, not the application | `pytest -W error` (the application's warnings only) |
| super-linter red on `script.py.mako` (black, flake8, mypy) | The Mako template is parsed as Python | Exclude that file only (`5ffc86b`) |

## Behaviour changes and hardening: approved fixes, data migration, security

**Proven on:** the Phase 4 tip (FastAPI 0.142, SQLAlchemy 2.0.54, Alembic 1.20, React 19). The owner's Q6 fixes, a data migration of existing rows (local time → UTC), Alembic at startup, and the hardening items Q8 put in scope.

**Result:** branch `plugin/uplift-basictodo/phase-5`, commits `e791a9c` to `eb178e3`.

**Idea:** here behaviour is **meant** to change, so the proof is a **classification**: every flipped test and every changed response is traced to one commit and one decision ID, and nothing else may change.

### Environment facts

| Fact | Consequence |
|---|---|
| pysqlite commits DDL on its own, outside the transaction | For an atomic migration: `isolation_level=None` on connect and `BEGIN IMMEDIATE` on the engine's `begin` event. Alembic then runs inside that transaction (its `begin_transaction` is a no-op on a connection already in one). |
| SQLite refuses a backup from the connection that holds the write lock (`SQLITE_LOCKED`); Python's `backup()` then loops forever | Take the write lock first, then back up through a second, read-only connection (`file:…?mode=ro`). It sees what is only in the `-wal` file; a file copy does not. |
| `zoneinfo` with `fold=0` | An ambiguous time is its first occurrence; a time in the spring gap gets the offset before the change, so converting it back gives a time one hour later |
| `datetime.astimezone()` without a zone uses a fixed offset | Never use it for stored data; resolve an IANA zone (`ZoneInfo`, `ZoneInfo.from_file("/etc/localtime")`) |
| TanStack Query v5: callbacks passed to `mutate()` do not run after the component unmounted; `useMutation`'s own callbacks do | A toast for a row that an optimistic update removes belongs in the hook |
| FastAPI's default 422 handler echoes the input; an unpaired surrogate in it makes the response fail to encode (500) | A custom `RequestValidationError` handler that replaces surrogates |
| TestClient sends a chunked body as one ASGI message | Count streamed bytes with a hand-written `receive` and against a real uvicorn |
| `http.client` with an explicit `Transfer-Encoding: chunked` header sends the parts unframed unless `encode_chunked=True` | Pass it |
| SQLite creates a database file 0644 under the usual umask; a chmod at connect leaves a window | Create the file 0600 in the engine's `do_connect` hook before SQLite opens it; SQLite gives `-wal`, `-shm` and `-journal` the database file's mode |
| The Python template's `lib/` rule in `.gitignore` also ignored `frontend/src/lib/`, so a new file there was silently left out | `!frontend/src/lib/` right after the rule (the owner's call); other `lib/` directories stay ignored |
| A fresh `uv run` creates `.venv` with the lock's black (26.10), not the branch linter's 26.5.1 | Format only with `uvx black==26.5.1`; never run a formatter over the whole tree |
| super-linter lints every changed file in full | A rewritten README meets textlint's terminology ("todo", "ID", "hostnames") and Prettier; codespell checks touched files such as `.gitignore` |

### Recipe

1. **Gate A, on the unchanged tip:** extend the harness first (golden master requests for every planned change, screens by title), then capture P4. Hardening pass with a separate review. Pin each keep, and pin each planned change as `test_legacy_*`.
2. **Gate B, one commit per decision row:** formatting of touched legacy files in a `style:` commit before (ASTs compared); the change; the tests that pinned the old behaviour **replaced**, not edited; per-test table and golden master against the previous capture; every difference classified by ID in the commit message.
3. **A positive control for every new guard:** remove the guard once, run its tests, and see one fail; revert. A guard whose removal no test notices needs another test (here: the pre-create of the database file, hidden by the later chmod).
4. **Gate C, on the tip:** P4 → P5 attribution for pytest and the golden master, OpenAPI diff and `types/todo.ts`, mypy in two fresh venvs, `pip-audit`, `npm audit`, e2e, super-linter, screens with a review page, an independent hardening verify. Stop before the push.

### Startup migration rules

- Back up only after `BEGIN IMMEDIATE`, with SQLite's backup API, exclusively created (`O_CREAT|O_EXCL`, 0600); check it with `integrity_check` and row by row against the source, before anything is written; on any error roll back and delete it.
- Stamp `0001` only if `sqlite_master` equals the baseline; never `stamp head` by hand.
- A data migration that reads existing values needs a plausibility check that can stop it (here: converted `created_at` within 30 minutes of `updated_at`) and an override.
- The app's lifespan refuses a database that is not at head, so a server started without `init_db.py` cannot serve unconverted rows.

### Done means (Phase 5)

| Check | Expected |
|---|---|
| pytest per test P4 → P5 | every change attributed to a commit and a decision ID; the P0 test file byte-identical and green |
| Golden master P4 → P5 | every difference attributed; keeps unchanged |
| OpenAPI P4 → P5 | only intended changes; `types/todo.ts` matches |
| Migration | sample databases converted row by row; DST both ways; downgrade (except the gap hour); every startup path; backup checks; WAL; atomicity; wrong zone stops |
| Hardening verify on the tip | no open High or Medium beyond the accepted ones |
| mypy (two fresh venvs), `pip-audit`, `npm audit`, e2e, super-linter | 0, 0, 0, green, exit 0 |
| Screens | every difference attributed; review page for the owner's UAT |

### Errors hit, and what resolved them

| Symptom | Cause | Resolution |
|---|---|---|
| A golden master request for a large DELETE failed at P4 | Its todo was titled "Delete me", which the legacy blocklist rejected | Title "Remove me" |
| Screen 08 differed by 17 pixels between identical runs | Captured while a border animation ran | Wait for `document.getAnimations()` to finish |
| A legacy pin for a 500 raised in the test instead | TestClient re-raises server exceptions | `TestClient(app, raise_server_exceptions=False)` |
| 422 for a lone surrogate became a 500 | The default handler echoes the input, which cannot be encoded | Custom 422 handler (`_sendable`) |
| flake8 F401/F811 in API tests | Fixtures imported from another test module | A `conftest.py` that re-exports them |
| The backup probe hung | Backup from the connection holding the write lock | A second, read-only connection |
| mypy "Statement is unreachable" after `assert isinstance(dbapi, sqlite3.Connection)` | The DBAPI protocol type does not overlap `sqlite3.Connection` | `cast()` |
| `uv run black` reformatted 30 untouched files | The fresh `.venv` had black 26.10 | Reverted; `uvx black==26.5.1` on touched files only |
| `titleLength.ts` missing from `git status` | `.gitignore`'s `lib/` | `git add -f`, then the negation `!frontend/src/lib/` |
| super-linter red after the README rewrite | markdownlint MD060, Prettier, textlint terminology, codespell | Fixed in `eb178e3` |
