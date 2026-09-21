"""Menu-driven command line interface."""

import argparse
import logging
from pathlib import Path
from typing import Callable

from . import __version__, validators
from .exceptions import TaskManagerError, ValidationError
from .models import PRIORITIES, STATUSES, Task
from .service import TaskService
from .storage import CsvTaskStorage

logger = logging.getLogger(__name__)

DEFAULT_DATA_FILE = Path("data") / "tasks.csv"
LOG_FILE = Path("logs") / "taskmanager.log"

MENU = """
=============================
      TASK MANAGER CLI
=============================
1. Add a task
2. View all tasks
3. View task details
4. Update a task
5. Delete a task
6. Search tasks
7. Exit
"""


# ---------- Input helpers ----------
def ask(label: str, validator: Callable[[str], str] | None = None, default: str | None = None) -> str:
    """Prompt until the input is valid. Blank input returns `default` when one is given."""
    while True:
        hint = f" [{default}]" if default else ""
        raw = input(f"{label}{hint}: ")
        if raw.strip() == "" and default is not None:
            return default
        try:
            return validator(raw) if validator else raw.strip()
        except ValidationError as exc:
            print(f"  ! {exc}")


def clearable(validator: Callable[[str], str]) -> Callable[[str], str]:
    """Wrap a validator so typing '-' clears the field."""
    return lambda value: "" if value.strip() == "-" else validator(value)


def ask_task_id() -> int:
    raw = input("Enter task ID: ").strip()
    if not raw.isdigit():
        raise ValidationError("Task ID must be a positive whole number.")
    return int(raw)


# ---------- Output helpers ----------
def print_table(tasks: list[Task]) -> None:
    if not tasks:
        print("\nNo tasks found.")
        return
    header = f"{'ID':<5}{'Title':<32}{'Priority':<10}{'Status':<13}{'Due date':<12}"
    print(f"\n{header}\n{'-' * len(header)}")
    for t in tasks:
        title = t.title if len(t.title) <= 30 else t.title[:27] + "..."
        print(f"{t.id:<5}{title:<32}{t.priority:<10}{t.status:<13}{t.due_date or '-':<12}")
    print(f"\n{len(tasks)} task(s).")


def print_details(task: Task) -> None:
    print(f"\nTask #{task.id}")
    print(f"  Title      : {task.title}")
    print(f"  Description: {task.description or '-'}")
    print(f"  Priority   : {task.priority}")
    print(f"  Status     : {task.status}")
    print(f"  Due date   : {task.due_date or '-'}")
    print(f"  Created at : {task.created_at or '-'}")


# ---------- Menu actions ----------
def add_task(service: TaskService) -> None:
    title = ask("Title", validators.validate_title)
    description = ask("Description (optional)", validators.validate_description, default="")
    priority = ask(f"Priority ({'/'.join(PRIORITIES)})", validators.validate_priority, default="medium")
    due_date = ask("Due date YYYY-MM-DD (optional)", validators.validate_due_date, default="")
    task = service.create(title, description, priority, due_date)
    print(f"\nOK - Task #{task.id} created.")


def view_all(service: TaskService) -> None:
    status = ask(
        f"Filter by status ({'/'.join(STATUSES)}, Enter for all)",
        validators.validate_status,
        default="",
    )
    print_table(service.list_all(status or None))


def view_details(service: TaskService) -> None:
    print_details(service.get(ask_task_id()))


def update_task(service: TaskService) -> None:
    task = service.get(ask_task_id())
    print_details(task)
    print("\nPress Enter to keep the current value.")
    changes = {
        "title": ask("Title", validators.validate_title, default=task.title),
        "description": ask("Description ('-' to clear)", clearable(validators.validate_description), default=task.description),
        "priority": ask(f"Priority ({'/'.join(PRIORITIES)})", validators.validate_priority, default=task.priority),
        "status": ask(f"Status ({'/'.join(STATUSES)})", validators.validate_status, default=task.status),
        "due_date": ask("Due date ('-' to clear)", clearable(validators.validate_due_date), default=task.due_date),
    }
    service.update(task.id, **changes)
    print(f"\nOK - Task #{task.id} updated.")


def delete_task(service: TaskService) -> None:
    task = service.get(ask_task_id())
    print_details(task)
    if input("\nDelete this task? (y/N): ").strip().lower() == "y":
        service.delete(task.id)
        print(f"OK - Task #{task.id} deleted.")
    else:
        print("Cancelled.")


def search_tasks(service: TaskService) -> None:
    keyword = input("Search keyword: ")
    print_table(service.search(keyword))


ACTIONS: dict[str, Callable[[TaskService], None]] = {
    "1": add_task,
    "2": view_all,
    "3": view_details,
    "4": update_task,
    "5": delete_task,
    "6": search_tasks,
}


# ---------- Entry point ----------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menu-driven task manager (CSV storage).")
    parser.add_argument("--file", type=Path, default=DEFAULT_DATA_FILE, help="CSV file to store tasks (default: data/tasks.csv)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def setup_logging() -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    except OSError:
        logging.disable(logging.CRITICAL)  # run without logs rather than crash


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()

    try:
        service = TaskService(CsvTaskStorage(args.file))
    except TaskManagerError as exc:
        print(f"Startup error: {exc}")
        return 1

    try:
        while True:
            print(MENU)
            choice = input("Choose an option (1-7): ").strip()
            if choice == "7":
                print("Goodbye!")
                return 0
            action = ACTIONS.get(choice)
            if action is None:
                print("Invalid choice. Please enter a number from 1 to 7.")
                continue
            try:
                action(service)
            except TaskManagerError as exc:
                logger.warning("%s", exc)
                print(f"\n! {exc}")
            except Exception:  # last-resort guard so the app never crashes mid-session
                logger.exception("Unexpected error")
                print("\n! Something went wrong. Details were written to the log file.")
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        return 0
