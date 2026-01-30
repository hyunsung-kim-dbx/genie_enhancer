# Genie Enhancer v2 - Implementation Plan

## Executive Summary

Restructure the enhancement workflow to use:
1. **4 fix types only** (metric views, metadata, sample queries, instructions)
2. **Sequential evaluation** (one fix → evaluate → next fix)
3. **Three-space architecture** (production, dev-best, dev-working)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THREE-SPACE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│   │  PRODUCTION  │      │   DEV-BEST   │      │ DEV-WORKING  │             │
│   │    Genie     │──────│    Genie     │──────│    Genie     │             │
│   │  (Original)  │ clone│ (Best Score) │ copy │  (Testing)   │             │
│   └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      ▲                     │                      │
│         │                      │                     │                      │
│    Never touched          Updated when           All changes               │
│    during run             score improves         applied here              │
│                                │                     │                      │
│                                └─────────────────────┘                      │
│                                  Rollback if score drops                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequential Enhancement Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ONE ENHANCEMENT LOOP (~40 min)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   METRIC    │    │  METADATA   │    │   SAMPLE    │    │INSTRUCTIONS │  │
│  │   VIEWS     │───▶│   CHANGES   │───▶│   QUERIES   │───▶│             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │           │
│        ▼                  ▼                  ▼                  ▼           │
│   ┌─────────┐        ┌─────────┐        ┌─────────┐        ┌─────────┐     │
│   │EVALUATE │        │EVALUATE │        │EVALUATE │        │EVALUATE │     │
│   │ + LOG   │        │ + LOG   │        │ + LOG   │        │ + LOG   │     │
│   └─────────┘        └─────────┘        └─────────┘        └─────────┘     │
│        │                  │                  │                  │           │
│        ▼                  ▼                  ▼                  ▼           │
│   Score better?      Score better?      Score better?      Score better?   │
│   Yes → Update       Yes → Update       Yes → Update       Yes → Update    │
│         dev-best           dev-best           dev-best           dev-best  │
│   No → Rollback      No → Rollback      No → Rollback      No → Rollback   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fix Types (4 Only)

### 1. Metric Views
| Action | Description |
|--------|-------------|
| `create_metric_view` | Create new metric view in Unity Catalog + add to space |
| `delete_metric_view` | Remove metric view from space config (not from UC) |

### 2. Metadata
| Action | Description |
|--------|-------------|
| `add_table_description` | Add/update table description |
| `add_column_description` | Add/update column description |
| `add_synonym` | Add synonym to column |
| `delete_synonym` | Remove synonym from column |

### 3. Sample Queries
| Action | Description |
|--------|-------------|
| `add_example_query` | Add parameterized query template |
| `delete_example_query` | Remove query template by ID |

### 4. Instructions
| Action | Description |
|--------|-------------|
| `update_text_instruction` | Update/replace text instruction content |

**REMOVED fix types:**
- ~~`add_join`~~ - No joins
- ~~`fix_join`~~ - No joins
- ~~`enable_get_example_values`~~ - Removed
- ~~`enable_build_value_dictionary`~~ - Removed
- ~~Filters/Measures/SQL Snippets~~ - Removed

---

## Detailed Workflow

### Phase 1: Initialization

```python
def initialize_enhancement():
    """
    1. Export production Genie config
    2. Delete any existing dev spaces (fresh start)
    3. Clone production → dev-working
    4. Clone production → dev-best
    5. Score initial state on dev-working
    6. Store initial_score as best_score
    """
```

### Phase 2: Analysis

```python
def analyze_failures():
    """
    For each failed benchmark:
    1. Call LLM with simplified prompt (4 fix types only)
    2. Collect ALL recommended fixes
    3. Group fixes by type:
       - metric_view_fixes[]
       - metadata_fixes[]
       - sample_query_fixes[]
       - instruction_fixes[]
    4. Deduplicate within each group
    """
```

### Phase 3: Sequential Application

