# Architecture Decision: Context-Informed Reactive Fixes

> **Decision Date**: 2026-01-31
> **Status**: Approved
> **Approach**: Reactive fixes informed by full domain context

---

## Context

The original approach analyzed failures in isolation. The improvement keeps the reactive model but adds:
1. **All benchmarks as domain context** - LLM sees the full picture
2. **Best practices embedded in prompts** - Fixes follow guidelines
3. **Korean language support** - Uses `korean_question` field

## Decision

**Keep reactive fix generation, but make it context-informed:**

```
┌─────────────────────────────────────────────────────────────┐
│  SCORE (run all 20 benchmarks using korean_question)         │
│  └── Identify failures                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  ANALYZE EACH FAILURE                                        │
│  ├── The specific failure (expected vs genie SQL)           │
│  ├── ALL 20 benchmarks as domain context                    │
│  ├── Best practices reference                               │
│  └── Generate INFORMED fixes                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  APPLY fixes → VALIDATE → repeat until 20/20 pass            │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Changes from Previous Approach

| Aspect | Before | After |
|--------|--------|-------|
| **Context** | Analyze failure in isolation | Include ALL benchmarks as context |
| **Language** | English `question` | Korean `korean_question` |
| **Best Practices** | Not referenced | Embedded in prompts |
| **Fix Categories** | 4 (incl. metric_view) | 3 (metadata, sample_query, instruction) |
| **Cross-benchmark** | No pattern recognition | LLM sees patterns across all questions |

---

## Prompt Structure

Each analysis prompt now includes:

```
═══════════════════════════════════════════════════════════════
## DOMAIN CONTEXT (All 20 Benchmarks)
═══════════════════════════════════════════════════════════════
{all_benchmarks}  ← Full domain knowledge

═══════════════════════════════════════════════════════════════
## BEST PRACTICES REFERENCE
═══════════════════════════════════════════════════════════════
- How to write good synonyms (Korean → column)
- How to create sample queries (parameterized templates)
- How to write instructions (business rules)

═══════════════════════════════════════════════════════════════
## FAILED BENCHMARK TO FIX
═══════════════════════════════════════════════════════════════
{question}        ← Korean question
{expected_sql}    ← Correct SQL
{genie_sql}       ← What Genie generated
{space_config}    ← Current configuration
```

---

## Fix Categories

### 1. Metadata (synonyms, descriptions)

**Purpose**: Map Korean terms to SQL columns

**Examples**:
- "리액션" → `reaction.count`
- "추천" → `votes_up`
- "메시지" → `message.message_id`

**Fix types**:
- `add_synonym` - Add Korean term as column synonym
- `add_column_description` - Clarify column purpose
- `add_table_description` - Clarify table scope

### 2. Sample Queries (example_question_sqls)

**Purpose**: Teach Genie query patterns

**Examples**:
- Top N pattern: "가장 많은", "상위"
- Date range: "최근 7일", "30일"
- Trend: "추이", "일별"
- Deduplication: ROW_NUMBER pattern

**Fix types**:
- `add_example_query` - Add parameterized template

### 3. Instructions (text_instructions)

**Purpose**: Document business rules

**Examples**:
- Default filter: `game_code = 'inzoi'`
- Date convention: "최근 30일" = `INTERVAL 30 DAYS`
- Deduplication: Use ROW_NUMBER for snapshot tables

**Fix types**:
- `update_text_instruction` - Update instruction content

---

## Implementation

### Modified Files

```
lib/enhancer.py
├── Added: all_benchmarks parameter
├── Added: set_all_benchmarks() method
├── Added: _format_benchmarks_context() method
├── Modified: _analyze_failure() to include context
└── Removed: metric_view category

prompts/
├── metadata_analysis.txt      ← Added domain context + best practices
├── sample_query_analysis.txt  ← Added domain context + best practices
├── instruction_analysis.txt   ← Added domain context + best practices
└── metric_view_analysis.txt   ← REMOVED
```

### Usage

```python
from lib.enhancer import EnhancementPlanner

# Load all benchmarks
with open("benchmarks/benchmarks.json") as f:
    all_benchmarks = json.load(f)["benchmarks"]

# Initialize with context
planner = EnhancementPlanner(
    llm_client=llm_client,
    all_benchmarks=all_benchmarks  # Full domain context
)

# Generate fixes for failures
fixes = planner.generate_plan(
    failed_benchmarks=failures,
    space_config=current_config
)
```

---

## Benefits

1. **Cross-benchmark pattern recognition**: LLM sees that "리액션" appears in 5 benchmarks → confident synonym
2. **Consistent fixes**: Same Korean term maps to same column across all fixes
3. **Better templates**: Sample queries designed to help multiple benchmarks
4. **Domain-aware instructions**: Rules extracted from patterns across all SQL

---

## Workflow

```
1. SCORE
   - Run all 20 benchmarks with korean_question
   - Identify failures

2. PLAN (with context)
   - For each failure:
     - Analyze with ALL benchmarks as context
     - Reference best practices
     - Generate metadata/sample_query/instruction fixes

3. APPLY
   - Apply all fixes to Genie Space

4. VALIDATE
   - Re-run all 20 benchmarks
   - If failures remain → back to PLAN
   - If 20/20 pass → done
```

---

## Success Criteria

- All 20 benchmarks pass validation
- Genie generates correct SQL for all Korean questions
- Fixes are consistent across similar questions
