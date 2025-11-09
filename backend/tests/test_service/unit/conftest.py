"""Shared fixtures for ToDoService unit tests."""
from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.logger import CustomLogger


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def real_logger():
    """Create a real logger for validators."""
    return CustomLogger("TestService")


@pytest.fixture
def validators(real_logger):
    """Create real validators for testing."""
    return ValidatorFactory.create_all_validators(real_logger)


@pytest.fixture
def builder(validators):
    """Create real builder for testing."""
    _, uuid_validator, field_validator = validators
    return ToDoEntryBuilder(uuid_validator, field_validator)


@pytest.fixture
def todo_service(mock_repository, mock_logger, validators, builder):
    """Create ToDoService with mocked repository and real validators."""
    input_sanitizer, uuid_validator, field_validator = validators
    return ToDoService(
        repository=mock_repository,
        logger=mock_logger,
        input_sanitizer=input_sanitizer,
        uuid_validator=uuid_validator,
        field_validator=field_validator,
        builder=builder,
    )
