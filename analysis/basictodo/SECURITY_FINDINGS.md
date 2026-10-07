# Security findings: basicToDo (Phase 5 hardening pass)

_`/modernize-harden basictodo`, 2026-10-07. Brief §3 Phase 5, entry criterion._

**Scanned tree:** the uplifted code at `7e6ae13` (the `phase-4` tip), not `legacy/basictodo`. That is the code Phase 5 changes, so the patch applies to it directly. It was scanned in a read-only worktree, which stayed clean.

**Route:** the security-auditor subagent route, not the 15–50-agent workflow. Both are the owner's choice.
- **Finder:** one `security-auditor`. It ran pip-audit, npm audit and bandit, plus probes in a scratch directory.
- **Refutation:** the owner's rule is _"one independent refutation pass for every Critical/High finding (separate agent, no access to the finder's reasoning) before a fix is written."_ **The finder reported no Critical or High finding, so no refutation agent was started.** I checked the four Medium findings against the code myself (column "Checked" below).
- **Patch review:** a second `security-auditor` gave one verdict per hunk (section "Patch review").

**Secrets:** no hardcoded credentials in the tree, and none in the history (pattern scans over all 257 commits). `analysis/.gitignore` quarantines `SECRETS.local.md` and `*.local.patch`; `git check-ignore` confirms. Neither file was needed.

## Scorecard

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 4 |
| Low | 17 |
| Informational | 2 |

**Top CWE categories:**
- CWE-770 (resource limits: F-05, F-06, F-19);
- CWE-20 (input validation: F-11, F-13);
- CWE-532 (sensitive data in logs: F-09, F-10);
- CWE-346 (Host/origin: F-03);
- CWE-1327 (bind address: F-02).

## Findings

**Scope key:**
- **Q6/Q8 item:** decided for this pass in brief §7.
- **accepted:** explicitly accepted in Q7, Q8 or Q8a.
- **residual:** outside the decided scope and below Medium. These are listed in `UPLIFT_NOTES.md`, not fixed.

