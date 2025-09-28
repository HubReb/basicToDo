from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.repository import ToDoRepository


def create_todo_service() -> ToDoService:
    """
    """
    repository = ToDoRepository()
    return ToDoService(repository)