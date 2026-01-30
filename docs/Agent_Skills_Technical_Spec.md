# Agent Skills Technical Specification

## Overview

This document provides detailed technical specifications for implementing the 4 agent skills for automated Genie Space creation.

### ⭐ Key Design Decision: LLM-Based Parsing

**Skill 1 (Document Parser) uses LLM instead of fixed code** for maximum flexibility:
- ✅ Adapts to any document format without code changes
- ✅ Handles variations in structure, language, and formatting
- ✅ Understands context and relationships
- ✅ Can be improved by refining prompts, not rewriting code

**Skills 2-4 use fixed code** for reliability:
- Skill 2: JSON transformation (deterministic)
- Skill 3: API calls (needs to be reliable)
- Skill 4: Validation (needs to be strict)

---

## Skill 1: LLM-Based Document Parser & Extractor ⭐ **RECOMMENDED**

### Function Signature

```python
def parse_document_with_llm(
    document_path: str,
    llm_client: Any,  # Databricks agent LLM or external LLM
    prompt_template: str = "default",
    output_schema: Dict = None,
    examples: List[Dict] = None
) -> Dict[str, Any]:
    """
    Use LLM to parse documentation and extract structured information.
    
    Args:
        document_path: Path to documentation file
        llm_client: LLM client (Databricks agent, OpenAI, etc.)
        prompt_template: Name of prompt template to use
        output_schema: JSON schema for desired output format
        examples: Few-shot examples for better extraction
    
    Returns:
        {
            "tables": [...],
            "columns": [...],
            "joins": [...],
            "example_queries": [...],
            "benchmarks": [...],
            "instructions": [...],
            "metadata": {...}
        }
    """
```

### LLM Prompt Design

#### Base Prompt Template
```python
DOCUMENT_EXTRACTION_PROMPT = """
You are an expert at extracting structured information from documentation 
for creating Databricks Genie Spaces.

Your task is to extract the following information from the provided document:

1. **Tables**: 
   - Table identifiers in format: catalog.schema.table
   - Table descriptions explaining scope, usage, and lifecycle

2. **Columns**:
   - Column names per table
   - Column descriptions
   - Synonyms/aliases for columns
   - Primary keys, foreign keys
   - Data types if mentioned

3. **Joins**:
   - Relationships between tables
   - Join conditions (SQL)
   - Relationship types (one-to-many, many-to-many, etc.)
   - Join descriptions/comments

4. **Example Queries**:
   - Natural language questions
   - Corresponding SQL queries
   - Parameters if queries are parameterized
   - Usage guidance

5. **Benchmarks**:
   - Evaluation questions
   - Expected SQL answers

6. **Instructions**:
   - General guidance for the Genie Space
   - Business rules and conventions

Output your extraction as a JSON object matching this schema:
{{
  "tables": [
    {{
      "identifier": "catalog.schema.table",
      "description": ["Description of the table"]
    }}
  ],
  "columns": [
    {{
      "table_identifier": "catalog.schema.table",
      "column_name": "column_name",
      "description": ["Column description"],
      "synonyms": ["synonym1", "synonym2"],
      "is_primary_key": false,
      "is_foreign_key": false
    }}
  ],
  "joins": [
    {{
      "left": {{
        "identifier": "catalog.schema.table1",
        "alias": "t1"
      }},
      "right": {{
        "identifier": "catalog.schema.table2",
        "alias": "t2"
      }},
      "sql": ["t1.id = t2.foreign_id"],
      "relationship_type": "one_to_many",
      "comment": ["Description of the join"]
    }}
  ],
  "example_queries": [
    {{
      "question": ["Natural language question"],
      "sql": ["SELECT ...", "FROM ..."],
      "parameters": [],
      "usage_guidance": ["When to use this query"]
    }}
  ],
  "benchmarks": [
    {{
      "question": ["Benchmark question"],
      "answer": {{
        "format": "SQL",
        "content": ["SELECT ..."]
      }}
    }}
  ],
  "instructions": [
    "General instruction 1",
    "General instruction 2"
  ]
}}

Document to extract from:
{document_content}

Extract the information and return ONLY valid JSON, no additional text.
"""
```

