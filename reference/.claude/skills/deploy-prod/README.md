# deploy-prod: Production Deployment Skill

Automated production deployment for the Genie Lamp Agent with frontend build and Databricks bundle deployment.

## Overview

This skill automates the complete production deployment workflow:

1. **Build Frontend** - Optimized production build
2. **Deploy Bundle** - Upload files to prod environment
3. **Start App** (initial only) - Initialize app for first deployment
4. **Deploy App** - Update app with new code

## Production Configuration

**Hardcoded settings for production:**
- Environment: `prod`
- Profile: `krafton-sandbox`
- Source Code Path: `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files`
- App Name: `genie-lamp-agent`

## Installation

### Option 1: Symlink (Recommended)

Create a symlink so the skill updates automatically with the repository:

```bash
# From project root
ln -s "$(pwd)/.claude/skills/deploy-prod" ~/.codex/skills/deploy-prod

# Verify installation
ls -la ~/.codex/skills/deploy-prod
```

### Option 2: Copy

Copy the skill directory to Claude Code's skills location:

```bash
# From project root
cp -r .claude/skills/deploy-prod ~/.codex/skills/

# Update when skill changes
cp -r .claude/skills/deploy-prod ~/.codex/skills/
```

### Restart Claude Code

After installation, restart Claude Code to load the skill.

## Usage

### In Claude Code

The skill is automatically triggered when you ask to deploy to production:

```
User: Deploy the app to production
Claude: [Uses deploy-prod skill automatically]

User: Update the production app
Claude: [Uses deploy-prod skill automatically]

User: Publish to prod
Claude: [Uses deploy-prod skill automatically]
```

### Manual Execution

You can also run the deployment script directly:

```bash
# Update existing production app (most common)
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --update

# Initial production deployment (first time only)
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --initial
```

## When to Use

**Use this skill when:**
- Deploying code changes to production
- Updating the production app after testing in dev
- Rolling out new features to users
- Applying bug fixes to production

**Don't use this skill when:**
- Testing in dev environment (use `deploy-app` instead)
- Running locally (use `deploy-local` instead)
- Just checking app status (use `databricks apps get`)

## Prerequisites

Before using this skill, ensure:

1. ✅ **Databricks CLI installed**
   ```bash
   databricks --version
   ```

2. ✅ **Profile configured**
   ```bash
   databricks configure --profile krafton-sandbox
   ```

3. ✅ **Frontend dependencies installed**
   ```bash
   cd frontend && npm install && cd ..
   ```

4. ✅ **In project root directory**
   ```bash
   pwd  # Should show .../genie-lamp-agent-prod
   ```

## Deployment Workflow

### Automated Steps

When you trigger the skill, it automatically:

1. **Builds frontend**
   - Runs `npm run build` in frontend directory
   - Creates optimized production build
   - Bundles all assets

2. **Deploys bundle**
   - Uploads all files to Databricks workspace
   - Target: `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files`
   - Environment: `prod`

3. **Starts app** (initial deployment only)
   - Initializes the app service
   - Creates app identity
   - Skipped for updates

4. **Deploys app code**
   - Updates app with new code
   - Preserves app identity and permissions
   - Triggers app restart

### What You Don't Need to Do

The skill handles these automatically:
- ✅ Frontend build
- ✅ Environment selection (prod)
- ✅ Profile selection (krafton-sandbox)
- ✅ Source code path configuration
- ✅ Command execution order
- ✅ Error handling

## Examples

### Example 1: Update After Backend Changes

You've fixed a bug in the backend code:

```bash
# Make changes
vim backend/services/job_manager.py

# Commit changes
git add backend/services/job_manager.py
git commit -m "fix: Resolve job status tracking issue"

# Deploy to production
# In Claude Code, just say:
"Deploy to production"

# Or manually:
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --update
```

### Example 2: Update After Frontend Changes

You've improved the UI:

```bash
# Make changes
vim frontend/components/JobStatus.tsx

# Commit changes
git add frontend/components/JobStatus.tsx
git commit -m "feat: Add progress indicators to job status"

# Deploy to production
# In Claude Code, just say:
"Update the production app"

# Or manually:
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --update
```

### Example 3: First-Time Production Deployment

