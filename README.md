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

## Architecture

```
kanban/
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Multi-container orchestration
├── .dockerignore       # Files excluded from build context
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

- Python 3.8+ **or** Docker + Docker Compose
- A modern web browser

### Running with Docker (Recommended)

The easiest way to run Kanban is with Docker Compose:

```bash
cd kanban
docker compose up -d
```

Then open **http://localhost:8060** in your browser.

**Configure port and password** via a `.env` file in the `kanban/` directory:

```bash
# .env
echo "KANBAN_HTTP_PORT=3000" > .env
echo "KANBAN_PASSWORD=mysecurepassword" >> .env
docker compose up -d
```

Or set them inline:

```bash
KANBAN_HTTP_PORT=3000 KANBAN_PASSWORD=mysecurepassword docker compose up -d
```

**Manage the container:**

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f

# Rebuild after changes
docker compose up -d --build
```

### Running with pre-built image (no local build)

To use the **pre-built image from GitHub Container Registry** instead of building locally:

```bash
# Set your configuration
echo "KANBAN_HTTP_PORT=3000" > .env
echo "KANBAN_PASSWORD=mysecurepassword" >> .env

# Use the pre-built image (it ignores the build step via override)
cat > docker-compose.override.yml << 'EOF'
services:
  kanban:
    build:
      disable: true
    image: ghcr.io/jeditec/kanban:latest
EOF

docker compose up -d
```

Or simply run directly:

```bash
docker run -d --name kanban \
  -p 3000:8060 \
  -e KANBAN_PASSWORD=mysecurepassword \
  -e KANBAN_HTTP_PORT=8060 \
  -v kanban-data:/app \
  ghcr.io/jeditec/kanban:latest
```

### Running with Docker (single container)

```bash
# Use the pre-built image from GitHub Container Registry
# (change ports as needed)
docker run -d --name kanban -p 8060:8060 -e KANBAN_PASSWORD=changeme -e KANBAN_HTTP_PORT=8060 -v kanban-data:/app ghcr.io/jeditec/kanban:latest

# Or build locally
docker build -t kanban .
docker run -d --name kanban -p 8060:8060 -e KANBAN_PASSWORD=changeme -e KANBAN_HTTP_PORT=8060 -v kanban-data:/app kanban
```

### Running the Server (native)

```bash
cd kanban
python3 server.py
# Or specify a custom port:
python3 server.py 3000
```

The default port is **8060** (configurable via `KANBAN_HTTP_PORT`).

Then open **http://localhost:8060** in your browser.

### Docker Architecture

```
kanban/
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Multi-container orchestration
├── .dockerignore       # Files excluded from build context
├── index.html          # Frontend
├── server.py           # Backend API server
├── kanban.db           # Database: SQLite (persisted via volume)
├── README.md           # This file
└── package.json        # (optional)
```

The `docker-compose.yml` uses a named volume (`kanban-data`) to persist the SQLite database across container restarts and recreations.

### Database

The SQLite database (`kanban.db`) is automatically created on first run. Tasks persist across server restarts.

To back up the database:
```bash
cp kanban.db kanban-backup.db
```

## Customization

### Changing the Port

```bash
# Via command line argument
python3 server.py 3000

# Via environment variable
KANBAN_HTTP_PORT=3000 python3 server.py
```

Default port is **8060**.

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

## Security

### Master Password

A master password is required to access the board. The default password is **`changeme`**. Set `KANBAN_PASSWORD` to change it.

```bash
# Native (custom password)
KANBAN_PASSWORD=mysecret python3 server.py

# Docker
docker run -d -p 8040:8040 -e KANBAN_PASSWORD=mysecret -v kanban-data:/app ghcr.io/jeditec/kanban:latest

# Docker Compose (env file)
echo "KANBAN_PASSWORD=mysecret" > .env
docker compose up -d

# docker-compose.yml with inline env
# services:
#   kanban:
#     environment:
#       - KANBAN_PASSWORD=mysecret
```

To **disable authentication entirely**, set `KANBAN_PASSWORD=''` (empty string).

## Technologies

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Backend:** Python 3
- **Database:** SQLite
- **Containerization:** Docker & Docker Compose
- **No dependencies required** — runs on pure Python standard library

## License

MIT
