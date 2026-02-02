# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Genie Space Enhancement System is an LLM-powered tool that automatically improves Databricks Genie space accuracy through benchmark-driven evaluation and AI-generated fixes. It uses a 4-stage workflow (Score → Plan → Apply → Validate) with both web UI and CLI interfaces.

## Project Rules

**IMPORTANT:** This project has specific rules that must be followed. These rules are located in `.claude/rules/` directory:

- **`.claude/rules/python-venv.md`**: Python virtual environment usage (CRITICAL - always use `.venv/bin/python`)
- **`.claude/rules/app-permissions.md`**: ⚠️ App service principal permissions (CRITICAL - never delete app)
- **`.claude/rules/README.md`**: Overview of all rules and how they work

These rules override default behavior and enforce project-specific standards. Always consult the rules when:
- Suggesting Python commands
- Writing scripts
- Running tests
- Installing dependencies
- **Working with app deployment or permissions** ⚠️

## Development Commands

### Environment Setup

```bash
# Always use the virtual environment
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r backend/requirements.txt

# Frontend setup
cd frontend && npm install
```

### Local Development

```bash
# Run backend (FastAPI)
.venv/bin/python -m uvicorn backend.main:app --reload --port 8000

# Run frontend (Next.js) - in separate terminal
cd frontend && npm run dev
```

### CLI Commands

```bash
# Score benchmarks
.venv/bin/python enhancer.py score \
  --host https://your-workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/benchmarks.json

# Generate enhancement plan
.venv/bin/python enhancer.py plan \
  --host https://your-workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $SPACE_ID \
  --failed-results output/score_results.json

# Apply fixes
.venv/bin/python enhancer.py apply \
  --host https://your-workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --plan output/enhancement_plan.json

# Validate improvements
.venv/bin/python enhancer.py validate \
  --host https://your-workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/benchmarks.json \
  --initial-score 0.65 \
  --target-score 0.90
```

### Deployment

```bash
# Deploy to Databricks Apps
databricks bundle deploy

# Build frontend for production
cd frontend && npm run build
```

## Architecture Overview

### Directory Structure

```
genie_enhancer/
├── backend/              # FastAPI service (port 8000)
│   ├── main.py          # API entry point
│   ├── middleware/      # Authentication
│   └── services/        # Job management, storage
├── frontend/            # Next.js UI (port 3000)
│   ├── app/            # Pages
│   └── components/     # React components
├── enhancer/           # Core Python package
│   ├── api/           # Genie API clients
│   ├── scoring/       # Benchmark evaluation
│   ├── enhancement/   # Fix generation & application
│   ├── llm/          # LLM integration
│   └── utils/        # SQL, state, reporting
├── workflows/         # Databricks job notebooks
└── prompts/          # LLM prompt templates
```

### High-Level Data Flow

```
User → Frontend → Backend API → Job Manager → Enhancement Tasks
                                     ↓
                              Session Store (SQLite)
                                     ↓
                          Databricks Platform (Genie/LLM)
```

## Core Components

### 1. Backend (FastAPI)

Location: `backend/`

**Services**:
- `session_store.py`: SQLite-based session management
- `job_manager.py`: Async background job orchestration
- `file_storage.py`: File upload handling
- `enhancement_tasks.py`: Task implementations (score, plan, apply, validate)

**Key Endpoints**:
- `/api/sessions/*` - Session CRUD
- `/api/jobs/score` - Start scoring job
- `/api/jobs/plan` - Start planning job
- `/api/jobs/apply` - Start apply job
- `/api/jobs/validate` - Start validation job

### 2. Frontend (Next.js)

Location: `frontend/`

**Components**:
- `Stepper.tsx`: Step indicator
- `SessionSidebar.tsx`: Session management
- `ConfigureStep.tsx`: Workspace configuration
- `ScoreStep.tsx`: Benchmark scoring
- `PlanStep.tsx`: Plan generation & application
- `ApplyStep.tsx`: Results validation

### 3. Core Package (enhancer/)

**API Layer** (`enhancer/api/`):
- Genie Conversational API client
- Genie Space CRUD operations
- Space cloning utilities

**Scoring Layer** (`enhancer/scoring/`):
- Sequential and batch benchmark scoring
- 13x faster batch mode

**Enhancement Layer** (`enhancer/enhancement/`):
- Category-based enhancement (9 categories)
- Batch fix application
- Sequential fix application (with rollback)

**LLM Layer** (`enhancer/llm/`):
- Databricks Foundation Model client
- Structured output support

**Utils Layer** (`enhancer/utils/`):
- SQL Warehouse executor
- Delta table state management
- Progress reporting

### 4. Workflows (Databricks Jobs)

Location: `workflows/`

4-stage pipeline for automated enhancement:
1. `01_score.py` - Benchmark evaluation
2. `02_plan.py` - Fix generation
3. `03_apply.py` - Batch fix application
4. `04_validate.py` - Re-scoring & validation

## Important Patterns

### Virtual Environment Requirement

**ALWAYS use `.venv/bin/python` instead of `python` or `python3`**. This is enforced by `.claude/rules/python-venv.md`. See the rules file for complete usage guidelines and examples.

