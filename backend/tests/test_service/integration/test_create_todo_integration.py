"""Integration tests for ToDoService.create_todo() with real validators."""

import sqlite3
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoRepositoryError,
    ToDoValidationError,
)
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


class TestCreateTodoValidationIntegration:
    """Integration tests for create_todo validation."""

    @pytest.mark.asyncio
    async def test_create_validates_and_sanitizes(self, todo_service, mock_repository):
        """Test create_todo validates and sanitizes input."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id, title="  Test Title  ", description="  Test Desc  "
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        # Verify data was sanitized
        assert result.title == "Test Title"
        assert result.description == "Test Desc"

        # Verify repository received sanitized data
        call_args = mock_repository.create_to_do.call_args[0][0]
        assert call_args.title == "Test Title"
        assert call_args.description == "Test Desc"

    @pytest.mark.asyncio
    async def test_create_strips_leading_whitespace(
        self, todo_service, mock_repository
    ):
        """Test create_todo strips leading whitespace."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id, title="   Leading spaces", description="   Leading desc"
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Leading spaces"
        assert result.description == "Leading desc"

    @pytest.mark.asyncio
    async def test_create_strips_trailing_whitespace(
        self, todo_service, mock_repository
    ):
        """Test create_todo strips trailing whitespace."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id, title="Trailing spaces   ", description="Trailing desc   "
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Trailing spaces"
        assert result.description == "Trailing desc"


class TestCreateTodoSQLLikeTextIntegration:
    """SQL-like text is created as ordinary text (Q6.1); bound parameters keep it inert."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "title, description",
        [
            ("'; DROP TABLE todos; --", "Desc"),
            ("Valid", "Test /* comment */ SELECT * FROM users"),
            ("Test -- comment", "Desc"),
            ("Test UNION SELECT * FROM users", "Desc"),
        ],
        ids=["drop table title", "select description", "double dash", "union select"],
    )
    async def test_create_keeps_sql_like_text(
        self, todo_service, mock_repository, title, description
    ):
        payload = ToDoCreateScheme(
            id=uuid.uuid4(), title=title, description=description
        )

        result = await todo_service.create_todo(payload)

        stored = mock_repository.create_to_do.call_args.args[0]
        assert (stored.title, stored.description) == (title, description)
        assert (result.title, result.description) == (title, description)


class TestCreateTodoUUIDValidationIntegration:
    """Integration tests for create_todo UUID validation."""

    @pytest.mark.asyncio
    async def test_create_validates_uuid(self, todo_service):
        """Test create_todo validates UUID through builder."""
        # Bypass Pydantic
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = "invalid-uuid"
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "Invalid UUID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_accepts_valid_uuid(self, todo_service, mock_repository):
        """Test create_todo accepts valid UUID."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.id == todo_id


class TestCreateTodoFieldValidationIntegration:
    """Integration tests for create_todo field validation."""

    @pytest.mark.asyncio
    async def test_create_validates_required_title(self, todo_service):
        """Test create_todo validates required title."""
        # Bypass Pydantic
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = uuid.uuid4()
        payload.title = ""
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_rejects_whitespace_only_title(self, todo_service):
        """Test create_todo rejects whitespace-only title."""
        # Bypass Pydantic
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = uuid.uuid4()
        payload.title = "   "
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_accepts_empty_description(
        self, todo_service, mock_repository
    ):
        """Test create_todo accepts empty description."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        # Schema converts empty string to None
        assert result.description is None or result.description == ""


class TestCreateTodoErrorHandlingIntegration:
    """Integration tests for create_todo error handling."""

    @pytest.mark.asyncio
    async def test_create_duplicate_id_becomes_already_exists(
        self, todo_service, mock_repository
    ):
        """Q6.3: only a primary-key clash means "already exists" (409)."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Duplicate", description="Desc")
        mock_repository.create_to_do.side_effect = IntegrityError(
            "INSERT", {}, sqlite3.IntegrityError("UNIQUE constraint failed: toDo.id")
        )

        with pytest.raises(ToDoAlreadyExistsError):
            await todo_service.create_todo(payload)

    @pytest.mark.asyncio
    async def test_create_check_violation_is_a_repository_error(
        self, todo_service, mock_repository
    ):
        """Q6.3: a CHECK violation is not a duplicate (500, not 409)."""
        payload = ToDoCreateScheme(id=uuid.uuid4(), title="Checked", description="Desc")
        mock_repository.create_to_do.side_effect = IntegrityError(
            "INSERT",
            {},
            sqlite3.IntegrityError("CHECK constraint failed: title_length_check"),
        )

        with pytest.raises(ToDoRepositoryError):
            await todo_service.create_todo(payload)

    @pytest.mark.asyncio
    async def test_create_validates_none_payload(self, todo_service):
        """Test create_todo rejects None payload."""
        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(None)  # type: ignore

        assert "payload cannot be None" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validates_none_id(self, todo_service):
        """Test create_todo rejects None ID."""
        # Bypass Pydantic
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = None
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "id is required" in str(exc_info.value)
