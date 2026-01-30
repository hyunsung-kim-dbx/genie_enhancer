# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 2: Plan Enhancements
# MAGIC
# MAGIC **Purpose:** Analyze failures and generate ALL fixes at once.
# MAGIC
# MAGIC **Outputs:**
# MAGIC - Complete fix plan grouped by category
# MAGIC - Ready for batch application in Stage 3

# COMMAND ----------

dbutils.widgets.text("run_id", "", "Job Run ID")
dbutils.widgets.text("loop_number", "1", "Loop Number")
dbutils.widgets.text("space_id", "", "Genie Space ID")
dbutils.widgets.text("databricks_host", "", "Databricks Host")
dbutils.widgets.text("databricks_token", "", "Databricks Token")
dbutils.widgets.text("llm_endpoint", "databricks-gpt-5-2", "LLM Endpoint")
dbutils.widgets.text("catalog", "sandbox", "Catalog")
dbutils.widgets.text("schema", "genie_enhancement", "Schema")
dbutils.widgets.text("parallel_workers", "1", "Parallel LLM Workers")

# COMMAND ----------

import json
import sys
from datetime import datetime

# Parameters
run_id = dbutils.widgets.get("run_id")
loop_number = int(dbutils.widgets.get("loop_number"))
space_id = dbutils.widgets.get("space_id")
databricks_host = dbutils.widgets.get("databricks_host")
databricks_token = dbutils.widgets.get("databricks_token")
llm_endpoint = dbutils.widgets.get("llm_endpoint")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
parallel_workers = int(dbutils.widgets.get("parallel_workers"))

print("=" * 80)
print(f"STAGE 2: PLAN ENHANCEMENTS (Loop {loop_number})")
print("=" * 80)

# COMMAND ----------

# Add project path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, project_root)

from lib.state import JobState
from lib.llm import DatabricksLLMClient
from lib.space_api import SpaceUpdater
from lib.enhancer import EnhancementPlanner
from pathlib import Path

# COMMAND ----------

# Get Stage 1 results
state = JobState(catalog=catalog, schema=schema, spark=spark)
score_output = state.get_stage_output(run_id, "score")

if not score_output:
    raise ValueError(f"No score results for run_id: {run_id}")

failed_results = score_output.get("failed_results", [])
initial_score = score_output.get("score", 0)

print(f"Score from Stage 1: {initial_score:.1%}")
print(f"Failed benchmarks: {len(failed_results)}")

state.start_stage(run_id, "plan", {"failed_count": len(failed_results)})
state.update_run_stage(run_id, "plan")

# COMMAND ----------

# Initialize clients
llm_client = DatabricksLLMClient(databricks_host, databricks_token, llm_endpoint)
space_api = SpaceUpdater(databricks_host, databricks_token)

# Get current space config
space_config = space_api.export_space(space_id)
print(f"✅ Space config loaded ({len(space_config.get('data_sources', {}).get('tables', []))} tables)")

# COMMAND ----------

# Generate enhancement plan
prompts_dir = Path(project_root) / "prompts"
planner = EnhancementPlanner(llm_client, prompts_dir)

start_time = datetime.now()

grouped_fixes = planner.generate_plan(
    failed_benchmarks=failed_results,
    space_config=space_config,
    parallel_workers=parallel_workers
)

duration = (datetime.now() - start_time).total_seconds()

# COMMAND ----------

# Save plan
state.save_enhancement_plan(run_id, grouped_fixes)

total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())

output_data = {
    "total_fixes": total_fixes,
    "fixes_by_category": {cat: len(fixes) for cat, fixes in grouped_fixes.items()},
    "duration_seconds": duration,
    "initial_score": initial_score,
    "space_config": json.dumps(space_config)
}

state.complete_stage(run_id, "plan", output_data)

print(f"\n✅ Plan saved: {total_fixes} total fixes")

# COMMAND ----------

# Display plan summary
for category in ["metric_view", "metadata", "sample_query", "instruction"]:
    fixes = grouped_fixes.get(category, [])
    print(f"\n{category.upper()} ({len(fixes)} fixes)")
    for fix in fixes[:3]:
        print(f"  - {fix.get('type')}: {str(fix)[:60]}...")
    if len(fixes) > 3:
        print(f"  ... and {len(fixes) - 3} more")

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"total_fixes": total_fixes, "run_id": run_id}))
