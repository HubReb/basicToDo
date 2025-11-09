import datetime
import uuid

import pytest

from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class TestUpdateTodoRepositoryInteraction:
    """Test update_todo repository interaction."""

    @pytest.mark.asyncio
    async def test_update_calls_repository_update(self, todo_service, mock_repository):
        """Test update_todo calls repository.update_to_do."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(id=todo_id, title="Updated")
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

        mock_repository.update_to_do.assert_called_once_with(todo_id, payload)

    @pytest.mark.asyncio
    async def test_update_passes_sanitized_payload(self, todo_service, mock_repository):
        """Test update_todo passes sanitized payload to repository."""
        todo_id = uuid.uuid4()
        payload = TodoUpdateScheme(
            id=todo_id,
            title="  Test  ",
            description="  Desc  "
        )
        mock_entry = ToDoEntryData(
            id=todo_id,
            title="Test",
            description="Desc",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            done=False,
            deleted=False
        )
        mock_repository.update_to_do.return_value = mock_entry

        await todo_service.update_todo(todo_id, payload)
        call_args = mock_repository.update_to_do.call_args[0][1]
        assert call_args.title == "Test"
        assert call_args.description == "Desc"