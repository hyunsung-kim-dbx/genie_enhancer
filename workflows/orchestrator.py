# Databricks notebook source
# MAGIC %md
# MAGIC # Enhancement Orchestrator
# MAGIC
# MAGIC Creates and runs a 4-stage Databricks Job:
# MAGIC 1. **Score** - Evaluate current state
# MAGIC 2. **Plan** - Generate ALL fixes
# MAGIC 3. **Apply** - Apply ALL fixes at once
# MAGIC 4. **Validate** - Check results
# MAGIC
# MAGIC If target not reached, trigger another job run (new loop).

# COMMAND ----------

dbutils.widgets.text("space_id", "", "Genie Space ID")
dbutils.widgets.text("databricks_host", "", "Databricks Host")
dbutils.widgets.text("databricks_token", "", "Databricks Token")
dbutils.widgets.text("warehouse_id", "", "SQL Warehouse ID")
dbutils.widgets.text("llm_endpoint", "databricks-gpt-5-2", "LLM Endpoint")
dbutils.widgets.text("catalog", "sandbox", "Catalog")
dbutils.widgets.text("schema", "genie_enhancement", "Schema")
dbutils.widgets.text("benchmarks_table", "", "Benchmarks Table")
dbutils.widgets.text("target_score", "0.90", "Target Score")
dbutils.widgets.text("cluster_id", "", "Cluster ID")
dbutils.widgets.dropdown("mode", "create_and_run", ["create_job", "run_inline", "create_and_run"], "Mode")

# COMMAND ----------

import json
import uuid
import requests
from datetime import datetime
import sys

# Parameters
space_id = dbutils.widgets.get("space_id")
databricks_host = dbutils.widgets.get("databricks_host") or spark.conf.get("spark.databricks.workspaceUrl", "")
databricks_token = dbutils.widgets.get("databricks_token")
warehouse_id = dbutils.widgets.get("warehouse_id")
llm_endpoint = dbutils.widgets.get("llm_endpoint")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
benchmarks_table = dbutils.widgets.get("benchmarks_table")
target_score = dbutils.widgets.get("target_score")
cluster_id = dbutils.widgets.get("cluster_id")
mode = dbutils.widgets.get("mode")

# Token from secrets if not provided
if not databricks_token:
    try:
        databricks_token = dbutils.secrets.get("genie-enhancement", "databricks-token")
    except:
        raise ValueError("databricks_token required")

print("=" * 80)
print("GENIE ENHANCEMENT ORCHESTRATOR")
print("=" * 80)
print(f"Space ID: {space_id}")
print(f"Target Score: {target_score}")
print(f"Mode: {mode}")

# COMMAND ----------

# Add project path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
workflows_dir = "/Workspace" + "/".join(notebook_path.split("/")[:-1])
project_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, project_root)

from enhancer.utils.state import JobState

# Initialize state
state = JobState(catalog=catalog, schema=schema, spark=spark)
state.ensure_tables_exist()

# Create run
run_id = state.create_run(space_id, {
    "target_score": target_score,
    "llm_endpoint": llm_endpoint,
    "warehouse_id": warehouse_id
})
loop_number = 1

print(f"\n✅ Created Run: {run_id}")

# COMMAND ----------

# Common parameters
common_params = {
    "run_id": run_id,
    "loop_number": str(loop_number),
    "space_id": space_id,
    "databricks_host": databricks_host,
    "databricks_token": databricks_token,
    "warehouse_id": warehouse_id,
    "llm_endpoint": llm_endpoint,
    "catalog": catalog,
    "schema": schema,
    "benchmarks_table": benchmarks_table,
    "target_score": target_score
}

