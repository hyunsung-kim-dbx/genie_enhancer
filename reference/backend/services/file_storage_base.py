"""Abstract base class for file storage implementations.

This module provides the base interface for file storage backends,
enabling support for local filesystem, cloud storage (S3, Azure Blob),
and Unity Catalog Volumes.
"""

from abc import ABC, abstractmethod
from typing import List
from fastapi import UploadFile


class FileStorageBase(ABC):
    """Abstract base class for file storage implementations.

    Concrete implementations must provide:
    - Storage initialization
    - File upload handling
    - Session directory management

    Implementations may override:
    - Session ID validation logic
    - Session cleanup behavior
    """

    @abstractmethod
    def __init__(self, volume_path: str = None, **kwargs):
        """Initialize storage backend with optional configuration.

        Args:
            volume_path: Optional path/location for storage
            **kwargs: Backend-specific configuration options
        """
        pass

    @abstractmethod
    async def save_uploads(
        self,
        files: List[UploadFile],
        session_id: str
    ) -> List[str]:
        """Save uploaded files to session-specific storage.

        Args:
            files: List of uploaded files from FastAPI
            session_id: Session identifier for organizing files

        Returns:
            List of storage paths where files were saved

        Raises:
            ValueError: If session_id is invalid
            IOError: If file save operation fails
        """
        pass

    @abstractmethod
    def get_session_dir(self, session_id: str) -> str:
        """Get storage path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Storage path for the session (may not exist yet)
        """
        pass

    @abstractmethod
    def create_session_dir(self, session_id: str) -> str:
        """Create and return session storage directory.

        Args:
            session_id: Session identifier

        Returns:
            Created storage path for the session

        Raises:
            IOError: If directory creation fails
        """
        pass

    def validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format.

        Default implementation: non-empty string check.
        Override for stricter validation (e.g., UUID format).

        Args:
            session_id: Session identifier to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(session_id and isinstance(session_id, str))

    def cleanup_session(self, session_id: str) -> None:
        """Clean up session storage.

        Default implementation: no-op.
        Override to implement cleanup logic (delete files, free resources).

        Args:
            session_id: Session identifier to clean up
        """
        pass
