---
name: deploy-local
description: Deploy the Genie Lamp Agent locally for development and testing. Use when the user asks to run the app locally, start local development, or test the app on their machine. Automatically sets up dependencies, environment, and starts both backend and frontend servers.
---

# Genie Lamp Agent Local Deployment

Deploy the Genie Lamp Agent locally for development and testing with automatic setup and server management.

## Overview

This skill helps you run the Genie Lamp Agent on your local machine for:
- **Local Development**: Test changes without deploying to Databricks
- **Debugging**: Debug backend and frontend issues locally
- **Testing**: Validate functionality before deployment
- **Demos**: Run demos on your local machine

## Prerequisites

Before running locally, ensure you have:

1. **Python 3.8+** installed
   ```bash
   python3 --version
   ```

2. **Node.js 18+** and npm installed
   ```bash
   node --version
   npm --version
   ```

3. **Virtual environment** created at `.venv/`
   ```bash
   python3 -m venv .venv
   ```

4. **Environment variables** configured in `.env` file:
   - `DATABRICKS_HOST`: Your workspace URL
   - `DATABRICKS_TOKEN`: Your personal access token
   - Optional: `LLM_MODEL`, `VISION_MODEL`

5. **Git repository** - You're in the project root directory

## What This Skill Does

The deploy-local skill automates the complete local setup:

1. ✅ **Checks Prerequisites**: Verifies Python, Node.js, npm, and venv
2. ✅ **Installs Backend Dependencies**: Runs `pip install` for backend requirements
3. ✅ **Installs Frontend Dependencies**: Runs `npm install` in frontend directory
4. ✅ **Validates Environment**: Checks `.env` file exists with required variables
5. ✅ **Starts Backend Server**: Launches FastAPI server with uvicorn (port 8000)
6. ✅ **Starts Frontend Server**: Launches Next.js dev server (port 3000)
7. ✅ **Provides Access URLs**: Shows you where to access the app

## Usage

**Quick Start (Recommended):**
```bash
# From project root
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py
```

**With Options:**
```bash
# Custom ports
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py \
  --backend-port 8080 \
  --frontend-port 3001

# Skip dependency installation (faster)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-install

# Skip environment validation
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-env-check
```

## Access the Application

After successful deployment:

- **Frontend (Web UI)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc (Alternative docs)

## Project Structure

The local deployment works with:

```
genie-lamp-agent/
├── backend/                  # FastAPI backend
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt      # Backend Python dependencies
│   ├── services/            # Job manager, file storage, validators
│   └── middleware/          # Authentication middleware
├── frontend/                # Next.js frontend
│   ├── package.json         # Frontend dependencies
│   ├── app/                 # Next.js pages
│   └── components/          # React components
├── .env                     # Environment variables (required)
└── .venv/                   # Python virtual environment
```

## Deployment Process

### Step 1: Prerequisites Check
Verifies:
- Python 3.8+ is available
- Node.js 18+ is available
- npm is available
- Virtual environment exists at `.venv/`
- `.env` file exists with required variables

### Step 2: Backend Setup
1. Installs backend dependencies from `backend/requirements.txt`
2. Uses the project's virtual environment (`.venv/bin/python`)

### Step 3: Frontend Setup
1. Changes to `frontend/` directory
2. Runs `npm install` to install dependencies
3. Returns to project root

### Step 4: Start Servers
1. **Backend**: Starts FastAPI with uvicorn on port 8000
   ```bash
   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend**: Starts Next.js dev server on port 3000
   ```bash
   cd frontend && npm run dev
   ```

Both servers run concurrently and watch for file changes (hot reload enabled).

### Step 5: Provide Access Information
Shows:
- Frontend URL
- Backend API URL
- API documentation URLs
- Stop instructions

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-port` | Backend server port | `8000` |
| `--frontend-port` | Frontend server port | `3000` |
| `--skip-install` | Skip dependency installation | `False` |
| `--skip-env-check` | Skip environment validation | `False` |
| `--backend-only` | Start only backend server | `False` |
| `--frontend-only` | Start only frontend server | `False` |

## Common Scenarios

### Scenario 1: Full Local Development
```bash
# First time - installs all dependencies
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py

# Subsequent runs - skip installation for speed
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-install
```

