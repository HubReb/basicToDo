# Business Rules: basicToDo

_System: `legacy/basictodo` · Extracted 2026-10-03 by `/modernize-extract-rules` (Workflow method) · Companion: [DATA_OBJECTS.md](DATA_OBJECTS.md)_

## How this catalog was built

- **Extraction:** 4 rounds × 3 lenses (calculations, validations, lifecycle) produced **123 candidate rules**. Extraction was **stopped at the 4-round cap before it ran dry**: round 4 still found 14 new cards, so a long tail of minor rules may remain. Rounds 3–4 mostly yielded finer-grained edge cases of rules already found.
- **Citation check:** every card's `file:line` citation was checked by an independent referee agent: **123 confirmed, 0 rejected.** To test whether zero rejections meant lenient referees, 9 of the most surprising behaviours were reproduced live against the running API in this session. All of them held.
- **P0 panel:** 10 cards were nominated P0. Each was judged by two independent agents (compliance lens + fidelity lens). **4 survived**; 6 were downgraded to P1 because the panel split on criticality.
- **Consolidation:** the workflow de-duplicates only on file + exact name, so the same behaviour was often reported 2–5 times in different words. The 123 cards were consolidated into **59 rules**. Each rule's `Trace` line lists its source cards (W-### = position in `rules_workflow_result.json`). Sources, edge cases, suspected defects and SME questions from every merged card are kept.
- **Instruction-shaped content in source:** none found (0 flags).

**This is a todo app, so nothing here moves money or is regulatory.** P0 is used only for **data-integrity** rules: identity and deletion semantics. Many rules describe **current behaviour that looks like a defect**. Those carry a `Suspected defect` line, and the keep-or-fix decision belongs in `/modernize-brief`.

## Summary

**59 rules**: 7 Calculation, 23 Validation, 13 Lifecycle, 16 Policy · **2 P0**, 39 P1, 18 P2 · **21 need SME confirmation** · 31 carry a suspected defect

| ID | Rule | Category | Priority | Source | Confidence |
|---|---|---|---|---|---|
| RULE-001 | List pagination: offset formula, defaults, and unbounded page/limit inputs | Calculation | P1 | `backend/app/data_access/repository.py:92-97 (+8)` | Medium |
| RULE-002 | List 'results' count equals items on the current page, not the total | Calculation | P1 | `backend/app/api/api.py:88-91 (+1)` | High |
| RULE-003 | Title length is counted in different units by the UI (UTF-16 code units) and the database (Unicode characters) | Calculation | P1 | `frontend/src/components/todos/TodoForm.tsx:15-27, 75-76, 89 (+2)` | High |
| RULE-004 | Leading and trailing whitespace is trimmed from text fields | Calculation | P2 | `backend/app/business_logic/validators/input_sanitizer.py:41 (+3)` | High |
| RULE-005 | Empty description is stored as blank and returned as null | Calculation | P2 | `backend/app/business_logic/validators/field_validator.py:37-40 (+2)` | High |
| RULE-006 | Characters-remaining counter shown near the title limit | Calculation | P2 | `frontend/src/components/todos/TodoForm.tsx:75-77, 97-101, 75-76 (+1)` | High |
| RULE-007 | Optimistic list adjustments on create, update and delete | Calculation | P2 | `frontend/src/hooks/queries/useCreateTodo.ts:10-50 (+2)` | High |
| RULE-008 | ToDo id is a client-supplied UUID and must be unique; a duplicate is rejected as a conflict (409) | Validation | P0 | `backend/app/schemas/data_schemes/create_todo_schema.py:8-22, 9, 13-22, 9-22 (+6)` | High |
| RULE-009 | Corrupt stored ToDos are silently skipped in list results | Validation | P1 | `backend/app/business_logic/todo_service.py:77-86, 81-85, 46-51 (+1)` | High |
| RULE-010 | Soft-deleted ToDos are invisible to every read and update | Validation | P1 | `backend/app/data_access/repository.py:70-97, 70-76, 86-97 (+2)` | Medium |
| RULE-011 | Partial update changes only the fields supplied | Validation | P1 | `backend/app/data_access/repository.py:70-84 (+2)` | Medium |
| RULE-012 | Title is required and non-blank (on create, and on edit when supplied) | Validation | P1 | `backend/app/schemas/data_schemes/create_todo_schema.py:24-29 (+6)` | High |
| RULE-013 | Title and description limited to 255 characters (enforced only by the DB CHECK and the UI) | Validation | P1 | `backend/app/data_access/database.py:67-82, 72-73, 79-82 (+6)` | Medium |
| RULE-014 | SQL keyword and symbol blocklist on all title/description text | Validation | P1 | `backend/app/business_logic/validators/input_sanitizer.py:13-41, 13-15, 37-41 (+4)` | Medium |
| RULE-015 | Frontend title validation before create and edit | Validation | P1 | `frontend/src/components/todos/TodoForm.tsx:7, 15-27, 39-46, 89 (+1)` | High |
| RULE-016 | Path ID must be a well-formed UUID for get, update and delete | Validation | P1 | `backend/app/api/api.py:53-54, 62-63, 75-76 (+2)` | High |
| RULE-017 | Clients can set only id/title/description on create and title/description/done on edit; other fields are silently ignored | Validation | P1 | `backend/app/schemas/data_schemes/update_todo_schema.py:7-10 (+5)` | High |
| RULE-018 | Explicit null title or done on edit causes a server error | Validation | P1 | `backend/app/business_logic/todo_service.py:55-64 (+4)` | Medium |
| RULE-019 | Description can be cleared on edit; explicit null and blank are stored differently | Validation | P1 | `backend/app/business_logic/todo_service.py:59-64 (+5)` | High |
| RULE-020 | Any UUID version, including the all-zero (nil) UUID, is accepted as a ToDo id | Validation | P1 | `backend/app/schemas/data_schemes/create_todo_schema.py:9-22 (+3)` | Medium |
| RULE-021 | An embedded NUL character bypasses the 255-character limit on SQLite | Validation | P1 | `backend/app/data_access/database.py:79-82, 33 (+2)` | High |
| RULE-022 | Same blank-title rule is rejected with 422 on create but 400 on edit (two-layer validation) | Validation | P1 | `backend/app/schemas/data_schemes/create_todo_schema.py:24-29 (+5)` | High |
| RULE-023 | Invalid edits are silently accepted when the same request marks the todo done | Validation | P1 | `backend/app/business_logic/todo_service.py:53-62, 88-98 (+1)` | High |
| RULE-024 | The done flag accepts loosely typed values such as 'yes', 'on', '1' and 1 | Validation | P1 | `backend/app/schemas/data_schemes/update_todo_schema.py:10 (+3)` | Medium |
| RULE-025 | Web UI does not pre-check the server's blocked words and symbols | Validation | P1 | `frontend/src/components/todos/TodoForm.tsx:15-27 (+3)` | High |
| RULE-026 | The server accepts line breaks and tabs inside titles, but the web UI edits titles on a single line | Validation | P1 | `backend/app/business_logic/validators/input_sanitizer.py:37-41 (+5)` | Medium |
| RULE-027 | Input checks run before the existence and duplicate checks (400/422 beats 404/409) | Validation | P1 | `backend/app/business_logic/todo_service.py:53-68, 39-43, 54-66, 89-93 (+6)` | High |
| RULE-028 | An empty list is a valid list response (contradicts test comments) | Validation | P2 | `backend/app/schemas/api_responses/get_list_to_do_response.py:13-21 (+3)` | High |
| RULE-029 | Duplicate ToDo titles are permitted | Validation | P2 | `backend/app/data_access/database.py:72, 93 (+2)` | High |
| RULE-030 | 'Blank title' is judged by different whitespace rules in the UI and the server, and invisible titles are accepted | Validation | P2 | `frontend/src/components/todos/TodoForm.tsx:15-20, 50 (+4)` | High |
| RULE-031 | Delete is a soft delete: row kept, flagged deleted, not restorable | Lifecycle | P0 | `backend/app/data_access/repository.py:53-68, 72-74, 86-97, 53-60 (+2)` | High |
| RULE-032 | Marking done (PUT done=true) takes precedence and discards other edits in the same request | Lifecycle | P1 | `backend/app/business_logic/todo_service.py:53-57, 88-98, 55-57 (+1)` | High |
| RULE-033 | Done flag has no state guard: re-marking done or reopening is always allowed | Lifecycle | P1 | `backend/app/business_logic/todo_service.py:53-68, 55, 59-68, 55-68, 54-57, 89-98 (+2)` | High |
| RULE-034 | New ToDo initial state and server-local creation timestamp | Lifecycle | P1 | `backend/app/business_logic/builders/todo_entry_builder.py:19-34, 26-34, 30 (+2)` | Medium |
| RULE-035 | Last-updated timestamp: set by the DB clock (UTC) at insert, never refreshed on change | Lifecycle | P1 | `backend/app/data_access/repository.py:70-84, 77-80, 45-51 (+6)` | Medium |
| RULE-036 | Failed create/edit keeps the input and offers a toast Retry that resends the request unchanged (skipping validation) | Lifecycle | P1 | `frontend/src/components/todos/TodoForm.tsx:48-72, 87, 54-72 (+4)` | High |
| RULE-037 | New todos must start not-deleted, but the model's default for 'deleted' is not a boolean (masked by the builder) | Lifecycle | P1 | `backend/app/models/todo.py:8-18 (+2)` | Medium |
| RULE-038 | Completing a todo records no completion time (or deletion time) | Lifecycle | P1 | `backend/app/business_logic/todo_service.py:88-98 (+5)` | High |
| RULE-039 | The README roadmap's todo lifecycle differs from what the code implements | Lifecycle | P1 | `README.md:104-118 (+3)` | Medium |
| RULE-040 | Inline edit lifecycle: View -&gt; Edit -&gt; View; editing hides Delete; Cancel discards (even mid-save) | Lifecycle | P2 | `frontend/src/components/todos/TodoItem.tsx:12-35, 11-37, 29-35 (+6)` | Medium |
| RULE-041 | Create-form submission lifecycle: input locked while saving, cleared on success, kept on failure | Lifecycle | P2 | `frontend/src/components/todos/TodoForm.tsx:39-72, 81-90 (+1)` | High |
| RULE-042 | No one can add todos while the list is loading or has failed to load | Lifecycle | P2 | `frontend/src/components/todos/TodoList.tsx:8-47 (+1)` | High |
| RULE-043 | A rendering crash replaces the whole app with a 'Something went wrong' page that shows the raw error | Lifecycle | P2 | `frontend/src/components/errors/ErrorBoundary.tsx:14-55 (+1)` | High |
| RULE-044 | UI overwrites description with a fixed placeholder | Policy | P1 | `frontend/src/components/todos/TodoForm.tsx:48-52 (+2)` | High |
| RULE-045 | Web UI only ever shows the first 10 ToDos, and never shows done status | Policy | P1 | `frontend/src/components/todos/TodoList.tsx:9, 26-45, 26-46 (+4)` | High |
| RULE-046 | UI delete: confirmation prompt, success toast before the server confirms, silent reappearance on failure | Policy | P1 | `frontend/src/components/todos/TodoDeleteButton.tsx:13-33, 13-32, 13-31 (+4)` | Medium |
| RULE-047 | Business outcome to HTTP status mapping | Policy | P1 | `backend/app/api/api.py:40-91 (+1)` | High |
| RULE-048 | Todo list visibility: active todos only, done included, unordered | Policy | P1 | `backend/app/data_access/repository.py:92-97 (+2)` | High |
| RULE-049 | No purge path: soft-deleted ToDos are kept forever (hard delete is unreachable and works only on active rows) | Policy | P1 | `backend/app/data_access/repository.py:21-23, 62-68, 86-90 (+2)` | Medium |
| RULE-050 | Failed requests are retried once automatically, reusing the same client-generated id | Policy | P1 | `frontend/src/config/queryClient.ts:11-13, 3-15 (+10)` | Medium |
| RULE-051 | Any caller may read, edit, complete or delete any todo (no ownership or authorization check) | Policy | P1 | `backend/app/api/api.py:22-29, 40-91 (+2)` | Medium |
| RULE-052 | Concurrent edits: last write wins with no conflict detection | Policy | P1 | `backend/app/data_access/repository.py:70-84 (+4)` | High |
| RULE-053 | UI treats the ToDo list as fresh for 5 minutes and does not refetch on tab focus | Policy | P2 | `frontend/src/config/queryClient.ts:3-10, 3-15 (+4)` | Medium |
| RULE-054 | User-facing errors read 'API Error &lt;status&gt;: &lt;detail&gt;' and never say which rule failed | Policy | P2 | `frontend/src/services/api/client.ts:12-20, 58-70, 58-73, 12-21 (+7)` | High |
| RULE-055 | API response envelope: success flag plus payload on success, bare detail on failure | Policy | P2 | `backend/app/schemas/api_responses/api_response.py:8-12 (+5)` | High |
| RULE-056 | API responses always report deleted = false | Policy | P2 | `backend/app/schemas/data_schemes/todo_schema.py:22-25 (+3)` | High |
| RULE-057 | Result toasts, including the Retry offer, disappear after 5 seconds of active page time and cannot be dismissed manually | Policy | P2 | `frontend/src/hooks/useToast.ts:12-22 (+2)` | Medium |
| RULE-058 | No request-rate limit or quota on creating todos, even though a rate-limiting library is declared | Policy | P2 | `pyproject.toml:19 (+2)` | Low |
| RULE-059 | The design doc's SUCCESS/FAILURE response status is not implemented | Policy | P2 | `documentation/backend.puml:22-25, 44-66, 68, 75-78 (+2)` | High |

## Calculation rules (7)

### RULE-001: List pagination: offset formula, defaults, and unbounded page/limit inputs
**Category:** Calculation  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:92-97`, `backend/app/business_logic/todo_service.py:77-86`, `backend/app/api/api.py:88-91, 88-90`, `backend/app/data_access/database.py:20-35, 33-34`, `backend/tests/test_api/test_list_to_do.py:191-289`, `frontend/e2e/global-setup.ts:8`, `frontend/e2e/smoke.spec.ts:18`, `frontend/e2e/todo-crud.spec.ts:6`, `frontend/e2e/todo-validation.spec.ts:6`  
**Plain English:** The ToDo list is returned one page at a time. The number of records skipped is (page - 1) x page size, only non-deleted ToDos count, and the defaults are page size 10 and page 1.  
**Specification:**  
  Given 25 active (non-deleted) ToDos and 3 soft-deleted ToDos in the store  
  When  GET /todo?limit=10&page=3 is called  
  Then  skip = (3 - 1) x 10 = 20, so ToDos #21-#25 come back (5 items). Deleted ToDos are left out before the offset is applied. With no parameters, limit=10 and page=1, so ToDos #1-#10 come back.  
**Parameters:** default limit = 10 (api.py:89, todo_service.py:78, repository.py:92); default page = 1; offset = (page - 1) * limit; filter deleted = false; no upper cap on limit; no ORDER BY clause  
**Edge cases handled:** page=0 gives skip = -limit, a negative OFFSET. SQLite treats a negative offset as 0, so page 0 returns the same rows as page 1; page=-1 with limit=10 gives skip=-20, which also behaves like page 1 on SQLite; limit=0 returns an empty list (results=0); limit=-1 means no limit on SQLite, so every active ToDo comes back in one call; limit=10000 is accepted and not capped; There is no ORDER BY, so page contents follow storage order (rowid/insertion order on SQLite). Order is not guaranteed on PostgreSQL/MySQL; Neither the API nor the service validates limit or page. Tests at backend/tests/test_api/test_list_to_do.py:191-290 accept either 200 or 422, which shows the intended behavior was never decided; A negative limit means no limit in SQLite; limit=1000 is accepted (the e2e cleanup relies on this). There's no cap to protect against large reads.; A negative limit combined with page &lt; 1 produces a positive skip. For example limit=-5&page=0 silently skips the first 5 rows.; list_todos (api.py:88-91) maps no exceptions, so any repository failure, including integer overflow, becomes a generic 500.; If DATABASE_URL points at PostgreSQL or MySQL (allowed by database.py:33), negative LIMIT/OFFSET values raise database errors, so the same request returns 500 instead of data. This comes from engine knowledge and was not run.; The API tests at test_list_to_do.py:191-289 mock the service and accept either 200 or 422 ('Should either cap or reject'), so the real arithmetic is never tested and the intended policy is undecided.; The e2e cleanup code (global-setup.ts:8, smoke.spec.ts:18, todo-validation.spec.ts:6) depends on limit=1000 meaning 'everything', i.e. on there being no page-size cap.; Because results equals the rows returned, limit=-1 is currently the only way to get a total count of active todos.; limit=-1&page=3 gives offset -2, which becomes 0, so all rows are returned and page is ignored; PostgreSQL and MySQL URLs are allowed (database.py:33) and reject a negative LIMIT/OFFSET. The service wraps that as a repository error, and the list endpoint has no error mapping, so the client gets a bare 500; Every out-of-range test accepts either 200 or 422, so no intended policy is written down; With more than 1000 ToDos, the e2e cleanup leaves records behind  
**Suspected defect:** limit and page have no bounds. Negative or zero values quietly fall back to database-specific behavior, and limit=-1 dumps the whole table. With no sort order, pages can overlap or skip items on non-SQLite databases. / There is no bounds validation. Page &lt;= 0 behaves like page 1, a negative limit removes the cap, a negative limit with page 0 skips rows, 64-bit overflow returns 500, and results change if the configured database engine changes. The SQLite outcomes were confirmed by running the same LIMIT/OFFSET arithmetic against an in-memory SQLite database. The SQLAlchemy layer itself was not run. / A negative limit acts as 'return everything' and bypasses pagination. The outcome also depends on the database backend: SQLite returns all rows, while PostgreSQL fails with a 500.  
**Confidence:** Medium — limit=-1 returned all rows; a huge page gave 500 (reproduced live); SME: What are the valid ranges for page and limit (for example page &gt;= 1, 1 &lt;= limit &lt;= 100)? Should out-of-range values be rejected with 422 or clamped? What sort order should the list use (created_at ascending or descending, title)? | What are the allowed ranges for page and limit (for example page &gt;= 1 and 1 &lt;= limit &lt;= 100), and what should happen when they're out of range? | What are the allowed ranges for limit and page (for example limit 1-100, page &gt;= 1), and should out-of-range values be rejected with 422 or clamped? Does any consumer rely on limit=-1 or very large limits to fetch everything?  
**Trace:** W-001, W-038, W-110, W-115

### RULE-002: List 'results' count equals items on the current page, not the total
**Category:** Calculation  
**Priority:** P1  
**Source:** `backend/app/api/api.py:88-91`, `backend/app/schemas/api_responses/get_list_to_do_response.py:10-21`  
**Plain English:** The 'results' number in the list response is how many ToDos are on this page. It is not the total number of ToDos.  
**Specification:**  
  Given 25 active ToDos  
  When  GET /todo?limit=10&page=1 is called  
  Then  results = 10 (len of the returned page), not 25. For page=3, results = 5.  
**Parameters:** results = len(todo_entries) after invalid rows are skipped  
**Edge cases handled:** If stored rows fail schema validation and are skipped, results drops below the page size (for example 9 instead of 10); An empty page gives results=0 and todo_entries=[]. The response schema only rejects null, not an empty list  
**Confidence:** High — citation confirmed by an independent referee; SME: Do consumers need a total count (and total pages) for paging? If so, the rewrite needs a separate total field, because the current 'results' is a page count.  
**Trace:** W-002

### RULE-003: Title length is counted in different units by the UI (UTF-16 code units) and the database (Unicode characters)
**Category:** Calculation  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoForm.tsx:15-27, 75-76, 89`, `frontend/src/components/todos/TodoEditForm.tsx:20-32, 73-74, 83, 90-94`, `backend/app/data_access/database.py:79-82`  
**Plain English:** Both sides enforce a '255 character' title limit, but the screen counts each emoji or other non-BMP character as 2 while the database counts it as 1. So the UI limit is stricter than the server's, and a todo with a server-valid title can become impossible to edit in the UI.  
**Specification:**  
  Given A todo whose title is 200 copies of the emoji U+1F389, created directly through POST /todo. The database CHECK length(title) &lt;= 255 sees 200 characters and accepts it.  
  When  The user clicks Edit in the web UI and then clicks Save without changing anything  
  Then  The edit form computes title.length = 400 and shows '-145 characters remaining' (255 - 400; the hint shows whenever remaining &lt; 50). Save is refused with 'Todo title cannot exceed 255 characters' and the Save button disables until the user types. In the create box, maxLength=255 stops input at 127 such emoji (254 code units), even though the server would accept up to 255.  
