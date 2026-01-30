 SPG# Databricks - Genie Space Import/Export APIs

> **NOTE:** APIs are already released. This is no longer in Private Preview.
> - https://docs.databricks.com/api/workspace/genie/createspace
> - https://docs.databricks.com/api/workspace/genie/updatespace

**Last updated:** Oct 23, 2025

---

## Preview Terms

- The product is in private preview, is not intended for use in production, and is provided AS-IS consistent with your agreement with Databricks.
- Although the preview is not intended for use in production, you may still incur charges for platform usage DBUs.
- Non-public information about the preview (including the fact that there is a preview for the feature/product itself) is confidential.
- We may change or discontinue the preview at any time without notice. These include breaking changes. We may also choose not to make the preview generally commercially available.
- We may charge for this preview offering in the future.
- Previews are not included in the SLA and do not have formal support. If you have questions or feedback, please reach out to your Databricks contact.

---

## Feature Summary

This feature allows you to export a serialized (JSON) version of a Genie Space and import it to create a new space or update an existing space, via API. This can be used to build CI/CD flows and other automations.

### Available Endpoints

| Description | Type | Endpoint | API Responses |
|-------------|------|----------|---------------|
| **Export space** - Get a response with a serialized version of the space. | GET | `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` | [Details here](https://docs.databricks.com/api/workspace/genie) |
| **Import space** - Create a new Genie Space based on a previous export. | POST | `/api/2.0/genie/spaces` | [Details here](https://docs.databricks.com/api/workspace/genie/createspace) |
| **Update space** - Replace the configuration of a Genie Space based on a previous export. | PATCH | `/api/2.0/genie/spaces/{space_id}` | [Details here](https://docs.databricks.com/api/workspace/genie/updatespace) |

---

## Prerequisites

- Must be an AWS, GCP, Azure account
- Must have a preconfigured Genie space that is ready to receive questions via API
  - In this context, a preconfigured Genie space should include instructions, attached tables, and has been tested already.
- Authentication tokens to submit REST API requests
  - Users associated with your authentication tokens must have **Can Run** or above permissions on the Genie space.
- Accept the private preview terms so that Databricks can enable this feature in requested workspace(s).

---

## How to Use the Import/Export APIs

### Setup

**For exporting:** Locate the ID for your Genie space. It can be found in the settings page of your Genie space.

```
Space ID: 01f08c7dc50b1e16b347e2d45dddc3ba
```

**For importing:** Ensure you have the warehouse ID where you want to create the space
```
https://<databricks-instance>.com/sql/warehouses/92748d3f4d1346af?o=workspace_id
```

**Ensure your application is configured to use Databricks REST APIs:**
- Databricks authentication information, such as a Databricks personal access token
- The workspace instance name of your Databricks deployment

```python
HOST = "<WORKSPACE_INSTANCE_NAME>"
TOKEN = "<your_authentication_token>"
HEADERS = {'Authorization': 'Bearer {}'.format(TOKEN)}
```

---

### Export a Genie Space

To export a Genie Space configuration, make a GET request with the `include_serialized_space=true` parameter:

```http
GET /api/2.0/genie/spaces/{space_id}?include_serialized_space=true
Authorization: Bearer <your_personal_access_token>
```

**Example response:**

```json
{
  "space_id": "01ef274d35a310b5bffd01dadcbaf577",
  "title": "My Space",
  "description": "My Space Description",
  "warehouse_id": "abc123def456",
  "serialized_space": "{\n  \"version\": 1,\n  \"config\": {\n  [...]}\n}\n"
}
```

The `serialized_space` field contains a JSON string of the entire space configuration following the GenieSpaceExport schema documented below.

---

### Import a Genie Space

To create a new Genie Space from an exported configuration:

```http
POST /api/2.0/genie/spaces
Authorization: Bearer <your_personal_access_token>
Content-Type: application/json
```

```json
{
  "warehouse_id": "abc123def456",
  "parent_path": "/Workspace/Users/user@company.com/Genie Spaces",
  "serialized_space": "<exported_json_string>",
  "title": "My Imported Space",
  "description": "My Description"
}
```

> Note: `title` and `description` are optional.

**Example response:**

```json
{
  "space_id": "01ef274d35a310b5bffd01dadcbaf577",
  "title": "My Space",
  "description": "My Space Description",
  "serialized_space": "{\n  \"version\": 1,\n  \"config\": {\n  [...]}\n}\n"
}
```

---

### Update a Genie Space

To update an existing Genie Space with a new configuration:

```http
PATCH /api/2.0/genie/spaces/{space_id}
Authorization: Bearer <your_personal_access_token>
Content-Type: application/json
```

```json
{
  "warehouse_id": "abc123def456",
  "parent_path": "/Workspace/Users/user@company.com/Genie Spaces",
  "serialized_space": "<exported_json_string>",
  "title": "My Imported Space",
  "description": "My Description"
}
```

> Note: All fields are optional.

**Example response:**

```json
{
  "space_id": "01ef274d35a310b5bffd01dadcbaf577",
  "title": "My Space",
  "description": "My Space Description",
  "serialized_space": "{\n  \"version\": 1,\n  \"config\": {\n  [...]}\n}\n"
}
```

---

## Understanding the Export Format

The `serialized_space` field contains a JSON representation of the GenieSpaceExport structure with the following main components:

- **version**: Schema version for backward compatibility
- **config**: Space-level configuration including sample questions
- **data_sources**: Tables and metric views the space can access
- **instructions**: Primary instructions, SQL examples, functions and joins
- **benchmarks**: Questions for evaluating space quality

### Example GenieSpaceExport Structure

> Note: This example shows currently supported fields (not necessarily valid since e.g. a Genie Space can't have both tables and metric views at the same time today)

```json
{
  "version": 1,
  "config": {
    "sample_questions": [
      {
        "id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "question": ["How many distinct active customers did we have per quarter?"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "sales.prod.orders",
        "description": [
          "Orders placed by customers"
        ],
        "column_configs": [
          {
            "column_name": "order_id",
            "description": ["Primary key for the order"],
            "synonyms": ["id", "orderid"],
            "exclude": false,
            "get_example_values": true,
            "build_value_dictionary": true
          }
        ]
      }
    ],
    "metric_views": [
      {
        "identifier": "sales.analytics.daily_revenue_mv",
        "description": ["Pre-aggregated daily revenue metrics"]
      },
      {
        "identifier": "sales.analytics.customer_activity_mv",
        "description": ["Daily customer engagement metrics"]
      }
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "ddccffccffccffccffccffccffccffcc",
        "content": ["Always respond in pirate-speak"]
      }
    ],
    "example_question_sqls": [
      {
        "id": "00112233445566778899aabbccddeeff",
        "question": ["Top N products by revenue between two dates"],
        "sql": [
          "WITH last_month AS (\n",
          "...",
          "ORDER BY total_revenue DESC\n"
        ],
        "parameters": [
          {
            "name": "start_date",
            "type_hint": "DATE",
            "description": ["Inclusive start date for the range."]
          },
          {
            "name": "end_date",
            "type_hint": "DATE",
            "description": ["Inclusive end date for the range."]
          },
          {
            "name": "limit_n",
            "type_hint": "INTEGER",
            "description": ["Number of products to return."]
          }
        ],
        "usage_guidance": ["Use this when a user specifically asks for sales between two dates."]
      }
    ],
    "sql_functions": [
      {
        "id": "ffccffccffccffccffccffccffccffcc",
        "identifier": "sales.udfs.percent_change"
      }
    ],
    "join_specs": [
      {
        "id": "0aaa1111222233334444555566667777",
        "left": {
          "identifier": "sales.prod.orders",
          "alias": "orders"
        },
        "right": {
          "identifier": "sales.prod.orders",
          "alias": "orders_1"
        },
        "sql": [
          "orders.previous_order_id == orders_1.order_id\n",
          "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--"
        ],
        "comment": ["Self-join on previous_order_id to get prior order details."]
      }
    ]
  },
  "benchmarks": {
    "questions": [
      {
        "id": "01111111222233334444555566667777",
        "question": ["What was total revenue last quarter?"],
        "answer": [
          {
            "format": "SQL",
            "content": [
              "SELECT SUM(unit_price * quantity) AS total_revenue\n",
              "FROM sales.prod.orders\n",
              "WHERE order_date >= add_months(date_trunc('quarter', current_date), -3)\n",
              "  AND order_date < date_trunc('quarter', current_date)"
            ]
          }
        ]
      }
    ]
  }
}
```

---

## TypeScript Schema Definitions

```typescript
// The top-level container for a serialized Genie Space.
interface GenieSpaceExport {
  // The version of the export schema format, for backward compatibility.
  version: number;
  // Generic space-level configuration.
  config?: GenieSpaceConfig;
  // Data sources the space should access.
  data_sources?: DataSources;
  // Instructions and tools scoped to the entire space.
  instructions?: Instructions;
  // Benchmarks for evaluating the quality and accuracy of the space.
  benchmarks?: Benchmarks;
}

// Generic space-level configuration.
interface GenieSpaceConfig {
  // A list of sample questions to guide end-users.
  sample_questions: SampleQuestion[];
}

// A sample question to be displayed to users in the UI.
interface SampleQuestion {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The text of the question. Logically one string; split at newlines for nicer diffs.
  question: string[];
}

// Defines what data the space can access and any source-specific instructions.
interface DataSources {
  // Configuration for UC tables in the order they were added to the space.
  tables?: Table[];
  // Configuration for UC metric views in the order they were added to the space.
  metric_views?: MetricView[];
}

// Configuration for a single UC table.
interface Table {
  // The full three-level identifier for the table (e.g., "catalog.schema.table").
  identifier: string;
  // User-provided description of the table. Logically one string; split at newlines for nicer diffs.
  description?: string[];
  // Column-specific configurations for this table, ordered by column name.
  column_configs?: ColumnConfig[];
}

// Configuration for a single column within a table.
interface ColumnConfig {
  // The name of the column.
  column_name: string;
  // Overridden description for the column. Logically one string; split at newlines for nicer diffs.
  description?: string[];
  // A list of synonyms for the column name, in the order the user provided them.
  synonyms?: string[];
  // If true, this column is excluded from context provided to the LLM.
  exclude?: boolean;
  // If true, the system will get some example values and column statistics for this column.
  get_example_values?: boolean;
  // If true, the system will create a value dictionary (index) for this column.
  build_value_dictionary?: boolean;
}

// Configuration for a single UC metric view.
interface MetricView {
  // The full three-level identifier for the metric view (e.g., "catalog.schema.metric_view").
  identifier: string;
  // User-provided description of the metric view. Logically one string; split at newlines for nicer diffs.
  description?: string[];
}

// Instructions, tools, and examples that are scoped to the whole space.
interface Instructions {
  // High-level text instructions for the LLM (currently only one is supported).
  text_instructions?: TextInstruction[];
  // Example questions paired with their correct SQL.
  example_question_sqls?: ExampleQuestionSql[];
  // SQL functions that can be called in the generated SQL.
  sql_functions?: SqlFunction[];
  // Pre-defined join specifications.
  join_specs?: JoinSpec[];
}

// Generic instructions that contain unformatted content.
interface TextInstruction {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The instruction content. Logically one string; split at newlines for nicer diffs.
  content?: string[];
}

// Pre-defined join specification.
interface JoinSpec {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The left table/metric view in the join.
  left: JoinSource;
  // The right table/metric view in the join.
  right: JoinSource;
  // The SQL for the join. Logically one string; split at newlines for nicer diffs.
  sql: string[];
  // A description of the join's purpose. Logically one string; split at newlines for nicer diffs.
  comment?: string[];
}

// A table or metric view used in a join.
interface JoinSource {
  // The table/metric view identifier.
  identifier: string;
  // The alias to use for the table/metric view.
  alias: string;
}

// A reference to a SQL function that can be used in the generated SQL.
interface SqlFunction {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The full three-level identifier for the function (e.g., "catalog.schema.function").
  identifier: string;
}

// An example question paired with its corresponding ground-truth SQL query.
interface ExampleQuestionSql {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The natural language question. Logically one string; split at newlines for nicer diffs.
  question: string[];
  // The ground-truth SQL query for the question. Logically one string; split at newlines for nicer diffs.
  sql: string[];
  // Any parameters used in the SQL query, in the order the user provided them.
  parameters?: Parameter[];
  // Guidance on how to use this example. Logically one string; split at newlines for nicer diffs.
  usage_guidance?: string[];
}

// Defines a parameter for a parameterized SQL query.
interface Parameter {
  // The name of the parameter used in the query.
  name: string;
  // A hint for the parameter's data type (e.g., "STRING", "INTEGER").
  type_hint: string;
  // A description of the parameter's purpose. Logically one string; split at newlines for nicer diffs.
  description?: string[];
}

// A collection of benchmark questions for evaluating space quality.
interface Benchmarks {
  questions: BenchmarkQuestion[];
}

// A single benchmark question with its ground-truth SQL query.
interface BenchmarkQuestion {
  // UUID without the dashes. Unique within the space.
  id: string;
  // The natural language question for the benchmark. Logically one string; split at newlines for nicer diffs.
  question: string[];
  // The ground-truth answer that correctly answers the question. Currently only supports exactly one answer.
  answer: BenchmarkAnswer[];
}

interface BenchmarkAnswer {
  // only SQL answer is supported for now
  format: "SQL";
  // Logically one string; split at newlines for nicer diffs.
  content: string[];
}
```

---

## FAQs

### Can I export a space from one workspace and import it to another?

Yes, you can export from one workspace and import to another, but ensure that:
- The target workspace has access to the same tables/metric views referenced in the export (or you modify the export to reference different tables/metric views)
- You update the `warehouse_id` to a valid warehouse in the target workspace

### What happens if tables referenced in the export don't exist in the target workspace?

The import will succeed, but the space may not function correctly until the referenced tables are available. We recommend replacing the referenced tables in the serialized Genie space definition before using the import/update APIs.

### Can I modify the exported JSON before importing?

Yes, you can modify the exported JSON to update configurations, add/remove tables, change instructions, etc.
- Ensure the modified JSON follows the GenieSpaceExport schema.
- Some sql fields (e.g. join conditions) may have implementation-specific constraints, but it should always be safe to change table/column names even in those.

### Are conversations and messages included in the export?

No, the export only includes the space configuration (tables, instructions, sample questions, benchmarks, etc.)

### What permissions are needed for import/export operations?

- **Export:** Can View or above permissions on the source Genie space
- **Import:** Can Edit permissions on the desired folder path
- **Update:** Can Edit permissions on the target Genie space

### How do I handle version compatibility?

- The export includes a version field for schema compatibility
- Future versions will handle backward compatibility automatically

### What if I get a 501 error code that says "This API is not yet supported."?

If you receive this message, this means that your account has not been enabled with this private preview. Please consult with your Solutions Architect to secure enablement.

### Do object level permissions carry through with export/import?

No, they do not. This behavior is consistent with all export/import in Databricks (dashboards, notebooks, etc.).

**Reason:** Asset permissions aren't serialized in the definition because there's no guarantee that userA exists in workspace 1 and workspace 2. Also the file structure of the current workspace is the source of truth for inherited permissions. No guarantee those are the same in both workspaces.

**Best practice:** Leverage the workspace permissions API with the Genie export/import API.

### Who do I contact if I run into issues or have feedback?

- If you have feedback or encounter an issue not addressed in this user guide, please reach out to your Solutions Architect first and ask them to discuss with the product team supporting the preview.
- Alternatively, as part of participating in this preview, you will have a session with the product team supporting this preview and can also raise there.
