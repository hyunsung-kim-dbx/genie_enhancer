"""File storage service for uploaded files."""

import os
import shutil
from pathlib import Path
from typing import BinaryIO


class LocalFileStorageService:
    """Local filesystem storage for uploaded files."""

    def __init__(self, base_path: str = "storage/uploads"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, session_id: str, filename: str, file: BinaryIO) -> str:
        """
        Save an uploaded file.

        Args:
            session_id: Session identifier
            filename: Original filename
            file: File object to save

        Returns:
            Relative path to saved file
        """
        # Create session directory
        session_dir = self.base_path / session_id
        session_dir.mkdir(exist_ok=True)

        # Save file
        file_path = session_dir / filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file, f)

        # Return relative path
        return str(file_path.relative_to(self.base_path.parent))

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get absolute path for a stored file.

        Args:
            relative_path: Relative path from save_file

        Returns:
            Absolute path to file
        """
        return self.base_path.parent / relative_path

    def list_session_files(self, session_id: str) -> list:
        """
        List all files for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of filenames
        """
        session_dir = self.base_path / session_id
        if not session_dir.exists():
            return []

        return [f.name for f in session_dir.iterdir() if f.is_file()]

    def delete_session_files(self, session_id: str) -> None:
        """
        Delete all files for a session.

        Args:
            session_id: Session identifier
        """
        session_dir = self.base_path / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