| ID | Sev | CWE | Location (`7e6ae13`) | Finding | Scope | Checked | Disposition |
|---|---|---|---|---|---|---|---|
| F-01 | Medium | 306 | `api/api.py` (all routes) | No authentication; anyone who reaches the port can read and change every todo | SEC-001, **accepted** (Q8: out of scope) | code: no auth anywhere | Accepted. Its reach shrinks with F-02 and F-03. |
| F-02 | Medium | 1327 | `main.py:11` | Binds `0.0.0.0` with `reload=True` | SEC-002 | code: `main.py:11` | **Fixed** by the patch (`settings.py`, `main.py`) |
| F-03 | Medium | 346 | `api/api.py:24-33` | No Host check (DNS rebinding); non-JSON bodies not refused with 415 | SEC-003 | code: CORS is the only middleware; pin `test_legacy_any_host_is_served` | **Fixed** by the patch (`TrustedHostMiddleware`, `require_json`) |
| F-04 | Medium | 158, 770 | `models/todo.py:19-20`, schemas without `max_length` | A NUL makes SQLite's `length()` stop, so rows of any size pass the 255 CHECK | Q6.2 (RULE-021) | pin `test_legacy_nul_bypasses_the_length_limit` (302 characters stored) | **Fixed** in the Q6.2 commit: schema validation rejects control characters (NUL included) and counts code points |
| F-05 | Low | 770 | `api/api.py:93` | `limit=-1` returns all rows; a huge `page` gives 500 | SEC-004 / Q6.4 | — | **Fixed** by the patch (`limit` 1–100, `page` 1–1,000,000) |
| F-06 | Low | 770 | `api/api.py:24` | No request body limit (a 50 MB body was read) | SEC-004 / **Q8b** | pin `test_legacy_oversized_body_is_accepted` | **Fixed** by the patch (`body_limit.py`, 16 KiB, 413). `extra="forbid"` on the schemas is not adopted: it would be a contract change nobody decided (residual). |
| F-07 | Low | 400 | `api.py` async routes, synchronous repository | Blocking DB calls on the event loop | — | — | residual |
| F-08 | Low | 117, 150 | `input_sanitizer.py:38` | Raw input in logs forges log lines and terminal escapes | SEC-010 | — | **Fixed** by the patch (`logger.py` neutralises every argument); Q6.1 also removes this call |
| F-09 | Low | 532 | `decorators.py:35,51`; `database.py:42-52` | DB errors log SQL and bound parameters | — | — | residual (only cut to 200 characters by the log filter; `hide_parameters` is outside Q8) |
| F-10 | Low | 209, 532 | `database.py:36`, `init_db.py:21` | A credential-bearing `DATABASE_URL` is echoed in errors and logs | SEC-012 | — | residual (SEC-012 is not in Q8) |
| F-11 | Low | 20, 755 | `todo_service.py:59-62`, `decorators.py:32-33` | `PUT {"title": null}` → 500; over-length → 409/500 | Q6.3 | pin `test_legacy_put_title_null_is_a_500` | **Fixed** in the Q6.2/6.3 commit |
| F-12 | Low | 184 | `input_sanitizer.py:13-15` | Keyword blocklist rejects ordinary titles and protects nothing | Q6.1 | — | **Fixed** in the Q6.1 commit |
| F-13 | Low | 20, 451 | schemas | Control and bidi characters accepted | Q6.2 | — | **Partly fixed** in the Q6.2 commit: Cc rejected as the owner decided. Cf (bidi such as U+202E) stays accepted (residual). |
| F-14 | Low | 459 | `repository.py:57-64` | Soft delete keeps content; re-creating an id gives 409 | **accepted** (Q7: RULE-008, RULE-031 kept) | — | Accepted; documented in README and API docs (Q7) |
| F-15 | Low | 538 | `.gitignore:61-62` | SQLite files not ignored; test DBs in history | SEC-014 | — | **Fixed** by the patch (`.gitignore`); history purge not done (residual; test strings only) |
| F-16 | Low | 276 | `database.py:28-34` | DB path follows the cwd; file created 0644 | SEC-014 | — | **Fixed** by the patch: path next to the package, file 0600, no chmod on directories |
| F-17 | Low | 942 | `api/api.py:29-32` | CORS with credentials and wildcard methods and headers | SEC-008 | pin `test_legacy_cors_allows_credentials_and_every_method` | **Fixed** by the patch |
| F-18 | Low | 1395 | CI `uv 0.7.16` (`python-app.yml`, `e2e.yml`) | uv advisories (see dependency table) | — | — | residual (uv stays 0.7.16 since Phase 3; `--locked` hash checks limit exposure) |
| F-19 | Low | 770 | `pyproject.toml:15` | No rate limiting; `slowapi` declared but unused | **accepted** (Q8a) | — | `slowapi` removed in Phase 5; no rate limiting in this pass |
| F-20 | Low | 778 | `logger.py:6-26` | `CustomLogger` miswired: INFO dropped, WARNING via lastResort | TD-3 | — | **Fixed** by the patch (`logger.py`) |
| F-21 | Low | 829, 200 | `api/api.py:24` | `/docs` and `/redoc` load scripts from a CDN without SRI | — | — | residual (e2e uses `/docs` as readiness probe) |
| F-22 | Info | 1188 | `playwright.config.ts:55-65` | e2e reuses a running backend locally, so cleanup can delete real todos | — | — | residual |
| F-23 | Info | — | `super-linter.yml`, `python-app.yml` | Write-scoped tokens on PR jobs; acceptable with `pull_request` | — | — | none |

