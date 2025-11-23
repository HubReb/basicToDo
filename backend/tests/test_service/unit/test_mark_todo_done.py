"""Unit tests for ToDoService.mark_to_do_as_done() method."""
import datetime
import uuid

import pytest

from backend.app.business_logic.exceptions import ToDoNotFoundError
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class TestMarkTodoDoneSuccess:
    """Test successful mark_to_do_as_done scenarios."""

    @pytest.mark.asyncio
    async def test_mark_as_done_success(self, todo_service, mock_repository):
        """Test marking a ToDo as done successfully."""
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

        result = await todo_service.mark_to_do_as_done(todo_id)

        assert result.done is True
        mock_repository.update_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_done_returns_schema(self, todo_service, mock_repository):
        """Test mark_as_done returns ToDoSchema."""
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

        result = await todo_service.mark_to_do_as_done(todo_id)

        assert isinstance(result, ToDoSchema)
        assert result.id == todo_id

    @pytest.mark.asyncio
    async def test_mark_as_done_preserves_title_and_description(self, todo_service, mock_repository):
        """Test mark_as_done preserves original title and description."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Original Title",
            description="Original Description",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_updated_entry = ToDoEntryData(
            id=todo_id,
            title="Original Title",
            description="Original Description",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry
        mock_repository.update_to_do.return_value = mock_updated_entry

        result = await todo_service.mark_to_do_as_done(todo_id)

        assert result.title == "Original Title"
        assert result.description == "Original Description"


class TestMarkTodoDoneNotFound:
    """Test mark_to_do_as_done not found scenarios."""

    @pytest.mark.asyncio
    async def test_mark_as_done_not_found(self, todo_service, mock_repository):
        """Test marking a non-existent ToDo as done."""
        mock_repository.get_to_do_entry.return_value = None
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.mark_to_do_as_done(todo_id)

    @pytest.mark.asyncio
    async def test_mark_as_done_not_found_does_not_update(self, todo_service, mock_repository):
        """Test mark_as_done doesn't call update when entry not found."""
        mock_repository.get_to_do_entry.return_value = None
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.mark_to_do_as_done(todo_id)

        mock_repository.update_to_do.assert_not_called()


class TestMarkTodoDoneRepositoryInteraction:
    """Test mark_to_do_as_done repository interaction."""

    @pytest.mark.asyncio
    async def test_mark_as_done_calls_get_then_update(self, todo_service, mock_repository):
        """Test mark_as_done calls get_to_do_entry then update_to_do."""
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

        await todo_service.mark_to_do_as_done(todo_id)

        mock_repository.get_to_do_entry.assert_called_once_with(todo_id)
        mock_repository.update_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_done_updates_with_done_true(self, todo_service, mock_repository):
        """Test mark_as_done creates proper update payload with done=True."""
        todo_id = uuid.uuid4()
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Original",
            description="Original Desc",
            created_at=datetime.datetime.now(),
            updated_at=None,
            done=False,
            deleted=False
        )
        mock_updated_entry = ToDoEntryData(
            id=todo_id,
            title="Original",
            description="Original Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=True,
            deleted=False
        )
        mock_repository.get_to_do_entry.return_value = mock_entry
        mock_repository.update_to_do.return_value = mock_updated_entry

        await todo_service.mark_to_do_as_done(todo_id)

        # Verify update was called with done=True
        call_args = mock_repository.update_to_do.call_args[0]
        update_payload = call_args[1]
        assert update_payload.done is True
        assert update_payload.title == "Original"
        assert update_payload.description == "Original Desc"

    @pytest.mark.asyncio
    async def test_mark_as_done_passes_todo_id(self, todo_service, mock_repository):
        """Test mark_as_done passes correct todo_id to update_to_do."""
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

        await todo_service.mark_to_do_as_done(todo_id)

        call_args = mock_repository.update_to_do.call_args[0]
        assert call_args[0] == todo_id
