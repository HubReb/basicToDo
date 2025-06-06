"""Logger to log information, warnings and errors"""

from logging import Logger


class CustomLogger(Logger):
    """A custom logger to simplify logging"""

    def __init__(self, name: str, level: int | str = 0) -> None:
        super().__init__(name, level)

    def log_missing_parameter(self, parameter_name: str) -> None:
        """Log a missing parameter."""
        self.error("Parameter %s is None.", parameter_name)

    def log_not_initialized(self, reference_name: str) -> None:
        """Log a reference to an uninitialized oject"""
        self.error(" %s is not initialized.", reference_name)