**Checked and not vulnerable (finder):**
- **SQL injection:** ORM with bound parameters only, no raw SQL; bandit B608 does not fire.
- **CSRF via simple requests:** FastAPI 0.142's `strict_content_type` already returns 422 for bodies without a JSON type.
- **Cross-origin reads:** blocked by CORS.
- **Mass assignment:** `deleted`, `done` and `created_at` are ignored on create.
- **Also checked:** XSS, deserialisation, path traversal, error leakage (`debug=False`), telemetry off, React Query devtools inactive outside development.

## Dependencies

| Ecosystem | Scope | Tool | Result |
|---|---|---|---|
| Python | runtime export at `7e6ae13` (72 pins) | `pip-audit` | **No known vulnerabilities** |
| Python | all groups (97 pins) | `pip-audit` | No known vulnerabilities |
| npm | `frontend/package-lock.json` (409 packages) | `npm audit --package-lock-only` | **0** (info 0, low 0, moderate 0, high 0, critical 0) |
| CI tooling | `uv 0.7.16`, pinned in the workflows | `pip-audit --no-deps` | 5 advisories; see below |

| Package | Installed | Advisory | Fixed in |
|---|---|---|---|
| uv | 0.7.16 | PYSEC-2026-2001 / GHSA-8qf3-x8v5-2pj8 / CVE-2025-54368 | 0.8.6 |
| uv | 0.7.16 | PYSEC-2026-2295 / GHSA-v653-r55g-hcmg / CVE-2025-13327 | 0.9.6 |
| uv | 0.7.16 | GHSA-w476-p2h3-79g9 | 0.9.5 |
| uv | 0.7.16 | GHSA-pjjw-68hj-v9mw | 0.11.6 |
| uv | 0.7.16 | GHSA-4gg8-gxpx-9rph | 0.11.15 |

**bandit:** one finding, B104 (bind to all interfaces) at `main.py:11` = F-02.

## Remediation log

**Patch:** `security_remediation.patch` (shareable). It has 9 files and 16 hunks (round 2), built from `72baf56` (product code identical to `7e6ae13`). `git apply --check` passes on that tree. There are no credential findings and therefore no `security_remediation.local.patch`.

The patch is the reviewed design. The Phase 5 commits apply it hunk by hunk, each together with its tests. Any deviation is recorded here, and the final verification runs on the tip.

| Finding | Fix | Carried by |
|---|---|---|
| F-02 (SEC-002) | `BASICTODO_HOST`/`PORT`/`RELOAD`, default 127.0.0.1 without reload; empty or `*` rejected | patch: `settings.py`, `main.py` |
| F-03 (SEC-003) | `TrustedHostMiddleware` (`BASICTODO_TRUSTED_HOSTS`, default `localhost,127.0.0.1`), outermost; route dependency `require_json` on POST/PUT → 415 | patch: `api.py`, `settings.py` |
| F-05 (SEC-004) | `limit` 1–100 (Q6.4), `page` 1–1,000,000 → 422 instead of all rows or 500 | patch: `api.py` |
| F-06 (SEC-004, Q8b) | `BodyLimitMiddleware`: Content-Length > 16,384 refused unread; otherwise the body is read with counting (chunked included) and replayed; JSON 413; no handler runs for an oversized body | patch: `body_limit.py`, `api.py` |
| F-08 (SEC-010), F-20 (TD-3) | `CustomLogger` over `logging.getLogger("basictodo.<name>")`, one handler, no root propagation. A filter formats each message once: string and exception values cut at 200 characters, then controls and lone surrogates escaped in the whole message. `init_db.py` logs the URL without its password. | patch: `logger.py`, `init_db.py` |
| F-15, F-16 (SEC-014) | `*.db`, side files and `*.bak` ignored (the sample DBs stay tracked); default path next to the package. Own files are restricted to 0600: the default DB, or a DB SQLite has just created. An existing operator file only gets a warning, and a failing chmod is only reported. | patch: `.gitignore`, `database.py` |
| Test configuration | `conftest.py` allows TestClient's Host `testserver` before the app is imported; the four SEC legacy pins are replaced in the security commit | patch: `conftest.py` |
| F-17 (SEC-008) | CORS: origins from `BASICTODO_CORS_ORIGINS`, no credentials, GET/POST/PUT/DELETE, Content-Type/Accept | patch: `api.py`, `settings.py` |
| F-04, F-11, F-12, F-13 | Q6.1, Q6.2 and Q6.3 as decided | Phase 5 commits for Q6.1 and Q6.2/6.3, not the security patch |
| F-01, F-14, F-19 | accepted (Q7, Q8, Q8a) | — |
| F-07, F-09, F-10, F-18, F-21, F-22 | residual | `UPLIFT_NOTES.md` |

