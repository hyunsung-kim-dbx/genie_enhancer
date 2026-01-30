# Deployment Guide - Genie Space Enhancement System

## ✅ System is Ready!

All components are implemented and ready for testing in your Databricks environment.

---

## 🚀 Quick Deployment Steps

### Step 1: Set Environment Variables

```bash
# Required
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
export GENIE_SPACE_ID="01ef274d35a310b5bffd01dadcbaf577"

# Optional (with defaults)
export LLM_ENDPOINT="databricks-meta-llama-3-1-70b-instruct"
export TARGET_SCORE="0.90"
export MAX_ITERATIONS="10"
```

### Step 2: Test LLM Connection

```bash
cd /Users/hyunsung.kim/genie_enhancer
python3 -m pipeline.databricks_llm
```

Expected output:
```
Testing Databricks LLM Client
============================================================

1. Testing connection...
LLM connection test successful: Hello, Genie!
✅ Connection successful!

2. Testing JSON generation...
✅ Valid JSON!
```

### Step 3: Run Test Mode (Dry Run)

```bash
python3 run_enhancement.py test
```

This will:
- Load all 20 benchmarks
- Run them through Genie
- Analyze failures
- Generate fixes
- **NOT apply changes** (dry run)
- Show what would be done

### Step 4: Run Development Mode

```bash
python3 run_enhancement.py dev
```

This will:
- Run 2 iterations max
- Lower threshold (80%)
- Actually apply changes
- Good for testing the loop

### Step 5: Run Production Mode

```bash
python3 run_enhancement.py
```

Full production run with all settings.

---

## 📦 What's Included

### Complete Pipeline ✅

```
genie_enhancer/
├── pipeline/
│   ├── genie_client.py              ✅ Ask Genie questions
│   ├── space_updater.py             ✅ Update space config
│   ├── benchmark_scorer.py          ✅ Score with LLM judge
│   ├── llm_enhancer.py              ✅ Generate fixes
│   ├── databricks_llm.py            ✅ LLM client
│   ├── reporter.py                  ✅ Progress reporting
│   └── benchmark_parser.py          ✅ Parse benchmarks
│
├── prompts/
│   ├── best_practices.txt           ✅ 3,500+ lines knowledge
│   ├── analysis_prompt.txt          ✅ Analysis template
│   ├── answer_comparison.txt        ✅ Judge template
│   └── prompt_loader.py             ✅ Prompt loader
│
├── job/
│   ├── enhancement_job.py           ✅ Main orchestration
│   └── config.py                    ✅ Configuration
│
├── benchmarks/
│   └── benchmarks.json              ✅ 20 Q&A pairs ready
│
├── run_enhancement.py               ✅ Entry point
├── requirements.txt                 ✅ Dependencies
└── README.md                        ✅ Complete docs
```

---

## 🔍 Debugging Tips

### Check Genie Space ID

```bash
# From Databricks workspace
# Go to your Genie Space → Settings → Copy Space ID
```

### Check LLM Endpoint

```bash
# List available endpoints
databricks serving-endpoints list

# Or use a different endpoint
export LLM_ENDPOINT="databricks-dbrx-instruct"
export LLM_ENDPOINT="databricks-meta-llama-3-1-405b-instruct"
```

### Enable Debug Logging

```bash
export LOG_LEVEL="DEBUG"
python3 run_enhancement.py test
```

### Test Individual Components

```python
# Test Genie Client
from pipeline import GenieConversationalClient
client = GenieConversationalClient(host, token, space_id)
response = client.ask("Test question")
print(response)

# Test Space Export
from pipeline import SpaceUpdater
updater = SpaceUpdater(host, token)
space = updater.export_space(space_id)
print(f"Exported: {space['title']}")

# Test Benchmark Loading
from pipeline import BenchmarkLoader
loader = BenchmarkLoader("benchmarks/benchmarks.json")
benchmarks = loader.load()
print(f"Loaded {len(benchmarks)} benchmarks")
```

---

## 📊 Expected Output

### Iteration Output

```
═══════════════════════════════════════════════════════════════════
ITERATION 1/10
═══════════════════════════════════════════════════════════════════

[1] Scoring benchmarks...
Running benchmarks (this may take a while)...
[1/20] Testing: What are the Discord messages with the most reactions?...
  ✅ PASS (N/A)
[2/20] Testing: What are the Steam reviews with the highest upvote counts?...
  ❌ FAIL (missing_table_or_column)
...

═══════════════════════════════════════════════════════════════════
Benchmark Score: 85.00% (17/20 passed)
Duration: 45.2s
═══════════════════════════════════════════════════════════════════

[1] Current score: 85.00%
[1] Analyzing failures and generating fixes...
[1/3] Analyzing failure: What are the Steam reviews...
  Generated 3 fix(es)
...

Total unique fixes: 10

[1] Validation: valid
[1] Applying 10 fixes to space...
[1] ✅ Changes applied successfully
[1] Waiting 30s for Genie to index changes...

═══════════════════════════════════════════════════════════════════
Iteration 1 Report
═══════════════════════════════════════════════════════════════════
Timestamp: 2026-01-29T14:30:00.000000
Space ID: 01ef274d35a310b5bffd01dadcbaf577

Score: 85.00% (17/20)
Score Change: +0.00%
Duration: 78.5s

Changes Made: 10
  - add_synonym: 5
  - add_column_description: 2
  - fix_join: 1
  - add_example_query: 2

Failures by Category:
  - missing_table_or_column: 2
  - wrong_join: 1
═══════════════════════════════════════════════════════════════════
```

