"""Unit tests for repository"""
import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.database import get_db_session
from backend.app.data_access.repository import ToDoRepository
from backend.app.factory import create_todo_service
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import ToDoCreateEntry, TodoUpdateEntry


# Better test structure
@pytest.fixture
def sample_todo_data():
    yield {
        "id": uuid4(),
        "title": "Test Todo",
        "description": "This is a test for todo",
    }

@pytest.fixture
def sample_todo_data_entry(sample_todo_data):
    test_item = sample_todo_data
    todo = ToDoEntryData(
        id=test_item["id"], title=test_item["title"], created_at=datetime.datetime.now(), updated_at=None, done=False,
        deleted=False, description=test_item["description"]
    )
    yield todo

@pytest.fixture
def sample_todo_data_entry_for_service(sample_todo_data):
    test_item = sample_todo_data
    todo = ToDoCreateEntry(
        id=test_item["id"], title=test_item["title"], description=test_item["description"]
    )
    yield todo

@pytest.mark.asyncio
async def test_create_todo_success(sample_todo_data_entry_for_service):
    # Arrange
    todo_data = sample_todo_data_entry_for_service
    service = create_todo_service()

    # Act
    result = await service.create_todo(todo_data)

    # Assert
    assert result.id == todo_data.id
    assert result.title == todo_data.title
    assert result.description == todo_data.description


@pytest.fixture
def test_setup(sample_todo_data_entry):
    """Create test data."""
    test_item = sample_todo_data_entry
    repo = ToDoRepository(get_db_session)
    yield test_item, repo



@pytest.fixture
def test_setup_with_addition(test_setup):
    """Create test data."""
    test_item, repo = test_setup
    repo.create_to_do(test_item)
    yield test_item, repo


@pytest.fixture

def test_add(test_setup):
    """Test addition"""
    test_data = test_setup[0]
    repo = test_setup[1]
    assert repo.create_to_do(test_data) is None
    new_result = repo.get_to_do_entry(test_data.id)
    assert new_result.title == "Test Todo"
    repo.delete_to_do(test_data.id)


def test_create_todo_failure_duplicate(test_setup_with_addition):
    """Test addition of already existing data point."""
    test_data = test_setup_with_addition[0]
    repo = test_setup_with_addition[1]
    todo_entry = ToDoEntryData(id=test_data.id, title=test_data.title, description=test_data.description,
                               created_at=test_data.created_at, updated_at=None, done=False, deleted=False)
    with pytest.raises(IntegrityError) as _:
        repo.create_to_do(todo_entry)
    repo.delete_to_do(test_data.id)


def test_delete_success(test_setup_with_addition):
    """Test deletion."""
    test_data = test_setup_with_addition[0]
    repo = test_setup_with_addition[1]
    assert repo.delete_to_do(test_data.id) is True


def test_delete_fails_not_found(test_setup):
    """Test deletion."""
    test_data = test_setup[0]
    repo = test_setup[1]
    assert repo.delete_to_do(test_data.id) == False


def test_get_entry_success(test_setup_with_addition):
    """Test get an entry."""
    test_data = test_setup_with_addition[0]
    repo = test_setup_with_addition[1]
    assert test_data.id == repo.get_to_do_entry(test_data.id).id
    repo.delete_to_do(test_data.id)


def test_get_entry_fails_not_found(test_setup):
    """Test get a non-existent entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    assert repo.get_to_do_entry(test_data.id) is None


def test_update_entry_fails_not_found(test_setup):
    """Test update a non-existing entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    test_update_data = TodoUpdateEntry(id=test_data.id, title="new title", description=test_data.description,
                                       done=test_data.done)
    assert repo.update_to_do(test_data.id, test_update_data) is None

def test_update_entry_success(test_setup_with_addition):
    """Test update an entry."""
    test_data = test_setup_with_addition[0]
    repo = test_setup_with_addition[1]
    test_update_data = TodoUpdateEntry(id=test_data.id, title="new title", description=test_data.description,
                                       done=test_data.done)
    result = repo.update_to_do(test_data.id, test_update_data)
    assert result.title == "new title"
    new_result = repo.get_to_do_entry(test_data.id)
    assert new_result.title == "new title"
    repo.delete_to_do(test_data.id)