```python
def apply_fixes_sequentially():
    """
    For each fix_type in [metric_views, metadata, sample_queries, instructions]:

        # Get fixes for this type
        fixes = grouped_fixes[fix_type]

        if not fixes:
            log(f"No {fix_type} fixes to apply")
            continue

        # Apply ONE fix at a time
        for fix in fixes:

            # Apply to dev-working
            apply_fix(dev_working_space, fix)

            # Wait for indexing
            wait(indexing_time)

            # Evaluate
            new_score = score_benchmarks(dev_working_space)

            # Log progress (visible in app)
            log_progress(fix_type, fix, new_score, best_score)

            # Decision
            if new_score > best_score:
                # Improvement! Update dev-best
                copy_config(dev_working → dev_best)
                best_score = new_score
                log(f"✅ Score improved: {best_score}")
            else:
                # No improvement - rollback
                copy_config(dev_best → dev_working)
                log(f"⏪ Rolled back, keeping best: {best_score}")
```

### Phase 4: Completion

```python
def complete_enhancement():
    """
    1. Show final results summary
    2. Ask user: "Promote dev-best to production?"
       - Yes → Apply dev-best config to production, delete dev spaces
       - No → Keep all three spaces for manual review
    3. Generate report
    """
```

---

## File Changes Required

### 1. New Files

| File | Purpose |
|------|---------|
| `pipeline/space_cloner.py` | Clone/delete Genie spaces |
| `pipeline/fix_applier.py` | Apply individual fixes |
| `pipeline/sequential_enhancer.py` | New enhancement orchestrator |
| `prompts/simplified_analysis.txt` | New prompt (4 fix types only) |

### 2. Modified Files

| File | Changes |
|------|---------|
| `job/enhancement_job.py` | Replace main loop with sequential approach |
| `job/config.py` | Add new config options (space naming, cleanup) |
| `pipeline/llm_enhancer.py` | Simplify to 4 fix types |
| `prompts/best_practices.txt` | Remove joins, filters, measures sections |
| `prompts/analysis_prompt.txt` | Simplify output format |
| `databricks_apps/interactive_enhancement_app.py` | Show 3-space status |

### 3. Files to Keep (No Changes)

| File | Reason |
|------|--------|
| `pipeline/genie_client.py` | Core Genie API client |
| `pipeline/benchmark_scorer.py` | Scoring logic unchanged |
| `pipeline/sql_executor.py` | SQL execution unchanged |
| `pipeline/reporter.py` | Reporting unchanged |

---

## New Configuration Options

```python
class EnhancementConfig:
    # Existing
    space_id: str              # Production space ID
    target_score: float
    max_iterations: int

    # NEW: Three-space naming
    dev_working_suffix: str = "_dev_working"
    dev_best_suffix: str = "_dev_best"

    # NEW: Cleanup behavior
    cleanup_on_success: str = "ask"  # "ask" | "promote" | "keep"
    always_fresh_start: bool = True  # Delete existing dev spaces

    # NEW: Fix type toggles (enable/disable specific types)
    enable_metric_views: bool = True
    enable_metadata: bool = True
    enable_sample_queries: bool = True
    enable_instructions: bool = True
```

---

## Simplified LLM Prompt Structure

```
# YOUR TASK: Analyze Failure and Recommend Fixes

You can ONLY recommend these 4 fix types:

## 1. METRIC VIEWS
- create_metric_view: For complex metrics, ratios, multi-dimensional analysis
- delete_metric_view: Remove unhelpful metric views

## 2. METADATA
- add_table_description: Improve table understanding
- add_column_description: Improve column understanding
- add_synonym / delete_synonym: Help term matching

## 3. SAMPLE QUERIES
- add_example_query: Teach query patterns (parameterized templates)
- delete_example_query: Remove confusing examples

## 4. INSTRUCTIONS
- update_text_instruction: Add/update general guidance

DO NOT recommend:
- Joins (use metric views instead)
- Filters/Measures/SQL Snippets (removed)
- get_example_values / build_value_dictionary (removed)
```

---

## Progress Logging (Verbose for App)

Each step logs detailed progress visible in the dashboard:

