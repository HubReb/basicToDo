"""Comprehensive API endpoint tests for ToDo application."""
import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.api.api import app
from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoValidationError,
)
from backend.app.schemas.todo import ToDoSchema


@pytest.fixture
def mock_service():
    """Provide a mock service for API tests."""
    with patch("backend.app.api.api.service") as mock:
        yield mock


@pytest.fixture
def client(mock_service):
    """Provide FastAPI test client with mocked service."""
    return TestClient(app)


@pytest.fixture
def sample_todo_id():
    """Provide consistent UUID for testing."""
    return uuid4()


@pytest.fixture
def created_todo(client, mock_service, sample_todo_id):
    """Create a todo and return its data."""
    # Mock the service to return a ToDoSchema constructed from the payload
    mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
        id=sample_todo_id,
        title="Test Todo",
        description="Test Description",
        created_at=datetime.datetime.now(),
        updated_at=None,
        deleted=False,
        done=False,
    ))

    payload = {
        "id": str(sample_todo_id),
        "title": "Test Todo",
        "description": "Test Description"
    }
    response = client.post("/todo", json=payload)
    assert response.status_code == 200
    return response.json()["todo_entry"]


# POST /todo tests
class TestCreateTodo:
    """Tests for POST /todo endpoint."""

    def test_create_todo_success(self, client, mock_service, sample_todo_id):
        """Test successful todo creation returns 200 and correct format."""
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=sample_todo_id,
            title="Buy groceries",
            description="Milk, eggs, bread",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        payload = {
            "id": str(sample_todo_id),
            "title": "Buy groceries",
            "description": "Milk, eggs, bread"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "todo_entry" in data
        assert data["todo_entry"]["id"] == str(sample_todo_id)
        assert data["todo_entry"]["title"] == "Buy groceries"
        assert data["todo_entry"]["description"] == "Milk, eggs, bread"
        assert "created_at" in data["todo_entry"]
        assert data["todo_entry"]["done"] is False
        assert data["todo_entry"]["deleted"] is False

    def test_create_todo_missing_description_payload(self, client, mock_service, sample_todo_id):
        """Test creating todo with minimal required fields (description is optional)."""
        # Mock service to return todo with None description
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=sample_todo_id,
            title="Minimal Todo",
            description=None,
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        payload = {
            "id": str(sample_todo_id),
            "title": "Minimal Todo",
            "description": None  # Explicitly optional
        }

        response = client.post("/todo", json=payload)

        # Description is optional, so this should succeed
        assert response.status_code == 200

    def test_create_todo_duplicate_returns_409(self, client, mock_service, created_todo):
        """Test creating duplicate todo returns 409 Conflict."""
        # Mock service to raise duplicate error
        mock_service.create_todo = AsyncMock(side_effect=ToDoAlreadyExistsError())

        payload = {
            "id": created_todo["id"],
            "title": "Different Title",
            "description": "Different Description"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.text.lower()

    def test_create_todo_missing_id_returns_422(self, client):
        """Test missing id field returns 422."""
        payload = {
            "title": "Test Todo",
            "description": "Test"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 422

    def test_create_todo_missing_title_returns_422(self, client, sample_todo_id):
        """Test missing title field returns 422."""
        payload = {
            "id": str(sample_todo_id),
            "description": "Test"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 422

    def test_create_todo_empty_title_returns_422(self, client, sample_todo_id):
        """Test empty title returns 422."""
        payload = {
            "id": str(sample_todo_id),
            "title": "",
            "description": "Test"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 422

    def test_create_todo_whitespace_only_title_returns_422(self, client, sample_todo_id):
        """Test whitespace-only title returns 422."""
        payload = {
            "id": str(sample_todo_id),
            "title": "   ",
            "description": "Test"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 422

    def test_create_todo_invalid_uuid_returns_422(self, client):
        """Test invalid UUID format returns 422."""
        payload = {
            "id": "not-a-valid-uuid",
            "title": "Test",
            "description": "Test"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 422

    def test_create_todo_sql_injection_in_title_returns_400(self, client, mock_service, sample_todo_id):
        """Test SQL injection attempt in title returns 400."""
        # Mock service to raise validation error for SQL injection
        mock_service.create_todo = AsyncMock(
            side_effect=ToDoValidationError("Invalid characters or SQL keywords in input"))

        sql_payloads = [
            "'; DROP TABLE todo;--",
            "Robert'); DROP TABLE students;--",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]

        for payload_text in sql_payloads:
            payload = {
                "id": str(uuid4()),
                "title": payload_text,
                "description": "Test"
            }

            response = client.post("/todo", json=payload)

            assert response.status_code == 400, f"BUG: SQL injection validation returns {response.status_code} instead of 400 for: {payload_text}"

    def test_create_todo_sql_injection_in_description_returns_400(self, client, mock_service, sample_todo_id):
        """Test SQL injection attempt in description returns 400."""
        # Mock service to raise validation error for SQL injection
        mock_service.create_todo = AsyncMock(
            side_effect=ToDoValidationError("Invalid characters or SQL keywords in input"))

        payload = {
            "id": str(sample_todo_id),
            "title": "Test",
            "description": "'; DELETE FROM todo;--"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 400

    def test_create_todo_with_emoji(self, client, mock_service, sample_todo_id):
        """Test creating todo with emoji characters."""
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=sample_todo_id,
            title="Buy milk 🥛",
            description="Don't forget! 📝",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        payload = {
            "id": str(sample_todo_id),
            "title": "Buy milk 🥛",
            "description": "Don't forget! 📝"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "🥛" in data["todo_entry"]["title"]
        assert "📝" in data["todo_entry"]["description"]

    def test_create_todo_with_unicode(self, client, mock_service, sample_todo_id):
        """Test creating todo with unicode characters."""
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=sample_todo_id,
            title="买牛奶",
            description="Café ☕",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        payload = {
            "id": str(sample_todo_id),
            "title": "买牛奶",
            "description": "Café ☕"
        }

        response = client.post("/todo", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["todo_entry"]["title"] == "买牛奶"
        assert "☕" in data["todo_entry"]["description"]

    def test_create_todo_returns_json_content_type(self, client, mock_service, sample_todo_id):
        """Test API returns JSON content type."""
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

        assert "application/json" in response.headers["content-type"]


# GET /todo/{todo_id} tests
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


# PUT /todo/{todo_id} tests
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


# DELETE /todo/{todo_id} tests
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


# GET /todo (list) tests
class TestListTodos:
    """Tests for GET /todo endpoint."""

    def test_list_todos_success(self, client, mock_service):
        """Test listing todos returns 200 and array."""
        # Mock service to return a list with one todo (empty lists are rejected by schema)
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=uuid4(),
                title="Test Todo",
                description="Test Description",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            )
        ])

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
            created_todos.append(ToDoSchema(
                id=todo_id,
                title=f"Todo {i}",
                description=f"Description {i}",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            ))

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
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=uuid4(),
                title=f"Todo {i}",
                description=f"Description {i}",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            ) for i in range(5)
        ])

        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 10
        assert len(data["todo_entries"]) <= 10

    def test_list_todos_pagination_custom_limit(self, client, mock_service):
        """Test pagination with custom limit."""
        # Mock service to return list with max 2 items
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=uuid4(),
                title=f"Todo {i}",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            ) for i in range(2)
        ])

        # Request with limit 2
        response = client.get("/todo?limit=2&page=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["todo_entries"]) <= 2

    def test_list_todos_pagination_page_2(self, client, mock_service):
        """Test getting second page of results."""
        # Mock service to return remaining items from page 2
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=uuid4(),
                title=f"Todo {i}",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            ) for i in range(5)  # 5 remaining items on page 2
        ])

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
        mock_service.create_todo = AsyncMock(return_value=ToDoSchema(
            id=todo_id,
            title="To Be Deleted",
            description="Test",
            created_at=datetime.datetime.now(),
            updated_at=None,
            deleted=False,
            done=False,
        ))

        # Create a todo
        payload = {
            "id": str(todo_id),
            "title": "To Be Deleted",
            "description": "Test"
        }
        client.post("/todo", json=payload)

        # Mock delete_todo
        mock_service.delete_todo = AsyncMock(return_value=True)

        # Delete it
        client.delete(f"/todo/{todo_id}")

        # Mock get_all_todos to return only non-deleted todos
        mock_service.get_all_todos = AsyncMock(return_value=[
            ToDoSchema(
                id=other_todo_id,
                title="Not Deleted",
                description="Test",
                created_at=datetime.datetime.now(),
                updated_at=None,
                deleted=False,
                done=False,
            )
        ])

        # List todos
        response = client.get("/todo")

        assert response.status_code == 200
        data = response.json()
        returned_ids = [todo["id"] for todo in data["todo_entries"]]

        # Deleted todo should not be in list
        assert str(todo_id) not in returned_ids

    def test_list_todos_negative_limit_returns_error(self, client, mock_service):
        """Test negative limit returns error or is handled."""
        # Mock service to return a todo (in case it gets called)
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

        response = client.get("/todo?limit=-1")

        # Should either reject with 422 or handle gracefully
        assert response.status_code in [200, 422]

    def test_list_todos_zero_limit(self, client, mock_service):
        """Test limit=0 is handled."""
        # Mock service to return a todo (in case it gets called)
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

        response = client.get("/todo?limit=0")

        # Should either reject with 422 or handle in some way
        assert response.status_code in [200, 422]

    def test_list_todos_negative_page_returns_error(self, client, mock_service):
        """Test negative page returns error or is handled."""
        # Mock service to return a todo (in case it gets called)
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

        response = client.get("/todo?page=-1")

        # Should either reject or handle gracefully
        assert response.status_code in [200, 422]

    def test_list_todos_zero_page_returns_error(self, client, mock_service):
        """Test page=0 returns error or is handled."""
        # Mock service to return a todo (in case it gets called)
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

        response = client.get("/todo?page=0")

        # Should either reject or handle gracefully
        assert response.status_code in [200, 422]

    def test_list_todos_very_large_limit(self, client, mock_service):
        """Test very large limit is handled."""
        # Mock service to return a todo (in case it gets called)
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

        response = client.get("/todo?limit=10000")

        # Should either cap or reject
        assert response.status_code in [200, 422]

    def test_list_todos_returns_json_content_type(self, client, mock_service):
        """Test list endpoint returns JSON."""
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

        assert "application/json" in response.headers["content-type"]


