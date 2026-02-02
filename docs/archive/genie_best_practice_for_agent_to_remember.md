# Genie Space Best Practices for Agent

> **Quick Reference**: What the agent must remember when creating Genie Spaces

---

## Core Principle

**METADATA QUALITY = GENIE QUALITY**

Genie understands your data through metadata. Poor metadata → poor results.

### Table Quantity Guidelines

| Count | Assessment | Action |
|-------|------------|--------|
| < 8 | Too few | Extraction too conservative - expand scope |
| 8-10 | Minimum viable | Consider adding supporting tables |
| **10-15** | **Optimal** | Good balance of coverage and focus |
| 15-20 | Acceptable | Monitor for complexity |
| 20-25 | Maximum | Consider splitting into multiple spaces |
| > 25 | Too many | API limit - must reduce |

**Don't be too conservative!** Include:
- Primary tables for the purpose
- Supporting/lookup tables for joins
- Reference tables for categorical values

---

## 1. METADATA (Most Critical!)

### Table Descriptions

Every table MUST have a description that includes:
- What the table represents
- Scope of data (what's included AND excluded)
- Conditions for when Genie should use this table

```
GOOD: "Contains all completed customer orders since 2020. Each row is one
       order transaction. Does NOT include pending orders (use orders_pending).
       Use for revenue analysis and purchase history."

BAD:  "Orders table"
```

### Column Descriptions

Every important column MUST have:
- What the field represents
- When to use this field
- Business rules that apply

```
GOOD: "Total order value in USD. Use for revenue calculations.
       Does NOT include tax or shipping."

BAD:  "Order amount"
```

### Synonyms (CRITICAL for Natural Language!)

Add terms users actually say to refer to fields:

```json
{
  "column_name": "order_amount",
  "synonyms": ["revenue", "sales", "total", "amount", "order value"]
}
```

Without synonyms, Genie can't match natural language to fields.

### Column Settings

| Setting | When to Enable |
|---------|----------------|
| `exclude` | Set `true` to hide column from Genie (default: `false`) |
| `get_example_values` | Date columns, key categorical fields |
| `build_value_dictionary` | Categorical fields with finite values (status, region, type) |

---

## 2. JOINS

### Philosophy

```
1. Pre-join data where sensible (best option - removes ambiguity)
2. For tables that CAN'T be pre-joined → use join_specs
3. Genie respects PK/FK from Unity Catalog
4. join_specs reinforces and adds to these relationships
```

### Join Format (MUST include relationship type marker!)

**MANY_TO_ONE** - Multiple left rows → one right row:
```json
{
  "sql": [
    "t.customer_id = c.customer_id ",
    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
  ],
  "comment": ["MANY-TO-ONE: Multiple orders belong to one customer"]
}
```

**ONE_TO_MANY** - One left row → multiple right rows:
```json
{
  "sql": [
    "c.customer_id = t.customer_id ",
    "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_MANY--"
  ],
  "comment": ["ONE-TO-MANY: One customer has multiple orders"]
}
```

**MANY_TO_MANY** - Self-joins and complex relationships:
```json
{
  "sql": [
    "t1.customer_id = t2.customer_id ",
    "AND t1.timestamp < t2.timestamp ",
    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--"
  ],
  "comment": ["MANY-TO-MANY: Link transactions by same customer"]
}
```

### Format Rules
- Use `=` not `==`
- **MUST include**: `--rt=FROM_RELATIONSHIP_TYPE_*--` marker
- Valid types: `MANY_TO_ONE`, `ONE_TO_MANY`, `MANY_TO_MANY`, `ONE_TO_ONE`
- Use `comment` field, NOT `instructions`
- **SQL lines should end with space** for proper formatting

---

## 3. EXAMPLE QUESTION SQLs (Teaching)

### Purpose
Teach Genie query patterns and structure - NOT raw Q&A storage.

### What to Include
- Parameterized templates for common patterns
- CTEs (Common Table Expressions)
- Standard calculations and complex filtering
- Output formatting style

### Example: Parameterized Template
```json
{
  "question": ["Top N items by metric between two dates"],
  "sql": [
    "WITH aggregated AS (",
    "  SELECT :group_column, SUM(:metric) as total",
    "  FROM :table",
    "  WHERE :date_column BETWEEN :start_date AND :end_date",
    "  GROUP BY :group_column",
    ")",
    "SELECT * FROM aggregated ORDER BY total DESC LIMIT :n"
  ],
  "parameters": [
    {"name": "start_date", "type_hint": "DATE"},
    {"name": "end_date", "type_hint": "DATE"},
    {"name": "n", "type_hint": "INTEGER"}
  ],
  "usage_guidance": ["Use for any top-N analysis with date filtering"]
}
```

### Workflow
1. Extract all Q&A pairs from document
2. Group similar questions by PATTERN
3. Create ONE parameterized template per pattern
4. Aim for quality templates, not quantity

---

## 4. SQL SNIPPETS (Building Blocks)

### Purpose
Named, reusable SQL pieces that map business terms to SQL.

### CRITICAL: Include Full Table Name!
SQL snippets MUST include full table name (catalog.schema.table.column) for context.

### Three Types

**Filters** (WHERE conditions):
```json
{
  "sql": ["catalog.schema.customers.status = 'approved' AND catalog.schema.customers.deleted_at IS NULL"],
  "display_name": "Active customers",
  "synonyms": ["active", "current", "live"]
}
```

**Expressions/Dimensions** (Row calculations):
```json
{
  "alias": "fiscal_year",
  "sql": ["CASE WHEN MONTH(catalog.schema.orders.order_date) >= 7 THEN YEAR(catalog.schema.orders.order_date) + 1 ELSE YEAR(catalog.schema.orders.order_date) END"],
  "display_name": "Fiscal year"
}
```

**Measures** (Aggregations):
```json
{
  "alias": "total_revenue",
  "sql": ["ROUND(SUM(catalog.schema.orders.amount), 2)"],
  "display_name": "Total revenue",
  "synonyms": ["revenue", "sales", "gross revenue"]
}
```

### Key Points
- **SYNONYMS are critical** - they enable natural language matching
- **Include full table name** (catalog.schema.table.column) in SQL

### API Limitation
The `instructions` field inside sql_snippets is NOT supported by the API.
Put usage rules in `text_instructions` instead.

---

## 5. SQL FUNCTIONS

### Purpose
UDFs for calculations that must be exact and consistent.

### When to Use
- Tax calculations
- Currency conversions
- Complex business formulas that shouldn't vary

```json
{
  "identifier": "catalog.schema.calculate_gst"
}
```

---

## 6. TEXT INSTRUCTIONS

### Purpose
High-level context and rules reinforcement.

### What to Include
- Overview of Genie Space purpose and scope
- Entity relationships and lifecycles
- Rules that apply across multiple components
- Usage rules for sql_snippets (workaround for API limitation)

### When to Add
Add AFTER other components are set up. Use to fill contextual gaps.

---

## 7. BENCHMARKS (Evaluation)

### Purpose
Store ALL Q&A pairs for evaluation. Genie does NOT learn from these.

### CRITICAL: Be AGGRESSIVE with Benchmark Extraction!

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  SIMPLE RULE: Question + SQL = BENCHMARK                                     ║
║                                                                              ║
║  If you see a question and corresponding SQL query → IT IS A BENCHMARK!     ║
║  Don't overthink it. Don't be conservative. Extract ALL pairs.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Benchmark Quantity Guidelines

| Count | Assessment | Action |
|-------|------------|--------|
| < 15 | Too few | Extraction too conservative - re-extract! |
| 15-20 | Minimum | Acceptable but look for more |
| **20-50** | **Optimal** | Good coverage for evaluation |
| > 50 | Great | Comprehensive evaluation data |

### What to Include
- ALL Q&A pairs from query documents
- These are success criteria for future evaluation
- Every question with a SQL answer = benchmark

### Format (NOTE: answer is an ARRAY!)
```json
{
  "id": "...",
  "question": ["What is the total revenue?"],
  "answer": [{
    "format": "SQL",
    "content": [
      "SELECT ROUND(SUM(totalPrice), 2) as total_revenue",
      "FROM samples.bakehouse.sales_transactions"
    ]
  }]
}
```

### Workflow
```
Document Q&A pairs → ALL go to benchmarks
                  → Patterns go to example_question_sqls
```

---

## Common Issues → What Fixes Them

| Issue | Fix With |
|-------|----------|
| Query uses wrong fields | Column descriptions + Synonyms |
| Incorrect calculation | Example queries + SQL functions |
| "No data available" (but exists) | Table descriptions + Synonyms |
| Answers about out-of-scope data | Table descriptions (scope clarity) |
| Inconsistent answers | Example queries + SQL functions |
| Wrong output format | Example queries + Field descriptions |

---

## Quick Checklist for Creating Genie Space

### Metadata
- [ ] Every table has detailed description with scope
- [ ] Important columns have descriptions with business rules
- [ ] Synonyms added for natural language matching
- [ ] `get_example_values` enabled for dates and key fields
- [ ] `build_value_dictionary` enabled for categorical fields

### Joins
- [ ] All table relationships defined
- [ ] SQL includes `--rt=FROM_RELATIONSHIP_TYPE_*--` marker
- [ ] Relationship types also described in comments
- [ ] Complex joins use SQL expression format

### Example Queries
- [ ] Common patterns converted to parameterized templates
- [ ] All items have `id` field
- [ ] CTEs and complex logic documented
- [ ] Output formatting style shown

### SQL Snippets
- [ ] All items (filters, expressions, measures) have `id` field
- [ ] Business terms defined as filters/expressions/measures
- [ ] Synonyms added for each snippet

### Benchmarks
- [ ] ALL Q&A pairs included for evaluation
- [ ] All items have `id` field
- [ ] `answer` is an ARRAY of objects

---

## API Format Reminders

### UUIDs
- 32 lowercase hex characters
- No dashes
- Pattern: `^[0-9a-f]{32}$`

### Text Fields
- Always arrays: `["text"]` not `"text"`

### Sorting (Required!)
- `tables`: Sort by `identifier`
- `column_configs`: Sort by `column_name`
- All id-based arrays: Sort by `id`

### Join SQL
- Use `=` not `==`
- **MUST include**: `--rt=FROM_RELATIONSHIP_TYPE_*--` marker
- Valid types: `MANY_TO_ONE`, `ONE_TO_MANY`, `MANY_TO_MANY`, `ONE_TO_ONE`
- Use `comment` NOT `instructions`
- **SQL lines should end with space**

### SQL Snippets
- All items need `id` field
- **Include full table name** (catalog.schema.table.column)
- NO `instructions` or `table_identifier` fields

### Benchmarks
- `answer` is an ARRAY: `[{"format": "SQL", "content": [...]}]`
- **SQL lines should end with space**

### Column Configs
- Include `exclude` field (default: `false`)
- **NO `id` field** - use `column_name` for identification

### Spark SQL Syntax Rules (CRITICAL!)

**Date Literals - MUST quote the date value:**
```sql
-- ✅ CORRECT
WHERE event_date >= DATE '2025-08-18'
WHERE event_date >= '2025-08-18'
WHERE event_date BETWEEN '2025-08-18' AND '2025-08-25'

-- ❌ WRONG - causes PARSE_SYNTAX_ERROR
WHERE event_date >= DATE 2025-08-18    -- Parsed as: DATE (2025 - 8 - 18) = DATE 1999
```

**String Literals - Always use single quotes:**
```sql
-- ✅ CORRECT
WHERE status = 'active'
WHERE game_code = 'inzoi'

-- ❌ WRONG
WHERE status = active              -- Treated as column reference
WHERE game_code = "inzoi"          -- Double quotes are for identifiers
```

**Boolean Comparisons:**
```sql
-- ✅ CORRECT
WHERE voted_up = false
WHERE is_active = true

-- ❌ WRONG
WHERE voted_up = 'false'           -- String, not boolean
```

**UNION Syntax:**
```sql
-- ✅ CORRECT - same number of columns, compatible types
SELECT col1, col2 FROM table1
UNION ALL
SELECT col1, col2 FROM table2

-- Note: UNION ALL keeps duplicates, UNION removes them
```

### Which Elements Need `id` Field

```
NEED `id`:
✓ sample_questions[]
✓ text_instructions[]
✓ example_question_sqls[]
✓ join_specs[]
✓ sql_functions[]
✓ sql_snippets.filters[]
✓ sql_snippets.expressions[]
✓ sql_snippets.measures[]
✓ benchmarks.questions[]

DO NOT HAVE `id`:
✗ tables[] - uses `identifier`
✗ column_configs[] - uses `column_name`
✗ parameters[] - uses `name`
✗ answer[] - no identifier needed
```

**Common Errors**:
- `"Cannot find field: id in ColumnConfig"` → Remove `id` from column_configs!
- `"Cannot find field: instructions in TextInstruction"` → Use `content`, not `instructions`!
- `"Invalid JSON in field 'serialized_space'"` → Check structure (see below)

---

## "Invalid JSON" Quick Troubleshooting

| Error Cause | Wrong | Correct |
|-------------|-------|---------|
| text_instructions | `"instructions": [...]` | `"content": [...]` |
| benchmarks location | Inside `instructions` | At TOP LEVEL |
| join_specs | `"instructions": [...]` | `"comment": [...]` |
| sql_snippets | Has `instructions` or `table_identifier` | Remove these fields |
| column_configs | Has `id` field | Remove `id`, use `column_name` |
| benchmarks.answer | `{...}` (object) | `[{...}]` (ARRAY) |
| ID format | `"abc-123"` or `"ABC123"` | 32 lowercase hex, no dashes |
