"""Integration tests for ToDoService.get_all_todos()."""
import datetime
import uuid

import pytest

from backend.app.models.todo import ToDoEntryData


class TestGetAllTodosSuccessIntegration:
    """Integration tests for successful get_all_todos scenarios."""

    @pytest.mark.asyncio
    async def test_get_all_returns_valid_entries(self, todo_service, mock_repository):
        """Test get_all_todos returns valid entries."""
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
    async def test_get_all_returns_empty_list_when_no_entries(self, todo_service, mock_repository):
        """Test get_all_todos returns empty list when no entries."""
        mock_repository.get_all_to_do_entries.return_value = []

        result = await todo_service.get_all_todos()

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_returns_single_entry(self, todo_service, mock_repository):
        """Test get_all_todos returns single entry."""
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


class TestGetAllTodosInvalidEntriesIntegration:
    """Integration tests for get_all_todos with invalid entries."""

    @pytest.mark.asyncio
    async def test_get_all_skips_invalid_entries(self, todo_service, mock_repository):
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
        invalid_entry = "invalid"
        mock_repository.get_all_to_do_entries.return_value = [valid_entry, invalid_entry]

        result = await todo_service.get_all_todos()

        assert len(result) == 1
        assert result[0].title == "Valid"

    @pytest.mark.asyncio
    async def test_get_all_returns_empty_when_all_invalid(self, todo_service, mock_repository):
        """Test get_all_todos returns empty list when all entries invalid."""
        invalid_entry1 = "invalid1"
        invalid_entry2 = None
        mock_repository.get_all_to_do_entries.return_value = [invalid_entry1, invalid_entry2]

        result = await todo_service.get_all_todos()

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_skips_multiple_invalid_entries(self, todo_service, mock_repository):
        """Test get_all_todos skips multiple invalid entries."""
        valid1 = ToDoEntryData(
            id=uuid.uuid4(),
            title="Valid1",
            description="Desc1",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        valid2 = ToDoEntryData(
            id=uuid.uuid4(),
            title="Valid2",
            description="Desc2",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        invalid1 = "invalid1"
        invalid2 = {"bad": "data"}
        mock_repository.get_all_to_do_entries.return_value = [valid1, invalid1, valid2, invalid2]

        result = await todo_service.get_all_todos()

        assert len(result) == 2
        assert result[0].title == "Valid1"
        assert result[1].title == "Valid2"


class TestGetAllTodosPaginationIntegration:
    """Integration tests for get_all_todos pagination."""

    @pytest.mark.asyncio
    async def test_get_all_with_custom_limit(self, todo_service, mock_repository):
        """Test get_all_todos with custom limit."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(limit=5)

        mock_repository.get_all_to_do_entries.assert_called_once_with(5, 1)

    @pytest.mark.asyncio
    async def test_get_all_with_custom_page(self, todo_service, mock_repository):
        """Test get_all_todos with custom page."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(page=3)

        mock_repository.get_all_to_do_entries.assert_called_once_with(10, 3)

    @pytest.mark.asyncio
    async def test_get_all_with_custom_limit_and_page(self, todo_service, mock_repository):
        """Test get_all_todos with custom limit and page."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos(limit=20, page=2)

        mock_repository.get_all_to_do_entries.assert_called_once_with(20, 2)

    @pytest.mark.asyncio
    async def test_get_all_default_pagination(self, todo_service, mock_repository):
        """Test get_all_todos uses default pagination values."""
        mock_repository.get_all_to_do_entries.return_value = []

        await todo_service.get_all_todos()

        # Default: limit=10, page=1
        mock_repository.get_all_to_do_entries.assert_called_once_with(10, 1)
