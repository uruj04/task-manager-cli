"""Unit tests for the service, validators and CSV storage."""

import tempfile
import unittest
from pathlib import Path

from taskmanager.exceptions import TaskNotFoundError, ValidationError
from taskmanager.service import TaskService
from taskmanager.storage import CsvTaskStorage


class TaskServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "tasks.csv"
        self.service = TaskService(CsvTaskStorage(self.path))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_assigns_incrementing_ids(self) -> None:
        first = self.service.create("Write report")
        second = self.service.create("Send email")
        self.assertEqual((first.id, second.id), (1, 2))

    def test_create_rejects_empty_title(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create("   ")

    def test_create_rejects_bad_priority_and_date(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create("Task", priority="urgent")
        with self.assertRaises(ValidationError):
            self.service.create("Task", due_date="2026-13-45")

    def test_get_missing_task_raises(self) -> None:
        with self.assertRaises(TaskNotFoundError):
            self.service.get(99)

    def test_update_changes_fields(self) -> None:
        task = self.service.create("Old title")
        self.service.update(task.id, title="New title", status="done")
        updated = self.service.get(task.id)
        self.assertEqual((updated.title, updated.status), ("New title", "done"))

    def test_update_is_all_or_nothing(self) -> None:
        task = self.service.create("Keep me")
        with self.assertRaises(ValidationError):
            self.service.update(task.id, title="Changed", status="bogus")
        self.assertEqual(self.service.get(task.id).title, "Keep me")

    def test_delete_removes_task(self) -> None:
        task = self.service.create("Temporary")
        self.service.delete(task.id)
        self.assertEqual(self.service.list_all(), [])

    def test_new_id_follows_highest_existing_id(self) -> None:
        self.service.create("A")
        self.service.create("B")
        self.service.delete(1)
        self.assertEqual(self.service.create("C").id, 3)

    def test_search_is_case_insensitive_on_title_and_description(self) -> None:
        self.service.create("Buy Milk", description="from the store")
        self.service.create("Call mom")
        self.assertEqual(len(self.service.search("milk")), 1)
        self.assertEqual(len(self.service.search("STORE")), 1)
        self.assertEqual(self.service.search("xyz"), [])

    def test_search_rejects_blank_keyword(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.search("  ")

    def test_filter_by_status(self) -> None:
        task = self.service.create("Finish")
        self.service.create("Other")
        self.service.update(task.id, status="done")
        self.assertEqual([t.id for t in self.service.list_all("done")], [1])

    def test_data_persists_between_sessions(self) -> None:
        self.service.create("Persistent", description="with, comma and \"quotes\"")
        reloaded = TaskService(CsvTaskStorage(self.path))
        task = reloaded.get(1)
        self.assertEqual(task.title, "Persistent")
        self.assertEqual(task.description, 'with, comma and "quotes"')


class CsvStorageTests(unittest.TestCase):
    def test_missing_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(CsvTaskStorage(Path(tmp) / "none.csv").load_all(), [])

    def test_malformed_rows_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.csv"
            path.write_text(
                "id,title,description,priority,status,due_date,created_at\n"
                "1,Good task,,medium,pending,,\n"
                "not-a-number,Bad task,,medium,pending,,\n",
                encoding="utf-8",
            )
            tasks = CsvTaskStorage(path).load_all()
            self.assertEqual([t.title for t in tasks], ["Good task"])


if __name__ == "__main__":
    unittest.main()
