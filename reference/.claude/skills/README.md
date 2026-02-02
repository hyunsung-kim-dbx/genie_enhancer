# Claude Code Skills for Genie Lamp Agent

This directory contains custom Claude Code skills for the Genie Lamp Agent project.

## What are Skills?

Skills are modular packages that extend Claude Code's capabilities by providing:
- Specialized workflows for specific tasks
- Project-specific knowledge and best practices
- Automated procedures with validation
- Bundled scripts and references

## Available Skills

### genie-commit

Automated git commit workflow with testing and validation.

**Triggers:** When you ask to "commit changes", "create a commit", or "save to git"

**Features:**
- Runs `.venv/bin/python -m pytest tests/ -v` before committing
- Analyzes changes to suggest commit type (feat/fix/refactor/docs/test)
- Follows conventional commit message format
- Checks for sensitive files (.env, tokens)
- Includes Co-Authored-By attribution for Claude

**Example Usage:**
```
User: "commit these changes"

Claude will:
1. Check git status and diff
2. Run full test suite
3. Analyze changes and classify commit type
4. Craft appropriate commit message
5. Stage files explicitly
6. Create commit with proper formatting
```

### genie-deploy

Automated Genie space deployment from real_requirements/inputs with automatic catalog replacement.

**Triggers:** When you ask to "deploy genie", "create a genie space from real requirements", or "run automated deployment"

**Features:**
- Parses documents from `real_requirements/inputs/` directory
- Generates Genie space configuration using LLM
- Validates tables against Unity Catalog
- **Automatically replaces** failed catalog.schema with `sandbox.agent_poc`
- Retries validation up to 3 times
- Deploys to Databricks workspace

**Example Usage:**
```
User: "deploy genie from real requirements"

Claude will:
1. Parse PDFs/markdown from real_requirements/inputs/
2. Generate structured requirements
3. Create Genie configuration
4. Validate tables (auto-replace with sandbox.agent_poc)
5. Deploy the Genie space
6. Return space ID and URL
```

**Script:** `scripts/auto_deploy.py`

**Key Configuration:**
- Input: `real_requirements/inputs/` directory (requirements documents)
- Benchmarks: `real_requirements/benchmarks/` directory (optional)
- Parsed output: `data/parsed.md`
- Config output: `output/genie_space_config.json`
- Result output: `output/genie_space_result.json`
- Auto-replacement: `sandbox.agent_poc`

**Troubleshooting:**
If deployment fails with `INTERNAL_ERROR`:
- Check for special characters (backticks, complex parentheses) in space_name, description, or purpose
- Clean metadata: Use simple names without special formatting
- Verify table names match Unity Catalog (e.g., `steam_app_id` → `steam_apps`)
- Test with minimal config first, then incrementally add components

See `genie-deploy/skill.md` for detailed troubleshooting steps.

### deploy-app

Deploy the Genie Lamp Agent Databricks app using Asset Bundles.

**Triggers:** When you ask to "deploy the app", "deploy genie-lamp-agent", "update the app", or "publish the app"

**Features:**
- Automated Databricks app deployment using Asset Bundles
- Support for both initial deployment (first-time) and update deployment
- Automatic handling of bundle deploy, app start, and app deploy commands
- Environment-specific deployments (dev, prod)
- Working directory support for nested bundle configs
- Pre-deployment validation (secrets, config files)

**Example Usage:**
```
User: "deploy the app to dev"

Claude will:
1. Ask for deployment type (initial or update)
2. Confirm source code path
3. Change to app/ directory
4. Run databricks bundle deploy
5. Start app (if initial) or skip (if update)
6. Deploy app code
7. Provide access instructions
```

**Script:** `.claude/skills/deploy-app/scripts/deploy_app.py`

**Project Configuration:**
- Bundle Name: `genie-lamp-agent`
- App Resource Name: `genie_lamp_app`
- Working Directory: `app/`
- Environments: `dev` (default), `prod`
- Source Code Path Pattern: `/Workspace/Users/<username>/.bundle/genie-lamp-agent/<env>/files`

**Prerequisites:**
- Databricks CLI installed and configured
- Secrets configured in `genie-lamp` scope (service-token, sql-warehouse-http-path)
- Frontend built (if deploying after frontend changes): `cd app/frontend && npm run build`

**Common Commands:**
```bash
# Initial deployment to dev
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/user@example.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --initial

# Update deployment to dev
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/user@example.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --update
```

See `.claude/skills/deploy-app/SKILL.md` for detailed deployment workflows and troubleshooting.

### deploy-dev

Automated development deployment with frontend build and deployment.

**Triggers:** When you ask to "deploy to dev", "publish to dev", "update dev app", or "deploy development"

**Features:**
- Fully automated development deployment workflow
- Frontend build included automatically
- Deploys to dev environment with correct source code path
- Support for both initial and update deployments
- Hardcoded configuration for consistency

