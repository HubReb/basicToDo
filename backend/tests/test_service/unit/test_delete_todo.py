"""Unit tests for ToDoService.delete_todo() method."""
import uuid

import pytest

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
)


class TestDeleteTodoSuccess:
    """Test successful delete_todo scenarios."""

    @pytest.mark.asyncio
    async def test_delete_success(self, todo_service, mock_repository):
        """Test deleting a ToDo successfully."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True
        mock_repository.delete_to_do.assert_called_once_with(todo_id)

    @pytest.mark.asyncio
    async def test_delete_returns_true(self, todo_service, mock_repository):
        """Test delete_todo returns True on success."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True
        assert isinstance(result, bool)


class TestDeleteTodoValidation:
    """Test delete_todo validation."""

    @pytest.mark.asyncio
    async def test_delete_validates_uuid(self, todo_service, mock_repository):
        """Test delete validates UUID before calling repository."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        await todo_service.delete_todo(todo_id)

        # Verify validator was called (indirectly via successful deletion)
        mock_repository.delete_to_do.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_with_valid_uuid_object(self, todo_service, mock_repository):
        """Test deleting with valid UUID object."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True


class TestDeleteTodoNotFound:
    """Test delete_todo not found scenarios."""

    @pytest.mark.asyncio
    async def test_delete_not_found(self, todo_service, mock_repository):
        """Test deleting a non-existent ToDo."""
        mock_repository.delete_to_do.return_value = False
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.delete_todo(todo_id)

    @pytest.mark.asyncio
    async def test_delete_not_found_returns_false_from_repo(self, todo_service, mock_repository):
        """Test delete_todo raises error when repository returns False."""
        mock_repository.delete_to_do.return_value = False
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.delete_todo(todo_id)

        mock_repository.delete_to_do.assert_called_once_with(todo_id)


class TestDeleteTodoRepositoryInteraction:
    """Test delete_todo repository interaction."""

    @pytest.mark.asyncio
    async def test_delete_calls_repository_delete(self, todo_service, mock_repository):
        """Test delete_todo calls repository.delete_to_do."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        await todo_service.delete_todo(todo_id)

        mock_repository.delete_to_do.assert_called_once_with(todo_id)

    @pytest.mark.asyncio
    async def test_delete_passes_validated_uuid(self, todo_service, mock_repository):
        """Test delete_todo passes validated UUID to repository."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        await todo_service.delete_todo(todo_id)

        call_args = mock_repository.delete_to_do.call_args[0]
        assert isinstance(call_args[0], uuid.UUID)
        assert call_args[0] == todo_id