"""Root conftest.py with shared fixtures for all tests."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger


# Session-scoped fixtures for shared components
@pytest.fixture(scope="session")
def session_logger():
    """Create a real logger for the entire test session."""
    return CustomLogger("TestSession")


@pytest.fixture(scope="session")
def session_validators(session_logger):
    """Create real validators for the entire test session."""
    return ValidatorFactory.create_all_validators(session_logger)


@pytest.fixture(scope="session")
def session_input_sanitizer(session_validators):
    """Get input sanitizer from session validators."""
    input_sanitizer, _, _ = session_validators
    return input_sanitizer


@pytest.fixture(scope="session")
def session_uuid_validator(session_validators):
    """Get UUID validator from session validators."""
    _, uuid_validator, _ = session_validators
    return uuid_validator


@pytest.fixture(scope="session")
def session_field_validator(session_validators):
    """Get field validator from session validators."""
    _, _, field_validator = session_validators
    return field_validator


@pytest.fixture(scope="session")
def session_builder(session_uuid_validator, session_field_validator):
    """Create a real builder for the entire test session."""
    return ToDoEntryBuilder(session_uuid_validator, session_field_validator)


# Function-scoped fixtures that need fresh instances per test
@pytest.fixture
def mock_repository():
    """Create an async mock repository for each test."""
    return AsyncMock()


@pytest.fixture
def mock_logger():
    """Create a mock logger for each test."""
    return MagicMock()


@pytest.fixture
def sample_todo_id():
    """Provide a consistent UUID for testing."""
    return uuid.uuid4()


# Commonly used service fixtures
@pytest.fixture
def todo_service_with_mock_repo(
    mock_repository,
    mock_logger,
    session_input_sanitizer,
    session_uuid_validator,
    session_field_validator,
    session_builder,
):
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
    mock_repository,
    session_logger,
    session_input_sanitizer,
    session_uuid_validator,
    session_field_validator,
    session_builder,
):
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
@pytest.fixture
async def test_db_engine():
    """Create an async test database engine using in-memory SQLite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create an async test database session."""
    AsyncTestSession = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = AsyncTestSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
async def test_session_scope(test_db_engine):
    """Create an async session scope context manager for testing."""
    AsyncTestSession = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    @asynccontextmanager
    async def _session_scope() -> AsyncGenerator[AsyncSession, None]:
        session = AsyncTestSession()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    return _session_scope


@pytest.fixture
async def todo_service_with_real_db(
    test_session_scope,
    session_logger,
    session_input_sanitizer,
    session_uuid_validator,
    session_field_validator,
    session_builder,
):
    """Create ToDoService with real async database for integration tests."""
    repository = ToDoRepository(test_session_scope, session_logger)

    return ToDoService(
        repository=repository,
        logger=session_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )
