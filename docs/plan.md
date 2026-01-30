# Genie Space Self-Healing Enhancement System - Implementation Plan

## Overview

This system implements an automated, iterative improvement loop for Databricks Genie Spaces using benchmark-driven evaluation and LLM-powered enhancements.

### Core Concept
```
┌─────────────────────────────────────────────────────────────────┐
│                    Self-Healing Loop                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Benchmark Scorer  →  Score < Threshold?  →  LLM Enhancer     │
│       ↑                                            ↓            │
│       │                                      Update Space       │
│       │                                            ↓            │
│       └────────────────────────────────────────────┘            │
│                                                                 │
│  Report to Databricks Apps at each iteration                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
genie_enhancer/
├── pipeline/                  # Core enhancement logic
│   ├── __init__.py
│   ├── benchmark_scorer.py   # Runs Q&A pairs against Genie
│   ├── llm_enhancer.py       # LLM-based space improvement
│   ├── genie_client.py       # Genie Conversational API wrapper
│   ├── space_updater.py      # Genie Space API wrapper
│   ├── evaluator.py          # Score calculation & analysis
│   └── reporter.py           # Report results to Databricks Apps
│
├── prompts/                  # LLM prompt templates ⭐ NEW
│   ├── __init__.py
│   ├── best_practices.txt    # Genie best practices knowledge base
│   ├── analysis_prompt.txt   # Failure analysis prompt template
│   ├── fix_generation.txt    # Fix generation prompt template
│   └── answer_comparison.txt # Answer comparison prompt for scoring
│
├── job/                      # Databricks job configuration
│   ├── __init__.py
│   ├── enhancement_job.py    # Main orchestration job
│   ├── config.py             # Job parameters & configuration
│   └── job_definition.json   # Databricks job JSON definition
│
├── doc/                      # Documentation (already exists)
│   └── ...
│
├── tests/                    # Unit and integration tests
│   ├── test_benchmark_scorer.py
│   ├── test_llm_enhancer.py
│   └── test_integration.py
│
├── notebooks/                # Development & debugging notebooks
│   ├── 01_test_scorer.py
│   ├── 02_test_enhancer.py
│   └── 03_run_iteration.py
│
└── requirements.txt          # Python dependencies
```

---

## Prompt Management Strategy ⭐ **CRITICAL FOR SUCCESS**

### Why Prompts are First-Class Assets

The "fat prompt" approach makes prompts **critical infrastructure**:
1. They contain all domain knowledge about Genie best practices
2. Quality of fixes depends directly on prompt quality
3. Prompts are easier to iterate/improve than code
4. Prompts can be versioned and A/B tested

### Prompt Library Structure

```
prompts/
├── best_practices.txt        # Complete Genie best practices (from doc/)
├── analysis_prompt.txt       # Template for analyzing failures
├── fix_generation.txt        # Template for generating fixes
├── answer_comparison.txt     # Template for comparing answers
└── prompt_loader.py          # Helper to load and format prompts
```

### Best Practices Knowledge Base (`prompts/best_practices.txt`)

**Content Source:** Extracted from:
- `doc/genie_best_practice_for_agent_to_remember.md`
- `doc/Genie_Space_Best_Practices.md`
- `doc/Genie_Space_API_Reference.md`

**Sections to Include:**
1. **Core Principles** (Metadata quality = Genie quality)
2. **Table/Column Descriptions** (What makes a good description)
3. **Synonyms Strategy** (What synonyms to add)
4. **Join Specifications** (Relationship type markers, format rules)
5. **Example Query Patterns** (How to create good examples)
6. **SQL Snippets** (Filters, expressions, measures)
7. **Common Issues → Fixes Mapping**
8. **Spark SQL Syntax Rules** (Date literals, string literals, etc.)
9. **Schema Requirements** (UUID format, sorting, array formatting)

**Format:** Plain text with clear sections, examples, and ❌/✅ indicators

### Prompt Loader Implementation

```python
# prompts/prompt_loader.py
from pathlib import Path
from typing import Dict

class PromptLoader:
    """Load and manage prompt templates."""

    def __init__(self, prompts_dir: Path = None):
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        self.prompts_dir = prompts_dir
        self._cache = {}

    def load(self, prompt_name: str) -> str:
        """Load prompt template from file."""
        if prompt_name not in self._cache:
            file_path = self.prompts_dir / f"{prompt_name}.txt"
            self._cache[prompt_name] = file_path.read_text(encoding='utf-8')
        return self._cache[prompt_name]

    def format_analysis_prompt(self,
                               question: str,
                               expected_sql: str,
                               genie_sql: str,
                               space_config: Dict) -> str:
        """Format failure analysis prompt with context."""
        best_practices = self.load("best_practices")
        template = self.load("analysis_prompt")

        return template.format(
            best_practices=best_practices,
            question=question,
            expected_sql=expected_sql,
            genie_sql=genie_sql if genie_sql else "None (no SQL generated)",
            space_config=self._format_space_config(space_config)
        )

    def format_answer_comparison_prompt(self,
                                       question: str,
                                       expected_result: str,
                                       genie_result: str) -> str:
        """Format answer comparison prompt for scoring."""
        template = self.load("answer_comparison")

        return template.format(
            question=question,
            expected_result=expected_result,
            genie_result=genie_result
        )

    def _format_space_config(self, config: Dict) -> str:
        """Format space config for readability in prompt."""
        import json
        return json.dumps(config, indent=2)
```

### Prompt Versioning Strategy

**Why:** As we learn what works, we'll want to improve prompts without breaking production.

**Approach:**
```
prompts/
├── v1/
│   ├── best_practices.txt
│   ├── analysis_prompt.txt
│   └── ...
├── v2/  # Improved version after learnings
│   ├── best_practices.txt  # Updated with new patterns
│   ├── analysis_prompt.txt
│   └── ...
└── active -> v2/  # Symlink to active version
```

**Job Configuration:**
```python
JOB_PARAMS = {
    ...
    "prompt_version": "v2",  # Can override for testing
}
```

### Prompt Improvement Workflow

1. **Collect failures** where LLM suggested bad fixes
2. **Analyze patterns** in bad suggestions
3. **Update best_practices.txt** with missing knowledge
4. **Refine analysis_prompt.txt** with clearer instructions
5. **Test on historical failures** to validate improvement
6. **Deploy as new version** (v3, v4, etc.)

### Example Prompt File Structure

**`prompts/best_practices.txt`:**
```
# Genie Space Best Practices - Complete Knowledge Base

## 🎯 Core Principle
METADATA QUALITY = GENIE QUALITY
Genie understands your data through metadata. Poor metadata → poor results.

## 📊 Table Descriptions

### What Makes a GOOD Table Description?
MUST include:
- What the table represents
- Scope of data (what's included AND excluded)
- Conditions for when Genie should use this table
- Lifecycle of entities

✅ GOOD Example:
"Contains all completed customer orders since 2020. Each row is one order
transaction. Does NOT include pending orders (use orders_pending table).
Use for revenue analysis and purchase history."

❌ BAD Example:
"Orders table"

[Continue with all sections from best practices docs...]
```

**`prompts/analysis_prompt.txt`:**
```
{best_practices}

---

# Your Task: Analyze Genie Space Failure

You are an expert at analyzing Genie Space failures. Use the best practices
above to guide your analysis.

## Failed Question
**Question:** {question}

**Expected SQL:**
{expected_sql}

**Genie's Generated SQL:**
{genie_sql}

**Current Space Configuration:**
{space_config}

[Rest of analysis instructions...]
```

### Benefits of This Approach

1. ✅ **Separation of Concerns** - Prompts separate from code
2. ✅ **Easy to Update** - Change prompts without code deployment
3. ✅ **Version Control** - Track prompt improvements over time
4. ✅ **A/B Testing** - Compare v1 vs v2 prompts
5. ✅ **Team Collaboration** - Non-engineers can improve prompts
6. ✅ **Documentation** - Prompts serve as living documentation

---

## Component 1: Benchmark Scorer (`pipeline/benchmark_scorer.py`)

### Purpose
Tests Genie Space by running Q&A pairs through the Conversational API and comparing results.

### Key Responsibilities
1. Load benchmark Q&A dataset
2. For each question:
   - Start conversation with Genie
   - Wait for SQL generation
   - Execute generated SQL
   - Extract results
3. Compare Genie's answer with expected answer using LLM judge
4. Calculate pass/fail for each question
5. Return overall score

### Implementation Approach

```python
class BenchmarkScorer:
    def __init__(self, genie_client, llm_client, config):
        """
        Args:
            genie_client: GenieConversationalClient for asking questions
            llm_client: LLM for comparing answers
            config: Scoring configuration
        """

    def score(self, benchmarks: List[Dict]) -> Dict:
        """
        Run all benchmarks and calculate score.

        Args:
            benchmarks: List of {question, expected_answer, ...}

        Returns:
            {
                "score": 0.85,  # 85% pass rate
                "total": 20,
                "passed": 17,
                "failed": 3,
                "results": [
                    {
                        "question": "...",
                        "expected_sql": "...",
                        "genie_sql": "...",
                        "expected_result": {...},
                        "genie_result": {...},
                        "passed": True/False,
                        "failure_reason": "..." if failed,
                        "failure_category": "missing_join" | "wrong_column" | ...
                    }
                ],
                "timestamp": "2026-01-29T10:30:00Z"
            }
        """
```

### Answer Comparison Strategy ⭐ **Using Fat Prompt**

**Recommended: LLM Judge with Domain Knowledge**

Use LLM with comprehensive prompt that includes:
- Understanding of SQL semantics
- Genie-specific answer formats
- Tolerance for equivalent expressions (e.g., SUM(x) vs SUM(x*1))
- Date/time format variations

```python
from prompts.prompt_loader import PromptLoader

class BenchmarkScorer:
    def __init__(self, genie_client, llm_client, config):
        self.genie_client = genie_client
        self.llm_client = llm_client
        self.config = config
        self.prompt_loader = PromptLoader()

    def _compare_answers(self, question, expected, actual) -> Dict:
        """Compare expected vs actual answer using LLM judge."""
        # Use fat prompt for comparison
        prompt = self.prompt_loader.format_answer_comparison_prompt(
            question=question,
            expected_result=expected,
            genie_result=actual
        )

        response = self.llm_client.generate(prompt, temperature=0.1)

        # Parse response for pass/fail + reasoning
        return self._parse_comparison_result(response)
```

**Alternative Options:**

**Option 1: SQL-based comparison** (Simple but brittle)
- Normalize both SQLs and compare
- Issues: Same result, different SQL

**Option 2: Result-based comparison** (More accurate but slower)
- Execute both SQLs
- Compare result sets
- Issues: Execution overhead

**Hybrid Approach** (Best of both worlds):
1. Quick SQL normalization check (fast path)
2. If SQLs differ, execute and compare results
3. If results differ, use LLM judge for semantic equivalence

### Failure Categorization

Critical for targeted fixes:
```python
FAILURE_CATEGORIES = {
    "missing_table": "Genie didn't use the correct table",
    "missing_column": "Genie didn't find the right column",
    "wrong_join": "Join condition was incorrect",
    "missing_join": "Required join was not performed",
    "wrong_aggregation": "Aggregation function was wrong",
    "wrong_filter": "Filter condition was wrong",
    "sql_syntax_error": "Generated SQL had syntax errors",
    "no_sql_generated": "Genie didn't generate any SQL",
    "execution_failed": "Generated SQL failed to execute"
}
```

---

## Component 2: LLM Enhancer (`pipeline/llm_enhancer.py`)

### Purpose
Analyzes benchmark failures and improves Genie Space configuration using LLM reasoning.

### Key Responsibilities
1. Analyze failure patterns from benchmark results
2. Identify root causes (missing metadata, poor joins, etc.)
3. Generate targeted fixes:
   - Add/update table/column descriptions
   - Add synonyms for columns
   - Add/update example queries
   - Fix/add join specifications
   - Update text instructions
   - Create/update metric views (if applicable)
4. Validate fixes before applying
5. Track what was changed

### Implementation Approach

```python
from prompts.prompt_loader import PromptLoader

class LLMEnhancer:
    def __init__(self, llm_client, space_client, config):
        """
        Args:
            llm_client: LLM for analysis and generation
            space_client: SpaceUpdater for applying changes
            config: Enhancement configuration
        """
        self.llm_client = llm_client
        self.space_client = space_client
        self.config = config
        self.prompt_loader = PromptLoader()  # Load fat prompts

    def enhance(self,
                space_id: str,
                benchmark_results: Dict,
                current_space_config: Dict) -> Dict:
        """
        Analyze failures and improve space configuration.

        Args:
            space_id: Genie Space ID
            benchmark_results: Output from BenchmarkScorer
            current_space_config: Current GenieSpaceExport JSON

        Returns:
            {
                "changes_made": [
                    {
                        "type": "add_synonym",
                        "table": "...",
                        "column": "...",
                        "synonym": "...",
                        "reason": "Question used term '...' but column is named '...'"
                    },
                    {
                        "type": "add_example_query",
                        "question": "...",
                        "sql": "...",
                        "reason": "Pattern not covered in existing examples"
                    },
                    {
                        "type": "update_join",
                        "tables": ["...", "..."],
                        "old_join": "...",
                        "new_join": "...",
                        "reason": "Join was missing relationship type marker"
                    }
                ],
                "new_space_config": {...},  # Updated GenieSpaceExport
                "validation_status": "valid" | "invalid",
                "validation_errors": [...]
            }
        """
        changes_made = []

        # Analyze each failure using fat prompt
        for failure in benchmark_results["results"]:
            if not failure["passed"]:
                # Format analysis prompt with best practices
                prompt = self.prompt_loader.format_analysis_prompt(
                    question=failure["question"],
                    expected_sql=failure["expected_sql"],
                    genie_sql=failure["genie_sql"],
                    space_config=current_space_config
                )

                # Call LLM with fat prompt
                analysis = self.llm_client.generate(
                    prompt=prompt,
                    temperature=0.1,  # Low temp for consistent analysis
                    max_tokens=2000
                )

                # Parse recommended fixes from LLM response
                fixes = self._parse_fixes(analysis)

                # Apply fixes to config
                for fix in fixes:
                    self._apply_fix(current_space_config, fix)
                    changes_made.append(fix)

        # Validate updated config
        validation = self._validate_config(current_space_config)

        return {
            "changes_made": changes_made,
            "new_space_config": current_space_config,
            "validation_status": validation["status"],
            "validation_errors": validation.get("errors", [])
        }
```

### Enhancement Strategies

