"""Unit tests for ToDoService.get_todo() method."""
import datetime
import uuid

import pytest

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
    ToDoValidationError,
)
from backend.app.models.todo import ToDoEntryData


class TestGetTodoSuccess:
    """Test successful get_todo scenarios."""

    @pytest.mark.asyncio
    async def test_get_success(self, todo_service, mock_repository):
        """Test getting a ToDo successfully."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        result = await todo_service.get_todo(todo_id)

        assert result.id == todo_id
        assert result.title == "Test"
        assert result.description == "Desc"
        mock_repository.get_to_do_entry.assert_called_once_with(todo_id)

    @pytest.mark.asyncio
    async def test_get_with_string_uuid(self, todo_service, mock_repository):
        """Test getting ToDo with string UUID."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        result = await todo_service.get_todo(str(todo_id))

        assert result.id == todo_id

    @pytest.mark.asyncio
    async def test_get_with_uuid_object(self, todo_service, mock_repository):
        """Test getting ToDo with UUID object."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        result = await todo_service.get_todo(todo_id)

        assert result.id == todo_id

    @pytest.mark.asyncio
    async def test_get_with_all_fields_populated(self, todo_service, mock_repository):
        """Test getting ToDo with all fields populated."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Complete Task",
            description="Full description",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        result = await todo_service.get_todo(todo_id)

        assert result.id == todo_id
        assert result.done is True
        assert result.updated_at is not None


class TestGetTodoValidation:
    """Test get_todo validation."""

    @pytest.mark.asyncio
    async def test_get_invalid_uuid(self, todo_service):
        """Test getting ToDo with invalid UUID."""
        invalid_id = "not-a-valid-uuid"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.get_todo(invalid_id)

        assert "Invalid UUID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_validates_uuid_before_repository_call(self, todo_service, mock_repository):
        """Test get_todo validates UUID before calling repository."""
        invalid_id = "invalid"

        with pytest.raises(ToDoValidationError):
            await todo_service.get_todo(invalid_id)

        mock_repository.get_to_do_entry.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_with_empty_string_uuid(self, todo_service):
        """Test getting ToDo with empty string UUID."""
        with pytest.raises(ToDoValidationError):
            await todo_service.get_todo("")

    @pytest.mark.asyncio
    async def test_get_with_partial_uuid(self, todo_service):
        """Test getting ToDo with partial UUID."""
        partial_uuid = "123e4567"

        with pytest.raises(ToDoValidationError):
            await todo_service.get_todo(partial_uuid)


class TestGetTodoNotFound:
    """Test get_todo not found scenarios."""

    @pytest.mark.asyncio
    async def test_get_not_found(self, todo_service, mock_repository):
        """Test getting a non-existent ToDo."""
        mock_repository.get_to_do_entry.return_value = None

        with pytest.raises(ToDoNotFoundError):
            await todo_service.get_todo(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_not_found_returns_none_from_repo(self, todo_service, mock_repository):
        """Test get_todo raises error when repository returns None."""
        mock_repository.get_to_do_entry.return_value = None
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.get_todo(todo_id)

        mock_repository.get_to_do_entry.assert_called_once_with(todo_id)


class TestGetTodoRepositoryInteraction:
    """Test get_todo repository interaction."""

    @pytest.mark.asyncio
    async def test_get_calls_repository_get(self, todo_service, mock_repository):
        """Test get_todo calls repository.get_to_do_entry."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        await todo_service.get_todo(todo_id)

        mock_repository.get_to_do_entry.assert_called_once_with(todo_id)

    @pytest.mark.asyncio
    async def test_get_passes_validated_uuid(self, todo_service, mock_repository):
        """Test get_todo passes validated UUID to repository."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        # Pass string UUID
        await todo_service.get_todo(str(todo_id))

        # Should call repository with UUID object (validated)
        call_args = mock_repository.get_to_do_entry.call_args[0]
        assert isinstance(call_args[0], uuid.UUID)
        assert call_args[0] == todo_id
