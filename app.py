import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static
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


class TaskManagerApp(App):
    """A TUI task manager built with Textual."""

    TITLE = "Tasks"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        data_path = Path(__file__).parent / "tasks.json"
        self.store = TaskStore(data_path)

    def compose(self) -> ComposeResult:
        yield Header()
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
        table.clear()
        for task in self.store.sorted_tasks():
            icon, style = PRIORITY_STYLES.get(task.priority, ("!! ", "yellow"))
            done_marker = "[x]" if task.done else "[ ]"
            if task.done:
                row = [
                    Text(icon, style="dim"),
                    Text(done_marker, style="dim"),
                    Text(task.title, style="dim strike"),
                    Text(", ".join(task.tags), style="dim"),
                    Text(task.created_at[:10], style="dim"),
                ]
            else:
                row = [
                    Text(icon, style=style),
                    Text(done_marker),
                    Text(task.title, style="bold" if task.priority == "high" else ""),
                    Text(", ".join(task.tags), style="italic"),
                    Text(task.created_at[:10]),
                ]
            table.add_row(*row, key=task.id)
        self._update_status()

    def _update_status(self) -> None:
        total = len(self.store.tasks)
        done = sum(1 for t in self.store.tasks if t.done)
        pending = total - done
        status = self.query_one("#status-bar", Static)
        status.update(f" {pending} pending / {done} done / {total} total")


if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