**Deviations in the Phase 5 commits** (each with its tests and a positive control):
- **SEC-014, R2 (security commit):** the 0600 handling lives in `backend/app/data_access/database_file.py` instead of `database.py`. Since the UTC commit (Q6.6), the engine that prepares the database at startup is the one that creates a new file, so both engines get it.
  `do_connect` creates a missing file 0600 (`O_CREAT|O_EXCL`) before SQLite opens it; the check of an existing file and its warning run at an engine's first connection. A test records the mode at the moment SQLite has opened a new file: 0600.
- **R4 (security commit):** `BASICTODO_PORT` is length-checked first; a 5,000-digit port gives `SettingsError`.
- **R1, R3 (logging commit):** the log filter catches every exception while formatting; `loggable_url()` drops the query string as well as the password. `init_db.py` logs `loggable_url(DATABASE_URL)` rather than the patch's `engine.url.render_as_string(...)`.

**Local checks of the patched tree** (before the review):
- black and flake8 clean, mypy 0;
- pytest: exactly the four SEC legacy pins flip (415, Host, CORS, body size), 504 pass;
- against real uvicorn:
  - 16,384 B → 200; 16,385 B → 413 JSON, with CORS headers for an allowed Origin;
  - 40,000 B chunked → 413; maximal valid request (6,198 B) → 200;
  - DELETE with a 20,000-B body → 413, and the row stays;
  - foreign Host → 400;
  - `text/plain` and no Content-Type → 415;
  - `limit=101` → 422.

## Patch review

### Round 1 (7 files, 12 hunks)

A second `security-auditor` reviewed the patch over the wire (uvicorn with httptools and h11) and at the ASGI level. **10 RESOLVES, 1 PARTIAL, 1 INTRODUCES-RISK.**

| Hunk | Verdict | Reason (short) |
|---|---|---|
| `.gitignore` | RESOLVES | DBs, side files and backups ignored; the sample DBs stay addable |
| `api.py` imports | RESOLVES | supporting imports |
| `api.py` settings, middleware, `require_json`, POST | RESOLVES | foreign Host 400 before any body is read; the 413 carries CORS; preflight only for the allowed origin; 415 for every non-JSON POST, nothing created |
| `api.py` PUT | RESOLVES | 415 before 422/404; GET and DELETE never 415 |
| `api.py` list bounds | RESOLVES | -1, 0, 101 and 1000 → 422; `page=1e20` was 500, now 422 |
| `body_limit.py` | RESOLVES | CL and chunked over the limit → 413 with no handler run; a lying CL is caught by counting; disconnects, websocket and lifespan unaffected |
| `database.py` imports and default path | RESOLVES ×2 | the default DB no longer follows the cwd |
| `database.py` `restrict_to_owner` | **INTRODUCES-RISK** | a failing chmod (EPERM: foreign owner, read-only or CIFS mount) broke every connection, and operator-chosen modes were reset |
| `logger.py` | **PARTIAL** | f-string messages not neutralised; `%d` broke because args became strings; double output with a configured root logger; `init_db.py` now printed the full URL, passwords included |
| `main.py` | RESOLVES | 127.0.0.1, no reloader |
| `settings.py` | RESOLVES | fails closed on empty values and `*`; nits: non-ASCII port digits, origin `null` or with a trailing slash accepted |

