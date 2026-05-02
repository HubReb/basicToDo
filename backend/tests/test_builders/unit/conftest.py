"""Shared fixtures for builder unit tests."""

from unittest.mock import MagicMock

import pytest

from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder


@pytest.fixture
def mock_uuid_validator():
    """Create a mock UUIDValidator."""
    return MagicMock()


@pytest.fixture
def mock_field_validator():
    """Create a mock FieldValidator."""
    return MagicMock()


@pytest.fixture
def builder(mock_uuid_validator, mock_field_validator):
    """Create ToDoEntryBuilder with mocked validators."""
    return ToDoEntryBuilder(mock_uuid_validator, mock_field_validator)