**Parameters:** MAX_TITLE_LENGTH = 255, counted in UTF-16 code units (JS String.length and the HTML maxLength attribute), hardcoded separately in TodoForm.tsx:7 and TodoEditForm.tsx:6. Database CHECK: length(title) &lt;= 255 and length(description) &lt;= 255, counted in Unicode code points (SQLite length()). Near-limit hint threshold: remaining &lt; 50.  
**Edge cases handled:** Verified: 200 x U+1F389 gives Python len = 200, SQLite length() = 200, JS .length = 400; 255 emoji insert successfully into the CHECK-constrained table; 256 plain ASCII characters are rejected; The remaining-characters counter uses the untrimmed length (item.length) while validation uses the trimmed length, so leading or trailing spaces lower the counter but are not counted against the limit; Combining sequences (for example 'e' + U+0301) count per code point in both systems, so there is no discrepancy for them; An HTML input whose initial value is longer than maxLength is not truncated: the user can delete characters but not add any; The UI never shows a description length counter because it always sends a fixed placeholder  
**Suspected defect:** The UI and the server use different definitions of 'character'. Users who rely on emoji or other non-BMP characters (an explicitly tested use case, see backend/tests/test_data/constants.py:54-60) get a lower limit in the UI, and titles valid on the server cannot be re-saved from the edit form. The rewrite should pick one counting unit (code points or grapheme clusters) and use it in every layer.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-093

### RULE-004: Leading and trailing whitespace is trimmed from text fields
**Category:** Calculation  
**Priority:** P2  
**Source:** `backend/app/business_logic/validators/input_sanitizer.py:41`, `backend/app/schemas/data_schemes/create_todo_schema.py:29`, `backend/app/schemas/data_schemes/todo_schema.py:34-49`, `frontend/src/components/todos/TodoForm.tsx:50`  
**Plain English:** Titles and descriptions are stored and returned without leading or trailing spaces. Spaces, tabs, and line breaks inside the text are kept.  
**Specification:**  
  Given A title of ' Wash dishes ' and a description of ' Read to p.223 '  
  When  the ToDo is created or updated  
  Then  They are stored and returned as 'Wash dishes' and 'Read to p.223'. 'Line1\nLine2' is kept as is.  
**Parameters:** Python str.strip() / JS String.trim()  
**Edge cases handled:** Whitespace-only text trims to '', which fails the required-title rule. For description, '' is returned as null  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-012

### RULE-005: Empty description is stored as blank and returned as null
**Category:** Calculation  
**Priority:** P2  
**Source:** `backend/app/business_logic/validators/field_validator.py:37-40`, `backend/app/business_logic/builders/todo_entry_builder.py:29`, `backend/app/schemas/data_schemes/todo_schema.py:42-49`  
**Plain English:** Description is optional. If it is missing or blank it is saved as an empty string, and the API always shows it as null.  
**Specification:**  
  Given POST /todo with id and title 'Wash dishes' and no description  
  When  the ToDo is created  
  Then  The stored description is '' (not NULL), and the response shows description: null  
**Parameters:** validate_optional returns '' when the sanitized value is None or empty; the output schema maps any falsy description to None  
**Edge cases handled:** A description of ' ' becomes '' when stored and null in the response; On update, an explicit {description:null} skips validation and stores NULL, which is also returned as null. Stored values can therefore be '' or NULL while the API shows null for both; The description still goes through the SQL keyword blocklist; On update, an explicit description null is written as NULL (the column is nullable), while "" is written as an empty string. Both are returned as null.; On edit, explicit description:null stores NULL rather than ""  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-013, W-026, W-057

### RULE-006: Characters-remaining counter shown near the title limit
**Category:** Calculation  
**Priority:** P2  
**Source:** `frontend/src/components/todos/TodoForm.tsx:75-77, 97-101, 75-76`, `frontend/src/components/todos/TodoEditForm.tsx:73-74, 90-94`  
**Plain English:** While typing a title, the user sees how many characters are left once fewer than 50 of the 255 remain.  
**Specification:**  
  Given A user has typed a 210-character title  
  When  the form re-renders  
  Then  remaining = 255 - 210 = 45, so '45 characters remaining' is shown. At 205 characters remaining = 50 and nothing is shown, because the threshold is strictly less than 50.  
**Parameters:** MAX_TITLE_LENGTH = 255; near-limit threshold: remaining &lt; 50 (title length &gt;= 206); hidden when the field is empty or an error is displayed  
**Edge cases handled:** The counter uses the raw, untrimmed length, but validation uses the trimmed length, so padding spaces count against the counter but not against the limit; Input maxLength=255 means remaining never goes below 0 through typing; The hint is hidden while an error message is showing or when the box is empty  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-017, W-043

### RULE-007: Optimistic list adjustments on create, update and delete
**Category:** Calculation  
**Priority:** P2  
**Source:** `frontend/src/hooks/queries/useCreateTodo.ts:10-50`, `frontend/src/hooks/queries/useDeleteTodo.ts:10-40`, `frontend/src/hooks/queries/useUpdateTodo.ts:11-48`  
**Plain English:** The screen updates right away, before the server answers: a new ToDo goes to the top and the count goes up by 1, a deleted ToDo is removed and the count goes down by 1, and an edited ToDo shows the new values with the current time. On failure the previous list is restored, and the list is always refetched afterwards.  
**Specification:**  
  Given The cached list shows results=4 with 4 ToDos  
  When  the user creates 'Call mom'  
  Then  The cache immediately shows 'Call mom' first, with results=5, done=false, created_at=now. If the server rejects it, the cache goes back to the 4-item list, and in every case the list is refetched.  
**Parameters:** create: results + 1, prepend; delete: results - 1, filter by id; update: merge fields and set updated_at = now; rollback to snapshot on error; invalidate ['todos'] when settled  
**Edge cases handled:** Optimistic order (newest first) differs from server order (storage order), so items jump after the refetch; Only the limit=10/page=1 cache entry is adjusted; The optimistic description is null when not supplied, but the UI always supplies 'not implemented yet'; The new item shows at the top, but after the refetch it moves to the server's order, and may drop off if there were already 10 or more  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-020, W-063

## Validation rules (23)

### RULE-008: ToDo id is a client-supplied UUID and must be unique; a duplicate is rejected as a conflict (409)
**Category:** Validation  
**Priority:** P0  
**Source:** `backend/app/schemas/data_schemes/create_todo_schema.py:8-22, 9, 13-22, 9-22`, `backend/app/business_logic/builders/todo_entry_builder.py:19-27, 21-27, 23-27`, `backend/app/business_logic/decorators.py:31-32`, `backend/app/api/api.py:40-50, 45-46`, `frontend/src/components/todos/TodoForm.tsx:48-52, 48-49`, `backend/app/data_access/repository.py:45-51`, `backend/app/business_logic/validators/uuid_validator.py:16-24`  
**Plain English:** The client creates the ToDo's identifier (a UUID) and sends it. A create request without a valid UUID is rejected, and reusing an existing id is reported as a conflict.  
**Specification:**  
  Given A ToDo with id 7c1e...-09 already exists  
  When  POST /todo with id 7c1e...-09 and title 'Another'  
  Then  The primary-key violation raises an IntegrityError, which is returned as 409 'ToDo already exists'. A missing or non-UUID id returns 422 from request validation.  
**Parameters:** id type UUID (frontend generates uuid v4); primary key on id  
**Edge cases handled:** The id is still taken after a soft delete, so recreating it returns 409; Every IntegrityError on create (including the 255-character CHECK violation) is reported as 409 'already exists', not only duplicate ids; GET, PUT, and DELETE path ids must parse as UUIDs or FastAPI returns 422 before the service runs (api.py:53-54,62-63,75-76; uuid_validator.py:16-24); The server never generates an id. The ORM's default=uuid.uuid4 is never used because the builder requires payload.id; Soft-deleted rows keep their ID, so a deleted todo's ID can never be reused; The decorator maps ANY IntegrityError (NOT NULL or CHECK constraint failures too) to 'already exists'; The frontend's mutation retry (retry: 1, queryClient.ts:11-13) reuses the same ID. If the first attempt reached the server but the response was lost, the retry gets 409 and the UI reports failure even though the todo exists.; A missing id gives HTTP 422 from the schema. The builder also guards id None with 'Invalid payload: id is required' (HTTP 400).; The nil UUID 00000000-0000-0000-0000-000000000000 is accepted (UUID objects are always truthy); The server never generates IDs, even though the unused ORM table declares default=uuid4; If a create succeeds but the response is lost, the automatic retry (queryClient retry=1) or the toast's Retry button resends the same id and gets 409  
**Confidence:** High — citation confirmed by an independent referee; SME: Should the server generate ToDo ids instead of trusting client-supplied UUIDs? Should a duplicate id be told apart from other integrity failures? | Should the modernized system keep client-assigned IDs (which enables idempotent retries but lets clients choose keys), or move to server-generated IDs?  
**Trace:** W-014, W-028, W-027, W-052

### RULE-009: Corrupt stored ToDos are silently skipped in list results
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:77-86, 81-85, 46-51`, `backend/app/schemas/data_schemes/todo_schema.py:34-67`  
**Plain English:** When the list is built, any stored ToDo that fails the output rules (blank title, missing created_at, bad id) is left out of the response and logged as a warning. The request does not fail.  
**Specification:**  
  Given A page of 10 stored ToDos where one row has title ' ' (whitespace only)  
  When  GET /todo?limit=10&page=1 is called  
  Then  9 ToDos come back with results=9. The bad row is skipped and the log says 'Invalid DB entry skipped'.  
**Parameters:** Output rules: title non-empty after trim; created_at not null; id a valid UUID; empty description becomes null  
**Edge cases handled:** The skipped row still uses up a slot in the offset/limit window, so the page holds fewer items than limit and the row is never shown on any page; A single-ToDo GET of the same corrupt row is not skipped. ToDoSchema.model_validate raises, which surfaces as a 500 (get_todo endpoint, api.py:53-59); The page then returns fewer than limit items even though more rows exist  
**Confidence:** High — citation confirmed by an independent referee; SME: Should corrupt records be hidden quietly, or reported or repaired? Is it acceptable that a list page can hold fewer items than requested?  
**Trace:** W-003, W-059

### RULE-010: Soft-deleted ToDos are invisible to every read and update
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:70-97, 70-76, 86-97`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`, `backend/app/api/api.py:53-91`  
**Plain English:** Once a ToDo is deleted, it no longer appears in lists, cannot be fetched by id, and cannot be edited or marked done. All of these act as if it does not exist.  
**Specification:**  
  Given A ToDo with id 3f2b...-a1 that has deleted=true  
  When  GET /todo/3f2b...-a1, PUT /todo/3f2b...-a1 {title:'X'}, or PUT {done:true} is called  
  Then  Each call returns 404 'ToDo not found', and GET /todo leaves the item out  
**Parameters:** filter: deleted IS FALSE on get_to_do_entry (lines 88-90), update_to_do (lines 72-74), get_all_to_do_entries (lines 95-97)  
**Edge cases handled:** Creating a new ToDo with the same id as a soft-deleted one still hits the primary-key conflict and returns 409 'ToDo already exists', even though GET returns 404 for that id; The id of a deleted todo cannot be reused (see the 'Client-assigned identity' card)  
**Confidence:** Medium — SME: Criticality: the two-judge P0 panel split on whether this guards data integrity. Confirm P0 vs P1. P0 panel split on whether this moves money / is regulatory (Faithful: yes. I read repository.py:70-97 and checked how the service and API use it. All three repository methods filter on `deleted.is_(False)`: update_to_do at lines 72-74, get_to_do_entry at 88-90 and get_all_to_do_entries at 95-97. Each path ends where the card says it does: - GET /to… (full judge reasoning in rules_workflow_result.json) | Is there a business need to restore (undelete) todos, or to let an administrator see deleted items?  
**Trace:** W-005, W-047

### RULE-011: Partial update changes only the fields supplied
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:70-84`, `backend/app/business_logic/todo_service.py:59-68, 53-68`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`  
**Plain English:** An update changes only the fields present in the request. Fields left out keep their stored values, and a field explicitly sent as null is set to null.  
**Specification:**  
  Given A ToDo with title 'A' and description 'D'  
  When  PUT /todo/{id} with {title:'B'}  
  Then  The title becomes 'B' and the description stays 'D'. PUT {description:null} clears the description, and the API returns it as null.  
**Parameters:** model_dump(exclude_unset=True); updatable fields: title, description, done  
**Edge cases handled:** PUT {} with an empty body changes nothing and returns the current ToDo, or 404 if it is missing or deleted; PUT {title:null} skips title validation (service only validates when title is not None), then tries to store a NULL title against a NOT NULL column. That raises an IntegrityError, which is mapped to ToDoAlreadyExistsError, which the update endpoint does not catch, so the client gets a 500; Title and description values go through the sanitizer and trim first (see the sanitizer and required-title rules); An empty body {} changes nothing and returns 200 with the unchanged todo; An unknown or soft-deleted ID gives HTTP 404; Explicit {title: null} skips validation but writes NULL into the NOT NULL title column. That raises IntegrityError, which becomes ToDoAlreadyExistsError, and update_todo in api.py doesn't catch it, so the result is HTTP 500.; Extra fields such as id in the body are ignored by the schema  
**Suspected defect:** Sending an explicit null title gives an unhandled 500 instead of a 400 validation error. / updated_at is never set on update (no assignment and no onupdate anywhere in backend/app), although tests mock it as being set. Explicit null title produces a 500 instead of a 400.  
**Confidence:** Medium — SME: Should an explicit null title be rejected with 400 'title is required'? Should clients be allowed to clear the description by sending null?  
**Trace:** W-008, W-036

### RULE-012: Title is required and non-blank (on create, and on edit when supplied)
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`, `backend/app/business_logic/validators/field_validator.py:29-35`, `backend/app/business_logic/builders/todo_entry_builder.py:28`, `backend/app/business_logic/todo_service.py:59-60`, `frontend/src/components/todos/TodoForm.tsx:15-27`, `frontend/src/components/todos/TodoEditForm.tsx:20-32`, `backend/app/api/api.py:69-70`  
**Plain English:** Every ToDo needs a title that is not empty after leading and trailing spaces are removed, both when it is created and when its title is changed.  
**Specification:**  
  Given A user submits a ToDo  
  When  the title is ' ' (spaces only)  
  Then  Create: the request schema rejects it with 422 ('title must not be null.'). Update: the service rejects it with 400 'Bad request' (internally 'Invalid payload: title is required'). Frontend: 'Todo title cannot be empty' is shown and nothing is sent.  
