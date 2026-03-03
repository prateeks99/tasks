# Tasks

A lightweight terminal-based task manager built with Python and Textual.

## Setup

```bash
git clone git@github.com:prateeks99/tasks.git
cd tasks
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
source .venv/bin/activate
python app.py
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `a` | Add a new task |
| `Space` | Toggle done/undone |
| `d` | Delete task (with confirmation) |
| `Up/Down` | Navigate between tasks |
| `Escape` | Close dialogs |
| `q` | Quit |

## Features

- Add tasks with title, priority (high/medium/low), and tags
- Color-coded priorities — red for high, yellow for medium, green for low
- Mark tasks as done — completed tasks appear dimmed with strikethrough
- Delete tasks with confirmation dialog
- Tasks sorted by: incomplete first, then priority, then newest
- Data stored in a simple `tasks.json` file

## Tech Stack

- Python
- [Textual](https://github.com/Textualize/textual) (TUI framework)
- JSON file storage