#### 1. Missing Table/Column Detection
```python
def fix_missing_table_column(failure: Dict) -> List[Dict]:
    """
    Analyze why Genie didn't find the right table/column.

    Strategy:
    1. Check if table/column has description
    2. Add description if missing
    3. Add synonyms from the question
    4. Enable get_example_values if relevant
    """
```

#### 2. Join Improvements
```python
def fix_join_issues(failures: List[Dict]) -> List[Dict]:
    """
    Fix join-related failures.

    Strategy:
    1. Check if join exists in join_specs
    2. If missing, add join spec with relationship type
    3. If exists, verify relationship type marker
    4. Add comment explaining the join
    """
```

#### 3. Example Query Enhancement
```python
def add_example_queries(failures: List[Dict]) -> List[Dict]:
    """
    Add example queries for patterns Genie struggles with.

    Strategy:
    1. Identify question patterns from failures
    2. Group similar patterns
    3. Create parameterized example for each pattern
    4. Add to example_question_sqls
    """
```

#### 4. Instruction Updates
```python
def update_instructions(failures: List[Dict]) -> List[Dict]:
    """
    Update text instructions with business rules.

    Strategy:
    1. Extract business rules from failed questions
    2. Add to text_instructions
    3. Keep instructions concise and clear
    """
```

### LLM Prompt Design ⭐ **"FAT PROMPT" APPROACH**

**Strategy:** Embed all Genie Space best practices directly in the prompt so the LLM has complete domain knowledge.

**Best Practices to Include:**
1. Metadata quality guidelines from `genie_best_practice_for_agent_to_remember.md`
2. Schema structure from `Genie_Space_API_Reference.md`
3. Join formatting rules (relationship type markers)
4. Synonym generation strategies
5. Example query patterns
6. Common failure patterns and fixes

