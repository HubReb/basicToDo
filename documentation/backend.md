# Backend Architecture

FastAPI + async SQLAlchemy (aiosqlite) + Pydantic. Layered architecture with a single `Todo` entity.

## Layered Overview

```mermaid
flowchart TD
    Client[HTTP Client]

    subgraph API["API Layer (backend/app/api)"]
        Routes["FastAPI Routes<br/>api.py"]
        Limiter["Rate Limiter<br/>(slowapi)"]
        CORS["CORS Middleware"]
    end

    subgraph BL["Business Logic (backend/app/business_logic)"]
        Service["ToDoService<br/>todo_service.py"]
        Builder["ToDoEntryBuilder"]
        Validators["Validators<br/>(uuid / field / input)"]
        Decorators["handle_service_exceptions"]
    end

    subgraph DA["Data Access (backend/app/data_access)"]
        Repo["ToDoRepository"]
        DB["Database<br/>safe_session_scope<br/>AsyncSessionLocal"]
        ORM["ToDoORM"]
    end

    subgraph Schemas["Schemas (backend/app/schemas)"]
        ReqSchemas["data_schemes<br/>Create / Update / Read"]
        RespSchemas["api_responses<br/>ToDoResponse / List / Get / Delete"]
    end

    Logger["CustomLogger<br/>logger.py"]
    Factory["create_todo_service<br/>factory.py"]
    Config["Settings<br/>config.py"]

    Client --> CORS --> Limiter --> Routes
    Routes --> Service
    Routes --> ReqSchemas
    Routes --> RespSchemas
    Service --> Builder
    Service --> Validators
    Service --> Repo
    Service --> Decorators
    Builder --> Validators
    Repo --> DB
    DB --> ORM
    Factory -.wires.-> Service
    Service -.logs.-> Logger
    Repo -.logs.-> Logger
    Routes -.reads.-> Config
    DB -.reads.-> Config
```

## Request Flow: `POST /todo`

```mermaid
sequenceDiagram
    actor Client
    participant API as api.py<br/>(FastAPI route)
    participant Svc as ToDoService
    participant Bld as ToDoEntryBuilder
    participant Val as Validators
    participant Repo as ToDoRepository
    participant DB as AsyncSession

    Client->>API: POST /todo {title, description, id}
    API->>API: ToDoCreateScheme validation
    API->>Svc: create_todo(payload)
    Svc->>Bld: build_from_create_schema(payload)
    Bld->>Val: validate uuid + fields
    Val-->>Bld: sanitized values
    Bld-->>Svc: ToDoORM
    Svc->>Repo: create_to_do(entry)
    Repo->>DB: session.add(entry) (async)
    DB-->>Repo: commit
    Repo-->>Svc: ok
    Svc-->>API: ToDoSchema
    API-->>Client: 200 ToDoResponse {success, todo_entry}
```

## Domain Model

```mermaid
classDiagram
    class ToDoORM {
        +UUID id
        +str title
        +str description
        +datetime created_at
        +datetime updated_at
        +bool deleted
        +bool done
    }

    class ToDoSchema {
        +UUID id
        +str title
        +str description
        +datetime created_at
        +datetime updated_at
        +bool deleted
        +bool done
    }

    class ToDoCreateScheme {
        +UUID id
        +str title
        +str description
    }

    class TodoUpdateScheme {
        +str title
        +str description
        +bool done
    }

    class ToDoResponse {
        +bool success
        +ToDoSchema todo_entry
    }

    class ListToDoResponse {
        +bool success
        +int results
        +int total_count
        +list~ToDoSchema~ todo_entries
    }

    class DeleteToDoResponse {
        +bool success
        +str message
    }

    ToDoSchema <.. ToDoORM : model_validate
    ToDoCreateScheme ..> ToDoORM : builder
    TodoUpdateScheme ..> ToDoORM : repository
    ToDoResponse o-- ToDoSchema
    ListToDoResponse o-- ToDoSchema
```

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> Active : create_todo
    Active --> ActiveDone : mark done
    ActiveDone --> Active : unmark done
    Active --> Deleted : delete_todo (soft)
    ActiveDone --> Deleted : delete_todo (soft)
    Deleted --> Active : restore_todo
    Deleted --> [*] : hard_delete_to_do
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| GET | `/todo` | List active todos (paginated) |
| POST | `/todo` | Create todo |
| GET | `/todo/{id}` | Get single todo |
| PUT | `/todo/{id}` | Update todo (or mark done) |
| DELETE | `/todo/{id}` | Soft-delete |
| GET | `/todo/deleted` | List soft-deleted todos |
| PATCH | `/todo/{id}/restore` | Restore a soft-deleted todo |

Rate limits: 30/min for mutating endpoints, 60/min for reads (configurable; see `backend/app/config.py`).

Full contract: [`specs/002-modernize-fullstack/contracts/api-endpoints.md`](../specs/002-modernize-fullstack/contracts/api-endpoints.md).

## Key Architectural Decisions

- **Async-only DB**: `aiosqlite` + `AsyncSession` end-to-end. No sync sessions exist.
- **Single declarative ORM**: `ToDoORM` in `data_access/database.py`. The earlier dual declarative + imperative mapping was removed.
- **Soft delete by default**: `delete_to_do` flips `deleted=True`. A separate `hard_delete_to_do` exists on the repository for purge flows but is not exposed via HTTP.
- **Service-level exception decorator**: `handle_service_exceptions` normalizes repository/validation errors into the domain exceptions the API layer catches.
- **Dependency wiring in `factory.py`**: `create_todo_service()` is the single place where validators, builder, repository, and logger are composed.
