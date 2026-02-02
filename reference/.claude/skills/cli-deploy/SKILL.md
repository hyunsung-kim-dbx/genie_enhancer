---
name: cli-deploy
description: Automated Genie space deployment from real_requirements/inputs with automatic catalog replacement to sandbox.agent_poc. Use when the user asks to deploy genie, create a genie space from real requirements, or wants to automate the full deployment workflow with the real requirements.
---

# CLI Deploy

Automate the complete Genie space deployment workflow including document parsing, generation, validation with automatic catalog replacement, and deployment.

## Input Directory Structure

The skill expects requirements organized in subdirectories:

```
real_requirements/
├── inputs/              # Requirements documents (REQUIRED)
│   ├── *.pdf           # PDF requirements documents
│   └── *.md            # Markdown requirements documents
└── benchmarks/          # Benchmark questions (OPTIONAL)
    └── benchmarks.json  # Curated benchmark questions with expected SQL
```

**Benefits of this structure:**
- Clear separation between input documents and test benchmarks
- Easier to manage multiple types of requirements files
- Optional benchmarks allow for comprehensive testing when available
- Follows the same pattern as `sample/` directory for consistency

## Deployment Workflow

Follow this workflow when the user requests deployment:

### 1. Parse Requirements Documents

**ALWAYS start by parsing documents from the `real_requirements/inputs/` directory** using the virtual environment:

```bash
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md
```

This will:
- **Check parse cache first** - if files haven't changed since last parse, uses cached results (fast!)
- Parse all PDF and markdown files in `real_requirements/inputs/` (only if needed)
- Extract FAQ questions, table specifications, and business context
- Output structured requirements to `data/parsed.md`
- Save cache metadata to `.parse_cache.json` for future runs

**Cache behavior:**
- By default, caching is enabled
- Re-parsing only happens if:
  - Input files changed (mtime or size)
  - Output file was modified or deleted
  - Parsing config changed (model, domain)
- To force re-parsing: add `--force` flag
- To disable caching: add `--no-cache` flag

**Check cache status:**
```bash
# View cache metadata (if exists)
cat .parse_cache.json | jq '.'
```

### 2. Create Genie Configuration Script

Create a Python script that automates the full pipeline with automatic catalog replacement. Save this as `scripts/auto_deploy.py`:

```python
#!/usr/bin/env python3
"""Automated Genie deployment with catalog replacement."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from genie.pipeline import generate_config, validate_config, deploy_space

# Load environment variables
load_dotenv()


def auto_deploy(
    requirements_path: str = "data/parsed.md",
    output_path: str = "output/genie_space_config.json",
    result_output: str = "output/genie_space_result.json",
    auto_replace_catalog: str = "sandbox",
    auto_replace_schema: str = "agent_poc"
):
    """Run full deployment with automatic catalog replacement."""

    print("=" * 80)
    print("🧞 Automated Genie Deployment")
    print("=" * 80)
    print()

    # Step 1: Generate configuration
    print("📝 Step 1/3: Generating configuration...")
    print("-" * 80)

    config_data = generate_config(
        requirements_path=requirements_path,
        output_path=output_path,
        verbose=True
    )

    print()
    print("✓ Configuration generated!")
    print()

    # Step 2: Validate with automatic replacement
    print("✓ Step 2/3: Validating with automatic catalog replacement...")
    print("-" * 80)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\nValidation attempt {attempt}/{max_attempts}")

        report = validate_config(
            config_path=output_path,
            verbose=True
        )

        if report.has_errors():
            # Check for table_not_found errors
            table_errors = [
                issue for issue in report.issues
                if issue.severity == "error" and issue.type == "table_not_found"
            ]

            if table_errors and attempt < max_attempts:
                print()
                print(f"⚠️  Found {len(table_errors)} table validation errors")
                print(f"🔄 Auto-replacing catalog.schema to {auto_replace_catalog}.{auto_replace_schema}")

                # Extract unique catalog.schema combinations
                failed_schemas = {}
                for issue in table_errors:
                    if issue.table:
                        parts = issue.table.split('.')
                        if len(parts) == 3:
                            catalog, schema, table = parts
                            key = f"{catalog}.{schema}"
                            if key not in failed_schemas:
                                failed_schemas[key] = []
                            failed_schemas[key].append(table)

                # Replace each failed catalog.schema
                import json
                from genie import update_config_catalog_schema

                for schema_key in failed_schemas.keys():
                    old_catalog, old_schema = schema_key.split('.')
                    print(f"  Replacing {old_catalog}.{old_schema} → {auto_replace_catalog}.{auto_replace_schema}")

                    counts = update_config_catalog_schema(
                        output_path,
                        old_catalog,
                        old_schema,
                        auto_replace_catalog,
                        auto_replace_schema
                    )

                    print(f"    Updated: {counts['tables']} tables, {counts['sql_expressions']} SQL expressions")
                    print(f"             {counts['example_queries']} queries, {counts['benchmark_questions']} benchmarks")

                print()
                continue
            else:
                print()
                print("❌ Validation failed!")
                print()
                print(report.summary())
                return 1

        # Validation passed
        print()
        print("✓ Validation passed!")
        break

    # Step 3: Deploy
    print()
    print("🚀 Step 3/3: Deploying Genie space...")
    print("-" * 80)

    result = deploy_space(
        config_path=output_path,
        verbose=True
    )

    # Save result
    result_path = Path(result_output)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 80)
    print("✓ DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()
    print(f"Space ID:  {result['space_id']}")
    print(f"Space URL: {result['space_url']}")
    print()
    print(f"Configuration: {output_path}")
    print(f"Result:        {result_output}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(auto_deploy())
```

### 3. (Optional) Add Benchmark Questions

**Highly recommended** for comprehensive testing. Create `real_requirements/benchmarks/benchmarks.json`:

```json
[
  {
    "question": "지난 주 가장 많이 팔린 제품은 무엇인가요?",
    "category": "KPI & Sales Analysis",
    "difficulty": "easy",
    "tags": ["sales", "product", "ranking"]
  },
  {
    "question": "어떤 카테고리가 가장 높은 매출을 기록했나요?",
    "category": "KPI & Sales Analysis",
    "difficulty": "easy",
    "tags": ["category", "revenue", "ranking"]
  },
  {
    "question": "브랜드별로 고객 반응을 비교해주세요",
    "category": "Cross-Analysis",
    "difficulty": "medium",
    "tags": ["brand", "comparison", "customer"]
  },
  {
    "question": "그래서 우리 고객들은 우리 제품에 대해서 뭐라고 말하고 있어?",
    "category": "Exploratory Questions",
    "difficulty": "hard",
    "tags": ["open-ended", "customer", "sentiment"]
  }
]
```

**Benchmark Benefits:**
- 🎯 **Comprehensive Testing**: Validates that Genie can answer specific business questions
- ✅ **Quality Assurance**: Ensures generated configuration meets actual requirements
- 📊 **Coverage Metrics**: Tracks which questions the space can handle by category and difficulty
- 🔍 **Debugging Aid**: Identifies gaps in table definitions or instructions
- 🏷️ **Organized Testing**: Categories and tags help organize test coverage

**Benchmark Fields:**
- `question`: Natural language question (Korean or English)
- `category`: Question category (e.g., "KPI & Sales Analysis", "Cross-Analysis", "Exploratory Questions")
- `difficulty`: Complexity level ("easy", "medium", "hard")
- `tags`: Array of keywords for filtering and searching

See `sample/benchmarks/benchmarks.json` for a complete example with 27 questions.

### 4. Run Automated Deployment

Execute the automated deployment script:

```bash
.venv/bin/python scripts/auto_deploy.py
```