**Analysis Prompt Template:**
```python
GENIE_BEST_PRACTICES = """
# Genie Space Best Practices (Critical Domain Knowledge)

## Core Principle
METADATA QUALITY = GENIE QUALITY
Genie understands data through metadata. Poor metadata → poor results.

## 1. Table Descriptions (MUST include)
- What the table represents
- Scope of data (what's included AND excluded)
- Conditions for when Genie should use this table
- Lifecycle information

Example GOOD:
"Contains all completed customer orders since 2020. Each row is one order transaction.
Does NOT include pending orders (use orders_pending). Use for revenue analysis and purchase history."

Example BAD:
"Orders table"

## 2. Column Descriptions (MUST include)
- What the field represents
- When to use this field
- Business rules that apply

Example GOOD:
"Total order value in USD. Use for revenue calculations. Does NOT include tax or shipping."

Example BAD:
"Order amount"

## 3. Synonyms (CRITICAL for Natural Language!)
Add terms users actually say:
- Column name variations (camelCase, snake_case)
- Business terms
- Common aliases
- Acronyms

Example:
column_name: "order_amount"
synonyms: ["revenue", "sales", "total", "amount", "order value"]

## 4. Column Settings
- exclude: Set true to hide from Genie (default false)
- get_example_values: Enable for date and categorical columns
- build_value_dictionary: Enable for categorical fields with finite values

## 5. Joins (CRITICAL FORMAT!)
MUST include relationship type marker!

MANY_TO_ONE (multiple left → one right):
{
  "sql": [
    "t.customer_id = c.customer_id ",
    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
  ],
  "comment": ["MANY-TO-ONE: Multiple orders belong to one customer"]
}

ONE_TO_MANY (one left → multiple right):
{
  "sql": [
    "c.customer_id = t.customer_id ",
    "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_MANY--"
  ],
  "comment": ["ONE-TO-MANY: One customer has multiple orders"]
}

Format Rules:
- Use = not ==
- MUST include --rt=FROM_RELATIONSHIP_TYPE_*-- marker
- Valid types: MANY_TO_ONE, ONE_TO_MANY, MANY_TO_MANY, ONE_TO_ONE
- Use comment field, NOT instructions
- SQL lines should end with space

## 6. Example Question SQLs (Teaching Patterns)
Purpose: Teach Genie query patterns, NOT raw Q&A storage
- Use parameterized templates for common patterns
- Include CTEs for complex logic
- Add usage_guidance for when to use
- Group similar patterns into one template

## 7. SQL Snippets (Building Blocks)
MUST include full table name (catalog.schema.table.column)!

Filters (WHERE conditions):
{
  "sql": ["catalog.schema.customers.status = 'approved'"],
  "display_name": "Active customers",
  "synonyms": ["active", "current", "live"]
}

Measures (Aggregations):
{
  "alias": "total_revenue",
  "sql": ["SUM(catalog.schema.orders.amount)"],
  "display_name": "Total revenue",
  "synonyms": ["revenue", "sales", "gross revenue"]
}

## 8. Benchmarks (Evaluation)
Include ALL Q&A pairs for evaluation
- Every question + SQL = benchmark
- These are success criteria
- answer is an ARRAY: [{"format": "SQL", "content": [...]}]

## Common Issues → What Fixes Them
- Query uses wrong fields → Column descriptions + Synonyms
- Incorrect calculation → Example queries + SQL functions
- "No data available" (but exists) → Table descriptions + Synonyms
- Answers about out-of-scope data → Table descriptions (scope clarity)
- Inconsistent answers → Example queries + SQL functions
- Wrong output format → Example queries + Field descriptions

## Spark SQL Syntax Rules (CRITICAL!)
Date Literals - MUST quote:
✅ WHERE event_date >= DATE '2025-08-18'
✅ WHERE event_date >= '2025-08-18'
❌ WHERE event_date >= DATE 2025-08-18  (WRONG!)

String Literals - Single quotes:
✅ WHERE status = 'active'
❌ WHERE status = active  (treated as column)
"""

ANALYSIS_PROMPT = f"""
{GENIE_BEST_PRACTICES}

---

# Your Task: Analyze Genie Space Failure

You are an expert at analyzing why a Genie Space (Databricks natural language to SQL system)
failed to answer questions correctly. Use the best practices above to guide your analysis.

## Failed Question Analysis

**Question:** {{question}}

**Expected SQL:**
{{expected_sql}}

**Genie's Generated SQL:**
{{genie_sql}}
(If None, Genie failed to generate any SQL)

**Current Space Configuration:**
{{space_config}}

## Analysis Instructions

1. **Identify Root Cause:**
   - Is metadata missing or incomplete?
   - Are synonyms missing for terms in the question?
   - Are joins missing or incorrectly formatted?
   - Are example queries needed for this pattern?
   - Is the SQL syntax incorrect?

2. **Match to Best Practices:**
   - Which best practice was violated?
   - What specific metadata is missing?
   - What should be added/updated?

3. **Generate Specific Fixes:**
   - Be precise: specify exact table, column, value
   - Follow the schema format exactly
   - Include reasoning for each fix

## Output Format

Return your analysis as JSON:
{{
  "root_cause": "Brief description of why Genie failed",
  "best_practice_violated": "Which best practice from above",
  "missing_elements": [
    "Specific missing metadata, synonyms, etc."
  ],
  "recommended_fixes": [
    {{
      "type": "add_synonym",
      "table": "catalog.schema.table",
      "column": "column_name",
      "synonym": "term_from_question",
      "reasoning": "Question used 'X' but column is 'Y'"
    }},
    {{
      "type": "add_column_description",
      "table": "catalog.schema.table",
      "column": "column_name",
      "description": ["New description following best practices"],
      "reasoning": "Column had no description"
    }},
    {{
      "type": "fix_join",
      "left_table": "catalog.schema.table1",
      "right_table": "catalog.schema.table2",
      "new_join_spec": {{
        "left": {{"identifier": "...", "alias": "..."}},
        "right": {{"identifier": "...", "alias": "..."}},
        "sql": ["... = ... ", "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"],
        "comment": ["Description"]
      }},
      "reasoning": "Join was missing relationship type marker"
    }},
    {{
      "type": "add_example_query",
      "pattern": "Pattern name (e.g., top N by metric)",
      "question": ["Parameterized question template"],
      "sql": ["Parameterized SQL"],
      "parameters": [
        {{"name": "param_name", "type_hint": "TYPE", "description": ["..."]}}
      ],
      "usage_guidance": ["When to use this pattern"],
      "reasoning": "This query pattern not covered in examples"
    }}
  ]
}}

IMPORTANT:
- All table identifiers must be catalog.schema.table format
- All SQL must follow Spark SQL syntax (quoted date literals!)
- All joins must include relationship type markers
- All fixes must reference specific elements from space_config
- Be conservative: only recommend changes that directly fix the failure
"""
```

**Benefits of Fat Prompt:**
1. ✅ LLM has complete domain knowledge
2. ✅ Fixes are aligned with Databricks best practices
3. ✅ Consistent quality across all iterations
4. ✅ Reduces trial-and-error
5. ✅ Self-documenting (prompt explains reasoning)

---

## Component 3: Genie Client (`pipeline/genie_client.py`)

### Purpose
Wrapper around Genie Conversational API for asking questions.

### Key Features
- Start conversations
- Poll for completion
- Handle timeouts and retries
- Extract SQL and results from responses

### Implementation
```python
class GenieConversationalClient:
    def __init__(self, host: str, token: str, space_id: str):
        """Initialize client with credentials."""

    def ask(self, question: str, timeout: int = 120) -> Dict:
        """
        Ask question and wait for answer.

        Returns:
            {
                "question": str,
                "conversation_id": str,
                "message_id": str,
                "status": "COMPLETED" | "FAILED",
                "sql": str or None,
                "result": {...} or None,
                "error": str or None
            }
        """
```

---

## Component 4: Space Updater (`pipeline/space_updater.py`)

### Purpose
Wrapper around Genie Space API for exporting/updating configurations.

### Key Features
- Export current space configuration
- Update space with new configuration
- Validate changes before applying
- Handle API errors gracefully

