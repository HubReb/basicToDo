"""Unit tests for repository"""

from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.todo import ToDoRepository
from backend.app.database import get_db
from backend.app.models import ToDo


@pytest.fixture
def test_setup():
    """Create test data."""
    test_item = {"id": uuid4(), "item": "This is test data."}
    repo = ToDoRepository(get_db())
    todo = ToDo(
        test_item["id"], test_item["item"], test_item["item"], None, None, False, False
    )
    assert repo.add_to_do(todo) is None
    yield test_item, repo
    repo.delete_to_do(test_item["id"])


@pytest.fixture
def test_setup_for_deletion():
    """Create test data."""
    test_item = {"id": uuid4(), "item": "This is test data."}
    repo = ToDoRepository(get_db())
    todo = ToDo(
        test_item["id"], test_item["item"], test_item["item"], None, None, False, False
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
    todo = ToDo(
        test_data["id"], test_data["item"], test_data["item"], None, None, False, False
    )
    assert repo.add_to_do(todo) is None


def test_existing_data_added_fails(test_setup):
    """Test addition of already existing data point."""
    test_data = test_setup[0]
    repo = test_setup[1]
    todo = ToDo(
        test_data["id"], test_data["item"], test_data["item"], None, None, False, False
    )
    with pytest.raises(IntegrityError) as exp:
        repo.add_to_do(todo)


def test_delete(test_setup_for_deletion):
    """Test deletion."""
    test_data = test_setup_for_deletion[0]
    repo = test_setup_for_deletion[1]
    assert repo.delete_to_do(test_data["id"]) is None


def test_delete_fails(test_setup_for_deletion):
    """Test deletion."""
    test_data = test_setup_for_deletion[0]
    repo = test_setup_for_deletion[1]
    assert repo.delete_to_do(test_data["id"]) is None
    with pytest.raises(ValueError):
        repo.delete_to_do(test_data["id"])


def test_get_entry(test_setup):
    """Test get an entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    todo = ToDo(
        test_data["id"], test_data["item"], test_data["item"], None, None, False, False
    )
    assert todo.id == repo.get_to_do_entry(test_data["id"]).id


def test_get_entry_fails(test_setup_without_addition_and_deletion):
    """Test get a non-existent entry."""
    test_data = test_setup_without_addition_and_deletion[0]
    repo = test_setup_without_addition_and_deletion[1]
    with pytest.raises(ValueError) as exp:
        repo.get_to_do_entry(test_data["id"])


def test_update_entry_fails(test_setup_without_addition_and_deletion):
    """Test update a non-existing entry."""
    test_data = test_setup_without_addition_and_deletion[0]
    repo = test_setup_without_addition_and_deletion[1]
    with pytest.raises(ValueError) as exp:
        repo.update_to_do(test_data["id"], test_data)


def test_update_entry(test_setup):
    """Test update an entry."""
    test_data = test_setup[0]
    repo = test_setup[1]
    repo.update_to_do(test_data["id"], {"title": "new title"})