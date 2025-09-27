"""Unit tests for repository"""
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.repository import ToDoRepository
from backend.app.data_access.database import get_db
from backend.app.models.todo import ToDoEntryData
from backend.app.business_logic.todo_service import ToDoService
from backend.app.schemas.todo import ToDoCreateEntry

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
        id=test_item["id"], title=test_item["title"], created_at=None, updated_at=None, done=False, deleted=False, description=test_item["description"]
    )
    yield todo

@pytest.fixture
def sample_todo_data_entry_for_service(sample_todo_data):
    test_item = sample_todo_data
    todo = ToDoCreateEntry(
        id=test_item["id"], item=test_item["title"], created_at=None
    )
    yield todo

@pytest.mark.asyncio
async def test_create_todo_success(sample_todo_data_entry_for_service):
    # Arrange
    todo_data = sample_todo_data_entry_for_service
    service = ToDoService()

    # Act
    todo_schema = ToDoCreateEntry.model_validate(todo_data)
    result = await service.create_todo(todo_schema)

    # Assert
    assert result.todo_entry.id == todo_schema.id
    assert result.todo_entry.title == todo_schema.item


@pytest.fixture
def test_setup(sample_todo_data_entry):
    """Create test data."""
    test_item = sample_todo_data_entry
    repo = ToDoRepository(get_db())
    assert repo.add_to_do(test_item) is None
    yield test_item, repo
    repo.delete_to_do(test_item.id)


@pytest.fixture
def test_setup_for_deletion():
    """Create test data."""
    test_item = {"id": uuid4(), "item": "This is test data."}
    repo = ToDoRepository(get_db())
    todo = ToDoEntryData(
        id=test_item["id"], title=test_item["item"], created_at=None, updated_at=None, done=False, deleted=False,
        description=test_item["item"]
    )
    repo.add_to_do(todo)
    yield test_item, repo


@pytest.fixture
def test_setup_without_addition():
    """Create test data."""
    test_item = {"id": uuid4(), "item": "This is test data."}
    repo = ToDoRepository(get_db())
    yield test_item, repo
    repo.delete_to_do(test_item["id"])


@pytest.fixture
def test_setup_without_addition_and_deletion():
    """Create test data."""
    test_item = {"id": uuid4(), "item": "This is test data."}
    repo = ToDoRepository(get_db())
    yield test_item, repo


def test_add(test_setup_without_addition):
    """Test addition"""
    test_data = test_setup_without_addition[0]
    repo = test_setup_without_addition[1]
    todo = ToDoEntryData(
        id=test_data["id"], title=test_data["item"], created_at=None, updated_at=None, done=False, deleted=False,
        description=test_data["item"]
    )
    assert repo.add_to_do(todo) is None


def test_create_todo_failure_duplicate(test_setup):
    """Test addition of already existing data point."""
    test_data = test_setup[0]
    repo = test_setup[1]
    with pytest.raises(IntegrityError) as _:
        repo.add_to_do(test_data)


def test_delete_success(test_setup_for_deletion):
    """Test deletion."""
    test_data = test_setup_for_deletion[0]
    repo = test_setup_for_deletion[1]
    assert repo.delete_to_do(test_data["id"]) is None


def test_delete_fails_not_found(test_setup_for_deletion):
    """Test deletion."""
    test_data = test_setup_for_deletion[0]
    repo = test_setup_for_deletion[1]
    assert repo.delete_to_do(test_data["id"]) is None
    with pytest.raises(ValueError):
        repo.delete_to_do(test_data["id"])


def test_get_entry_success(test_setup):
    """Test get an entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    assert test_data.id == repo.get_to_do_entry(test_data.id).id


def test_get_entry_fails_not_found(test_setup_without_addition_and_deletion):
    """Test get a non-existent entry."""
    test_data = test_setup_without_addition_and_deletion[0]
    repo = test_setup_without_addition_and_deletion[1]
    with pytest.raises(ValueError) as _:
        repo.get_to_do_entry(test_data["id"])


def test_update_entry_fails_not_found(test_setup_without_addition_and_deletion):
    """Test update a non-existing entry."""
    test_data = test_setup_without_addition_and_deletion[0]
    repo = test_setup_without_addition_and_deletion[1]
    with pytest.raises(ValueError) as _:
        repo.update_to_do(test_data["id"], test_data)


def test_update_entry_success(test_setup):
    """Test update an entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    repo.update_to_do(test_data.id, {"title": "new title"})