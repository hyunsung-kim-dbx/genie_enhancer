"""Session and job persistence using SQLite."""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from backend.services.session_store_base import SessionStoreBase, Job


class SQLiteSessionStore(SessionStoreBase):
    """Manages session and job state using SQLite."""

    def __init__(self, db_path: str = "storage/sessions.db", **kwargs):
        """Initialize SQLite session storage.

        Args:
            db_path: Path to SQLite database file
            **kwargs: Additional configuration options (ignored)
        """
        self.db_path = db_path
        print(f"Using SQLite local storage: {db_path}")
        self.sqlite_conn = None
        self._init_sqlite()
        self.setup_schema()
        self.migrate_schema()

    def _init_sqlite(self):
        """Initialize SQLite database for local storage."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self.sqlite_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row
        print(f"SQLite database initialized at: {os.path.abspath(self.db_path)}")

    def setup_schema(self) -> None:
        """Set up database schema."""
        if self.sqlite_conn:
            self._create_sqlite_tables()

    def _create_sqlite_tables(self):
        """Create SQLite tables if they don't exist."""
        cursor = self.sqlite_conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhancement_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                updated_at TIMESTAMP,
                workspace_config TEXT
            )
        """)

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhancement_jobs (
                job_id TEXT PRIMARY KEY,
                session_id TEXT,
                type TEXT,
                status TEXT,
                inputs TEXT,
                result TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                progress TEXT,
                FOREIGN KEY (session_id) REFERENCES enhancement_sessions(session_id)
            )
        """)

        self.sqlite_conn.commit()
        cursor.close()

    def migrate_schema(self) -> None:
        """Run schema migrations."""
        if self.sqlite_conn:
            self._migrate_sqlite_tables()

    def _migrate_sqlite_tables(self):
        """Migrate SQLite tables to add new columns if needed."""
        cursor = self.sqlite_conn.cursor()

        # Check if workspace_config column exists
        cursor.execute("PRAGMA table_info(enhancement_sessions)")
        columns = {col[1] for col in cursor.fetchall()}

        if 'workspace_config' not in columns:
            print("Migrating SQLite sessions table - adding workspace_config column")
            cursor.execute("ALTER TABLE enhancement_sessions ADD COLUMN workspace_config TEXT")
            self.sqlite_conn.commit()
            print("SQLite migration completed")

        cursor.close()

    def close(self) -> None:
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None

    def create_session(self, user_id: str, name: Optional[str] = None) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        if name is None:
            name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "INSERT INTO enhancement_sessions (session_id, user_id, created_at, name, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)",
            (session_id, user_id, name)
        )
        self.sqlite_conn.commit()
        cursor.close()
        return session_id

    def save_job(self, job: Job):
        """Save a new job record."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "INSERT INTO enhancement_jobs (job_id, session_id, type, status, inputs, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job.job_id, job.session_id, job.type, job.status, json.dumps(job.inputs), job.created_at)
        )
        self.sqlite_conn.commit()
        cursor.close()

    def update_job(self, job: Job):
        """Update an existing job."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            """UPDATE enhancement_jobs
               SET status = ?, result = ?, error = ?, completed_at = ?, progress = ?
               WHERE job_id = ?""",
            (
                job.status,
                json.dumps(job.result) if job.result else None,
                job.error,
                job.completed_at,
                json.dumps(job.progress) if job.progress else None,
                job.job_id
            )
        )
        self.sqlite_conn.commit()
        cursor.close()

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM enhancement_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return Job(
            job_id=row["job_id"],
            type=row["type"],
            session_id=row["session_id"],
            status=row["status"],
            inputs=json.loads(row["inputs"]),
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            progress=json.loads(row["progress"]) if row["progress"] else None
        )

    def get_session_jobs(self, session_id: str) -> List[Job]:
        """Get all jobs for a session."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM enhancement_jobs WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
        rows = cursor.fetchall()
        cursor.close()

        return [
            Job(
                job_id=row["job_id"],
                type=row["type"],
                session_id=row["session_id"],
                status=row["status"],
                inputs=json.loads(row["inputs"]),
                result=json.loads(row["result"]) if row["result"] else None,
                error=row["error"],
                created_at=datetime.fromisoformat(row["created_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                progress=json.loads(row["progress"]) if row["progress"] else None
            )
            for row in rows
        ]

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM enhancement_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "workspace_config": json.loads(row["workspace_config"]) if row["workspace_config"] else None
        }

    def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "UPDATE enhancement_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        self.sqlite_conn.commit()
        cursor.close()

    def list_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List sessions for a user."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "SELECT * FROM enhancement_sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        )
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "workspace_config": json.loads(row["workspace_config"]) if row["workspace_config"] else None
            }
            for row in rows
        ]

    def rename_session(self, session_id: str, name: str) -> None:
        """Rename a session."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "UPDATE enhancement_sessions SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (name, session_id)
        )
        self.sqlite_conn.commit()
        cursor.close()

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its jobs."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("DELETE FROM enhancement_jobs WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM enhancement_sessions WHERE session_id = ?", (session_id,))
        self.sqlite_conn.commit()
        cursor.close()