```
═══════════════════════════════════════════════════════════════════════════════
LOOP 1 - STARTING
═══════════════════════════════════════════════════════════════════════════════

[INIT] Cloning production space...
  → Created: My Genie Space_dev_working (space_id: abc123)
  → Created: My Genie Space_dev_best (space_id: def456)
  → Initial score: 45.0% (9/20 passed)

───────────────────────────────────────────────────────────────────────────────
PHASE 1: METRIC VIEWS (2 fixes)
───────────────────────────────────────────────────────────────────────────────

[1/2] Creating metric view: revenue_metrics
  → Applied to dev-working
  → Waiting 60s for indexing...
  → Scoring benchmarks...
  → New score: 50.0% (10/20 passed)
  → ✅ IMPROVED! Updating dev-best. Best score: 50.0%

[2/2] Creating metric view: customer_metrics
  → Applied to dev-working
  → Waiting 60s for indexing...
  → Scoring benchmarks...
  → New score: 48.0% (9.6/20 passed)
  → ⏪ NO IMPROVEMENT. Rolling back to dev-best.

───────────────────────────────────────────────────────────────────────────────
PHASE 2: METADATA (5 fixes)
───────────────────────────────────────────────────────────────────────────────

[1/5] Adding synonym 'revenue' to orders.amount
  → Applied to dev-working
  → Waiting 60s for indexing...
  → Scoring benchmarks...
  → New score: 55.0% (11/20 passed)
  → ✅ IMPROVED! Updating dev-best. Best score: 55.0%

... (continues for all fixes)

───────────────────────────────────────────────────────────────────────────────
PHASE 3: SAMPLE QUERIES (1 fix)
───────────────────────────────────────────────────────────────────────────────

...

───────────────────────────────────────────────────────────────────────────────
PHASE 4: INSTRUCTIONS (1 fix)
───────────────────────────────────────────────────────────────────────────────

...

═══════════════════════════════════════════════════════════════════════════════
LOOP 1 - COMPLETE
═══════════════════════════════════════════════════════════════════════════════

Initial score:  45.0%
Final score:    65.0%
Improvement:    +20.0%
Duration:       42 minutes

What would you like to do?
  [1] Promote dev-best to production
  [2] Keep all spaces for review
  [3] Run another loop
```

---

## API Requirements

### Space Cloning API

Need to verify Databricks API supports:
```
POST /api/2.0/genie/spaces
{
  "title": "My Space_dev_working",
  "description": "Dev copy for enhancement",
  "warehouse_id": "...",
  "serialized_space": "..." // Copied from production
}
```

### Space Deletion API

```
DELETE /api/2.0/genie/spaces/{space_id}
```

---

## Implementation Order

### Step 1: Space Management (Day 1)
- [ ] Implement `SpaceCloner` class
- [ ] Add clone, delete, copy_config methods
- [ ] Test with real Genie spaces

### Step 2: Simplified Prompts (Day 1)
- [ ] Create `simplified_analysis.txt`
- [ ] Update `best_practices.txt` (remove joins, etc.)
- [ ] Update `PromptLoader` for new prompt

### Step 3: Fix Applier (Day 2)
- [ ] Create `FixApplier` class
- [ ] Implement apply/rollback for each fix type
- [ ] Handle one-at-a-time application

### Step 4: Sequential Enhancer (Day 2-3)
- [ ] Create `SequentialEnhancer` class
- [ ] Implement main loop with 4 phases
- [ ] Add verbose logging for app visibility

### Step 5: Job Integration (Day 3)
- [ ] Update `EnhancementJob` to use new flow
- [ ] Add config options
- [ ] Implement completion prompts

### Step 6: Dashboard Updates (Day 4)
- [ ] Show three-space status
- [ ] Real-time progress updates
- [ ] Completion action buttons

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Production space accidentally modified | Never touch production; all changes on dev-working |
| Orphaned dev spaces | Track created spaces; cleanup on job completion |
| Long loop times (40+ min) | Verbose logging keeps user informed; can cancel |
| API rate limits | Add delays between operations |
| Clone fails mid-process | Cleanup partial creates; restart fresh |

---

## Success Criteria

1. ✅ Production Genie is NEVER modified during enhancement
2. ✅ Only 4 fix types are ever applied
3. ✅ Each fix is evaluated individually before next
4. ✅ Best configuration is always preserved
5. ✅ User can see real-time progress in app
6. ✅ User decides final promotion/cleanup

---

## Questions Resolved

| Question | Answer |
|----------|--------|
| Loop strategy | One fix at a time |
| Delete behavior | Add and rollback (no explicit delete) |
| Query style | Full parameterized templates |
| Best-dev update | On improvement only |
| End cleanup | User decides |
| Space naming | Suffix pattern (`_dev_working`, `_dev_best`) |
| Reuse spaces | Always fresh start |
