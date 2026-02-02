# Databricks Deployment Guide

This guide explains how to deploy the Genie Space Enhancement System to Databricks.

## Prerequisites

- Databricks Workspace (AWS, Azure, or GCP)
- Unity Catalog enabled
- SQL Warehouse for metric views
- Databricks CLI installed locally

## Installation

### 1. Install Databricks CLI

```bash
# macOS/Linux
pip install databricks-cli

# Configure authentication
databricks configure --token
```

Enter:
- Host: `https://your-workspace.cloud.databricks.com`
- Token: Your personal access token

### 2. Upload Code to Databricks Workspace

```bash
# From your local repo directory
cd /Users/hyunsung.kim/genie_enhancer

# Upload to Workspace
databricks workspace import-dir . /Workspace/Users/your.email@company.com/genie_enhancer --overwrite
```

Or use the Databricks UI:
1. Go to Workspace
2. Navigate to your user folder
3. Click "Import" → "Folder"
4. Select the `genie_enhancer` directory

## Deployment Options

### Option A: Databricks App (Recommended for UI)

Deploy as a managed Databricks App with automatic scaling and authentication.

#### Step 1: Review App Configuration

Check `config/app.yaml`:
```yaml
name: genie-space-enhancement
entrypoint: app.py
dependencies:
  - requirements.txt
```

#### Step 2: Deploy via Databricks CLI

```bash
# Navigate to the uploaded workspace path
cd /Workspace/Users/your.email@company.com/genie_enhancer

# Deploy the app
databricks apps create --config config/app.yaml
```

Or use the Databricks UI:
1. Go to "Apps" in the left sidebar
2. Click "Create App"
3. Select "From Workspace"
4. Navigate to `/Workspace/Users/your.email@company.com/genie_enhancer`
5. Select `config/app.yaml`
6. Click "Create"

#### Step 3: Access Your App

1. Go to "Apps" in Databricks
2. Find "genie-space-enhancement"
3. Click to open the app URL
4. The Streamlit UI will load automatically

### Option B: Databricks Job (Recommended for Automation)

Deploy as a scheduled or triggered job for automated enhancement cycles.

#### Step 1: Review Job Configuration

Check `config/job.yaml` for the 4-stage pipeline configuration.

#### Step 2: Create Job

```bash
# Create job from YAML
databricks jobs create --json-file config/job.yaml
```

Or use the Databricks UI:
1. Go to "Workflows"
2. Click "Create Job"
3. Import from `config/job.yaml`

#### Step 3: Run Job

```bash
# Get job ID from previous step
databricks jobs run-now --job-id <job-id>

# Monitor progress
databricks runs get --run-id <run-id>
```

### Option C: Interactive Notebook

For quick testing and development.

#### Step 1: Create Notebook

1. In Databricks, create a new Python notebook
2. Attach to a cluster with ML runtime

#### Step 2: Run Enhancement

```python
%pip install -r /Workspace/Users/your.email@company.com/genie_enhancer/requirements.txt

# Import the enhancement system
import sys
sys.path.append('/Workspace/Users/your.email@company.com/genie_enhancer')

from lib.genie_client import GenieConversationClient
from lib.space_api import SpaceAPI
from lib.scorer import BenchmarkScorer
from lib.enhancer import SpaceEnhancer
from lib.applier import EnhancementApplier

# Configure
space_id = "01f0f5c840c118b9824acd167525a768"
host = dbutils.secrets.get("genie", "workspace-host")
token = dbutils.secrets.get("genie", "access-token")

# Run enhancement cycle
# ... (see run_enhancement.py for full example)
```

## Configuration

### Environment Variables

Set these in your app/job configuration or use Databricks Secrets:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Workspace URL | `https://workspace.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Personal Access Token | Use secrets! |
| `CATALOG` | Unity Catalog name | `sandbox` |
| `SCHEMA` | Schema for state tables | `genie_enhancement` |
| `DEFAULT_LLM_ENDPOINT` | LLM endpoint name | `databricks-meta-llama-3-1-70b-instruct` |

### Databricks Secrets

Store sensitive values in Databricks Secrets:

```bash
# Create secret scope
databricks secrets create-scope --scope genie

