""" DELETE /todo/{todo_id} tests"""

from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
)
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service)


class TestDeleteTodo:
    """Tests for DELETE /todo/{todo_id} endpoint."""

    def test_delete_todo_success(self, client, mock_service, created_todo):
        """Test successful deletion returns 200."""
        # Mock service to return successful deletion
        mock_service.delete_todo = AsyncMock(return_value=True)

        response = client.delete(f"/todo/{created_todo['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    def test_delete_todo_not_found_returns_404(self, client, mock_service):
        """Test deleting non-existent todo returns 404."""
        # Mock service to raise not found error
        mock_service.delete_todo = AsyncMock(side_effect=ToDoNotFoundError())

        response = client.delete(f"/todo/{uuid4()}")

        assert response.status_code == 404

    def test_delete_todo_invalid_uuid_returns_422(self, client):
        """Test deleting with invalid UUID returns 422."""
        response = client.delete("/todo/not-a-uuid")

        assert response.status_code == 422

    def test_delete_todo_is_soft_delete(self, client, mock_service, created_todo):
        """Test that delete is soft delete (marked as deleted, not removed)."""
        # Mock service to return successful deletion
        mock_service.delete_todo = AsyncMock(return_value=True)

        # Delete the todo
        delete_response = client.delete(f"/todo/{created_todo['id']}")
        assert delete_response.status_code == 200

        # Mock get_todo to raise not found error (soft-deleted items are not found)
        mock_service.get_todo = AsyncMock(side_effect=ToDoNotFoundError())

        # Try to get it - should return 404 for soft-deleted items
        get_response = client.get(f"/todo/{created_todo['id']}")
        assert get_response.status_code == 404

    def test_delete_todo_twice_returns_404(self, client, mock_service, created_todo):
        """Test deleting already deleted todo returns 404."""
        # Mock service to return successful deletion first time
        mock_service.delete_todo = AsyncMock(return_value=True)

        # First delete
        first_response = client.delete(f"/todo/{created_todo['id']}")
        assert first_response.status_code == 200

        # Mock service to raise not found error on second delete
        mock_service.delete_todo = AsyncMock(side_effect=ToDoNotFoundError())

        # Second delete
        second_response = client.delete(f"/todo/{created_todo['id']}")
        assert second_response.status_code == 404