### Implementation
```python
class SpaceUpdater:
    def __init__(self, host: str, token: str):
        """Initialize client with credentials."""

    def export_space(self, space_id: str) -> Dict:
        """Export space configuration as GenieSpaceExport."""

    def update_space(self, space_id: str, serialized_space: str) -> Dict:
        """Update space with new configuration."""

    def validate_config(self, config: Dict) -> Dict:
        """Validate GenieSpaceExport before applying."""
```

---

## Component 5: Reporter (`pipeline/reporter.py`)

### Purpose
Report progress to Databricks Apps or dashboards.

### What to Report
- Current iteration number
- Current benchmark score
- Score trend (improving/degrading)
- Changes made in this iteration
- Failures by category
- Time taken for iteration
- ETA to threshold (if applicable)

### Implementation
```python
class ProgressReporter:
    def __init__(self, config: Dict):
        """
        Config includes:
        - report_to: "databricks_app" | "table" | "file"
        - table_name: for "table" mode
        - app_endpoint: for "databricks_app" mode
        """

    def report(self, iteration_data: Dict) -> None:
        """
        Report iteration results.

        Args:
            iteration_data: {
                "iteration": 1,
                "timestamp": "...",
                "score": 0.85,
                "score_delta": +0.15,
                "changes_made": [...],
                "failures_by_category": {...},
                "duration_seconds": 120
            }
        """
```

### Reporting Options

**Option 1: Write to Delta Table** (Recommended ⭐)
```python
def report_to_table(data: Dict, table_name: str):
    """Write to Delta table for dashboarding."""
    spark.createDataFrame([data]).write.mode("append").saveAsTable(table_name)
```

**Option 2: Call Databricks App Endpoint**
```python
def report_to_app(data: Dict, endpoint: str):
    """POST to Databricks App REST endpoint."""
    requests.post(endpoint, json=data)
```

**Option 3: Write to MLflow**
```python
def report_to_mlflow(data: Dict, run_id: str):
    """Log as MLflow metrics and parameters."""
    mlflow.log_metrics({"score": data["score"]}, step=data["iteration"])
```

---

## Component 6: Main Orchestration Job (`job/enhancement_job.py`)

### Purpose
Main Databricks job that orchestrates the entire enhancement loop.

### Job Parameters
```python
JOB_PARAMS = {
    # Target configuration
    "space_id": "01ef274d35a310b5bffd01dadcbaf577",
    "warehouse_id": "abc123def456",

    # Benchmark configuration
    "benchmark_source": "catalog.schema.benchmarks_table",  # or path to file

    # Threshold configuration
    "target_score": 0.90,  # Stop when 90% pass rate
    "max_iterations": 10,  # Safety limit
    "min_score_improvement": 0.05,  # Stop if improvement < 5% for 3 consecutive iterations

    # LLM configuration
    "llm_endpoint": "databricks-meta-llama-3-1-70b-instruct",
    "llm_temperature": 0.1,

    # Reporting configuration
    "report_table": "catalog.schema.enhancement_progress",
    "report_to_app": True,
    "app_endpoint": "https://...",

    # Timeout configuration
    "question_timeout": 120,  # seconds per question
    "iteration_timeout": 3600,  # max 1 hour per iteration
}
```

### Main Loop Logic

```python
def run_enhancement_job(config: Dict) -> Dict:
    """
    Main enhancement loop.

    Returns:
        {
            "success": True/False,
            "final_score": 0.92,
            "iterations": 5,
            "total_duration": 7200,  # seconds
            "final_status": "threshold_reached" | "max_iterations" | "no_improvement"
        }
    """

    # Initialize components
    genie_client = GenieConversationalClient(...)
    space_updater = SpaceUpdater(...)
    scorer = BenchmarkScorer(...)
    enhancer = LLMEnhancer(...)
    reporter = ProgressReporter(...)

    # Load benchmarks
    benchmarks = load_benchmarks(config["benchmark_source"])

    # Track progress
    iteration = 0
    best_score = 0.0
    no_improvement_count = 0

    while iteration < config["max_iterations"]:
        iteration += 1
        logger.info(f"Starting iteration {iteration}")

        # 1. Score current space
        benchmark_results = scorer.score(benchmarks)
        current_score = benchmark_results["score"]

        logger.info(f"Current score: {current_score:.2%}")

        # 2. Check if threshold reached
        if current_score >= config["target_score"]:
            logger.info(f"Threshold reached! Score: {current_score:.2%}")
            reporter.report({
                "iteration": iteration,
                "score": current_score,
                "status": "threshold_reached"
            })
            return {
                "success": True,
                "final_score": current_score,
                "iterations": iteration,
                "final_status": "threshold_reached"
            }

        # 3. Check for improvement
        score_improvement = current_score - best_score
        if score_improvement < config["min_score_improvement"]:
            no_improvement_count += 1
            if no_improvement_count >= 3:
                logger.warning("No significant improvement for 3 iterations. Stopping.")
                return {
                    "success": False,
                    "final_score": current_score,
                    "iterations": iteration,
                    "final_status": "no_improvement"
                }
        else:
            no_improvement_count = 0
            best_score = current_score

        # 4. Export current space config
        current_config = space_updater.export_space(config["space_id"])

        # 5. Enhance space based on failures
        enhancement_result = enhancer.enhance(
            space_id=config["space_id"],
            benchmark_results=benchmark_results,
            current_space_config=current_config
        )

        # 6. Validate enhanced config
        if enhancement_result["validation_status"] != "valid":
            logger.error(f"Enhancement validation failed: {enhancement_result['validation_errors']}")
            # Skip this iteration or try to fix
            continue

        # 7. Apply changes
        space_updater.update_space(
            space_id=config["space_id"],
            serialized_space=json.dumps(enhancement_result["new_space_config"])
        )

        logger.info(f"Applied {len(enhancement_result['changes_made'])} changes")

        # 8. Report progress
        reporter.report({
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "score": current_score,
            "score_delta": score_improvement,
            "changes_made": enhancement_result["changes_made"],
            "failures_by_category": aggregate_failures(benchmark_results)
        })

        # 9. Wait before next iteration (allow Genie to index changes)
        time.sleep(30)  # 30 seconds for Genie to process updates

    # Max iterations reached
    return {
        "success": False,
        "final_score": current_score,
        "iterations": iteration,
        "final_status": "max_iterations_reached"
    }
```