# Add secrets
databricks secrets put --scope genie --key access-token
databricks secrets put --scope genie --key workspace-host
```

Update `config/app.yaml` to use secrets:
```yaml
secrets:
  - scope: "genie"
    key: "access-token"
    env_var: "DATABRICKS_TOKEN"
  - scope: "genie"
    key: "workspace-host"
    env_var: "DATABRICKS_HOST"
```

## Verification

### Test the App

1. Open the deployed app URL
2. Enter your credentials (or use pre-configured secrets)
3. Select a Genie Space
4. Load a benchmark file
5. Click "Score Benchmarks"
6. Verify results appear

### Check Logs

For Databricks Apps:
```bash
# View app logs
databricks apps logs --name genie-space-enhancement
```

For Databricks Jobs:
```bash
# View run logs
databricks runs get-output --run-id <run-id>
```

### Verify Delta Tables

Check that state tables are created:

```sql
-- Check catalog/schema
SHOW SCHEMAS IN sandbox;

-- Check tables
SHOW TABLES IN sandbox.genie_enhancement;

-- View recent runs
SELECT * FROM sandbox.genie_enhancement.genie_job_runs
ORDER BY start_time DESC
LIMIT 10;
```

## Troubleshooting

### Issue: App fails to start

**Solution:** Check requirements.txt dependencies
```bash
# SSH into the app container (if available)
pip list

# Verify all packages installed
pip install -r requirements.txt
```

### Issue: Authentication errors

**Solution:** Verify secrets are configured correctly
```bash
# Test secrets
databricks secrets list --scope genie

# Verify token has correct permissions
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
     https://your-workspace.cloud.databricks.com/api/2.0/clusters/list
```

### Issue: Delta table not found

**Solution:** Create schema and tables
```sql
-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS sandbox.genie_enhancement;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA sandbox.genie_enhancement TO `your.email@company.com`;
```

### Issue: Genie API rate limits

**Solution:** Adjust concurrent request settings

In the UI, reduce "Max Concurrent Calls" or edit the code:
```python
# In batch_genie_client.py
MAX_CONCURRENT_GENIE_CALLS = 2  # Reduce from 3
```

## Performance Tuning

### For Batch Scoring

Adjust concurrency based on your workspace limits:
```python
# Recommended settings
--genie-concurrent 3  # Default, works for most workspaces
--genie-concurrent 5  # If you have higher rate limits
--genie-concurrent 1  # Conservative, for shared workspaces
```

### For Large Benchmarks

Enable progress tracking:
```python
from lib.batch_scorer import BatchScorer

scorer = BatchScorer(
    genie_client=client,
    max_concurrent=3,
    show_progress=True  # Enable progress bar
)
```

## Monitoring

### Create Dashboard

1. Go to "Dashboards" in Databricks
2. Create new dashboard
3. Add visualizations from Delta tables:

```sql
-- Score trends over time
SELECT
  DATE(start_time) as date,
  AVG(score) as avg_score,
  COUNT(*) as num_runs
FROM sandbox.genie_enhancement.genie_job_runs
WHERE status = 'SUCCESS'
GROUP BY DATE(start_time)
ORDER BY date DESC;

-- Fix effectiveness
SELECT
  category,
  COUNT(*) as fixes_applied,
  AVG(score_improvement) as avg_improvement
FROM sandbox.genie_enhancement.genie_fixes
GROUP BY category
ORDER BY avg_improvement DESC;
```

### Set Up Alerts

Use Databricks Alerts to notify on:
- Job failures
- Score degradation
- API errors

## Best Practices

1. **Use Secrets** - Never hard-code tokens
2. **Start Small** - Test with a small benchmark first
3. **Monitor Costs** - Track LLM API usage
4. **Version Control** - Keep your config in git
5. **Review Fixes** - Always review generated fixes before applying
6. **Backup Spaces** - Export Genie Space before making changes

## Next Steps

- Read [USAGE_GUIDE.md](docs/USAGE_GUIDE.md) for detailed usage
- Check [ARCHITECTURE_V3_ENHANCEMENTS.md](docs/ARCHITECTURE_V3_ENHANCEMENTS.md) for system design
- See [BATCH_SCORING.md](docs/BATCH_SCORING.md) for performance optimization

## Support

For issues or questions:
- Check existing documentation in `docs/`
- Review error logs in Databricks
- Contact the Genie team on Slack

---

**Ready to Deploy?** Follow Option A above to get started with the Databricks App! 🚀
