"""Unit tests for ToDoService.create_todo() method."""
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoValidationError,
)
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class TestCreateTodoSuccess:
    """Test successful create_todo scenarios."""

    @pytest.mark.asyncio
    async def test_create_success(self, todo_service, mock_repository):
        """Test creating a ToDo successfully."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert isinstance(result, ToDoSchema)
        assert result.title == "Test"
        assert result.description == "Desc"
        mock_repository.create_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_valid_emojis(self, todo_service, mock_repository):
        """Test creating ToDo with emojis works."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="🎉 Party time 🎂",
            description="Celebrate"
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "🎉 Party time 🎂"

    @pytest.mark.asyncio
    async def test_create_strips_whitespace(self, todo_service, mock_repository):
        """Test create_todo strips whitespace from title and description."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="  Test  ",
            description="  Desc  "
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Test"
        assert result.description == "Desc"

    @pytest.mark.asyncio
    async def test_create_with_empty_description(self, todo_service, mock_repository):
        """Test creating ToDo with empty description."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="")
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Test"
        # Schema converts empty string to None
        assert result.description is None or result.description == ""

    @pytest.mark.asyncio
    async def test_create_with_unicode(self, todo_service, mock_repository):
        """Test creating ToDo with Unicode characters."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="Hello 世界 🌍",
            description="Test"
        )
        mock_repository.create_to_do.return_value = None

        result = await todo_service.create_todo(payload)

        assert result.title == "Hello 世界 🌍"


class TestCreateTodoValidation:
    """Test create_todo validation."""

    @pytest.mark.asyncio
    async def test_create_with_sql_injection_title(self, todo_service):
        """Test creating ToDo rejects SQL injection in title."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="'; DROP TABLE todos; --",
            description="Desc"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_sql_injection_description(self, todo_service):
        """Test creating ToDo rejects SQL injection in description."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="Valid Title",
            description="Test /* */ SELECT * FROM users"
        )

        with pytest.raises(ToDoValidationError) as exc_info:
            await todo_service.create_todo(payload)

        assert "Invalid characters or SQL keywords" in str(exc_info.value)

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
    async def test_create_already_exists(self, todo_service, mock_repository):
        """Test creating a ToDo that already exists."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Duplicate", description="Desc")
        mock_repository.create_to_do.side_effect = IntegrityError("msg", "params", "orig")

        with pytest.raises(ToDoAlreadyExistsError):
            await todo_service.create_todo(payload)


class TestCreateTodoRepositoryInteraction:
    """Test create_todo repository interaction."""

    @pytest.mark.asyncio
    async def test_create_calls_repository_create(self, todo_service, mock_repository):
        """Test create_todo calls repository.create_to_do."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        mock_repository.create_to_do.assert_called_once()
        args = mock_repository.create_to_do.call_args[0]
        assert isinstance(args[0], ToDoEntryData)
        assert args[0].id == todo_id

    @pytest.mark.asyncio
    async def test_create_passes_validated_data(self, todo_service, mock_repository):
        """Test create_todo passes validated data to repository."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(
            id=todo_id,
            title="  Test  ",
            description="  Desc  "
        )
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        args = mock_repository.create_to_do.call_args[0]
        assert args[0].title == "Test"
        assert args[0].description == "Desc"

    @pytest.mark.asyncio
    async def test_create_sets_default_values(self, todo_service, mock_repository):
        """Test create_todo sets default values for new entry."""
        todo_id = uuid.uuid4()
        payload = ToDoCreateScheme(id=todo_id, title="Test", description="Desc")
        mock_repository.create_to_do.return_value = None

        await todo_service.create_todo(payload)

        args = mock_repository.create_to_do.call_args[0]
        assert args[0].done is False
        assert args[0].deleted is False
        assert args[0].updated_at is None
        assert args[0].created_at is not None
