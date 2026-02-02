# Genie Space Enhancement System - Architecture

## Overview

The Genie Space Enhancement System is an automated improvement tool for Databricks Genie Spaces. It uses benchmark-driven evaluation and LLM-powered enhancements to iteratively improve Genie Space accuracy.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  GENIE SPACE ENHANCEMENT SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Frontend   │───▶│   Backend    │───▶│  Enhancer    │     │
│  │  (Next.js)   │    │  (FastAPI)   │    │   (Core)     │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │             │
│         └────────────────────┴────────────────────┘             │
│                              │                                  │
│                              ▼                                  │
│                  ┌───────────────────────┐                     │
│                  │  Databricks Platform  │                     │
│                  │  - Genie Spaces       │                     │
│                  │  - SQL Warehouses     │                     │
│                  │  - LLM Endpoints      │                     │
│                  └───────────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
genie_enhancer/
├── .claude/                      # Claude Code configuration
│   ├── rules/                    # Project-specific rules
│   │   ├── README.md
│   │   ├── python-venv.md
│   │   └── app-permissions.md
│   └── skills/                   # Custom automation skills
├── backend/                      # FastAPI service
│   ├── middleware/               # Authentication middleware
│   │   └── auth.py
│   ├── services/                 # Backend services
│   │   ├── session_store.py     # SQLite session management
│   │   ├── job_manager.py       # Async job orchestration
│   │   ├── file_storage.py      # File upload handling
│   │   └── enhancement_tasks.py # Background task implementations
│   ├── main.py                   # FastAPI app entry point
│   └── requirements.txt          # Backend dependencies
├── frontend/                     # Next.js web interface
│   ├── app/                      # Next.js pages
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/               # React components
│   │   ├── Stepper.tsx
│   │   ├── SessionSidebar.tsx
│   │   ├── ConfigureStep.tsx
│   │   ├── ScoreStep.tsx
│   │   ├── PlanStep.tsx
│   │   └── ApplyStep.tsx
│   ├── lib/                      # Utilities and hooks
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── enhancer/                     # Core Python package
│   ├── api/                      # Genie API clients
│   │   ├── genie_client.py
│   │   ├── batch_genie_client.py
│   │   ├── space_api.py
│   │   └── space_cloner.py
│   ├── scoring/                  # Benchmark scoring
│   │   ├── scorer.py
│   │   ├── batch_scorer.py
│   │   └── benchmark_parser.py
│   ├── enhancement/              # Enhancement logic
│   │   ├── enhancer.py
│   │   ├── category_enhancer.py
│   │   ├── sequential_enhancer.py
│   │   └── applier.py
│   ├── llm/                      # LLM integration
│   │   └── llm.py
│   └── utils/                    # Utilities
│       ├── sql.py
│       ├── reporter.py
│       ├── delta_reporter.py
│       └── state.py
├── workflows/                    # Databricks job workflows
│   ├── 01_score.py
│   ├── 02_plan.py
│   ├── 03_apply.py
│   ├── 04_validate.py
│   └── orchestrator.py
├── prompts/                      # LLM prompts
├── benchmarks/                   # Test data
├── storage/                      # Runtime storage
│   ├── sessions.db              # SQLite database
│   └── uploads/                 # Uploaded files
├── output/                       # Generated outputs
├── enhancer.py                   # CLI entry point
├── app.yaml                      # Databricks Apps config
├── databricks.yml                # Asset bundle config
├── requirements.txt              # Root dependencies
├── ARCHITECTURE.md               # This file
├── CLAUDE.md                     # Claude Code guidance
└── README.md                     # User documentation
```

## Core Components

### 1. Frontend (Next.js/React)

**Purpose**: Multi-user web interface for interactive enhancement workflow

**Key Features**:
- 4-step wizard: Configure → Score → Plan & Apply → Validate
- Session management with sidebar
- Real-time job progress tracking
- Interactive configuration and results display

**Tech Stack**:
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS

### 2. Backend (FastAPI)

**Purpose**: API service for job orchestration and session management

**Key Features**:
- RESTful API endpoints for enhancement workflow
- Async background job processing
- SQLite-based session persistence
- File upload handling
- OAuth2 authentication (Databricks Apps)

**Key Endpoints**:
- `/api/sessions/*` - Session management
- `/api/jobs/score` - Start benchmark scoring
- `/api/jobs/plan` - Generate enhancement plan
- `/api/jobs/apply` - Apply fixes
- `/api/jobs/validate` - Validate improvements

### 3. Enhancer (Core Package)

**Purpose**: Core business logic for enhancement system

**Modules**:

**API Layer** (`enhancer/api/`):
- `genie_client.py`: Genie Conversational API wrapper
- `batch_genie_client.py`: Batch Genie query processing
- `space_api.py`: Genie Space CRUD operations
- `space_cloner.py`: Space cloning utilities

**Scoring Layer** (`enhancer/scoring/`):
- `scorer.py`: Sequential benchmark scorer
- `batch_scorer.py`: Batch benchmark scorer (13x faster)
- `benchmark_parser.py`: Benchmark file loading

**Enhancement Layer** (`enhancer/enhancement/`):
- `enhancer.py`: Legacy enhancement planner
- `category_enhancer.py`: Category-based enhancement (9 categories)
- `sequential_enhancer.py`: Sequential fix application
- `applier.py`: Batch fix application

**LLM Layer** (`enhancer/llm/`):
- `llm.py`: Databricks LLM client with structured output

**Utils Layer** (`enhancer/utils/`):
- `sql.py`: SQL Warehouse executor
- `state.py`: Job state management (Delta tables)
- `reporter.py`: Progress reporting
- `delta_reporter.py`: Delta table reporting

### 4. Workflows (Databricks Jobs)

**Purpose**: Automated enhancement pipeline for production use

**4-Stage Pipeline**:
1. **Score** - Evaluate current Genie Space performance
2. **Plan** - Generate ALL fixes using category-based analysis
3. **Apply** - Apply ALL fixes in ONE batch update
4. **Validate** - Re-score and check improvement

**Loop Behavior**: If target not reached, trigger another job run

## Data Flow

### Web Application Flow

```
User → Frontend → Backend API → Job Manager → Enhancement Tasks
                                      ↓
                               Session Store (SQLite)
                                      ↓
                            Databricks Platform (Genie/LLM)
```

### CLI Flow

```
User → CLI (enhancer.py) → Core Package → Databricks Platform
```

### Databricks Workflow Flow

```
Job Orchestrator → Stage 1 (Score) → Stage 2 (Plan) → Stage 3 (Apply) → Stage 4 (Validate)
                         ↓                 ↓                 ↓                 ↓
                    Delta Tables (State Persistence & Visibility)
```

## Enhancement Categories

The system uses a 9-category enhancement approach:

1. **instruction_fix** - AI guidance improvements
2. **join_specs_delete** - Remove incorrect joins
3. **join_specs_add** - Add missing joins
4. **sql_snippets_delete** - Remove incorrect SQL expressions
5. **sql_snippets_add** - Add missing SQL expressions
6. **metadata_delete** - Remove incorrect table metadata
7. **metadata_add** - Add missing table metadata
8. **sample_queries_delete** - Remove incorrect examples
9. **sample_queries_add** - Add missing examples

## Key Patterns

### 1. Batch Processing

- **Batch Genie Queries**: Process multiple questions concurrently
- **Batch LLM Calls**: Chunk requests to respect token limits
- **Batch Fix Application**: Apply all fixes in one API call

### 2. Async Job Processing

- Jobs run in ThreadPoolExecutor
- Progress tracking via SQLite
- Non-blocking API responses
- Polling for results

### 3. Session Management

- SQLite for persistence
- Session-scoped storage
- Job history tracking
- State restoration

## Performance

| Operation | Mode | Time (20 benchmarks) | Speedup |
|-----------|------|---------------------|---------|
| Scoring | Sequential | ~7 min | 1x |
| Scoring | Parallel | ~1.5 min | 4.6x |
| Scoring | **Batch** | **~30s** | **13x** |

## Deployment

### Databricks App Deployment

```bash
databricks bundle deploy
```

**Runtime**: Python app running on Databricks Apps infrastructure
**Port**: 8000 (uvicorn)
**Access**: `https://<workspace-url>/apps/genie-enhancer`

### Local Development

```bash
# Backend
.venv/bin/python -m uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev
```

## Configuration

### Environment Variables

**Required**:
- `DATABRICKS_HOST`: Workspace URL
- `DATABRICKS_TOKEN`: Access token
- `DATABRICKS_HTTP_PATH`: SQL Warehouse path

**Optional**:
- `FRONTEND_EXPORT_DIR`: Frontend build location (default: frontend/out)

### Secrets

Stored in Databricks secrets scope `genie-enhancement`:
- `service-token`: App service principal token
- `sql-warehouse-http-path`: SQL Warehouse HTTP path

## Security

- OAuth2 authentication (Databricks Apps)
- Token-based API access
- Session isolation
- Input validation (Pydantic models)
- SQL injection prevention (parameterized queries)

## Extensibility

### Adding New Enhancement Categories

1. Update `CategoryEnhancer` in `enhancer/enhancement/category_enhancer.py`
2. Add prompt template in `prompts/`
3. Update `BatchApplier` to handle new category

### Adding New Workflow Steps

1. Create task function in `backend/services/enhancement_tasks.py`
2. Add API endpoint in `backend/main.py`
3. Create React component in `frontend/components/`
4. Update workflow state machine in `frontend/app/page.tsx`

### Custom Scoring Metrics

1. Extend `BenchmarkScorer` in `enhancer/scoring/scorer.py`
2. Update result aggregation logic
3. Modify frontend display components

## Monitoring

- Job status tracking via API
- SQLite-based audit trail
- Progress callbacks for long-running tasks
- Error logging and reporting

## Known Limitations

- SQLite session store (single-instance)
- No distributed job processing
- File uploads stored locally
- Session cleanup requires manual intervention
