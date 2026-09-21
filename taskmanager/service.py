"""Business logic: CRUD and search, independent of the user interface."""

import logging
from datetime import datetime

from . import validators
from .exceptions import TaskNotFoundError, ValidationError
from .models import Task
from .storage import CsvTaskStorage

logger = logging.getLogger(__name__)

_FIELD_VALIDATORS = {
    "title": validators.validate_title,
    "description": validators.validate_description,
    "priority": validators.validate_priority,
    "status": validators.validate_status,
    "due_date": validators.validate_due_date,
}


class TaskService:
    """Coordinates validation, in-memory state and persistence."""

    def __init__(self, storage: CsvTaskStorage) -> None:
        self._storage = storage
        self._tasks: list[Task] = storage.load_all()

    # ---- Create ----
    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: str = "",
    ) -> Task:
        task = Task(
            id=self._next_id(),
            title=validators.validate_title(title),
            description=validators.validate_description(description),
            priority=validators.validate_priority(priority),
            status="pending",
            due_date=validators.validate_due_date(due_date),
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._tasks.append(task)
        self._storage.save_all(self._tasks)
        logger.info("Created task #%d", task.id)
        return task

    # ---- Read ----
    def list_all(self, status: str | None = None) -> list[Task]:
        tasks = sorted(self._tasks, key=lambda t: t.id)
        if status:
            status = validators.validate_status(status)
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def get(self, task_id: int) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f"No task found with ID {task_id}.")

    # ---- Update ----
    def update(self, task_id: int, **changes: str) -> Task:
        task = self.get(task_id)
        # Validate everything first so a bad value never leaves a half-updated task.
        cleaned: dict[str, str] = {}
        for field, value in changes.items():
            if field not in _FIELD_VALIDATORS:
                raise ValidationError(f"Unknown field: {field}")
            cleaned[field] = _FIELD_VALIDATORS[field](value)
        for field, value in cleaned.items():
            setattr(task, field, value)
        self._storage.save_all(self._tasks)
        logger.info("Updated task #%d (%s)", task.id, ", ".join(cleaned))
        return task

    # ---- Delete ----
    def delete(self, task_id: int) -> Task:
        task = self.get(task_id)
        self._tasks.remove(task)
        self._storage.save_all(self._tasks)
        logger.info("Deleted task #%d", task_id)
        return task

    # ---- Search ----
    def search(self, keyword: str) -> list[Task]:
        keyword = validators.validate_keyword(keyword).lower()
        return [
            t
            for t in sorted(self._tasks, key=lambda t: t.id)
            if keyword in t.title.lower() or keyword in t.description.lower()
        ]

    def _next_id(self) -> int:
        return max((t.id for t in self._tasks), default=0) + 1