### Enhancement Categories

The system uses 9 fix categories:
1. instruction_fix
2. join_specs_delete/add
3. sql_snippets_delete/add
4. metadata_delete/add
5. sample_queries_delete/add

### Batch Processing

- Batch Genie queries for 13x speedup
- Batch LLM evaluation
- Single API call for all fixes

### Async Job Processing

- Jobs run in ThreadPoolExecutor
- Progress stored in SQLite
- Polling-based status checks
- Non-blocking API responses

## Code Organization Standards

**Project Rules:** See `.claude/rules/` for detailed project-specific rules.

Key standards:
1. All markdown documentation (except README.md, ARCHITECTURE.md, CLAUDE.md) goes in `docs/` directory
2. **Always use `.venv/bin/python` for Python commands** (see `.claude/rules/python-venv.md`)
3. No automated test suite yet - validation through CLI commands

## Key Integration Points

### Databricks Foundation Models

- Uses serving endpoints for LLM access
- Supports structured output via Pydantic models
- Temperature: 0.1 (deterministic)
- Max tokens: 4000 (configurable)

### Genie Conversational API

- Complete API wrapper in `enhancer/api/genie_client.py`
- Batch processing support in `enhancer/api/batch_genie_client.py`
- Rate limiting and retry logic

### Genie Space API

Complete API wrapper in `enhancer/api/space_api.py`:
- `export_space()`: Get space configuration
- `update_space()`: Apply fixes
- Error handling and validation

## Common Workflows

### Adding New Fix Categories

1. Update `CategoryEnhancer` in `enhancer/enhancement/category_enhancer.py`
2. Add prompt template in `prompts/`
3. Update `BatchApplier` to handle new category
4. Test with CLI before deploying

### Modifying Frontend Steps

1. Update component in `frontend/components/`
2. Update state management in `frontend/app/page.tsx`
3. Test with `npm run dev`
4. Build with `npm run build`

### Adding Backend Endpoints

1. Add request/response models (Pydantic)
2. Create endpoint in `backend/main.py`
3. Add task function in `backend/services/enhancement_tasks.py`
4. Test with FastAPI docs at `/docs`

## Output Files

All generated files go to `output/` directory:
- `score_results.json`: Scoring results
- `enhancement_plan.json`: Generated fix plan
- `validation_results.json`: Validation results

## Configuration & Environment

### Environment Variables

Required:
- `DATABRICKS_HOST`: Workspace URL
- `DATABRICKS_TOKEN`: Personal access token
- `DATABRICKS_HTTP_PATH`: SQL Warehouse path

Optional:
- `FRONTEND_EXPORT_DIR`: Frontend build location (default: frontend/out)

### Storage Configuration

**File Storage:** Local file system (`storage/uploads/`)
- Session files organized by session ID
- Auto-cleanup not implemented

**Session Storage:** SQLite database (`storage/sessions.db`)
- Persistent session and job tracking
- Automatically created on first run

### App Deployment Authentication

For app deployment, credentials come from Databricks secrets:

**Secrets Scope:** `genie-enhancement`

**Required Secrets:**
- `service-token`: Databricks access token
- `sql-warehouse-http-path`: SQL Warehouse HTTP path

**Setup:**
```bash
# Create secrets scope (if not exists)
databricks secrets create-scope genie-enhancement

# Add service token
databricks secrets put-secret genie-enhancement service-token

# Add SQL warehouse path
databricks secrets put-secret genie-enhancement sql-warehouse-http-path
```

## Testing

Currently manual testing through:
- CLI commands (scoring, planning, applying, validating)
- Web UI workflow
- Databricks job execution

To add automated tests:
- Use pytest framework
- Place tests in `tests/` directory
- Run with `.venv/bin/python -m pytest`

## Performance Metrics

| Scoring Mode | 20 Benchmarks | Speedup |
|--------------|--------------|---------|
| Sequential | ~7 min | 1x |
| Parallel | ~1.5 min | 4.6x |
| **Batch** | **~30s** | **13x** |

## Deployment Checklist

Before deploying to Databricks Apps:

1. ✅ Build frontend: `cd frontend && npm run build`
2. ✅ Test backend locally: `.venv/bin/python -m uvicorn backend.main:app`
3. ✅ Verify secrets exist in `genie-enhancement` scope
4. ✅ Update `databricks.yml` if needed
5. ✅ Run `databricks bundle deploy`
6. ✅ Check app logs: `databricks apps logs genie-enhancer`

## Troubleshooting

**Frontend not loading:**
- Check `frontend/out/` exists (run `npm run build`)
- Verify `FRONTEND_EXPORT_DIR` in `app.yaml`
- Check backend logs for static file errors

**Job stuck in "running":**
- Check job status via API: `/api/jobs/{job_id}`
- View backend logs
- Verify Databricks credentials are valid

**Import errors:**
- Ensure `.venv/bin/python` is used
- Check all dependencies installed
- Verify Python path includes project root

## Additional Resources

- ARCHITECTURE.md: Detailed system architecture
- README.md: User-facing documentation
- `.claude/rules/`: Project-specific rules
