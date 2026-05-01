"""Tests for GET /todo/deleted endpoint."""
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import client, mock_service


class TestListDeletedEndpoint:
    """Tests for GET /todo/deleted endpoint."""

    def test_list_deleted_with_items_returns_200(self, client, mock_service):
        """Test listing deleted todos returns 200 with correct entries."""
        todo_id = uuid4()
        deleted_todo = ToDoSchema(
            id=todo_id,
            title="Deleted Todo",
            description="Description",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=True,
            done=False,
        )
        mock_service.get_deleted_todos = AsyncMock(return_value=[deleted_todo])

        response = client.get("/todo/deleted")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["todo_entries"]) == 1
        assert data["todo_entries"][0]["id"] == str(todo_id)

    def test_list_deleted_with_no_items_returns_200_empty(self, client, mock_service):
        """Test listing deleted todos when none exist returns 200 with empty list."""
        mock_service.get_deleted_todos = AsyncMock(return_value=[])

        response = client.get("/todo/deleted")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["todo_entries"] == []
        assert data["total_count"] == 0

    def test_list_deleted_with_pagination_params(self, client, mock_service):
        """Test listing deleted todos with limit and page params uses correct pagination."""
        mock_service.get_deleted_todos = AsyncMock(return_value=[])

        response = client.get("/todo/deleted?limit=5&page=2")

        assert response.status_code == 200
        mock_service.get_deleted_todos.assert_called_once_with(5, 2)

    def test_list_deleted_invalid_limit_returns_422(self, client, mock_service):
        """Test invalid limit (0 or negative) returns 422."""
        response = client.get("/todo/deleted?limit=0")
        assert response.status_code == 422

    def test_list_deleted_invalid_page_returns_422(self, client, mock_service):
        """Test invalid page (0 or negative) returns 422."""
        response = client.get("/todo/deleted?page=0")
        assert response.status_code == 422
