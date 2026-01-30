# Agent Skills Proposal: Automated Genie Space Creation

## Executive Summary

Your approach is **excellent and well-aligned** with the Genie Space architecture. The semantic layer is indeed a JSON file (`GenieSpaceExport` schema), and automating the conversion from documentation to properly structured JSON following best practices is a powerful way to:

1. **Scale Genie Space creation** - Automate repetitive configuration work
2. **Ensure consistency** - Apply best practices systematically across all spaces
3. **Enable CI/CD workflows** - Version control and automated updates
4. **Reduce human error** - Eliminate manual JSON construction mistakes

## Architecture Overview

```
Documentation (Markdown/Text/Any Format)
    ↓
[Agent Skill 1: LLM-Based Document Parser]
    ↓
Structured Data (Tables, Columns, Joins, Queries)
    ↓
[Agent Skill 2: JSON Schema Builder & Best Practices Enforcer]
    ↓
GenieSpaceExport JSON (Validated)
    ↓
[Agent Skill 3: Genie Space API Handler]
    ↓
Genie Space Created/Updated
    ↓
[Agent Skill 4: Validation & Best Practices Checker]
    ↓
Validated & Optimized Genie Space
```

## Proposed Agent Skills

### Skill 1: LLM-Based Document Parser & Extractor ⭐ **RECOMMENDED APPROACH**
**Purpose:** Use LLM to flexibly extract structured information from any documentation format

**Why LLM Instead of Fixed Code?**
- ✅ **Flexibility**: Adapts to any document structure without code changes
- ✅ **Robustness**: Handles variations in formatting, language, and structure
- ✅ **Context Understanding**: Understands intent, not just patterns
- ✅ **Multilingual**: Naturally handles Korean, English, or mixed content
- ✅ **Future-Proof**: Works with new document types without updates
- ✅ **Better Extraction**: Can infer relationships and context that regex can't

**Capabilities:**
- **LLM-Powered Extraction**: Uses language model to understand document structure
- Extract from any format:
  - **Tables & Columns**: Identify table identifiers, column names, descriptions
  - **Join Relationships**: Parse join specifications and infer relationship types
  - **SQL Examples**: Extract example queries with natural language questions
  - **Business Rules**: Extract filtering conditions, aggregation patterns
  - **Metadata**: Extract descriptions, synonyms, field usage guidance
  - **Benchmarks**: Identify benchmark questions from documentation

**Input:** 
- Documentation files (markdown, text, HTML, etc.)
- Optional: Unity Catalog metadata for validation
- Optional: Examples of desired output format

**Output:**
- Structured JSON object with:
  - `tables`: Array of table definitions
  - `columns`: Column configurations with metadata
  - `joins`: Join specifications
  - `example_queries`: Question-SQL pairs
  - `benchmarks`: Evaluation questions
  - `instructions`: General guidance extracted from docs

**Implementation Approach:**
- **Prompt Engineering**: Design prompts that guide LLM to extract structured data
- **Few-Shot Learning**: Provide examples of good extractions
- **Structured Output**: Request JSON output matching target schema
- **Validation**: Post-process LLM output to ensure completeness
- **Iterative Refinement**: Allow LLM to refine extraction if validation fails

**Key Features:**
- Handles ANY document format (markdown, text, HTML, PDF text, etc.)
- Extracts Korean/English/mixed content naturally
- Understands context and relationships
- Adapts to document structure variations
- Can handle incomplete or ambiguous documentation
- Infers missing information from context

---

### Skill 2: JSON Schema Builder & Best Practices Enforcer
**Purpose:** Convert parsed document data into valid `GenieSpaceExport` JSON following best practices

**Capabilities:**
- Transform extracted data into `GenieSpaceExport` schema
- Apply best practices automatically:
  - **Metadata Enhancement**: Generate comprehensive table/column descriptions
  - **Synonym Generation**: Extract synonyms from documentation and business terms
  - **Join Specification**: Convert SQL joins to `JoinSpec` format with proper relationship types
  - **Example Query Formatting**: Convert SQL examples to `ExampleQuestionSql` format
  - **Benchmark Creation**: Format questions as `BenchmarkQuestion` objects
  - **Instruction Synthesis**: Create `TextInstruction` from extracted guidance

**Input:**
- Structured data from Skill 1
- Best practices rules (from reference guide)

**Output:**
- Valid `GenieSpaceExport` JSON string
- Validation report

**Best Practices Applied:**
1. **Data Engineering**: Validate that tables are "Gold Layer" ready
2. **Metadata**: Ensure comprehensive descriptions (scope, usage conditions, lifecycle)
3. **Synonyms**: Extract business terms, acronyms, aliases
4. **Joins**: Properly specify relationship types (one-to-many, many-to-many)
5. **SQL Examples**: Format as parameterized queries with usage guidance
6. **Benchmarks**: Include desired output format specifications

**Key Features:**
- Generates UUIDs for all required ID fields
- Splits long strings into arrays for better diff management
- Validates against TypeScript schema
- Applies formatting conventions (newline splitting, etc.)

---

### Skill 3: Genie Space API Handler
**Purpose:** Handle all Genie Space API operations (export, import, update)

**Capabilities:**
- **Export**: Retrieve existing space configuration
- **Import**: Create new Genie Space from JSON
- **Update**: Update existing space with new configuration
- **Authentication**: Handle Databricks token management
- **Error Handling**: Retry logic, error reporting

**Input:**
- `serialized_space`: JSON string
- `warehouse_id`: Target warehouse
- `space_id`: (for update/export)
- `title`, `description`: Space metadata
- `parent_path`: Workspace path

**Output:**
- API response with `space_id`
- Success/failure status
- Error details if failed

**Key Features:**
- Handles authentication (Bearer token)
- Validates warehouse_id exists
- Checks permissions before operations
- Supports workspace-to-workspace migration
- Idempotent operations (safe to retry)

---

### Skill 4: Validation & Best Practices Checker
**Purpose:** Validate JSON against schema and best practices, provide optimization suggestions

**Capabilities:**
- **Schema Validation**: Ensure JSON matches `GenieSpaceExport` schema
- **Best Practices Audit**: Check against best practices guide:
  - Table descriptions completeness
  - Column metadata quality
  - Join specifications correctness
  - SQL example quality
  - Benchmark coverage
- **Optimization Suggestions**: Recommend improvements
- **Pre-import Validation**: Check before API calls

**Input:**
- `GenieSpaceExport` JSON
- Best practices checklist

**Output:**
- Validation report with:
  - Schema validation results
  - Best practices compliance score
  - Missing elements checklist
  - Optimization recommendations
  - Warnings/errors

**Validation Checks:**
1. ✅ All required fields present
2. ✅ UUIDs properly formatted
3. ✅ Table identifiers valid (catalog.schema.table)
4. ✅ Join specifications complete (left, right, sql, relationship type)
5. ✅ SQL examples have corresponding questions
6. ✅ Benchmarks have desired output format
7. ✅ Descriptions follow best practices (scope, conditions, lifecycle)
8. ✅ Synonyms populated for key fields
9. ✅ Example values/value dictionaries enabled where appropriate

---

## Workflow Example

### Scenario: Create Genie Space from Documentation

```python
# Step 1: Parse Document using LLM
parsed_data = llm_document_parser_skill.parse(
    document_path="doc/question-table-mapping-kpi-delivery.md",
    extraction_prompt="extract_tables_columns_joins",  # Predefined prompt template
    output_format="json"  # Request structured JSON output
)

# Step 2: Build JSON with Best Practices
genie_json = json_builder_skill.build(
    parsed_data=parsed_data,
    apply_best_practices=True
)

# Step 3: Validate
validation_report = validator_skill.validate(genie_json)
if not validation_report.is_valid:
    print(validation_report.recommendations)
    # Optionally auto-fix or request user input

# Step 4: Create/Update Space
result = api_handler_skill.create_space(
    serialized_space=genie_json,
    warehouse_id="abc123def456",
    title="KPI Delivery Genie Space",
    description="Automated from documentation"
)

# Step 5: Post-creation validation
final_check = validator_skill.validate_space(space_id=result.space_id)
```

---

## Implementation Considerations

### 1. **LLM-Based Parsing Strategy** ⭐ **KEY DECISION**

**Recommended Approach:**
- Use LLM (via Databricks agent capabilities) for document parsing
- Provide structured prompts with examples
- Request JSON output matching intermediate schema
- Validate and refine iteratively

**Prompt Structure:**
```
You are an expert at extracting structured information from documentation 
for Genie Space creation. Extract the following from the document:

1. Tables: catalog.schema.table identifiers with descriptions
2. Columns: column names, descriptions, synonyms per table
3. Joins: relationships between tables with SQL conditions
4. Example Queries: natural language questions with corresponding SQL
5. Benchmarks: evaluation questions with expected SQL answers

Output as JSON matching this schema: {...}

Document:
{document_content}
```

**Benefits:**
- No code changes needed for new document formats
- Handles edge cases and variations automatically
- Better at understanding context and intent
- Can be improved by refining prompts, not code

**Alternative (Hybrid):**
- Use LLM for initial extraction
- Use fixed code for validation and normalization
- Best of both worlds: flexibility + reliability

### 2. **Best Practices Automation**
Some best practices can be fully automated:
- ✅ Schema structure validation
- ✅ UUID generation
- ✅ JSON formatting
- ✅ Basic metadata extraction

Some require human judgment:
- ⚠️ Business context (what makes a good description)
- ⚠️ Synonym selection (domain-specific terms)
- ⚠️ Join relationship types (business logic)

**Recommendation**: Start with automation, but allow human review/override for critical decisions.

### 3. **Incremental Updates**
The skills should support:
- **Incremental updates**: Update only changed parts
- **Merge strategies**: Handle conflicts when updating existing spaces
- **Version control**: Track changes over time

### 4. **Error Handling**
- Graceful degradation when documents are incomplete
- Clear error messages for missing required information
- Suggestions for fixing common issues

### 5. **Testing & Validation**
- Unit tests for each skill
- Integration tests for full workflow
- Benchmark validation (run benchmarks after creation)

---

## Benefits of This Approach

1. **Speed**: Reduce Genie Space creation time from hours to minutes
2. **Consistency**: All spaces follow same best practices
3. **Scalability**: Create multiple spaces from documentation templates
4. **Maintainability**: Update spaces by updating documentation
5. **Quality**: Automated validation ensures high-quality configurations
6. **Documentation-Driven**: Documentation becomes the source of truth

---

## Potential Challenges & Solutions

### Challenge 1: Document Format Variations
**Solution**: ✅ **LLM-based parsing handles this automatically** - adapts to any format without code changes. Can refine prompts for better extraction if needed.

### Challenge 2: Complex Business Logic
**Solution**: Extract what's possible automatically, flag ambiguous cases for human review

### Challenge 3: API Rate Limits
**Solution**: Implement retry logic with exponential backoff, batch operations

### Challenge 4: Schema Evolution
**Solution**: Version the JSON builder skill, support multiple schema versions

---

## Next Steps

1. **Design LLM prompts** for Skill 1 (Document Parser) - create prompt templates with examples
2. **Test extraction quality** - run LLM extraction on your existing documentation, refine prompts
3. **Build Skill 2** (JSON Builder) with best practices rules - this can be fixed code (reliable transformation)
4. **Test with real API** (Skill 3) in a test workspace
5. **Implement Skill 4** (Validator) to ensure quality - fixed code for reliable validation
6. **Iterate** - refine LLM prompts based on results, no code changes needed

---

## Conclusion

Your approach is **sound and highly practical**. The semantic layer being JSON makes it perfect for automation, and following best practices ensures high-quality Genie Spaces. The 4-skill architecture provides separation of concerns and allows for incremental development and testing.

**Recommendation**: Start with Skills 1 & 2 (Parser + Builder) as they provide immediate value even without API integration. Then add Skills 3 & 4 for full automation.
