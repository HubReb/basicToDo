"""Unit tests for ToDoService.create_todo() method."""

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
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.tests.test_data.factories import create_todo_create_scheme


class TestCreateTodoSuccess:
    """Test successful create_todo scenarios."""

    @pytest.mark.asyncio
    async def test_create_success(self, todo_service, mock_repository):
        """Test creating a ToDo successfully."""
        payload = create_todo_create_scheme(title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert isinstance(result, ToDoSchema)
        assert result.title == "Test"
        assert result.description == "Desc"
        mock_repository.create_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_valid_emojis(self, todo_service, mock_repository):
        """Test creating ToDo with emojis works."""
        payload = create_todo_create_scheme(
            title="🎉 Party time 🎂", description="Celebrate"
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "🎉 Party time 🎂"

    @pytest.mark.asyncio
    async def test_create_strips_whitespace(self, todo_service, mock_repository):
        """Test create_todo strips whitespace from title and description."""
        payload = create_todo_create_scheme(title="  Test  ", description="  Desc  ")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Test"
        assert result.description == "Desc"

    @pytest.mark.asyncio
    async def test_create_with_empty_description(self, todo_service, mock_repository):
        """Test creating ToDo with empty description."""
        payload = create_todo_create_scheme(title="Test", description="")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Test"
        # Schema converts empty string to None
        assert result.description is None or result.description == ""

    @pytest.mark.asyncio
    async def test_create_with_unicode(self, todo_service, mock_repository):
        """Test creating ToDo with Unicode characters."""
        payload = create_todo_create_scheme(title="Hello 世界 🌍", description="Test")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Hello 世界 🌍"


class TestCreateTodoValidation:
    """Test create_todo validation."""

    @pytest.mark.asyncio
    async def test_create_keeps_sql_like_title(self, todo_service, mock_repository):
        """SQL in a title is ordinary text and reaches the repository (Q6.1)."""
        payload = create_todo_create_scheme(
            title="'; DROP TABLE todos; --", description="Desc"
        )

        result = await todo_service.create_todo(payload)

        assert result.title == "'; DROP TABLE todos; --"
        mock_repository.create_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_keeps_sql_like_description(
        self, todo_service, mock_repository
    ):
        """SQL in a description is ordinary text and reaches the repository (Q6.1)."""
        payload = create_todo_create_scheme(
            title="Valid Title", description="Test /* */ SELECT * FROM users"
        )

        result = await todo_service.create_todo(payload)

        assert result.description == "Test /* */ SELECT * FROM users"
        mock_repository.create_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_empty_title(self, todo_service):
        """Test creating ToDo with empty title raises error."""
        # Bypass Pydantic validation
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = uuid.uuid4()
        payload.title = ""
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_whitespace_only_title(self, todo_service):
        """Test creating ToDo with whitespace-only title raises error."""
        # Bypass Pydantic validation
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = uuid.uuid4()
        payload.title = "   "
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "title is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_none_payload(self, todo_service):
        """Test creating ToDo with None payload raises error."""
        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(None)  # type: ignore

        assert "payload cannot be None" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_none_id(self, todo_service):
        """Test creating ToDo with None ID raises error."""
        # Bypass Pydantic validation
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = None
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "id is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_invalid_uuid(self, todo_service):
        """Test creating ToDo with invalid UUID raises error."""
        # Bypass Pydantic validation
        payload = MagicMock(spec=ToDoCreateScheme)
        payload.id = "not-a-uuid"
        payload.title = "Test"
        payload.description = "Desc"

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "Invalid UUID" in str(exc_info.value)


class TestCreateTodoRepositoryErrors:
    """Test create_todo repository error handling."""

    @pytest.mark.asyncio
    async def test_create_duplicate_id_becomes_already_exists(
        self, todo_service, mock_repository
    ):
        """Q6.3: only a primary-key clash means "already exists" (409)."""
        payload = create_todo_create_scheme(title="Duplicate", description="Desc")
        mock_repository.create_to_do.side_effect = IntegrityError(
            "INSERT", {}, sqlite3.IntegrityError("UNIQUE constraint failed: toDo.id")
        )

        with pytest.raises(ToDoAlreadyExistsError):
            await todo_service.create_todo(payload)

    @pytest.mark.asyncio
    async def test_create_other_integrity_error_is_a_repository_error(
        self, todo_service, mock_repository
    ):
        """Q6.3: a CHECK or NOT NULL violation is not a duplicate (500, not 409)."""
        payload = create_todo_create_scheme(title="Checked", description="Desc")
        mock_repository.create_to_do.side_effect = IntegrityError(
            "INSERT",
            {},
            sqlite3.IntegrityError("CHECK constraint failed: title_length_check"),
        )

        with pytest.raises(ToDoRepositoryError):
            await todo_service.create_todo(payload)


class TestCreateTodoRepositoryInteraction:
    """Test create_todo repository interaction."""

    @pytest.mark.asyncio
    async def test_create_calls_repository_create(self, todo_service, mock_repository):
        """Test create_todo calls repository.create_to_do."""
        payload = create_todo_create_scheme(title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        mock_repository.create_to_do.assert_called_once()
        args = mock_repository.create_to_do.call_args[0]
        assert isinstance(args[0], ToDoEntryData)
        assert args[0].id == payload.id

    @pytest.mark.asyncio
    async def test_create_passes_validated_data(self, todo_service, mock_repository):
        """Test create_todo passes validated data to repository."""
        payload = create_todo_create_scheme(title="  Test  ", description="  Desc  ")
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        args = mock_repository.create_to_do.call_args[0]
        assert args[0].title == "Test"
        assert args[0].description == "Desc"

    @pytest.mark.asyncio
    async def test_create_sets_default_values(self, todo_service, mock_repository):
        """Test create_todo sets default values for new entry."""
        payload = create_todo_create_scheme(title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        args = mock_repository.create_to_do.call_args[0]
        assert args[0].done is False
        assert args[0].deleted is False
        assert args[0].updated_at is None
        assert args[0].created_at is not None
