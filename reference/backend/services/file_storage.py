"""File storage service using local file system."""

import os
from typing import List
from fastapi import UploadFile
from backend.services.file_storage_base import FileStorageBase


class LocalFileStorageService(FileStorageBase):
    """Manages file uploads using local file system."""

    def __init__(self, volume_path: str = None, **kwargs):
        """
        Initialize file storage service with local file system.

        Args:
            volume_path: Ignored - always uses local storage
        """
        # Always use local storage
        self.volume_path = os.path.join(os.getcwd(), "storage", "uploads")
        os.makedirs(self.volume_path, exist_ok=True)
        print(f"Using local file storage: {self.volume_path}")

    async def save_uploads(self, files: List[UploadFile], session_id: str) -> List[str]:
        """
        Save uploaded files to session-specific directory.

        Args:
            files: List of uploaded files
            session_id: Session identifier

        Returns:
            List of saved file paths
        """
        session_dir = f"{self.volume_path}/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

        file_paths = []
        for file in files:
            path = f"{session_dir}/{file.filename}"
            with open(path, 'wb') as f:
                content = await file.read()
                f.write(content)
            file_paths.append(path)

        return file_paths

    def get_session_dir(self, session_id: str) -> str:
        """Get the directory path for a session."""
        return f"{self.volume_path}/{session_id}"

    def create_session_dir(self, session_id: str) -> str:
        """Create and return session directory."""
        session_dir = self.get_session_dir(session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
