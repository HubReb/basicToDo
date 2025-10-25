"""Unit tests for ToDoService."""
from uuid import uuid4

import pytest

from backend.app.business_logic.exceptions import ToDoRepositoryError
from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.repository import ToDoRepositoryInterface
from backend.app.logger import CustomLogger
from backend.app.schemas.todo import ToDoCreateEntry


class FakeRepo(ToDoRepositoryInterface):
    def __init__(self):
        self.data = {}

    def create_to_do(self, entry):
        if entry.id in self.data:
            raise Exception("IntegrityError")
        self.data[entry.id] = entry

    def get_to_do_entry(self, id): return self.data.get(id)

    def update_to_do(self, id, payload): return None

    def delete_to_do(self, id): return id in self.data

    def hard_delete_to_do(self, id): return id in self.data

    def get_all_to_do_entries(self, limit, page): return list(self.data.values())


@pytest.mark.asyncio
async def test_create_todo_success():
    repo = FakeRepo()
    service = ToDoService(repo, CustomLogger("test"))
    entry = ToDoCreateEntry(id=uuid4(), title="Test", description="Desc")
    result = await service.create_todo(entry)
    assert result.title == "Test"


@pytest.mark.asyncio
async def test_create_todo_duplicate():
    repo = FakeRepo()
    service = ToDoService(repo, CustomLogger("test"))
    entry = ToDoCreateEntry(id=uuid4(), title="Test", description="Desc")
    await service.create_todo(entry)
    with pytest.raises(ToDoRepositoryError):
        await service.create_todo(entry)