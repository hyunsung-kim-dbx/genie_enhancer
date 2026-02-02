# Generalization Changes to Genie Enhancer

## Goal
Make the system **domain-agnostic** by learning patterns from benchmarks instead of hardcoding domain knowledge.

## What Changed

### Before
- Prompts had generic examples (Discord, Steam)
- No systematic pattern extraction from benchmarks
- Fixes were reactive to failures only

### After
- **Two-step analysis process**:
  1. **STEP 1**: Learn domain patterns from ALL benchmarks
  2. **STEP 2**: Apply learned patterns to fix failures

## Updated Prompts

### 1. `category_metadata_add.txt`
**New Section: STEP 1 - Pattern Discovery**
- Table usage analysis (frequency, relationships)
- Metric/calculation pattern extraction
- Korean vocabulary mining across ALL benchmarks
- Date/time pattern identification
- Aggregation pattern discovery

**Enhanced: STEP 2 - Failure Analysis**
- Uses learned vocabulary map from STEP 1
- Generates descriptions based on discovered usage patterns
- Prioritizes based on frequency across full benchmark corpus

### 2. `category_instruction_fix.txt`
**New Section: STEP 1 - Domain Rule Discovery**
- Default filter pattern extraction
- Date interpretation rule mining ("최근 7일" → SQL INTERVAL)
- Calculation convention discovery (try_divide, ::decimal)
- Data deduplication rule identification
- Aggregation convention extraction

**Output: Domain Rule Book**
- Documents business rules discovered from benchmarks
- Generates instructions based on consistent patterns

### 3. `category_sample_queries_add.txt`
**New Section: STEP 1 - Query Pattern Extraction**
- Identifies query structure families (CTEs, window functions, etc.)
- Parameterizes common patterns into templates
- Calculates pattern frequency
- Converts specific queries into reusable templates

**Output: Pattern Template Library**
- Reusable query templates learned from benchmarks

### 4. `category_join_specs_add.txt`
**New Section: STEP 1 - Join Pattern Mining**
- Extracts all JOINs from expected SQL
- Determines relationship types (many-to-one, etc.)
- Analyzes join frequency
- Identifies join descriptions from questions

**Output: Join Relationship Map**
- Understanding of which tables should be joinable

### 5. `category_sql_snippets_add.txt`
**New Section: STEP 1 - SQL Pattern Mining**
- Measure patterns (aggregations like DAU, ARPU)
- Expression patterns (CASE, date transforms)
- Filter patterns (common WHERE conditions)
- Synonym extraction for each pattern

**Output: Reusable SQL Library**
- Identifies calculations that should become snippets

## How It Works Now

### Input
```
benchmarks/
├── kpi_benchmark.json        # Any domain
├── social_benchmark.json     # Any domain
└── [custom_benchmark.json]   # Any domain
```

### Processing

1. **Domain Inference** (STEP 1)
   - Analyzes ALL benchmark questions and expected SQL
   - Extracts patterns automatically:
     * Tables used and their frequency
     * Calculation formulas
     * Korean term → SQL mappings
     * Join relationships
     * Date handling conventions

2. **Fix Generation** (STEP 2)
   - Applies learned patterns to failures
   - Generates fixes that align with domain conventions
   - Uses discovered vocabulary for synonyms
   - Creates instructions based on inferred rules

### Output
```json
{
  "version": 2,
  "data_sources": {
    "tables": [/* Learned from benchmark SQL */]
  },
  "instructions": {
    "text_instructions": [/* Learned domain rules */],
    "example_question_sqls": [/* Learned patterns */],
    "join_specs": [/* Discovered relationships */],
    "sql_snippets": {
      "measures": [/* Extracted calculations */]
    }
  }
}
```

## Benefits

1. **Truly Generalizable**
   - Works for KPI domain (DAU, ARPU, retention)
   - Works for social domain (messages, reactions)
   - Works for ANY domain in benchmarks

2. **Self-Documenting**
   - Domain knowledge comes from benchmarks
   - No manual domain expertise required
   - Adapts to domain conventions automatically

3. **Pattern-Based Learning**
   - Identifies reusable patterns
   - Creates templates, not one-off fixes
   - Helps multiple failures with single fix

4. **Frequency-Aware**
   - Prioritizes high-frequency patterns
   - Focuses on most impactful fixes first

## Testing

To test with KPI domain:
```bash
python run_enhancement.py \
  --benchmarks benchmarks/kpi_benchmark.json \
  --space-id <your-space-id>
```

The system will:
1. Analyze kpi_benchmark.json to learn KPI patterns
2. Generate fixes that align with KPI conventions
3. Produce a Genie space structure appropriate for KPI domain

## Next Steps

Optional enhancements:
- [ ] Update delete prompts with same pattern-learning approach
- [ ] Add visualization of discovered patterns
- [ ] Create pattern library output for inspection
- [ ] Add confidence scores for pattern matches
