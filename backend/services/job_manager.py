"""Job manager for background task orchestration."""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

from .session_store_base import SessionStoreBase, Job


class JobManager:
    """Manages background job execution with thread pool."""

    def __init__(self, session_store: SessionStoreBase, max_workers: int = 4):
        """
        Initialize job manager.

        Args:
            session_store: Store for persisting job state
            max_workers: Maximum concurrent jobs
        """
        self.store = session_store
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Set global session store reference for job tasks
        from .enhancement_tasks import set_session_store
        set_session_store(session_store)

    def create_job(self, job_type: str, session_id: str, inputs: dict) -> Job:
        """
        Create a new job record.

        Args:
            job_type: Type of job (score, plan, apply, validate)
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
        self.store.update_session_activity(session_id)

        return job

    async def run_job(self, job_id: str, task_func: Callable, *args, **kwargs) -> None:
        """
        Execute a job in the background.

        Args:
            job_id: Job identifier
            task_func: Function to execute
            *args: Positional arguments for task_func
            **kwargs: Keyword arguments for task_func
        """
        job = self.store.get_job(job_id)
        if not job:
            return

        job.status = "running"
        self.store.update_job(job)

        try:
            if 'job_id' not in kwargs:
                kwargs['job_id'] = job_id

            loop = asyncio.get_event_loop()

            def run_with_kwargs():
                return task_func(*args, **kwargs)

            result = await loop.run_in_executor(
                self.executor,
                run_with_kwargs
            )

            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now()

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()

        finally:
            self.store.update_job(job)

    def get_job(self, job_id: str) -> Job:
        """Get job status."""
        return self.store.get_job(job_id)