You're deploying to production for the first time:

```bash
# Ensure everything is ready
databricks configure --profile krafton-sandbox
cd frontend && npm install && cd ..

# Deploy to production
# In Claude Code, just say:
"Deploy to production for the first time"

# Or manually:
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py --initial
```

## Verification

After deployment, verify the app is running:

### Check App Status
```bash
databricks apps list -p krafton-sandbox | grep genie-lamp-agent
```

### View App Details
```bash
databricks apps get genie-lamp-agent -p krafton-sandbox
```

### Check Logs
```bash
databricks apps logs genie-lamp-agent -p krafton-sandbox
```

### Access the App
Navigate to: **Workspace** > **Apps** > **genie-lamp-agent**

## Troubleshooting

### Frontend Build Fails

**Error:** `npm: command not found` or build errors

**Solution:**
```bash
# Install Node.js (if not installed)
brew install node  # macOS

# Install dependencies
cd frontend
npm install

# Try build manually
npm run build
cd ..
```

### Bundle Deploy Fails

**Error:** Profile not found or authentication errors

**Solution:**
```bash
# Reconfigure profile
databricks configure --profile krafton-sandbox

# Verify configuration
databricks workspace list -p krafton-sandbox
```

### App Deploy Fails

**Error:** Source code path not found

**Solution:**
```bash
# Verify bundle deployed successfully
databricks bundle validate -t prod -p krafton-sandbox

# Check workspace path exists
databricks workspace list /Workspace/Shared/databricks-agent-poc/genie-lamp-app -p krafton-sandbox
```

### Permission Denied

**Error:** Cannot access workspace path

**Solution:**
- Contact workspace administrator
- Verify you have access to `/Workspace/Shared/databricks-agent-poc/`
- Check that the app service principal has correct permissions

## Safety Features

This skill includes safety features to prevent accidents:

1. **Never deletes the app** - Only updates code
2. **Validates project structure** - Checks for databricks.yml
3. **Clear error messages** - Shows exactly what failed
4. **Step-by-step execution** - Stops on first error
5. **Detailed logging** - Shows all commands and outputs

## Production vs Dev

### Key Differences

| Feature | Production (deploy-prod) | Development (deploy-app) |
|---------|-------------------------|--------------------------|
| Automation | Fully automated | Manual steps |
| Frontend Build | Automatic | Manual |
| Environment | prod (hardcoded) | dev or prod (configurable) |
| Source Path | Shared workspace | User workspace |
| Use Case | Production releases | Development testing |

### When to Use Each

**Use deploy-prod for:**
- ✅ Production deployments
- ✅ User-facing updates
- ✅ Fully automated workflow
- ✅ Consistent, reproducible deployments

**Use deploy-app for:**
- ✅ Dev environment testing
- ✅ Flexible deployment steps
- ✅ Custom configurations
- ✅ Development iterations

## Best Practices

1. **Test in dev first** - Always test changes in dev before prod
2. **Use version control** - Commit changes before deploying
3. **Review changes** - Check git diff before deploying
4. **Deploy off-hours** - Minimize user impact
5. **Monitor after deployment** - Watch logs for issues
6. **Keep dependencies updated** - Run `npm update` periodically
7. **Document changes** - Use clear commit messages
8. **Have rollback plan** - Know how to revert if needed

## Related Skills

- **deploy-app**: Flexible deployment for dev/prod with manual steps
- **deploy-local**: Local development and testing
- **genie-commit**: Automated git commits with validation
- **stop-local**: Stop local development servers

## Skill Files

```
.claude/skills/deploy-prod/
├── README.md              # This file
├── SKILL.md               # Skill specification for Claude Code
└── scripts/
    └── deploy_prod.py     # Production deployment script
```

## Support

For issues or questions:

1. Check this README and SKILL.md documentation
2. Review `.claude/rules/app-permissions.md` for safety guidelines
3. Check app logs: `databricks apps logs genie-lamp-agent -p krafton-sandbox`
4. Contact workspace administrator for permission issues
5. Create an issue in the project repository

## Version History

- **v1.0** - Initial production deployment skill
  - Automated frontend build
  - Hardcoded production configuration
  - Support for initial and update deployments
  - Comprehensive error handling and logging
