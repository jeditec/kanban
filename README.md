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

### Quick Start — Inline

Run everything in one command:

```bash
KANBAN_HTTP_PORT=3000 KANBAN_PASSWORD=mysecurepassword docker compose up -d
```

Open **http://localhost:3000** in your browser.

### Full Docker Compose Configuration

Create a `docker-compose.yml` for full control:

```yaml
services:
  kanban:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: kanban
    ports:
      - "${KANBAN_HTTP_PORT:-8060}:${KANBAN_HTTP_PORT:-8060}"
    environment:
      - KANBAN_PASSWORD=${KANBAN_PASSWORD:-changeme}
      - KANBAN_HTTP_PORT=${KANBAN_HTTP_PORT:-8060}
    volumes:
      - ./data:/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:${KANBAN_HTTP_PORT:-8060}/')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Then run:

```bash
docker compose up -d
```

## Manage the Container

```bash
# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f

# Remove container
docker compose down
```

### Architecture

```
kanban/
├── docker-compose.yml  # Full orchestration: port, password, bind mount, healthcheck
├── README.md           # This file
└── package.json        # (optional)
```

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

Set it:
- Inline: `KANBAN_PASSWORD=mysecret docker compose up -d`
- `docker-compose.yml`: `environment: [KANBAN_PASSWORD=mysecret]`

To disable auth, set `KANBAN_PASSWORD=''`.

### Changing the Port

Set it:
- Inline: `KANBAN_HTTP_PORT=3000 docker compose up -d`
- `docker-compose.yml` ports mapping: `"3000:8060"`

Default port is **8060**.

## License

MIT
