"""FastAPI backend for Genie Space Enhancement System."""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel

from backend.services.session_store import SQLiteSessionStore
from backend.services.job_manager import JobManager
from backend.services.file_storage import LocalFileStorageService
from backend.services.enhancement_tasks import (
    run_score_job,
    run_plan_job,
    run_apply_job,
    run_validate_job
)
from backend.middleware.auth import get_current_user


# Initialize FastAPI app
app = FastAPI(
    title="Genie Space Enhancement API",
    description="Automated improvement system for Databricks Genie Spaces",
    version="3.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Next.js static export
frontend_export_dir = os.getenv("FRONTEND_EXPORT_DIR", "../frontend/out")
frontend_export_path = Path(frontend_export_dir)

print(f"Frontend export dir: {frontend_export_dir}")
print(f"Frontend path exists: {frontend_export_path.exists()}")

# Mount static assets early (before API routes)
if frontend_export_path.exists():
    print(f"Mounting frontend static assets from {frontend_export_path}")
    if (frontend_export_path / "_next").exists():
        app.mount("/_next", StaticFiles(directory=str(frontend_export_path / "_next")), name="next_static")
        print("Mounted /_next static files")
else:
    print(f"WARNING: Frontend export directory not found at {frontend_export_path.absolute()}")

# Initialize services
session_store = SQLiteSessionStore()
job_manager = JobManager(session_store)
file_storage = LocalFileStorageService()


# Request/Response models
class WorkspaceConfig(BaseModel):
    """Databricks workspace configuration."""
    host: str
    token: str
    warehouse_id: str
    space_id: str
    llm_endpoint: str = "databricks-gpt-5-2"


class ScoreRequest(BaseModel):
    """Request to score benchmarks."""
    session_id: str
    workspace_config: WorkspaceConfig
    benchmarks: List[dict]


class PlanRequest(BaseModel):
    """Request to generate enhancement plan."""
    session_id: str
    workspace_config: WorkspaceConfig
    failed_benchmarks: List[dict]


class ApplyRequest(BaseModel):
    """Request to apply enhancements."""
    session_id: str
    workspace_config: WorkspaceConfig
    grouped_fixes: dict
    dry_run: bool = False


class ValidateRequest(BaseModel):
    """Request to validate enhancements."""
    session_id: str
    workspace_config: WorkspaceConfig
    benchmarks: List[dict]
    initial_score: float
    target_score: float = 0.90


class SessionResponse(BaseModel):
    """Session information."""
    session_id: str
    name: str
    created_at: str
    updated_at: str


class JobResponse(BaseModel):
    """Job status response."""
    job_id: str
    type: str
    status: str
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "genie-enhancement", "version": "3.0.0"}


# Workspace configuration
@app.get("/api/workspace/config")
async def get_workspace_config():
    """Get default workspace configuration from environment variables.

    Auto-populates host and token from environment.
    - Host: From DATABRICKS_HOST env var (set by Databricks Apps)
    - Token: From DATABRICKS_TOKEN env var (should be interpolated from secrets)

    If token is still a template {{...}}, it means:
    1. Secret doesn't exist, OR
    2. App doesn't have permission to read it, OR
    3. Secret scope/key name is incorrect

    Check: databricks secrets list --scope genie-enhancement
    """
    import os

    # Get all DATABRICKS_HOST env vars (there might be duplicates in env)
    host = os.getenv("DATABRICKS_HOST", "")

    # Clean up host
    if host.startswith("{{"):
        # Template not interpolated, try to find the actual value
        # Check if there's another DATABRICKS_HOST that's not a template
        host = ""

    if not host:
        # Fallback to server hostname
        server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
        if server_hostname and not server_hostname.startswith("{{"):
            host = f"https://{server_hostname}"

    # Ensure https://
    if host and not host.startswith("http"):
        host = f"https://{host}"

    # Get token - should be interpolated from secrets
    token = os.getenv("DATABRICKS_TOKEN", "")

    # Check if template is not interpolated
    token_not_interpolated = token.startswith("{{")

    if token_not_interpolated:
        # Token is still a template - secret not accessible
        token = ""
        print(f"WARNING: DATABRICKS_TOKEN is still a template: {token}")
        print("This means the secret is not being read from the scope.")
        print("Check: 1) Secret exists, 2) App has read permission, 3) Secret name is correct")

    return {
        "host": host,
        "token": token,
        "_debug": {
            "host_raw": os.getenv("DATABRICKS_HOST", ""),
            "token_is_template": token_not_interpolated,
            "token_hint": "Check 'databricks secrets list --scope genie-enhancement'" if token_not_interpolated else "Token successfully loaded"
        }
    }