**Parameters:** blank = empty after strip()  
**Edge cases handled:** The same blank title gets different HTTP codes: 422 on create (Pydantic request validation) and 400 on update (service validation); A missing title on create returns 422; The frontend edit form disables Save while an error is displayed (TodoEditForm.tsx:96-102); A missing or blank title fails at schema level with HTTP 422, not 400; If the schema were bypassed, the service-level FieldValidator would still raise 'Invalid payload: title is required', which maps to HTTP 400; A title that becomes empty after sanitizer trimming is rejected at service level; On edit, leaving out title keeps the current title; The same rule returns different status codes on create (422) and edit (400); Explicit JSON null for title skips validation (payload.title is None), but the null is still written. See the partial-update rule.; Title validation is skipped completely when done=true, because the mark-as-done path runs first  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-009, W-024, W-053, W-025

### RULE-013: Title and description limited to 255 characters (enforced only by the DB CHECK and the UI)
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/data_access/database.py:67-82, 72-73, 79-82`, `backend/app/main.py:9-10`, `backend/scripts/init_db.py:15-19`, `backend/app/business_logic/decorators.py:31-32`, `frontend/src/components/todos/TodoForm.tsx:7, 22-24`, `frontend/src/components/todos/TodoEditForm.tsx:6, 27-29`, `backend/app/api/api.py:45-46, 62-72`  
**Plain English:** Titles and descriptions may be at most 255 characters. The UI blocks longer input, but the backend relies only on a database CHECK constraint, and a violation comes back as a misleading 'already exists' error.  
**Specification:**  
  Given An API client (not the UI) sends a title of 300 characters  
  When  POST /todo is called  
  Then  No API-level check runs. The DB CHECK 'length(title) &lt;= 255' fails at commit with an IntegrityError, which is mapped to ToDoAlreadyExistsError and returned as 409 'ToDo already exists'. In the UI, the input's maxLength=255 stops typing at 255 characters, and the trimmed-length check (&gt; 255) is a second guard.  
**Parameters:** MAX_TITLE_LENGTH = 255 (frontend, both forms); CHECK title_length_check length(title) &lt;= 255; CHECK description_length_check length(description) &lt;= 255; String(255) columns  
**Edge cases handled:** The same overflow on PUT raises ToDoAlreadyExistsError, which the update endpoint does not catch, so the client gets a 500; The CHECK constraints exist only on the ToDoORM DDL model (Base.metadata, created by main.py and init_db.py). The imperative mapping used for reads and writes (database.py:89-100) declares no constraints. If the schema was created any other way, nothing enforces the limit, because SQLite ignores VARCHAR length; The frontend sends a fixed description, so the description limit can only be reached through the API; The constraint only exists if the table was created from Base.metadata (ToDoORM). The imperatively mapped to_do_table (database.py:89-99) has no CHECK constraints.; On PostgreSQL or MySQL an over-length VARCHAR raises DataError rather than IntegrityError, which maps to ToDoRepositoryError and HTTP 500; SQLite length() counts characters, while the frontend counts UTF-16 code units, so the limits differ for emoji; The UI shows an 'N characters remaining' hint when fewer than 50 characters remain  
**Suspected defect:** Overlong text returns 409 'ToDo already exists' on create and 500 on update, instead of a 400/422 validation error. The limit depends on how the database schema was created. / A length violation on create is reported as a duplicate (409 'ToDo already exists'), and on edit as a 500.  
**Confidence:** Medium — a 300-character title returned 409 'ToDo already exists' (reproduced live); SME: Is 255 characters the real business limit for both title and description? Should the API check it explicitly and return a clear validation error? | Should the API validate the 255-character limit itself and return 400/422 with a clear message?  
**Trace:** W-010, W-029, W-055

### RULE-014: SQL keyword and symbol blocklist on all title/description text
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/validators/input_sanitizer.py:13-41, 13-15, 37-41`, `backend/app/business_logic/validators/field_validator.py:29-40`, `backend/tests/test_validators/integration/test_input_sanitizer_integration.py:89-93, 141-159`, `backend/tests/test_validators/unit/test_input_sanitizer.py:139-147`, `backend/tests/test_data/constants.py:48-52, 26`  
**Plain English:** Any title or description containing certain punctuation (;, --, /*, */) or certain whole words, matched without regard to case (including everyday words like 'or', 'create', 'update', 'delete', 'select', 'drop'), is rejected as a suspected SQL injection.  
**Specification:**  
  Given A user creates a ToDo with title 'Buy milk or bread'  
  When  POST /todo is called  
  Then  The request is rejected with 400 'Bad request' because the whole word 'or' matches. 'Update resume', 'Create slides', 'Drop off kids', 'Select a gift', and 'Eggs; milk' are rejected too. 'This was updated yesterday' and 'ORDERED pizza' are accepted because the keyword must be a whole word.  
**Parameters:** Case-insensitive regex. Blocked tokens anywhere in the text: '--', ';', '/*', '*/'. Blocked whole words: xp_cmdshell, drop, delete, insert, update, exec, execute, union, select, shutdown, create, alter, rename, truncate, declare, or  
**Edge cases handled:** The check runs on the raw value, before trimming. The trimmed value is returned; A null value passes through as null, and the optional description becomes ''; Non-string values are turned into strings ('123', 'True') and logged as a warning; Single and double quotes, newlines, tabs, unicode, and emoji are allowed; The same check applies to description on create and update, but not on the mark-done path; The frontend has no matching check, so users only see a generic 'API Error 400: Bad request' toast; Tests (backend/tests/test_data/constants.py:6-52) pin this behavior, including rejecting '1=1 OR 1=1'; Whole-word matching means 'updated', 'ordered' and 'selection' pass, while 'or', 'update', 'create', 'select', 'delete', 'drop' and 'rename' fail; Semicolons are rejected anywhere, so ordinary punctuation like 'Groceries; pharmacy' fails; None passes through as None, and empty or whitespace-only input becomes an empty string; The rejected raw input goes into the exception message and the warning log, but the API client only ever sees the generic 'Bad request'; Not applied on the mark-done path, where title and description in the request are ignored; The integration test named 'time-based injection' (test_input_sanitizer_integration.py:89-93) passes only because its payload contains ';' and '--'. WAITFOR on its own is accepted.; MySQL '#' comments, '||' concatenation, and apostrophes or double quotes are all allowed.; A hyphen, apostrophe or accented letter next to a keyword still counts as a word boundary, so 'Re-create' and "x OR'1'='1" are rejected.; The rejection reason (which token matched) is only logged. The caller just gets 'Bad request'.; 'Re-create' and 'Pre-select' are blocked, while 'Recreate' and 'Preselect' are allowed; A cron expression such as '*/5' and a Markdown rule '---' are blocked; A keyword at the very start or end is blocked ('DROP this idea', 'Please DROP'); Full-width or look-alike Unicode letters (for example 'ＳＥＬＥＣＴ') are not matched  
**Suspected defect:** The blocklist rejects ordinary English task titles (any use of 'or', 'create', 'update', 'delete', 'select', 'drop', 'rename', 'alter', or a semicolon). Data access already uses parameterized ORM queries (repository.py), so the filter adds no injection protection and causes many false rejections. / A security filter is being used as a business validation. It rejects common English todo titles ('Create slides', 'Call mom or dad', 'Update resume', 'Drop off parcel'), even though the data layer already uses parameterized ORM queries. A rewrite should decide on purpose whether to keep this. / Common English words ('or', 'update', 'delete', 'create', 'select') block ordinary todos. Queries are already parameterized through the ORM, so this blacklist mostly hurts real users rather than adding protection. / The filter blocks common to-do verbs and conjunctions (update, create, delete, select, execute, drop, or) yet lets real injection syntax through. Storage already uses ORM-bound parameters (repository.py:70-97), so the filter adds no real protection and mainly rejects legitimate titles. The exact regex was run in memory against every example above. / The blocklist adds no protection beyond the ORM's parameterized queries but rejects legitimate user text, and the test data checks only one harmless phrase, so false positives go untested.  
**Confidence:** Medium — 'Buy milk or bread', 'Update CV', 'Pay rent -- urgent', 'Call mom; dad' -> 400; 'select_all', 'delete2', 'Re-check *.log files' -> 200 (reproduced live); SME: Should the rewrite keep this keyword blocklist, given that it rejects common task wording? Or can it be dropped in favor of parameterized queries, keeping only explicit length and format rules? | Is rejecting natural-language titles that contain words like 'or', 'update', 'create', 'delete', 'select', 'drop' or a semicolon intended behavior that must be preserved, or was it a security over-reach that the new system (using parameterized queries) should drop? | Is it acceptable that ordinary words such as 'or', 'update', 'create', 'select' and 'drop', and the symbols ';', '--' and '/*', are forbidden in ToDo text? Or should the rewrite rely on parameterized queries and drop the blocklist?  
**Trace:** W-011, W-023, W-054, W-111, W-117

### RULE-015: Frontend title validation before create and edit
**Category:** Validation  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoForm.tsx:7, 15-27, 39-46, 89`, `frontend/src/components/todos/TodoEditForm.tsx:6, 20-32, 44-49, 83, 101`  
**Plain English:** The web UI won't submit a todo whose trimmed title is empty or longer than 255 characters. The input box can't hold more than 255 characters, and Save stays disabled while an error is shown.  
**Specification:**  
  Given The user types " " in the 'Add a todo item' box (or clears the title in the edit form)  
  When  The user presses Enter (or clicks Save)  
  Then  No API call is made, the message 'Todo title cannot be empty' appears with a red border, and in the edit form Save is disabled until the user types again (typing clears the error)  
**Parameters:** MAX_TITLE_LENGTH = 255 (duplicated in TodoForm.tsx:7 and TodoEditForm.tsx:6); message 'Todo title cannot exceed 255 characters'  
**Edge cases handled:** The submitted title is trimmed (item.trim()); The over-255 branch can't normally be reached because the input has maxLength=255; The frontend doesn't check the backend SQL keyword blocklist  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-030

### RULE-016: Path ID must be a well-formed UUID for get, update and delete
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/api/api.py:53-54, 62-63, 75-76`, `backend/app/business_logic/todo_service.py:47, 72`, `backend/app/business_logic/validators/uuid_validator.py:16-24`  
**Plain English:** Single-todo operations only accept a UUID-shaped identifier in the URL.  
**Specification:**  
  Given A request GET /todo/abc123  
  When  The API receives it  
  Then  FastAPI rejects it with HTTP 422 before the service runs. If the service is called directly with an invalid string, UUIDValidator raises ToDoValidationError ('Invalid UUID: ...').  
**Parameters:** UUID format  
**Edge cases handled:** The update path in the service never calls uuid_validator itself and relies on FastAPI typing; GET maps only ToDoNotFoundError, so any other service error on GET becomes HTTP 500  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-031

### RULE-017: Clients can set only id/title/description on create and title/description/done on edit; other fields are silently ignored
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`, `backend/app/data_access/repository.py:77-78, 70-84`, `backend/app/api/api.py:62-72, 40-44`, `backend/app/schemas/data_schemes/create_todo_schema.py:8-11`, `backend/app/business_logic/builders/todo_entry_builder.py:26-34`, `backend/app/business_logic/todo_service.py:55-68`  
**Plain English:** An update can change only the title, description and done flag. The id, deletion flag, created_at and updated_at cannot be changed through the API.  
**Specification:**  
  Given Todo X has created_at 2026-10-03T09:15 and deleted=false  
  When  The client sends PUT /todo/X {created_at: "2020-01-01T00:00:00", deleted: true, id: "00000000-0000-0000-0000-000000000001"}  
  Then  All three fields are ignored, nothing changes, and the response is HTTP 200 with the unchanged entry  
**Parameters:** TodoUpdateScheme fields: title, description, done (all optional)  
**Edge cases handled:** Only fields that are explicitly present are applied. Omitted fields keep their current values; A misspelled required field fails only indirectly. {"id":..., "titel":"x"} gets 422 because title is missing, not because 'titel' is unknown.; There is no way through the API to import historical todos with their original status or creation time.; Update requests behave the same way (unknown fields are ignored), as already catalogued for the update schema.; deleted=true on create is ignored; A wrong-case 'Title' leaves title missing, so the request fails with 422; Unknown business fields such as 'priority' are dropped silently; PUT {} on a soft-deleted or unknown id returns 404, because the repository lookup filters out deleted rows (repository.py:72-76); {"deleted": false} cannot restore a soft-deleted todo: it returns 404; {"done": false} alone is not a no-op: it reopens the todo  
**Suspected defect:** Typos in optional fields cause silent data loss with a success response. Clients that think they can create a todo already marked done get no warning. / A misspelled optional field (for example 'descripton') is lost silently while the response reports success.  
**Confidence:** High — citation confirmed by an independent referee; create with done/deleted/created_at -> 200, all three ignored (reproduced live); SME: Should unknown or server-owned fields on create be rejected with 422, so client mistakes like a misspelled 'descripton' surface, or is silently dropping them intended?  
**Trace:** W-051, W-113, W-116, W-101

### RULE-018: Explicit null title or done on edit causes a server error
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:55-64`, `backend/app/data_access/repository.py:77-78`, `backend/app/data_access/database.py:72, 77`, `backend/app/business_logic/decorators.py:31-32`, `backend/app/api/api.py:62-72`  
**Plain English:** Sending null for title or done skips validation and tries to write NULL to a required column. The resulting database error is mapped to 'already exists', which the edit endpoint does not handle, so the client gets a 500.  
**Specification:**  
  Given Active todo X  
  When  The client sends PUT /todo/X {title: null} or PUT /todo/X {done: null}  
  Then  NOT NULL violation -&gt; IntegrityError -&gt; ToDoAlreadyExistsError -&gt; not caught by the update route -&gt; HTTP 500. By contrast, PUT /todo/X {description: null} clears the description and returns 200  
**Parameters:** title NOT NULL; done NOT NULL; description nullable  
**Edge cases handled:** done:null does not trigger the done path because `if payload.done` is false, so it goes through the normal edit path  
**Suspected defect:** The update route does not map ToDoAlreadyExistsError, and null values bypass the title validation.  
**Confidence:** Medium — SME: Should explicit null for title or done be rejected with 400/422?  
**Trace:** W-056

### RULE-019: Description can be cleared on edit; explicit null and blank are stored differently
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:59-64`, `backend/app/data_access/repository.py:77-78`, `backend/app/business_logic/validators/field_validator.py:37-40`, `backend/app/schemas/data_schemes/update_todo_schema.py:9`, `backend/app/data_access/database.py:73, 94`, `backend/app/schemas/data_schemes/todo_schema.py:42-46`  
**Plain English:** An edit can remove a ToDo's description by sending null or a blank string. Null is saved as a database NULL without any validation, blank is saved as an empty string, and both come back as null. An edit with no recognised fields changes nothing and still succeeds.  
**Specification:**  
  Given An active ToDo with description "Read the book until page 223."  
  When  The client sends PUT /todo/{id} with body {"description": null}  
  Then  The description column is set to NULL: validation is skipped because the value is None, and model_dump(exclude_unset=True) keeps the explicitly sent null. The response shows description: null. With {"description": " "} the sanitizer trims it to "", which is stored as an empty string and also returned as null. With {} nothing changes and the response is 200 with the ToDo unchanged.  
**Parameters:** Optional-field normalization: sanitized-or-"" (field_validator.py:40); description column nullable=True (database.py:73)  
**Edge cases handled:** A null description skips the SQL keyword blocklist completely (there is nothing to check); Clearing title the same way is not possible: an explicit null title hits the NOT NULL column and becomes a 500 (already catalogued); PUT {} returns 200 and the unchanged ToDo, so an empty update counts as success; Unknown fields such as {"deleted": true} or {"id": ...} are ignored and the response is still 200 with no change; Database rows can hold either NULL or "" for 'no description', so reports or queries on the stored data must treat both as empty; There are two physical forms of 'no description': empty string (from create or a blank edit) and NULL (from an explicit null edit). Both read back as null.; The web UI cannot clear a description, because it always sends the placeholder 'not implemented yet'. Clearing is possible only through the API.; Contrast: an explicit null title or done in the same request causes a server error. Only description supports clearing.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-066, W-078

### RULE-020: Any UUID version, including the all-zero (nil) UUID, is accepted as a ToDo id
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/schemas/data_schemes/create_todo_schema.py:9-22`, `backend/app/business_logic/validators/uuid_validator.py:16-24`, `backend/app/schemas/data_schemes/todo_schema.py:51-60`, `backend/app/api/api.py:53-54`  
**Plain English:** The server only checks that the id parses as a UUID. It does not check the version or reject the all-zero id, and alternative spellings are converted to the standard hyphenated form.  
**Specification:**  
  Given No ToDo with the nil id exists  
  When  A client POSTs /todo {"id":"00000000-0000-0000-0000-000000000000","title":"Test"}  
  Then  The ToDo is created. The 'if not value' check never fires because Python UUID objects are always truthy, and there is no version check. A second POST with the same nil id gets 409.  
