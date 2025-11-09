"""Integration tests for ToDoService.delete_todo() with real validators."""
import uuid

import pytest

from backend.app.business_logic.exceptions import ToDoNotFoundError


class TestDeleteTodoValidationIntegration:
    """Integration tests for delete_todo validation."""

    @pytest.mark.asyncio
    async def test_delete_validates_uuid(self, todo_service, mock_repository):
        """Test delete_todo validates UUID."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_accepts_valid_uuid(self, todo_service, mock_repository):
        """Test delete_todo accepts valid UUID object."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True
        mock_repository.delete_to_do.assert_called_once_with(todo_id)


class TestDeleteTodoNotFoundIntegration:
    """Integration tests for delete_todo not found scenarios."""

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_error(self, todo_service, mock_repository):
        """Test delete_todo raises ToDoNotFoundError when entry not found."""
        mock_repository.delete_to_do.return_value = False

        with pytest.raises(ToDoNotFoundError):
            await todo_service.delete_todo(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_not_found_when_repository_returns_false(self, todo_service, mock_repository):
        """Test delete_todo raises error when repository returns False."""
        mock_repository.delete_to_do.return_value = False
        todo_id = uuid.uuid4()

        with pytest.raises(ToDoNotFoundError):
            await todo_service.delete_todo(todo_id)

        mock_repository.delete_to_do.assert_called_once_with(todo_id)


class TestDeleteTodoSuccessIntegration:
    """Integration tests for successful delete_todo scenarios."""

    @pytest.mark.asyncio
    async def test_delete_success_returns_true(self, todo_service, mock_repository):
        """Test delete_todo returns True on success."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        result = await todo_service.delete_todo(todo_id)

        assert result is True
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_delete_calls_repository_delete(self, todo_service, mock_repository):
        """Test delete_todo calls repository.delete_to_do."""
        todo_id = uuid.uuid4()
        mock_repository.delete_to_do.return_value = True

        await todo_service.delete_todo(todo_id)

        mock_repository.delete_to_do.assert_called_once_with(todo_id)