#### Few-Shot Examples
```python
EXTRACTION_EXAMPLES = [
    {
        "input": """
### 1. 디스코드에서 리액션이 가장 많은 메시지는 무엇인가요?

**필요한 테이블:**
- `main.log_discord.message`
- `main.log_discord.reaction`

**필요한 컬럼:**
- `message.message_id`, `message.content`, `message.created_at`
- `reaction.reaction_id`, `reaction.message_id`

**조인 관계:**
```sql
message LEFT JOIN reaction ON message.message_id = reaction.message_id
```
        """,
        "output": {
            "tables": [
                {
                    "identifier": "main.log_discord.message",
                    "description": ["Messages posted in Discord channels"]
                },
                {
                    "identifier": "main.log_discord.reaction",
                    "description": ["Reactions added to Discord messages"]
                }
            ],
            "columns": [
                {
                    "table_identifier": "main.log_discord.message",
                    "column_name": "message_id",
                    "description": ["Primary key for the message"],
                    "is_primary_key": True
                },
                {
                    "table_identifier": "main.log_discord.reaction",
                    "column_name": "message_id",
                    "description": ["Foreign key referencing message.message_id"],
                    "is_foreign_key": True
                }
            ],
            "joins": [
                {
                    "left": {
                        "identifier": "main.log_discord.message",
                        "alias": "message"
                    },
                    "right": {
                        "identifier": "main.log_discord.reaction",
                        "alias": "reaction"
                    },
                    "sql": ["message.message_id = reaction.message_id"],
                    "relationship_type": "one_to_many",
                    "comment": ["Join reactions to messages"]
                }
            ]
        }
    }
]
```

### LLM-Based Extraction Implementation

