# deploy-dev - Development Deployment Skill

Automated development deployment for the Genie Lamp Agent with frontend build, bundle deployment, and app deployment.

## Quick Start

```bash
# Update existing dev app (most common)
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py --update

# Initial dev deployment (first time only)
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py --initial
```

## What This Skill Does

Automates the complete development deployment workflow:

1. ✅ **Build Frontend** - `npm run build` in frontend directory
2. ✅ **Deploy Bundle** - `databricks bundle deploy -t dev -p krafton-sandbox`
3. ✅ **Start App** (initial only) - `databricks apps start genie-lamp-agent-dev`
4. ✅ **Deploy App** - `databricks apps deploy` with dev source code path

## Configuration

Hardcoded for the Genie Lamp Agent development environment:

- **App Name**: `genie-lamp-agent-dev`
- **Environment**: `dev`
- **Profile**: `krafton-sandbox`
- **Source Code Path**: `/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files`

## Usage in Claude Code

When the user asks to deploy to dev:

```
User: "Deploy to dev"
Claude: /deploy-dev
```

The skill handles the entire workflow automatically.

## Prerequisites

- Databricks CLI installed and configured
- Frontend dependencies installed (`cd frontend && npm install`)
- Running from project root directory
- Valid Databricks profile (`krafton-sandbox`)

## Safety

⚠️ **NEVER delete the app** - Use `--update` for existing apps to preserve permissions.

See `.claude/rules/app-permissions.md` for complete safety guidelines.

## Related Skills

- **deploy-prod**: Production deployment (uses `prod` target)
- **deploy-app**: Flexible deployment for any environment
- **deploy-local**: Local development environment

## Documentation

Full documentation in `SKILL.md`.
