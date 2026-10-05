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
| `uv sync` installs the project editable; the finder points at the checkout that was synced | In another worktree, a **script** entry point (`backend/scripts/init_db.py`) imports `backend.app` from that other checkout. `python -m …` and pytest resolve `cwd` first. Set `PYTHONPATH=$PWD` (the scripts below do), and let each process record what it loaded (`provenance.py`). Do not rely on a separate probe. |
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