---

## Databricks Job Configuration (`job/job_definition.json`)

```json
{
  "name": "Genie Space Self-Healing Enhancement",
  "tasks": [
    {
      "task_key": "enhancement_loop",
      "description": "Run iterative enhancement loop",
      "libraries": [
        {
          "pypi": {
            "package": "databricks-sdk==0.18.0"
          }
        }
      ],
      "python_wheel_task": {
        "package_name": "genie_enhancer",
        "entry_point": "run_enhancement_job",
        "parameters": [
          "--space-id", "{{space_id}}",
          "--target-score", "{{target_score}}",
          "--max-iterations", "{{max_iterations}}"
        ]
      },
      "new_cluster": {
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 0,
        "spark_conf": {
          "spark.databricks.cluster.profile": "singleNode"
        }
      },
      "timeout_seconds": 14400,
      "max_retries": 0
    }
  ],
  "parameters": [
    {
      "name": "space_id",
      "default": "01ef274d35a310b5bffd01dadcbaf577"
    },
    {
      "name": "target_score",
      "default": "0.90"
    },
    {
      "name": "max_iterations",
      "default": "10"
    }
  ]
}
```

---

## Enhancement Types Supported

### 1. Column Metadata
- Add/update descriptions
- Add synonyms
- Enable get_example_values
- Enable build_value_dictionary

### 2. Table Metadata
- Add/update descriptions
- Clarify scope and usage

### 3. Join Specifications
- Add missing joins
- Fix relationship types
- Add join comments

### 4. Example Queries
- Add parameterized examples for patterns
- Add usage guidance
- Add CTEs for complex logic

### 5. Text Instructions
- Add business rules
- Add calculation conventions
- Add scope clarifications

### 6. Sample Queries
- Update UI sample questions based on common failures

### 7. Metric Views (Future)
- Create metric views for complex aggregations
- Currently noted but not implemented in first iteration

---

## Key Design Decisions

### 1. LLM for Enhancement (Not Fixed Rules)
**Rationale:** Failures are diverse and context-dependent. LLM can reason about causes and generate appropriate fixes better than fixed rules.

### 2. Databricks LLM for Both Judge and Enhancer
**Rationale:** Keep everything in Databricks ecosystem, use managed endpoints, no external API costs.

### 3. Result-Based Comparison (Not SQL Comparison)
**Rationale:** Same answer can have different SQL. Result comparison is more reliable.

### 4. Incremental Updates (Not Full Rewrites)
**Rationale:** Preserve manual configurations, only fix what's broken.

### 5. Validation Before Apply
**Rationale:** Never apply invalid configs. Validate against schema and best practices.

---

## Testing Strategy

### Unit Tests
- `test_benchmark_scorer.py`: Test scoring logic with mock Genie responses
- `test_llm_enhancer.py`: Test enhancement generation with mock LLM
- `test_genie_client.py`: Test API interactions with mock responses
- `test_space_updater.py`: Test space updates with mock API

### Integration Tests
- `test_integration.py`: Test full loop with test Genie Space
- Use small benchmark set (5-10 questions)
- Verify convergence within 3 iterations

### Development Notebooks
- `01_test_scorer.py`: Interactive testing of scorer
- `02_test_enhancer.py`: Interactive testing of enhancer
- `03_run_iteration.py`: Manual single iteration for debugging

---

## Success Metrics

### Primary Metric
- **Benchmark Pass Rate**: % of questions answered correctly

