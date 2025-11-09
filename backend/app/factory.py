from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.data_access.database import safe_session_scope
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger


def create_todo_service() -> ToDoService:
    """
    Create a ToDoService instance with all dependencies.
    """
    logger = CustomLogger("ToDoService")
    repository = ToDoRepository(safe_session_scope, logger)

    # Create validators using ValidatorFactory
    input_sanitizer = ValidatorFactory.create_input_sanitizer(logger)
    uuid_validator = ValidatorFactory.create_uuid_validator(logger)
    field_validator = ValidatorFactory.create_field_validator(logger)

    # Create builder
    builder = ToDoEntryBuilder(uuid_validator, field_validator)

    return ToDoService(
        repository=repository,
        logger=logger,
        input_sanitizer=input_sanitizer,
        uuid_validator=uuid_validator,
        field_validator=field_validator,
        builder=builder,
    )