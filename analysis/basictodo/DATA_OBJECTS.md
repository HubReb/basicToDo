# Data Objects: basicToDo

_Companion to [BUSINESS_RULES.md](BUSINESS_RULES.md). Catalogued by the `/modernize-extract-rules` workflow's DTO agent; rule references remapped to the consolidated RULE-### IDs._

**29 objects.** One persisted entity (`toDo`) is reached through three backend shapes: the domain dataclass, an imperative Table mapping, and a declarative ORM class used only for DDL. It reaches the wire through Pydantic request/response models and is mirrored by hand in TypeScript on the frontend.

| # | Object | Source | Fields | Used by rules |
|---|---|---|---:|---|
| 1 | [ToDoEntryData (domain entity / persistence record)](#obj-1) | `backend/app/models/todo.py:9` | 8 | RULE-001, RULE-005, RULE-008, RULE-009, RULE-010, RULE-011, RULE-019, RULE-031, RULE-032, RULE-033, RULE-034, RULE-035, RULE-037, RULE-038, RULE-039, RULE-048, RULE-049, RULE-051, RULE-052 |
| 2 | [to_do_table (runtime imperative Table mapping for "toDo")](#obj-2) | `backend/app/data_access/database.py:89` | 7 | RULE-001, RULE-010, RULE-031, RULE-034, RULE-035 |
| 3 | [ToDoORM (declarative DDL source for the physical "toDo" table)](#obj-3) | `backend/app/data_access/database.py:68` | 9 | RULE-003, RULE-008, RULE-013, RULE-018, RULE-021, RULE-029, RULE-038, RULE-049, RULE-051, RULE-052 |
| 4 | [ToDoCreateScheme (POST /todo request body)](#obj-4) | `backend/app/schemas/data_schemes/create_todo_schema.py:8` | 4 | RULE-004, RULE-005, RULE-008, RULE-012, RULE-014, RULE-017, RULE-020, RULE-022, RULE-026, RULE-027, RULE-029, RULE-030 |
| 5 | [TodoUpdateScheme (PUT /todo/{id} body; also the internal mark-done command)](#obj-5) | `backend/app/schemas/data_schemes/update_todo_schema.py:7` | 4 | RULE-004, RULE-005, RULE-011, RULE-012, RULE-014, RULE-017, RULE-018, RULE-019, RULE-022, RULE-023, RULE-024, RULE-027, RULE-032, RULE-033, RULE-052 |
| 6 | [ToDoSchema (response read model / outbound DTO)](#obj-6) | `backend/app/schemas/data_schemes/todo_schema.py:10` | 8 | RULE-004, RULE-005, RULE-009, RULE-011, RULE-019, RULE-034, RULE-035, RULE-056 |
| 7 | [ApiResponse (base success envelope)](#obj-7) | `backend/app/schemas/api_responses/api_response.py:8` | 4 | RULE-055, RULE-059 |
| 8 | [ToDoResponse (POST /todo and PUT /todo/{id} response)](#obj-8) | `backend/app/schemas/api_responses/to_do_response.py:8` | 2 | RULE-032, RULE-034, RULE-055, RULE-059 |
| 9 | [GetToDoResponse (GET /todo/{id} response)](#obj-9) | `backend/app/schemas/api_responses/get_to_do_response.py:9` | 2 | RULE-010, RULE-055, RULE-059 |
| 10 | [ListToDoResponse (GET /todo response)](#obj-10) | `backend/app/schemas/api_responses/get_list_to_do_response.py:10` | 3 | RULE-001, RULE-002, RULE-009, RULE-028, RULE-048, RULE-055, RULE-059 |
| 11 | [DeleteToDoResponse (DELETE /todo/{id} response)](#obj-11) | `backend/app/schemas/api_responses/delete_to_do_response.py:6` | 2 | RULE-031, RULE-055, RULE-059 |
| 12 | [Request path/query parameters (implicit, from the FastAPI signatures)](#obj-12) | `backend/app/api/api.py:89` | 3 | RULE-001, RULE-016, RULE-020, RULE-048 |
| 13 | [HTTP error body (FastAPI HTTPException / request-validation error)](#obj-13) | `backend/app/api/api.py:45` | 3 | RULE-008, RULE-018, RULE-022, RULE-027, RULE-047, RULE-054, RULE-055 |
| 14 | [ToDoError exception taxonomy (business outcome codes)](#obj-14) | `backend/app/business_logic/exceptions.py:4` | 5 | RULE-008, RULE-014, RULE-018, RULE-027, RULE-047 |
| 15 | [Status enum and status-based responses (design doc only; NOT implemented)](#obj-15) | `documentation/backend.puml:22` | 3 | RULE-059 |
| 16 | [Config (backend app configuration record; dead code)](#obj-16) | `backend/app/config.py:6` | 6 | — |
| 17 | [Todo (frontend entity)](#obj-17) | `frontend/src/types/todo.ts:9` | 7 | RULE-005, RULE-007, RULE-045, RULE-056 |
| 18 | [TodoCreateRequest (frontend create payload)](#obj-18) | `frontend/src/types/todo.ts:22` | 3 | RULE-003, RULE-006, RULE-008, RULE-015, RULE-025, RULE-030, RULE-036, RULE-041, RULE-044, RULE-050 |
| 19 | [TodoUpdateRequest (frontend edit payload)](#obj-19) | `frontend/src/types/todo.ts:31` | 3 | RULE-003, RULE-006, RULE-007, RULE-015, RULE-017, RULE-025, RULE-030, RULE-036, RULE-044, RULE-050 |
| 20 | [ApiResponse / TodoResponse / GetTodoResponse (frontend response envelopes)](#obj-20) | `frontend/src/types/todo.ts:40` | 2 | RULE-055 |
| 21 | [TodoListResponse (frontend list payload / query-cache entry)](#obj-21) | `frontend/src/types/todo.ts:61` | 3 | RULE-002, RULE-007, RULE-042, RULE-045, RULE-046, RULE-053 |
| 22 | [DeleteTodoResponse (frontend delete payload)](#obj-22) | `frontend/src/types/todo.ts:69` | 2 | RULE-046 |
| 23 | [ApiError (frontend error body type)](#obj-23) | `frontend/src/types/todo.ts:76` | 1 | RULE-054, RULE-055 |
| 24 | [ApiClientError (frontend error record)](#obj-24) | `frontend/src/services/api/client.ts:12` | 4 | RULE-054 |
| 25 | [Optimistic mutation context (rollback snapshot)](#obj-25) | `frontend/src/hooks/queries/useCreateTodo.ts:39` | 1 | RULE-007, RULE-040, RULE-046 |
| 26 | [ToastOptions (frontend notification record)](#obj-26) | `frontend/src/hooks/useToast.ts:3` | 5 | RULE-036, RULE-040, RULE-046, RULE-050, RULE-054, RULE-057 |
| 27 | [QueryClient default options (frontend cache / retry policy record)](#obj-27) | `frontend/src/config/queryClient.ts:3` | 5 | RULE-050, RULE-053 |
| 28 | [TodoItemProps / TodoEditFormProps (UI view-model props)](#obj-28) | `frontend/src/components/todos/TodoItem.tsx:6` | 5 | RULE-026, RULE-040, RULE-045 |
| 29 | [ErrorBoundary Props/State (frontend crash record)](#obj-29) | `frontend/src/components/errors/ErrorBoundary.tsx:4` | 4 | RULE-043 |

<a id="obj-1"></a>
## 1. ToDoEntryData (domain entity / persistence record)

**Source:** `backend/app/models/todo.py:9`  
**Used by rules:** RULE-001, RULE-005, RULE-008, RULE-009, RULE-010, RULE-011, RULE-019, RULE-031, RULE-032, RULE-033, RULE-034, RULE-035, RULE-037, RULE-038, RULE-039, RULE-048, RULE-049, RULE-051, RULE-052

| Field | Type | Note |
|---|---|---|
| `id` | `uuid.UUID` | Primary key, supplied by the client. Normalised by UUIDValidator in the builder (todo_entry_builder.py:27). There is no server-side generation on the runtime path. |
| `title` | `str` | Checked against the blocklist and trimmed by FieldValidator.validate_required (todo_entry_builder.py:28; field_validator.py:29-35). Changed through setattr on update (repository.py:77-78). |
| `description` | `str (declared), effectively str \| None` | On create, a missing or blank value becomes "" (field_validator.py:37-40). An explicit null on update is written as NULL (repository.py:77-78). The type annotation does not reflect the None case. |
| `created_at` | `datetime \| None` | Set to datetime.datetime.now(): server-local and naive (todo_entry_builder.py:30). No code path changes it afterwards. |
| `updated_at` | `datetime \| None` | The builder sets None (todo_entry_builder.py:31). At INSERT, the to_do_table default func.now() fills it (database.py:96). Inferred from SQLAlchemy behaviour: None on a column with a default is left out of the INSERT. Never touched on update. |
| `deleted` | `Mapped[bool] (the dataclass default is a mapped_column() object, not False)` | todo.py:17. The default is a MappedColumn instance, so building the object without deleted= leaves a non-boolean value. The builder hides this by passing deleted=False (todo_entry_builder.py:32). Set to True only by repository.delete_to_do (repository.py:58). Every read and update filters on deleted IS FALSE (repository.py:73, :89, :96). |
| `done` | `bool = False` | Changed only through TodoUpdateScheme via setattr (repository.py:77-78). There is no completion timestamp. |
| `(absent) owner / version / done_at / deleted_at` | `n/a` | No ownership, optimistic-lock version, completion time or deletion time is modelled (todo.py:9-18). |

<a id="obj-2"></a>
## 2. to_do_table (runtime imperative Table mapping for "toDo")

**Source:** `backend/app/data_access/database.py:89`  
**Used by rules:** RULE-001, RULE-010, RULE-031, RULE-034, RULE-035

| Field | Type | Note |
|---|---|---|
| `id` | `UUIDType(binary=False), PK, index, default uuid.uuid4` | database.py:92. The uuid4 default never fires because the builder always supplies the id. |
| `title` | `String(255) NOT NULL, index` | database.py:93. No CHECK constraint in this definition. |
| `description` | `String(255) NULL` | database.py:94 |
| `created_at` | `TIMESTAMP(timezone=True) NOT NULL, default func.now()` | database.py:95. Overridden by the explicit datetime.now() from the builder. |
| `updated_at` | `TIMESTAMP(timezone=True) NULL, default func.now()` | database.py:96. This client-side default is the only reason updated_at gets a value: CURRENT_TIMESTAMP, which is UTC on SQLite. Nothing refreshes it on update. |
| `deleted` | `Boolean NOT NULL, default False` | database.py:97 |
| `done` | `Boolean NOT NULL, default False` | database.py:98 |

<a id="obj-3"></a>
## 3. ToDoORM (declarative DDL source for the physical "toDo" table)

**Source:** `backend/app/data_access/database.py:68`  
**Used by rules:** RULE-003, RULE-008, RULE-013, RULE-018, RULE-021, RULE-029, RULE-038, RULE-049, RULE-051, RULE-052

| Field | Type | Note |
|---|---|---|
| `id` | `UUIDType(binary=False) PRIMARY KEY` | database.py:71. The PK uniqueness makes duplicate ids raise IntegrityError, which becomes ToDoAlreadyExistsError (decorators.py:31-32). Inferred from sqlalchemy_utils: stored as CHAR(32) hex on SQLite. |
| `title` | `String(255) NOT NULL, non-unique index` | database.py:72. The index is not unique, so duplicate titles are allowed. |
| `description` | `String(255) NULL` | database.py:73 |
| `created_at` | `TIMESTAMP(tz) NOT NULL, default=datetime.datetime.now()` | database.py:74. Magic value: now() is evaluated once at import, giving a fixed timestamp. Runtime inserts do not go through this class. |
| `updated_at` | `TIMESTAMP(tz) NULL` | database.py:75 |
| `deleted` | `Boolean NOT NULL default False` | database.py:76 |
| `done` | `Boolean NOT NULL default False` | database.py:77. NOT NULL means an explicit {"done": null} edit fails as an IntegrityError. |
| `title_length_check` | `CHECK length(title) <= 255` | database.py:80. The only server-side length limit. length() counts characters, while the UI counts UTF-16 units. On SQLite, length() stops at an embedded NUL. |
| `description_length_check` | `CHECK length(description) <= 255` | database.py:81 |

<a id="obj-4"></a>
## 4. ToDoCreateScheme (POST /todo request body)

**Source:** `backend/app/schemas/data_schemes/create_todo_schema.py:8`  
**Used by rules:** RULE-004, RULE-005, RULE-008, RULE-012, RULE-014, RULE-017, RULE-020, RULE-022, RULE-026, RULE-027, RULE-029, RULE-030

| Field | Type | Note |
|---|---|---|
| `id` | `UUID (required)` | create_todo_schema.py:9. Pydantic lax parsing accepts any UUID version and alternate spellings. The check `if not value` (line 16) never fails because UUID objects are always truthy, so the nil UUID is accepted. The builder re-validates it (todo_entry_builder.py:27). |
| `title` | `str (required)` | Lines 24-29: rejects None or blank using Python str.strip() whitespace rules (HTTP 422) and returns the stripped value. The builder then applies the blocklist and trims again (field_validator.py:29-35; input_sanitizer.py:13-15, :37-41), giving HTTP 400. There is no max_length. |
| `description` | `Optional[str] = None` | Line 11. Blocklist checked and blank turned into "" in the builder (todo_entry_builder.py:29). There is no max_length. |
| `(extra fields)` | `ignored` | No model_config is set, so Pydantic v2 drops unknown keys by default (extra='ignore'). Client-sent done, deleted, timestamps and misspelt keys are silently discarded. |

<a id="obj-5"></a>
## 5. TodoUpdateScheme (PUT /todo/{id} body; also the internal mark-done command)

**Source:** `backend/app/schemas/data_schemes/update_todo_schema.py:7`  
**Used by rules:** RULE-004, RULE-005, RULE-011, RULE-012, RULE-014, RULE-017, RULE-018, RULE-019, RULE-022, RULE-023, RULE-024, RULE-027, RULE-032, RULE-033, RULE-052

| Field | Type | Note |
|---|---|---|
| `title` | `Optional[str] = None` | Validated only when not None (todo_service.py:59-60): blocklist, then blank becomes ToDoValidationError (400). An explicit null skips validation and is written as NULL. The NOT NULL failure becomes ToDoAlreadyExistsError, which the PUT handler does not catch (api.py:67-72), so the response is 500. |
| `description` | `Optional[str] = None` | Validated only when not None (todo_service.py:61-62). Blank is stored as "" and an explicit null as NULL. Both read back as null. |
| `done` | `Optional[bool] = None` | Pydantic lax bool accepts 'yes', 'on', '1', 1 and similar. A truthy value short-circuits to mark_to_do_as_done (todo_service.py:55-57), dropping the payload's title and description without validating them. false or null goes through the normal partial update. There is no guard on the current state. |
| `(fields-set tracking)` | `model_dump(exclude_unset=True)` | repository.py:77. Only keys the client sent are applied, so an empty body is a successful no-op. The service also builds this object at todo_service.py:94 with a snapshot of title and description plus done=True. |

<a id="obj-6"></a>
## 6. ToDoSchema (response read model / outbound DTO)

**Source:** `backend/app/schemas/data_schemes/todo_schema.py:10`  
**Used by rules:** RULE-004, RULE-005, RULE-009, RULE-011, RULE-019, RULE-034, RULE-035, RULE-056

| Field | Type | Note |
|---|---|---|
| `id` | `UUID` | Lines 13, 51-60 |
| `title` | `str (required)` | Lines 34-40: stripped, and empty raises ValidationError. In the list, failing rows are logged and skipped (todo_service.py:82-85). On a single GET, the error becomes ToDoRepositoryError, which is uncaught at api.py:58, so the response is 500. |
| `description` | `Optional[str] = None` | Lines 42-49: a falsy value (including "") becomes None, otherwise it is stripped. The error text on line 49 wrongly says 'title'. |
| `created_at` | `datetime (required)` | Lines 22, 62-67 |
| `updated_at` | `Optional[datetime] = None` | Line 23 |
| `deleted` | `bool = False` | Line 24. Always false in responses because every read filters out deleted rows. |
| `done` | `bool = False` | Line 25 |
| `Config` | `from_attributes, populate_by_name, arbitrary_types_allowed` | Lines 27-32. Old-style class Config in Pydantic v2. Built from ToDoEntryData with model_validate. |

<a id="obj-7"></a>
## 7. ApiResponse (base success envelope)

**Source:** `backend/app/schemas/api_responses/api_response.py:8`  
**Used by rules:** RULE-055, RULE-059

| Field | Type | Note |
|---|---|---|
| `success` | `bool` | Always True: every endpoint returns it only on success (api.py:44, 57, 66, 79, 91). |
| `data` | `Optional[dict] = None` | No endpoint ever fills it. |
| `message` | `Optional[str] = None` | Only DeleteToDoResponse fills it. |
| `error` | `Optional[str] = None` | Never filled. Failures use HTTPException instead. |

<a id="obj-8"></a>
## 8. ToDoResponse (POST /todo and PUT /todo/{id} response)

**Source:** `backend/app/schemas/api_responses/to_do_response.py:8`  
**Used by rules:** RULE-032, RULE-034, RULE-055, RULE-059

| Field | Type | Note |
|---|---|---|
| `(inherits ApiResponse)` | `success, data, message, error` |  |
| `todo_entry` | `ToDoSchema (required, non-null)` | Lines 10-17. Used at api.py:40, :44, :62, :66. |

<a id="obj-9"></a>
## 9. GetToDoResponse (GET /todo/{id} response)

**Source:** `backend/app/schemas/api_responses/get_to_do_response.py:9`  
**Used by rules:** RULE-010, RULE-055, RULE-059

| Field | Type | Note |
|---|---|---|
| `(inherits ApiResponse)` | `success, data, message, error` |  |
| `todo_entry` | `ToDoSchema (required, non-null)` | Lines 11-18. Used at api.py:53-57. |

<a id="obj-10"></a>
## 10. ListToDoResponse (GET /todo response)

**Source:** `backend/app/schemas/api_responses/get_list_to_do_response.py:10`  
**Used by rules:** RULE-001, RULE-002, RULE-009, RULE-028, RULE-048, RULE-055, RULE-059

| Field | Type | Note |
|---|---|---|
| `(inherits ApiResponse)` | `success, data, message, error` |  |
| `results` | `Optional[int] = 0` | Set to len(todos) for the current page after corrupt rows are skipped (api.py:91). It is not the total count. |
| `todo_entries` | `List[ToDoSchema] (required)` | Lines 16-21 reject only None, so an empty list is valid. The query has no ORDER BY (repository.py:95-97). |

<a id="obj-11"></a>
## 11. DeleteToDoResponse (DELETE /todo/{id} response)

**Source:** `backend/app/schemas/api_responses/delete_to_do_response.py:6`  
**Used by rules:** RULE-031, RULE-055, RULE-059

| Field | Type | Note |
|---|---|---|
| `(inherits ApiResponse)` | `success, data, message, error` |  |
| `message` | `Optional[str] = None` | Always 'Deleted successfully' (api.py:79). The deleted item is not returned. |

<a id="obj-12"></a>
## 12. Request path/query parameters (implicit, from the FastAPI signatures)

**Source:** `backend/app/api/api.py:89`  
**Used by rules:** RULE-001, RULE-016, RULE-020, RULE-048

| Field | Type | Note |
|---|---|---|
| `limit` | `int = 10 (query)` | api.py:89. No range check and no maximum. Passed straight to .limit() (repository.py:97). |
| `page` | `int = 1 (query)` | api.py:89. skip = (page - 1) * limit (repository.py:93). No range check. |
| `todo_id` | `UUID (path)` | api.py:54, :63, :76. FastAPI parses it, and a malformed value gives 422. The service re-validates it with UUIDValidator for get and delete (todo_service.py:47, :72) but not for update. |

<a id="obj-13"></a>
## 13. HTTP error body (FastAPI HTTPException / request-validation error)

**Source:** `backend/app/api/api.py:45`  
**Used by rules:** RULE-008, RULE-018, RULE-022, RULE-027, RULE-047, RULE-054, RULE-055

| Field | Type | Note |
|---|---|---|
| `detail (handled errors)` | `str` | Fixed generic text: 'ToDo already exists' (409, api.py:46), 'Bad request' (400, api.py:48, :70, :83), 'ToDo not found' (404, api.py:59, :68, :81), 'Internal error' (500, api.py:50, :72, :85). It never names the rule that failed. |
| `detail (HTTP 422)` | `list[object] (loc, msg, type, input)` | Generated by FastAPI's RequestValidationError when Pydantic rejects the body or a parameter. This is framework behaviour inferred from FastAPI defaults; the repo does not define it. |
| `(unhandled paths)` | `500` | GET does not map ToDoRepositoryError (api.py:58-59). PUT does not map ToDoAlreadyExistsError (api.py:67-72). GET /todo maps no exceptions at all (api.py:88-91). |

<a id="obj-14"></a>
## 14. ToDoError exception taxonomy (business outcome codes)

**Source:** `backend/app/business_logic/exceptions.py:4`  
**Used by rules:** RULE-008, RULE-014, RULE-018, RULE-027, RULE-047

| Field | Type | Note |
|---|---|---|
| `ToDoError` | `Exception (base)` | exceptions.py:4 |
| `ToDoAlreadyExistsError` | `ToDoError` | exceptions.py:8. Raised for ANY IntegrityError (decorators.py:31-32), including NOT NULL violations on update, not only duplicate ids. |
| `ToDoNotFoundError` | `ToDoError` | exceptions.py:12 |
| `ToDoValidationError` | `ToDoError` | exceptions.py:16. Raised by InputSanitizer (input_sanitizer.py:39), FieldValidator (field_validator.py:34), UUIDValidator (uuid_validator.py:24) and the builder (todo_entry_builder.py:22, :24). |
| `ToDoRepositoryError` | `ToDoError` | exceptions.py:20. Wraps any other exception (decorators.py:33-35), including ToDoSchema ValidationError on a single GET. |

<a id="obj-15"></a>
## 15. Status enum and status-based responses (design doc only; NOT implemented)

**Source:** `documentation/backend.puml:22`  
**Used by rules:** RULE-059

| Field | Type | Note |
|---|---|---|
| `SUCCESS` | `str` | backend.puml:23 |
| `FAILURE` | `str` | backend.puml:24 |
| `status` | `Status (on ToDoResponse, GetToDoResponse, ListToDoResponse, DeleteToDoResponse)` | backend.puml:44-66. The code uses success: bool instead (api_response.py:9). The documented models.ToDo.update(values) method (backend.puml:14) also does not exist. |

<a id="obj-16"></a>
## 16. Config (backend app configuration record; dead code)

**Source:** `backend/app/config.py:6`  
**Used by rules:** —

| Field | Type | Note |
|---|---|---|
| `db_path` | `str` | config.py:8. _get_db_path() reads self.config_file before it is assigned on line 11, so it would raise AttributeError when DATABASE_URL is unset. |
| `database_url` | `str` | config.py:9 |
| `reload` | `bool` | config.py:10, from the RELOAD env var |
| `config_file` | `str` | config.py:11. config_dummy.json:2 holds only a placeholder db_path and no credentials. |
| `port` | `int` | config.py:22 |
| `host` | `str` | config.py:23 |

<a id="obj-17"></a>
## 17. Todo (frontend entity)

**Source:** `frontend/src/types/todo.ts:9`  
**Used by rules:** RULE-005, RULE-007, RULE-045, RULE-056

| Field | Type | Note |
|---|---|---|
| `id` | `string` |  |
| `title` | `string` |  |
| `description` | `string \| null` |  |
| `created_at` | `string (ISO)` |  |
| `updated_at` | `string \| null` | Set optimistically on the client to new Date().toISOString() during an edit (useUpdateTodo.ts:29), which the server never does. |
| `deleted` | `boolean` |  |
| `done` | `boolean` | Never rendered: TodoList passes only id and title to TodoItem (TodoList.tsx:38-42). |

<a id="obj-18"></a>
## 18. TodoCreateRequest (frontend create payload)

**Source:** `frontend/src/types/todo.ts:22`  
**Used by rules:** RULE-003, RULE-006, RULE-008, RULE-015, RULE-025, RULE-030, RULE-036, RULE-041, RULE-044, RULE-050

| Field | Type | Note |
|---|---|---|
| `id` | `string` | uuid() v4 generated once per submit (TodoForm.tsx:49). Retry reuses the same object (TodoForm.tsx:69). |
| `title` | `string` | item.trim() (TodoForm.tsx:50), after the UI check for blank or more than 255 UTF-16 units (TodoForm.tsx:15-27). There is no blocklist pre-check. |
| `description` | `string \| null (optional)` | Always the hard-coded placeholder 'not implemented yet' (TodoForm.tsx:51). |

<a id="obj-19"></a>
## 19. TodoUpdateRequest (frontend edit payload)

**Source:** `frontend/src/types/todo.ts:31`  
**Used by rules:** RULE-003, RULE-006, RULE-007, RULE-015, RULE-017, RULE-025, RULE-030, RULE-036, RULE-044, RULE-050

| Field | Type | Note |
|---|---|---|
| `title` | `string (optional)` | title.trim() (TodoEditForm.tsx:51), after the UI validation at TodoEditForm.tsx:20-32. |
| `description` | `string \| null (optional)` | Always 'not implemented yet' (TodoEditForm.tsx:51). |
| `done` | `boolean (optional)` | Declared but never sent by any UI component. |

<a id="obj-20"></a>
## 20. ApiResponse / TodoResponse / GetTodoResponse (frontend response envelopes)

**Source:** `frontend/src/types/todo.ts:40`  
**Used by rules:** RULE-055

| Field | Type | Note |
|---|---|---|
| `success` | `boolean` | todo.ts:41. The backend's data, message and error fields are not mirrored. |
| `todo_entry` | `Todo` | TodoResponse todo.ts:47-49, GetTodoResponse todo.ts:54-56. GetTodoResponse is used only by todoApi.getById (todoApi.ts:35-38), which no component calls. |

<a id="obj-21"></a>
## 21. TodoListResponse (frontend list payload / query-cache entry)

**Source:** `frontend/src/types/todo.ts:61`  
**Used by rules:** RULE-002, RULE-007, RULE-042, RULE-045, RULE-046, RULE-053

| Field | Type | Note |
|---|---|---|
| `success` | `boolean` |  |
| `results` | `number` | Adjusted by +1/-1 in optimistic updates (useCreateTodo.ts:34, useDeleteTodo.ts:24). |
| `todo_entries` | `Todo[]` | Cached under the query key ['todos', {limit, page}] (useTodoList.ts:6). The UI only ever asks for (10, 1) (TodoList.tsx:9). The form is rendered only after a successful load (TodoList.tsx:11-30). |

<a id="obj-22"></a>
## 22. DeleteTodoResponse (frontend delete payload)

**Source:** `frontend/src/types/todo.ts:69`  
**Used by rules:** RULE-046

| Field | Type | Note |
|---|---|---|
| `success` | `boolean` |  |
| `message` | `string` | The return value is ignored. The 'Todo deleted' toast fires before the request is sent (TodoDeleteButton.tsx:14-22). |

<a id="obj-23"></a>
## 23. ApiError (frontend error body type)

**Source:** `frontend/src/types/todo.ts:76`  
**Used by rules:** RULE-054, RULE-055

| Field | Type | Note |
|---|---|---|
| `detail` | `string` | Typed as string, but a 422 sends an array. Interpolating it at client.ts:18 produces '[object Object]'. |

<a id="obj-24"></a>
## 24. ApiClientError (frontend error record)

**Source:** `frontend/src/services/api/client.ts:12`  
**Used by rules:** RULE-054

| Field | Type | Note |
|---|---|---|
| `status` | `number` |  |
| `statusText` | `string` |  |
| `detail` | `string \| undefined` | Taken from body.detail, falling back to statusText (client.ts:60-69). |
| `message` | `string` | Built as `API Error ${status}: ${detail \|\| statusText}` (client.ts:18). This is the text shown in toasts and in ErrorMessage. |

<a id="obj-25"></a>
## 25. Optimistic mutation context (rollback snapshot)

**Source:** `frontend/src/hooks/queries/useCreateTodo.ts:39`  
**Used by rules:** RULE-007, RULE-040, RULE-046

| Field | Type | Note |
|---|---|---|
| `previousTodos` | `TodoListResponse \| undefined` | Snapshot of the ['todos', {limit:10, page:1}] cache only (useCreateTodo.ts:15, useUpdateTodo.ts:16, useDeleteTodo.ts:15). Restored in onError (useCreateTodo.ts:41-45, useUpdateTodo.ts:39-43, useDeleteTodo.ts:31-35). Every outcome triggers a refetch in onSettled. |

<a id="obj-26"></a>
## 26. ToastOptions (frontend notification record)

**Source:** `frontend/src/hooks/useToast.ts:3`  
**Used by rules:** RULE-036, RULE-040, RULE-046, RULE-050, RULE-054, RULE-057

| Field | Type | Note |
|---|---|---|
| `title` | `string` |  |
| `description` | `string (optional)` | Carries error.message on failure. |
| `status` | `'success' \| 'error' \| 'warning' \| 'info' (default 'info')` | useToast.ts:12 |
| `duration` | `number (default 5000 ms)` | useToast.ts:12. The toaster has pauseOnPageIdle: true (toaster.ts:5). closable is never set, so no close button is shown (toaster.tsx:32). |
| `onRetry` | `() => void (optional)` | Becomes the 'Retry' action (useToast.ts:18-21). It calls mutate with the original payload and no success callbacks (TodoForm.tsx:69, TodoEditForm.tsx:67, TodoDeleteButton.tsx:28). |

<a id="obj-27"></a>
## 27. QueryClient default options (frontend cache / retry policy record)

**Source:** `frontend/src/config/queryClient.ts:3`  
**Used by rules:** RULE-050, RULE-053

| Field | Type | Note |
|---|---|---|
| `queries.staleTime` | `number = 300000 (5 min)` | queryClient.ts:6 |
| `queries.gcTime` | `number = 600000 (10 min)` | queryClient.ts:7 |
| `queries.retry` | `number = 1` | queryClient.ts:8 |
| `queries.refetchOnWindowFocus` | `boolean = false` | queryClient.ts:9 |
| `mutations.retry` | `number = 1` | queryClient.ts:12. Failed create, edit and delete calls are re-sent automatically once. |

<a id="obj-28"></a>
## 28. TodoItemProps / TodoEditFormProps (UI view-model props)

**Source:** `frontend/src/components/todos/TodoItem.tsx:6`  
**Used by rules:** RULE-026, RULE-040, RULE-045

| Field | Type | Note |
|---|---|---|
| `TodoItemProps.id` | `string` | TodoItem.tsx:7 |
| `TodoItemProps.title` | `string` | TodoItem.tsx:8. done and description are not passed, so the UI cannot show done status. |
| `isEditing (local state)` | `boolean` | TodoItem.tsx:12. While true, the Edit and Delete buttons are hidden (TodoItem.tsx:19-26). |
| `TodoEditFormProps.initialTitle` | `string` | TodoEditForm.tsx:10. Edited in a single-line &lt;Input&gt; (TodoEditForm.tsx:78-84). |
| `TodoEditFormProps.onCancel` | `() => void` | TodoEditForm.tsx:11. Called on success (line 55) and by Cancel (line 105) with no confirmation, even while a save is pending. |

<a id="obj-29"></a>
## 29. ErrorBoundary Props/State (frontend crash record)

**Source:** `frontend/src/components/errors/ErrorBoundary.tsx:4`  
**Used by rules:** RULE-043

| Field | Type | Note |
|---|---|---|
| `Props.children` | `ReactNode` |  |
| `Props.fallback` | `ReactNode (optional)` | Never supplied at App.tsx:14. |
| `State.hasError` | `boolean` | ErrorBoundary.tsx:10 |
| `State.error` | `Error (optional)` | Its raw .message is rendered under 'Something went wrong' (ErrorBoundary.tsx:41-43). |