**Example Usage:**
```
User: "deploy to dev"

Claude will:
1. Build frontend (npm run build)
2. Deploy bundle to dev environment
3. Start app (if initial deployment)
4. Deploy app with dev source code path
5. Provide access URL and verification commands
```

**Script:** `.claude/skills/deploy-dev/scripts/deploy_dev.py`

**Configuration:**
- App Name: `genie-lamp-agent-dev`
- Environment: `dev`
- Profile: `krafton-sandbox`
- Source Code Path: `/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files`

**Common Commands:**
```bash
# Update existing dev app (most common)
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py --update

# Initial dev deployment (first time only)
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py --initial
```

**Development Workflow:**
1. Make code changes
2. Deploy to dev: `/deploy-dev`
3. Test in dev environment
4. Deploy to prod when ready: `/deploy-prod`

See `.claude/skills/deploy-dev/SKILL.md` for detailed documentation.

### deploy-prod

Automated production deployment with frontend build and deployment.

**Triggers:** When you ask to "deploy to prod", "deploy to production", "publish to prod", or "update production"

**Features:**
- Fully automated production deployment workflow
- Frontend build included automatically
- Deploys to prod environment with correct source code path
- Support for both initial and update deployments
- Hardcoded configuration for consistency
- Safety checks and best practices

**Example Usage:**
```
User: "deploy to production"

Claude will:
1. Build frontend (npm run build)
2. Deploy bundle to prod environment
3. Start app (if initial deployment)
4. Deploy app with production source code path
5. Provide access URL and verification commands
```

**Script:** `.claude/skills/deploy-prod/scripts/deploy_prod.py`

**Configuration:**
- App Name: `genie-lamp-agent`
- Environment: `prod`
- Profile: `krafton-sandbox`
- Source Code Path: `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files`

**Common Commands:**
```bash
# Update existing prod app (most common)
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --update

# Initial prod deployment (first time only)
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --initial
```

**Safety Checklist:**
- [ ] Code tested in dev environment first
- [ ] Changes reviewed and approved
- [ ] Using `--update` flag (not `--initial`)
- [ ] Ready for production deployment

See `.claude/skills/deploy-prod/SKILL.md` for detailed documentation and safety guidelines.

### deploy-local

Deploy the Genie Lamp Agent locally for development and testing.

**Triggers:** When you ask to "run locally", "start local development", "test locally", or "deploy on local"

**Features:**
- Checks prerequisites (Python, Node.js, npm, virtual environment)
- Installs backend dependencies (FastAPI, uvicorn, etc.)
- Installs frontend dependencies (Next.js, React, etc.)
- Validates environment configuration (.env file)
- Starts backend FastAPI server with hot reload (port 8000)
- Starts frontend Next.js dev server with hot reload (port 3000)
- Supports custom ports and flexible deployment modes

**Example Usage:**
```
User: "run the app locally"

Claude will:
1. Check prerequisites (Python, Node.js, npm, venv)
2. Install backend dependencies (if needed)
3. Install frontend dependencies (if needed)
4. Validate .env file has required variables
5. Start backend server on port 8000
6. Start frontend server on port 3000
7. Provide access URLs and instructions
```

**Script:** `.claude/skills/deploy-local/scripts/deploy_local.py`

**Access URLs:**
- Frontend (Web UI): http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (Redoc): http://localhost:8000/redoc

**Prerequisites:**
- Python 3.8+
- Node.js 18+ and npm
- Virtual environment at `.venv/`
- `.env` file with `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

**Common Commands:**
```bash
# Full local deployment (installs deps + starts servers)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py

# Skip installation (faster for repeated runs)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-install

# Custom ports
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py \
  --backend-port 8080 --frontend-port 3001

# Backend only (useful for API development)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --backend-only

# Frontend only (if backend is running elsewhere)
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --frontend-only
```

**Development Workflow:**
1. Start local deployment: `/deploy-local`
2. Make code changes (auto-reload on save)
3. Test in browser (http://localhost:3000)
4. Stop servers with `Ctrl+C`
5. Deploy to Databricks when ready: `/deploy-app`

See `.claude/skills/deploy-local/README.md` for detailed usage and troubleshooting.

### stop-local

Stop local Genie Lamp Agent development servers.

**Triggers:** When you ask to "stop local servers", "shut down local development", "stop servers", or "clean up processes"

**Features:**
- Identifies processes by port (8000 for backend, 3000 for frontend)
- Graceful shutdown with SIGTERM (5 second timeout)
- Force-kills if needed with SIGKILL
- Verifies ports are freed
- Supports stopping individual servers or both together
- Clear status reporting

**Example Usage:**
```
User: "stop local servers"

Claude will:
1. Find processes on ports 8000 and 3000
2. Send graceful shutdown signal (SIGTERM)
3. Wait up to 5 seconds for clean shutdown
4. Force-kill if processes don't stop
5. Verify ports are freed
6. Report status of each server
```

**Script:** `.claude/skills/stop-local/scripts/stop_local.py`

**Common Commands:**
```bash
# Stop both servers
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py