**Parameters:** Id type: uuid.UUID, any version (not UUID4)  
**Edge cases handled:** A 32-hex-digit id without hyphens, or a braced/urn form, is accepted (depending on the Pydantic parser) and returned in canonical hyphenated form; The UI always generates v4 ids (TodoForm.tsx:49), so this only matters for direct API clients; A missing or null id is rejected by the field type with 422 before the 'must not be null' validator runs.; Path ids on GET/PUT/DELETE go through the same parser, so a nil-UUID todo can be read, edited and deleted like any other.; The service's UUIDValidator (400 on failure) is unreachable from the HTTP API, because FastAPI already rejects malformed path ids with 422.  
**Suspected defect:** The 'id must not be null' guards (create_todo_schema.py:16-17, todo_schema.py:54-55) can never fire: UUID objects are always truthy (checked in Python), and a null id is already rejected by the type. Re-parsing at create_todo_schema.py:18-21 and todo_schema.py:56-59 is redundant. As a result the nil UUID is accepted as a real identifier.  
**Confidence:** Medium — SME: Should the server accept only randomly generated (v4) ids and reject the nil UUID and non-canonical spellings, or is any parseable UUID acceptable?  
**Trace:** W-073, W-077

### RULE-021: An embedded NUL character bypasses the 255-character limit on SQLite
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/data_access/database.py:79-82, 33`, `backend/app/business_logic/validators/input_sanitizer.py:13-15, 37-41`, `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`  
**Plain English:** The only server-side length check is the database CHECK on length(title)/length(description). SQLite's length() stops counting at the first NUL character, so a title such as 'a' + NUL + 1,000 more letters is stored in full.  
**Specification:**  
  Given POST /todo with a valid UUID and title "a\u0000" followed by 1,000 'b' characters (1,002 characters in total)  
  When  The todo is saved to the SQLite database  
  Then  Pydantic accepts the string, strip() does not remove NUL, and the SQL blocklist regex does not match it. The CHECK sees length() = 1 and passes, so a 1,002-character title is stored and the request returns 200. By contrast, a 256-character plain title fails the CHECK and comes back as 409 'ToDo already exists'.  
**Parameters:** CHECK length(title) &lt;= 255 (title_length_check), CHECK length(description) &lt;= 255 (description_length_check). There is no application-layer length check.  
**Edge cases handled:** Verified in an in-memory SQLite database with the same CHECK: inserting 'a\x00' + 'b'*1000 succeeded and read back with length 1002; Applies equally to description and to the update path, which writes through the same table; The web UI cannot type a NUL, so this is reachable only through direct API calls; database.py:33 also allows postgresql:// URLs. PostgreSQL rejects NUL characters in text values, so these rows could not be migrated as-is  
**Suspected defect:** The 255-character business limit depends on a database quirk rather than an explicit validation. Oversized and NUL-containing rows can already exist in production data and would break a migration to PostgreSQL. The rewrite should validate length (and reject control characters) in the application layer, and the migration needs to scan for such rows.  
**Confidence:** High — citation confirmed by an independent referee; an embedded NUL plus 300 characters was accepted with 200 (reproduced live)  
**Trace:** W-094

### RULE-022: Same blank-title rule is rejected with 422 on create but 400 on edit (two-layer validation)
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`, `backend/app/api/api.py:40-48, 62-70`, `backend/app/business_logic/todo_service.py:59-60`, `backend/app/services/api/../../../../frontend/src/services/api/client.ts:58-69`, `backend/tests/test_api/test_api_endpoints.py:107-129`, `backend/tests/test_api/test_update_to_do.py:132-143`  
**Plain English:** Input is checked in two places: checks built into the request schema (create title blank or missing, bad id format, wrong field types) fail with HTTP 422 and a list of reasons per field, while checks in the service layer (blocked words and symbols, blank title on edit) fail with HTTP 400 and only the text 'Bad request'. So the one business rule 'title must not be blank' gives a different outcome depending on whether you are creating or editing.  
**Specification:**  
  Given An existing open todo X titled 'Buy milk'  
  When  (a) POST /todo with {id: &lt;new uuid&gt;, title: " "}; (b) PUT /todo/X with {title: " "}  
  Then  (a) HTTP 422 with detail [{loc:["body","title"], msg:"Value error, title must not be null."}] and nothing stored; (b) HTTP 400 with {"detail":"Bad request"}, and X keeps the title 'Buy milk'  
**Parameters:** Schema-layer reject status = 422 (FastAPI/pydantic default, list-shaped detail); service-layer reject status = 400, fixed detail 'Bad request' (api.py:48, api.py:70); schema message 'title must not be null.' (create_todo_schema.py:28)  
**Edge cases handled:** POST with title 'Tea or coffee' passes the schema and fails the service blocklist, so it returns 400, not 422; POST without an id, or with id 'not-a-valid-uuid', returns 422 (test_api_endpoints.py:131-141); PUT body {"title": 5} returns 422 (wrong type), while PUT {"title": ""} returns 400; The web client builds its message as 'API Error {status}: {detail}' and expects detail to be a string (client.ts:63-64, 18). A 422 detail is a list, so the user would see 'API Error 422: [object Object]'  
**Suspected defect:** One rule, two status codes. The API test for blank-title edits accepts either 400 or 422 (test_update_to_do.py:143), so the contract was never pinned down. The 422 detail list also renders as '[object Object]' in the UI. Note: the client.ts citation is legacy/basictodo/frontend/src/services/api/client.ts:58-69.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-099

### RULE-023: Invalid edits are silently accepted when the same request marks the todo done
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:53-62, 88-98`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`  
**Plain English:** If an edit request contains done=true, the system skips every title and description check for that request, so a blank or blocked title that would normally be rejected returns success instead. The edit is quietly dropped and the caller gets no error.  
**Specification:**  
  Given An open todo X titled 'Buy milk' with description 'Oat milk'  
  When  PUT /todo/X with {done: true, title: " ", description: "DROP everything; --"}  
  Then  HTTP 200; X is now done=true and still titled 'Buy milk' with description 'Oat milk'; no 400 is raised. The same body without done (or with done=false) returns 400 'Bad request'  
**Parameters:** Branch condition: payload.done is truthy (todo_service.py:55). Title and description validation happens only after that branch (todo_service.py:59-62)  
**Edge cases handled:** {done: true, title: null} returns 200 (done), even though {title: null} alone causes a server error; {done: true} on a soft-deleted or unknown id returns 404 (todo_service.py:91-93); {done: true, title: 'New title'} with a valid title also drops the title change without telling the caller  
**Suspected defect:** Invalid input gets a success response, and the client cannot tell its other changes were thrown away. A rewrite should either validate every field supplied or reject mixed requests.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-100

### RULE-024: The done flag accepts loosely typed values such as 'yes', 'on', '1' and 1
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/schemas/data_schemes/update_todo_schema.py:10`, `backend/app/business_logic/todo_service.py:55-57, 59-68`, `uv.lock:573-574`, `backend/app/api/api.py:62-63`  
**Plain English:** The 'done' field on edit isn't limited to JSON true/false: text such as 'yes', 'on', 'true', '1' or the number 1 marks the todo done, and 'no', 'off', 'false', '0' or 0 reopens it. Anything else is rejected with 422.  
**Specification:**  
  Given An open todo X  
  When  PUT /todo/X with {"done": "yes"}  
  Then  HTTP 200 and X is marked done (same as {"done": true}). Then PUT /todo/X with {"done": "off"} returns 200 and X is open again. PUT with {"done": "maybe"} or {"done": 2} returns 422  
**Parameters:** done: Optional[bool] with no strict mode. pydantic 2.11.5 lax coercion accepts true/false, 0/1, and the case-insensitive strings 'true','false','yes','no','on','off','y','n','t','f','1','0'  
**Edge cases handled:** {"done": "false"} counts as false, so it does not take the mark-done branch. It runs the normal update and sets done=false; {"done": null} skips mark-done, then tries to store NULL in a NOT NULL column (already catalogued as a server error); {"done": 0} reopens a completed todo just as {"done": false} does; {"done": "yes", "title": "New"}: the mark-done branch wins and the title is ignored; {"done": null} is a separate, already-known path that ends in a server error; The web UI never sends 'done', so only direct API clients reach this behavior  
**Suspected defect:** A completion flag that accepts free-form strings could let a typo or a mis-serialized client change a todo's status by accident (for example, "0" reopens it).  
**Confidence:** Medium — done='yes'/'on'/'1'/1 all accepted as true (reproduced live); SME: Should the API accept only JSON true/false for 'done', or does any client depend on string or number forms ('yes', '1', 1)? A rewrite in another stack will not reproduce pydantic's lax coercion unless this is decided. | Should the rewrite accept only JSON true/false for the completion flag (strict), or are clients known to send string or numeric forms that must keep working? (Not verified at runtime: pydantic is not installed in the analysis environment.)  
**Trace:** W-102, W-109

### RULE-025: Web UI does not pre-check the server's blocked words and symbols
**Category:** Validation  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoForm.tsx:15-27`, `frontend/src/components/todos/TodoEditForm.tsx:20-32`, `backend/app/business_logic/validators/input_sanitizer.py:13-15, 37-39`, `backend/app/api/api.py:47-48`  
**Plain English:** The screen only checks that a title isn't blank and is at most 255 characters, so ordinary titles the server always rejects (any containing 'or', 'update', 'create', 'select', ';' or '--') get through the screen and fail only after they are sent.  
**Specification:**  
  Given The user is on the main screen with the create form  
  When  They type 'Tea or coffee' (or 'Update CV', 'Call mom; then dentist') and press Enter  
  Then  Screen validation passes, the todo briefly appears (optimistic add), the server returns 400 'Bad request', the entry is rolled back, and a toast says 'Failed to create todo' with 'API Error 400: Bad request' and a Retry button that will fail the same way every time  
**Parameters:** Client checks: trimmed title non-empty; trimmed length &lt;= MAX_TITLE_LENGTH = 255. Server blocklist: --, ;, /*, */, xp_cmdshell, drop, delete, insert, update, exec, execute, union, select, shutdown, create, alter, rename, truncate, declare, OR (whole words, case-insensitive)  
**Edge cases handled:** Editing an existing todo to 'Select venue' fails the same way: the edit form stays open with the 'Failed to update todo' toast; A title made only of U+0085 (next-line control character) survives JavaScript trim() but Python strip() removes it, so the server returns 422 and the toast reads 'API Error 422: [object Object]'; A title made only of U+FEFF is blocked by the UI as empty, although the server would accept it  
**Suspected defect:** Client and server validation rules have drifted apart. Users get a generic error and a Retry for a rejection that can never succeed.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-103

### RULE-026: The server accepts line breaks and tabs inside titles, but the web UI edits titles on a single line
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/validators/input_sanitizer.py:37-41`, `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`, `backend/tests/test_validators/unit/test_input_sanitizer.py:129-137`, `backend/tests/test_validators/integration/test_input_sanitizer_integration.py:49-53`, `frontend/src/components/todos/TodoEditForm.tsx:15, 34-36, 51, 78-84`, `frontend/src/components/todos/TodoItem.tsx:17-18`  
**Plain English:** Server-side title validation trims only leading and trailing whitespace, so titles stored through the API can contain line breaks and tabs. The web UI shows and edits titles in a single-line box, so a multi-line title displays on one line, and any keystroke in the edit box removes its line breaks before saving.  
**Specification:**  
  Given A todo created directly through the API with title "Line1\nLine2". The server returns 200 and stores the line break.  
  When  A user opens the todo in the web UI, clicks Edit, types '!' at the end, and saves.  
  Then  The list shows the title as 'Line1 Line2' (whitespace collapses on screen). The edit box shows 'Line1Line2' because single-line HTML inputs drop CR/LF. After the keystroke the saved title is 'Line1Line2!', so the line break is lost and the description is overwritten with the placeholder. Clicking Save without typing sends the original "Line1\nLine2" unchanged, because the form state still holds the unsanitized initial value.  
**Parameters:** Characters allowed in titles and descriptions: everything except the blocked tokens and words. Only leading and trailing whitespace is trimmed (Python str.strip).  
**Edge cases handled:** Tabs inside text are kept ("Tab\there" is accepted unchanged, test_input_sanitizer.py:134-137).; A leading or trailing newline is removed by the trim. Interior ones stay.; Multi-line descriptions are explicitly expected (test_input_sanitizer_integration.py:49-53), but the UI never displays or edits descriptions.; Pasting multi-line text into the create box strips the line breaks in the browser, so only API clients can create multi-line titles.  
**Suspected defect:** A UI edit round trip silently changes multi-line titles, and the front end and back end disagree on which characters a title may contain. The UI part relies on standard HTML input sanitization and was not run in a browser.  
**Confidence:** Medium — SME: Are titles meant to be single-line? Should the server reject or normalize CR/LF, tabs and other control characters in titles, and should descriptions keep multi-line text?  
**Trace:** W-112

### RULE-027: Input checks run before the existence and duplicate checks (400/422 beats 404/409)
**Category:** Validation  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:53-68, 39-43, 54-66, 89-93`, `backend/app/business_logic/builders/todo_entry_builder.py:26-29`, `backend/app/data_access/repository.py:70-76, 45-51`, `backend/app/api/api.py:40-48, 62-72, 40-50`, `backend/app/data_access/database.py:54-64`, `backend/app/business_logic/decorators.py:25-32`, `backend/tests/test_service/integration/test_update_todo_integration.py:69-106`  
**Plain English:** If a request is invalid and also targets a ToDo that does not exist (or reuses an id that already exists), the system reports the bad input (400 or 422) instead of 'not found' (404) or 'already exists' (409). The one exception is a mark-done request, which checks existence first and skips input validation.  
**Specification:**  
  Given No active ToDo with id 6f1c2a9e-0000-4000-8000-000000000001 exists (either never created or soft-deleted), and a separate ToDo with id A already exists  
  When  The client sends PUT /todo/6f1c2a9e-0000-4000-8000-000000000001 with {"title": "Drop off parcel"}, or with {"title": " "}  
  Then  The response is 400 'Bad request' and the database is never queried. The same PUT with {"title": "Buy milk"} returns 404 'ToDo not found'. With {"done": true, "title": " "} it returns 404, because mark-done checks existence first and skips validation. On create, POST {"id": A, "title": "Select venue"} returns 400 (not 409), and POST {"id": A, "title": " "} returns 422.  
**Parameters:** Edit check order: (1) if done is truthy: existence check, then mark done; (2) title blank/blocklist check (400); (3) description blocklist check (400); (4) existence check inside repository update (404). Create check order: (1) schema checks: id is a UUID, title not blank (422); (2) builder blank/blocklist checks (400); (3) duplicate id or DB constraint at insert (409).  
**Edge cases handled:** Soft-deleted ToDo plus an invalid title gives 400, not 404; Missing ToDo plus an invalid description only ({"description": "a; b"}) gives 400; Existing id plus an over-length title gives 409 either way, because both failures surface at insert as an integrity error; An invalid edit to a soft-deleted todo returns 400, so the caller only learns the todo is gone after sending valid input; PUT /todo/M with {} or {'description': 'x'} returns 404 at once, because title validation only runs when a title is supplied; A duplicate id combined with a 256+ character title fails only at the database, and both errors map to 409, so they can't be told apart; The duplicate-id check happens only when the session commits on exiting the scope (database.py:54-64), after all business validation has passed  
**Suspected defect:** Not wrong in itself, but undocumented. A rewrite that looks up the record (or checks for duplicates) before validating would return 404/409 where the legacy system returns 400, and contract tests would break.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should 'not found' / 'already exists' take priority over input-format errors in the new system, or is validating the payload first the intended contract for clients?  
**Trace:** W-114, W-118

### RULE-028: An empty list is a valid list response (contradicts test comments)
**Category:** Validation  
**Priority:** P2  
**Source:** `backend/app/schemas/api_responses/get_list_to_do_response.py:13-21`, `backend/app/api/api.py:88-91`, `frontend/src/components/todos/TodoList.tsx:26-34`, `backend/tests/test_api/test_list_to_do.py:16`  
**Plain English:** When there are no ToDos, or the requested page is past the last item, the list call still succeeds with zero items. Only a missing (null) list is rejected.  
**Specification:**  
  Given 3 active ToDos  
  When  GET /todo?limit=10&page=2  
  Then  The response is 200 {"success": true, "results": 0, "todo_entries": []}. The UI shows 'No todos yet. Add one above!' when page 1 is empty.  
**Parameters:** results default = 0 (get_list_to_do_response.py:13); validator rejects only None (line 19)  
**Edge cases handled:** Test comments say 'empty lists are rejected by schema' (test_list_to_do.py:16, 293), but the validator only rejects None, so the comment is wrong  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-071

### RULE-029: Duplicate ToDo titles are permitted
**Category:** Validation  
**Priority:** P2  
**Source:** `backend/app/data_access/database.py:72, 93`, `backend/app/data_access/repository.py:45-51`, `backend/app/business_logic/decorators.py:31-32`  
**Plain English:** Two ToDos can have exactly the same title. Only the id has to be unique.  
**Specification:**  
  Given An active ToDo titled "Buy milk" exists  
  When  A client POSTs /todo with a new id and title "Buy milk"  
  Then  The ToDo is created with 200 and the list now has two "Buy milk" entries. The title column has an ordinary (non-unique) index, and the only conflict check is the primary-key id.  
