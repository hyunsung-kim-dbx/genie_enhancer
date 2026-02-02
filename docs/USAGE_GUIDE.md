# Genie Enhancer Usage Guide

Complete guide for using the Genie Space enhancement system with batch scoring.

## Quick Start

### Basic Usage (Batch Mode - Recommended)

```bash
python run_enhancement.py \
  --host workspace.cloud.databricks.com \
  --token dapi... \
  --space-id 01abc123... \
  --warehouse-id xyz789... \
  --benchmarks benchmarks/kpi_benchmark.json
```

This uses:
- ✅ **Batch mode** (13x faster)
- ✅ Safe defaults (3 concurrent Genie calls)
- ✅ Circuit breaker protection
- ✅ Automatic retry on failures

### Sequential Mode (Fallback)

If you encounter issues with batch mode:

```bash
python run_enhancement.py \
  --no-batch \
  --host ... \
  --token ... \
  --space-id ... \
  --warehouse-id ... \
  --benchmarks benchmarks/kpi_benchmark.json
```

## Command Line Options

### Required

| Option | Description | Example |
|--------|-------------|---------|
| `--host` | Databricks workspace host | `workspace.cloud.databricks.com` |
| `--token` | Personal access token | `dapi...` |
| `--space-id` | Genie Space ID to enhance | `01abc123...` |
| `--warehouse-id` | SQL Warehouse ID | `xyz789...` |

### Optional

| Option | Default | Description |
|--------|---------|-------------|
| `--benchmarks` | `benchmarks/fixed_benchmark_final.json` | Benchmark file path |
| `--llm-endpoint` | `databricks-claude-sonnet-4` | LLM endpoint name |
| `--target-score` | `0.90` | Target accuracy (0.0-1.0) |
| `--max-loops` | `3` | Maximum enhancement loops |
| `--indexing-wait` | `60` | Seconds to wait after applying fixes |
| `--auto-promote` | `False` | Auto-promote to production on success |
| `--no-cleanup` | `False` | Keep dev spaces after completion |

### Batch Mode Options

| Option | Default | Description |
|--------|---------|-------------|
| `--no-batch` | `False` | Disable batch mode, use sequential |
| `--genie-concurrent` | `3` | Max concurrent Genie API calls |
| `--sql-concurrent` | `10` | Max concurrent SQL queries |

## Usage Examples

### 1. Development Testing (Conservative)

Test with conservative settings and keep dev spaces:

```bash
python run_enhancement.py \
  --host workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $GENIE_SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/kpi_benchmark.json \
  --genie-concurrent 2 \
  --no-cleanup
```

**Result:**
- Slower but safer (2 concurrent Genie calls)
- Dev spaces preserved for inspection
- Easy to debug issues

### 2. Production Run (Aggressive)

Fast production enhancement with auto-promotion:

```bash
python run_enhancement.py \
  --host workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $GENIE_SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/kpi_benchmark.json \
  --genie-concurrent 5 \
  --sql-concurrent 15 \
  --target-score 0.95 \
  --auto-promote
```

**Result:**
- Maximum speed (5 concurrent Genie calls)
- Auto-promotes if target reached
- Cleans up automatically

### 3. Unstable Environment (Sequential Fallback)

When batch mode has issues:

```bash
python run_enhancement.py \
  --no-batch \
  --host workspace.cloud.databricks.com \
  --token $DATABRICKS_TOKEN \
  --space-id $GENIE_SPACE_ID \
  --warehouse-id $WAREHOUSE_ID \
  --benchmarks benchmarks/kpi_benchmark.json
```

**Result:**
- Sequential mode (slower but most reliable)
- No concurrency issues
- Best for debugging

### 4. Using Config File

Create `config.json`:

```json
{
  "databricks_host": "workspace.cloud.databricks.com",
  "databricks_token": "dapi...",
  "space_id": "01abc123...",
  "warehouse_id": "xyz789...",
  "benchmarks": "benchmarks/kpi_benchmark.json"
}
```

Run:

```bash
python run_enhancement.py --config config.json
```

### 5. Using Environment Variables

```bash
export DATABRICKS_HOST=workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi...
export GENIE_SPACE_ID=01abc123...
export WAREHOUSE_ID=xyz789...

python run_enhancement.py \
  --benchmarks benchmarks/kpi_benchmark.json
```

## Understanding the Output

### Phase Logs