# Stop only backend
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --backend-only

# Stop only frontend
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --frontend-only

# Force kill without waiting
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --force

# Custom ports
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py \
  --backend-port 8080 --frontend-port 3001
```

**Development Workflow:**
1. Start servers: `/deploy-local`
2. Make changes (hot reload enabled)
3. Stop servers: `/stop-local`
4. Restart: `/deploy-local --skip-install`

**Verification:**
```bash
# Check if servers are stopped
lsof -i :8000  # Should return nothing
lsof -i :3000  # Should return nothing
```

See `.claude/skills/stop-local/README.md` for detailed usage.

### create-folder

Safely create directories with validation and parent directory creation.

**Triggers:** When you ask to "create folder", "make directory", "mkdir -p", or "ensure folder exists"

**Features:**
- Checks if directory already exists before creation
- Creates parent directories automatically with `-p` flag
- Verifies successful creation
- Handles errors gracefully with clear messages
- Supports single or multiple directory creation

**Example Usage:**
```
User: "create folder if not exists for output"

Claude will:
1. Check if 'output' directory exists
2. Create with mkdir -p if needed
3. Verify creation success
4. Report status to user
```

**Use Cases:**
- Single directory: `mkdir -p data`
- Nested directories: `mkdir -p output/configs/prod`
- Multiple directories: `mkdir -p data benchmarks logs`
- Project structure: `mkdir -p src/api src/models tests/unit`

## Installing Skills

### Option 1: Symlink to Claude Code skills directory (Recommended)

This makes the skills available globally in Claude Code:

```bash
# Create symlinks for all skills
ln -s "$(pwd)/.claude/skills/genie-commit" ~/.codex/skills/genie-commit
ln -s "$(pwd)/.claude/skills/genie-deploy" ~/.codex/skills/genie-deploy
ln -s "$(pwd)/.claude/skills/deploy-app" ~/.codex/skills/deploy-app
ln -s "$(pwd)/.claude/skills/deploy-dev" ~/.codex/skills/deploy-dev
ln -s "$(pwd)/.claude/skills/deploy-prod" ~/.codex/skills/deploy-prod
ln -s "$(pwd)/.claude/skills/deploy-local" ~/.codex/skills/deploy-local
ln -s "$(pwd)/.claude/skills/stop-local" ~/.codex/skills/stop-local
ln -s "$(pwd)/.claude/skills/create-folder" ~/.codex/skills/create-folder

# Verify
ls -la ~/.codex/skills/genie-* ~/.codex/skills/deploy-* ~/.codex/skills/stop-* ~/.codex/skills/create-folder
```

### Option 2: Copy to Claude Code skills directory

```bash
# Copy the skills
cp -r .claude/skills/genie-commit ~/.codex/skills/
cp -r .claude/skills/genie-deploy ~/.codex/skills/
cp -r .claude/skills/deploy-app ~/.codex/skills/
cp -r .claude/skills/deploy-dev ~/.codex/skills/
cp -r .claude/skills/deploy-prod ~/.codex/skills/
cp -r .claude/skills/deploy-local ~/.codex/skills/
cp -r .claude/skills/stop-local ~/.codex/skills/
cp -r .claude/skills/create-folder ~/.codex/skills/

# Verify
ls -la ~/.codex/skills/genie-* ~/.codex/skills/deploy-* ~/.codex/skills/stop-* ~/.codex/skills/create-folder
```

### After Installation

**Restart Claude Code** to load the new skills. The skills will automatically trigger based on their descriptions.

## Creating New Skills

To create additional project-specific skills:

1. Use the skill-creator system skill:
   ```bash
   cd ~/.codex/skills/.system/skill-creator
   python3 scripts/init_skill.py <skill-name> --path $(pwd)/.claude/skills --resources scripts,references
   ```

2. Edit the generated `SKILL.md` with your workflow

3. Add scripts to `scripts/` and references to `references/`

4. Test the skill by symlinking or copying to `~/.codex/skills/`

5. Commit to this repo to version control

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # Required: Workflow instructions with YAML frontmatter
├── scripts/              # Optional: Executable Python/Bash scripts
├── references/           # Optional: Documentation loaded as needed
└── assets/               # Optional: Templates, files for output
```

## Best Practices

1. **Keep skills focused** - One skill per major workflow
2. **Be concise** - Skills share context window with conversation
3. **Use references** - Move detailed docs to `references/` to keep SKILL.md lean
4. **Test thoroughly** - Run scripts and test workflows before committing
5. **Document triggers** - Clear description of when skill should activate

## Contributing

When adding new skills:

1. Create skill in `.claude/skills/` directory
2. Test locally by symlinking to `~/.codex/skills/`
3. Update this README with skill description
4. Commit with message: `feat: Add <skill-name> skill for <purpose>`

## References

- [Claude Code Skills Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- Skill creator guide: `~/.codex/skills/.system/skill-creator/SKILL.md`