**Parameters:** title column: String(255), nullable=False, index=True, no unique constraint  
**Edge cases handled:** The same title is also allowed after case or whitespace changes, since there is no normalization-based uniqueness; Any IntegrityError on create (e.g. a CHECK constraint) is reported as 'ToDo already exists' (already catalogued), but title duplication never triggers one  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-072

### RULE-030: 'Blank title' is judged by different whitespace rules in the UI and the server, and invisible titles are accepted
**Category:** Validation  
**Priority:** P2  
**Source:** `frontend/src/components/todos/TodoForm.tsx:15-20, 50`, `frontend/src/components/todos/TodoEditForm.tsx:20-25, 51`, `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`, `backend/app/business_logic/validators/field_validator.py:29-35`, `backend/app/business_logic/validators/input_sanitizer.py:41`  
**Plain English:** The UI decides a title is empty using JavaScript trim(), and the server uses Python strip(). They remove different sets of invisible characters, and neither removes zero-width spaces, so some titles are rejected on one side only and visually blank titles get through both.  
**Specification:**  
  Given Three candidate titles: (a) two zero-width spaces U+200B, (b) a single zero-width no-break space U+FEFF, (c) a pasted unit-separator control character U+001F  
  When  Each is submitted, through the UI or directly to the API  
  Then  (a) Both UI and server accept it, so a todo with a visually empty title is created. (b) The UI rejects it with 'Todo title cannot be empty', but POST /todo accepts and stores it. (c) The UI accepts it and sends it. The server strips it to empty and rejects it: 422 on create (Pydantic schema validator) or 400 'Bad request' on update (service validate_required).  
**Parameters:** UI whitespace set: ECMAScript trim() (Zs category, TAB/VT/FF, U+FEFF, LF/CR/U+2028/U+2029). Server whitespace set: Python str.strip() (Zs, TAB/LF/VT/FF/CR, U+001C-U+001F, U+0085, U+2028/U+2029; not U+FEFF). Neither set includes U+200B.  
**Edge cases handled:** Verified empirically: U+FEFF is trimmed by JS but not by Python; U+001C, U+001F and U+0085 are trimmed by Python but not by JS; U+200B is trimmed by neither; U+00A0 (no-break space) and U+3000 (ideographic space) are trimmed by both, so those cases match; The same blank-after-trim title gets 422 on create but 400 on update, because different layers reject it  
**Suspected defect:** There is no single definition of a 'blank' title. Visually empty todos can be created, and the UI and server disagree on some inputs. The rewrite should define the trimmed character set once (ideally including zero-width and format characters) and share it between client and server.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-095

## Lifecycle rules (13)

### RULE-031: Delete is a soft delete: row kept, flagged deleted, not restorable
**Category:** Lifecycle  
**Priority:** P0  
**Source:** `backend/app/data_access/repository.py:53-68, 72-74, 86-97, 53-60`, `backend/app/business_logic/todo_service.py:70-75`, `backend/app/api/api.py:75-85`  
**Plain English:** Deleting a ToDo only sets its 'deleted' flag to true. The row stays in the database, and deleting a ToDo that is already deleted or does not exist returns 'not found'.  
**Specification:**  
  Given An active ToDo with id 3f2b...-a1 and deleted=false  
  When  DELETE /todo/3f2b...-a1 is called twice  
  Then  The first call sets deleted=true, keeps the row, and returns 200 {success:true, message:'Deleted successfully'}. The second call returns 404 'ToDo not found' because the lookup skips deleted rows.  
**Parameters:** deleted flag default = false; hard_delete_to_do exists in the repository but no API route uses it  
**Edge cases handled:** Soft-deleted rows stay in the table forever. No purge or retention job exists; A permanent delete (hard_delete_to_do, repository.py:62-68) is implemented but not reachable from the API; There is no undelete or restore path; repository.hard_delete_to_do exists but no service method or endpoint exposes it; The row and ID are kept forever, so the ID can't be reused (409 on create); There is no retention or purge policy in code. The README lists restore and purge as future features.; A todo that is already deleted or never existed returns 404; Deletion does not update updated_at, so the time of deletion is not recorded anywhere; There is no audit of who deleted the todo  
**Confidence:** High — citation confirmed by an independent referee; One duplicate card was downgraded by its own P0 panel; the other cards' panels confirmed P0.; SME: Is soft delete a business requirement (audit or recovery)? How long should soft-deleted ToDos be kept before permanent purge, and should users be able to restore them?  
**Trace:** W-004, W-035, W-046

### RULE-032: Marking done (PUT done=true) takes precedence and discards other edits in the same request
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:53-57, 88-98, 55-57`, `backend/app/data_access/repository.py:70-84, 70-90, 53-60`  
**Plain English:** If an update request sets done=true, the ToDo is marked complete and any title or description sent in the same request is ignored. The stored title and description are kept.  
**Specification:**  
  Given An active ToDo with title 'Buy milk', description 'Whole', done=false  
  When  PUT /todo/{id} with {title:'Buy bread', description:'Rye', done:true}  
  Then  The response shows title 'Buy milk', description 'Whole', done=true. The new title and description are thrown away without any error.  
**Parameters:** trigger: payload.done is truthy  
**Edge cases handled:** Marking an already-done ToDo done again works and changes nothing (idempotent); On the mark-done path the existing title and description are written back without passing through the SQL-keyword sanitizer again; The ToDo must exist and not be deleted, otherwise the result is 404; The frontend has no control to mark a ToDo done (TodoItem.tsx:11-37 renders only Edit and Delete) and does not display done status, so this transition is API-only; A soft-deleted or unknown ID gives ToDoNotFoundError and HTTP 404; Title and description validation and sanitization are skipped on this path, because existing values are copied back; The frontend has no control for marking a todo done, so this is API-only; The todo is already done: no guard, it is re-saved and returns 200 (idempotent); The todo is soft-deleted or does not exist: get_to_do_entry filters deleted=False, so the result is 404 'ToDo not found'; Title/description in the same request are not validated or sanitized on this path. They are simply ignored, so {done:true, title:"DROP TABLE"} returns 200; No completion timestamp is recorded; Lost update: if another request changes the title to "Pay rent + fees" between the read and the write, the old "Pay rent" is written back; Soft delete works the same way: it reads a detached copy, then merges the whole stale object (repository.py:53-60), so a concurrent edit can be reverted when the record is flagged deleted; A ToDo that is missing or soft-deleted at either step returns 404; A stored title that would fail today's blocklist is still written back unchanged, because no validation runs on this path  
**Suspected defect:** When done=true is sent together with other fields, the title and description changes are lost and the client is not told. / Title and description changes in a done=true request are silently dropped while the response is still 200 OK. / When done=true is combined with title or description edits, the edits are silently discarded and the API still returns 200. Clients get no signal that part of their update was ignored. / Read-then-write in separate transactions with full-field write-back allows lost updates. There is also no idempotency signal (e.g. 'already done') for clients.  
**Confidence:** High — citation confirmed by an independent referee; PUT {title:'Renamed', done:true} returned done=true with the old title (reproduced live); SME: When a client marks a ToDo done and edits its text in the same request, should both changes be applied? Is marking done meant to be a user-facing feature (the UI does not offer it today)? | When a client sends done=true together with a new title or description, should the edits be applied, rejected, or ignored as they are today? | Done is never recorded with a timestamp. Should completion time be captured (completed_at), and should a combined done+edit request apply both changes or reject the request?  
**Trace:** W-006, W-033, W-044, W-067

### RULE-033: Done flag has no state guard: re-marking done or reopening is always allowed
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:53-68, 55, 59-68, 55-68, 54-57, 89-98`, `backend/app/data_access/repository.py:77-78, 70-84`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`  
**Plain English:** Sending done=false on an update reopens a completed ToDo. Nothing stops a completed ToDo from being reopened or edited.  
**Specification:**  
  Given A ToDo with done=true and title 'File taxes'  
  When  PUT /todo/{id} with {done:false}  
  Then  The normal update path runs, done is set to false, and the ToDo is open again. A later PUT {title:'File taxes 2026'} on a done ToDo also succeeds.  
**Parameters:** status values: done=false (open) and done=true (complete); deleted=true is the terminal state  
**Edge cases handled:** The lifecycle is open, then done, then open again freely. Any of these states can move to deleted, and deleted is final (no route back); Omitting done (null or unset) leaves done unchanged; Explicit done: null is set but falsy, so it goes down the general path and is written as NULL into a NOT NULL column. That raises IntegrityError, which becomes ToDoAlreadyExistsError and an unhandled HTTP 500.; PUT {} (empty body) is a no-op that returns 200 with the unchanged entry; PUT {done: null} writes NULL to a NOT NULL column and returns 500 (see the 'Explicit null' card); Done and Open todos are treated the same by edit and delete. Being done does not lock any field; The pinned pydantic 2.11 parses 'done' loosely because update_todo_schema.py:10 sets no strict mode. {"done": "yes"}, {"done": 1}, {"done": "on"} or {"done": "true"} all mark the todo done. {"done": "no"}, {"done": 0} or {"done": "off"} reopen it.; Mark-done reads the todo and writes it in two separate database sessions (todo_service.py:91-95 calls repository.get_to_do_entry and then repository.update_to_do). If the todo is soft-deleted between the two steps, the write finds nothing and the caller gets 404.; The mark-done branch writes back the stored title and description without re-running sanitisation (todo_service.py:94). Mark-done therefore cannot fail on input validation.; The tests exercise Open-&gt;Done only, against a mocked repository (backend/tests/test_service/integration/test_mark_todo_done_integration.py:30-58). Done-&gt;Done and Open-&gt;Open are untested.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should completed ToDos be reopenable or editable, or should completion be final or require a separate 'reopen' action? | Is reopening a completed todo an allowed transition, and should it be audited (for example by stamping updated_at or a completed_at timestamp)? | The code allows reopening a done todo by sending done=false. Is reopening an intended business capability, or should Done be a final state for edits?  
**Trace:** W-007, W-034, W-045, W-082

### RULE-034: New ToDo initial state and server-local creation timestamp
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/business_logic/builders/todo_entry_builder.py:19-34, 26-34, 30`, `backend/app/schemas/data_schemes/todo_schema.py:62-67`, `backend/app/data_access/database.py:74`  
**Plain English:** Every new ToDo starts open (not done), not deleted, with no update time, and its creation time is the server's current local time.  
**Specification:**  
  Given POST /todo with id 7c1e...-09 and title 'Wash dishes' on a server running in UTC+2 at 2026-10-03 14:05:00 local time  
  When  the ToDo is created  
  Then  created_at = 2026-10-03T14:05:00 (naive local time, no timezone offset), updated_at = null, done = false, deleted = false  
**Parameters:** done=false; deleted=false; updated_at=None; created_at=datetime.datetime.now() (naive, server local time)  
**Edge cases handled:** created_at is naive local time saved in a TIMESTAMP(timezone=True) column, so the timezone is lost and moving servers or changing DST shifts how it reads; The DDL-only model ToDoORM has default=datetime.datetime.now() evaluated once at import (database.py:74), a frozen timestamp. It is never used for inserts because the builder always sets created_at; The imperative table gives updated_at a default of func.now() (database.py:96). Depending on how SQLAlchemy treats an explicit None, the stored updated_at may be the insert time rather than NULL, while the create response shows null; Client-supplied done or deleted values cannot be set at creation because the create schema has no such fields; The mapped table declares updated_at default=func.now() (database.py:96). Under SQLAlchemy's rule that an explicit None on a defaulted column is omitted from INSERT, the stored updated_at may end up as the DB CURRENT_TIMESTAMP (UTC in SQLite) while the create response shows null.; Servers in different timezones, or DST changes, produce timestamps that cannot be compared; ToDoORM's default=datetime.datetime.now() (database.py:74) is evaluated once at import. This is a latent bug, but ToDoORM is not used for inserts  
**Confidence:** Medium — SME: Should created_at be stored in UTC with a timezone? Should a newly created ToDo have updated_at null or equal to created_at?  
**Trace:** W-015, W-032, W-050

### RULE-035: Last-updated timestamp: set by the DB clock (UTC) at insert, never refreshed on change
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:70-84, 77-80, 45-51`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`, `backend/app/business_logic/todo_service.py:88-98, 40-43`, `frontend/src/hooks/queries/useUpdateTodo.ts:24-31, 24-30`, `backend/app/business_logic/builders/todo_entry_builder.py:30-31, 26-34`, `backend/app/data_access/database.py:96, 88-100, 74, 89-100`, `frontend/src/hooks/queries/useCreateTodo.ts:26`  
**Plain English:** Editing, completing, or deleting a ToDo does not change its updated_at value on the server, even though the UI briefly shows the current time as the update time.  
**Specification:**  
  Given A ToDo created at 2026-10-01 09:00 with updated_at null  
  When  PUT /todo/{id} {title:'New'} is called on 2026-10-03 14:05  
  Then  The server leaves updated_at unchanged (null). The frontend shows updated_at=now right away (optimistic), then the refetch replaces it with the server value.  
**Parameters:** No server code assigns updated_at on update, mark-done, or soft delete  
**Edge cases handled:** The update schema has no updated_at field and the repository only copies fields that were sent; The DB-level default func.now() applies only on insert, not on update (no onupdate defined); SQLAlchemy usually omits None-valued columns that have a default from the INSERT, so updated_at may equal the DB's now() (UTC in SQLite) rather than null; created_at uses server local time while func.now() in SQLite is UTC, so the two timestamps can differ by the timezone offset at creation; UTC server: updated_at roughly equals created_at but is cut to whole seconds, so it can look up to &lt;1 s earlier than created_at; PostgreSQL/MySQL DATABASE_URL (allowed by database.py:33): now() gives the database's own transaction time with that server's timezone handling, so the result depends on the backend; Unit/integration tests only check updated_at is None at builder level or with a mocked repository (tests/test_builders/unit/test_todo_entry_builder.py:254-265); no test checks the value after a real insert; The table DDL comes from ToDoORM via Base.metadata.create_all, which has no DB-level defaults. Runtime writes go through the imperatively mapped to_do_table, whose Python/SQL defaults are applied; ToDoORM.created_at default=datetime.datetime.now() (database.py:74) is called once at module import. Any future insert through ToDoORM without a created_at would stamp every row with the server start time. No current write path uses ToDoORM; This is the creation-time case of the already-catalogued 'updated_at never maintained' rule. The value is not null after creation, it is the insert time.; The response to the create call is built from the in-memory object (todo_service.py:43), so it may differ from what a later GET returns.; On PostgreSQL or MySQL (allowed by DATABASE_URL), now() returns the database server's time with its own timezone rules, so the offset differs.; Unit tests only check that updated_at is None on the object handed to a mocked repository (backend/tests/test_service/unit/test_create_todo.py:236), so this behaviour is untested.  
**Suspected defect:** updated_at exists in the schema and the API contract but is never set when a ToDo is modified, so any audit or 'recently changed' feature built on it would get wrong data. / updated_at never changes after creation. Any reporting or sync logic that relies on it will be wrong, and the UI's optimistic value disagrees with the server. / Two problems: (1) Intent vs reality: the builder and its tests expect updated_at=null for a new ToDo, but the stored value is the DB insert time. (2) Mixed clocks: created_at uses server-local naive time while updated_at uses DB UTC time, so 'last updated' can come before 'created'. Also a latent frozen default at database.py:74. / The app and the database disagree on the initial value, and they use different clocks (server local time versus database UTC). This yields updated_at earlier than created_at.  
**Confidence:** Medium — fresh insert: created_at 14:02 local, updated_at 12:02 UTC (reproduced live); SME: Should updated_at be set to the current time on every edit, completion, and delete? Is any report or sort order expected to rely on it? | Should a newly created ToDo have updated_at = null (builder intent) or = its creation time? Which clock and timezone should all ToDo timestamps use: server local or UTC? (Engineering: please confirm with a real-SQLite integration test that POST /todo returns a non-null updated_at.) | Should a newly created todo have updated_at empty, equal to created_at, or the insert time? And should all timestamps be stored in UTC?  
**Trace:** W-016, W-049, W-065, W-089