#### Implementation Example
```python
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class LLMDocumentParser:
    def __init__(self, llm_client: Any):
        """
        Initialize with LLM client.
        
        For Databricks agents, this would be the agent's LLM capability.
        For external use, could be OpenAI, Anthropic, etc.
        """
        self.llm_client = llm_client
        self.base_prompt = DOCUMENT_EXTRACTION_PROMPT
        self.examples = EXTRACTION_EXAMPLES
    
    def parse(
        self,
        document_path: str,
        prompt_template: str = "default",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Parse document using LLM.
        
        Uses iterative refinement if initial extraction fails validation.
        """
        document_content = Path(document_path).read_text(encoding='utf-8')
        
        # Build prompt with few-shot examples
        prompt = self._build_prompt(document_content, prompt_template)
        
        # Try extraction with retries
        for attempt in range(max_retries):
            try:
                # Call LLM
                response = self.llm_client.generate(
                    prompt=prompt,
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=4000
                )
                
                # Parse JSON response
                extracted_data = self._parse_llm_response(response)
                
                # Validate extraction
                validation_result = self._validate_extraction(extracted_data)
                
                if validation_result["is_valid"]:
                    return extracted_data
                else:
                    # Refine prompt with validation feedback
                    prompt = self._refine_prompt(
                        prompt, 
                        validation_result["errors"],
                        attempt
                    )
                    
            except json.JSONDecodeError as e:
                # LLM didn't return valid JSON, try again with clearer instructions
                prompt = self._add_json_formatting_instruction(prompt)
                continue
        
        raise ValueError(f"Failed to extract valid data after {max_retries} attempts")
    
    def _build_prompt(self, document_content: str, template: str) -> str:
        """Build prompt with document content and examples."""
        # Include few-shot examples
        examples_text = "\n\n".join([
            f"Example {i+1}:\nInput:\n{ex['input']}\n\nOutput:\n{json.dumps(ex['output'], indent=2)}"
            for i, ex in enumerate(self.examples[:2])  # Use 1-2 examples
        ])
        
        prompt = f"""{self.base_prompt}

Here are some examples of good extractions:
{examples_text}

Now extract from this document:
{document_content}
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response, handling various formats."""
        # Try to extract JSON from response
        # LLM might wrap JSON in markdown code blocks or add explanations
        
        # Remove markdown code blocks if present
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            response = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.find("```") + 3
            json_end = response.find("```", json_start)
            response = response[json_start:json_end].strip()
        
        # Parse JSON
        return json.loads(response)
    
    def _validate_extraction(self, data: Dict) -> Dict:
        """Validate extracted data structure."""
        errors = []
        
        # Check required top-level keys
        required_keys = ["tables", "columns", "joins", "example_queries"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Validate table identifiers format
        for table in data.get("tables", []):
            identifier = table.get("identifier", "")
            if not self._is_valid_table_identifier(identifier):
                errors.append(f"Invalid table identifier: {identifier}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _is_valid_table_identifier(self, identifier: str) -> bool:
        """Check if identifier follows catalog.schema.table format."""
        parts = identifier.split(".")
        return len(parts) == 3 and all(part.strip() for part in parts)
    
    def _refine_prompt(self, original_prompt: str, errors: List[str], attempt: int) -> str:
        """Refine prompt based on validation errors."""
        error_feedback = "\n".join([f"- {error}" for error in errors])
        
        refinement = f"""

Previous extraction had errors. Please fix:
{error_feedback}

Make sure to:
- Include all required fields
- Use correct table identifier format (catalog.schema.table)
- Provide valid JSON structure

Try again:
"""
        return original_prompt + refinement
    
    def _add_json_formatting_instruction(self, prompt: str) -> str:
        """Add instruction to return only JSON."""
        return prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no explanations or markdown."
```

### Alternative: Hybrid Approach (LLM + Validation)

For maximum reliability, you can combine LLM extraction with validation:

```python
class HybridDocumentParser:
    """Combines LLM flexibility with rule-based validation."""
    
    def __init__(self, llm_client: Any):
        self.llm_parser = LLMDocumentParser(llm_client)
        self.validator = ExtractionValidator()
    
    def parse(self, document_path: str) -> Dict[str, Any]:
        # Use LLM for extraction
        extracted = self.llm_parser.parse(document_path)
        
        # Validate and fix common issues
        validated = self.validator.validate_and_fix(extracted)
        
        return validated

class ExtractionValidator:
    """Validates and fixes common extraction issues."""
    
    def validate_and_fix(self, data: Dict) -> Dict:
        """Validate extraction and fix common issues."""
        # Fix table identifiers
        for table in data.get("tables", []):
            identifier = table.get("identifier", "")
            if not self._is_valid_table_identifier(identifier):
                # Try to fix common issues
                fixed = self._fix_table_identifier(identifier)
                if fixed:
                    table["identifier"] = fixed
        
        # Ensure columns reference valid tables
        valid_table_ids = {t["identifier"] for t in data.get("tables", [])}
        data["columns"] = [
            col for col in data.get("columns", [])
            if col.get("table_identifier") in valid_table_ids
        ]
        
        return data
    
    def _fix_table_identifier(self, identifier: str) -> Optional[str]:
        """Try to fix common table identifier issues."""
        # Remove extra spaces
        identifier = identifier.strip()
        
        # Fix common separators
        identifier = identifier.replace(" ", ".")
        
        # Check if it's already valid
        if self._is_valid_table_identifier(identifier):
            return identifier
        
        return None
```

---

## Skill 2: JSON Schema Builder & Best Practices Enforcer

### Function Signature

```python
def build_genie_space_json(
    parsed_data: Dict[str, Any],
    space_config: Dict[str, Any] = None,
    apply_best_practices: bool = True
) -> str:
    """
    Build GenieSpaceExport JSON from parsed document data.
    
    Args:
        parsed_data: Output from Skill 1
        space_config: Additional config (title, description, warehouse_id)
        apply_best_practices: Whether to apply best practices rules
    
    Returns:
        JSON string following GenieSpaceExport schema
    """
```

### Best Practices Enforcement

#### 1. Metadata Enhancement
```python
def enhance_table_descriptions(tables: List[Dict]) -> List[Dict]:
    """
    Enhance table descriptions following best practices:
    - Scope of the table
    - When Genie should use the table
    - Lifecycle of entities
    - Relationships to wider Genie Space
    
    Template:
    "This table covers [scope]. Use this table for [use cases]. 
     [Lifecycle information]. [Relationship information]."
    """
```

#### 2. Synonym Generation
```python
def generate_synonyms(column: Dict, context: str) -> List[str]:
    """
    Generate synonyms from:
    - Column name variations (camelCase, snake_case, etc.)
    - Business terms found in documentation
    - Common aliases
    - Acronyms
    """
```

#### 3. Join Specification Builder
```python
def build_join_spec(join_data: Dict) -> Dict:
    """
    Convert extracted join to JoinSpec format.
    
    Returns:
        {
            "id": generate_uuid(),
            "left": {
                "identifier": join_data["left"]["identifier"],
                "alias": join_data["left"]["alias"]
            },
            "right": {
                "identifier": join_data["right"]["identifier"],
                "alias": join_data["right"]["alias"]
            },
            "sql": join_data["sql"],  # Array of strings
            "comment": join_data.get("comment", [])
        }
    """
```

#### 4. Example Query Builder
```python
def build_example_question_sql(query_data: Dict) -> Dict:
    """
    Convert extracted query to ExampleQuestionSql format.
    
    Returns:
        {
            "id": generate_uuid(),
            "question": query_data["question"],  # Array of strings
            "sql": query_data["sql"],  # Array of strings
            "parameters": query_data.get("parameters", []),
            "usage_guidance": query_data.get("usage_guidance", [])
        }
    """
```

### Implementation Example

```python
import json
import uuid
from typing import Dict, List

class GenieSpaceJSONBuilder:
    def __init__(self):
        self.version = 1
    
    def build(self, parsed_data: Dict, space_config: Dict = None) -> str:
        space_config = space_config or {}
        
        genie_space = {
            "version": self.version,
            "config": self._build_config(parsed_data),
            "data_sources": self._build_data_sources(parsed_data),
            "instructions": self._build_instructions(parsed_data),
            "benchmarks": self._build_benchmarks(parsed_data)
        }
        
        return json.dumps(genie_space, indent=2, ensure_ascii=False)
    
    def _build_config(self, parsed_data: Dict) -> Dict:
        """Build config section with sample questions."""
        sample_questions = []
        for query in parsed_data.get("example_queries", [])[:5]:  # Top 5 as samples
            sample_questions.append({
                "id": self._generate_uuid(),
                "question": query["question"]
            })
        
        return {
            "sample_questions": sample_questions
        }
    
    def _build_data_sources(self, parsed_data: Dict) -> Dict:
        """Build data_sources section."""
        tables = []
        for table_data in parsed_data.get("tables", []):
            table = {
                "identifier": table_data["identifier"],
                "description": table_data.get("description", [])
            }
            
            # Add column configs
            columns = [
                col for col in parsed_data.get("columns", [])
                if col.get("table_identifier") == table_data["identifier"]
            ]
            
            if columns:
                table["column_configs"] = [
                    self._build_column_config(col) for col in columns
                ]
            
            tables.append(table)
        
        return {"tables": tables}
    
    def _build_column_config(self, column_data: Dict) -> Dict:
        """Build ColumnConfig following best practices."""
        config = {
            "column_name": column_data["column_name"],
            "description": column_data.get("description", []),
            "synonyms": column_data.get("synonyms", []),
            "exclude": column_data.get("exclude", False),
            "get_example_values": column_data.get("get_example_values", True),
            "build_value_dictionary": column_data.get("build_value_dictionary", False)
        }
        
        # Apply best practices
        if not config["description"]:
            config["description"] = [f"Column: {config['column_name']}"]
        
        return config
    
    def _build_instructions(self, parsed_data: Dict) -> Dict:
        """Build instructions section."""
        instructions = {
            "text_instructions": self._build_text_instructions(parsed_data),
            "example_question_sqls": self._build_example_question_sqls(parsed_data),
            "join_specs": self._build_join_specs(parsed_data),
            "sql_functions": parsed_data.get("sql_functions", [])
        }
        return instructions
    
    def _build_join_specs(self, parsed_data: Dict) -> List[Dict]:
        """Build join specifications."""
        join_specs = []
        for join_data in parsed_data.get("joins", []):
            join_specs.append({
                "id": self._generate_uuid(),
                "left": {
                    "identifier": join_data["left"]["identifier"],
                    "alias": join_data["left"]["alias"]
                },
                "right": {
                    "identifier": join_data["right"]["identifier"],
                    "alias": join_data["right"]["alias"]
                },
                "sql": join_data["sql"],
                "comment": join_data.get("comment", [])
            })
        return join_specs
    
    def _build_example_question_sqls(self, parsed_data: Dict) -> List[Dict]:
        """Build example question-SQL pairs."""
        examples = []
        for query in parsed_data.get("example_queries", []):
            examples.append({
                "id": self._generate_uuid(),
                "question": query["question"],
                "sql": query["sql"],
                "parameters": query.get("parameters", []),
                "usage_guidance": query.get("usage_guidance", [])
            })
        return examples
    
    def _build_benchmarks(self, parsed_data: Dict) -> Dict:
        """Build benchmarks section."""
        benchmark_questions = []
        for benchmark in parsed_data.get("benchmarks", []):
            benchmark_questions.append({
                "id": self._generate_uuid(),
                "question": benchmark["question"],
                "answer": [{
                    "format": "SQL",
                    "content": benchmark["answer"]["content"]
                }]
            })
        
        return {"questions": benchmark_questions}
    
    def _generate_uuid(self) -> str:
        """Generate UUID without dashes."""
        return uuid.uuid4().hex
```

---

## Skill 3: Genie Space API Handler

### Function Signature

```python
class GenieSpaceAPIHandler:
    def __init__(self, host: str, token: str):
        self.host = host
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def export_space(self, space_id: str) -> Dict:
        """Export existing Genie Space."""
    
    def create_space(
        self,
        serialized_space: str,
        warehouse_id: str,
        title: str = None,
        description: str = None,
        parent_path: str = None
    ) -> Dict:
        """Create new Genie Space."""
    
    def update_space(
        self,
        space_id: str,
        serialized_space: str = None,
        warehouse_id: str = None,
        title: str = None,
        description: str = None
    ) -> Dict:
        """Update existing Genie Space."""
```

### Implementation Example

```python
import requests
from typing import Dict, Optional

class GenieSpaceAPIHandler:
    def __init__(self, host: str, token: str):
        self.base_url = f"https://{host}/api/2.0/genie"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def export_space(self, space_id: str) -> Dict:
        """Export existing Genie Space."""
        url = f"{self.base_url}/spaces/{space_id}"
        params = {"include_serialized_space": "true"}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def create_space(
        self,
        serialized_space: str,
        warehouse_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        parent_path: Optional[str] = None
    ) -> Dict:
        """Create new Genie Space."""
        url = f"{self.base_url}/spaces"
        
        payload = {
            "warehouse_id": warehouse_id,
            "serialized_space": serialized_space
        }
        
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        if parent_path:
            payload["parent_path"] = parent_path
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def update_space(
        self,
        space_id: str,
        serialized_space: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update existing Genie Space."""
        url = f"{self.base_url}/spaces/{space_id}"
        
        payload = {}
        if serialized_space:
            payload["serialized_space"] = serialized_space
        if warehouse_id:
            payload["warehouse_id"] = warehouse_id
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        
        response = requests.patch(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
```

---

## Skill 4: Validation & Best Practices Checker

### Function Signature

```python
def validate_genie_space_json(
    json_string: str,
    strict_mode: bool = False
) -> ValidationReport:
    """
    Validate GenieSpaceExport JSON against schema and best practices.
    
    Returns:
        ValidationReport with:
        - is_valid: bool
        - schema_errors: List[str]
        - best_practices_score: float (0-1)
        - missing_elements: List[str]
        - recommendations: List[str]
        - warnings: List[str]
    """
```

### Validation Checks

#### 1. Schema Validation
```python
def validate_schema(json_data: Dict) -> List[str]:
    """
    Check:
    - Required fields present
    - Field types correct
    - UUIDs properly formatted
    - Array types are arrays
    - String arrays properly formatted
    """
```

#### 2. Best Practices Validation
```python
def validate_best_practices(json_data: Dict) -> Dict:
    """
    Check:
    - Table descriptions follow best practices (scope, usage, lifecycle)
    - Column descriptions present and meaningful
    - Synonyms populated for key columns
    - Joins have proper relationship types
    - Example queries have usage guidance
    - Benchmarks have desired output format
    - Sample questions present
    """
```

### Implementation Example

```python
from typing import Dict, List
import json
import re

class GenieSpaceValidator:
    def __init__(self):
        self.uuid_pattern = re.compile(r'^[0-9a-f]{32}$')
    
    def validate(self, json_string: str) -> Dict:
        """Main validation function."""
        try:
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return {
                "is_valid": False,
                "schema_errors": [f"Invalid JSON: {str(e)}"],
                "best_practices_score": 0.0
            }
        
        schema_errors = self._validate_schema(json_data)
        best_practices = self._validate_best_practices(json_data)
        
        return {
            "is_valid": len(schema_errors) == 0,
            "schema_errors": schema_errors,
            "best_practices_score": best_practices["score"],
            "missing_elements": best_practices["missing"],
            "recommendations": best_practices["recommendations"],
            "warnings": best_practices["warnings"]
        }
    
    def _validate_schema(self, data: Dict) -> List[str]:
        """Validate against GenieSpaceExport schema."""
        errors = []
        
        # Check version
        if "version" not in data:
            errors.append("Missing required field: version")
        
        # Check data_sources
        if "data_sources" in data:
            if "tables" in data["data_sources"]:
                for table in data["data_sources"]["tables"]:
                    if "identifier" not in table:
                        errors.append("Table missing identifier")
                    if not self._is_valid_table_identifier(table.get("identifier", "")):
                        errors.append(f"Invalid table identifier: {table.get('identifier')}")
        
        # Check instructions
        if "instructions" in data:
            instructions = data["instructions"]
            
            # Validate example_question_sqls
            if "example_question_sqls" in instructions:
                for example in instructions["example_question_sqls"]:
                    if "id" not in example or not self.uuid_pattern.match(example["id"]):
                        errors.append("Invalid or missing UUID in example_question_sql")
                    if "question" not in example or not isinstance(example["question"], list):
                        errors.append("example_question_sql missing question array")
                    if "sql" not in example or not isinstance(example["sql"], list):
                        errors.append("example_question_sql missing sql array")
            
            # Validate join_specs
            if "join_specs" in instructions:
                for join_spec in instructions["join_specs"]:
                    if "id" not in join_spec or not self.uuid_pattern.match(join_spec["id"]):
                        errors.append("Invalid or missing UUID in join_spec")
                    if "left" not in join_spec or "right" not in join_spec:
                        errors.append("join_spec missing left or right")
        
        return errors
    
    def _validate_best_practices(self, data: Dict) -> Dict:
        """Validate best practices compliance."""
        score = 1.0
        missing = []
        recommendations = []
        warnings = []
        
        # Check table descriptions
        if "data_sources" in data and "tables" in data["data_sources"]:
            for table in data["data_sources"]["tables"]:
                description = table.get("description", [])
                if not description:
                    missing.append(f"Table {table.get('identifier')} missing description")
                    score -= 0.1
                elif len(" ".join(description)) < 50:
                    recommendations.append(
                        f"Table {table.get('identifier')} description is too short. "
                        "Should include scope, usage conditions, and lifecycle."
                    )
        
        # Check column metadata
        if "data_sources" in data and "tables" in data["data_sources"]:
            for table in data["data_sources"].get("tables", []):
                for col_config in table.get("column_configs", []):
                    if not col_config.get("description"):
                        warnings.append(
                            f"Column {col_config.get('column_name')} in table "
                            f"{table.get('identifier')} missing description"
                        )
                    if not col_config.get("synonyms"):
                        recommendations.append(
                            f"Consider adding synonyms for column "
                            f"{col_config.get('column_name')}"
                        )
        
        # Check sample questions
        if "config" not in data or not data["config"].get("sample_questions"):
            missing.append("No sample questions defined")
            score -= 0.2
        
        # Check example queries have usage guidance
        if "instructions" in data:
            example_queries = data["instructions"].get("example_question_sqls", [])
            for query in example_queries:
                if not query.get("usage_guidance"):
                    recommendations.append(
                        f"Example query '{query.get('question', [''])[0]}' "
                        "should include usage_guidance"
                    )
        
        score = max(0.0, score)  # Ensure score is non-negative
        
        return {
            "score": score,
            "missing": missing,
            "recommendations": recommendations,
            "warnings": warnings
        }
    
    def _is_valid_table_identifier(self, identifier: str) -> bool:
        """Check if table identifier follows catalog.schema.table format."""
        parts = identifier.split(".")
        return len(parts) == 3 and all(part for part in parts)
```

---

## Integration Example

```python
# Complete workflow with LLM-based parsing
def create_genie_space_from_document(
    document_path: str,
    warehouse_id: str,
    llm_client: Any,  # Databricks agent LLM
    api_handler: GenieSpaceAPIHandler,
    title: str = None
) -> Dict:
    """End-to-end workflow."""
    
    # Step 1: Parse document using LLM
    parser = LLMDocumentParser(llm_client)
    parsed_data = parser.parse(document_path)
    
    # Step 2: Build JSON
    builder = GenieSpaceJSONBuilder()
    genie_json = builder.build(parsed_data, {"title": title})
    
    # Step 3: Validate
    validator = GenieSpaceValidator()
    validation_report = validator.validate(genie_json)
    
    if not validation_report["is_valid"]:
        raise ValueError(f"Validation failed: {validation_report['schema_errors']}")
    
    if validation_report["best_practices_score"] < 0.7:
        print("Warning: Best practices score is low")
        print("Recommendations:", validation_report["recommendations"])
    
    # Step 4: Create space
    result = api_handler.create_space(
        serialized_space=genie_json,
        warehouse_id=warehouse_id,
        title=title or "Auto-generated Genie Space"
    )
    
    return result
```

---

## Testing Strategy

### Unit Tests
- Test each skill independently
- Mock external dependencies (API calls, file I/O)
- Test edge cases and error handling

### Integration Tests
- Test full workflow with sample documents
- Test API interactions (use test workspace)
- Validate output JSON against schema

### End-to-End Tests
- Create test Genie Space from documentation
- Run benchmarks
- Verify space functions correctly
