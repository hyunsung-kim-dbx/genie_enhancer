# Genie Space Enhancement System v3.0

Automated improvement system for Databricks Genie Spaces using benchmark-driven evaluation and LLM-powered enhancements.

## What It Does

1. **Score** - Evaluate Genie Space against Q&A benchmarks
2. **Plan** - Analyze failures, generate ALL fixes at once
3. **Apply** - Apply ALL fixes in ONE batch update
4. **Validate** - Re-score and check improvement

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              4-STAGE DATABRICKS JOB PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  │  Stage 1  │───▶│  Stage 2  │───▶│  Stage 3  │───▶│  Stage 4  │
│  │   SCORE   │    │   PLAN    │    │   APPLY   │    │ VALIDATE  │
│  └───────────┘    └───────────┘    └───────────┘    └───────────┘
│       │                │                │                │
│       ▼                ▼                ▼                ▼
│  ┌─────────────────────────────────────────────────────────────┐
│  │              DELTA TABLES (State & Visibility)              │
│  └─────────────────────────────────────────────────────────────┘
│                                                                 │
│  If target not reached → Trigger new job run (Loop N+1)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
genie_enhancer/
├── lib/                     # Python library
│   ├── genie_client.py      # Genie Conversational API
│   ├── space_api.py         # Genie Space import/export
│   ├── scorer.py            # Benchmark scoring
│   ├── enhancer.py          # Fix generation (batch)
│   ├── applier.py           # Fix application (batch)
│   ├── llm.py               # Databricks LLM client
│   ├── sql.py               # SQL executor
│   └── state.py             # Job state (Delta)
├── workflows/               # Databricks Workflows
│   ├── 01_score.py          # Stage 1: Score benchmarks
│   ├── 02_plan.py           # Stage 2: Generate fixes
│   ├── 03_apply.py          # Stage 3: Apply ALL fixes
│   ├── 04_validate.py       # Stage 4: Validate results
│   └── orchestrator.py      # Job coordinator
├── app/                     # Databricks App
│   └── main.py              # Streamlit UI
├── prompts/                 # LLM prompts
├── benchmarks/              # Test data
├── config/                  # Configuration
│   ├── job.yaml             # Job definition
│   └── app.yaml             # App config
└── docs/                    # Documentation
```

## Quick Start

### 1. Upload to Databricks

```bash
databricks workspace import-dir genie_enhancer /Workspace/Users/your.email/genie_enhancer
```

### 2. Run Orchestrator

Open `workflows/orchestrator.py` and set:
- `space_id`: Your Genie Space ID
- `databricks_token`: Your token (or use secrets)
- `warehouse_id`: SQL Warehouse for metric views
- `target_score`: Target benchmark pass rate (e.g., 0.90)

Choose mode:
- `run_inline`: Run all stages in this notebook
- `create_job`: Create Databricks Job only
- `create_and_run`: Create and start job

### 3. Monitor Progress

View state in Delta tables:
```sql
-- Job runs
SELECT * FROM sandbox.genie_enhancement.genie_job_runs;

-- Stage results
SELECT * FROM sandbox.genie_enhancement.genie_job_stage_results
WHERE run_id = 'your-run-id';
```

## Key Concepts

### Batch Apply (Not Sequential)

All fixes are applied in ONE Genie Space API call:
- Faster execution
- Single point of failure
- Clearer before/after comparison

### Multi-Loop Design

Each job run = one loop. If target not reached:
1. Job completes with status `NEEDS_ANOTHER_LOOP`
2. User (or automation) triggers new job run
3. New loop starts with Loop N+1

### Four Fix Categories

1. **Metric Views** - Create UC metric views for complex aggregations
2. **Metadata** - Table/column descriptions, synonyms
3. **Sample Queries** - Parameterized query templates
4. **Instructions** - Text instructions for Genie

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `space_id` | Genie Space ID | Required |
| `target_score` | Target pass rate (0.0-1.0) | 0.90 |
| `llm_endpoint` | LLM endpoint name | llama-3.1-70b |
| `warehouse_id` | SQL Warehouse (for metric views) | Optional |
| `catalog` | Unity Catalog for state | sandbox |
| `schema` | Schema for state tables | genie_enhancement |

## License

Internal Databricks tool for Genie Space enhancement.