workflows = {
    "score": f"{workflows_dir}/01_score",
    "plan": f"{workflows_dir}/02_plan",
    "apply": f"{workflows_dir}/03_apply",
    "validate": f"{workflows_dir}/04_validate"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Job Definition

# COMMAND ----------

if mode in ["create_job", "create_and_run"]:
    job_def = {
        "name": f"Genie Enhancement - {space_id[:8]} - Loop {loop_number}",
        "tasks": [
            {
                "task_key": "01_score",
                "notebook_task": {"notebook_path": workflows["score"], "base_parameters": common_params},
                "existing_cluster_id": cluster_id if cluster_id else None,
                "timeout_seconds": 3600
            },
            {
                "task_key": "02_plan",
                "depends_on": [{"task_key": "01_score"}],
                "notebook_task": {"notebook_path": workflows["plan"], "base_parameters": common_params},
                "existing_cluster_id": cluster_id if cluster_id else None,
                "timeout_seconds": 7200
            },
            {
                "task_key": "03_apply",
                "depends_on": [{"task_key": "02_plan"}],
                "notebook_task": {"notebook_path": workflows["apply"], "base_parameters": common_params},
                "existing_cluster_id": cluster_id if cluster_id else None,
                "timeout_seconds": 3600
            },
            {
                "task_key": "04_validate",
                "depends_on": [{"task_key": "03_apply"}],
                "notebook_task": {"notebook_path": workflows["validate"], "base_parameters": {**common_params, "indexing_wait": "60"}},
                "existing_cluster_id": cluster_id if cluster_id else None,
                "timeout_seconds": 3600
            }
        ],
        "format": "MULTI_TASK",
        "max_concurrent_runs": 1,
        "tags": {"project": "genie-enhancement", "run_id": run_id, "loop": str(loop_number)}
    }

    # Use serverless compute if no existing cluster specified
    if not cluster_id:
        for task in job_def["tasks"]:
            del task["existing_cluster_id"]
            task["environment_key"] = "Default"

    # Create job
    response = requests.post(
        f"https://{databricks_host}/api/2.1/jobs/create",
        headers={"Authorization": f"Bearer {databricks_token}"},
        json=job_def
    )

    if response.status_code == 200:
        job_id = response.json()["job_id"]
        print(f"\n✅ Job Created: {job_id}")
        print(f"   View: https://{databricks_host}/#job/{job_id}")

        if mode == "create_and_run":
            run_response = requests.post(
                f"https://{databricks_host}/api/2.1/jobs/run-now",
                headers={"Authorization": f"Bearer {databricks_token}"},
                json={"job_id": job_id}
            )
            if run_response.status_code == 200:
                job_run_id = run_response.json()["run_id"]
                print(f"\n🚀 Job Started: {job_run_id}")
                print(f"   View: https://{databricks_host}/#job/{job_id}/run/{job_run_id}")
    else:
        print(f"❌ Failed to create job: {response.text}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Inline Mode

# COMMAND ----------

if mode == "run_inline":
    print("\n🔵 Running 4-stage pipeline inline...")

    # Stage 1
    print("\n--- Stage 1: Score ---")
    r1 = dbutils.notebook.run(workflows["score"], 3600, common_params)
    print(f"Result: {r1}")

    # Stage 2
    print("\n--- Stage 2: Plan ---")
    r2 = dbutils.notebook.run(workflows["plan"], 7200, common_params)
    print(f"Result: {r2}")

    # Stage 3
    print("\n--- Stage 3: Apply ---")
    r3 = dbutils.notebook.run(workflows["apply"], 3600, common_params)
    print(f"Result: {r3}")

    # Stage 4
    print("\n--- Stage 4: Validate ---")
    r4 = dbutils.notebook.run(workflows["validate"], 3600, {**common_params, "indexing_wait": "60"})
    result = json.loads(r4)
    print(f"Result: {r4}")

    # Check if another loop needed
    print(f"\n{'=' * 80}")
    if result.get("target_reached"):
        print(f"🎉 TARGET REACHED! Final Score: {result['final_score']:.1%}")
    else:
        print(f"⚠️ Target not reached. Score: {result['final_score']:.1%}")
        print(f"   Run orchestrator again with loop_number={result['next_loop_number']}")

# COMMAND ----------

# Show recent runs
runs_df = spark.sql(f"""
    SELECT run_id, space_id, status, current_stage, created_at
    FROM {state._get_table('runs')}
    ORDER BY created_at DESC
    LIMIT 5
""")
display(runs_df)