### Final Output

```
═══════════════════════════════════════════════════════════════════
FINAL RESULTS
═══════════════════════════════════════════════════════════════════
Space ID: 01ef274d35a310b5bffd01dadcbaf577
Status: threshold_reached
Success: ✅ YES

Initial Score: 65.00%
Final Score: 92.00%
Improvement: +27.00%

Iterations: 3
Total Duration: 234.5s (3.9 min)
═══════════════════════════════════════════════════════════════════

✅ Job completed successfully!
```

---

## 🎯 Success Criteria

Your system is working correctly if:

1. ✅ LLM connection test passes
2. ✅ Genie client can ask questions and get responses
3. ✅ Benchmark scorer runs and produces scores
4. ✅ LLM enhancer generates fixes in valid JSON format
5. ✅ Space updater can export and validate configs
6. ✅ Changes apply successfully and score improves
7. ✅ System converges to target score or stops appropriately

---

## 🐛 Common Issues & Solutions

### Issue: "Missing required config: databricks_host"

**Solution:**
```bash
export DATABRICKS_HOST="your-workspace.cloud.databricks.com"
# Don't include https://
```

### Issue: "LLM connection test failed"

**Solutions:**
```bash
# 1. Check endpoint exists
databricks serving-endpoints list | grep llama

# 2. Try different endpoint
export LLM_ENDPOINT="databricks-dbrx-instruct"

# 3. Check token permissions
# Token needs access to serving endpoints
```

### Issue: "Failed to export space: 404 Not Found"

**Solutions:**
```bash
# 1. Verify space ID
# Go to Genie Space → Settings → Copy Space ID

# 2. Check permissions
# Token needs "Can View" on space

# 3. Test manually
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  "https://$DATABRICKS_HOST/api/2.0/genie/spaces/$GENIE_SPACE_ID"
```

### Issue: "Benchmark source not found"

**Solution:**
```bash
# Verify benchmarks exist
ls -la benchmarks/benchmarks.json

# If missing, regenerate
python3 -m pipeline.benchmark_parser
```

### Issue: "No fixes generated"

**Possible causes:**
1. All benchmarks passed (no failures to fix!)
2. LLM not returning valid JSON
3. Failures are too complex for LLM to analyze

**Debug:**
```bash
# Enable debug logging to see LLM responses
export LOG_LEVEL="DEBUG"
python3 run_enhancement.py test
```

---

## 📈 Monitoring in Production

### Option 1: Delta Table Reports

```bash
export REPORT_TO="delta_table"
export REPORT_TABLE="catalog.schema.genie_enhancement_progress"

python3 run_enhancement.py
```

Then create dashboard:
```sql
SELECT
  iteration,
  timestamp,
  score,
  score_delta,
  passed,
  failed,
  num_changes
FROM catalog.schema.genie_enhancement_progress
WHERE space_id = '...'
ORDER BY iteration
```

### Option 2: MLflow Tracking

```bash
export REPORT_TO="mlflow"
export MLFLOW_EXPERIMENT="/genie-enhancement"

python3 run_enhancement.py
```

View in MLflow UI to compare runs.

---

## 🔐 Production Best Practices

### 1. Use Service Principal

Instead of personal token:
```bash
export DATABRICKS_TOKEN="..." # Service principal token
```

### 2. Store Secrets Securely

Use Databricks Secrets:
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
token = w.secrets.get_secret(scope="genie", key="token")
```

### 3. Schedule as Job

Create Databricks Job:
```json
{
  "name": "Genie Space Enhancement",
  "tasks": [{
    "task_key": "enhance",
    "python_wheel_task": {
      "entry_point": "run_enhancement"
    },
    "new_cluster": {
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 0
    }
  }],
  "schedule": {
    "quartz_cron_expression": "0 0 2 * * ?",  # Daily at 2 AM
    "timezone_id": "UTC"
  }
}
```

### 4. Set Alerts

Monitor job status and set alerts for:
- Job failures
- Score degradation
- No improvement for multiple runs

---

## 🎓 Next Steps

1. **Test with Small Benchmark Set** - Start with 3-5 questions
2. **Review Generated Fixes** - Check quality of fixes in dry run
3. **Run on Dev Space First** - Don't test on production space
4. **Monitor Score Improvements** - Track progress over iterations
5. **Add More Benchmarks** - Expand coverage as system proves reliable
6. **Schedule Regular Runs** - Keep space optimal over time

---

## 📞 Getting Help

Check these resources:
1. `README.md` - Usage guide
2. `IMPLEMENTATION_STATUS.md` - Current status
3. `plan.md` - Architecture details
4. Logs - `export LOG_LEVEL="DEBUG"`

---

**You're ready to run the system! 🚀**

Start with:
```bash
python3 run_enhancement.py test
```
