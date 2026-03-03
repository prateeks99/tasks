from textual.app import App, ComposeResult
from textual.widgets import Header, Footer


class TaskManagerApp(App):
    """A TUI task manager built with Textual."""

    TITLE = "Tasks"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
