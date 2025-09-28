"""Logger to log information, warnings and errors"""

from logging import Formatter, INFO, Logger, StreamHandler, getLogger


class CustomLogger(Logger):
    """A custom logger to simplify logging"""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.logger = getLogger(name)
        self.logger.setLevel(INFO)

        # Create handler and set level
        handler = StreamHandler()
        handler.setLevel(INFO)

        # Create formatter
        formatter = Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def log_missing_parameter(self, parameter_name: str) -> None:
        """Log a missing parameter."""
        self.logger.error("Parameter %s is None.", parameter_name)

    def log_not_initialized(self, reference_name: str) -> None:
        """Log a reference to an uninitialized oject"""
        self.logger.error(" %s is not initialized.", reference_name)