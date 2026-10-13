"""Browser-based demo for the Task Manager CLI business layer."""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from taskmanager.exceptions import TaskManagerError
from taskmanager.models import PRIORITIES, STATUSES, Task
from taskmanager.service import TaskService
from taskmanager.storage import CsvTaskStorage


st.set_page_config(page_title="Task Manager", page_icon="✅", layout="wide")


def service() -> TaskService:
    """Create one CSV-backed service for this visitor's browser session."""
    if "task_manager_service" not in st.session_state:
        directory = tempfile.TemporaryDirectory(prefix="task-manager-demo-")
        st.session_state.task_manager_tempdir = directory
        st.session_state.task_manager_service = TaskService(
            CsvTaskStorage(Path(directory.name) / "tasks.csv")
        )
    return st.session_state.task_manager_service


def task_rows(tasks: list[Task]) -> list[dict[str, str | int]]:
    return [asdict(task) for task in tasks]


def show_error(action) -> bool:
    """Run a service operation and display its validation errors."""
    try:
        action()
    except TaskManagerError as exc:
        st.error(str(exc))
        return False
    return True


tasks = service()

st.title("Task Manager")
st.caption("A browser demo built on the project's original CSV-backed CRUD service.")
st.info("Tasks are private to this browser session and are cleared when the demo session ends.")

tab_add, tab_tasks, tab_edit, tab_search = st.tabs(
    ["Add task", "View tasks", "Update or delete", "Search"]
)

with tab_add:
    st.subheader("Create a task")
    with st.form("create-task", clear_on_submit=True):
        title = st.text_input("Title", max_chars=80)
        description = st.text_area("Description", max_chars=300)
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", PRIORITIES, index=1)
        with col2:
            due_date = st.text_input("Due date (YYYY-MM-DD, optional)")
        create = st.form_submit_button("Add task", type="primary")
    if create:
        if show_error(lambda: tasks.create(title, description, priority, due_date)):
            st.success("Task created.")

with tab_tasks:
    st.subheader("All tasks")
    status_filter = st.selectbox("Filter by status", ("all", *STATUSES))
    visible_tasks = tasks.list_all(None if status_filter == "all" else status_filter)
    if visible_tasks:
        st.dataframe(task_rows(visible_tasks), use_container_width=True, hide_index=True)
    else:
        st.info("No tasks match this filter yet.")

with tab_edit:
    st.subheader("Update or delete a task")
    all_tasks = tasks.list_all()
    if not all_tasks:
        st.info("Add a task first.")
    else:
        task_by_label = {f"#{task.id} - {task.title}": task for task in all_tasks}
        selected_label = st.selectbox("Choose a task", tuple(task_by_label))
        selected = task_by_label[selected_label]

        with st.form("update-task"):
            updated_title = st.text_input("Title", value=selected.title, max_chars=80)
            updated_description = st.text_area(
                "Description", value=selected.description, max_chars=300
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                updated_priority = st.selectbox(
                    "Priority", PRIORITIES, index=PRIORITIES.index(selected.priority)
                )
            with col2:
                updated_status = st.selectbox(
                    "Status", STATUSES, index=STATUSES.index(selected.status)
                )
            with col3:
                updated_due_date = st.text_input("Due date", value=selected.due_date)
            update = st.form_submit_button("Save changes", type="primary")
        if update:
            if show_error(
                lambda: tasks.update(
                    selected.id,
                    title=updated_title,
                    description=updated_description,
                    priority=updated_priority,
                    status=updated_status,
                    due_date=updated_due_date,
                )
            ):
                st.success("Task updated.")
                st.rerun()

        st.divider()
        confirm_delete = st.checkbox(f"I want to delete task #{selected.id}")
        if st.button("Delete task", type="secondary", disabled=not confirm_delete):
            if show_error(lambda: tasks.delete(selected.id)):
                st.success("Task deleted.")
                st.rerun()

with tab_search:
    st.subheader("Search tasks")
    keyword = st.text_input("Search title or description")
    if keyword.strip():
        try:
            matches = tasks.search(keyword)
        except TaskManagerError as exc:
            st.error(str(exc))
        else:
            st.write(f"**{len(matches)} matching task(s)**")
            if matches:
                st.dataframe(task_rows(matches), use_container_width=True, hide_index=True)
