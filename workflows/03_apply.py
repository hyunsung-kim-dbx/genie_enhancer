# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 3: Apply All Fixes
# MAGIC
# MAGIC **Purpose:** Apply ALL fixes in ONE batch update.
# MAGIC
# MAGIC **Key:** Single Genie Space API call - not one-at-a-time!

# COMMAND ----------

dbutils.widgets.text("run_id", "", "Job Run ID")
dbutils.widgets.text("loop_number", "1", "Loop Number")
dbutils.widgets.text("space_id", "", "Genie Space ID")
dbutils.widgets.text("databricks_host", "", "Databricks Host")
dbutils.widgets.text("databricks_token", "", "Databricks Token")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")
dbutils.widgets.text("catalog", "sandbox", "Catalog")
dbutils.widgets.text("schema", "genie_enhancement", "Schema")
dbutils.widgets.text("dry_run", "false", "Dry Run")

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
warehouse_id = dbutils.widgets.get("warehouse_id")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
dry_run = dbutils.widgets.get("dry_run").lower() == "true"

print("=" * 80)
print(f"STAGE 3: APPLY ALL FIXES (Loop {loop_number})")
print("=" * 80)
print(f"Dry Run: {dry_run}")

# COMMAND ----------

# Add project path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, project_root)

from enhancer.utils.state import JobState
from enhancer.api.space_api import SpaceUpdater
from enhancer.utils.sql import SQLExecutor
from enhancer.enhancement.applier import BatchApplier

# COMMAND ----------

# Get Stage 2 plan
state = JobState(catalog=catalog, schema=schema, spark=spark)
plan_output = state.get_stage_output(run_id, "plan")

if not plan_output:
    raise ValueError(f"No plan for run_id: {run_id}")

total_fixes = plan_output.get("total_fixes", 0)
print(f"Plan from Stage 2: {total_fixes} fixes")

# Load grouped fixes from Delta
grouped_fixes = state.get_enhancement_plan(run_id)

state.start_stage(run_id, "apply", {"total_fixes": total_fixes, "dry_run": dry_run})
state.update_run_stage(run_id, "apply")

# COMMAND ----------

# Initialize applier
space_api = SpaceUpdater(databricks_host, databricks_token)

sql_executor = None
if warehouse_id:
    sql_executor = SQLExecutor(databricks_host, databricks_token, warehouse_id)

applier = BatchApplier(
    space_api=space_api,
    sql_executor=sql_executor,
    config={"catalog": catalog, "schema": schema}
)

# COMMAND ----------

# Apply ALL fixes in ONE batch
start_time = datetime.now()

result = applier.apply_all(
    space_id=space_id,
    grouped_fixes=grouped_fixes,
    dry_run=dry_run
)

duration = (datetime.now() - start_time).total_seconds()

print(f"\n{'=' * 80}")
print(f"Applied: {len(result['applied'])} | Failed: {len(result['failed'])}")
print(f"Duration: {duration:.1f}s")
print("=" * 80)

# COMMAND ----------

# Save results
for fix in result["applied"]:
    state.save_implementation_result(run_id, fix, applied=True)
for fix in result["failed"]:
    state.save_implementation_result(run_id, fix, applied=False, rejection_reason=fix.get("error"))

output_data = {
    "applied_count": len(result["applied"]),
    "failed_count": len(result["failed"]),
    "duration_seconds": duration,
    "dry_run": dry_run,
    "success": result["success"]
}

state.complete_stage(run_id, "apply", output_data)

print(f"✅ Results saved")

# COMMAND ----------

# Display applied fixes
if result["applied"]:
    display_data = [{"Category": f.get("_category"), "Type": f.get("type"), "Status": "✅"} for f in result["applied"]]
    display(spark.createDataFrame(display_data))

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"applied": len(result["applied"]), "failed": len(result["failed"]), "run_id": run_id}))
