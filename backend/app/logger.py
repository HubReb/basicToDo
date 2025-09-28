"""Logger to log information, warnings and errors"""

from logging import Logger, getLogger


class CustomLogger(Logger):
    """A custom logger to simplify logging"""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.logger = getLogger(name)

    def log_missing_parameter(self, parameter_name: str) -> None:
        """Log a missing parameter."""
        self.logger.error("Parameter %s is None.", parameter_name)

    def log_not_initialized(self, reference_name: str) -> None:
        """Log a reference to an uninitialized oject"""
        self.logger.error(" %s is not initialized.", reference_name)