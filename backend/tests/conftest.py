"""Root conftest.py with shared fixtures for all tests."""
import uuid
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
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
    """Create a mock repository for each test."""
    return MagicMock()


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
    """Create ToDoService with mocked repository and real validators.

    This is the standard service fixture for unit tests.
    """
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
    """Create ToDoService for integration tests with real logger.

    This fixture uses real validators and logger but mocked repository,
    suitable for integration tests.
    """
    return ToDoService(
        repository=mock_repository,
        logger=session_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )
