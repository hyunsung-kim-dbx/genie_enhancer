# Databricks Genie Space API Reference

> **Official API Documentation**
> - Create Space: https://docs.databricks.com/api/workspace/genie/createspace
> - Update Space: https://docs.databricks.com/api/workspace/genie/updatespace
> - Last Updated: January 2026

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Authentication](#authentication)
3. [GenieSpaceExport Schema](#geniespaceexport-schema)
4. [Complete Examples](#complete-examples)
5. [Field Reference](#field-reference)
6. [Common Errors](#common-errors)
7. [Best Practices](#best-practices)

---

## API Endpoints

| Operation | Method | Endpoint | Description |
|-----------|--------|----------|-------------|
| Export | GET | `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` | Get space with serialized config |
| Create | POST | `/api/2.0/genie/spaces` | Create new space |
| Update | PATCH | `/api/2.0/genie/spaces/{space_id}` | Update existing space |
| List | GET | `/api/2.0/genie/spaces` | List all spaces |

---

## Authentication

```bash
HOST="<WORKSPACE_INSTANCE_NAME>"
TOKEN="<your_personal_access_token>"

# Example curl
curl -X GET "https://${HOST}/api/2.0/genie/spaces" \
  -H "Authorization: Bearer ${TOKEN}"
```

### Required Permissions

| Operation | Permission Level |
|-----------|-----------------|
| Export | Can View |
| Create | Can Edit (on folder) |
| Update | Can Edit (on space) |

---

## GenieSpaceExport Schema

The `serialized_space` field contains a JSON string following this schema:

### Top-Level Structure

```typescript
interface GenieSpaceExport {
  version: number;                    // Required: Schema version (currently 1)
  config?: GenieSpaceConfig;          // Sample questions for UI
  data_sources?: DataSources;         // Tables and metric views
  instructions?: Instructions;        // Instructions, examples, joins, functions
  benchmarks?: Benchmarks;            // Evaluation questions
}
```

### Visual Schema Overview

```
GenieSpaceExport
├── version: 1
├── config
│   └── sample_questions[]
│       ├── id: string (32 hex chars)
│       └── question: string[]
├── data_sources
│   ├── tables[]
│   │   ├── identifier: "catalog.schema.table"
│   │   ├── description?: string[]
│   │   └── column_configs[]
│   │       ├── column_name: string
│   │       ├── description?: string[]
│   │       ├── synonyms?: string[]
│   │       ├── exclude?: boolean
│   │       ├── get_example_values?: boolean
│   │       └── build_value_dictionary?: boolean
│   └── metric_views[]
│       ├── identifier: "catalog.schema.metric_view"
│       └── description?: string[]
├── instructions
│   ├── text_instructions[] (max 1)
│   │   ├── id: string
│   │   └── content?: string[]
│   ├── example_question_sqls[]
│   │   ├── id: string
│   │   ├── question: string[]
│   │   ├── sql: string[]
│   │   ├── parameters[]?
│   │   │   ├── name: string
│   │   │   ├── type_hint: string
│   │   │   └── description?: string[]
│   │   └── usage_guidance?: string[]
│   ├── sql_functions[]
│   │   ├── id: string
│   │   └── identifier: "catalog.schema.function"
│   ├── join_specs[]
│   │   ├── id: string
│   │   ├── left: { identifier, alias }
│   │   ├── right: { identifier, alias }
│   │   ├── sql: string[]
│   │   └── comment?: string[]
│   └── sql_snippets
│       ├── filters[]
│       │   ├── id: string
│       │   ├── sql: string[]
│       │   ├── display_name: string
│       │   └── synonyms?: string[]
│       ├── expressions[]
│       │   ├── id: string
│       │   ├── alias: string
│       │   ├── sql: string[]
│       │   └── display_name: string
│       └── measures[]
│           ├── id: string
│           ├── alias: string
│           ├── sql: string[]
│           ├── display_name: string
│           └── synonyms?: string[]
└── benchmarks
    └── questions[]
        ├── id: string
        ├── question: string[]
        └── answer[]
            ├── format: "SQL"
            └── content: string[]
```

---

## Complete Examples

### Create Space Request

```bash
curl -X POST "https://${HOST}/api/2.0/genie/spaces" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_id": "abc123def456",
    "parent_path": "/Workspace/Users/user@company.com/Genie Spaces",
    "title": "Sales Analytics Space",
    "description": "Space for analyzing sales performance and trends",
    "serialized_space": "<JSON_STRING_HERE>"
  }'
```

### Complete serialized_space Example

```json
{
  "version": 1,
  "config": {
    "sample_questions": [
      {
        "id": "a1b2c3d4e5f6789012345678abcdef01",
        "question": ["What were total sales last month?"]
      },
      {
        "id": "b2c3d4e5f6789012345678abcdef0102",
        "question": ["Show top 10 customers by revenue"]
      },
      {
        "id": "c3d4e5f6789012345678abcdef010203",
        "question": ["Compare sales by region for Q1 vs Q2"]
      },
      {
        "id": "d4e5f6789012345678abcdef01020304",
        "question": ["Which products have the highest return rate?"]
      },
      {
        "id": "e5f6789012345678abcdef0102030405",
        "question": ["Show monthly revenue trend for the past year"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "sales.analytics.customers",
        "description": [
          "Customer master data including demographics and segments"
        ],
        "column_configs": [
          {
            "column_name": "customer_id",
            "description": ["Unique identifier for each customer"],
            "synonyms": ["id", "cust_id"],
            "get_example_values": false,
            "build_value_dictionary": false
          },
          {
            "column_name": "customer_name",
            "description": ["Full name of the customer"],
            "synonyms": ["name", "client_name"],
            "get_example_values": true,
            "build_value_dictionary": false
          },
          {
            "column_name": "segment",
            "description": ["Customer segment classification"],
            "synonyms": ["tier", "category"],
            "get_example_values": true,
            "build_value_dictionary": true
          }
        ]
      },
      {
        "identifier": "sales.analytics.orders",
        "description": [
          "Transactional order data including order date, amount, and customer information"
        ],
        "column_configs": [
          {
            "column_name": "order_amount",
            "description": ["Total monetary value of the order in USD"],
            "synonyms": ["amount", "total", "revenue"],
            "get_example_values": false
          },
          {
            "column_name": "order_date",
            "description": ["Date when the order was placed"],
            "synonyms": ["date", "purchase_date"],
            "get_example_values": true
          },
          {
            "column_name": "order_id",
            "description": ["Unique identifier for the order"],
            "synonyms": ["id"],
            "get_example_values": false
          },
          {
            "column_name": "region",
            "description": ["Geographic region where the order was placed"],
            "synonyms": ["area", "territory"],
            "get_example_values": true,
            "build_value_dictionary": true
          },
          {
            "column_name": "status",
            "description": ["Current status of the order"],
            "synonyms": ["state", "order_status"],
            "get_example_values": true,
            "build_value_dictionary": true
          }
        ]
      },
      {
        "identifier": "sales.analytics.products",
        "description": [
          "Product catalog with pricing and category information"
        ]
      }
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "f6789012345678abcdef010203040506",
        "content": [
          "When calculating revenue, sum the order_amount column.",
          "When asked about 'last month', use the previous calendar month (not the last 30 days).",
          "Round all monetary values to 2 decimal places.",
          "Only include orders with status = 'completed' when calculating revenue unless otherwise specified."
        ]
      }
    ],
    "example_question_sqls": [
      {
        "id": "00112233445566778899aabbccddeeff",
        "question": ["Top N products by revenue between two dates"],
        "sql": [
          "SELECT p.product_name, SUM(o.order_amount) as total_revenue\n",
          "FROM sales.analytics.orders o\n",
          "JOIN sales.analytics.products p ON o.product_id = p.product_id\n",
          "WHERE o.order_date BETWEEN :start_date AND :end_date\n",
          "GROUP BY p.product_name\n",
          "ORDER BY total_revenue DESC\n",
          "LIMIT :limit_n"
        ],
        "parameters": [
          {
            "name": "start_date",
            "type_hint": "DATE",
            "description": ["Inclusive start date for the range"]
          },
          {
            "name": "end_date",
            "type_hint": "DATE",
            "description": ["Inclusive end date for the range"]
          },
          {
            "name": "limit_n",
            "type_hint": "INTEGER",
            "description": ["Number of products to return"]
          }
        ],
        "usage_guidance": ["Use this when a user asks for top products within a date range"]
      }
    ],
    "sql_functions": [
      {
        "id": "aabbccddeeff00112233445566778899",
        "identifier": "sales.udfs.percent_change"
      }
    ],
    "join_specs": [
      {
        "id": "11223344556677889900aabbccddeeff",
        "left": {
          "identifier": "sales.analytics.orders",
          "alias": "orders"
        },
        "right": {
          "identifier": "sales.analytics.customers",
          "alias": "customers"
        },
        "sql": ["orders.customer_id = customers.customer_id"],
        "comment": ["Link orders to customer information. One customer can have many orders."]
      },
      {
        "id": "22334455667788990011aabbccddeeff",
        "left": {
          "identifier": "sales.analytics.orders",
          "alias": "orders"
        },
        "right": {
          "identifier": "sales.analytics.products",
          "alias": "products"
        },
        "sql": ["orders.product_id = products.product_id"],
        "comment": ["Link orders to product details. Each order line references one product."]
      }
    ],
    "sql_snippets": {
      "filters": [
        {
          "id": "55667788990011223344aabbccddeeff",
          "sql": ["orders.order_amount > 1000"],
          "display_name": "high value orders",
          "synonyms": ["large orders", "big purchases"]
        },
        {
          "id": "66778899001122334455aabbccddeeff",
          "sql": ["orders.status = 'completed'"],
          "display_name": "completed orders",
          "synonyms": ["finished orders", "successful orders"]
        }
      ],
      "expressions": [
        {
          "id": "77889900112233445566aabbccddeeff",
          "alias": "order_year",
          "sql": ["YEAR(orders.order_date)"],
          "display_name": "order year"
        },
        {
          "id": "88990011223344556677aabbccddeeff",
          "alias": "order_month",
          "sql": ["MONTH(orders.order_date)"],
          "display_name": "order month"
        }
      ],
      "measures": [
        {
          "id": "99001122334455667788aabbccddeeff",
          "alias": "total_revenue",
          "sql": ["SUM(orders.order_amount)"],
          "display_name": "total revenue",
          "synonyms": ["revenue", "total sales"]
        },
        {
          "id": "00112233445566778899aabbccddeef0",
          "alias": "order_count",
          "sql": ["COUNT(orders.order_id)"],
          "display_name": "number of orders",
          "synonyms": ["order count", "total orders"]
        }
      ]
    }
  },
  "benchmarks": {
    "questions": [
      {
        "id": "33445566778899001122aabbccddeeff",
        "question": ["What was total revenue last quarter?"],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT SUM(order_amount) AS total_revenue\n",
              "FROM sales.analytics.orders\n",
              "WHERE status = 'completed'\n",
              "  AND order_date >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL 3 MONTH)\n",
              "  AND order_date < DATE_TRUNC('quarter', CURRENT_DATE)"
            ]
          }
        ]
      },
      {
        "id": "44556677889900112233aabbccddeeff",
        "question": ["Show top 10 customers by revenue"],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT c.customer_name, SUM(o.order_amount) as total_revenue\n",
              "FROM sales.analytics.orders o\n",
              "JOIN sales.analytics.customers c ON o.customer_id = c.customer_id\n",
              "WHERE o.status = 'completed'\n",
              "GROUP BY c.customer_name\n",
              "ORDER BY total_revenue DESC\n",
              "LIMIT 10"
            ]
          }
        ]
      }
    ]
  }
}
```

### Update Space Request

```bash
curl -X PATCH "https://${HOST}/api/2.0/genie/spaces/${SPACE_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "serialized_space": "<JSON_STRING_HERE>",
    "title": "Updated Space Title"
  }'
```

---

## Field Reference

### GenieSpaceExport (Top Level)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | integer | **Yes** | Schema version. Currently `1` |
| `config` | object | No | Space configuration including sample questions |
| `data_sources` | object | No | Tables and metric views |
| `instructions` | object | No | Instructions, examples, functions, joins |
| `benchmarks` | object | No | Evaluation questions |

### config.sample_questions[]

Questions displayed in the UI to guide users. **No SQL** - just natural language.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID (no dashes) |
| `question` | string[] | **Yes** | Question text as array (split at newlines) |

**Best Practice**: Include at least 5 diverse sample questions.

### data_sources.tables[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identifier` | string | **Yes** | Full path: `catalog.schema.table` |
| `description` | string[] | No | Table description |
| `column_configs` | array | No | Column-specific configurations |

### data_sources.tables[].column_configs[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `column_name` | string | **Yes** | Column name |
| `description` | string[] | No | Column description |
| `synonyms` | string[] | No | Alternative names for the column |
| `exclude` | boolean | No | If true, exclude from LLM context |
| `get_example_values` | boolean | No | Sample example values |
| `build_value_dictionary` | boolean | No | Build value index (for categorical) |

### data_sources.metric_views[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identifier` | string | **Yes** | Full path: `catalog.schema.metric_view` |
| `description` | string[] | No | Metric view description |

> **Note**: A space cannot have both tables and metric_views simultaneously.

### instructions.text_instructions[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `content` | string[] | No | Instruction text |

> **Limit**: Maximum 1 text instruction per space.

### instructions.example_question_sqls[]

Example questions paired with ground-truth SQL. Used for teaching the model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `question` | string[] | **Yes** | Natural language question |
| `sql` | string[] | **Yes** | Ground-truth SQL query |
| `parameters` | array | No | Parameters for parameterized queries |
| `usage_guidance` | string[] | No | When to use this example |

### instructions.example_question_sqls[].parameters[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Parameter name (used as `:name` in SQL) |
| `type_hint` | string | **Yes** | Data type: `STRING`, `INTEGER`, `DATE`, etc. |
| `description` | string[] | No | Parameter description |

### instructions.sql_functions[]

References to UDFs that can be used in generated SQL.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `identifier` | string | **Yes** | Full path: `catalog.schema.function` |

### instructions.join_specs[]

Pre-defined join specifications.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `left` | object | **Yes** | Left table/view `{identifier, alias}` |
| `right` | object | **Yes** | Right table/view `{identifier, alias}` |
| `sql` | string[] | **Yes** | Join condition SQL |
| `comment` | string[] | No | Description of join purpose |

### instructions.sql_snippets

Reusable SQL components for filters, expressions, and measures.

#### sql_snippets.filters[]

WHERE clause conditions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `sql` | string[] | **Yes** | SQL condition (e.g., `["status = 'active'"]`) |
| `display_name` | string | **Yes** | Human-readable name |
| `synonyms` | string[] | No | Alternative names |

#### sql_snippets.expressions[]

Row-level calculations (non-aggregated).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `alias` | string | **Yes** | Column alias for the expression |
| `sql` | string[] | **Yes** | SQL expression (e.g., `["YEAR(order_date)"]`) |
| `display_name` | string | **Yes** | Human-readable name |

#### sql_snippets.measures[]

Aggregation expressions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `alias` | string | **Yes** | Column alias for the measure |
| `sql` | string[] | **Yes** | SQL aggregation (e.g., `["SUM(amount)"]`) |
| `display_name` | string | **Yes** | Human-readable name |
| `synonyms` | string[] | No | Alternative names |

### benchmarks.questions[]

Evaluation questions with ground-truth SQL answers.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | 32-character lowercase hex UUID |
| `question` | string[] | **Yes** | Natural language question |
| `answer` | array | **Yes** | Ground-truth answer(s) |

### benchmarks.questions[].answer[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | **Yes** | Currently only `"SQL"` supported |
| `content` | string[] | **Yes** | SQL query content |

---

## Common Errors

### INVALID_PARAMETER_VALUE

```json
{
  "error_code": "INVALID_PARAMETER_VALUE",
  "message": "Invalid serialized_space: Cannot find field: <field_name> in message <message_type>"
}
```

**Cause**: The serialized_space contains a field that doesn't exist in the API schema.

**Common invalid fields**:
- `sql_snippets` (filters, expressions, measures) - **NOT in official API**
- Any field with `instructions` inside sql_snippets items

### 401 Unauthorized

**Cause**: Invalid or expired authentication token.

**Solution**: Refresh your personal access token.

### 403 Forbidden

**Cause**: Insufficient permissions.

**Solution**: Request Can Edit permissions on the space or folder.

### 404 Not Found

**Cause**: Space ID doesn't exist.

**Solution**: Verify the space_id is correct.

### 501 Not Implemented

```json
{
  "error_code": "NOT_IMPLEMENTED",
  "message": "This API is not yet supported."
}
```

**Cause**: API not enabled for your workspace.

**Solution**: Contact your Databricks Solutions Architect.

---

## Best Practices

### 1. Sample Questions

- Include **at least 5** diverse sample questions
- Cover common use cases your users will ask
- Keep questions clear and specific
- No SQL in sample questions (they're UI guidance only)

### 2. Table Descriptions

- Provide detailed descriptions for each table
- Explain what data the table contains and its scope
- Document any important business rules

### 3. Column Configurations

- Add `synonyms` for columns with multiple names (e.g., "revenue" → ["sales", "amount"])
- Enable `get_example_values` for date and categorical columns
- Enable `build_value_dictionary` for categorical columns with finite values
- Use `exclude: true` for sensitive or irrelevant columns

### 4. Text Instructions

- Keep to **one** text instruction (API limit)
- Include business rules and calculation definitions
- Explain date conventions (e.g., "last month" = previous calendar month)
- Document any data quality considerations

### 5. Join Specifications

- Define all table relationships explicitly
- Use clear, consistent aliases
- Include comments explaining the relationship

### 6. Benchmarks

- Include benchmark questions for quality evaluation
- Cover edge cases and complex queries
- Ensure SQL is correct and tested

### 7. UUID Generation

```python
import uuid

def generate_id():
    """Generate 32-character lowercase hex UUID (no dashes)"""
    return uuid.uuid4().hex.lower()
    # Example: "a1b2c3d4e5f6789012345678abcdef01"
```

**Requirements**:
- Exactly 32 characters
- Lowercase hexadecimal only (0-9, a-f)
- No dashes
- Pattern: `^[0-9a-f]{32}$`

### 8. Array Formatting

All text fields should be arrays (for cleaner diffs):

```json
// Correct
"description": ["This is the description"]
"sql": ["SELECT *\n", "FROM table\n", "WHERE x = 1"]

// Wrong
"description": "This is the description"
```

---

## Python Code Examples

### Export Space

```python
import requests
import json

def export_space(host: str, token: str, space_id: str) -> dict:
    """Export a Genie Space configuration."""
    url = f"https://{host}/api/2.0/genie/spaces/{space_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"include_serialized_space": "true"}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    result = response.json()
    # Parse the serialized_space JSON string
    if "serialized_space" in result:
        result["serialized_space_parsed"] = json.loads(result["serialized_space"])
    return result
```

### Create Space

```python
def create_space(
    host: str,
    token: str,
    warehouse_id: str,
    serialized_space: dict,
    title: str = None,
    description: str = None,
    parent_path: str = None
) -> dict:
    """Create a new Genie Space."""
    url = f"https://{host}/api/2.0/genie/spaces"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "warehouse_id": warehouse_id,
        "serialized_space": json.dumps(serialized_space)  # Must be JSON string
    }
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if parent_path:
        payload["parent_path"] = parent_path

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
```

### Update Space

```python
def update_space(
    host: str,
    token: str,
    space_id: str,
    serialized_space: dict = None,
    title: str = None,
    description: str = None
) -> dict:
    """Update an existing Genie Space."""
    url = f"https://{host}/api/2.0/genie/spaces/{space_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {}
    if serialized_space:
        payload["serialized_space"] = json.dumps(serialized_space)
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description

    if not payload:
        raise ValueError("At least one field must be provided for update")

    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
```

### Build Valid GenieSpaceExport

```python
import uuid

def generate_id() -> str:
    """Generate valid 32-char lowercase hex UUID."""
    return uuid.uuid4().hex.lower()

def build_genie_space_export(
    tables: list,
    sample_questions: list = None,
    text_instruction: str = None,
    join_specs: list = None,
    example_sqls: list = None,
    benchmarks: list = None
) -> dict:
    """Build a valid GenieSpaceExport structure."""

    export = {"version": 1}

    # Config with sample questions
    if sample_questions:
        export["config"] = {
            "sample_questions": [
                {"id": generate_id(), "question": [q]}
                for q in sample_questions
            ]
        }

    # Data sources
    if tables:
        export["data_sources"] = {"tables": tables}

    # Instructions
    instructions = {}

    if text_instruction:
        instructions["text_instructions"] = [{
            "id": generate_id(),
            "content": text_instruction if isinstance(text_instruction, list)
                       else [text_instruction]
        }]

    if example_sqls:
        instructions["example_question_sqls"] = example_sqls

    if join_specs:
        instructions["join_specs"] = join_specs

    if instructions:
        export["instructions"] = instructions

    # Benchmarks
    if benchmarks:
        export["benchmarks"] = {
            "questions": [
                {
                    "id": generate_id(),
                    "question": [b["question"]] if isinstance(b["question"], str)
                               else b["question"],
                    "answer": [{
                        "format": "SQL",
                        "content": b["sql"] if isinstance(b["sql"], list)
                                  else [b["sql"]]
                    }]
                }
                for b in benchmarks
            ]
        }

    return export
```

---

## Schema Validation

### JSON Schema (Draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GenieSpaceExport",
  "type": "object",
  "required": ["version"],
  "properties": {
    "version": {"type": "integer", "const": 1},
    "config": {
      "type": "object",
      "properties": {
        "sample_questions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "question"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "question": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    },
    "data_sources": {
      "type": "object",
      "properties": {
        "tables": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["identifier"],
            "properties": {
              "identifier": {"type": "string", "pattern": "^[^.]+\\.[^.]+\\.[^.]+$"},
              "description": {"type": "array", "items": {"type": "string"}},
              "column_configs": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["column_name"],
                  "properties": {
                    "column_name": {"type": "string"},
                    "description": {"type": "array", "items": {"type": "string"}},
                    "synonyms": {"type": "array", "items": {"type": "string"}},
                    "exclude": {"type": "boolean"},
                    "get_example_values": {"type": "boolean"},
                    "build_value_dictionary": {"type": "boolean"}
                  }
                }
              }
            }
          }
        },
        "metric_views": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["identifier"],
            "properties": {
              "identifier": {"type": "string"},
              "description": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    },
    "instructions": {
      "type": "object",
      "properties": {
        "text_instructions": {
          "type": "array",
          "maxItems": 1,
          "items": {
            "type": "object",
            "required": ["id"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "content": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "example_question_sqls": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "question", "sql"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "question": {"type": "array", "items": {"type": "string"}},
              "sql": {"type": "array", "items": {"type": "string"}},
              "parameters": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["name", "type_hint"],
                  "properties": {
                    "name": {"type": "string"},
                    "type_hint": {"type": "string"},
                    "description": {"type": "array", "items": {"type": "string"}}
                  }
                }
              },
              "usage_guidance": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "sql_functions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "identifier"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "identifier": {"type": "string"}
            }
          }
        },
        "join_specs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "left", "right", "sql"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "left": {
                "type": "object",
                "required": ["identifier", "alias"],
                "properties": {
                  "identifier": {"type": "string"},
                  "alias": {"type": "string"}
                }
              },
              "right": {
                "type": "object",
                "required": ["identifier", "alias"],
                "properties": {
                  "identifier": {"type": "string"},
                  "alias": {"type": "string"}
                }
              },
              "sql": {"type": "array", "items": {"type": "string"}},
              "comment": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "sql_snippets": {
          "type": "object",
          "properties": {
            "filters": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["id", "sql", "display_name"],
                "properties": {
                  "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
                  "sql": {"type": "array", "items": {"type": "string"}},
                  "display_name": {"type": "string"},
                  "synonyms": {"type": "array", "items": {"type": "string"}}
                }
              }
            },
            "expressions": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["id", "alias", "sql", "display_name"],
                "properties": {
                  "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
                  "alias": {"type": "string"},
                  "sql": {"type": "array", "items": {"type": "string"}},
                  "display_name": {"type": "string"}
                }
              }
            },
            "measures": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["id", "alias", "sql", "display_name"],
                "properties": {
                  "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
                  "alias": {"type": "string"},
                  "sql": {"type": "array", "items": {"type": "string"}},
                  "display_name": {"type": "string"},
                  "synonyms": {"type": "array", "items": {"type": "string"}}
                }
              }
            }
          }
        }
      }
    },
    "benchmarks": {
      "type": "object",
      "properties": {
        "questions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "question", "answer"],
            "properties": {
              "id": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
              "question": {"type": "array", "items": {"type": "string"}},
              "answer": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["format", "content"],
                  "properties": {
                    "format": {"type": "string", "enum": ["SQL"]},
                    "content": {"type": "array", "items": {"type": "string"}}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## Invalid Fields (Common Mistakes)

> **Important**: The following fields are **NOT** supported by the official API and will cause errors:

| Invalid Field | Location | Error Message |
|--------------|----------|---------------|
| `instructions` | Inside `sql_snippets.filters[]` | `Cannot find field: instructions in message ...Filter` |
| `instructions` | Inside `sql_snippets.expressions[]` | `Cannot find field: instructions in message ...Expression` |
| `instructions` | Inside `sql_snippets.measures[]` | `Cannot find field: instructions in message ...Measure` |
| `table_identifier` | Inside `sql_snippets.filters[]` | Invalid field |
| `table_identifier` | Inside `sql_snippets.expressions[]` | Invalid field |
| `table_identifier` | Inside `sql_snippets.measures[]` | Invalid field |

### Valid sql_snippets Structure

```json
"sql_snippets": {
  "filters": [
    {
      "id": "...",
      "sql": ["..."],
      "display_name": "...",
      "synonyms": ["..."]
    }
  ],
  "expressions": [
    {
      "id": "...",
      "alias": "...",
      "sql": ["..."],
      "display_name": "..."
    }
  ],
  "measures": [
    {
      "id": "...",
      "alias": "...",
      "sql": ["..."],
      "display_name": "...",
      "synonyms": ["..."]
    }
  ]
}
```

### Invalid sql_snippets Structure (DO NOT USE)

```json
"sql_snippets": {
  "filters": [
    {
      "id": "...",
      "sql": ["..."],
      "display_name": "...",
      "synonyms": ["..."],
      "instructions": ["..."],      // ❌ INVALID - causes API error
      "table_identifier": "..."     // ❌ INVALID - causes API error
    }
  ]
}
```

If you're migrating from a schema that included these fields, remove them before calling the API.
