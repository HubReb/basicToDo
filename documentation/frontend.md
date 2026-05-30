# Frontend Architecture

React 19 + TypeScript + Vite. UI from Chakra UI v3, server state from TanStack Query v5. Tests run on Vitest.

## Component Tree

```mermaid
flowchart TD
    Main["main.tsx"] --> App
    App["App.tsx"] --> EB["ErrorBoundary"]
    EB --> QCP["QueryClientProvider"]
    QCP --> CP["ChakraProvider"]
    CP --> Header
    CP --> TodoList
    CP --> Toaster
    QCP --> Devtools["ReactQueryDevtools"]

    TodoList --> TodoForm
    TodoList --> TodoItem
    TodoList --> TodoRestoreButton
    TodoList --> Pagination
    TodoList --> Spinner
    TodoList --> ErrorMessage

    TodoItem --> TodoEditForm
    TodoItem --> TodoDeleteButton
```

## Server-State Layer

Every server interaction goes through a TanStack Query hook, which delegates to the `todoApi` singleton, which uses the shared Axios `apiClient`.

```mermaid
flowchart LR
    subgraph Components
        TL[TodoList]
        TF[TodoForm]
        TI[TodoItem]
        TEF[TodoEditForm]
        TDB[TodoDeleteButton]
        TRB[TodoRestoreButton]
    end

    subgraph Hooks["hooks/queries"]
        UTL[useTodoList]
        UDTL[useDeletedTodoList]
        UCT[useCreateTodo]
        UUT[useUpdateTodo]
        UDT[useDeleteTodo]
        URT[useRestoreTodo]
    end

    subgraph Services["services/api"]
        Api[todoApi]
        Client[apiClient<br/>axios]
    end

    Backend[("FastAPI<br/>backend")]

    TL --> UTL
    TL --> UDTL
    TF --> UCT
    TI --> UUT
    TEF --> UUT
    TDB --> UDT
    TRB --> URT

    UTL --> Api
    UDTL --> Api
    UCT --> Api
    UUT --> Api
    UDT --> Api
    URT --> Api

    Api --> Client --> Backend
```

## Optimistic Update Flow (Create)

All mutations follow the same `onMutate` → `onError` rollback → `onSettled` invalidate pattern. Create is shown here; update/delete/restore are structurally identical.

```mermaid
sequenceDiagram
    actor User
    participant Form as TodoForm
    participant Hook as useCreateTodo
    participant QC as QueryClient cache
    participant Api as todoApi
    participant BE as Backend

    User->>Form: submit
    Form->>Hook: mutate(newTodo)
    Hook->>QC: cancelQueries(['todos'])
    Hook->>QC: snapshot previous
    Hook->>QC: setQueryData (optimistic)
    Form-->>User: UI shows new todo immediately

    Hook->>Api: create(data)
    Api->>BE: POST /todo

    alt success
        BE-->>Api: 200 ToDoResponse
        Api-->>Hook: Todo
        Hook->>QC: invalidateQueries(['todos'])
        QC->>Api: refetch list
        Api->>BE: GET /todo
        BE-->>QC: authoritative list
    else error
        BE-->>Api: 4xx/5xx
        Hook->>QC: restore snapshot
        Form-->>User: toast error, UI rolls back
    end
```

## Module Map

| Path | Responsibility |
|------|----------------|
| `src/main.tsx` | Vite entry point, mounts `<App />` |
| `src/App.tsx` | Provider composition: ErrorBoundary → QueryClientProvider → ChakraProvider |
| `src/components/Header.tsx` | App header |
| `src/components/todos/` | Domain components: `TodoList`, `TodoForm`, `TodoItem`, `TodoEditForm`, `TodoDeleteButton`, `TodoRestoreButton` |
| `src/components/common/` | Shared UI: `Pagination`, `Spinner` |
| `src/components/errors/` | `ErrorBoundary`, `ErrorMessage` |
| `src/components/ui/toaster.tsx` | Chakra Toaster mount |
| `src/hooks/queries/` | One TanStack Query hook per backend operation |
| `src/hooks/useToast.ts` | Toast helper bound to the shared toaster |
| `src/hooks/useTodoValidation.ts` | Client-side title/description validation matching backend rules |
| `src/services/api/client.ts` | Axios instance, base URL, error normalization |
| `src/services/api/todoApi.ts` | Single source of truth for endpoint URLs and request/response shapes |
| `src/config/queryClient.ts` | Shared `QueryClient` (stale times, retry policy) |
| `src/config/env.ts` | Typed access to `import.meta.env` |
| `src/types/todo.ts` | Shared Todo / request / response types |
| `src/lib/toaster.ts` | Toaster singleton |

## Key Decisions

- **One hook per endpoint** under `hooks/queries/`. Components never call `todoApi` directly — they go through a hook so caching, optimistic updates, and invalidation stay co-located with the mutation they belong to.
- **Single API surface**: every component path that hits the network goes through `services/api/todoApi.ts`. URLs and response shapes change in one place.
- **Optimistic UI on all mutations**: required by the project constitution. The `onMutate` / `onError` / `onSettled` triad in each mutation hook implements it consistently.
- **Path alias `@/*`**: configured in `tsconfig` and Vite. Imports use `@/hooks/...`, `@/services/...` rather than relative paths.
- **Error boundary at the root** so render-time errors in the tree fall through to a recoverable UI instead of a blank screen.
