"""Integration tests for ToDoService.get_todo() with real validators."""
import datetime
import uuid

import pytest

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
    ToDoValidationError,
)
from backend.app.models.todo import ToDoEntryData


class TestGetTodoValidationIntegration:
    """Integration tests for get_todo validation."""

    @pytest.mark.asyncio
    async def test_get_validates_uuid_string(self, todo_service, mock_repository):
        """Test get_todo validates string UUID."""
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
    async def test_get_rejects_invalid_uuid(self, todo_service):
        """Test get_todo rejects invalid UUID."""
        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.get_todo("not-a-uuid")

        assert "Invalid UUID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_rejects_empty_string_uuid(self, todo_service):
        """Test get_todo rejects empty string UUID."""
        with pytest.raises(ToDoValidationError):
            await todo_service.get_todo("")

    @pytest.mark.asyncio
    async def test_get_rejects_partial_uuid(self, todo_service):
        """Test get_todo rejects partial UUID."""
        with pytest.raises(ToDoValidationError):
            await todo_service.get_todo("123e4567")

    @pytest.mark.asyncio
    async def test_get_accepts_uuid_object(self, todo_service, mock_repository):
        """Test get_todo accepts UUID object."""
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


class TestGetTodoNotFoundIntegration:
    """Integration tests for get_todo not found scenarios."""

    @pytest.mark.asyncio
    async def test_get_not_found_raises_error(self, todo_service, mock_repository):
        """Test get_todo raises ToDoNotFoundError when entry not found."""
        mock_repository.get_to_do_entry.return_value = None

        with pytest.raises(ToDoNotFoundError):
            await todo_service.get_todo(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_not_found_does_not_return_none(self, todo_service, mock_repository):
        """Test get_todo raises error instead of returning None."""
        mock_repository.get_to_do_entry.return_value = None

        with pytest.raises(ToDoNotFoundError):
            await todo_service.get_todo(uuid.uuid4())


class TestGetTodoSuccessIntegration:
    """Integration tests for successful get_todo scenarios."""

    @pytest.mark.asyncio
    async def test_get_returns_complete_todo(self, todo_service, mock_repository):
        """Test get_todo returns complete ToDo data."""
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
        assert result.title == "Complete Task"
        assert result.description == "Full description"
        assert result.done is True
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_returns_minimal_todo(self, todo_service, mock_repository):
        """Test get_todo returns minimal ToDo data."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Minimal",
            description="",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry

        result = await todo_service.get_todo(todo_id)

        assert result.id == todo_id
        assert result.title == "Minimal"
        # Schema converts empty string to None
        assert result.description is None or result.description == ""
        assert result.done is False
        assert result.updated_at is None
