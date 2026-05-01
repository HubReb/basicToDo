"""Shared fixtures for builder integration tests."""

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.logger import CustomLogger


@pytest.fixture
def builder():
    """Create ToDoEntryBuilder with real validators."""
    logger = CustomLogger("ToDoEntryBuilderIntegrationTest")
    uuid_validator = ValidatorFactory.create_uuid_validator(logger)
    field_validator = ValidatorFactory.create_field_validator(logger)
    return ToDoEntryBuilder(uuid_validator, field_validator)
