""" Response schema validation tests """
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.schemas.todo import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service, sample_todo_id)


class TestResponseSchemas:
    """Tests for response schema validation."""

    def test_create_response_has_required_fields(self, client, mock_service, sample_todo_id):
        """Test create response has all required fields."""
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=sample_todo_id,
            title="Test",
            description="Test",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        payload = {
            "id": str(sample_todo_id),
            "title": "Test",
            "description": "Test"
        }
        response = client.post("/todo", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "todo_entry" in data

        todo = data["todo_entry"]
        assert "id" in todo
        assert "title" in todo
        assert "description" in todo
        assert "created_at" in todo
        assert "updated_at" in todo
        assert "done" in todo
        assert "deleted" in todo

    def test_get_response_has_required_fields(self, client, mock_service, created_todo):
        """Test get response has all required fields."""
        # Mock service to return a todo
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
        assert "success" in data
        assert "todo_entry" in data

    def test_list_response_has_required_fields(self, client, mock_service):
        """Test list response has all required fields."""
        # Mock service to return a todo (empty lists are rejected by schema)
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=uuid4(),
                title="Test",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            )
        ])

        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "results" in data
        assert "todo_entries" in data

    def test_delete_response_has_required_fields(self, client, mock_service, created_todo):
        """Test delete response has all required fields."""
        # Mock service to return successful deletion
        mock_service.delete_todo = AsyncMock(return_value=True)

        response = client.delete(f"/todo/{created_todo['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data