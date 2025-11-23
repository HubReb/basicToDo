"""Comprehensive API endpoint tests for ToDo application: POST /todo tests."""
import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoValidationError,
)
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service)


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

        assert response.status_code == 200

    def test_create_todo_duplicate_returns_409(self, client, mock_service, created_todo):
        """Test creating duplicate todo returns 409 Conflict."""
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