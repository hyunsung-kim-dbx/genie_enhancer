"""Job manager for background task orchestration."""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Any

from .session_store_base import SessionStoreBase, Job


class JobManager:
    """Manages background job execution with process pool."""

    def __init__(self, session_store: SessionStoreBase, max_workers: int = 4):
        """
        Initialize job manager.

        Args:
            session_store: Store for persisting job state
            max_workers: Maximum concurrent jobs
        """
        self.store = session_store
        # Use ThreadPoolExecutor instead of ProcessPoolExecutor to allow sharing session_store
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Set global session store reference for job tasks
        from .job_tasks import set_session_store
        set_session_store(session_store)

    def create_job(self, job_type: str, session_id: str, inputs: dict) -> Job:
        """
        Create a new job record.

        Args:
            job_type: Type of job (parse, generate, validate, deploy)
            session_id: Session identifier
            inputs: Job input parameters

        Returns:
            Created Job object
        """
        job = Job(
            job_id=str(uuid.uuid4()),
            type=job_type,
            session_id=session_id,
            status="pending",
            inputs=inputs,
            created_at=datetime.now()
        )
        self.store.save_job(job)

        # Update session activity timestamp
        self.store.update_session_activity(session_id)

        return job

    async def run_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> None:
        """
        Execute a job in the background.

        Args:
            job_id: Job identifier
            task_func: Function to execute
            *args: Positional arguments for task_func
            **kwargs: Keyword arguments for task_func (including optional job_id for progress tracking)
        """
        # Update status to running
        job = self.store.get_job(job_id)
        if not job:
            return

        job.status = "running"
        self.store.update_job(job)

        try:
            # Add job_id to kwargs if not already present (for progress tracking)
            if 'job_id' not in kwargs:
                kwargs['job_id'] = job_id

            # Run in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()

            # Create a wrapper function that accepts the combined args
            def run_with_kwargs():
                return task_func(*args, **kwargs)

            result = await loop.run_in_executor(
                self.executor,
                run_with_kwargs
            )

            # Update with result
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now()

        except Exception as e:
            # Update with error
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()

        finally:
            self.store.update_job(job)

    def get_job(self, job_id: str) -> Job:
        """Get job status."""
        return self.store.get_job(job_id)
