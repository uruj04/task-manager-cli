"""Data model for a task."""

from dataclasses import dataclass

PRIORITIES = ("low", "medium", "high")
STATUSES = ("pending", "in-progress", "done")


@dataclass
class Task:
    """A single task record."""

    id: int
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    due_date: str = ""  # ISO format YYYY-MM-DD, or empty
    created_at: str = ""  # ISO timestamp
