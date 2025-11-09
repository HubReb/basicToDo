"""Builder interface."""
from abc import ABC, abstractmethod

from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


class BuilderInterface(ABC):
    """Common interface for all builders."""

    @abstractmethod
    async def build_from_create_schema(self, payload: ToDoCreateScheme) -> ToDoEntryData:
        """Builds validated ToDoEntryData objects from input schemas."""
        pass