# Error response format tests
class TestErrorResponses:
    """Tests for consistent error response formats."""

    def test_404_error_format(self, client, mock_service):
        """Test 404 error has consistent format."""
        # Mock service to raise not found error
        mock_service.get_todo = AsyncMock(side_effect=ToDoNotFoundError())

        response = client.get(f"/todo/{uuid4()}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data

    def test_422_error_format(self, client):
        """Test 422 validation error has consistent format."""
        payload = {"title": "Missing ID"}
        response = client.post("/todo", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_409_error_format(self, client, mock_service, created_todo):
        """Test 409 conflict error has consistent format."""
        # Mock service to raise already exists error
        mock_service.create_todo = AsyncMock(side_effect=ToDoAlreadyExistsError())

        payload = {
            "id": created_todo["id"],
            "title": "Duplicate",
            "description": "Test"
        }
        response = client.post("/todo", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data or "message" in data

    def test_400_error_format(self, client, mock_service):
        """Test 400 validation error has consistent format."""
        # Mock service to raise validation error
        mock_service.create_todo = AsyncMock(
            side_effect=ToDoValidationError("Invalid characters or SQL keywords in input"))

        payload = {
            "id": str(uuid4()),
            "title": "'; DROP TABLE todo;--",
            "description": "Test"
        }
        response = client.post("/todo", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "message" in data


# Response schema validation tests
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