"""Custom exceptions used across the application."""


class TaskManagerError(Exception):
    """Base class for all application errors."""


class ValidationError(TaskManagerError):
    """Raised when user input fails validation."""


class TaskNotFoundError(TaskManagerError):
    """Raised when a task with the given ID does not exist."""


class StorageError(TaskManagerError):
    """Raised when reading from or writing to storage fails."""