class WorkspaceCredentials(BaseModel):
    """Workspace credentials for listing resources."""
    host: str
    token: str


@app.post("/api/workspace/warehouses")
async def list_warehouses(credentials: WorkspaceCredentials):
    """List available SQL Warehouses."""
    import os
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.config import Config

    # Use credentials from request (user-provided in UI)
    host = credentials.host if credentials.host.startswith("https://") else f"https://{credentials.host}"

    # CRITICAL: Explicitly clear OAuth env vars to prevent SDK from picking them up
    # The Databricks Apps runtime sets these, but we want to use PAT auth instead
    saved_client_id = os.environ.pop('DATABRICKS_CLIENT_ID', None)
    saved_client_secret = os.environ.pop('DATABRICKS_CLIENT_SECRET', None)

    try:
        # Explicitly use PAT auth with OAuth disabled
        config = Config(
            host=host,
            token=credentials.token,
            client_id="",  # Empty string to override env var
            client_secret="",
        )
        client = WorkspaceClient(config=config)

        warehouses = []
        for wh in client.warehouses.list():
            warehouses.append({
                "id": wh.id,
                "name": wh.name,
                "state": wh.state.value if wh.state else "UNKNOWN",
                "cluster_size": wh.cluster_size if hasattr(wh, 'cluster_size') else None
            })

        return {"warehouses": warehouses}
    except Exception as e:
        return {"error": str(e), "warehouses": []}
    finally:
        # Restore env vars if they were set
        if saved_client_id:
            os.environ['DATABRICKS_CLIENT_ID'] = saved_client_id
        if saved_client_secret:
            os.environ['DATABRICKS_CLIENT_SECRET'] = saved_client_secret


@app.post("/api/workspace/spaces")
async def list_genie_spaces(credentials: WorkspaceCredentials):
    """List available Genie Spaces."""
    import os
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.config import Config

    # Use credentials from request (user-provided in UI)
    host = credentials.host if credentials.host.startswith("https://") else f"https://{credentials.host}"

    # CRITICAL: Explicitly clear OAuth env vars to prevent SDK from picking them up
    # The Databricks Apps runtime sets these, but we want to use PAT auth instead
    saved_client_id = os.environ.pop('DATABRICKS_CLIENT_ID', None)
    saved_client_secret = os.environ.pop('DATABRICKS_CLIENT_SECRET', None)

    try:
        # Explicitly use PAT auth with OAuth disabled
        config = Config(
            host=host,
            token=credentials.token,
            client_id="",  # Empty string to override env var
            client_secret="",
        )
        client = WorkspaceClient(config=config)

        spaces = []
        for space in client.genie.spaces.list():
            spaces.append({
                "id": space.space_id,
                "name": space.name,
                "description": space.description if hasattr(space, 'description') else None
            })

        return {"spaces": spaces}
    except Exception as e:
        return {"error": str(e), "spaces": []}
    finally:
        # Restore env vars if they were set
        if saved_client_id:
            os.environ['DATABRICKS_CLIENT_ID'] = saved_client_id
        if saved_client_secret:
            os.environ['DATABRICKS_CLIENT_SECRET'] = saved_client_secret


# Session management
@app.post("/api/sessions/create")
async def create_session(user: dict = Depends(get_current_user)):
    """Create a new enhancement session."""
    session_id = session_store.create_session(user["user_id"])
    session = session_store.get_session(session_id)
    return session


