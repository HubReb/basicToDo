"""Root conftest.py with shared fixtures for all tests."""
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.database import Base, ToDoORM
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger
from backend.app.business_logic.validators import ValidatorFactory


# Session-scoped fixtures for shared components
@pytest.fixture(scope="session")
def session_logger() -> CustomLogger:
    """Create a real logger for the entire test session."""
    return CustomLogger("TestSession")


@pytest.fixture(scope="session")
def session_validators(session_logger: CustomLogger):  # type: ignore[no-untyped-def]
    """Create real validators for the entire test session."""
    return ValidatorFactory.create_all_validators(session_logger)


@pytest.fixture(scope="session")
def session_input_sanitizer(session_validators):  # type: ignore[no-untyped-def]
    """Get input sanitizer from session validators."""
    input_sanitizer, _, _ = session_validators
    return input_sanitizer


@pytest.fixture(scope="session")
def session_uuid_validator(session_validators):  # type: ignore[no-untyped-def]
    """Get UUID validator from session validators."""
    _, uuid_validator, _ = session_validators
    return uuid_validator


@pytest.fixture(scope="session")
def session_field_validator(session_validators):  # type: ignore[no-untyped-def]
    """Get field validator from session validators."""
    _, _, field_validator = session_validators
    return field_validator


@pytest.fixture(scope="session")
def session_builder(session_uuid_validator, session_field_validator):  # type: ignore[no-untyped-def]
    """Create a real builder for the entire test session."""
    return ToDoEntryBuilder(session_uuid_validator, session_field_validator)


# Function-scoped fixtures that need fresh instances per test
@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create a mock repository for each test (async-compatible)."""
    return AsyncMock()


@pytest.fixture
def mock_logger() -> MagicMock:
    """Create a mock logger for each test."""
    return MagicMock()


@pytest.fixture
def sample_todo_id() -> uuid.UUID:
    """Provide a consistent UUID for testing."""
    return uuid.uuid4()


# Commonly used service fixtures
@pytest.fixture
def todo_service_with_mock_repo(
    mock_repository: AsyncMock,
    mock_logger: MagicMock,
    session_input_sanitizer,  # type: ignore[no-untyped-def]
    session_uuid_validator,  # type: ignore[no-untyped-def]
    session_field_validator,  # type: ignore[no-untyped-def]
    session_builder,  # type: ignore[no-untyped-def]
) -> ToDoService:
    """Create ToDoService with mocked repository and real validators."""
    return ToDoService(
        repository=mock_repository,
        logger=mock_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )


@pytest.fixture
def todo_service_integration(
    mock_repository: AsyncMock,
    session_logger: CustomLogger,
    session_input_sanitizer,  # type: ignore[no-untyped-def]
    session_uuid_validator,  # type: ignore[no-untyped-def]
    session_field_validator,  # type: ignore[no-untyped-def]
    session_builder,  # type: ignore[no-untyped-def]
) -> ToDoService:
    """Create ToDoService for integration tests with real logger."""
    return ToDoService(
        repository=mock_repository,
        logger=session_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )


# Async database fixtures for integration tests
@pytest_asyncio.fixture(scope="function")
async def test_async_engine():  # type: ignore[no-untyped-def]
    """Create a test async database engine using in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_async_session(test_async_engine):  # type: ignore[no-untyped-def]
    """Create a test async database session."""
    session_factory = async_sessionmaker(
        bind=test_async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_session_scope(test_async_engine):  # type: ignore[no-untyped-def]
    """Create an async session scope context manager for testing."""
    session_factory = async_sessionmaker(
        bind=test_async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    @asynccontextmanager
    async def _session_scope() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return _session_scope


@pytest_asyncio.fixture(scope="function")
async def todo_service_with_real_db(
    async_session_scope,  # type: ignore[no-untyped-def]
    session_logger: CustomLogger,
    session_input_sanitizer,  # type: ignore[no-untyped-def]
    session_uuid_validator,  # type: ignore[no-untyped-def]
    session_field_validator,  # type: ignore[no-untyped-def]
    session_builder,  # type: ignore[no-untyped-def]
) -> ToDoService:
    """Create ToDoService with real async database for integration tests."""
    repository = ToDoRepository(async_session_scope, session_logger)

    return ToDoService(
        repository=repository,
        logger=session_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )
