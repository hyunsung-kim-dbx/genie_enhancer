"""Background tasks for enhancement workflow."""

import logging
from typing import Dict, Any, Optional

from enhancer.api.genie_client import GenieConversationalClient
from enhancer.scoring.batch_scorer import BatchBenchmarkScorer
from enhancer.enhancement.category_enhancer import CategoryEnhancer
from enhancer.enhancement.applier import BatchApplier
from enhancer.llm.llm import DatabricksLLMClient
from enhancer.utils.sql import SQLExecutor
from enhancer.api.space_api import SpaceUpdater

logger = logging.getLogger(__name__)

# Global session store reference
_session_store = None


def set_session_store(store):
    """Set the global session store reference."""
    global _session_store
    _session_store = store


def update_job_progress(job_id: str, progress: Dict[str, Any]):
    """Update job progress in session store."""
    if _session_store:
        job = _session_store.get_job(job_id)
        if job:
            job.progress = progress
            _session_store.update_job(job)


def run_score_job(
    session_id: str,
    space_id: str,
    databricks_host: str,
    databricks_token: str,
    warehouse_id: str,
    benchmarks: list,
    llm_endpoint: str = "databricks-gpt-5-2",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score benchmarks against Genie Space.

    Args:
        session_id: Session identifier
        space_id: Genie Space ID
        databricks_host: Databricks workspace URL
        databricks_token: Access token
        warehouse_id: SQL Warehouse ID
        benchmarks: List of benchmark questions
        llm_endpoint: LLM model endpoint
        job_id: Optional job ID for progress tracking

    Returns:
        Scoring results with score, passed, failed counts
    """
    logger.info(f"Starting score job for session {session_id}")

    # Initialize clients
    genie_client = GenieConversationalClient(databricks_host, databricks_token, space_id)
    llm_client = DatabricksLLMClient(databricks_host, databricks_token, llm_endpoint)
    sql_executor = SQLExecutor(databricks_host, databricks_token, warehouse_id)

    # Create scorer
    scorer = BatchBenchmarkScorer(
        genie_client,
        llm_client,
        sql_executor,
        progress_callback=lambda p: update_job_progress(job_id, p) if job_id else None
    )

    # Run scoring
    results = scorer.score(benchmarks)

    logger.info(f"Score job completed: {results['score']:.1%}")

    return {
        "score": results["score"],
        "passed": results["passed"],
        "failed": results["failed"],
        "total": results["total"],
        "results": results["results"]
    }


def run_plan_job(
    session_id: str,
    space_id: str,
    databricks_host: str,
    databricks_token: str,
    failed_benchmarks: list,
    llm_endpoint: str = "databricks-gpt-5-2",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate enhancement plan from failed benchmarks.

    Args:
        session_id: Session identifier
        space_id: Genie Space ID
        databricks_host: Databricks workspace URL
        databricks_token: Access token
        failed_benchmarks: List of failed benchmark results
        llm_endpoint: LLM model endpoint
        job_id: Optional job ID for progress tracking

    Returns:
        Enhancement plan with grouped fixes
    """
    logger.info(f"Starting plan job for session {session_id}")

    # Initialize clients
    llm_client = DatabricksLLMClient(databricks_host, databricks_token, llm_endpoint)
    space_api = SpaceUpdater(databricks_host, databricks_token)

    # Get current space config
    space_config = space_api.export_space(space_id)

    # Generate plan
    from pathlib import Path
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    planner = CategoryEnhancer(llm_client, prompts_dir)

    grouped_fixes = planner.generate_plan(
        failed_benchmarks=failed_benchmarks,
        space_config=space_config
    )

    total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())
    logger.info(f"Plan job completed: {total_fixes} fixes generated")

    return {
        "total_fixes": total_fixes,
        "grouped_fixes": grouped_fixes
    }


def run_apply_job(
    session_id: str,
    space_id: str,
    databricks_host: str,
    databricks_token: str,
    warehouse_id: str,
    grouped_fixes: dict,
    dry_run: bool = False,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply enhancement fixes to Genie Space.

    Args:
        session_id: Session identifier
        space_id: Genie Space ID
        databricks_host: Databricks workspace URL
        databricks_token: Access token
        warehouse_id: SQL Warehouse ID
        grouped_fixes: Grouped enhancement fixes
        dry_run: If True, don't actually apply changes
        job_id: Optional job ID for progress tracking

    Returns:
        Application results
    """
    logger.info(f"Starting apply job for session {session_id} (dry_run={dry_run})")

    # Initialize clients
    space_api = SpaceUpdater(databricks_host, databricks_token)
    sql_executor = SQLExecutor(databricks_host, databricks_token, warehouse_id)

    # Apply fixes
    applier = BatchApplier(space_api, sql_executor)

    if dry_run:
        logger.info("Dry run mode - skipping actual application")
        return {
            "applied_count": 0,
            "dry_run": True,
            "success": True
        }

    result = applier.apply_all_fixes(space_id, grouped_fixes)

    logger.info(f"Apply job completed: {result.get('applied_count', 0)} fixes applied")

    return result


def run_validate_job(
    session_id: str,
    space_id: str,
    databricks_host: str,
    databricks_token: str,
    warehouse_id: str,
    benchmarks: list,
    initial_score: float,
    target_score: float,
    llm_endpoint: str = "databricks-gpt-5-2",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate enhancements by re-scoring benchmarks.

    Args:
        session_id: Session identifier
        space_id: Genie Space ID
        databricks_host: Databricks workspace URL
        databricks_token: Access token
        warehouse_id: SQL Warehouse ID
        benchmarks: List of benchmark questions
        initial_score: Initial score before enhancements
        target_score: Target score threshold
        llm_endpoint: LLM model endpoint
        job_id: Optional job ID for progress tracking

    Returns:
        Validation results with new score and comparison
    """
    logger.info(f"Starting validate job for session {session_id}")

    # Re-run scoring
    score_result = run_score_job(
        session_id,
        space_id,
        databricks_host,
        databricks_token,
        warehouse_id,
        benchmarks,
        llm_endpoint,
        job_id
    )

    new_score = score_result["score"]
    improvement = new_score - initial_score
    target_reached = new_score >= target_score

    logger.info(f"Validate job completed: {new_score:.1%} (improvement: {improvement:+.1%})")

    return {
        "initial_score": initial_score,
        "new_score": new_score,
        "improvement": improvement,
        "target_score": target_score,
        "target_reached": target_reached,
        "results": score_result["results"]
    }