**Further issues from round 1:**
- the patch broke the test run (TrustedHost rejects `testserver`: 70 failed, 15 errors, coverage below 80 %);
- non-ASCII or 5,000-digit `Content-Length` raised in-process (not reachable through uvicorn, which answers 400);
- the e2e cleanup with `limit=1000` would be skipped silently, which the pagination commit covers;
- `exc_info` tracebacks are not neutralised (no call site uses them), and bidi characters pass the log filter (visual only).

**Revisions for round 2:**
- `database.py`: only own files; chmod only the default DB or a just-created empty DB; existing operator files get a warning; `OSError` is a warning, never an exception.
- `logger.py`: the message is formatted once in the filter and escaped as a whole, values keep their types, format errors are caught, no propagation.
- `init_db.py`: the URL is logged without its password.
- `body_limit.py`: ASCII digits only, more than 20 digits counts as too large, compact JSON, docstring corrected.
- `settings.py`: ASCII port digits, origins as `scheme://host[:port]`.
- `conftest.py`: `testserver` allowed.
- **Local checks:**
  - the suite without `BASICTODO_*`: exactly the four SEC pins fail, 504 pass;
  - EPERM on chmod: the connection works, with a warning;
  - an operator file stays 0664;
  - a new file gets 0600;
  - `%d` works;
  - f-strings and exception text are escaped;
  - one line per record with a configured root logger.

### Round 2 (9 files, 16 hunks)

**16 of 16 RESOLVES.** The review loop ends here, after two of the at most three rounds.

| Hunk | Verdict | Reason (short) |
|---|---|---|
| `.gitignore` | RESOLVES | DBs, `-journal`/`-wal`/`-shm` and `.bak` ignored; `baseline/db/*.db` stays addable |
| `api.py` imports, middleware, PUT, list bounds | RESOLVES ×4 | live server: foreign Host 400; `text/plain` 415; `charset=utf-8` 200; preflight without credentials; PATCH preflight 400; the 413 carries CORS; `limit=0`/`1000` 422 |
| `body_limit.py` | RESOLVES | non-ASCII digits, `+5`, `1e9` fall back to counting; 20+ digits 413 unread; chunked and DELETE over the limit 413; compact JSON |
| `database.py` imports, default path, `restrict_to_owner` | RESOLVES ×3 | operator files keep their mode (warning only); new and default DBs 0600; foreign uid and EPERM only warn, the connection works |
| `logger.py` | RESOLVES | f-strings escaped; `%d`/`%.2f` work; one handler, no double output |
| `main.py` | RESOLVES | listens on 127.0.0.1, no reloader |
| `settings.py` | RESOLVES | non-ASCII ports, `null`, trailing `/`, paths, upper-case scheme, userinfo, `file://`, `*` refused |
| `init_db.py` ×2 | RESOLVES | the URL is logged with `***` for the password |
| `conftest.py` ×2 | RESOLVES | the suite passes without `BASICTODO_*` |

**Suite of the patched tree, no `BASICTODO_*` set:** 4 failed (exactly the four SEC legacy pins), 504 passed, 1 skipped; coverage 80.45 %. black, flake8 and mypy are clean. There are no credential values and no instruction-shaped text in the patch.

**Residuals from round 2** (Low; no verdict changed). They are fixed in the Phase 5 commits as deviations from the reviewed patch, and the hardening verify on the tip checks them:

