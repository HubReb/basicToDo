from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.database import safe_session_scope
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger


def create_todo_service() -> ToDoService:
    """
    Create a ToDoService instance.
    """
    logger = CustomLogger("ToDoService")
    repository = ToDoRepository(safe_session_scope, logger)
    return ToDoService(repository=repository, logger=logger)