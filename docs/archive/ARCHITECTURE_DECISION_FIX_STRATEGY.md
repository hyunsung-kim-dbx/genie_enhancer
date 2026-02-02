# Architecture Decision: Fix Strategy (One-by-One vs Batch)

## Question
Should the enhancement system apply fixes one element at a time, or batch multiple fixes together?

---

## Option 1: One-by-One (Sequential) ❌ **Not Recommended**

### How it works:
```
Iteration 1: Add synonym to column A → Update space → Re-test → Measure impact
Iteration 2: Add description to table B → Update space → Re-test → Measure impact
Iteration 3: Fix join between A and B → Update space → Re-test → Measure impact
...
```

### Pros:
- ✅ Can measure impact of each individual fix
- ✅ Easy to identify which fix helped/hurt
- ✅ Clear attribution (this fix improved score by X%)
- ✅ Easy to rollback bad fixes

### Cons:
- ❌ **VERY SLOW** - Need to update space, wait for indexing (~30s), re-test after EACH fix
- ❌ Many API calls (expensive)
- ❌ Could take 50+ iterations for 50 fixes
- ❌ Impractical for production use

### Example Timeline:
- 20 failures × 2 fixes each = 40 fixes
- 40 iterations × (30s wait + 2min testing) = **100+ minutes per enhancement cycle**

---

## Option 2: Batch All Fixes (Parallel) ⭐ **RECOMMENDED**

### How it works:
```
Iteration 1:
  - Analyze ALL failures
  - Generate ALL fixes (synonyms, descriptions, joins, examples)
  - Validate ALL fixes
  - Apply ALL fixes in one update
  - Wait 30s for indexing
  - Re-test ALL benchmarks
  - Measure new score
```

### Pros:
- ✅ **FAST** - One update per iteration
- ✅ Fewer API calls (cost-efficient)
- ✅ Practical for production use
- ✅ Can still track which fixes were applied together
- ✅ Natural batching by failure analysis

### Cons:
- ⚠️ Can't isolate impact of individual fixes
- ⚠️ If score degrades, need to inspect the batch to find problematic fix
- ⚠️ All-or-nothing per iteration (but validation helps!)

### Example Timeline:
- 20 failures → Analyze all → Generate 40 fixes
- 1 iteration × (30s wait + 2min testing) = **2.5 minutes per enhancement cycle**
- **40x faster than one-by-one!**

### Mitigation for Cons:
1. **Validation Before Apply:** Catch bad fixes before they're applied
2. **Categorize Fixes:** Track fixes by type (synonyms, joins, examples)
3. **Score Tracking:** If score degrades, can inspect the batch
4. **Conservative Fixing:** LLM only recommends fixes with high confidence
5. **Rollback Option:** Keep previous config version to rollback if needed

---

## Option 3: Batch by Category (Hybrid) ⚙️ **Alternative**

### How it works:
```
Iteration 1: Apply all synonym fixes → Test → Measure
Iteration 2: Apply all description fixes → Test → Measure
Iteration 3: Apply all join fixes → Test → Measure
Iteration 4: Apply all example query fixes → Test → Measure
```

### Pros:
- ✅ Balance between speed and attribution
- ✅ Can measure impact per category
- ✅ Easier to debug than full batch

### Cons:
- ⚠️ Still slower than full batch (4-5 iterations instead of 1)
- ⚠️ More complex logic
- ⚠️ Arbitrary category boundaries

---

## Recommendation: Option 2 (Batch All) ⭐

### Why:
1. **Speed is Critical:** For practical use, we need fast iterations
2. **Validation Catches Bad Fixes:** Pre-apply validation prevents most issues
3. **LLM is Smart:** With fat prompts, LLM generates good fixes
4. **Track by Type:** We log all fixes with types/reasons for inspection
5. **Rollback Available:** Can revert to previous config if score degrades

### Implementation Strategy:

```python
def enhance(self, space_id, benchmark_results, current_space_config):
    """Batch enhancement: Apply all fixes in one iteration."""

    all_fixes = []

    # Analyze ALL failures and collect fixes
    for failure in benchmark_results["results"]:
        if not failure["passed"]:
            # LLM analyzes and recommends fixes
            fixes = self._analyze_failure(failure, current_space_config)
            all_fixes.extend(fixes)

    # Deduplicate fixes (e.g., same synonym recommended multiple times)
    unique_fixes = self._deduplicate_fixes(all_fixes)

    # Validate ALL fixes before applying
    validation = self._validate_fixes(unique_fixes, current_space_config)
    if not validation["all_valid"]:
        # Filter out invalid fixes
        unique_fixes = [f for f in unique_fixes if f["id"] in validation["valid_ids"]]

    # Apply ALL fixes to config
    updated_config = self._apply_all_fixes(current_space_config, unique_fixes)

    # Validate final config
    final_validation = self._validate_space_config(updated_config)

    if not final_validation["is_valid"]:
        raise ValueError(f"Updated config is invalid: {final_validation['errors']}")

    return {
        "changes_made": unique_fixes,  # Full list with types/reasons
        "new_space_config": updated_config,
        "validation_status": "valid",
        "stats": {
            "total_fixes": len(unique_fixes),
            "by_type": self._count_by_type(unique_fixes)
        }
    }
```

### Tracking & Debugging:

```python
# Each fix is logged with full context
{
  "type": "add_synonym",
  "table": "catalog.schema.orders",
  "column": "order_amount",
  "synonym": "revenue",
  "reasoning": "Question used 'revenue' but column is 'order_amount'",
  "question_id": "abc123",  # Which failure caused this fix
  "confidence": "high"
}
```

If score degrades, inspect the batch:
```python
# Group fixes by type to identify problem area
fixes_by_type = {
    "add_synonym": 15,
    "add_column_description": 8,
    "fix_join": 3,
    "add_example_query": 2
}

# Check if any specific category is suspicious
# E.g., if all 3 join fixes are wrong, that's the issue
```

---

## Decision: Batch All Fixes ⭐

**Rationale:**
- 40x faster → practical for production
- Validation prevents bad fixes
- Can still debug via logged fix details
- Aligns with LLM analysis workflow (analyze all failures at once)

**Trade-off Accepted:**
- Can't isolate individual fix impact
- Mitigated by validation, logging, and rollback capability

**Implementation Priority:**
- Phase 1: Batch all fixes (fast, practical)
- Phase 2: Add rollback if score degrades
- Phase 3: Optional A/B testing mode (batch vs one-by-one for research)
