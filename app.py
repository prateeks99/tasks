import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer


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


class TaskManagerApp(App):
    """A TUI task manager built with Textual."""

    TITLE = "Tasks"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        data_path = Path(__file__).parent / "tasks.json"
        self.store = TaskStore(data_path)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
