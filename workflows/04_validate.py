# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 4: Validate Results
# MAGIC
# MAGIC **Purpose:** Re-score benchmarks and compare with initial.
# MAGIC
# MAGIC **Decision:** If target not reached, trigger another loop.

# COMMAND ----------

dbutils.widgets.text("run_id", "", "Job Run ID")
dbutils.widgets.text("loop_number", "1", "Loop Number")
dbutils.widgets.text("space_id", "", "Genie Space ID")
dbutils.widgets.text("databricks_host", "", "Databricks Host")
dbutils.widgets.text("databricks_token", "", "Databricks Token")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")
dbutils.widgets.text("llm_endpoint", "databricks-gpt-5-2", "LLM Endpoint")
dbutils.widgets.text("catalog", "sandbox", "Catalog")
dbutils.widgets.text("schema", "genie_enhancement", "Schema")
dbutils.widgets.text("target_score", "0.90", "Target Score")
dbutils.widgets.text("indexing_wait", "60", "Indexing Wait (seconds)")
dbutils.widgets.text("benchmarks_table", "", "Benchmarks Table")

# COMMAND ----------

import json
import sys
import time
from datetime import datetime

# Parameters
run_id = dbutils.widgets.get("run_id")
loop_number = int(dbutils.widgets.get("loop_number"))
space_id = dbutils.widgets.get("space_id")
databricks_host = dbutils.widgets.get("databricks_host")
databricks_token = dbutils.widgets.get("databricks_token")
warehouse_id = dbutils.widgets.get("warehouse_id")
llm_endpoint = dbutils.widgets.get("llm_endpoint")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
target_score = float(dbutils.widgets.get("target_score"))
indexing_wait = int(dbutils.widgets.get("indexing_wait"))
benchmarks_table = dbutils.widgets.get("benchmarks_table")

print("=" * 80)
print(f"STAGE 4: VALIDATE RESULTS (Loop {loop_number})")
print("=" * 80)
print(f"Target Score: {target_score:.1%}")

# COMMAND ----------

# Add project path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, project_root)

from enhancer.utils.state import JobState
from enhancer.api.genie_client import GenieConversationalClient
from enhancer.scoring.scorer import BenchmarkScorer
from enhancer.llm.llm import DatabricksLLMClient
from enhancer.utils.sql import SQLExecutor

# COMMAND ----------

# Get previous results
state = JobState(catalog=catalog, schema=schema, spark=spark)

score_output = state.get_stage_output(run_id, "score")
apply_output = state.get_stage_output(run_id, "apply")

initial_score = score_output.get("score", 0)
applied_count = apply_output.get("applied_count", 0)

print(f"Initial Score: {initial_score:.1%}")
print(f"Fixes Applied: {applied_count}")

state.start_stage(run_id, "validate", {"initial_score": initial_score})
state.update_run_stage(run_id, "validate")

# COMMAND ----------

# Wait for Genie indexing
if applied_count > 0:
    print(f"\n⏳ Waiting {indexing_wait}s for Genie indexing...")
    time.sleep(indexing_wait)
    print("✅ Indexing wait complete")

# COMMAND ----------

# Load benchmarks
if benchmarks_table:
    benchmarks_df = spark.table(benchmarks_table)
else:
    benchmarks_df = spark.table(f"{catalog}.{schema}.benchmarks")
benchmarks = [row.asDict() for row in benchmarks_df.collect()]

# COMMAND ----------

# Initialize scorer
genie_client = GenieConversationalClient(databricks_host, databricks_token, space_id)
llm_client = DatabricksLLMClient(databricks_host, databricks_token, llm_endpoint)
sql_executor = SQLExecutor(databricks_host, databricks_token, warehouse_id) if warehouse_id else None
scorer = BenchmarkScorer(genie_client, llm_client, sql_executor, {"question_timeout": 120})

# COMMAND ----------

# Run final scoring
print(f"\nScoring {len(benchmarks)} benchmarks...")
start_time = datetime.now()

final_results = scorer.score(benchmarks)

duration = (datetime.now() - start_time).total_seconds()
final_score = final_results["score"]
improvement = final_score - initial_score

print(f"\n{'=' * 80}")
print(f"RESULTS")
print(f"{'=' * 80}")
print(f"Initial:     {initial_score:.1%}")
print(f"Final:       {final_score:.1%}")
print(f"Improvement: {improvement:+.1%}")
print(f"Target:      {target_score:.1%}")
print(f"{'=' * 80}")

# COMMAND ----------

# Save final results
state.save_benchmark_results(run_id, f"loop_{loop_number}_final", final_results["results"])

target_reached = final_score >= target_score

output_data = {
    "initial_score": initial_score,
    "final_score": final_score,
    "improvement": improvement,
    "target_score": target_score,
    "target_reached": target_reached,
    "passed": final_results["passed"],
    "failed": final_results["failed"],
    "duration_seconds": duration,
    "loop_number": loop_number
}

state.complete_stage(run_id, "validate", output_data)

# Complete run
status = "TARGET_REACHED" if target_reached else "NEEDS_ANOTHER_LOOP"
state.complete_run(run_id, status=status)

# COMMAND ----------

# Summary
if target_reached:
    print(f"\n🎉 TARGET REACHED! Score: {final_score:.1%}")
else:
    print(f"\n⚠️ Target not reached. Score: {final_score:.1%} < {target_score:.1%}")
    print(f"   Consider running another loop (Loop {loop_number + 1})")

# COMMAND ----------

# Show comparison
comparison_data = []
for r in final_results["results"]:
    comparison_data.append({
        "Question": r["question"][:50],
        "Status": "✅" if r["passed"] else "❌",
        "Category": r.get("failure_category", "")
    })
display(spark.createDataFrame(comparison_data))

# COMMAND ----------

dbutils.notebook.exit(json.dumps({
    "initial_score": initial_score,
    "final_score": final_score,
    "improvement": improvement,
    "target_reached": target_reached,
    "needs_another_loop": not target_reached,
    "next_loop_number": loop_number + 1,
    "run_id": run_id
}))
