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

- **F1's `dist/` change** is fully attributed. JS modules changed only in the bumped react/react-dom 19.3.0 and @tanstack 5.104.1. All app modules and the other 68 packages are identical, and the CSS is byte-identical.
- **D-19 and D-24 do not show** in this app. The CSS diff is serialization only. The Chakra outline token loses to the unlayered legacy `button` rule in `src/index.css`. A positive control proves that the screenshot setup detects a one-line CSS change.

## Residual and deferred

- **ESLint 10** and other lint-plugin majors are not part of Phase 2. ESLint stays 9.39.5, and its one pre-existing error (`e2e/smoke.spec.ts:89`, unused `e`) is unchanged.
- **TypeScript 7** is blocked by typescript-eslint's peer range (D-22).
- **Native `resolve.tsconfigPaths`** instead of vite-tsconfig-paths: optional, not done.
- **The unlayered `button` rules in `src/index.css`** (a Vite template leftover) override Chakra and make the buttons barely legible. This is pre-existing and left as is; it is a candidate for a later UI pass.
- **Visual review by the owner:** accepted on 2026-10-05.