```
[1/7] Initializing clients...
[2/7] Loading benchmarks...
Loaded 12 benchmarks

[3/7] Setting up three-space architecture...
Production:   01f0f5c840c118b9824acd167525a768
Dev-Working:  01f0f5c840c118b9824acd167525a768-working
Dev-Best:     01f0f5c840c118b9824acd167525a768-best

Using BATCH scorer (13x faster)
Batch config: genie_concurrent=3, sql_concurrent=10

============================================================
ENHANCEMENT LOOP 1/3
============================================================

[4a] Scoring benchmarks (loop 1)...

============================================================
PHASE 1: Batch Genie Queries
============================================================
[INFO] Starting batch Genie calls for 12 questions
[INFO] [0] ✅ Success in 8.3s (attempt 1)
[INFO] [1] ✅ Success in 7.9s (attempt 1)
[INFO] [2] ✅ Success in 9.1s (attempt 1)
...
[INFO] Batch complete: 12/12 succeeded in 32.4s (circuit: closed)

============================================================
PHASE 2: Batch SQL Execution
============================================================
[INFO] Phase 2 complete: 12/12 SQL executions succeeded in 8.7s

============================================================
PHASE 3: Batch LLM Evaluation
============================================================
[INFO] Evaluating in 2 chunks of 10
[INFO] Phase 3 complete: 8/12 evaluations passed in 5.2s

Score: 66.7% (8/12 passed)

[4b] Generating fixes (loop 1)...
Generated 15 fixes

[4c] Applying 15 fixes (loop 1)...
Applied: 15, Failed: 0

[4d] Waiting 60s for Genie indexing...
```

### Circuit Breaker Logs

If Genie API has issues:

```
[WARN] [2] ⏱️ Timeout after 120s (attempt 1)
[INFO] [2] Retrying in 5s...
[INFO] [2] ✅ Success in 9.1s (attempt 2)
...
[ERROR] Circuit breaker: Too many failures (5) - OPENING circuit
[WARN] Circuit breaker OPEN - falling back to sequential mode
[INFO] Executing in SEQUENTIAL fallback mode
```

### Final Results

```
============================================================
ENHANCEMENT COMPLETE
============================================================
Final Score: 91.7%
Target: 90.0%
Loops: 2
Promoted: False

Results saved to: enhancement_result_20260202_143522.json
```

## Troubleshooting

### Issue: Batch mode fails with timeout errors

**Symptoms:**
```
[WARN] [2] ⏱️ Timeout after 120s (attempt 1)
[ERROR] Circuit breaker: Too many failures (5) - OPENING circuit
```

**Solutions:**

1. **Reduce concurrency:**
   ```bash
   --genie-concurrent 2
   ```

2. **Use sequential mode:**
   ```bash
   --no-batch
   ```

3. **Check Genie Space status:**
   - Is space still indexing?
   - Check Databricks UI for space status

### Issue: "Circuit breaker OPEN"

**What it means:** Too many Genie API failures, system switched to sequential fallback.

**Solutions:**

1. **Wait and retry** - Circuit auto-recovers after 60s

2. **Check Genie Space:**
   - Verify space exists
   - Check space is not in error state
   - Verify permissions

3. **Use sequential mode explicitly:**
   ```bash
   --no-batch
   ```

### Issue: Slow performance even with batch mode

**Check:**

1. **Actual mode used:**
   - Look for "Using BATCH scorer" in logs
   - If you see "Using SEQUENTIAL scorer", batch is disabled

2. **Concurrency settings:**
   ```bash
   # Increase concurrency (if API allows)
   --genie-concurrent 5 --sql-concurrent 15
   ```

3. **Network/API latency:**
   - Check if in same region as Databricks workspace
   - Check network connectivity

### Issue: Import errors for batch_scorer

**Solution:** Make sure new files are present:

```bash
ls lib/batch_scorer.py lib/batch_genie_client.py
```

If missing, you need to copy the new files.

## Performance Tuning

### For Stable Environments

```bash
# Aggressive settings - maximum speed
--genie-concurrent 7 \
--sql-concurrent 20
```

**Expected:** ~20-25s for 20 benchmarks

### For Unstable Environments

```bash
# Conservative settings - maximum reliability
--genie-concurrent 2 \
--sql-concurrent 5
```

**Expected:** ~50-60s for 20 benchmarks

### Finding Optimal Settings

Start conservative and gradually increase:

```bash
# Step 1: Try default (3 concurrent)
python run_enhancement.py ...

# Step 2: If stable, try 5 concurrent
python run_enhancement.py --genie-concurrent 5 ...

# Step 3: If still stable, try 7 concurrent
python run_enhancement.py --genie-concurrent 7 ...
```

Monitor circuit breaker logs. If circuit opens, reduce concurrency.

## Best Practices

1. **Start with defaults** - They're tested and safe

2. **Use batch mode** - Unless you have specific issues

3. **Keep dev spaces initially** - Use `--no-cleanup` for first runs

4. **Test before auto-promote** - Run without `--auto-promote` first

5. **Use config files** - Easier than long command lines

6. **Monitor logs** - Watch for circuit breaker events

7. **Tune gradually** - Don't jump to max concurrency immediately

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Enhance Genie Space

on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  enhance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run enhancement
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          GENIE_SPACE_ID: ${{ secrets.GENIE_SPACE_ID }}
          WAREHOUSE_ID: ${{ secrets.WAREHOUSE_ID }}
        run: |
          python run_enhancement.py \
            --benchmarks benchmarks/kpi_benchmark.json \
            --genie-concurrent 3 \
            --target-score 0.90
```

## Next Steps

- Read `docs/BATCH_SCORING.md` for technical details
- Read `docs/GENERALIZATION_CHANGES.md` for domain inference
- Check `benchmarks/` for example benchmark files
