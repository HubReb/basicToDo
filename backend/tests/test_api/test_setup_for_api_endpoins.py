import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.api.api import app
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema


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