### Secondary Metrics
- **Iterations to Threshold**: How many iterations to reach target
- **Convergence Rate**: Score improvement per iteration
- **Change Efficiency**: Score improvement per change made
- **Time per Iteration**: Total duration including Genie calls

### Quality Metrics
- **False Positives**: Questions marked as passed but shouldn't be
- **False Negatives**: Questions marked as failed but shouldn't be
- **Degradation**: Score going down after changes

---

## Risks & Mitigations

### Risk 1: LLM Makes Bad Changes
**Mitigation:**
- Validate all changes before applying
- Track score after each change
- Rollback if score degrades

### Risk 2: No Convergence
**Mitigation:**
- Set max_iterations limit
- Detect no-improvement cycles
- Manual review after 3 failed attempts

### Risk 3: Genie API Rate Limits
**Mitigation:**
- Add delays between questions
- Batch questions if API supports
- Implement exponential backoff

### Risk 4: Changes Break Existing Queries
**Mitigation:**
- Only add, never remove (unless clearly wrong)
- Test with full benchmark set after each change
- Keep audit log of all changes

---

## Future Enhancements

### Phase 2: Metric View Creation
- Automatically create metric views for complex aggregations
- Detect patterns that need pre-aggregation

### Phase 3: Multi-Space Learning
- Learn from improvements across multiple spaces
- Build library of common fixes

### Phase 4: Continuous Monitoring
- Run scoring periodically
- Alert if score degrades
- Auto-enhance on degradation

### Phase 5: User Feedback Integration
- Incorporate user thumbs up/down
- Use real user queries as benchmarks

---

## Open Questions for Clarification

### 1. Benchmark Source
- **Question:** Where are the Q&A benchmark sets stored?
- **Options:**
  - Delta table with columns: `question`, `expected_sql`, `expected_result`
  - JSON/CSV files in DBFS
  - Embedded in the Genie Space as benchmarks
- **Assumption:** Will use Genie Space's built-in benchmarks field initially

### 2. Metric View Strategy
- **Question:** When should we create metric views vs just adding example queries?
- **Assumption:** Start with example queries only, add metric view creation in Phase 2

### 3. Reporting Destination
- **Question:** What Databricks app should receive reports?
- **Options:**
  - Custom Databricks App with REST endpoint
  - Delta table that powers a dashboard
  - MLflow experiment tracking
- **Assumption:** Will use Delta table initially

### 4. Stop Conditions
- **Question:** Besides threshold, what other conditions should stop the job?
- **Assumptions:**
  - Max iterations reached
  - No improvement for 3 consecutive iterations
  - Score degrades for 2 consecutive iterations

### 5. Starting Genie Space Quality
- **Question:** What's the expected baseline quality?
- **Assumption:** "Decent" means ~50-70% baseline pass rate

---

## Implementation Timeline (Estimated)

### Week 1: Core Infrastructure
- `genie_client.py`: Conversational API wrapper
- `space_updater.py`: Space API wrapper
- `benchmark_scorer.py`: Basic scoring logic

### Week 2: Enhancement Logic
- `llm_enhancer.py`: LLM-based enhancement
- Enhancement prompt engineering
- Validation logic

### Week 3: Orchestration & Reporting
- `enhancement_job.py`: Main loop
- `reporter.py`: Progress reporting
- Job configuration

### Week 4: Testing & Refinement
- Unit tests
- Integration tests
- End-to-end testing with real Genie Space
- Bug fixes and optimization

---

## Dependencies

### Python Libraries
```
databricks-sdk>=0.18.0
requests>=2.31.0
mlflow>=2.9.0
pyspark>=3.5.0
```

### Databricks Requirements
- Genie Space with Can Edit permissions
- SQL Warehouse with Can Use permissions
- Delta table access for reporting
- Databricks LLM endpoint access (Foundation Models API)

---

## Summary

This system implements a self-healing loop that:
1. ✅ Scores Genie Space with benchmarks using Conversational API
2. ✅ Identifies failure patterns
3. ✅ Uses LLM to generate targeted enhancements
4. ✅ Updates Genie Space configuration via API
5. ✅ Reports progress to Databricks Apps
6. ✅ Iterates until threshold or convergence

**Key Innovation #1: FAT PROMPT APPROACH ⭐**
- Embed complete Genie best practices directly in LLM prompts
- LLM has full domain knowledge (metadata requirements, join formats, SQL syntax, etc.)
- Prompts are first-class assets stored in `prompts/` directory
- Easy to iterate and improve without code changes
- Ensures fixes align with Databricks best practices

**Key Innovation #2: LLM-Powered Analysis**
- LLM analyzes failures with domain expertise
- Generates targeted fixes (not generic rules)
- Handles diverse failure patterns adaptively
- Self-documenting through prompt content

**Architecture Highlights:**
- `prompts/` - Domain knowledge and prompt templates (critical assets!)
- `pipeline/` - Core enhancement logic using prompts
- `job/` - Databricks job orchestration
- Clean separation: prompts (knowledge) vs code (logic)