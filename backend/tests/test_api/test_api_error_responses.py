""" Error response format tests"""

from unittest.mock import AsyncMock
from uuid import uuid4

from backend.app.business_logic.exceptions import (ToDoAlreadyExistsError, ToDoNotFoundError, ToDoValidationError)
from backend.tests.test_api.test_setup_for_api_endpoins import (client, created_todo, mock_service)


class TestErrorResponses:
    """Tests for consistent error response formats."""

    def test_404_error_format(self, client, mock_service):
        """Test 404 error has consistent format."""
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