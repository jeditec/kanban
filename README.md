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
- **Master Password** — Simple password protection via `KANBAN_PASSWORD` env var

## Prerequisites

- Docker + Docker Compose
- A modern web browser

## Getting Started

### Quick Start — Everything Inline

Run with a custom port and password directly in the command:

```bash
KANBAN_HTTP_PORT=3000 KANBAN_PASSWORD=mysecurepassword docker compose up -d
```

Open **http://localhost:3000** in your browser.

### Using a `.env` File

For persistent configuration, create a `.env` file:

```bash
echo "KANBAN_HTTP_PORT=3000" > .env
echo "KANBAN_PASSWORD=mysecurepassword" >> .env
docker compose up -d
```

Then just run:

```bash
docker compose up -d
```

### Using the Pre-built Image (No Local Build)

By default, `docker compose up` builds the image locally. To use the pre-built image from GitHub Container Registry instead:

```bash
cat > docker-compose.override.yml << 'EOF'
services:
  kanban:
    build:
      disable: true
    image: ghcr.io/jeditec/kanban:latest
EOF

KANBAN_HTTP_PORT=3000 KANBAN_PASSWORD=mysecurepassword docker compose up -d
```

### Manage the Container

```bash
# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f

# Rebuild locally after code changes
docker compose up -d --build
```

### Architecture

```
kanban/
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Orchestration with port, password, volume
├── .dockerignore       # Files excluded from build context
├── index.html          # Frontend: HTML + CSS + vanilla JavaScript
├── server.py           # Backend: Python HTTP server with SQLite
├── .env                # Your port & password configuration
├── README.md           # This file
└── package.json        # (optional)
```

The `docker-compose.yml` uses:
- **`KANBAN_HTTP_PORT`** — Maps host port to container port (default `8060`)
- **`KANBAN_PASSWORD`** — Master password for access (default `changeme`)
- **`kanban-data`** volume — Persists the SQLite database across restarts

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | Get all tasks |
| `POST` | `/api/tasks` | Create a new task |
| `PUT` | `/api/tasks` | Update an existing task |
| `DELETE` | `/api/tasks` | Delete a task |

### Task Object

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

## Security

### Master Password

A master password is required to access the board. Default is **`changeme`**.

| Scenario | Configuration |
|----------|---------------|
| Custom password | `KANBAN_PASSWORD=mysecret` |
| Disable auth | `KANBAN_PASSWORD=''` |

### Changing the Port

| Scenario | Configuration |
|----------|---------------|
| Custom port | `KANBAN_HTTP_PORT=3000` |
| Default port | `8060` |

## License

MIT
