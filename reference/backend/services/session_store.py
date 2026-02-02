"""Session and job persistence using SQLite."""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from backend.services.session_store_base import SessionStoreBase, Job


class SQLiteSessionStore(SessionStoreBase):
    """Manages session and job state using SQLite."""

    def __init__(self, db_path: str = "storage/sessions.db", **kwargs):
        """Initialize SQLite session storage.

        Args:
            db_path: Path to SQLite database file
            **kwargs: Additional configuration options (ignored)
        """
        # Always use SQLite for persistence
        self.db_path = db_path
        print(f"Using SQLite local storage: {db_path}")
        self.conn = None
        self.sqlite_conn = None
        self._sessions = {}
        self._jobs = {}
        self._init_sqlite()
        self.setup_schema()
        self.migrate_schema()

    def _init_sqlite(self):
        """Initialize SQLite database for local storage."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self.sqlite_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
        print(f"SQLite database initialized at: {os.path.abspath(self.db_path)}")

    def setup_schema(self) -> None:
        """Set up database schema (hook method implementation)."""
        if self.sqlite_conn:
            self._create_sqlite_tables()

    def _create_sqlite_tables(self):
        """Create SQLite tables if they don't exist."""
        cursor = self.sqlite_conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                updated_at TIMESTAMP
            )
        """)

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_jobs (
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
                FOREIGN KEY (session_id) REFERENCES genie_sessions(session_id)
            )
        """)

        self.sqlite_conn.commit()
        cursor.close()

    def migrate_schema(self) -> None:
        """Run schema migrations (hook method implementation)."""
        if self.sqlite_conn:
            self._migrate_sqlite_tables()

    def _migrate_sqlite_tables(self):
        """Migrate SQLite tables to add new columns if needed."""
        cursor = self.sqlite_conn.cursor()

        # Check if name and updated_at columns exist
        cursor.execute("PRAGMA table_info(genie_sessions)")
        columns = {col[1] for col in cursor.fetchall()}

        if 'name' not in columns or 'updated_at' not in columns:
            print("Migrating SQLite sessions table - adding name and updated_at columns")

            if 'name' not in columns:
                cursor.execute("ALTER TABLE genie_sessions ADD COLUMN name TEXT")

            if 'updated_at' not in columns:
                cursor.execute("ALTER TABLE genie_sessions ADD COLUMN updated_at TIMESTAMP")

            # Backfill name and updated_at
            cursor.execute("""
                UPDATE genie_sessions
                SET name = strftime('%Y-%m-%d %H:%M:%S', created_at),
                    updated_at = created_at
                WHERE name IS NULL OR updated_at IS NULL
            """)

            self.sqlite_conn.commit()
            print("SQLite migration completed")

        cursor.close()

    def close(self) -> None:
        """Close database connections (hook method implementation)."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None

    def create_session(self, user_id: str, name: Optional[str] = None) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        if name is None:
            name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "INSERT INTO genie_sessions (session_id, user_id, created_at, name, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)",
                (session_id, user_id, name)
            )
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            self._sessions[session_id] = {
                "user_id": user_id,
                "name": name,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        return session_id

    def save_job(self, job: Job):
        """Save a new job record."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """INSERT INTO genie_jobs
                   (job_id, session_id, type, status, inputs, progress, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (job.job_id, job.session_id, job.type, job.status,
                 json.dumps(job.inputs),
                 json.dumps(job.progress) if job.progress else None)
            )
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM genie_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return Job(
                job_id=row[0],
                session_id=row[1],
                type=row[2],
                status=row[3],
                inputs=json.loads(row[4]) if row[4] else {},
                result=json.loads(row[5]) if row[5] else None,
                error=row[6],
                created_at=row[7],
                completed_at=row[8],
                progress=json.loads(row[9]) if row[9] else None
            )
        else:
            # In-memory storage fallback
            return self._jobs.get(job_id)

    def update_job(self, job: Job):
        """Update job status, result, error, and progress."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """UPDATE genie_jobs
                   SET status = ?, result = ?, error = ?, completed_at = ?, progress = ?
                   WHERE job_id = ?""",
                (job.status,
                 json.dumps(job.result) if job.result else None,
                 job.error,
                 job.completed_at,
                 json.dumps(job.progress) if job.progress else None,
                 job.job_id)
            )
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            self._jobs[job.job_id] = job

    def get_jobs_for_session(self, session_id: str) -> List[Job]:
        """Get all jobs for a session."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "SELECT * FROM genie_jobs WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            rows = cursor.fetchall()
            cursor.close()

            return [
                Job(
                    job_id=row[0],
                    session_id=row[1],
                    type=row[2],
                    status=row[3],
                    inputs=json.loads(row[4]) if row[4] else {},
                    result=json.loads(row[5]) if row[5] else None,
                    error=row[6],
                    created_at=row[7],
                    completed_at=row[8],
                    progress=json.loads(row[9]) if row[9] else None
                )
                for row in rows
            ]
        else:
            # In-memory storage fallback
            jobs = [job for job in self._jobs.values() if job.session_id == session_id]
            return sorted(jobs, key=lambda j: j.created_at or datetime.min)

    def list_sessions(self, user_id: str = None, limit: int = 50, offset: int = 0) -> Tuple[List[dict], int]:
        """List sessions with job counts, ordered by updated_at DESC."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()

            # Build query with optional user_id filter
            where_clause = "WHERE s.user_id = ?" if user_id else ""
            params = [user_id, limit, offset] if user_id else [limit, offset]

            query = f"""
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                {where_clause}
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                ORDER BY s.updated_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM genie_sessions s {where_clause}"
            count_params = [user_id] if user_id else []
            cursor.execute(count_query, tuple(count_params))
            total = cursor.fetchone()[0]

            cursor.close()

            sessions = [
                {
                    "session_id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "job_count": row[5]
                }
                for row in rows
            ]

            return sessions, total
        else:
            # In-memory storage fallback
            sessions = list(self._sessions.values())
            if user_id:
                sessions = [s for s in sessions if s.get("user_id") == user_id]

            # Add job counts
            for session in sessions:
                session_id = session.get("session_id")
                if session_id:
                    session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == session_id)
                else:
                    # Find session_id by matching session object
                    for sid, sdata in self._sessions.items():
                        if sdata == session:
                            session["session_id"] = sid
                            session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == sid)
                            break

            # Sort by updated_at DESC
            sessions = sorted(sessions, key=lambda s: s.get("updated_at", datetime.min), reverse=True)
            total = len(sessions)
            return sessions[offset:offset + limit], total

    def update_session_name(self, session_id: str, name: str):
        """Update session name and updated_at timestamp."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (name, session_id)
            )
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            if session_id in self._sessions:
                self._sessions[session_id]["name"] = name
                self._sessions[session_id]["updated_at"] = datetime.now()

    def update_session_activity(self, session_id: str):
        """Update session updated_at timestamp to mark activity."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            if session_id in self._sessions:
                self._sessions[session_id]["updated_at"] = datetime.now()

    def get_session_with_stats(self, session_id: str) -> Optional[dict]:
        """Get session with job count and metadata."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                """,
                (session_id,)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "session_id": row[0],
                "user_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "job_count": row[5]
            }
        else:
            # In-memory storage fallback
            if session_id not in self._sessions:
                return None
            session = self._sessions[session_id].copy()
            session["session_id"] = session_id
            session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == session_id)
            return session

    def delete_session(self, session_id: str):
        """Delete session and all associated jobs (hard delete with cascade)."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            # Delete jobs first (foreign key relationship)
            cursor.execute("DELETE FROM genie_jobs WHERE session_id = ?", (session_id,))
            # Delete session
            cursor.execute("DELETE FROM genie_sessions WHERE session_id = ?", (session_id,))
            self.sqlite_conn.commit()
            cursor.close()
        else:
            # In-memory storage fallback
            # Delete all jobs for this session
            self._jobs = {jid: job for jid, job in self._jobs.items() if job.session_id != session_id}
            # Delete session
            if session_id in self._sessions:
                del self._sessions[session_id]
