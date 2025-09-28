from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger

def create_todo_service() -> ToDoService:
    """
    Create a ToDoService instance.
    """
    repository = ToDoRepository()
    logger = CustomLogger("ToDoService")
    return ToDoService(repository, logger)