<!--
Sync Impact Report
===================
Version change: N/A (initial) → 1.0.0
Modified principles: N/A (initial creation)
Added sections:
  - Principle I: Clean Architecture Enforcement
  - Principle II: Type Safety and Code Quality
  - Principle III: Testing Standards
  - Principle IV: User Experience Consistency
  - Principle V: Performance and Reliability
  - Principle VI: Simplicity and Incremental Delivery
  - Section: Technical Constraints
  - Section: Development Workflow and Quality Gates
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md — ✅ compatible (success criteria align with SC principles)
  - .specify/templates/tasks-template.md — ✅ compatible (phased delivery matches Principle VI)
Follow-up TODOs: None
-->

# basicToDo Constitution

## Core Principles

### I. Clean Architecture Enforcement

All code MUST follow the established layered architecture with strict
separation of concerns:

- **API Layer** handles HTTP routing, request/response serialization,
  and error-code mapping only. No business logic in route handlers.
- **Service Layer** owns business rules, validation, and orchestration.
  Services MUST be created through the factory pattern with dependency
  injection—never instantiated directly in route handlers.
- **Repository Layer** encapsulates all database queries and session
  management. No raw SQL or ORM calls outside the repository.
- **Schema Layer** (Pydantic) validates all data crossing system
  boundaries. Internal layers communicate via domain models.

Cross-layer imports MUST flow downward only (API → Service → Repository
→ Database). Upward or lateral imports are prohibited.

**Rationale**: The project uses this pattern to keep concerns isolated
and enable independent testing of each layer. Violating boundaries
creates hidden coupling that makes changes brittle.

### II. Type Safety and Code Quality

All code MUST pass static analysis before merge:

- **Python**: MyPy strict mode (`disallow_untyped_defs = true`,
  `strict_optional = true`, `warn_return_any = true`). Every function
  MUST have complete type annotations. Pylint and Black MUST report
  zero errors.
- **TypeScript**: ESLint MUST report zero errors. Prefer explicit
  types at module boundaries; inferred types are acceptable for local
  variables where the type is obvious.
- **No `# type: ignore` or `@ts-ignore` without a paired comment**
  explaining why the suppression is necessary and what would fix it.

Input sanitization MUST be applied at system boundaries: regex
validation, UUID format checks, and SQL injection protection in the
service layer.

**Rationale**: Strict typing catches entire classes of bugs at compile
time. The project enforces MyPy strict mode to maintain this guarantee
as the codebase grows.

### III. Testing Standards

Every feature MUST ship with tests that verify correctness at the
appropriate level:

- **Backend unit tests** (pytest): Test service-layer logic in
  isolation. Mock only external dependencies (database, network),
  never internal service methods.
- **Backend integration tests** (pytest): Test the full request path
  from API endpoint through database and back. Use a real SQLite
  test database, not mocks.
- **Frontend unit tests** (vitest): Test component rendering and
  interaction logic. Use React Testing Library idioms—query by
  accessible roles and text, not implementation details.
- **Coverage gate**: New code MUST NOT decrease the overall test
  coverage percentage. Critical paths (CRUD operations, error
  handling, authentication) MUST have explicit test cases.

Tests MUST be deterministic: no reliance on execution order, system
clock, or network availability. Flaky tests MUST be fixed or removed
within one sprint of detection.

**Rationale**: Tests are the primary safety net for a rapidly evolving
codebase. Integration tests against real databases prevent the class
of bugs where mocked tests pass but production fails.

### IV. User Experience Consistency

All user-facing changes MUST maintain visual and behavioral coherence:

- **Component library**: Use Chakra UI components as the primary
  building blocks. Custom components MUST follow Chakra's theming
  and spacing conventions.
- **Interaction patterns**: Destructive actions (delete, bulk
  operations) MUST require confirmation. State changes MUST provide
  immediate visual feedback (loading indicators, success/error
  messages).
- **Responsive behavior**: The UI MUST be usable at viewport widths
  from 320px to 1920px. No horizontal scrolling on standard content.
- **Error states**: Every user action that can fail MUST display a
  human-readable error message. Empty states (no todos, no results)
  MUST show helpful guidance, not blank screens.
- **Accessibility**: Interactive elements MUST be keyboard-navigable.
  Form inputs MUST have associated labels. Color MUST NOT be the
  sole indicator of state.

**Rationale**: UX improvements are a stated project priority. These
standards prevent regressions where new features break the feel of
existing functionality.

### V. Performance and Reliability

The application MUST meet these performance baselines:

- **API response time**: All CRUD endpoints MUST respond in under
  200ms at p95 under normal load (single-user development context).
