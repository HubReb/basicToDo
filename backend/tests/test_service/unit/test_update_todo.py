"""Unit tests for ToDoService.update_todo() method."""
import datetime
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoValidationError,
)
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class TestUpdateTodoSuccess:
    """Test successful update_todo scenarios."""

    @pytest.mark.asyncio
    async def test_update_success(self, todo_service, mock_repository):
        """Test updating a ToDo successfully."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="Updated", description="Updated")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Updated",
            description="Updated",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.title == "Updated"
        assert result.description == "Updated"
        mock_repository.update_to_do.assert_called_once_with(todo_id, payload)

    @pytest.mark.asyncio
    async def test_update_partial_title_only(self, todo_service, mock_repository):
        """Test updating only title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="New Title")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="New Title",
            description="Old Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_partial_description_only(self, todo_service, mock_repository):
        """Test updating only description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( description="New Desc")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Old Title",
            description="New Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.description == "New Desc"

    @pytest.mark.asyncio
    async def test_update_strips_whitespace(self, todo_service, mock_repository):
        """Test update strips whitespace from title and description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            id=todo_id,
            title="  Updated  ",
            description="  Desc  "
        )
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Updated",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "Updated"
        assert call_args.description == "Desc"


class TestUpdateTodoWithDone:
    """Test update_todo with done=True."""

    @pytest.mark.asyncio
    async def test_update_with_done_true_calls_mark_as_done(self, todo_service, mock_repository):
        """Test updating with done=True calls mark_to_do_as_done."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( done=True)
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_updated_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry
        mock_repository.update_to_do.return_value = mock_updated_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.done is True
        mock_repository.get_to_do_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_done_false_normal_update(self, todo_service, mock_repository):
        """Test updating with done=False uses normal update path."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="Updated", done=False)
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Updated",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry
        await todo_service.update_todo(todo_id, payload)

        mock_repository.update_to_do.assert_called_once()
        mock_repository.get_to_do_entry.assert_not_called()


class TestUpdateTodoValidation:
    """Test update_todo validation."""

    @pytest.mark.asyncio
    async def test_update_with_empty_string_title(self, todo_service):
        """Test updating with empty string title raises error."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="", description="Desc")

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_with_whitespace_only_title(self, todo_service):
        """Test updating with whitespace-only title raises error."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="   ", description="Desc")

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_with_sql_injection_title(self, todo_service):
        """Test updating with SQL injection in title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            id=todo_id,
            title="'; DROP TABLE todos; --",
            description="Desc"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_with_sql_injection_description(self, todo_service):
        """Test updating with SQL injection in description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            id=todo_id,
            title="Valid Title",
            description="Test /* */ SELECT * FROM users"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_validates_title_when_provided(self, todo_service, mock_repository):
        """Test update validates title only when provided."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( description="New Desc")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Old Title",
            description="New Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.description == "New Desc"


class TestUpdateTodoRepositoryErrors:
    """Test update_todo repository error handling."""

    @pytest.mark.asyncio
    async def test_update_not_found(self, todo_service, mock_repository):
        """Test updating a non-existent ToDo."""
        mock_repository.update_to_do.return_value = None
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="Updated", description="Updated")

        with pytest.raises(ToDoNotFoundError):
            await todo_service.update_todo(todo_id, payload)

    @pytest.mark.asyncio
    async def test_update_already_exists(self, todo_service, mock_repository):
        """Test updating ToDo to duplicate title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme( title="Duplicate", description="Desc")
        mock_repository.update_to_do.side_effect = IntegrityError("msg", "params", "orig")

        with pytest.raises(ToDoAlreadyExistsError):
            await todo_service.update_todo(todo_id, payload)