This will:
1. Generate configuration from `data/parsed.md`
2. **Automatically load benchmarks** from `real_requirements/benchmarks/benchmarks.json` (if exists)
3. Validate tables against Unity Catalog
4. Automatically replace any failed catalog.schema with `sandbox.agent_poc`
5. Re-validate up to 3 times if needed
6. Deploy the Genie space

### 5. Verify Deployment

After deployment completes, verify the results:

```bash
# Check the deployment result
cat output/genie_space_result.json

# Check the final configuration
cat output/genie_space_config.json
```

## Configuration

The automated deployment uses these defaults:

- **Requirements input**: `data/parsed.md` (from parse step)
- **Config output**: `output/genie_space_config.json`
- **Result output**: `output/genie_space_result.json`
- **Auto-replace catalog**: `sandbox`
- **Auto-replace schema**: `agent_poc`

## Environment Variables

Required in `.env`:
- `DATABRICKS_HOST`: Databricks workspace URL
- `DATABRICKS_TOKEN`: Personal access token

Optional:
- `LLM_MODEL`: Text model for generation (default: databricks-gpt-5-2)
- `VISION_MODEL`: Vision model for PDF parsing (default: databricks-claude-sonnet-4)

## Error Handling

### Parse Failures

If parsing fails:
1. Check that `real_requirements/inputs/` directory exists and contains PDF/markdown files
2. Verify environment variables are set correctly
3. Check for corrupt or unsupported file formats
4. Ensure input files are in `real_requirements/inputs/`, not directly in `real_requirements/`

### Parse Cache Not Working

If you notice parsing is re-running when it shouldn't:
1. Check if `.parse_cache.json` exists in project root
2. Verify output file `data/parsed.md` exists and hasn't been manually modified
3. Check if input files in `real_requirements/inputs/` were modified (cache tracks mtime and size)
4. If cache seems stuck, force re-parse: `.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md --force`
5. If you want to see cache validation details, the parse command prints cache status when `verbose=True` (default)

### Validation Failures

If validation still fails after 3 attempts:
1. Check that `sandbox.agent_poc` schema exists in Unity Catalog
2. Verify table names are correct in the requirements
3. Manually inspect `output/genie_space_config.json` for issues

### Deployment Failures

If deployment fails:
1. Verify Databricks credentials are valid
2. Check that you have permissions to create Genie spaces
3. Ensure parent workspace path is accessible

### Deployment API Errors (INTERNAL_ERROR)

If deployment fails with `500 Internal Server Error` and error code `INTERNAL_ERROR`:

**Root Cause**: The Databricks Genie API rejects configurations with special characters in metadata fields.