- **Frontend initial load**: Time to interactive MUST be under 3
  seconds on a standard broadband connection.
- **Bundle size**: Frontend production bundle MUST NOT exceed 500KB
  gzipped without explicit justification and approval.
- **Database queries**: No endpoint MUST execute more than 5 database
  queries. N+1 query patterns are prohibited—use eager loading or
  batch queries.
- **Error recovery**: Transient failures (database lock contention,
  network hiccups) MUST be handled gracefully. The application MUST
  NOT crash on malformed input.

**Rationale**: Even as a learning project, establishing performance
discipline early prevents costly remediation later and builds good
engineering habits.

### VI. Simplicity and Incremental Delivery

Complexity MUST be justified by a concrete, current requirement:

- **YAGNI**: Do not build features, abstractions, or infrastructure
  for hypothetical future needs. Three similar lines of code are
  preferable to a premature abstraction.
- **Minimal changes**: Bug fixes address the bug. Feature work
  delivers the feature. Do not bundle unrelated refactoring,
  cleanup, or "improvements" into the same change.
- **Incremental delivery**: Features MUST be decomposable into
  independently testable and deployable increments. Each increment
  MUST deliver user-visible value.
- **Dependencies**: New dependencies MUST solve a problem that cannot
  be reasonably addressed with existing libraries or standard library
  features. Every addition increases maintenance surface.

**Rationale**: The project is a learning playground with rapid
iteration. Keeping changes small and focused reduces risk, speeds
review, and makes it easier to identify what broke when something
goes wrong.

## Technical Constraints

The following technology choices are binding for all contributions:

- **Backend**: Python 3.13+, FastAPI, SQLAlchemy 2.0, SQLite,
  Pydantic. Package management via UV.
- **Frontend**: React 19, TypeScript 5.8+, Vite 6, Chakra UI 3.
  Package management via NPM.
- **Dev tooling**: MyPy (strict), Pylint, Black (Python); ESLint
  (TypeScript). Pytest (backend tests), Vitest (frontend tests).
- **Database**: SQLite for development and current deployment.
  All schema changes MUST go through SQLAlchemy ORM model
  definitions—no hand-written DDL.
- **API contract**: RESTful JSON over HTTP. All endpoints MUST use
  Pydantic schemas for request validation and response serialization.

Changing any of these choices requires a constitution amendment
(see Governance).

## Development Workflow and Quality Gates

All changes MUST pass through these gates before merge:

1. **Static analysis**: MyPy, Pylint, Black (backend); ESLint
   (frontend) MUST report zero errors.
2. **Test suite**: All existing tests MUST pass. New functionality
   MUST include tests per Principle III.
3. **Architecture review**: Changes MUST comply with the layered
   architecture (Principle I). New files MUST be placed in the
   correct layer directory.
4. **Performance check**: Changes to database queries or API
   endpoints MUST be verified against Principle V baselines.
5. **UX verification**: Frontend changes MUST be visually verified
   in a browser before marking complete. Test the golden path and
   at least one error/edge case.

Pull requests MUST include:
- A clear description of what changed and why.
- Evidence that quality gates passed (test output, linter output).
- Screenshots or recordings for UI changes.

## Governance

This constitution is the authoritative source for technical decisions
in the basicToDo project. All contributions, reviews, and
architectural choices MUST align with these principles.

### Amendment Process

1. **Propose**: Open a pull request modifying this constitution file.
   Include the rationale for the change and its impact on existing
   code.
2. **Review**: The amendment MUST be reviewed with attention to
   downstream effects on existing code and workflows.
3. **Migrate**: If the amendment changes existing standards, include
   a migration plan or follow-up tasks to bring existing code into
   compliance.
4. **Version**: Update the version number per semantic versioning:
   - MAJOR: Principle removed or fundamentally redefined.
   - MINOR: New principle or section added, or material expansion.
   - PATCH: Clarifications, wording, or non-semantic refinements.

### Compliance

- All pull requests and code reviews MUST verify compliance with
  these principles.
- The Constitution Check section in implementation plans MUST
  reference specific principles and confirm adherence.
- Violations MUST be documented in the Complexity Tracking table
  with justification for why the violation is necessary and what
  simpler alternative was rejected.

### Precedence

This constitution supersedes informal conventions, ad-hoc decisions,
and individual preferences. When in doubt, defer to the principle
that most directly applies. If two principles conflict, prefer the
one that reduces risk to users (Principle IV, V) over developer
convenience.

**Version**: 1.0.0 | **Ratified**: 2026-04-25 | **Last Amended**: 2026-04-25
