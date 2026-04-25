"""Integration tests for PATCH /todo/{id}/restore and GET /todo/deleted."""
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.app.business_logic.exceptions import ToDoNotFoundError
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import client, mock_service


class TestRestoreTodoEndpoint:
    """Tests for PATCH /todo/{id}/restore."""

    def test_restore_returns_200(self, client, mock_service):
        """Test successful restore returns 200 with todo_entry."""
        todo_id = uuid4()
        mock_service.restore_todo = AsyncMock(
            return_value=ToDoSchema(
                id=todo_id,
                title="Restored Todo",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                deleted=False,
                done=False,
            )
        )

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["todo_entry"]["id"] == str(todo_id)
        assert data["todo_entry"]["deleted"] is False

    def test_restore_nonexistent_returns_404(self, client, mock_service):
        """Test restoring a non-existent todo returns 404."""
        todo_id = uuid4()
        mock_service.restore_todo = AsyncMock(side_effect=ToDoNotFoundError)

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 404

    def test_restore_active_todo_returns_404(self, client, mock_service):
        """Test restoring a non-deleted (active) todo returns 404."""
        todo_id = uuid4()
        mock_service.restore_todo = AsyncMock(side_effect=ToDoNotFoundError)

        response = client.patch(f"/todo/{todo_id}/restore")

        assert response.status_code == 404

    def test_restore_invalid_uuid_returns_422(self, client, mock_service):
        """Test restoring with invalid UUID returns 422."""
        response = client.patch("/todo/not-a-uuid/restore")

        assert response.status_code == 422


class TestGetDeletedTodosEndpoint:
    """Tests for GET /todo/deleted."""

    def test_list_deleted_returns_todos_with_total_count(self, client, mock_service):
        """Test GET /todo/deleted returns list with total_count."""
        todo_id = uuid4()
        mock_service.get_deleted_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=todo_id,
                    title="Deleted Todo",
                    description="Test",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=True,
                    done=False,
                )
            ]
        )
        mock_service.count_deleted = AsyncMock(return_value=1)

        response = client.get("/todo/deleted")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_count"] == 1
        assert data["results"] == 1
        assert len(data["todo_entries"]) == 1
        assert data["todo_entries"][0]["deleted"] is True

    def test_list_deleted_empty_returns_empty(self, client, mock_service):
        """Test GET /todo/deleted with no deleted items."""
        mock_service.get_deleted_todos = AsyncMock(return_value=[])
        mock_service.count_deleted = AsyncMock(return_value=0)

        response = client.get("/todo/deleted")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["results"] == 0
        assert len(data["todo_entries"]) == 0
