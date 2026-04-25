"""Builder interface."""
from abc import ABC, abstractmethod

from backend.app.data_access.database import ToDoORM
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme


class BuilderInterface(ABC):
    """Common interface for all builders."""

    @abstractmethod
    async def build_from_create_schema(self, payload: ToDoCreateScheme) -> ToDoORM:
        """Builds validated ToDoORM objects from input schemas."""
        pass