# deploy-local Skill

Deploy the Genie Lamp Agent locally for development and testing.

## Overview

The `deploy-local` skill automates the complete local development setup for the Genie Lamp Agent. It:
- Checks prerequisites (Python, Node.js, npm, venv)
- Installs backend and frontend dependencies
- Validates environment configuration
- Starts both backend (FastAPI) and frontend (Next.js) servers
- Provides access URLs and instructions

## When to Use

Use this skill when you want to:
- Run the app locally for development
- Test changes before deploying to Databricks
- Debug backend or frontend issues
- Run demos on your local machine

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm
- Virtual environment at `.venv/`
- `.env` file with `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

## Quick Start

**From Claude Code:**
```
/deploy-local
```

**From Command Line:**
```bash
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py
```

## Options

```bash
# Custom ports
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py \
  --backend-port 8080 \
  --frontend-port 3001

# Skip dependency installation (faster for repeated runs)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-install

# Backend only (useful for API development)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --backend-only

# Frontend only (if backend is running elsewhere)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --frontend-only
```

## Access URLs

After successful deployment:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (Redoc)**: http://localhost:8000/redoc

## What It Does

1. **Prerequisites Check**
   - Verifies Python 3.8+, Node.js 18+, npm
   - Checks virtual environment exists
   - Validates project structure

2. **Environment Validation**
   - Checks `.env` file exists
   - Verifies required variables are set (DATABRICKS_HOST, DATABRICKS_TOKEN)

3. **Backend Setup**
   - Installs dependencies from `backend/requirements.txt`
   - Uses project virtual environment (`.venv/bin/python`)

4. **Frontend Setup**
   - Runs `npm install` in `frontend/` directory
   - Installs all required Node.js packages

5. **Server Startup**
   - Starts FastAPI backend with uvicorn (hot reload enabled)
   - Starts Next.js frontend dev server (hot reload enabled)
   - Both servers run concurrently

6. **Access Information**
   - Displays URLs for frontend and backend
   - Shows API documentation links
   - Provides stop instructions

## Development Workflow

1. **Start Local Deployment**
   ```bash
   /deploy-local
   ```

2. **Make Code Changes**
   - Edit backend files (FastAPI auto-reloads)
   - Edit frontend files (Next.js hot-reloads)

3. **Test Changes**
   - Access frontend: http://localhost:3000
   - Test API: http://localhost:8000/docs

4. **Stop Servers**
   - Press `Ctrl+C` in terminal

5. **Deploy to Databricks** (when ready)
   ```bash
   cd frontend && npm run build && cd ..
   /deploy-app
   ```

## Troubleshooting

### Port Already in Use
```bash
# Use different ports
/deploy-local --backend-port 8080 --frontend-port 3001

# Or kill existing processes
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### Virtual Environment Not Found
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Node.js Not Found
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm
```

### Environment Variables Missing
```bash
# Create .env file
cp .env.example .env

# Edit with your credentials
vim .env
```

## Differences from Production

**Local:**
- Hot reload enabled (fast development)
- Debug logging
- CORS allows all origins
- No authentication required
- Local file storage
- SQLite session management

**Production (Databricks):**
- Built frontend (optimized)
- Production logging
- CORS restricted
- Databricks authentication
- Workspace file storage
- Persistent storage

## Files

- `skill.md`: Skill description and documentation
- `scripts/deploy_local.py`: Main deployment script
- `README.md`: This file

## Integration with Claude Code

This skill is automatically available in Claude Code when installed. Use it by:
1. Typing `/deploy-local` in Claude Code
2. Or asking Claude to "deploy locally" or "run the app locally"

## Related Skills

- **deploy-app**: Deploy to Databricks Apps (production)
- **genie-commit**: Create commits with automated validation
- **genie-deploy**: Deploy Genie spaces from requirements

## Support

For issues or questions:
- Check prerequisites are installed correctly
- Verify `.env` file has required variables
- Check backend logs in terminal
- Check frontend logs in browser console (F12)
- See project documentation in `README.md` and `ARCHITECTURE.md`
