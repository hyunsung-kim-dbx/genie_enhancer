# Genie Space Enhancement System v3.0

Automated improvement system for Databricks Genie Spaces using benchmark-driven evaluation and LLM-powered enhancements.

## What It Does

1. **Score** - Evaluate Genie Space against Q&A benchmarks (⚡ 13x faster with batch mode)
2. **Plan** - Analyze failures and generate ALL fixes at once using category-based approach
3. **Apply** - Apply ALL fixes in ONE batch update
4. **Validate** - Re-score and check improvement

## 🚀 Quick Start

### Web UI (Recommended)

```bash
# Start backend
.venv/bin/python -m uvicorn backend.main:app --reload --port 8000

# Start frontend (in separate terminal)
cd frontend && npm run dev
```

Access at: `http://localhost:3000`

### CLI

```bash
# Full workflow
.venv/bin/python enhancer.py score --host $HOST --token $TOKEN --space-id $SPACE_ID --warehouse-id $WAREHOUSE_ID --benchmarks benchmarks.json
.venv/bin/python enhancer.py plan --host $HOST --token $TOKEN --space-id $SPACE_ID --failed-results output/score_results.json
.venv/bin/python enhancer.py apply --host $HOST --token $TOKEN --space-id $SPACE_ID --warehouse-id $WAREHOUSE_ID --plan output/enhancement_plan.json
.venv/bin/python enhancer.py validate --host $HOST --token $TOKEN --space-id $SPACE_ID --warehouse-id $WAREHOUSE_ID --benchmarks benchmarks.json
```

## 📊 Performance

| Scoring Mode | 20 Benchmarks | Speedup |
|--------------|--------------|---------|
| Sequential (old) | ~7 min | 1x |
| Parallel (v2) | ~1.5 min | 4.6x |
| **Batch (v3)** | **~30s** | **13x** |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         GENIE ENHANCEMENT SYSTEM             │
├─────────────────────────────────────────────┤
│                                              │
│  Frontend (Next.js) → Backend (FastAPI)     │
│           ↓                ↓                 │
│      Enhancer Core Package                  │
│           ↓                                  │
│   Databricks Platform                       │
│   - Genie Spaces                            │
│   - SQL Warehouses                          │
│   - LLM Endpoints                           │
│                                              │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
genie_enhancer/
├── backend/              # FastAPI service
│   ├── main.py          # API entry point
│   ├── middleware/      # Authentication
│   └── services/        # Job management, storage
├── frontend/            # Next.js web interface
│   ├── app/            # Pages
│   └── components/     # React components
├── enhancer/           # Core Python package
│   ├── api/           # Genie API clients
│   ├── scoring/       # Benchmark evaluation
│   ├── enhancement/   # Fix generation & application
│   ├── llm/          # LLM integration
│   └── utils/        # SQL, state, reporting
├── workflows/         # Databricks job workflows
├── prompts/          # LLM prompt templates
└── enhancer.py       # CLI entry point
```

## 🔧 Installation

```bash
# Create virtual environment
python3 -m venv .venv

# Install dependencies
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install
```

## 🌐 Web UI Features

- **Session Management**: Multiple enhancement sessions with history
- **4-Step Workflow**: Configure → Score → Plan & Apply → Validate
- **Real-time Progress**: Job status tracking and progress indicators
- **Interactive Results**: Visual score comparisons and improvement metrics
- **File Upload**: Upload benchmark files directly through UI

## 💻 CLI Features

- **Modular Commands**: Run individual steps or full pipeline
- **Flexible Configuration**: Command-line options or environment variables
- **JSON Output**: Structured results for automation
- **Dry Run Mode**: Preview changes without applying

## 📝 Enhancement Categories

The system uses 9 fix categories:

1. **instruction_fix** - AI guidance improvements
2. **join_specs_delete/add** - Join relationship fixes
3. **sql_snippets_delete/add** - SQL expression fixes
4. **metadata_delete/add** - Table metadata fixes
5. **sample_queries_delete/add** - Example query fixes

## 🚢 Deployment

### Databricks Apps

```bash
# Build frontend
cd frontend && npm run build

# Deploy bundle
databricks bundle deploy
```

Access at: `https://<workspace-url>/apps/genie-enhancer`

### Local Development

```bash
# Terminal 1: Backend
.venv/bin/python -m uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

## 🔐 Configuration

### Environment Variables

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/...
```

### Secrets (for Databricks Apps)

```bash
# Create scope
databricks secrets create-scope genie-enhancement

# Add secrets
databricks secrets put-secret genie-enhancement service-token
databricks secrets put-secret genie-enhancement sql-warehouse-http-path
```

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system architecture
- [CLAUDE.md](CLAUDE.md) - Development guidance
- [.claude/rules/](.claude/rules/) - Project-specific rules

## 🛠️ Development

### Project Rules

This project follows specific rules enforced by Claude Code:

- **Always use `.venv/bin/python`** for Python commands (never `python` or `python3`)
- **Never delete the Databricks app** - only deploy updates
- See `.claude/rules/` for complete guidelines

### Adding Features

1. **New Enhancement Category**: Update `CategoryEnhancer` and prompts
2. **New Frontend Step**: Add component and update workflow
3. **New API Endpoint**: Add to `backend/main.py` and create task function

## 🧪 Testing

Currently manual testing through:
- CLI commands
- Web UI workflow
- Databricks job execution

## 📊 Example Workflow

```bash
# 1. Score current state
.venv/bin/python enhancer.py score \
  --host https://workspace.databricks.com \
  --token $TOKEN \
  --space-id abc123 \
  --warehouse-id xyz789 \
  --benchmarks benchmarks/kpi_benchmark.json

# Output: Score: 65.0% (13/20)

# 2. Generate enhancement plan
.venv/bin/python enhancer.py plan \
  --host https://workspace.databricks.com \
  --token $TOKEN \
  --space-id abc123 \
  --failed-results output/score_results.json

# Output: Generated 24 fixes across 6 categories

# 3. Apply fixes
.venv/bin/python enhancer.py apply \
  --host https://workspace.databricks.com \
  --token $TOKEN \
  --space-id abc123 \
  --warehouse-id xyz789 \
  --plan output/enhancement_plan.json

# Output: Applied 24 fixes successfully

# 4. Validate improvements
.venv/bin/python enhancer.py validate \
  --host https://workspace.databricks.com \
  --token $TOKEN \
  --space-id abc123 \
  --warehouse-id xyz789 \
  --benchmarks benchmarks/kpi_benchmark.json \
  --initial-score 0.65 \
  --target-score 0.90

# Output: New Score: 85.0% (17/20), Improvement: +20.0%
```

## 🤝 Contributing

1. Follow `.claude/rules/` guidelines
2. Use `.venv/bin/python` for all Python commands
3. Test both CLI and Web UI before committing
4. Update documentation for new features

## 📄 License

Internal tool for Databricks Genie Space enhancement.

## 🆘 Support

For issues or questions:
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system details
- Review [CLAUDE.md](CLAUDE.md) for development guidance
- Check `.claude/rules/` for project standards
