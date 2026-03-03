import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Select, Static
from rich.text import Text


@dataclass
class Task:
    """A single task item."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    done: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "tags": self.tags,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


class TaskStore:
    """Reads and writes tasks to a JSON file."""

    def __init__(self, path: Path):
        self.path = path
        self.tasks: list[Task] = []
        self.load()

    def load(self) -> None:
        if self.path.exists() and self.path.stat().st_size > 0:
            data = json.loads(self.path.read_text())
            self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        else:
            self.tasks = []
            self.save()

    def save(self) -> None:
        data = {"tasks": [t.to_dict() for t in self.tasks]}
        self.path.write_text(json.dumps(data, indent=2) + "\n")

    def add(self, task: Task) -> None:
        self.tasks.append(task)
        self.save()

    def delete(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save()

    def toggle(self, task_id: str) -> None:
        for t in self.tasks:
            if t.id == task_id:
                t.done = not t.done
                break
        self.save()

    def sorted_tasks(self) -> list[Task]:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            self.tasks,
            key=lambda t: (t.done, priority_order.get(t.priority, 1), t.created_at),
        )


PRIORITY_STYLES = {
    "high": ("!!!", "bold red"),
    "medium": ("!! ", "yellow"),
    "low": ("!  ", "dim green"),
}


class AddTaskModal(ModalScreen[Task | None]):
    """Modal dialog for creating a new task."""

    BINDINGS = [("escape", "cancel", "Cancel")]
    AUTO_FOCUS = "#task-title"

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Label("Add New Task", id="dialog-title")
            yield Label("Title")
            yield Input(placeholder="What needs to be done?", id="task-title")
            yield Label("Priority")
            yield Select(
                [("High", "high"), ("Medium", "medium"), ("Low", "low")],
                value="medium",
                id="task-priority",
            )
            yield Label("Tags (comma-separated)")
            yield Input(placeholder="work, personal, urgent...", id="task-tags")
            with Horizontal(id="dialog-buttons"):
                yield Button("Add Task", variant="success", id="btn-add")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add":
            title = self.query_one("#task-title", Input).value.strip()
            if not title:
                self.notify("Title cannot be empty", severity="error")
                return
            priority = self.query_one("#task-priority", Select).value
            tags_raw = self.query_one("#task-tags", Input).value.strip()
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
            self.dismiss(Task(title=title, priority=str(priority), tags=tags))
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmModal(ModalScreen[bool]):
    """Simple yes/no confirmation dialog."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self.message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes", variant="error", id="btn-yes")
                yield Button("No", variant="default", id="btn-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


class TaskManagerApp(App):
    """A TUI task manager built with Textual."""

    TITLE = "Tasks"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("a", "add_task", "Add"),
        ("d", "delete_task", "Delete"),
        ("space", "toggle_task", "Toggle Done"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        data_path = Path(__file__).parent / "tasks.json"
        self.store = TaskStore(data_path)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("No tasks yet. Press 'a' to add one.", id="empty-message")
        yield DataTable(id="task-table", cursor_type="row", zebra_stripes=True)
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#task-table", DataTable)
        table.add_column("Prio", key="priority", width=5)
        table.add_column("Done", key="done", width=6)
        table.add_column("Title", key="title")
        table.add_column("Tags", key="tags", width=20)
        table.add_column("Created", key="created", width=12)
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#task-table", DataTable)
        empty = self.query_one("#empty-message", Static)
        table.clear()
        has_tasks = len(self.store.tasks) > 0
        table.display = has_tasks
        empty.display = not has_tasks
        for task in self.store.sorted_tasks():
            icon, style = PRIORITY_STYLES.get(task.priority, ("!! ", "yellow"))
            done_marker = "[x]" if task.done else "[ ]"
            created = datetime.fromisoformat(task.created_at).strftime("%b %d")
            if task.done:
                row = [
                    Text(icon, style="dim"),
                    Text(done_marker, style="dim"),
                    Text(task.title, style="dim strike"),
                    Text(", ".join(task.tags), style="dim"),
                    Text(created, style="dim"),
                ]
            else:
                row = [
                    Text(icon, style=style),
                    Text(done_marker),
                    Text(task.title, style="bold" if task.priority == "high" else ""),
                    Text(", ".join(task.tags), style="italic"),
                    Text(created),
                ]
            table.add_row(*row, key=task.id)
        self._update_status()

    def _update_status(self) -> None:
        total = len(self.store.tasks)
        done = sum(1 for t in self.store.tasks if t.done)
        pending = total - done
        status = self.query_one("#status-bar", Static)
        status.update(f" {pending} pending / {done} done / {total} total")

    def action_add_task(self) -> None:
        def on_result(task: Task | None) -> None:
            if task is not None:
                self.store.add(task)
                self._refresh_table()
                self.notify(f"Added: {task.title}")
        self.push_screen(AddTaskModal(), on_result)

    def action_toggle_task(self) -> None:
        table = self.query_one("#task-table", DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        task_id = str(row_key.value)
        self.store.toggle(task_id)
        task = next((t for t in self.store.tasks if t.id == task_id), None)
        if task:
            status = "done" if task.done else "pending"
            self.notify(f"Marked '{task.title}' as {status}")
        self._refresh_table()

    def action_delete_task(self) -> None:
        table = self.query_one("#task-table", DataTable)
        if table.row_count == 0:
            self.notify("No tasks to delete", severity="warning")
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        task_id = str(row_key.value)
        task_title = next((t.title for t in self.store.tasks if t.id == task_id), "this task")

        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self.store.delete(task_id)
                self._refresh_table()
                self.notify(f"Deleted: {task_title}")
        self.push_screen(ConfirmModal(f"Delete '{task_title}'?"), on_confirm)


if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