### RULE-036: Failed create/edit keeps the input and offers a toast Retry that resends the request unchanged (skipping validation)
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoForm.tsx:48-72, 87, 54-72`, `frontend/src/components/todos/TodoEditForm.tsx:51-70, 53-70`, `frontend/src/config/queryClient.ts:11-13`, `frontend/src/components/todos/TodoDeleteButton.tsx:22-31`, `frontend/src/hooks/useToast.ts:11-23`  
**Plain English:** The input is cleared (create) or the edit form closed (edit) only after the server confirms success. On failure the text stays and a Retry button resends exactly the same request, including the same client-generated todo id.  
**Specification:**  
  Given A user types 'Buy groceries'. The browser generates id 7c9e6679-7425-40de-944b-e07fc1f90ae7. The server responds with HTTP 500.  
  When  The user presses Enter  
  Then  The request is automatically resent once (mutation retry = 1). If it still fails, a 'Failed to create todo' toast with Retry appears and 'Buy groceries' stays in the input. Clicking Retry posts the same id 7c9e6679-... and the same title. Only on success is the input cleared and the 'Todo created' toast shown. For edits, the edit form stays open on failure and closes only on success.  
**Parameters:** mutations.retry = 1; queries.retry = 1; Retry action label 'Retry'; create input disabled while a create is in flight  
**Edge cases handled:** If the first POST was saved but its response was lost, the automatic or manual retry gets 409 'ToDo already exists'. The user sees a failure toast even though the todo exists, and the list refetch then shows it.; If the user presses Enter again instead of clicking Retry, handleSubmit generates a new UUID. When the first attempt had actually been saved, this creates a second todo with the same title.; Business rejections (400 blocklist, 409 duplicate) are also automatically resent once before the error toast. Each click on Retry sends up to two more identical requests.; The create input is disabled while a create is pending (TodoForm.tsx:87), which blocks double-submission during a single attempt.; A failed Retry raises no new error toast or Retry offer, because no per-call onError is attached. Only the hook-level rollback and refetch run (useCreateTodo.ts:41-50).; Retrying a delete resends DELETE for the same id. If the first attempt actually succeeded, the resend gets 404.; The id is fixed when the user first submits (TodoForm.tsx:48-52), so every Retry reuses it.  
**Suspected defect:** After a successful Retry the UI does not reset the create input, close the edit form, or confirm success. The user cannot tell that the retry worked, and may submit the todo again (creating a duplicate with a new id).  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-076, W-084

### RULE-037: New todos must start not-deleted, but the model's default for 'deleted' is not a boolean (masked by the builder)
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/models/todo.py:8-18`, `backend/app/business_logic/builders/todo_entry_builder.py:26-34`, `backend/app/data_access/database.py:97`  
**Plain English:** A todo is meant to be active (not deleted) until someone deletes it. Today that holds only because the single creation path always passes deleted = false. The domain model's own default for 'deleted' is a database column-definition object, not false.  
**Specification:**  
  Given Code that builds a todo record without passing the deleted flag, such as a future import, migration or alternative creation path  
  When  The record is constructed and saved  
  Then  Its deleted attribute holds a SQLAlchemy mapped-column object (truthy, not a boolean) instead of false. Insert probably fails or the record is treated as deleted. In current code every construction (builder and all test factories) passes deleted=False explicitly, so API-created todos start with deleted = false and done = false.  
**Parameters:** Model default deleted = mapped_column(default=False) (column object); model default done = False; table default deleted = False  
**Edge cases handled:** The database table default deleted = False (database.py:97) applies only when the column is left out of the INSERT. The ORM sends the attribute value, so the table default does not rescue a bad model default.; The test factories also pass deleted=False explicitly (backend/tests/test_data/factories.py:15-27), so the faulty default is never exercised.  
**Suspected defect:** models/todo.py:17 sets `deleted: Mapped[bool] = mapped_column(default=False, name='deleted')` as a dataclass field default. The generated constructor uses the column object itself as the default value, not False. / In a plain dataclass, the default for 'deleted' is the SQLAlchemy column-configuration object, not the boolean False.  
**Confidence:** Medium — SME: Is there any creation path other than POST /todo (bulk import, data migration, admin script) that must create todos? If so, confirm they must always start with deleted = false and done = false regardless of how they are constructed. | Engineering to confirm: can ToDoEntryData ever be created without an explicit 'deleted' value (imports, scripts, a future restore feature)? The rewrite should make 'not deleted' the explicit default.  
**Trace:** W-080, W-090

### RULE-038: Completing a todo records no completion time (or deletion time)
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `backend/app/business_logic/todo_service.py:88-98`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`, `backend/app/data_access/repository.py:77-78`, `backend/app/models/todo.py:8-18`, `backend/app/data_access/database.py:89-99`, `README.md:115`  
**Plain English:** Marking a todo done only flips the done flag. Nothing records when it was completed, reopened or deleted, so the roadmap's 'time to complete' analysis can't be computed from stored data.  
**Specification:**  
  Given Todo 'Pay rent' was created on 2026-10-01 at 09:00 (created_at) with done=false  
  When  PUT /todo/{id} {done: true} on 2026-10-03 at 18:30, then {done: false} on 2026-10-04, then {done: true} on 2026-10-05  
  Then  Each response shows the toggled done flag. The stored record has no completion date and no trace of the reopen, and updated_at keeps the value it got at insert. The first completion time (2 days 9.5 hours) can't be reconstructed.  
**Parameters:** Fields written on mark-done: done=true plus a re-write of the current title and description. The toDo table has only id, title, description, created_at, updated_at, deleted and done. There is no completed_at, deleted_at or status-history column.  
**Edge cases handled:** Reopening (done=false) erases all evidence that the todo was ever completed; Soft-deleting a done todo keeps done=true on the hidden row, but the deletion time isn't recorded anywhere; Legacy data can't be backfilled with real completion times after migration  
**Suspected defect:** README.md:115 plans time-to-complete tracking, but no completion timestamps are captured today, so pre-migration history can't support it.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should the new system record completion (and deletion) timestamps or a status history? If so, how should legacy done todos be treated, given they have no completion date?  
**Trace:** W-119

### RULE-039: The README roadmap's todo lifecycle differs from what the code implements
**Category:** Lifecycle  
**Priority:** P1  
**Source:** `README.md:104-118`, `backend/app/data_access/repository.py:53-68`, `backend/app/business_logic/todo_service.py:55-57`, `frontend/src/components/todos/TodoItem.tsx:11-37`  
**Plain English:** The README lists soft delete, restore, a bulk 'purge all deleted' dialog and mark-as-done as future work. In code, soft delete and API mark-done/reopen already exist, while restore, bulk purge and any UI done control do not.  
**Specification:**  
  Given README 'Further steps' lists: Deletion (mark as deleted, plus a dialog to permanently delete all todos marked deleted), Restore (undelete), Mark as done, Reminders (due dates) and Subtasks  
  When  The rewrite team takes the todo lifecycle from the documentation instead of the code  
  Then  They would treat existing behaviour as new features and miss what's absent. What the code does: Active -&gt; Deleted exists (DELETE /todo/{id}). Open &lt;-&gt; Done exists only via PUT done=true/false, with no UI control. Deleted -&gt; Active (restore) doesn't exist. Deleted -&gt; Purged doesn't exist; the only physical delete is per item, unused, and limited to active todos.  
**Parameters:** Planned but not implemented: restore (README.md:109), bulk purge of all soft-deleted todos via a dialog (README.md:108), UI mark-as-done (README.md:110), due-date reminders (README.md:118), subtasks (README.md:117), time-to-complete tracking (README.md:115)  
**Edge cases handled:** README.md:108 describes soft delete as future work, but repository.py:53-60 already implements it; README.md:110 describes mark-as-done as future work, but the API already supports it (todo_service.py:55-57); only the UI lacks it  
**Confidence:** Medium — SME: Which roadmap transitions belong in the target lifecycle? (a) Restore of soft-deleted todos: should it exist, and for how long after deletion? (b) Bulk purge of all soft-deleted todos: who may trigger it, and should there be an automatic retention period instead? (c) A UI control for done/reopen?  
**Trace:** W-121

### RULE-040: Inline edit lifecycle: View -&gt; Edit -&gt; View; editing hides Delete; Cancel discards (even mid-save)
**Category:** Lifecycle  
**Priority:** P2  
**Source:** `frontend/src/components/todos/TodoItem.tsx:12-35, 11-37, 29-35`, `frontend/src/components/todos/TodoEditForm.tsx:15, 53-55, 105, 14-15, 34-42, 53-70, 95-108, 78-84`, `frontend/e2e/todo-crud.spec.ts:87-111`, `frontend/e2e/todo-validation.spec.ts:89-118`, `frontend/src/components/todos/__tests__/TodoItem.test.tsx:43-48`, `frontend/src/hooks/queries/useUpdateTodo.ts:11-44`, `frontend/src/components/todos/TodoForm.tsx:87`  
**Plain English:** While a todo is in edit mode, its Edit and Delete buttons are hidden. The edit box starts with the current title, and Cancel throws away unsaved changes with no confirmation.  
**Specification:**  
  Given The list shows the todo 'Original todo'  
  When  The user clicks Edit, types 'Changed text', then clicks Cancel  
  Then  While editing, the 'Edit' and 'Delete Todo' buttons for that item are hidden. Clicking Cancel closes the form immediately with no prompt, and the item still reads 'Original todo'. A successful Save also closes the form.  
**Parameters:** none  
**Edge cases handled:** This is a UI-only guard. The server does not lock a todo while it is being edited, and anyone can delete it through the API meanwhile. A later Save then gets 404 'ToDo not found'.; Each item has its own edit state, so several todos can be in edit mode at once.; A todo cannot be deleted while it is being edited, because the Delete button is hidden (TodoItem.tsx:19-26).; The editor has no Enter-to-save: only the Save button submits, since the input is not inside a form.; The UI does not know a todo's done status, so done todos are edited the same way. They stay done because the edit payload omits 'done'.; The editor is seeded once when it opens. If the title changes elsewhere while the editor is open, Save overwrites that change.; Save succeeds after Cancel: change is stored but never confirmed to the user; Save fails after Cancel: title reverts in the list with no message; User keeps typing during the save: the extra text is not saved and is dropped when the form closes on success; User reopens Edit before the response: the new form starts from the optimistic title, and the old save's outcome is still not reported  
**Suspected defect:** The create and edit forms handle an in-flight save differently, and the save outcome can be lost when the user cancels.  
**Confidence:** Medium — SME: While a save is pending, should the edit form be locked (input and Cancel disabled), as the create form is? And must the outcome of a save always be reported, even if the user has closed the editor?  
**Trace:** W-081, W-086, W-106

### RULE-041: Create-form submission lifecycle: input locked while saving, cleared on success, kept on failure
**Category:** Lifecycle  
**Priority:** P2  
**Source:** `frontend/src/components/todos/TodoForm.tsx:39-72, 81-90`, `frontend/e2e/todo-crud.spec.ts:21-34`  
**Plain English:** After a valid title is submitted, the add-todo input is disabled until the server answers. On success the input is emptied and 'Todo created' is shown. On failure the typed text stays in the box and an error toast with Retry is shown.  
**Specification:**  
  Given An empty add-todo input  
  When  The user types 'Buy groceries' and presses Enter, and the server accepts it  
  Then  The input is disabled while the request is pending, then cleared, and a success toast 'Todo created / Your todo has been added successfully' appears. If the server rejects the request, the input keeps 'Buy groceries', becomes editable again, and the toast 'Failed to create todo' with Retry appears.  
**Parameters:** Success toast title 'Todo created'; failure toast title 'Failed to create todo'. Input disabled while createTodo.isPending is true (TodoForm.tsx:87).  
**Edge cases handled:** Submission is Enter-only: there is no Add button.; An inline validation error is cleared as soon as the user types again (TodoForm.tsx:33-36).  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-085

### RULE-042: No one can add todos while the list is loading or has failed to load
**Category:** Lifecycle  
**Priority:** P2  
**Source:** `frontend/src/components/todos/TodoList.tsx:8-47`, `frontend/src/config/queryClient.ts:8`  
**Plain English:** The main screen is in one of four states: loading, error, empty or populated. The add-todo input exists only in the empty and populated states, so users cannot create todos while the list is loading or has failed to load.  
**Specification:**  
  Given The backend returns 500 for GET /todo  
  When  The page loads (after one automatic retry)  
  Then  The screen shows only an error box reading 'API Error 500: Internal error' and a Retry button. The add-todo input is not rendered. If the list loads with zero items, the input is shown with the message 'No todos yet. Add one above!'.  
**Parameters:** Empty-state text 'No todos yet. Add one above!' (TodoList.tsx:31-35). The error fallback text 'Failed to load todos' is used only when the error is not an Error instance (TodoList.tsx:17). List query retry = 1.  
**Edge cases handled:** While loading, only a spinner is shown (TodoList.tsx:11), so the form is unavailable there too.; The Retry button re-runs the list query only (TodoList.tsx:18).  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-087

### RULE-043: A rendering crash replaces the whole app with a 'Something went wrong' page that shows the raw error
**Category:** Lifecycle  
**Priority:** P2  
**Source:** `frontend/src/components/errors/ErrorBoundary.tsx:14-55`, `frontend/src/App.tsx:12-24`  
**Plain English:** If the screen crashes while drawing, the header, list, form and notifications are all replaced by a 'Something went wrong' page showing the internal error message, plus a 'Try Again' button that re-draws the app without reloading the page.  
**Specification:**  
  Given The app is showing the todo list  
  When  A rendering error is thrown (for example, an unexpected value reaches a component) and the user then clicks 'Try Again'  
  Then  The app moves from Normal to Crashed: the full UI is replaced by 'Something went wrong' plus the error's message, or 'An unexpected error occurred' if there is none. 'Try Again' clears the crash state and re-renders. If the cause persists, the crash page returns at once.  
**Parameters:** Fallback heading 'Something went wrong'; default message 'An unexpected error occurred'; button 'Try Again'. A custom fallback is supported but App doesn't use one.  
**Edge cases handled:** Failed API calls don't trigger this state; they go to toasts or the list's own error screen with a Retry button (TodoList.tsx:13-24); Raw internal error text is shown to end users; The boundary wraps everything, including the Chakra provider (App.tsx:14-16), yet its fallback uses Chakra components; whether the fallback renders correctly outside the provider wasn't verified  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-123

## Policy rules (16)

### RULE-044: UI overwrites description with a fixed placeholder
**Category:** Policy  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoForm.tsx:48-52`, `frontend/src/components/todos/TodoEditForm.tsx:51`, `README.md:14-16`  
**Plain English:** The web UI has no description field. Every ToDo it creates gets the description 'not implemented yet', and every edit through the UI resets the description to that text.  
**Specification:**  
  Given A ToDo whose description was set to 'Read to page 223' through the API  
  When  the user edits only its title in the UI  
  Then  PUT sends {title:'&lt;new&gt;', description:'not implemented yet'}, and the real description is lost  
**Parameters:** description literal = 'not implemented yet'  
**Edge cases handled:** The UI never displays description, done, created_at, or updated_at (TodoItem.tsx:11-37, TodoList.tsx:37-43); The UI never displays the description, so users can't see that it was overwritten; README.md:14-16 says 'Update' lets the user enter a new description, but the code edits the title. The documentation and the code disagree  
**Suspected defect:** UI edits silently destroy descriptions entered through the API, and placeholder text ends up in production data. / Every UI edit destroys the existing description.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should descriptions be editable in the new UI? Should existing 'not implemented yet' values be migrated to null? | Should migrated data treat the description "not implemented yet" as empty, and should the new UI leave the description untouched when only the title is edited? | Should UI edits leave the description out of the request (so it is preserved), or is description editing planned?  
**Trace:** W-018, W-040, W-062

