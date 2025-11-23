"""Integration tests for ToDoService.update_todo() with real validators."""
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


class TestUpdateTodoValidationIntegration:
    """Integration tests for update_todo validation."""

    @pytest.mark.asyncio
    async def test_update_validates_and_sanitizes_title(self, todo_service, mock_repository):
        """Test update_todo validates and sanitizes title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            title="  Updated Title  ",
            description="Desc"
        )
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Updated Title",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        # Verify payload was sanitized
        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_validates_and_sanitizes_description(self, todo_service, mock_repository):
        """Test update_todo validates and sanitizes description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            description="  Updated Desc  "
        )
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Title",
            description="Updated Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        # Verify payload was sanitized
        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.description == "Updated Desc"

    @pytest.mark.asyncio
    async def test_update_rejects_empty_title(self, todo_service):
        """Test update_todo rejects empty title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="")

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_rejects_whitespace_only_title(self, todo_service):
        """Test update_todo rejects whitespace-only title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="   ")

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "title is required" in str(exc_info.value)


class TestUpdateTodoSQLInjectionIntegration:
    """Integration tests for update_todo SQL injection protection."""

    @pytest.mark.asyncio
    async def test_update_blocks_sql_injection_in_title(self, todo_service):
        """Test update_todo blocks SQL injection in title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            title="'; DROP TABLE todos; --"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_blocks_sql_injection_in_description(self, todo_service):
        """Test update_todo blocks SQL injection in description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            title="Valid",
            description="Test /* comment */ UNION SELECT"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.update_todo(todo_id, payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_blocks_double_dash_in_title(self, todo_service):
        """Test update_todo blocks double dash comments in title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            title="Test -- comment"
        )

        with pytest.raises(ToDoValidationError):
            await todo_service.update_todo(todo_id, payload)

    @pytest.mark.asyncio
    async def test_update_blocks_semicolon_in_description(self, todo_service):
        """Test update_todo blocks semicolon in description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            description="Test; DROP TABLE"
        )

        with pytest.raises(ToDoValidationError):
            await todo_service.update_todo(todo_id, payload)


class TestUpdateTodoDoneIntegration:
    """Integration tests for update_todo with done flag."""

    @pytest.mark.asyncio
    async def test_update_with_done_true_marks_as_done(self, todo_service, mock_repository):
        """Test update with done=True uses mark_as_done flow."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(done=True)
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

    @pytest.mark.asyncio
    async def test_update_with_done_true_calls_get_entry(self, todo_service, mock_repository):
        """Test update with done=True calls get_to_do_entry."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(done=True)
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

        await todo_service.update_todo(todo_id, payload)

        mock_repository.get_to_do_entry.assert_called_once()


class TestUpdateTodoErrorHandlingIntegration:
    """Integration tests for update_todo error handling."""

    @pytest.mark.asyncio
    async def test_update_not_found_raises_error(self, todo_service, mock_repository):
        """Test update_todo raises ToDoNotFoundError when entry not found."""
        mock_repository.update_to_do.return_value = None
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="Updated")

        with pytest.raises(ToDoNotFoundError):
            await todo_service.update_todo(todo_id, payload)

    @pytest.mark.asyncio
    async def test_update_integrity_error_becomes_already_exists(self, todo_service, mock_repository):
        """Test update_todo converts IntegrityError to ToDoAlreadyExistsError."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="Duplicate")
        mock_repository.update_to_do.side_effect = IntegrityError("msg", "params", "orig")

        with pytest.raises(ToDoAlreadyExistsError):
            await todo_service.update_todo(todo_id, payload)


class TestUpdateTodoPartialUpdatesIntegration:
    """Integration tests for partial updates."""

    @pytest.mark.asyncio
    async def test_update_only_title_validates_title(self, todo_service, mock_repository):
        """Test updating only title validates title field."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="  New Title  ")
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

        await todo_service.update_todo(todo_id, payload)

        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_only_description_validates_description(self, todo_service, mock_repository):
        """Test updating only description validates description field."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(description="  New Desc  ")
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

        await todo_service.update_todo(todo_id, payload)

        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.description == "New Desc"

    @pytest.mark.asyncio
    async def test_update_description_only_skips_title_validation(self, todo_service, mock_repository):
        """Test updating description only doesn't validate title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(description="New Desc")
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

        # Should succeed without validating title
        assert result.description == "New Desc"
