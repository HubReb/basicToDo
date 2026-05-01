"""Tests for PATCH /todo/{id}/restore endpoint."""

import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import ToDoNotFoundError
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class TestRestoreEndpoint:
    """Tests for PATCH /todo/{id}/restore endpoint."""

    def test_restore_deleted_todo_returns_200(self, client, mock_service):
        """Test restoring a deleted todo returns 200 with restored entry."""
        todo_id = uuid4()
        restored_todo = ToDoSchema(
            id=todo_id,
            title="Restored Todo",
            description="Restored Description",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        )
        mock_service.restore_todo = AsyncMock(return_value=restored_todo)

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["todo_entry"]["id"] == str(todo_id)
        assert data["todo_entry"]["deleted"] is False

    def test_restore_active_todo_returns_404(self, client, mock_service):
        """Test restoring an active (non-deleted) todo returns 404."""
        todo_id = uuid4()
        mock_service.restore_todo = AsyncMock(side_effect=ToDoNotFoundError)

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 404

    def test_restore_missing_todo_returns_404(self, client, mock_service):
        """Test restoring a non-existent todo returns 404."""
        todo_id = uuid4()
        mock_service.restore_todo = AsyncMock(side_effect=ToDoNotFoundError)

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 404

    def test_restore_calls_service_with_correct_id(self, client, mock_service):
        """Test restore endpoint calls service with the correct todo id."""
        todo_id = uuid4()
        restored_todo = ToDoSchema(
            id=todo_id,
            title="Restored Todo",
            description=None,
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        )
        mock_service.restore_todo = AsyncMock(return_value=restored_todo)

        client.patch(f"/todo/{todo_id}/restore")

        mock_service.restore_todo.assert_called_once_with(todo_id)
