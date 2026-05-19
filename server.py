#!/usr/bin/env python3
"""Kanban Board API Server with SQLite backend."""

import json
import sqlite3
import os
import time
import pyminizip
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban.db')

# Master password for simple authentication (set via KANBAN_PASSWORD env var)
# Defaults to 'changeme' if not set — override with KANBAN_PASSWORD= to set a custom password
# or KANBAN_PASSWORD='' to disable authentication entirely
MASTER_PASSWORD = os.environ.get('KANBAN_PASSWORD', 'changeme')
PASSWORD_HEADER = 'X-Password'

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


def _derive_key(password: str) -> bytes:
    """Derive a 32-byte encryption key from a password using PBKDF2, then base64-encode for Fernet."""
    import base64
    salt = b'kanban_backup_salt_v1'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    raw_key = kdf.derive(password.encode('utf-8'))
    return base64.urlsafe_b64encode(raw_key)


def _encrypt_data(data, password: str) -> bytes:
    """Encrypt data using the password."""
    import base64
    raw_key = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'kanban_backup_salt_v1',
        iterations=100000,
    ).derive(password.encode('utf-8'))
    fernet = Fernet(base64.urlsafe_b64encode(raw_key))
    return fernet.encrypt(json.dumps(data).encode('utf-8'))


def _decrypt_data(encrypted_data: bytes, password: str):
    """Decrypt data using the password."""
    import base64
    raw_key = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'kanban_backup_salt_v1',
        iterations=100000,
    ).derive(password.encode('utf-8'))
    fernet = Fernet(base64.urlsafe_b64encode(raw_key))
    return json.loads(fernet.decrypt(encrypted_data).decode('utf-8'))


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

        if parsed.path == '/api/tasks':
            data = json.loads(body)
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
        elif parsed.path == '/api/export':
            data = json.loads(body)
            self._export_zip(data.get('password', ''))
        elif parsed.path == '/api/import':
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in content_type:
                self._handle_multipart_import(body, content_len)
            else:
                data = json.loads(body)
                password = data.get('password', '')
                encrypted_b64 = data.get('encrypted', '')
                if not encrypted_b64:
                    self._send_error(400, 'Missing encrypted data')
                    return
                self._import_zip(encrypted_b64, password)
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

    def _send_binary(self, code, data, content_type='application/zip', filename='backup.zip'):
        """Send a binary response."""
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def _export_zip(self, password):
        """Create a password-protected ZIP with all tasks."""
        if not password:
            self._send_error(400, 'Password is required')
            return

        conn = get_db()
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
        conn.close()
        tasks = [dict(r) for r in rows]

        # Write tasks JSON to a temp file
        json_path = f'/tmp/kanban-export-{int(time.time() * 1000)}.json'
        with open(json_path, 'w') as f:
            json.dump(tasks, f, indent=2)

        # Create password-protected ZIP using pyminizip
        zip_path = f'/tmp/kanban-backup-{time.strftime("%Y-%m-%d")}.zip'
        pyminizip.compress(json_path, None, zip_path, password, 5)

        # Read and send the ZIP
        with open(zip_path, 'rb') as f:
            zip_data = f.read()

        # Cleanup temp files
        os.unlink(json_path)
        os.unlink(zip_path)

        self._send_binary(200, zip_data, 'application/zip', f'kanban-backup-{time.strftime("%Y-%m-%d")}.zip')

    def _import_from_zip(self, zip_path, password):
        """Extract tasks from a password-protected ZIP and import them."""
        # Create a temp dir for extraction
        extract_dir = f'/tmp/kanban-import-{int(time.time() * 1000)}'
        os.makedirs(extract_dir, exist_ok=True)

        try:
            # Extract using pyminizip (handles AES-encrypted ZIPs)
            # pyminizip changes CWD during extraction, so save/restore it
            saved_cwd = os.getcwd()
            try:
                pyminizip.uncompress(zip_path, password, extract_dir, 0)
            except Exception:
                self._send_error(400, 'Incorrect password or invalid backup file')
                return
            finally:
                os.chdir(saved_cwd)

            # Find the JSON file
            json_files = [f for f in os.listdir(extract_dir) if f.endswith('.json')]
            if not json_files:
                self._send_error(400, 'Invalid backup format: no JSON file found')
                return

            json_path = os.path.join(extract_dir, json_files[0])
            with open(json_path, 'r') as f:
                tasks = json.load(f)

            if not isinstance(tasks, list):
                self._send_error(400, 'Invalid backup format')
                return

            count = 0
            conn = get_db()
            for t in tasks:
                if t.get('id') and t.get('title'):
                    conn.execute(
                        "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            t.get('id'),
                            t.get('title'),
                            t.get('description', t.get('desc', '')),
                            t.get('priority', 'none'),
                            t.get('status', 'todo'),
                            t.get('created_at', t.get('created', int(time.time() * 1000))),
                        )
                    )
                    count += 1
            conn.commit()
            conn.close()
            self._send_json(200, {'imported': count})
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)

    def _import_zip(self, encrypted_b64, password):
        """Import tasks from base64-encoded encrypted ZIP data."""
        import base64
        try:
            zip_data = base64.b64decode(encrypted_b64)
        except Exception:
            self._send_error(400, 'Invalid encrypted data format')
            return

        zip_path = f'/tmp/kanban-import-{int(time.time() * 1000)}.zip'
        with open(zip_path, 'wb') as f:
            f.write(zip_data)

        try:
            self._import_from_zip(zip_path, password)
        finally:
            os.unlink(zip_path)

    def _handle_multipart_import(self, body, content_len):
        """Handle multipart/form-data import (direct ZIP file upload)."""
        from email.parser import BytesParser
        from email.policy import HTTP

        content_type = self.headers.get('Content-Type', '')
        if 'boundary=' not in content_type:
            self._send_error(400, 'Missing boundary in Content-Type')
            return
        boundary = content_type.split('boundary=')[-1].strip()

        header = f'Content-Type: multipart/form-data; boundary={boundary}\r\n\r\n'.encode()
        msg = BytesParser(policy=HTTP).parsebytes(header + body)

        password = ''
        zip_data = None

        if isinstance(msg.get_payload(), list):
            for sub in msg.get_payload():
                name = sub.get_param('name', header='Content-Disposition')
                if name == 'password':
                    password = sub.get_payload(decode=True).decode('utf-8')
                elif sub.get_filename():
                    zip_data = sub.get_payload(decode=True)

        if not password:
            self._send_error(400, 'Missing password')
            return
        if not zip_data:
            self._send_error(400, 'Missing file')
            return

        zip_path = f'/tmp/kanban-import-{int(time.time() * 1000)}.zip'
        with open(zip_path, 'wb') as f:
            f.write(zip_data)

        try:
            self._import_from_zip(zip_path, password)
        finally:
            os.unlink(zip_path)

    # CORS preflight
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Action, X-Password')
        self.end_headers()

    def log_message(self, format, *args):
        pass


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    import sys
    port = int(os.environ.get('KANBAN_HTTP_PORT', '8060'))
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

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