### RULE-045: Web UI only ever shows the first 10 ToDos, and never shows done status
**Category:** Policy  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoList.tsx:9, 26-45, 26-46`, `frontend/src/hooks/queries/useTodoList.ts:4-8`, `frontend/src/services/api/todoApi.ts:61-65`, `frontend/src/hooks/queries/useCreateTodo.ts:15-35`, `frontend/src/components/todos/TodoItem.tsx:6-37`  
**Plain English:** The main screen always asks for page 1 with 10 items and has no paging control, so users cannot see their 11th ToDo or later ones.  
**Specification:**  
  Given A user has 12 active ToDos  
  When  the main list loads  
  Then  Only the first 10 in server storage order appear. ToDos #11 and #12 cannot be reached in the UI.  
**Parameters:** limit = 10, page = 1 (hardcoded in TodoList and in the optimistic-cache keys of all mutation hooks)  
**Edge cases handled:** A newly created 11th ToDo appears at the top for a moment (optimistic prepend), then disappears after the refetch because the server puts it past position 10; With 0 todos the UI shows 'No todos yet. Add one above!'; Done status isn't displayed. TodoItem shows only the title.  
**Suspected defect:** ToDos beyond the first 10 are hidden from users with no way to reach them. / Todos past the 10th are unreachable in the UI, and a newly created todo can vanish after refetch. / Todos beyond the 10th cannot be reached from the UI, and the done lifecycle exists only in the API.  
**Confidence:** High — citation confirmed by an independent referee; after 11 creates, the newest ToDo is not on page 1 (reproduced live at API level); SME: What page size and paging style (pages, infinite scroll, show all) should the new UI use? | Should the UI page through all todos (or show everything), and in what order should they appear? | Should the UI offer a complete/reopen action and show done status? Should it paginate?  
**Trace:** W-019, W-039, W-060

### RULE-046: UI delete: confirmation prompt, success toast before the server confirms, silent reappearance on failure
**Category:** Policy  
**Priority:** P1  
**Source:** `frontend/src/components/todos/TodoDeleteButton.tsx:13-33, 13-32, 13-31`, `frontend/src/hooks/queries/useDeleteTodo.ts:10-40, 10-36`, `frontend/src/components/todos/TodoList.tsx:37-43`, `frontend/src/config/queryClient.ts:11-13`, `frontend/package.json:21`  
**Plain English:** Before deleting, the user must confirm 'Do you really want to delete this item?'. The 'Todo deleted' success message then appears straight away, before the server has confirmed.  
**Specification:**  
  Given A user clicks 'Delete Todo' and confirms the dialog  
  When  the server call fails (for example 404 or 500)  
  Then  The user sees 'Todo deleted' (success) first, then 'Failed to delete todo' with a Retry button, and the item comes back in the list  
**Parameters:** confirmation text: 'Do you really want to delete this item?'; toast duration default 5000 ms (useToast.ts:12)  
**Edge cases handled:** Cancelling the confirmation does nothing; On failure the user sees a success toast followed by a failure toast; Server 500 or network failure: item reappears permanently with no explanation after a success toast; Server 404 (already deleted in another tab): item flickers back, then the refetch removes it again; The Retry action for delete can never be reached through the normal flow; onMutate skips removal only when no list is cached ('if (!old) return old'). In that case the button stays mounted and the error toast would show.  
**Suspected defect:** The success notification appears before the outcome is known, so users can see both success and failure messages for one action. / The success toast is shown before the server result, so failed deletes are briefly reported as successful. / The success toast appears before the server confirms the delete. / Two problems combine: the success toast is shown optimistically, and the error toast lives in a component that the optimistic removal unmounts. Together they hide every delete failure from the user.  
**Confidence:** Medium — SME: Should the delete success message wait for server confirmation? | Should a failed delete always tell the user and offer a retry? And should 'Todo deleted' appear only after the server confirms? (Engineering should confirm with a forced-500 test that the onError toast never fires in the current build.)  
**Trace:** W-021, W-041, W-061, W-105

### RULE-047: Business outcome to HTTP status mapping
**Category:** Policy  
**Priority:** P1  
**Source:** `backend/app/api/api.py:40-91`, `backend/app/business_logic/decorators.py:18-35, 21-35`  
**Plain English:** Validation failures return 400 'Bad request', missing or deleted ToDos return 404, duplicate or other integrity failures on create return 409, and unexpected failures return 500. The single-get and list endpoints map only some of these.  
**Specification:**  
  Given Service outcomes: validation error, not found, integrity violation, unexpected error  
  When  a create, get, update, delete, or list endpoint is called  
  Then  create: 400 / 409 / 500. get: 404 only, anything else is an unhandled 500. update: 404 / 400 / 500, with integrity errors (ToDoAlreadyExistsError) unhandled, giving 500. delete: 404 / 400 / 500. list: no mapping, any error is a 500.  
**Parameters:** error detail strings: 'Bad request', 'ToDo not found', 'ToDo already exists', 'Internal error'  
**Edge cases handled:** Any database IntegrityError (duplicate id, length CHECK, NOT NULL) becomes ToDoAlreadyExistsError, which is only meaningful on create; Every other unexpected exception is wrapped as ToDoRepositoryError, so the client only ever sees 'Internal error'; Validation messages from the sanitizer and field validator are not passed to the client, which always gets 'Bad request'; Any non-business exception in the service is wrapped as ToDoRepositoryError; GET doesn't map ToDoRepositoryError (for example a corrupt row that fails ToDoSchema) and falls through to a raw 500; Update doesn't map ToDoAlreadyExistsError (NOT NULL or CHECK violations), which falls through to a raw 500; Any IntegrityError is reported as 'ToDo already exists', even when the cause is a length or null violation; The decorator turns every IntegrityError into AlreadyExists, including NOT NULL and CHECK violations; docs/backend.puml:22-25 describes a Status enum (SUCCESS/FAILURE), but the code returns a success boolean  
**Suspected defect:** Update has no 409 handler, so integrity failures there return 500. All IntegrityErrors on create are labelled 'already exists' whatever the real cause. / IntegrityError is treated as 'already exists' no matter what caused it, and the error mapping is inconsistent across endpoints.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should validation errors return a specific reason to the client, for example which field failed and why? | What error contract should the new API expose (status codes and messages) for validation, not-found, conflict and constraint violations, applied the same way across all endpoints?  
**Trace:** W-022, W-042, W-064

### RULE-048: Todo list visibility: active todos only, done included, unordered
**Category:** Policy  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:92-97`, `backend/app/business_logic/todo_service.py:77-86`, `backend/app/api/api.py:88-91`  
**Plain English:** The todo list shows every todo that hasn't been deleted, whether done or not, in no guaranteed order. Records that fail data validation are quietly left out, and the 'results' count reflects only the items on the returned page.  
**Specification:**  
  Given The database holds 3 active todos (1 done), 1 soft-deleted todo, and 1 active row with a blank title  
  When  GET /todo is called  
  Then  The response has results=3 with the 2 open and 1 done todos. The deleted row is excluded, and the blank-title row is skipped with a warning log.  
**Parameters:** Filter deleted = false; no done filter; no ORDER BY  
**Edge cases handled:** results is the page item count, not the total count, so clients can't work out the number of pages; Without ORDER BY, which todos land on a page depends on the database; The list endpoint has no exception mapping, so database errors become HTTP 500; limit=100000 is accepted (no cap); page=0 or a negative limit produces a negative offset or limit, which behaves differently per database  
**Confidence:** High — citation confirmed by an independent referee; SME: Should the list have a defined sort order (for example newest first), report a total count, and offer filtering by done status? | What sort order should the list use (newest first? open before done?), what is the maximum page size, and should the response include a total count?  
**Trace:** W-037, W-058

