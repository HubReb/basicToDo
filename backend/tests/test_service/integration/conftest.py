"""Shared fixtures for ToDoService integration tests."""
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
def logger():
    """Create a real logger for integration testing."""
    return CustomLogger("ToDoServiceIntegrationTest")


@pytest.fixture
def validators(logger):
    """Create real validators for integration testing."""
    return ValidatorFactory.create_all_validators(logger)


@pytest.fixture
def builder(validators):
    """Create real builder for integration testing."""
    _, uuid_validator, field_validator = validators
    return ToDoEntryBuilder(uuid_validator, field_validator)


@pytest.fixture
def todo_service(mock_repository, logger, validators, builder):
    """Create ToDoService with real validators and builder, mocked repository."""
    input_sanitizer, uuid_validator, field_validator = validators
    return ToDoService(
        repository=mock_repository,
        logger=logger,
        input_sanitizer=input_sanitizer,
        uuid_validator=uuid_validator,
        field_validator=field_validator,
        builder=builder,
    )
