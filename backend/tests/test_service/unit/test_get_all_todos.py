"""Unit tests for ToDoService.get_all_todos() method."""
import datetime
import uuid

import pytest

from backend.app.models.todo import ToDoEntryData


class TestGetAllTodosSuccess:
    """Test successful get_all_todos scenarios."""

    @pytest.mark.asyncio
    async def test_get_all_success(self, todo_service, mock_repository):
        """Test getting all ToDos successfully."""
        entry1 = ToDoEntryData(
            id=uuid.uuid4(),
            title="Test1",
            description="Desc1",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        entry2 = ToDoEntryData(
            id=uuid.uuid4(),
            title="Test2",
            description="Desc2",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_all_to_do_entries.return_value = [entry1, entry2]

        result = await todo_service.get_all_todos()

        assert len(result) == 2
        assert result[0].title == "Test1"
        assert result[1].title == "Test2"

    @pytest.mark.asyncio
    async def test_get_all_empty_result(self, todo_service, mock_repository):
        """Test getting all ToDos with empty result."""
        mock_repository.get_all_to_do_entries.return_value = []

        result = await todo_service.get_all_todos()

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self, todo_service, mock_repository):
        """Test get_all_todos always returns list."""
        mock_repository.get_all_to_do_entries.return_value = []

        result = await todo_service.get_all_todos()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_single_entry(self, todo_service, mock_repository):
        """Test getting all ToDos with single entry."""
        entry = ToDoEntryData(
            id=uuid.uuid4(),
            title="Single",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_repository.get_all_to_do_entries.return_value = [entry]

        result = await todo_service.get_all_todos()

        assert len(result) == 1
        assert result[0].title == "Single"


class TestGetAllTodosPagination:
    """Test get_all_todos pagination."""

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self, todo_service, mock_repository):
        """Test getting all ToDos with custom limit."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(limit=5)

        mock_repository.get_all_to_do_entries.assert_called_once_with(5, 1)

    @pytest.mark.asyncio
    async def test_get_all_with_page(self, todo_service, mock_repository):
        """Test getting all ToDos with custom page."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(page=3)

        mock_repository.get_all_to_do_entries.assert_called_once_with(10, 3)

    @pytest.mark.asyncio
    async def test_get_all_with_limit_and_page(self, todo_service, mock_repository):
        """Test getting all ToDos with custom limit and page."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(limit=20, page=2)

        mock_repository.get_all_to_do_entries.assert_called_once_with(20, 2)

    @pytest.mark.asyncio
    async def test_get_all_default_pagination(self, todo_service, mock_repository):
        """Test get_all_todos default pagination values."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos()

        # Default: limit=10, page=1
        mock_repository.get_all_to_do_entries.assert_called_once_with(10, 1)


class TestGetAllTodosInvalidEntries:
    """Test get_all_todos with invalid entries."""

    @pytest.mark.asyncio
    async def test_get_all_skips_invalid(self, todo_service, mock_repository):
        """Test get_all_todos skips invalid entries."""
        valid_entry = ToDoEntryData(
            id=uuid.uuid4(),
            title="Valid",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        invalid_entry = "invalid entry"
        mock_repository.get_all_to_do_entries.return_value = [valid_entry, invalid_entry]

        result = await todo_service.get_all_todos()

        assert len(result) == 1
        assert result[0].title == "Valid"

    @pytest.mark.asyncio
    async def test_get_all_logs_invalid_entries(self, todo_service, mock_repository, mock_logger):
        """Test get_all_todos logs warning for invalid entries."""
        valid_entry = ToDoEntryData(
            id=uuid.uuid4(),
            title="Valid",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        invalid_entry = "invalid entry"
        mock_repository.get_all_to_do_entries.return_value = [valid_entry, invalid_entry]

        await todo_service.get_all_todos()

        # Should log warning for invalid entry
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_get_all_all_invalid_returns_empty(self, todo_service, mock_repository):
        """Test get_all_todos returns empty list when all entries invalid."""
        invalid_entry1 = "invalid1"
        invalid_entry2 = None
        mock_repository.get_all_to_do_entries.return_value = [invalid_entry1, invalid_entry2]

        result = await todo_service.get_all_todos()

        assert result == []


class TestGetAllTodosRepositoryInteraction:
    """Test get_all_todos repository interaction."""

    @pytest.mark.asyncio
    async def test_get_all_calls_repository_get_all(self, todo_service, mock_repository):
        """Test get_all_todos calls repository.get_all_to_do_entries."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos()

        mock_repository.get_all_to_do_entries.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_passes_correct_params(self, todo_service, mock_repository):
        """Test get_all_todos passes correct parameters to repository."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(limit=15, page=5)

        call_args = mock_repository.get_all_to_do_entries.call_args[0]
        assert call_args[0] == 15  # limit
        assert call_args[1] == 5  # page