### Scenario 2: Backend Development Only
```bash
# Start only backend (useful for API development)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --backend-only

# Access API docs at http://localhost:8000/docs
```

### Scenario 3: Frontend Development Only
```bash
# Start only frontend (if backend is already running elsewhere)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --frontend-only

# Access app at http://localhost:3000
```

### Scenario 4: Port Conflicts
```bash
# Use different ports if 3000/8000 are in use
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py \
  --backend-port 8080 \
  --frontend-port 3001
```

## Environment Variables

The app requires these variables in `.env`:

**Required:**
```bash
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
```

**Optional:**
```bash
# LLM Configuration
LLM_MODEL=databricks-gpt-5-2
VISION_MODEL=databricks-claude-sonnet-4

# Backend Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## Stopping the Servers

To stop the local deployment:

1. **Press `Ctrl+C`** in the terminal where servers are running
2. Both servers will gracefully shut down
3. Ports will be freed for future use

If servers don't stop:
```bash
# Find and kill processes
lsof -ti:8000 | xargs kill -9  # Kill backend
lsof -ti:3000 | xargs kill -9  # Kill frontend
```

## Troubleshooting

### Error: "Virtual environment not found"
**Solution:**
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Error: "Node.js not found"
**Solution:**
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Windows
# Download from https://nodejs.org/
```

### Error: "Port 8000 already in use"
**Solution:**
```bash
# Use different port
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --backend-port 8080

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Error: "DATABRICKS_HOST not set"
**Solution:**
1. Create `.env` file from example: `cp .env.example .env`
2. Edit `.env` and add your credentials:
   ```bash
   DATABRICKS_HOST=https://your-workspace.databricks.com
   DATABRICKS_TOKEN=your-token
   ```

### Error: "Module not found" when starting backend
**Solution:**
```bash
# Reinstall backend dependencies
.venv/bin/python -m pip install -r backend/requirements.txt
```

### Error: "npm packages not found" when starting frontend
**Solution:**
```bash
# Reinstall frontend dependencies
cd frontend && npm install && cd ..
```

## Development Workflow

**Typical Local Development Flow:**

1. **Make Code Changes**
   ```bash
   # Edit backend files
   vim backend/services/job_tasks.py

   # Edit frontend files
   vim frontend/components/JobProgress.tsx
   ```

2. **See Changes Live**
   - Backend: Uvicorn auto-reloads on file changes
   - Frontend: Next.js hot-reloads in browser
   - No restart needed!

3. **Test Changes**
   - Access frontend: http://localhost:3000
   - Check API docs: http://localhost:8000/docs
   - Test endpoints with Swagger UI

4. **Commit When Ready**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

5. **Deploy to Databricks**
   ```bash
   # Build frontend for production
   cd frontend && npm run build && cd ..

   # Deploy using deploy-app skill
   /deploy-app
   ```

## Differences from Production

**Local Deployment:**
- ✅ Hot reload enabled (fast development)
- ✅ Debug logging enabled
- ✅ CORS allows all origins
- ✅ No authentication required
- ✅ File storage in local filesystem
- ✅ SQLite for session management

**Production (Databricks App):**
- ⚙️ Built frontend (optimized)
- ⚙️ Production logging
- ⚙️ CORS restricted
- ⚙️ Databricks authentication required
- ⚙️ Workspace file storage
- ⚙️ Persistent session storage

## Monitoring Local Servers

**View Logs:**
- Backend logs appear in the terminal
- Frontend logs appear in browser console and terminal
- Check `backend/logs/` for detailed logs (if configured)

**Check Server Status:**
```bash
# Check if ports are listening
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## Next Steps After Local Testing

1. **Validate Locally**: Test all features work correctly
2. **Run CLI Tests**: Test CLI commands if needed
3. **Build Frontend**: `cd frontend && npm run build && cd ..`
4. **Deploy to Databricks**: Use `/deploy-app` skill
5. **Verify Production**: Test deployed app in Databricks

## Support

For issues:
- 🐛 Backend errors: Check backend logs in terminal
- 🖥️ Frontend errors: Check browser console (F12)
- 🔧 Environment issues: Verify `.env` file
- 📖 Documentation: See `README.md` and `ARCHITECTURE.md`

## Summary

**Quick Start:**
```bash
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Stop:**
- Press `Ctrl+C` in terminal
