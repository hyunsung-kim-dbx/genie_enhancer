"""
Rollback Utility

Provides rollback capability to restore Genie Space to a previous iteration state.
Works with both automated and interactive modes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RollbackUtility:
    """Utility for rolling back Genie Space configuration."""

    def __init__(self, space_updater, catalog: str = None, schema: str = None, spark=None):
        """
        Initialize rollback utility.

        Args:
            space_updater: SpaceUpdater instance
            catalog: Catalog name (defaults to CATALOG env var or "sandbox")
            schema: Schema name (defaults to SCHEMA env var or "genie_enhancement")
            spark: Spark session (optional)
        """
        import os
        self.space_updater = space_updater
        self.catalog = catalog or os.getenv("CATALOG", "sandbox")
        self.schema = schema or os.getenv("SCHEMA", "genie_enhancement")
        self.full_name = f"{self.catalog}.{self.schema}"
        self.spark = spark or self._get_spark_session()

    def _get_spark_session(self):
        """Get Spark session if available."""
        try:
            from pyspark.sql import SparkSession
            return SparkSession.builder.getOrCreate()
        except ImportError:
            logger.warning("PySpark not available")
            return None

    def list_rollback_points(self, run_id: str) -> list:
        """
        List available rollback points for a run.

        Args:
            run_id: Enhancement run ID

        Returns:
            List of rollback point dictionaries
        """
        if not self.spark:
            raise RuntimeError("Spark session required for rollback")

        query = f"""
        SELECT
            iteration_number,
            score,
            num_changes,
            config_snapshot_path,
            started_at
        FROM {self.catalog}.enhancement_iterations
        WHERE run_id = '{run_id}'
          AND status = 'COMPLETED'
          AND can_rollback = TRUE
        ORDER BY iteration_number
        """

        df = self.spark.sql(query)
        rollback_points = df.toPandas().to_dict('records')

        logger.info(f"Found {len(rollback_points)} rollback points for run {run_id}")
        return rollback_points

    def get_config_snapshot(
        self,
        run_id: str,
        iteration_number: int
    ) -> Optional[Dict]:
        """
        Get configuration snapshot for a specific iteration.

        Args:
            run_id: Enhancement run ID
            iteration_number: Target iteration number

        Returns:
            Configuration dictionary or None
        """
        if not self.spark:
            raise RuntimeError("Spark session required")

        # Get snapshot path
        query = f"""
        SELECT config_snapshot_path
        FROM {self.catalog}.enhancement_iterations
        WHERE run_id = '{run_id}'
          AND iteration_number = {iteration_number}
          AND can_rollback = TRUE
        """

        df = self.spark.sql(query)
        rows = df.collect()

        if not rows:
            logger.error(f"No rollback point found for iteration {iteration_number}")
            return None

        snapshot_path = rows[0]['config_snapshot_path']

        if not snapshot_path:
            logger.error(f"No snapshot path for iteration {iteration_number}")
            return None

        # Load config from path (DBFS or S3)
        try:
            # Read from DBFS
            with open(snapshot_path.replace('dbfs:', '/dbfs'), 'r') as f:
                config = json.load(f)

            logger.info(f"Loaded config snapshot from {snapshot_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load config snapshot: {e}")
            return None

    def rollback(
        self,
        space_id: str,
        run_id: str,
        target_iteration: int,
        dry_run: bool = False
    ) -> Dict:
        """
        Rollback Genie Space to a previous iteration.

        Args:
            space_id: Genie Space ID
            run_id: Enhancement run ID
            target_iteration: Target iteration number to rollback to
            dry_run: If True, validate but don't apply

        Returns:
            Result dictionary with status and details
        """
        logger.info(f"Starting rollback to iteration {target_iteration}")

        # 1. Validate rollback point exists
        rollback_points = self.list_rollback_points(run_id)
        valid_iterations = [rp['iteration_number'] for rp in rollback_points]

        if target_iteration not in valid_iterations:
            return {
                "success": False,
                "error": f"Invalid target iteration. Available: {valid_iterations}"
            }

        # 2. Load target configuration
        target_config = self.get_config_snapshot(run_id, target_iteration)

        if not target_config:
            return {
                "success": False,
                "error": "Failed to load target configuration"
            }

        # 3. Validate configuration
        validation = self.space_updater.validate_config(target_config)

        if not validation['is_valid']:
            return {
                "success": False,
                "error": "Target configuration is invalid",
                "validation_errors": validation['errors']
            }

        # 4. Apply rollback (if not dry run)
        if dry_run:
            logger.info("DRY RUN: Would rollback to iteration {target_iteration}")
            return {
                "success": True,
                "dry_run": True,
                "target_iteration": target_iteration,
                "message": "Dry run successful - configuration is valid"
            }

        try:
            # Apply configuration
            self.space_updater.update_space(
                space_id=space_id,
                serialized_space=json.dumps(target_config)
            )

            # Record rollback in Delta table
            if self.spark:
                self._record_rollback(run_id, target_iteration, space_id)

            logger.info(f"✅ Successfully rolled back to iteration {target_iteration}")

            return {
                "success": True,
                "target_iteration": target_iteration,
                "message": f"Rolled back to iteration {target_iteration}",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _record_rollback(self, run_id: str, target_iteration: int, space_id: str):
        """Record rollback action in Delta table."""
        try:
            rollback_record = {
                "run_id": run_id,
                "space_id": space_id,
                "rollback_to_iteration": target_iteration,
                "rollback_timestamp": datetime.now(),
                "rollback_by": "rollback_utility"
            }

            df = self.spark.createDataFrame([rollback_record])

            # Append to rollback history table (create if not exists)
            df.write.format("delta").mode("append").saveAsTable(
                f"{self.full_name}.enhancement_rollbacks"
            )

            logger.info("Rollback action recorded in Delta table")

        except Exception as e:
            logger.warning(f"Failed to record rollback: {e}")

    def compare_configs(
        self,
        run_id: str,
        iteration_a: int,
        iteration_b: int
    ) -> Dict:
        """
        Compare configurations between two iterations.

        Args:
            run_id: Enhancement run ID
            iteration_a: First iteration
            iteration_b: Second iteration

        Returns:
            Dictionary with differences
        """
        config_a = self.get_config_snapshot(run_id, iteration_a)
        config_b = self.get_config_snapshot(run_id, iteration_b)

        if not config_a or not config_b:
            return {"error": "Failed to load configurations"}

        # Simple comparison (can be enhanced)
        differences = {
            "tables_added": [],
            "tables_removed": [],
            "synonyms_changed": [],
            "joins_changed": []
        }

        # Compare tables
        tables_a = set(t['identifier'] for t in config_a.get('data_sources', {}).get('tables', []))
        tables_b = set(t['identifier'] for t in config_b.get('data_sources', {}).get('tables', []))

        differences['tables_added'] = list(tables_b - tables_a)
        differences['tables_removed'] = list(tables_a - tables_b)

        # Compare joins
        joins_a = len(config_a.get('instructions', {}).get('join_specs', []))
        joins_b = len(config_b.get('instructions', {}).get('join_specs', []))

        differences['joins_changed'] = joins_b - joins_a

        return differences


# CLI interface for manual rollback
if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    if len(sys.argv) < 4:
        print("Usage: python rollback_utility.py <space_id> <run_id> <target_iteration>")
        print("Example: python rollback_utility.py 01j7abc123 run-uuid-456 3")
        sys.exit(1)

    space_id = sys.argv[1]
    run_id = sys.argv[2]
    target_iteration = int(sys.argv[3])

    # Initialize
    from lib.space_api import SpaceUpdater

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        sys.exit(1)

    space_updater = SpaceUpdater(host, token)
    rollback_util = RollbackUtility(space_updater)

    # List available rollback points
    print(f"\nAvailable rollback points for run {run_id}:")
    rollback_points = rollback_util.list_rollback_points(run_id)

    for rp in rollback_points:
        print(f"  Iteration {rp['iteration_number']}: Score {rp['score']:.1%}, {rp['num_changes']} changes")

    # Confirm rollback
    print(f"\n⚠️  This will rollback Space {space_id} to iteration {target_iteration}")
    confirm = input("Are you sure? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Rollback cancelled")
        sys.exit(0)

    # Perform rollback
    print("\nPerforming rollback...")
    result = rollback_util.rollback(space_id, run_id, target_iteration)

    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ Rollback failed: {result['error']}")
        sys.exit(1)
