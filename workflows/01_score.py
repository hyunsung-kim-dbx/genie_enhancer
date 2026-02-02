# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 1: Score Benchmarks
# MAGIC
# MAGIC **Purpose:** Evaluate current Genie Space performance against benchmarks.
# MAGIC
# MAGIC **Outputs:**
# MAGIC - Current score percentage
# MAGIC - List of failed benchmarks for Stage 2

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
dbutils.widgets.text("benchmarks_table", "", "Benchmarks Table")

# COMMAND ----------

import json
import sys
from datetime import datetime
from pathlib import Path

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
benchmarks_table = dbutils.widgets.get("benchmarks_table")

print("=" * 80)
print(f"STAGE 1: SCORE BENCHMARKS (Loop {loop_number})")
print("=" * 80)
print(f"Run ID: {run_id}")
print(f"Space ID: {space_id}")

# COMMAND ----------

# Add project path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, project_root)

from enhancer.api.genie_client import GenieConversationalClient
from enhancer.scoring.scorer import BenchmarkScorer
from enhancer.llm.llm import DatabricksLLMClient
from enhancer.utils.sql import SQLExecutor
from enhancer.utils.state import JobState

# COMMAND ----------

# Initialize state
state = JobState(catalog=catalog, schema=schema, spark=spark)
state.ensure_tables_exist()
state.start_stage(run_id, "score", {"loop_number": loop_number})

# COMMAND ----------

# Load benchmarks
if benchmarks_table:
    benchmarks_df = spark.table(benchmarks_table)
    benchmarks = [row.asDict() for row in benchmarks_df.collect()]
else:
    default_table = f"{catalog}.{schema}.benchmarks"
    benchmarks_df = spark.table(default_table)
    benchmarks = [row.asDict() for row in benchmarks_df.collect()]

print(f"Loaded {len(benchmarks)} benchmarks")

# COMMAND ----------

# Initialize clients
genie_client = GenieConversationalClient(databricks_host, databricks_token, space_id)
llm_client = DatabricksLLMClient(databricks_host, databricks_token, llm_endpoint)

sql_executor = None
if warehouse_id:
    sql_executor = SQLExecutor(databricks_host, databricks_token, warehouse_id)

scorer = BenchmarkScorer(genie_client, llm_client, sql_executor, {"question_timeout": 120})

print("✅ Clients initialized")

# COMMAND ----------

# Run scoring
print(f"\nScoring {len(benchmarks)} benchmarks...")
start_time = datetime.now()

results = scorer.score(benchmarks)

duration = (datetime.now() - start_time).total_seconds()

print(f"\n{'=' * 80}")
print(f"Score: {results['score']:.1%} ({results['passed']}/{results['total']})")
print(f"Duration: {duration:.1f}s")
print("=" * 80)

# COMMAND ----------

# Save results
state.save_benchmark_results(run_id, f"loop_{loop_number}", results["results"])

failed_results = [r for r in results["results"] if not r["passed"]]

output_data = {
    "score": results["score"],
    "passed": results["passed"],
    "failed": results["failed"],
    "total": results["total"],
    "duration_seconds": duration,
    "loop_number": loop_number,
    "failed_results": failed_results
}

state.complete_stage(run_id, "score", output_data)

print(f"✅ Results saved | Failed: {len(failed_results)}")

# COMMAND ----------

# Display results
display_data = [{"Question": r["question"][:60], "Status": "✅" if r["passed"] else "❌", "Category": r.get("failure_category", "")} for r in results["results"]]
display(spark.createDataFrame(display_data))

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"score": results["score"], "failed": results["failed"], "run_id": run_id}))
