""" GET /todo/{todo_id} tests"""
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
)
from backend.app.schemas.todo import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service)


class TestGetTodo:
    """Tests for GET /todo/{todo_id} endpoint."""

    def test_get_todo_success(self, client, mock_service, created_todo):
        """Test successful retrieval returns 200 and correct format."""
        # Mock service to return the todo
        todo_id = uuid4()
        mock_service.get_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title=created_todo["title"],
            description=created_todo["description"],
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        response = client.get(f"/todo/{created_todo['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "todo_entry" in data
        assert data["todo_entry"]["title"] == created_todo["title"]

    def test_get_todo_not_found_returns_404(self, client, mock_service):
        """Test getting non-existent todo returns 404."""
        # Mock service to raise not found error
        mock_service.get_todo = AsyncMock(side_effect=ToDoNotFoundError())

        non_existent_id = uuid4()

        response = client.get(f"/todo/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.text.lower()

    def test_get_todo_invalid_uuid_returns_422(self, client):
        """Test invalid UUID in path returns 422."""
        response = client.get("/todo/not-a-uuid")

        assert response.status_code == 422

    def test_get_todo_deleted_returns_404(self, client, mock_service, created_todo):
        """Test getting deleted todo returns 404."""
        # Mock delete to succeed
        mock_service.delete_todo = AsyncMock(return_value=True)

        # Delete the todo
        delete_response = client.delete(f"/todo/{created_todo['id']}")
        assert delete_response.status_code == 200

        # Mock get_todo to raise not found error (deleted todos are not found)
        mock_service.get_todo = AsyncMock(side_effect=ToDoNotFoundError())

        # Try to get it
        response = client.get(f"/todo/{created_todo['id']}")

        assert response.status_code == 404