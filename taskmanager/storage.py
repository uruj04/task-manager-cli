"""CSV persistence layer."""

import csv
import logging
import os
import tempfile
from dataclasses import asdict, fields
from pathlib import Path

from .exceptions import StorageError
from .models import Task

logger = logging.getLogger(__name__)


class CsvTaskStorage:
    """Loads and saves tasks to a CSV file."""

    FIELDNAMES = [f.name for f in fields(Task)]

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_all(self) -> list[Task]:
        """Return all tasks. A missing file means no tasks yet; bad rows are skipped."""
        if not self.path.exists():
            return []

        tasks: list[Task] = []
        try:
            with self.path.open("r", newline="", encoding="utf-8") as file:
                for line_no, row in enumerate(csv.DictReader(file), start=2):
                    try:
                        tasks.append(self._row_to_task(row))
                    except (KeyError, ValueError, TypeError) as exc:
                        logger.warning("Skipping malformed row %d: %s", line_no, exc)
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            raise StorageError(f"Could not read '{self.path}': {exc}") from exc

        logger.info("Loaded %d task(s) from %s", len(tasks), self.path)
        return tasks

    def save_all(self, tasks: list[Task]) -> None:
        """Write all tasks atomically so a crash cannot corrupt the file."""
        tmp_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                for task in tasks:
                    writer.writerow(asdict(task))
            os.replace(tmp_path, self.path)
        except OSError as exc:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise StorageError(f"Could not write '{self.path}': {exc}") from exc

    @staticmethod
    def _row_to_task(row: dict[str, str | None]) -> Task:
        def text(key: str, default: str = "") -> str:
            return (row.get(key) or default).strip()

        return Task(
            id=int(row["id"]),
            title=text("title"),
            description=text("description"),
            priority=text("priority", "medium"),
            status=text("status", "pending"),
            due_date=text("due_date"),
            created_at=text("created_at"),
        )
