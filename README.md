# 📋 Kanban Board

A modern, feature-rich Kanban board web application with drag-and-drop task management, SQLite persistence, and a beautiful dark-themed UI.

## Features

- **Drag & Drop** — Move tasks between columns by dragging cards
- **4 Columns** — To Do → In Progress → Review → Done
- **Task Management** — Create, edit, delete, and duplicate tasks
- **Priority Levels** — Low, Medium, High with color-coded left borders
- **Task Details** — Title, description, and priority for each card
- **Statistics Bar** — Real-time count of total, active, and done tasks
- **Persistent Storage** — All data stored in SQLite database
- **Import / Export** — Backup and restore tasks as JSON files
- **Keyboard Shortcuts** — `Enter` to save, `Escape` to close modals
- **Confirmation Modals** — Styled delete confirmation instead of browser popups
- **Responsive Design** — Works on mobile with horizontal scrolling

## Architecture

```
kanban/
├── index.html          # Frontend: HTML + CSS + vanilla JavaScript
├── server.py           # Backend: Python HTTP server with SQLite
├── kanban.db           # Database: SQLite storage (auto-created)
├── README.md           # This file
└── package.json        # (optional) for future enhancements
```

### Frontend (`index.html`)

- **Vanilla JavaScript** — No frameworks or libraries
- **CSS Variables** — Easy theming with CSS custom properties
- **Drag & Drop API** — Native HTML5 drag and drop for moving cards
- **REST API Client** — Communicates with the backend via `fetch()`
- **Modal System** — Custom confirmation and form modals

### Backend (`server.py`)

- **Python 3 HTTP Server** — Built-in `http.server` module
- **SQLite Database** — Schema with `tasks` table (id, title, description, priority, status, created_at)
- **RESTful API** — JSON endpoints for CRUD operations
- **CORS Support** — Allows cross-origin requests
- **Auto-Seeding** — Demo tasks on first run

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | Get all active tasks |
| `POST` | `/api/tasks` | Create a new task |
| `PUT` | `/api/tasks` | Update an existing task |
| `DELETE` | `/api/tasks` | Permanently delete a task |
| `/` | — | Serve the frontend |

#### Task Object

```json
{
  "id": "unique-id",
  "title": "Task title",
  "description": "Optional description",
  "priority": "low | medium | high | none",
  "status": "todo | in-progress | review | done",
  "created_at": 1779171990584
}
```

### Database Schema

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'none',
    status TEXT DEFAULT 'todo',
    created_at INTEGER NOT NULL
);
```

## Getting Started

### Prerequisites

- Python 3.8+
- A modern web browser

### Running the Server

```bash
cd kanban
python3 server.py
# Or specify a custom port:
python3 server.py 8040
```

Then open **http://localhost:8040** in your browser.

### Database

The SQLite database (`kanban.db`) is automatically created on first run. Tasks persist across server restarts.

To back up the database:
```bash
cp kanban.db kanban-backup.db
```

## Customization

### Changing the Port

```bash
python3 server.py 3000
```

### Theming

Edit CSS variables in `index.html` under `:root`:

```css
:root {
    --bg: #1a1a2e;          /* Background */
    --accent: #e94560;      /* Accent color */
    --text: #e0e0e0;        /* Text color */
    --card-bg: #0f3460;     /* Card background */
}
```

### Adding New Priorities

1. Add a CSS rule for the new priority border color in `createCardEl()`
2. Add a badge style class
3. Add the option to the `<select>` dropdown

## Technologies

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Backend:** Python 3
- **Database:** SQLite
- **No dependencies required** — runs on pure Python standard library

## License

MIT
