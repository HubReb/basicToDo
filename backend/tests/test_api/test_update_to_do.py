""" PUT /todo/{todo_id} tests """
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import (
    ToDoNotFoundError,
    ToDoValidationError
)
from backend.app.schemas.todo import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service)


class TestUpdateTodo:
    """Tests for PUT /todo/{todo_id} endpoint."""

    def test_update_todo_success(self, client, mock_service, created_todo):
        """Test successful update returns 200."""
        # Mock service to return updated todo
        todo_id = uuid4()
        mock_service.update_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title="Updated Title",
            description="Updated Description",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            deleted=False,
            done=False,
        ))

        update_payload = {
            "id": created_todo["id"],
            "title": "Updated Title",
            "description": "Updated Description"
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["todo_entry"]["title"] == "Updated Title"
        assert data["todo_entry"]["description"] == "Updated Description"

    def test_update_todo_mark_as_done(self, client, mock_service, created_todo):
        """Test marking todo as done."""
        # Mock service to return todo marked as done
        todo_id = uuid4()
        mock_service.update_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title=created_todo["title"],
            description=created_todo["description"],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            deleted=False,
            done=True,
        ))

        update_payload = {
            "id": created_todo["id"],
            "done": True
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["todo_entry"]["done"] is True

    def test_update_todo_partial_update(self, client, mock_service, created_todo):
        """Test partial update with only some fields."""
        # Mock service to return updated todo with preserved description
        todo_id = uuid4()
        mock_service.update_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title="Only Title Updated",
            description=created_todo["description"],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            deleted=False,
            done=False,
        ))

        update_payload = {
            "id": created_todo["id"],
            "title": "Only Title Updated"
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["todo_entry"]["title"] == "Only Title Updated"
        # Original description should be preserved
        assert data["todo_entry"]["description"] == created_todo["description"]

    def test_update_todo_not_found_returns_404(self, client, mock_service):
        """Test updating non-existent todo returns 404."""
        # Mock service to raise not found error
        mock_service.update_todo = AsyncMock(side_effect=ToDoNotFoundError())

        non_existent_id = uuid4()
        update_payload = {
            "id": str(non_existent_id),
            "title": "Updated"
        }

        response = client.put(f"/todo/{non_existent_id}", json=update_payload)

        assert response.status_code == 404

    def test_update_todo_invalid_uuid_returns_422(self, client):
        """Test invalid UUID returns 422."""
        update_payload = {
            "id": "not-a-uuid",
            "title": "Updated"
        }

        response = client.put("/todo/not-a-uuid", json=update_payload)

        assert response.status_code == 422

    def test_update_todo_sql_injection_returns_400(self, client, mock_service, created_todo):
        """Test SQL injection attempt in update returns 400."""
        # Mock service to raise validation error for SQL injection
        mock_service.update_todo = AsyncMock(
            side_effect=ToDoValidationError("Invalid characters or SQL keywords in input"))

        update_payload = {
            "id": created_todo["id"],
            "title": "'; DROP TABLE todo;--"
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code == 400

    def test_update_todo_empty_title_returns_422(self, client, mock_service, created_todo):
        """Test updating with empty title returns 422."""
        # Mock service to raise validation error for empty title
        mock_service.update_todo = AsyncMock(side_effect=ToDoValidationError("Title cannot be empty"))

        update_payload = {
            "id": created_todo["id"],
            "title": ""
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code in [400, 422]

    def test_update_todo_with_emoji(self, client, mock_service, created_todo):
        """Test updating todo with emoji."""
        # Mock service to return updated todo with emoji
        todo_id = uuid4()
        mock_service.update_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title="Updated with emoji 🎉",
            description=created_todo["description"],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            deleted=False,
            done=False,
        ))

        update_payload = {
            "id": created_todo["id"],
            "title": "Updated with emoji 🎉"
        }

        response = client.put(f"/todo/{created_todo['id']}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert "🎉" in data["todo_entry"]["title"]