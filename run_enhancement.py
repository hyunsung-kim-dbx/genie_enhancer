#!/usr/bin/env python3
"""
Genie Space Enhancement Runner

Simple script to run the full enhancement loop:
1. Clone production → dev-working + dev-best
2. Score benchmarks (baseline)
3. Generate fixes using category-based analysis
4. Apply all fixes at once
5. Score again (validation)
6. Optionally promote to production

Usage:
    python run_enhancement.py --config config.json

    Or set environment variables:
        export DATABRICKS_HOST=workspace.cloud.databricks.com
        export DATABRICKS_TOKEN=your-token
        export GENIE_SPACE_ID=your-space-id
        export WAREHOUSE_ID=your-warehouse-id
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.genie_client import GenieConversationalClient
from lib.space_cloner import SpaceCloner
from lib.scorer import BenchmarkScorer
from lib.benchmark_parser import BenchmarkLoader
from lib.llm import DatabricksLLMClient
from lib.sql import SQLExecutor
from lib.category_enhancer import CategoryEnhancer
from lib.applier import BatchApplier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_enhancement(
    databricks_host: str,
    databricks_token: str,
    space_id: str,
    warehouse_id: str,
    benchmark_file: str,
    llm_endpoint: str = "databricks-claude-sonnet-4",
    target_score: float = 0.90,
    indexing_wait: int = 60,
    max_loops: int = 3,
    auto_promote: bool = False,
    auto_cleanup: bool = True,
):
    """
    Run the full enhancement loop.

    Args:
        databricks_host: Databricks workspace host
        databricks_token: Personal access token
        space_id: Production Genie Space ID to enhance
        warehouse_id: SQL Warehouse ID
        benchmark_file: Path to benchmark JSON file
        llm_endpoint: LLM endpoint name
        target_score: Target accuracy score (0.0-1.0)
        indexing_wait: Seconds to wait after applying fixes
        max_loops: Maximum enhancement loops
        auto_promote: Automatically promote on success
        auto_cleanup: Clean up dev spaces on completion

    Returns:
        dict with results
    """
    logger.info("=" * 70)
    logger.info("GENIE SPACE ENHANCEMENT")
    logger.info("=" * 70)
    logger.info(f"Production Space: {space_id}")
    logger.info(f"Target Score: {target_score:.0%}")
    logger.info(f"Max Loops: {max_loops}")

    # =========================================================================
    # 1. Initialize Clients
    # =========================================================================
    logger.info("\n[1/7] Initializing clients...")

    space_cloner = SpaceCloner(host=databricks_host, token=databricks_token)

    llm_client = DatabricksLLMClient(
        host=databricks_host,
        token=databricks_token,
        endpoint_name=llm_endpoint,
        request_delay=10.0,
        rate_limit_base_delay=90.0
    )

    if not llm_client.test_connection():
        raise RuntimeError("LLM connection failed")

    sql_executor = SQLExecutor(
        host=databricks_host,
        token=databricks_token,
        warehouse_id=warehouse_id
    )

    # =========================================================================
    # 2. Load Benchmarks
    # =========================================================================
    logger.info("\n[2/7] Loading benchmarks...")

    loader = BenchmarkLoader(benchmark_file)
    benchmarks = loader.load()
    logger.info(f"Loaded {len(benchmarks)} benchmarks")

    # =========================================================================
    # 3. Setup Three-Space Architecture
    # =========================================================================
    logger.info("\n[3/7] Setting up three-space architecture...")

    setup_result = space_cloner.setup_three_spaces(production_space_id=space_id)

    if not setup_result['success']:
        raise RuntimeError(f"Three-space setup failed: {setup_result['error']}")

    production_id = setup_result['production_id']
    dev_working_id = setup_result['dev_working_id']
    dev_best_id = setup_result['dev_best_id']
    initial_config = setup_result['initial_config']

    logger.info(f"Production:   {production_id}")
    logger.info(f"Dev-Working:  {dev_working_id}")
    logger.info(f"Dev-Best:     {dev_best_id}")

    # Initialize remaining clients with dev-working space
    genie_client = GenieConversationalClient(
        host=databricks_host,
        token=databricks_token,
        space_id=dev_working_id,
        verbose=False
    )

    scorer = BenchmarkScorer(
        genie_client=genie_client,
        llm_client=llm_client,
        sql_executor=sql_executor,
        config={"parallel_workers": 0}
    )

    planner = CategoryEnhancer(llm_client, project_root / "prompts")

    applier = BatchApplier(
        space_api=space_cloner,
        sql_executor=sql_executor,
        config={"catalog": "sandbox", "schema": "genie_enhancement"}
    )

    # =========================================================================
    # 4. Enhancement Loop
    # =========================================================================
    best_score = 0.0
    best_config = initial_config
    loop_results = []

    for loop_num in range(1, max_loops + 1):
        logger.info("\n" + "=" * 70)
        logger.info(f"ENHANCEMENT LOOP {loop_num}/{max_loops}")
        logger.info("=" * 70)

        # ---------------------------------------------------------------------
        # 4a. Score current state
        # ---------------------------------------------------------------------
        logger.info(f"\n[4a] Scoring benchmarks (loop {loop_num})...")

        score_results = scorer.score(benchmarks)
        current_score = score_results['score']

        logger.info(f"Score: {current_score:.1%} ({score_results['passed']}/{score_results['total']} passed)")

        # Check if target reached
        if current_score >= target_score:
            logger.info(f"\n🎉 TARGET REACHED! Score: {current_score:.1%}")
            best_score = current_score
            break

        # Update best if improved
        if current_score > best_score:
            best_score = current_score
            best_config = space_cloner.get_dev_working_config()
            space_cloner.update_dev_best()  # Save to dev-best
            logger.info(f"New best score: {best_score:.1%}")

        # ---------------------------------------------------------------------
        # 4b. Generate fixes
        # ---------------------------------------------------------------------
        logger.info(f"\n[4b] Generating fixes (loop {loop_num})...")

        failed_results = [r for r in score_results['results'] if not r['passed']]

        if not failed_results:
            logger.info("No failures to fix!")
            break

        grouped_fixes = planner.generate_plan(
            failed_benchmarks=failed_results,
            space_config=space_cloner.get_dev_working_config(),
            parallel_workers=3
        )

        total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())
        logger.info(f"Generated {total_fixes} fixes")

        if total_fixes == 0:
            logger.info("No fixes generated, stopping loop")
            break

        # ---------------------------------------------------------------------
        # 4c. Apply fixes
        # ---------------------------------------------------------------------
        logger.info(f"\n[4c] Applying {total_fixes} fixes (loop {loop_num})...")

        apply_result = applier.apply_all(
            space_id=dev_working_id,
            grouped_fixes=grouped_fixes,
            dry_run=False
        )

        logger.info(f"Applied: {len(apply_result['applied'])}, Failed: {len(apply_result['failed'])}")

        if len(apply_result['applied']) == 0:
            logger.warning("No fixes applied, stopping loop")
            break

        # ---------------------------------------------------------------------
        # 4d. Wait for indexing
        # ---------------------------------------------------------------------
        logger.info(f"\n[4d] Waiting {indexing_wait}s for Genie indexing...")
        time.sleep(indexing_wait)

        # Record loop result
        loop_results.append({
            "loop": loop_num,
            "score_before": current_score,
            "fixes_applied": len(apply_result['applied']),
            "fixes_failed": len(apply_result['failed']),
        })

    # =========================================================================
    # 5. Final Scoring
    # =========================================================================
    logger.info("\n[5/7] Final validation scoring...")

    final_results = scorer.score(benchmarks)
    final_score = final_results['score']

    logger.info(f"Final Score: {final_score:.1%} ({final_results['passed']}/{final_results['total']} passed)")

    # Update best if improved
    if final_score > best_score:
        best_score = final_score
        space_cloner.update_dev_best()

    # =========================================================================
    # 6. Promotion Decision
    # =========================================================================
    logger.info("\n[6/7] Promotion decision...")

    promoted = False
    if final_score >= target_score or auto_promote:
        if auto_promote:
            logger.info("Auto-promoting dev-best to production...")
            promote_result = space_cloner.promote_to_production()

            if promote_result['success']:
                logger.info("✅ Production updated with enhanced configuration!")
                promoted = True
            else:
                logger.error(f"Promotion failed: {promote_result['error']}")
        else:
            logger.info("Target reached! Run with --auto-promote to apply to production")
    else:
        logger.info(f"Target not reached. Best score: {best_score:.1%}")

    # =========================================================================
    # 7. Cleanup
    # =========================================================================
    logger.info("\n[7/7] Cleanup...")

    if auto_cleanup:
        cleanup_result = space_cloner.cleanup_dev_spaces()
        if cleanup_result['success']:
            logger.info("✅ Dev spaces cleaned up")
        else:
            logger.warning(f"Cleanup warning: {cleanup_result['error']}")
    else:
        logger.info("Dev spaces preserved for review:")
        logger.info(f"  Dev-Working: {dev_working_id}")
        logger.info(f"  Dev-Best: {dev_best_id}")

    # =========================================================================
    # Results
    # =========================================================================
    results = {
        "success": final_score >= target_score,
        "production_id": production_id,
        "dev_working_id": dev_working_id if not auto_cleanup else None,
        "dev_best_id": dev_best_id if not auto_cleanup else None,
        "initial_score": score_results['score'] if loop_results else final_score,
        "final_score": final_score,
        "best_score": best_score,
        "target_score": target_score,
        "loops_completed": len(loop_results),
        "promoted": promoted,
        "loop_results": loop_results,
    }

    logger.info("\n" + "=" * 70)
    logger.info("ENHANCEMENT COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Final Score: {final_score:.1%}")
    logger.info(f"Target: {target_score:.1%}")
    logger.info(f"Loops: {len(loop_results)}")
    logger.info(f"Promoted: {promoted}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run Genie Space enhancement")

    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--host", type=str, help="Databricks host")
    parser.add_argument("--token", type=str, help="Databricks token")
    parser.add_argument("--space-id", type=str, help="Production Genie Space ID")
    parser.add_argument("--warehouse-id", type=str, help="SQL Warehouse ID")
    parser.add_argument("--benchmarks", type=str, help="Path to benchmark JSON file")
    parser.add_argument("--llm-endpoint", type=str, default="databricks-claude-sonnet-4")
    parser.add_argument("--target-score", type=float, default=0.90)
    parser.add_argument("--indexing-wait", type=int, default=60)
    parser.add_argument("--max-loops", type=int, default=3)
    parser.add_argument("--auto-promote", action="store_true", help="Auto-promote on success")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't cleanup dev spaces")

    args = parser.parse_args()

    # Load config from file or environment
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        config = {}

    # CLI args override config file, env vars are fallback
    databricks_host = args.host or config.get("databricks_host") or os.getenv("DATABRICKS_HOST")
    databricks_token = args.token or config.get("databricks_token") or os.getenv("DATABRICKS_TOKEN")
    space_id = args.space_id or config.get("space_id") or os.getenv("GENIE_SPACE_ID")
    warehouse_id = args.warehouse_id or config.get("warehouse_id") or os.getenv("WAREHOUSE_ID")
    benchmark_file = args.benchmarks or config.get("benchmarks") or "benchmarks/fixed_benchmark_final.json"

    if not all([databricks_host, databricks_token, space_id, warehouse_id]):
        print("Error: Missing required parameters")
        print("  Required: --host, --token, --space-id, --warehouse-id")
        print("  Or set environment variables: DATABRICKS_HOST, DATABRICKS_TOKEN, GENIE_SPACE_ID, WAREHOUSE_ID")
        print("  Or use --config with a JSON file")
        sys.exit(1)

    results = run_enhancement(
        databricks_host=databricks_host,
        databricks_token=databricks_token,
        space_id=space_id,
        warehouse_id=warehouse_id,
        benchmark_file=benchmark_file,
        llm_endpoint=args.llm_endpoint,
        target_score=args.target_score,
        indexing_wait=args.indexing_wait,
        max_loops=args.max_loops,
        auto_promote=args.auto_promote,
        auto_cleanup=not args.no_cleanup,
    )

    # Save results
    output_file = f"enhancement_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()
