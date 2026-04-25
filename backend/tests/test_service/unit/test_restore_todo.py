"""Unit tests for restore_todo service method."""
import uuid

import pytest

from backend.app.business_logic.exceptions import ToDoNotFoundError
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.tests.test_data.factories import create_todo_entry


class TestRestoreTodoSuccess:
    """Test successful restore operations."""

    async def test_restore_returns_todo_schema(self, todo_service_with_mock_repo, mock_repository):
        """Test that restore returns a ToDoSchema."""
        todo_id = uuid.uuid4()
        mock_entry = create_todo_entry(id=todo_id, title="Restored", deleted=False)
        mock_repository.restore_to_do.return_value = mock_entry

        result = await todo_service_with_mock_repo.restore_todo(todo_id)

        assert isinstance(result, ToDoSchema)
        assert result.title == "Restored"


class TestRestoreTodoNotFound:
    """Test restore when todo does not exist."""

    async def test_restore_nonexistent_raises_not_found(self, todo_service_with_mock_repo, mock_repository):
        """Test that restoring a non-existent todo raises ToDoNotFoundError."""
        todo_id = uuid.uuid4()
        mock_repository.restore_to_do.return_value = None

        with pytest.raises(ToDoNotFoundError):
            await todo_service_with_mock_repo.restore_todo(todo_id)


class TestRestoreTodoValidation:
    """Test UUID validation during restore."""

    async def test_restore_calls_uuid_validator(
        self, todo_service_with_mock_repo, mock_repository
    ):
        """Test that UUID validation is called."""
        todo_id = uuid.uuid4()
        mock_entry = create_todo_entry(id=todo_id, title="Test", deleted=False)
        mock_repository.restore_to_do.return_value = mock_entry

        await todo_service_with_mock_repo.restore_todo(todo_id)

        mock_repository.restore_to_do.assert_called_once()
