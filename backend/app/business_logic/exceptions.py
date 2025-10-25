"""Business-layer exceptions for the ToDo domain."""


class ToDoError(Exception):
    """Base exception for ToDo domain errors."""


class ToDoAlreadyExistsError(ToDoError):
    """Raised when trying to create a ToDo that already exists."""


class ToDoNotFoundError(ToDoError):
    """Raised when a ToDo item is not found."""


class ToDoValidationError(ToDoError):
    """Raised when data validation fails inside the service."""


class ToDoRepositoryError(ToDoError):
    """Raised for unexpected repository or DB errors."""