### RULE-049: No purge path: soft-deleted ToDos are kept forever (hard delete is unreachable and works only on active rows)
**Category:** Policy  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:21-23, 62-68, 86-90`, `backend/app/factory.py:9-31`, `backend/app/business_logic/todo_service.py:70-75`  
**Plain English:** Soft-deleted todos are kept forever. A physical (hard) delete exists in the data layer, but no service method, API route or batch job ever calls it.  
**Specification:**  
  Given A todo was soft-deleted on 2024-01-01  
  When  Any amount of time passes (for example until 2026-10-03)  
  Then  The row is still in the toDo table with deleted=1. Nothing purges or archives it  
**Parameters:** Retention period: unlimited (no value configured). hard_delete_to_do is defined but unreachable  
**Edge cases handled:** Rows that are logically deleted keep counting toward primary-key uniqueness forever; Unreachable today: no API endpoint, service method or scheduled job calls hard_delete_to_do; Wiring a purge feature to this method as-is would silently purge nothing and still look successful at the API level unless the false return is checked; Calling it on an active todo skips the soft-delete stage entirely, so the todo is unrecoverable at once  
**Suspected defect:** The purge logic is inverted relative to the documented intent (README.md:108: permanently delete todos marked as deleted). It can delete only todos that are NOT marked deleted.  
**Confidence:** Medium — SME: What retention period applies to deleted todos (for example a GDPR or erasure requirement)? Should hard_delete_to_do be exposed through a scheduled purge or an erasure request?  
**Trace:** W-048, W-120

### RULE-050: Failed requests are retried once automatically, reusing the same client-generated id
**Category:** Policy  
**Priority:** P1  
**Source:** `frontend/src/config/queryClient.ts:11-13, 3-15`, `frontend/src/components/todos/TodoForm.tsx:48-70`, `frontend/src/components/todos/TodoEditForm.tsx:51-68`, `frontend/src/components/todos/TodoDeleteButton.tsx:22-29`, `frontend/src/hooks/useToast.ts:11-23`, `frontend/src/hooks/queries/useCreateTodo.ts:41-50`, `backend/app/api/api.py:45-46, 80-81`, `backend/app/business_logic/decorators.py:31-32`, `backend/app/data_access/repository.py:53-56`, `frontend/src/hooks/queries/useDeleteTodo.ts:31-40`, `backend/tests/test_api/test_delete_to_do.py:58-71`  
**Plain English:** Every failed create, edit or delete is retried automatically once, and the error message also offers a Retry button. Both send exactly the same request, including the same ToDo id, so retries can never create duplicates but can report a failure for something that actually worked.  
**Specification:**  
  Given A user submits "Buy milk". The UI generates id X once per submit. The server saves the ToDo but the response is lost on the network.  
  When  The mutation's single automatic retry fires, or the user clicks 'Retry' in the error toast  
  Then  POST /todo is sent again with id X. The server answers 409 "ToDo already exists". The UI shows 'Failed to create todo' with 'API Error 409: ToDo already exists' and rolls back the optimistic item. The refetch that follows then shows the ToDo was saved after all.  
**Parameters:** mutations.retry = 1; queries.retry = 1 (queryClient.ts:8,12); toast default duration = 5000 ms; Retry action label 'Retry' (useToast.ts:12,18-21)  
**Edge cases handled:** Delete: if the first DELETE succeeded but the response was lost, the retry gets 404 'ToDo not found' and an error toast, even though the ToDo was deleted (on top of the success toast already shown); Update: resending is harmless because the same title/description are written again; The automatic retry fires on any error, including 400 blocklist rejections and 409, so a blocked title is sent twice; A successful toast Retry calls mutate() without the original onSuccess, so the input isn't cleared and no 'Todo created' toast appears; Retries also fire for permanent 4xx rejections. A title containing a blocklisted word (for example 'or') is sent twice and rejected twice with 400 before the error toast appears.; The 'Todo deleted' success toast has already been shown before any of this happens (TodoDeleteButton.tsx:16-20). The user can therefore see a success toast and a failure toast for the same delete.; The initial list load is also retried once before the error state appears (queryClient.ts:8).  
**Confidence:** Medium — SME: Should creating with an id that already exists and is identical, or deleting a todo that is already deleted, be treated as success, so that automatic or manual resends are safe? Or should the client stop resending non-repeatable operations?  
**Trace:** W-068, W-083

### RULE-051: Any caller may read, edit, complete or delete any todo (no ownership or authorization check)
**Category:** Policy  
**Priority:** P1  
**Source:** `backend/app/api/api.py:22-29, 40-91`, `backend/app/models/todo.py:8-18`, `backend/app/data_access/database.py:89-99`  
**Plain English:** There are no users and no owners: every todo sits in one shared list, and any request that reaches the API can view, change, mark done or delete any todo. The only restriction is a browser-origin (CORS) allow-list.  
**Specification:**  
  Given One backend shared by Alice and Bob. Alice created todo id 3f2b9c1e-0000-4000-8000-000000000001 titled 'Pay rent'.  
  When  Bob sends DELETE /todo/3f2b9c1e-0000-4000-8000-000000000001 (or PUT with {"done": true}) without any credentials  
  Then  The response is HTTP 200 {success: true, message: 'Deleted successfully'}. Alice's todo disappears from every list. No identity is checked, and no actor is recorded on the record.  
**Parameters:** Allowed browser origin = http://localhost:5173 (credentials allowed, all methods and headers); no auth scheme or dependency on any endpoint; the data model has no owner/user field (id, title, description, created_at, updated_at, deleted, done only)  
**Edge cases handled:** CORS only limits browsers on other origins. curl, scripts and server-to-server callers are not restricted at all.; GET /todo lists every active id, so ids do not need to be guessed before deleting or editing someone else's todo.; The e2e suite relies on this: it bulk-deletes every todo through unauthenticated calls (frontend/e2e/todo-validation.spec.ts:6-15).; README.md:3 says the app is a playground 'not intended for production usage'. This is consistent with deliberately having no auth.  
**Confidence:** Medium — SME: Is the todo list meant to stay one shared list with no user accounts, or must the rewrite add per-user ownership so that only the creator can view, edit, complete or delete a todo?  
**Trace:** W-074

### RULE-052: Concurrent edits: last write wins with no conflict detection
**Category:** Policy  
**Priority:** P1  
**Source:** `backend/app/data_access/repository.py:70-84`, `backend/app/schemas/data_schemes/update_todo_schema.py:7-10`, `backend/app/api/api.py:62-66`, `frontend/src/components/todos/TodoEditForm.tsx:15, 51`, `frontend/src/config/queryClient.ts:6-9`  
**Plain English:** When two people edit the same todo, the later save silently overwrites the earlier one. Nothing checks whether the todo changed since the editor loaded it.  
**Specification:**  
  Given Todo X titled 'Buy milk' is loaded in browser A and in browser B. The list cache counts as fresh for 5 minutes and is not refetched when the tab regains focus.  
  When  A saves the title 'Buy oat milk' at 10:00. Then B, whose edit form still holds the 'Buy milk' it captured when opened (TodoEditForm.tsx:15), saves 'Buy whole milk' at 10:01.  
  Then  Both PUTs return 200. The stored title is 'Buy whole milk', and A's change is lost with no warning to either user. update_to_do loads the row by id plus deleted=false and applies the supplied fields (repository.py:72-78). TodoUpdateScheme has no version, ETag or expected-updated_at field, so no precondition can be expressed.  
  And   Every UI save also sends description 'not implemented yet' (TodoEditForm.tsx:51), so a description edited concurrently through the API is overwritten too. Fields not sent in a PUT, such as done, are left as they are.  
**Parameters:** No version or concurrency token exists; staleTime = 5 minutes (queryClient.ts:6); refetchOnWindowFocus = false (queryClient.ts:9)  
**Edge cases handled:** A marks the todo done through the API while B renames it in the UI: done stays true, because B's PUT leaves done out; Two API clients PUT different titles at the same moment: whichever commits last is kept; updated_at is never maintained, so it cannot serve as a conflict check without changes  
**Suspected defect:** Edits can be lost silently with no conflict detection. Because the UI treats the list as fresh for 5 minutes, stale edits are likely.  
**Confidence:** High — citation confirmed by an independent referee; SME: Is last-write-wins acceptable, or should the rewrite reject stale edits (for example with a version number or an If-Match check on updated_at) and tell the second editor?  
**Trace:** W-107

### RULE-053: UI treats the ToDo list as fresh for 5 minutes and does not refetch on tab focus
**Category:** Policy  
**Priority:** P2  
**Source:** `frontend/src/config/queryClient.ts:3-10, 3-15`, `frontend/src/hooks/queries/useTodoList.ts:4-8`, `frontend/src/hooks/queries/useCreateTodo.ts:47-50`, `frontend/src/hooks/queries/useUpdateTodo.ts:45-48`, `frontend/src/hooks/queries/useDeleteTodo.ts:37-40`  
**Plain English:** After the web UI loads the list, it does not fetch it again for 5 minutes unless this user creates, edits or deletes something, so changes made elsewhere do not appear right away.  
**Specification:**  
  Given User A loads the list at 10:00 and user B adds a ToDo at 10:01  
  When  User A returns to the browser tab at 10:04 without doing anything  
  Then  A's list does not show B's ToDo: staleTime is 300,000 ms and refetchOnWindowFocus is false. It refreshes as soon as A creates, edits or deletes something (all ['todos'] queries are invalidated), or when the list is fetched again after 10:05. Cached data with no viewers is dropped after 600,000 ms.  
**Parameters:** staleTime = 300000 ms (5 min); gcTime = 600000 ms (10 min); refetchOnWindowFocus = false; queries.retry = 1  
**Edge cases handled:** A failed list load is retried once before the error and Retry button appear (TodoList.tsx:13-23); Every mutation invalidates all ['todos'] queries whatever page or limit they used; Remounting the list within 5 minutes reuses cached data without asking the server again.  
**Confidence:** Medium — SME: Is a list that can be up to several minutes out of date acceptable, or must the rewrite show other users' and tabs' changes (by polling, refresh on focus, or push updates)?  
**Trace:** W-069, W-088

### RULE-054: User-facing errors read 'API Error &lt;status&gt;: &lt;detail&gt;' and never say which rule failed
**Category:** Policy  
**Priority:** P2  
**Source:** `frontend/src/services/api/client.ts:12-20, 58-70, 58-73, 12-21`, `frontend/src/components/todos/TodoForm.tsx:64-68, 64-70`, `frontend/src/components/todos/TodoEditForm.tsx:62-66, 62-68`, `backend/app/api/api.py:46-50, 45-50, 67-72, 80-85, 40-50, 62-72, 40-41, 62-70`, `frontend/src/components/todos/TodoDeleteButton.tsx:23-29`, `frontend/src/types/todo.ts:76-78`, `backend/app/schemas/data_schemes/create_todo_schema.py:24-29`, `backend/app/business_logic/todo_service.py:59-60`  
**Plain English:** When the server rejects an action, the user sees only a status code and a generic phrase like 'Bad request'. They are not told, for example, that the word 'or' in the title is not allowed.  
**Specification:**  
  Given A user enters the title "Buy milk or bread". The backend blocklist rejects 'or' as a whole word.  
  When  POST /todo returns 400 with body {"detail":"Bad request"}  
  Then  The toast title is 'Failed to create todo' and its description is 'API Error 400: Bad request'  
**Parameters:** Message template: `API Error ${status}: ${detail || statusText}` (client.ts:18)  
**Edge cases handled:** FastAPI schema errors (422) return detail as an array, so the message becomes 'API Error 422: [object Object]'; A non-JSON error body falls back to the HTTP status text; A server crash (500 with no JSON body) gives 'API Error 500: Internal Server Error'; Unhandled server errors (for example GET of a corrupt record, or any list-endpoint failure) return plain text, not JSON. The message then falls back to the status text, 'API Error 500: Internal Server Error'.; A todo deleted elsewhere while being edited gives 'API Error 404: ToDo not found'. The list then refetches and the item disappears.; If the error body is not JSON, the HTTP status text is shown instead (client.ts:60-67).; When a delete fails, the error toast appears after a 'Todo deleted' success toast has already been shown.; Verified: String([{msg:'x'}]) yields '[object Object]' in Node; Blank or whitespace-only title: 422 on create (backend/tests/test_api/test_api_endpoints.py:107-129 asserts 422) but 400 on update (backend/tests/test_api/test_update_to_do.py:132-143 accepts either 400 or 422, so the asymmetry is untested); A missing id, malformed UUID, or non-integer limit/page also produces 422 with an array detail; A non-JSON 500 (for example an unhandled list error) falls back to statusText, giving 'API Error 500: Internal Server Error'  
**Suspected defect:** 422 detail arrays are shown as '[object Object]'. Generic 'Bad request' gives the user no way to tell which word or character was blocked. / The service builds a specific reason ('Invalid characters or SQL keywords in input: ...' at input_sanitizer.py:39, 'Invalid payload: title is required' at field_validator.py:34). The API replaces it with the fixed text 'Bad request' (api.py:48,70,83), so users cannot tell which word or field caused the rejection. / The UI's error contract assumes detail is always a string. The rewrite should normalise validation errors to one shape and one status code for the same rule, whichever layer enforces it.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should users be told why their input was rejected (for example, which word is not allowed)? Or should the blocklist be dropped so that ordinary words like 'or' and 'update' are accepted?  
**Trace:** W-070, W-075, W-092, W-096

### RULE-055: API response envelope: success flag plus payload on success, bare detail on failure
**Category:** Policy  
**Priority:** P2  
**Source:** `backend/app/schemas/api_responses/api_response.py:8-12`, `backend/app/schemas/api_responses/to_do_response.py:8-17`, `backend/app/schemas/api_responses/get_to_do_response.py:9-18`, `backend/app/schemas/api_responses/delete_to_do_response.py:6-8`, `backend/app/api/api.py:44, 57, 66, 79`, `frontend/src/types/todo.ts:40-78`  
**Plain English:** Every successful call returns success = true with the todo, or a 'Deleted successfully' message, and HTTP 200, including for create. Every failure returns only {"detail": "..."}. The envelope's success = false and error fields are never used.  
**Specification:**  
  Given A valid new todo {id: 'a1b2c3d4-0000-4000-8000-000000000001', title: 'Wash dishes'}  
  When  The client POSTs it, later DELETEs it, then DELETEs it again  
  Then  The create returns HTTP 200 (not 201) with {success: true, data: null, message: null, error: null, todo_entry: {...}}. The first delete returns 200 with {success: true, message: 'Deleted successfully', data: null, error: null}. The second delete returns 404 with {detail: 'ToDo not found'}, with no success field.  
**Parameters:** Create success status = 200; delete success message = 'Deleted successfully'; single-todo responses require todo_entry to be present  
**Edge cases handled:** Single-todo responses declare todo_entry as required, so a missing todo is rejected by the type. The extra 'must not be null' validator never adds anything, because pydantic model instances are always truthy.; The frontend only reads detail from failures (types/todo.ts:76-78) and never checks success = false.  
**Suspected defect:** ApiResponse defines error, data and success = false (api_response.py:9-12), but no endpoint ever fills them. Clients built against the documented envelope would expect failures in that shape and find {detail} instead.  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-079

### RULE-056: API responses always report deleted = false
**Category:** Policy  
**Priority:** P2  
**Source:** `backend/app/schemas/data_schemes/todo_schema.py:22-25`, `backend/app/data_access/repository.py:86-97`, `frontend/src/types/todo.ts:9-17`, `frontend/src/hooks/queries/useCreateTodo.ts:21-29`  
**Plain English:** Every todo the API returns includes a 'deleted' flag, but deleted todos are never returned, so the flag always reads false and tells the client nothing.  
**Specification:**  
  Given An active todo  
  When  It is returned by create, get, update or list  
  Then  The payload contains "deleted": false. A soft-deleted todo is never returned at all (get and update give 404, list leaves it out), so "deleted": true never appears.  
**Parameters:** ToDoSchema.deleted default False; the read queries filter deleted.is_(False).  
**Edge cases handled:** The front-end type declares the field, and optimistic inserts hard-code deleted:false, but no UI reads it.  
**Confidence:** High — citation confirmed by an independent referee; SME: Should the rewrite drop 'deleted' from the public contract, or keep it for a planned restore or trash view (README 'Further steps')?  
**Trace:** W-091

### RULE-057: Result toasts, including the Retry offer, disappear after 5 seconds of active page time and cannot be dismissed manually
**Category:** Policy  
**Priority:** P2  
**Source:** `frontend/src/hooks/useToast.ts:12-22`, `frontend/src/lib/toaster.ts:3-6`, `frontend/src/components/ui/toaster.tsx:29-32`  
**Plain English:** Every success or failure notice disappears on its own after 5 seconds (the timer pauses while the page is idle or hidden), so the one-click Retry after a failed create, edit or delete is only offered for that window.  
**Specification:**  
  Given A create request that fails with a server error, while the user keeps the tab in the foreground  
  When  The error toast 'Failed to create todo' appears with a Retry action  
  Then  The toast and its Retry button stay visible for 5,000 ms and then auto-dismiss. After that the user can only retry by submitting the form again (the typed text is kept). There is no close button, because 'closable' is never set.  
**Parameters:** duration = 5000 ms (default in useAppToast, never overridden by callers); placement = bottom-end; pauseOnPageIdle = true; Retry action label = 'Retry'.  
**Edge cases handled:** If the tab is hidden or the page is idle, the 5-second countdown pauses (pauseOnPageIdle); Success toasts use the same 5-second duration; None of the callers in the components passes a custom duration; User switches tabs or leaves the page idle: the timer pauses and the Retry offer lasts longer; For a create failure, the typed text stays in the input, so the user can resubmit by pressing Enter after the toast expires; Several failures in a row stack separate toasts, each with its own 5-second window  
**Confidence:** Medium — SME: Should the Retry offer after a failed save stay until the user dismisses it, or is a 5-second auto-dismiss (paused while the tab is hidden or idle) the intended behavior? Also, confirm whether the Chakra/Zag pauseOnPageIdle semantics (pause while the document is hidden) are what the business expects. | Should failure notifications stay until the user dismisses them, so the Retry offer cannot expire unnoticed? Is 5 seconds the right lifetime for success messages?  
**Trace:** W-097, W-108

### RULE-058: No request-rate limit or quota on creating todos, even though a rate-limiting library is declared
**Category:** Policy  
**Priority:** P2  
**Source:** `pyproject.toml:19`, `backend/app/api/api.py:20-31, 20-29`, `backend/app/data_access/repository.py:45-51`  
**Plain English:** Any caller can create, edit or delete todos as often as they like, and there is no cap on how many todos exist. A rate-limiting dependency (slowapi) is listed but never wired in.  
**Specification:**  
  Given A client that sends 10,000 POST /todo requests with distinct UUIDs in one minute  
  When  The requests reach the API  
  Then  All of them are accepted. No limiter middleware or decorator is registered, and the repository inserts without counting existing rows.  
**Parameters:** Declared dependency slowapi &gt;= 0.1.9 (pyproject.toml:19). No imports of slowapi, Limiter, or any rate-limit configuration anywhere in backend or frontend code (grep returned no matches).  
**Edge cases handled:** The e2e harness cleans up by listing up to limit=1000 rows (frontend/e2e/global-setup.ts:8), which implicitly assumes no server-side cap on page size; Combined with the missing ownership checks recorded earlier, a single client can fill the shared list without bound; CORS limits only browsers on other origins; scripts and non-browser clients are not restricted  
**Confidence:** Low — SME: Was a per-client rate limit or a maximum number of todos intended (slowapi is a declared dependency)? If so, what limits apply (requests per minute per IP or user, maximum active todos), and should the rewrite enforce them? | Was per-client rate limiting meant to be part of the product (slowapi is a declared dependency but unused)? If so, what limits per endpoint, and what should the user see when throttled?  
**Trace:** W-098, W-104

### RULE-059: The design doc's SUCCESS/FAILURE response status is not implemented
**Category:** Policy  
**Priority:** P2  
**Source:** `documentation/backend.puml:22-25, 44-66, 68, 75-78`, `backend/app/schemas/api_responses/api_response.py:8-12`, `backend/app/api/api.py:44, 57, 66, 79, 91`  
**Plain English:** The design document says every API response carries a status of SUCCESS or FAILURE. The code instead sends success=true on successes and only an error detail on failures, so FAILURE never appears.  
**Specification:**  
  Given The design doc gives ToDoResponse, GetToDoResponse, ListToDoResponse and DeleteToDoResponse a field 'status: Status' (an enum of SUCCESS or FAILURE)  
  When  A client calls GET /todo/{missing id}, or POST /todo with a valid new todo  
  Then  Missing id: HTTP 404 with body {detail: 'ToDo not found'}, with no status or success field. Valid create: HTTP 200 with {success: true, todo_entry: {...}, data: null, message: null, error: null}, with no status field.  
**Parameters:** Implemented field: success (boolean, always true when present). Documented field: status enum SUCCESS/FAILURE. Unused envelope fields: data and error, always null. message is set only on delete ('Deleted successfully').  
**Edge cases handled:** The success=false / FAILURE state can't be reached through any endpoint; Clients built from the design doc would look for a 'status' field that doesn't exist  
**Suspected defect:** Documentation drift. The same file misspells created_at as 'reated_at' (backend.puml:31) and still marks the database package as 'Currently under reconstruction' (backend.puml:82).  
**Confidence:** High — citation confirmed by an independent referee  
**Trace:** W-122

## Rules requiring SME confirmation

Every rule below is Medium or Low confidence. Each needs a human answer before it can anchor a behaviour contract. P0 rules are listed first.

- **RULE-001** (P1, Medium): List pagination: offset formula, defaults, and unbounded page/limit inputs
  - What are the valid ranges for page and limit (for example page &gt;= 1, 1 &lt;= limit &lt;= 100)? Should out-of-range values be rejected with 422 or clamped? What sort order should the list use (created_at ascending or descending, title)?
  - What are the allowed ranges for page and limit (for example page &gt;= 1 and 1 &lt;= limit &lt;= 100), and what should happen when they're out of range?
  - What are the allowed ranges for limit and page (for example limit 1-100, page &gt;= 1), and should out-of-range values be rejected with 422 or clamped? Does any consumer rely on limit=-1 or very large limits to fetch everything?
- **RULE-010** (P1, Medium): Soft-deleted ToDos are invisible to every read and update
  - Criticality: the two-judge P0 panel split on whether this guards data integrity. Confirm P0 vs P1. P0 panel split on whether this moves money / is regulatory (Faithful: yes. I read repository.py:70-97 and checked how the service and API use it. All three repository methods filter on `deleted.is_(False)`: update_to_do at lines 72-74, get_to_do_entry at 88-90 and get_all_to_do_entries at 95-97. Each path ends where the card says it does: - GET /to… (full judge reasoning in rules_workflow_result.json)
  - Is there a business need to restore (undelete) todos, or to let an administrator see deleted items?
- **RULE-011** (P1, Medium): Partial update changes only the fields supplied
  - Should an explicit null title be rejected with 400 'title is required'? Should clients be allowed to clear the description by sending null?
- **RULE-013** (P1, Medium): Title and description limited to 255 characters (enforced only by the DB CHECK and the UI)
  - Is 255 characters the real business limit for both title and description? Should the API check it explicitly and return a clear validation error?
  - Should the API validate the 255-character limit itself and return 400/422 with a clear message?
- **RULE-014** (P1, Medium): SQL keyword and symbol blocklist on all title/description text
  - Should the rewrite keep this keyword blocklist, given that it rejects common task wording? Or can it be dropped in favor of parameterized queries, keeping only explicit length and format rules?
  - Is rejecting natural-language titles that contain words like 'or', 'update', 'create', 'delete', 'select', 'drop' or a semicolon intended behavior that must be preserved, or was it a security over-reach that the new system (using parameterized queries) should drop?
  - Is it acceptable that ordinary words such as 'or', 'update', 'create', 'select' and 'drop', and the symbols ';', '--' and '/*', are forbidden in ToDo text? Or should the rewrite rely on parameterized queries and drop the blocklist?
- **RULE-018** (P1, Medium): Explicit null title or done on edit causes a server error
  - Should explicit null for title or done be rejected with 400/422?
- **RULE-020** (P1, Medium): Any UUID version, including the all-zero (nil) UUID, is accepted as a ToDo id
  - Should the server accept only randomly generated (v4) ids and reject the nil UUID and non-canonical spellings, or is any parseable UUID acceptable?
- **RULE-024** (P1, Medium): The done flag accepts loosely typed values such as 'yes', 'on', '1' and 1
  - Should the API accept only JSON true/false for 'done', or does any client depend on string or number forms ('yes', '1', 1)? A rewrite in another stack will not reproduce pydantic's lax coercion unless this is decided.
  - Should the rewrite accept only JSON true/false for the completion flag (strict), or are clients known to send string or numeric forms that must keep working? (Not verified at runtime: pydantic is not installed in the analysis environment.)
- **RULE-026** (P1, Medium): The server accepts line breaks and tabs inside titles, but the web UI edits titles on a single line
  - Are titles meant to be single-line? Should the server reject or normalize CR/LF, tabs and other control characters in titles, and should descriptions keep multi-line text?
- **RULE-034** (P1, Medium): New ToDo initial state and server-local creation timestamp
  - Should created_at be stored in UTC with a timezone? Should a newly created ToDo have updated_at null or equal to created_at?
- **RULE-035** (P1, Medium): Last-updated timestamp: set by the DB clock (UTC) at insert, never refreshed on change
  - Should updated_at be set to the current time on every edit, completion, and delete? Is any report or sort order expected to rely on it?
  - Should a newly created ToDo have updated_at = null (builder intent) or = its creation time? Which clock and timezone should all ToDo timestamps use: server local or UTC? (Engineering: please confirm with a real-SQLite integration test that POST /todo returns a non-null updated_at.)
  - Should a newly created todo have updated_at empty, equal to created_at, or the insert time? And should all timestamps be stored in UTC?
- **RULE-037** (P1, Medium): New todos must start not-deleted, but the model's default for 'deleted' is not a boolean (masked by the builder)
  - Is there any creation path other than POST /todo (bulk import, data migration, admin script) that must create todos? If so, confirm they must always start with deleted = false and done = false regardless of how they are constructed.
  - Engineering to confirm: can ToDoEntryData ever be created without an explicit 'deleted' value (imports, scripts, a future restore feature)? The rewrite should make 'not deleted' the explicit default.
- **RULE-039** (P1, Medium): The README roadmap's todo lifecycle differs from what the code implements
  - Which roadmap transitions belong in the target lifecycle? (a) Restore of soft-deleted todos: should it exist, and for how long after deletion? (b) Bulk purge of all soft-deleted todos: who may trigger it, and should there be an automatic retention period instead? (c) A UI control for done/reopen?
- **RULE-046** (P1, Medium): UI delete: confirmation prompt, success toast before the server confirms, silent reappearance on failure
  - Should the delete success message wait for server confirmation?
  - Should a failed delete always tell the user and offer a retry? And should 'Todo deleted' appear only after the server confirms? (Engineering should confirm with a forced-500 test that the onError toast never fires in the current build.)
- **RULE-049** (P1, Medium): No purge path: soft-deleted ToDos are kept forever (hard delete is unreachable and works only on active rows)
  - What retention period applies to deleted todos (for example a GDPR or erasure requirement)? Should hard_delete_to_do be exposed through a scheduled purge or an erasure request?
- **RULE-050** (P1, Medium): Failed requests are retried once automatically, reusing the same client-generated id
  - Should creating with an id that already exists and is identical, or deleting a todo that is already deleted, be treated as success, so that automatic or manual resends are safe? Or should the client stop resending non-repeatable operations?
- **RULE-051** (P1, Medium): Any caller may read, edit, complete or delete any todo (no ownership or authorization check)
  - Is the todo list meant to stay one shared list with no user accounts, or must the rewrite add per-user ownership so that only the creator can view, edit, complete or delete a todo?
- **RULE-040** (P2, Medium): Inline edit lifecycle: View -&gt; Edit -&gt; View; editing hides Delete; Cancel discards (even mid-save)
  - While a save is pending, should the edit form be locked (input and Cancel disabled), as the create form is? And must the outcome of a save always be reported, even if the user has closed the editor?
- **RULE-053** (P2, Medium): UI treats the ToDo list as fresh for 5 minutes and does not refetch on tab focus
  - Is a list that can be up to several minutes out of date acceptable, or must the rewrite show other users' and tabs' changes (by polling, refresh on focus, or push updates)?
- **RULE-057** (P2, Medium): Result toasts, including the Retry offer, disappear after 5 seconds of active page time and cannot be dismissed manually
  - Should the Retry offer after a failed save stay until the user dismisses it, or is a 5-second auto-dismiss (paused while the tab is hidden or idle) the intended behavior? Also, confirm whether the Chakra/Zag pauseOnPageIdle semantics (pause while the document is hidden) are what the business expects.
  - Should failure notifications stay until the user dismisses them, so the Retry offer cannot expire unnoticed? Is 5 seconds the right lifetime for success messages?
- **RULE-058** (P2, Low): No request-rate limit or quota on creating todos, even though a rate-limiting library is declared
  - Was a per-client rate limit or a maximum number of todos intended (slowapi is a declared dependency)? If so, what limits apply (requests per minute per IP or user, maximum active todos), and should the rewrite enforce them?
  - Was per-client rate limiting meant to be part of the product (slowapi is a declared dependency but unused)? If so, what limits per endpoint, and what should the user see when throttled?