| # | Residual | Fix in Phase 5 |
|---|---|---|
| R1 | The log filter catches only `TypeError`/`ValueError`; `KeyError`, `OverflowError` or a failing `__str__` reach the caller (no current call site) | catch every exception while formatting, with a fallback message |
| R2 | SQLite creates the file 0644 before the connect hook makes it 0600 (short window; legacy was 0644 permanently) | `do_connect` creates a missing file with `O_CREAT\|O_EXCL`, 0600, before SQLite opens it; the warning about existing files comes once per engine |
| R3 | A password in the URL's query string (`?password=`) would still be logged (no Postgres/MySQL driver is installed) | log the URL without its query |
| R4 | A port with more than 4,300 digits raises `ValueError` instead of `SettingsError` | length check first |

**Not touched by the patch:** `database.py:36` echoes a rejected `DATABASE_URL` with its password (F-10/SEC-012, residual). The e2e cleanup with `limit=1000` is handled by the pagination commit.

## Verify on the tip (Phase 5)

A separate `security-auditor` checked the tip independently (product code of `47877f8`, identical at `eb178e3`). It read this document and probed the code: 216 focused tests; `init_db.py` and the server from `main.py` on 127.0.0.1; raw-socket HTTP probes; Python probes for R1–R4, the database file and the migration and backup code; `pip-audit` (59 runtime pins) and `npm audit --omit=dev`, both 0.

**Verdict: no open High or Medium finding beyond the accepted ones** (F-01/SEC-001; F-19/Q8a is the accepted Low).

| Status | Findings |
|---|---|
| FIXED | F-02, F-03, F-04, F-05, F-06, F-08, F-11, F-12, F-15 (history purge residual), F-16, F-17, F-20 |
| PARTLY FIXED | F-13: control characters rejected; bidi (Cf) still accepted, as documented |
| ACCEPTED | F-01 (SEC-001), F-14 (Q7), F-19 (Q8a) |
| RESIDUAL | F-07, F-09, F-10, F-18, F-21, F-22 |

**Probes beyond the tests:**
- A foreign Host with a 20,000-byte body gets 400, not 413, so the body is never read.
- Pipelined and keep-alive requests are each checked.
- CL+TE, a 21-digit Content-Length and `+5` get 400 from uvicorn.
- A request hidden in an unread oversized body is not processed.
- GET with a 20,000-byte body gets 413.
- A preflight from `null`, for PATCH or for a custom header gets 400.

**R1–R4: verified.**
- **R1:** every exception while formatting gives the fallback line, with one Info nit (N-3).
- **R2:** a new file exists 0600 and empty before SQLite opens it; the `-journal` is 0600; an existing 0644 file with content gets one warning per engine and keeps its mode.
- **R3:** userinfo and query passwords are rendered as `***` or dropped.
- **R4:** ports of 4,301 and 5,000 digits give `SettingsError`.

**New observations, all Informational** (none at Medium or above; residual, not fixed in this pass):

| # | CWE | Location | Observation |
|---|---|---|---|
| N-1 | 89 | `schema.py` `_rows` | Table and column names from the database's own `sqlite_master` are quoted without doubling `"`. A crafted table name gave an `OperationalError`, rollback, backup removed, `toDo` intact. Not reachable through the API; whoever can craft the file controls the data anyway. Fix: `name.replace('"', '""')`. |
| N-2 | 367 | `schema.py` `_backup` | The backup is created exclusively 0600, closed, then reopened by name. A planted symlink is refused (`SchemaError`, target untouched); only a writer of the database's directory could race the reopen, and could replace the database anyway. |
| N-3 | 755 | `logger.py` `NeutraliseMessage` | The fallback formats `repr(record.msg)`; a message object whose `__str__` and `__repr__` both raise escapes the filter. Every call site passes a string literal. Fix: a second `try` with a constant message. |
| N-4 | 150 | `init_db.py` | Exception and schema-diff text goes to stderr unescaped; it comes from the operator's database file or environment, not from API input. |
| N-5 | 346 | Starlette `TrustedHostMiddleware` | Two Host headers (the allowed one first) or an absolute-form target naming another host get 200. A browser cannot send either, so DNS rebinding is not affected; any other client that reaches the port is covered by F-01. |