@app.get("/api/sessions")
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """List user's enhancement sessions."""
    sessions = session_store.list_sessions(user["user_id"], limit, offset)
    return {"sessions": sessions, "has_more": len(sessions) == limit}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    """Get session details."""
    session = session_store.get_session(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    return session


@app.post("/api/sessions/{session_id}/rename")
async def rename_session(
    session_id: str,
    name: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """Rename a session."""
    session_store.rename_session(session_id, name)
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """Delete a session."""
    session_store.delete_session(session_id)
    file_storage.delete_session_files(session_id)
    return {"success": True}


# Job management
@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str, user: dict = Depends(get_current_user)):
    """Get job status."""
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}, 404

    return JobResponse(
        job_id=job.job_id,
        type=job.type,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error
    )


@app.get("/api/sessions/{session_id}/jobs")
async def get_session_jobs(session_id: str, user: dict = Depends(get_current_user)):
    """Get all jobs for a session."""
    jobs = session_store.get_session_jobs(session_id)
    return {
        "jobs": [
            JobResponse(
                job_id=job.job_id,
                type=job.type,
                status=job.status,
                progress=job.progress,
                result=job.result,
                error=job.error
            )
            for job in jobs
        ]
    }


# Enhancement workflow
@app.post("/api/jobs/score")
async def start_score_job(
    request: ScoreRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Start benchmark scoring job."""
    job = job_manager.create_job("score", request.session_id, {
        "workspace_config": request.workspace_config.dict(),
        "benchmarks": request.benchmarks
    })

    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_score_job,
        request.session_id,
        request.workspace_config.space_id,
        request.workspace_config.host,
        request.workspace_config.token,
        request.workspace_config.warehouse_id,
        request.benchmarks,
        request.workspace_config.llm_endpoint
    )

    return {"job_id": job.job_id, "status": "pending"}


@app.post("/api/jobs/plan")
async def start_plan_job(
    request: PlanRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Start enhancement planning job."""
    job = job_manager.create_job("plan", request.session_id, {
        "workspace_config": request.workspace_config.dict(),
        "failed_benchmarks": request.failed_benchmarks
    })

    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_plan_job,
        request.session_id,
        request.workspace_config.space_id,
        request.workspace_config.host,
        request.workspace_config.token,
        request.failed_benchmarks,
        request.workspace_config.llm_endpoint
    )

    return {"job_id": job.job_id, "status": "pending"}


@app.post("/api/jobs/apply")
async def start_apply_job(
    request: ApplyRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Start fix application job."""
    job = job_manager.create_job("apply", request.session_id, {
        "workspace_config": request.workspace_config.dict(),
        "grouped_fixes": request.grouped_fixes,
        "dry_run": request.dry_run
    })

    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_apply_job,
        request.session_id,
        request.workspace_config.space_id,
        request.workspace_config.host,
        request.workspace_config.token,
        request.workspace_config.warehouse_id,
        request.grouped_fixes,
        request.dry_run
    )

    return {"job_id": job.job_id, "status": "pending"}


@app.post("/api/jobs/validate")
async def start_validate_job(
    request: ValidateRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Start validation job."""
    job = job_manager.create_job("validate", request.session_id, {
        "workspace_config": request.workspace_config.dict(),
        "benchmarks": request.benchmarks,
        "initial_score": request.initial_score,
        "target_score": request.target_score
    })

    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_validate_job,
        request.session_id,
        request.workspace_config.space_id,
        request.workspace_config.host,
        request.workspace_config.token,
        request.workspace_config.warehouse_id,
        request.benchmarks,
        request.initial_score,
        request.target_score,
        request.workspace_config.llm_endpoint
    )

    return {"job_id": job.job_id, "status": "pending"}


# File upload
@app.post("/api/sessions/{session_id}/upload")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload benchmark file for a session."""
    file_path = file_storage.save_file(session_id, file.filename, file.file)
    return {"filename": file.filename, "path": file_path}


# Serve frontend
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve Next.js frontend for all other routes."""
    if frontend_export_path.exists():
        # Try to serve specific file
        file_path = frontend_export_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Serve index.html for client-side routing
        index_path = frontend_export_path / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)

    return {"error": "Frontend not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
