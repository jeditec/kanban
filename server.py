#!/usr/bin/env python3
"""Kanban Board API Server with SQLite backend."""

import json
import sqlite3
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban.db')

# Master password for simple authentication (set via KANBAN_PASSWORD env var)
# Defaults to 'changeme' if not set — override with KANBAN_PASSWORD= to set a custom password
# or KANBAN_PASSWORD='' to disable authentication entirely
MASTER_PASSWORD = os.environ.get('KANBAN_PASSWORD', 'changeme')
PASSWORD_HEADER = 'X-Password'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority TEXT DEFAULT 'none',
            status TEXT DEFAULT 'todo',
            created_at INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def _check_password(handler):
    """Check if the request contains the correct master password header.
    Returns True if authentication passes or no password is set."""
    if not MASTER_PASSWORD:
        return True
    provided = handler.headers.get(PASSWORD_HEADER, '')
    return provided == MASTER_PASSWORD


class KanbanHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/tasks':
            if not _check_password(self):
                self._send_json(401, {'error': 'Unauthorized'})
                return
            self._serve_tasks()
        elif parsed.path == '/':
            self.serve_index()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len else b'{}'
        data = json.loads(body)

        if parsed.path == '/api/tasks':
            if not _check_password(self):
                self._send_json(401, {'error': 'Unauthorized'})
                return
            action = self.headers.get('X-Action', 'create')
            if action == 'create':
                self._create_task(data)
            elif action == 'update':
                self._update_task(data)
            else:
                self._create_task(data)
        else:
            self._send_error(404, 'Not found')

    def do_PUT(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len else b'{}'
        data = json.loads(body)

        if parsed.path == '/api/tasks':
            if not _check_password(self):
                self._send_json(401, {'error': 'Unauthorized'})
                return
            self._update_task(data)
        else:
            self._send_error(404, 'Not found')

    def do_DELETE(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len else b'{}'
        data = json.loads(body)

        if parsed.path == '/api/tasks':
            if not _check_password(self):
                self._send_json(401, {'error': 'Unauthorized'})
                return
            self._delete_task(data)
        else:
            self._send_error(404, 'Not found')

    # --- Handlers ---
    def _serve_tasks(self):
        conn = get_db()
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
        conn.close()
        tasks = [dict(r) for r in rows]
        self._send_json(200, tasks)

    def _create_task(self, data):
        task = {
            'id': data.get('id', self._gen_id()),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'priority': data.get('priority', 'none'),
            'status': data.get('status', 'todo'),
            'created_at': data.get('created_at', int(__import__('time').time()) * 1000),
        }
        if not task['title']:
            self._send_error(400, 'Title is required')
            return
        conn = get_db()
        conn.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
            (task['id'], task['title'], task['description'],
             task['priority'], task['status'], task['created_at'])
        )
        conn.commit()
        conn.close()
        self._send_json(201, task)

    def _update_task(self, data):
        task_id = data.get('id')
        if not task_id:
            self._send_error(400, 'Task ID is required')
            return
        conn = get_db()
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            conn.close()
            self._send_error(404, 'Task not found')
            return
        title = data.get('title', existing['title'])
        description = data.get('description', existing['description'])
        priority = data.get('priority', existing['priority'])
        status = data.get('status', existing['status'])
        conn.execute(
            "UPDATE tasks SET title=?, description=?, priority=?, status=? WHERE id=?",
            (title, description, priority, status, task_id)
        )
        conn.commit()
        updated = dict(conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())
        conn.close()
        self._send_json(200, updated)

    def _delete_task(self, data):
        task_id = data.get('id')
        if not task_id:
            self._send_error(400, 'Task ID is required')
            return
        conn = get_db()
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        self._send_json(200, {'deleted': task_id})

    # --- Helpers ---
    def serve_index(self):
        index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
        try:
            with open(index_path, 'r') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self._send_error(404, 'index.html not found')

    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, code, message):
        self._send_json(code, {'error': message})

    def _gen_id(self):
        import time, random
        return time.strftime('%Y%m%d%H%M%S', __import__('time').gmtime()) + \
               str(random.randint(100000, 999999)) + \
               str(__import__('time').time_ns() % 100000)

    # CORS preflight
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Action')
        self.end_headers()

    def log_message(self, format, *args):
        pass


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8040

    init_db()
    # Seed demo data if empty
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    if count == 0:
        import time
        now = int(time.time() * 1000)
        conn = get_db()
        for t in [
            ('demo-1', 'Welcome to your Kanban Board!',
             'Drag cards between columns to move them. Try it!', 'medium', 'todo', now),
            ('demo-2', 'Create your first task',
             'Click the "+ New Task" button to get started.', 'high', 'todo', now),
            ('demo-3', 'Customize priorities',
             'Set high, medium, or low priority for each task.', 'low', 'in-progress', now),
        ]:
            conn.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)", t)
        conn.commit()
        conn.close()

    server = ReusableHTTPServer(('0.0.0.0', port), KanbanHandler)
    print(f"📋 Kanban Board running on http://localhost:{port}")
    print(f"   Database: {DB_PATH}")
    print("   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
