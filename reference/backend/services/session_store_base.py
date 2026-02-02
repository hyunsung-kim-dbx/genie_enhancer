"""Abstract base class for session and job persistence.

This module provides the base interface for session storage backends,
enabling support for SQLite, PostgreSQL, in-memory storage, and other
database systems.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
from pydantic import BaseModel


class Job(BaseModel):
    """Job model for tracking async operations."""
    job_id: str
    session_id: str
    type: str  # parse, generate, validate, deploy
    status: str  # pending, running, completed, failed
    inputs: dict
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[dict] = None  # Progress tracking data


class SessionStoreBase(ABC):
    """Abstract base class for session and job persistence.

    Concrete implementations must provide:
    - Session CRUD operations
    - Job CRUD operations
    - Transaction and consistency guarantees

    Implementations may override:
    - Schema setup and migration logic
    - Health check behavior
    - Connection management
    """

    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize storage backend with backend-specific configuration.

        Args:
            **kwargs: Backend-specific configuration options
                     (e.g., db_path, connection_string, pool_size)
        """
        pass

    # ========== Session CRUD Operations ==========

    @abstractmethod
    def create_session(
        self,
        user_id: str,
        name: Optional[str] = None
    ) -> str:
        """Create new session.

        Args:
            user_id: User identifier
            name: Optional session name

        Returns:
            Generated session_id (UUID string)

        Raises:
            ValueError: If user_id is invalid
        """
        pass

    @abstractmethod
    def get_session_with_stats(self, session_id: str) -> Optional[dict]:
        """Get session details with job count.

        Args:
            session_id: Session identifier

        Returns:
            Dict with keys: id, user_id, name, created_at, updated_at, job_count
            None if session not found

        Example:
            {
                "id": "uuid-123",
                "user_id": "user-456",
                "name": "My Session",
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T11:45:00",
                "job_count": 5
            }
        """
        pass

    @abstractmethod
    def list_sessions(
        self,
        user_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        """List sessions with pagination.

        Args:
            user_id: Optional filter by user_id
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            Tuple of (sessions list, total count)
            Sessions ordered by updated_at DESC

        Example:
            ([
                {"id": "uuid-1", "user_id": "user-1", "name": "Session 1", ...},
                {"id": "uuid-2", "user_id": "user-2", "name": "Session 2", ...}
            ], 42)
        """
        pass

    @abstractmethod
    def update_session_name(self, session_id: str, name: str) -> None:
        """Update session name and updated_at timestamp.

        Args:
            session_id: Session identifier
            name: New session name

        Raises:
            ValueError: If session not found
        """
        pass

    @abstractmethod
    def update_session_activity(self, session_id: str) -> None:
        """Update session updated_at timestamp.

        Used to track session activity without changing data.

        Args:
            session_id: Session identifier

        Raises:
            ValueError: If session not found
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Delete session and all associated jobs (cascade).

        Args:
            session_id: Session identifier

        Note:
            Should cascade delete all jobs for the session
        """
        pass

    # ========== Job CRUD Operations ==========

    @abstractmethod
    def save_job(self, job: Job) -> None:
        """Save new job record.

        Args:
            job: Job object to persist

        Raises:
            ValueError: If job_id already exists
        """
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        pass

    @abstractmethod
    def update_job(self, job: Job) -> None:
        """Update job status, result, error, progress.

        Args:
            job: Job object with updated fields

        Raises:
            ValueError: If job not found
        """
        pass

    @abstractmethod
    def get_jobs_for_session(self, session_id: str) -> List[Job]:
        """Get all jobs for session, ordered by created_at.

        Args:
            session_id: Session identifier

        Returns:
            List of Job objects, oldest first
        """
        pass

    # ========== Hook Methods (Optional Overrides) ==========

    def setup_schema(self) -> None:
        """Set up database schema.

        Default: no-op.
        Override for SQL databases to create tables.

        Called during __init__ to ensure schema exists.
        """
        pass

    def migrate_schema(self) -> None:
        """Run schema migrations.

        Default: no-op.
        Override to apply schema changes for version upgrades.

        Called after setup_schema during __init__.
        """
        pass

    def health_check(self) -> bool:
        """Check storage backend health.

        Default: return True.
        Override to perform actual health checks (database ping, connection test).

        Returns:
            True if healthy, False otherwise
        """
        return True

    def close(self) -> None:
        """Close connections and cleanup.

        Default: no-op.
        Override to close database connections, release resources.

        Called during application shutdown.
        """
        pass
