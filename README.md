# Genie Space Enhancement System v3.0

Automated improvement system for Databricks Genie Spaces using benchmark-driven evaluation and LLM-powered enhancements.

## What It Does

1. **Score** - Evaluate Genie Space against Q&A benchmarks ⚡ **NEW: 13x faster with batch scoring**
2. **Plan** - Analyze failures, generate ALL fixes at once (domain-agnostic pattern learning)
3. **Apply** - Apply ALL fixes in ONE batch update
4. **Validate** - Re-score and check improvement

## 🚀 Performance

| Scoring Mode | 20 Benchmarks | Speedup |
|--------------|--------------|---------|
| Sequential (old) | ~7 min | 1x |
| Parallel (v2) | ~1.5 min | 4.6x |
| **Batch (v3)** | **~30s** | **13x** |

Batch mode includes safety measures:
- ✅ Rate limiting (semaphore)
- ✅ Retry with exponential backoff
- ✅ Circuit breaker (auto-fallback to sequential)
- ✅ Per-query timeout handling
- ✅ Graceful degradation

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

### 1. Basic Usage (Batch Mode - Recommended)

```bash
python run_enhancement.py \
  --host workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $GENIE_SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/kpi_benchmark.json
```

**Options:**
- `--genie-concurrent N` - Max concurrent Genie calls (default: 3)
- `--no-batch` - Use sequential mode instead
- `--auto-promote` - Auto-promote on success
- See `docs/USAGE_GUIDE.md` for all options

### 2. Upload to Databricks

```bash
databricks workspace import-dir genie_enhancer /Workspace/Users/your.email/genie_enhancer
```

### 3. Run Orchestrator

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

## Documentation

### Quick Start Guides
- **[USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** - Complete usage guide with examples
- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Deployment instructions

### System Architecture
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - V2 architecture (interactive workflow)
- **[ARCHITECTURE_V3_ENHANCEMENTS.md](docs/ARCHITECTURE_V3_ENHANCEMENTS.md)** - V3 improvements (batch, UI)

### Features & Integration
- **[BATCH_SCORING.md](docs/BATCH_SCORING.md)** - Batch scoring system (13x faster)
- **[GENERALIZATION_CHANGES.md](docs/GENERALIZATION_CHANGES.md)** - Domain-agnostic pattern learning
- **[STREAMLIT_UI.md](docs/STREAMLIT_UI.md)** - Enhanced UI visual guide
- **[UI_INTEGRATION.md](docs/UI_INTEGRATION.md)** - UI integration guide
- **[INTEGRATION_SUMMARY.md](docs/INTEGRATION_SUMMARY.md)** - Complete integration summary

### API References
- **[Genie_Conversational_API.md](docs/Genie_Conversational_API.md)** - Conversational API
- **[Databricks_Genie_Space_Import_Export_APIs.md](docs/Databricks_Genie_Space_Import_Export_APIs.md)** - Import/export APIs
- **[Genie_Space_API_Reference.md](docs/Genie_Space_API_Reference.md)** - API reference

### Best Practices
- **[Genie_Space_Best_Practices.md](docs/Genie_Space_Best_Practices.md)** - Genie Space best practices

### Historical Documentation
- **[docs/archive/](docs/archive/)** - Archived documentation (see INDEX.md)

## License

Internal Databricks tool for Genie Space enhancement.
