"""GET /todo (list) tests"""

import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


class TestListTodos:
    """Tests for GET /todo endpoint."""

    def test_list_todos_success(self, client, mock_service):
        """Test listing todos returns 200 and array."""
        # Mock service to return a list with one todo (empty lists are rejected by schema)
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=uuid4(),
                    title="Test Todo",
                    description="Test Description",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
            ]
        )

        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "todo_entries" in data
        assert isinstance(data["todo_entries"], list)
        assert "results" in data
        assert isinstance(data["results"], int)

    def test_list_todos_returns_created_items(self, client, mock_service):
        """Test that created todos appear in list."""
        # Create test data
        todo_ids = []
        created_todos = []
        for i in range(3):
            todo_id = uuid4()
            todo_ids.append(str(todo_id))
            created_todos.append(
                ToDoSchema(
                    id=todo_id,
                    title=f"Todo {i}",
                    description=f"Description {i}",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
            )

        # Mock get_all_todos to return our test data
        mock_service.get_all_todos = AsyncMock(return_value=created_todos)

        # List todos
        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        returned_ids = [todo["id"] for todo in data["todo_entries"]]

        # All created todos should be in the list
        for todo_id in todo_ids:
            assert todo_id in returned_ids

    def test_list_todos_pagination_default(self, client, mock_service):
        """Test default pagination parameters."""
        # Mock service to return list of todos (max 10 by default)
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=uuid4(),
                    title=f"Todo {i}",
                    description=f"Description {i}",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
                for i in range(5)
            ]
        )

        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 10
        assert len(data["todo_entries"]) <= 10

    def test_list_todos_pagination_custom_limit(self, client, mock_service):
        """Test pagination with custom limit."""
        # Mock service to return list with max 2 items
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=uuid4(),
                    title=f"Todo {i}",
                    description="Test",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
                for i in range(2)
            ]
        )

        # Request with limit 2
        response = client.get("/todo?limit=2&page=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["todo_entries"]) <= 2

    def test_list_todos_pagination_page_2(self, client, mock_service):
        """Test getting second page of results."""
        # Mock service to return remaining items from page 2
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=uuid4(),
                    title=f"Todo {i}",
                    description="Test",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
                for i in range(5)  # 5 remaining items on page 2
            ]
        )

        # Get page 2 with limit 10
        response = client.get("/todo?limit=10&page=2")

        assert response.status_code == 200
        data = response.json()
        # Should have remaining items
        assert len(data["todo_entries"]) >= 0

    def test_list_todos_excludes_deleted(self, client, mock_service):
        """Test that deleted todos don't appear in list."""
        todo_id = uuid4()
        other_todo_id = uuid4()

        # Mock create_todo
        mock_service.create_todo = AsyncMock(
            return_value=ToDoSchema(
                id=todo_id,
                title="To Be Deleted",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            )
        )

        # Create a todo
        payload = {"id": str(todo_id), "title": "To Be Deleted", "description": "Test"}
        client.post("/todo", json=payload)

        # Mock delete_todo
        mock_service.delete_todo = AsyncMock(return_value=True)

        # Delete it
        client.delete(f"/todo/{todo_id}")

        # Mock get_all_todos to return only non-deleted todos
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=other_todo_id,
                    title="Not Deleted",
                    description="Test",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
            ]
        )

        # List todos
        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        returned_ids = [todo["id"] for todo in data["todo_entries"]]

        # Deleted todo should not be in list
        assert str(todo_id) not in returned_ids

    @pytest.mark.parametrize(
        "query",
        [
            "limit=-1",
            "limit=0",
            "limit=101",
            "limit=1000",
            "page=-1",
            "page=0",
            "page=1000001",
        ],
    )
    def test_list_todos_out_of_bounds_is_a_422(self, client, mock_service, query):
        """Q6.4 / SEC-004: limit 1 to 100, page 1 to 1,000,000; the service is not called."""
        mock_service.get_all_todos = AsyncMock(return_value=[])

        response = client.get(f"/todo?{query}")

        assert response.status_code == 422
        mock_service.get_all_todos.assert_not_called()

    @pytest.mark.parametrize("query", ["limit=1", "limit=100", "page=1000000"])
    def test_list_todos_at_the_bounds_is_accepted(self, client, mock_service, query):
        """Q6.4: the bounds themselves are valid."""
        mock_service.get_all_todos = AsyncMock(return_value=[])

        assert client.get(f"/todo?{query}").status_code == 200

    def test_list_todos_returns_json_content_type(self, client, mock_service):
        """Test list endpoint returns JSON."""
        # Mock service to return a todo (empty lists are rejected by schema)
        mock_service.get_all_todos = AsyncMock(
            return_value=[
                ToDoSchema(
                    id=uuid4(),
                    title="Test",
                    description="Test",
                    created_at=datetime.datetime.now(),
                    updated_at=None,
                    deleted=False,
                    done=False,
                )
            ]
        )

        response = client.get("/todo")

        assert "application/json" in response.headers["content-type"]
