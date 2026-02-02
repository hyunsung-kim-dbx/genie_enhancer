"""Base class for session and job persistence."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Job:
    """Represents a background job."""
    job_id: str
    type: str  # score, plan, apply, validate
    session_id: str
    status: str  # pending, running, completed, failed
    inputs: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None


class SessionStoreBase(ABC):
    """Abstract base for session and job storage."""

    @abstractmethod
    def setup_schema(self) -> None:
        """Set up database schema."""
        pass

    @abstractmethod
    def migrate_schema(self) -> None:
        """Run schema migrations."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connections."""
        pass

    @abstractmethod
    def create_session(self, user_id: str, name: Optional[str] = None) -> str:
        """Create a new session."""
        pass

    @abstractmethod
    def save_job(self, job: Job) -> None:
        """Save a new job."""
        pass

    @abstractmethod
    def update_job(self, job: Job) -> None:
        """Update an existing job."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        pass

    @abstractmethod
    def get_session_jobs(self, session_id: str) -> List[Job]:
        """Get all jobs for a session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        pass

    @abstractmethod
    def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        pass

    @abstractmethod
    def list_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List sessions for a user."""
        pass

    @abstractmethod
    def rename_session(self, session_id: str, name: str) -> None:
        """Rename a session."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        pass