**Common Issues:**
1. **Special characters in space_name, description, or purpose**:
   - Backticks (`) in field values
   - Parentheses with complex content
   - Mixed formatting characters

**Solution:**
```bash
# Clean the metadata fields in the generated config
cat output/genie_space_config.json | jq '
  .space_name = "Simple Space Name Without Special Characters" |
  .description = "Clean description without backticks or complex parentheses" |
  .purpose = "Clear purpose statement"
' > output/genie_space_config_clean.json

# Extract just the genie_space_config if it's nested
cat output/genie_space_config_clean.json | jq '.genie_space_config // .' > output/genie_space_config.json

# Try deployment again
.venv/bin/python genie.py deploy --config output/genie_space_config.json
```

**Debugging Steps:**
1. Test with minimal configuration first:
   ```bash
   # Create minimal test config with 1-2 tables
   cat output/genie_space_config.json | jq '
     .space_name = "Test Space" |
     .description = "Test deployment" |
     .purpose = "Testing" |
     .tables = .tables[0:2] |
     .join_specifications = [] |
     .sql_snippets = {filters: [], expressions: [], measures: []} |
     .example_sql_queries = [] |
     .instructions = [{content: "Test space.", priority: 1}]
   ' > /tmp/minimal_config.json

   .venv/bin/python genie.py deploy --config /tmp/minimal_config.json
   ```

2. If minimal config works, incrementally add components:
   - First: Add all tables
   - Then: Add join specifications
   - Then: Add SQL snippets
   - Finally: Add example queries

3. Check the serialized space for issues:
   ```bash
   # After a failed deployment, check the debug output
   cat output/debug_serialized_space.json | jq '.serialized_space'

   # If serialized_space is null, the config structure is wrong
   # If it's populated, the issue is with the content
   ```

**Common Fixes:**
- Remove backticks from descriptions (use plain text or quotes)
- Simplify space names (avoid special characters and parentheses)
- Keep descriptions concise and avoid complex formatting
- Ensure markdown in instructions is valid and not overly complex

**Table Name Mismatches:**
If validation passes but deployment fails, check for table name issues:
```bash
# Identify tables that don't exist in target schema
# Common issues:
# - Table names extracted incorrectly (e.g., "log_discord" as table instead of schema)
# - Table names that changed (e.g., "steam_app_id" → "steam_apps")

# Fix table names:
sed -i '' 's/old_table_name/new_table_name/g' output/genie_space_config.json

# Remove non-existent tables:
cat output/genie_space_config.json | jq '
  .tables = [.tables[] | select(.table_name != "non_existent_table")]
' > output/genie_space_config_fixed.json
```

### Benchmark Issues

If benchmarks are not loading:
1. Check that `real_requirements/benchmarks/benchmarks.json` exists
2. Verify JSON format is valid (use `jq . benchmarks.json` to validate)
3. Ensure each benchmark has required fields: `question`, `category`, `difficulty`, `tags`
4. Benchmarks are optional - generation works without them, but testing is less comprehensive

## Manual Override

If you need to customize the replacement catalog/schema, edit `scripts/auto_deploy.py`:

```python
# Change these parameters in the auto_deploy() call
sys.exit(auto_deploy(
    auto_replace_catalog="your_catalog",
    auto_replace_schema="your_schema"
))
```

## Project-Specific Details

### Virtual Environment

Always use `.venv/bin/python` instead of `python` or `python3` as enforced by project standards.

### Output Directory Structure

```
output/
├── genie_space_config.json    # Generated configuration
└── genie_space_result.json    # Deployment result with space ID and URL
```

### Input Directory Structure

The project expects requirements in the following structure:

```
real_requirements/
├── inputs/              # Requirements documents (REQUIRED)
│   ├── *.pdf           # PDF requirements documents
│   └── *.md            # Markdown requirements documents
└── benchmarks/          # Benchmark questions (OPTIONAL)
    └── benchmarks.json  # Curated benchmark questions with expected SQL
```

**Requirements format** in `real_requirements/inputs/`:
- **FAQ sections**: Business questions to extract as examples
- **Table specifications**: Table names and sample queries
- **Business context**: Domain-specific requirements

**Benchmarks format** in `real_requirements/benchmarks/benchmarks.json`:
- Array of benchmark questions with metadata
- Used for comprehensive testing and validation
- Automatically loaded during generation if file exists
- Each benchmark includes:
  - `question`: Natural language question (Korean or English)
  - `category`: Question category for organization
  - `difficulty`: Complexity level (easy/medium/hard)
  - `tags`: Keywords for filtering and analysis
- See `sample/benchmarks/benchmarks.json` for example with 27 questions

**How benchmarks are used:**
1. **During Generation**: Loaded and included in the Genie space configuration
2. **During Validation**: Used to test if the space can answer business questions
3. **Quality Review**: Provides coverage metrics by category and difficulty
4. **Deployment**: Included in the deployed space for end-user testing
5. **Feedback Loop**: Helps identify which question types need improvement

## Quick Reference

### Full Workflow (One Command)

```bash
# Parse, generate, validate with auto-replacement, and deploy
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md && \
.venv/bin/python scripts/auto_deploy.py
```

### Step-by-Step Workflow

```bash
# Step 1: Parse documents
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md

# Step 2: (Optional) Add benchmarks
# Create real_requirements/benchmarks/benchmarks.json with your test questions

# Step 3: Generate and deploy with auto-replacement
.venv/bin/python scripts/auto_deploy.py
```

### Full Workflow with Benchmarks

```bash
# Complete workflow with benchmarks
# 1. Prepare directory structure
mkdir -p real_requirements/inputs real_requirements/benchmarks

# 2. Copy demo benchmarks as starting point
cp sample/benchmarks/benchmarks.json real_requirements/benchmarks/

# 3. Edit benchmarks to match your domain
# (edit real_requirements/benchmarks/benchmarks.json)

# 4. Parse requirements
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md

# 5. Deploy (automatically loads benchmarks)
.venv/bin/python scripts/auto_deploy.py

# 6. Verify benchmarks were loaded
cat output/genie_space_config.json | jq '.benchmark_questions | length'
```

### Check Deployment Status

```bash
# View space details
cat output/genie_space_result.json | jq '.space_url'

# View configuration
cat output/genie_space_config.json | jq '.space_name'

# Check if benchmarks were loaded
cat output/genie_space_config.json | jq '.benchmark_questions | length'
cat output/genie_space_config.json | jq '.benchmark_questions[] | .question' | head -5
```

### Verify Parse Cache

```bash
# Check cache metadata
cat .parse_cache.json | jq '{timestamp: .timestamp, input_files: (.input_files | length), output: .output_path}'

# Force cache refresh
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md --force

# Test cache (should skip parsing if nothing changed)
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md
```

## Best Practices

1. **Organize inputs properly**: Place requirements in `real_requirements/inputs/`, benchmarks in `real_requirements/benchmarks/`
2. **Always parse first**: Use `parse` command to convert documents to structured format
3. **Let cache work**: Don't use `--force` unless necessary - cache is smart and detects changes automatically
4. **Check parsed output**: Review `data/parsed.md` before generation
5. **Verify catalog exists**: Ensure `sandbox.agent_poc` schema exists in Unity Catalog
6. **Test with demo data**: Test the workflow with demo requirements first (see `sample/` directory)
7. **Save outputs**: Keep `output/` directory for debugging and audit trails
8. **Monitor cache**: Check `.parse_cache.json` to see when documents were last parsed
9. **Use benchmarks**: Add curated benchmarks to `real_requirements/benchmarks/benchmarks.json` for better testing

### Creating Effective Benchmarks

When creating benchmarks, follow these guidelines:

**1. Coverage by Category**
- **KPI & Sales Analysis**: Specific metric questions (easy-medium)
- **Sentiment & Trend Analysis**: Pattern and trend questions (medium-hard)
- **Cross-Analysis**: Comparative questions across dimensions (medium)
- **Exploratory Questions**: Open-ended discovery questions (hard)

**2. Difficulty Levels**
- **Easy**: Single table, simple aggregations, clear metrics
- **Medium**: Multiple tables, joins, time-based comparisons
- **Hard**: Complex analysis, open-ended, requires domain knowledge

**3. Question Diversity**
- Mix of specific and broad questions
- Include time-based queries (last week, recent, trending)
- Add ranking/comparison questions
- Include exploratory/open-ended questions

**4. Real Business Value**
- Questions stakeholders actually ask
- Align with KPIs and business goals
- Cover common use cases first

**Example workflow:**
```bash
# 1. Start with demo benchmarks as template
cp sample/benchmarks/benchmarks.json real_requirements/benchmarks/benchmarks.json

# 2. Edit to match your domain
# - Update questions to your business context
# - Keep categories and structure
# - Aim for 20-30 questions covering different difficulty levels

# 3. Validate JSON format
jq . real_requirements/benchmarks/benchmarks.json

# 4. Deploy and test
.venv/bin/python scripts/auto_deploy.py
```

## References

See the main project documentation for more details:
- `CLAUDE.md`: Project overview and development commands
- `README.md`: User guide and setup instructions
- `ARCHITECTURE.md`: System architecture and design decisions
