"""Integration tests for ToDoService.update_todo() with real validators."""

import sqlite3
import datetime
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
    ToDoRepositoryError,
)
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class TestUpdateTodoValidationIntegration:
    """Integration tests for update_todo validation."""

    @pytest.mark.asyncio
    async def test_update_validates_and_sanitizes_title(
        self, todo_service, mock_repository
    ):
        """Test update_todo validates and sanitizes title."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="  Updated Title  ", description="Desc")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Updated Title",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False,
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        # Verify payload was sanitized
        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_validates_and_sanitizes_description(
        self, todo_service, mock_repository
    ):
        """Test update_todo validates and sanitizes description."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(description="  Updated Desc  ")
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Title",
            description="Updated Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False,
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        # Verify payload was sanitized
        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.description == "Updated Desc"

    @pytest.mark.parametrize("title", ["", "   "], ids=["empty", "whitespace"])
    def test_update_blank_title_is_rejected_by_the_schema(self, title):
        """Q6.3: a blank title is a schema error (422), as on create."""
        with pytest.raises(ValidationError, match="title must not be null"):
            TodoUpdateScheme(title=title)


class TestUpdateTodoSQLLikeTextIntegration:
    """SQL-like text is passed on as ordinary text (Q6.1); bound parameters keep it inert."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fields",
        [
            {"title": "'; DROP TABLE todos; --"},
            {"title": "Valid", "description": "Test /* comment */ UNION SELECT"},
            {"title": "Test -- comment"},
            {"description": "Test; DROP TABLE"},
        ],
        ids=[
            "drop table title",
            "union select description",
            "double dash",
            "semicolon",
        ],
    )
    async def test_update_keeps_sql_like_text(
        self, todo_service, mock_repository, fields
    ):
        todo_id = uuid.uuid4()
        mock_repository.update_to_do.return_value = ToDoEntryData(
            id=todo_id,
            title=fields.get("title", "Old"),
            description=fields.get("description"),
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False,
        )

        await todo_service.update_todo(todo_id, TodoUpdateScheme(**fields))

        sent = mock_repository.update_to_do.call_args.args[1]
        assert sent.model_dump(exclude_unset=True) == fields


class TestUpdateTodoDoneIntegration:
    """Integration tests for update_todo with done flag."""

    @pytest.mark.asyncio
    async def test_update_with_done_true_marks_as_done(
        self, todo_service, mock_repository
    ):
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
            deleted=False,
        )
        mock_updated_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False,
        )
        mock_repository.get_to_do_entry.return_value = mock_entry
        mock_repository.update_to_do.return_value = mock_updated_entry

        result = await todo_service.update_todo(todo_id, payload)

        assert result.done is True

    @pytest.mark.asyncio
    async def test_update_with_done_true_needs_no_separate_read(
        self, todo_service, mock_repository
    ):
        """Q6.5: done:true is one update like any other edit; no prior read."""
        todo_id = uuid.uuid4()
        mock_repository.update_to_do.return_value = ToDoEntryData(
            id=todo_id,
            title="Renamed",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False,
        )

        await todo_service.update_todo(todo_id, TodoUpdateScheme(done=True))

        mock_repository.get_to_do_entry.assert_not_called()
        mock_repository.update_to_do.assert_called_once()


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
    async def test_update_integrity_error_is_a_repository_error(
        self, todo_service, mock_repository
    ):
        """Q6.3: an update cannot clash on the id; any IntegrityError is a 500."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(title="Checked")
        mock_repository.update_to_do.side_effect = IntegrityError(
            "UPDATE",
            {},
            sqlite3.IntegrityError("CHECK constraint failed: title_length_check"),
        )

        with pytest.raises(ToDoRepositoryError):
            await todo_service.update_todo(todo_id, payload)


class TestUpdateTodoPartialUpdatesIntegration:
    """Integration tests for partial updates."""

    @pytest.mark.asyncio
    async def test_update_only_title_validates_title(
        self, todo_service, mock_repository
    ):
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
            deleted=False,
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_only_description_validates_description(
        self, todo_service, mock_repository
    ):
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
            deleted=False,
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)

        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.description == "New Desc"

    @pytest.mark.asyncio
    async def test_update_description_only_skips_title_validation(
        self, todo_service, mock_repository
    ):
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
            deleted=False,
        )
        mock_repository.update_to_do.return_value = mock_entry

        result = await todo_service.update_todo(todo_id, payload)

        # Should succeed without validating title
        assert result.description == "New Desc"
