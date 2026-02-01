# FINAL COMPREHENSIVE WORKING SAMPLE
# Based on official Databricks reference structure
# Testing ALL join relationship types

import json
import uuid
import requests

# Helper function to generate UUID
def gen_id():
    return uuid.uuid4().hex.lower()

# These would be set in your environment
# warehouse_id = "your_warehouse_id"
# url = "https://your-workspace.databricks.com/api/2.0/genie/spaces"
# headers = {"Authorization": "Bearer your_token"}

print("=== FINAL WORKING GENIE SPACE SAMPLE ===")
print("Based on official Databricks reference with all corrections")
print("Testing ALL join relationship types\n")

# Generate sorted IDs upfront
sample_q_ids = sorted([gen_id() for _ in range(5)])
text_inst_id = gen_id()
example_sql_ids = sorted([gen_id() for _ in range(3)])
join_spec_ids = sorted([gen_id() for _ in range(5)])
filter_ids = sorted([gen_id() for _ in range(2)])
expr_ids = sorted([gen_id() for _ in range(3)])
measure_ids = sorted([gen_id() for _ in range(3)])
benchmark_ids = sorted([gen_id() for _ in range(3)])

final_working_config = {
    "version": 1,

    # CONFIG: Sample questions for UI (no SQL - just guidance)
    "config": {
        "sample_questions": [
            {"id": sample_q_ids[0], "question": ["What is the total revenue from all transactions?"]},
            {"id": sample_q_ids[1], "question": ["Show top 10 customers by total spending"]},
            {"id": sample_q_ids[2], "question": ["What are the most popular products?"]},
            {"id": sample_q_ids[3], "question": ["Show sales by payment method"]},
            {"id": sample_q_ids[4], "question": ["What is the average transaction value?"]}
        ]
    },

    # DATA SOURCES: Tables with full column configurations
    # IMPORTANT: Tables must be sorted by identifier alphabetically
    "data_sources": {
        "tables": [
            {
                "identifier": "samples.bakehouse.sales_customers",
                "description": [
                    "Contains customer information including names, location, and contact details. ",
                    "Each row represents one unique customer. ",
                    "Use this table for customer demographics and to join with transactions for customer-level analysis."
                ],
                # IMPORTANT: column_configs must be sorted by column_name alphabetically
                "column_configs": [
                    {
                        "column_name": "customerID",
                        "description": ["Unique identifier for each customer. Primary key."],
                        "synonyms": ["customer id", "customer identifier", "cust id"],
                        "exclude": False,
                        "get_example_values": True,
                        "build_value_dictionary": False
                    },
                    {
                        "column_name": "first_name",
                        "description": ["Customer's first name"],
                        "synonyms": ["firstname", "given name"],
                        "exclude": False
                    },
                    {
                        "column_name": "last_name",
                        "description": ["Customer's last name"],
                        "synonyms": ["lastname", "surname", "family name"],
                        "exclude": False
                    },
                    {
                        "column_name": "state",
                        "description": ["US state where customer is located"],
                        "synonyms": ["location", "region", "state code"],
                        "exclude": False,
                        "get_example_values": True,
                        "build_value_dictionary": True
                    }
                ]
            },
            {
                "identifier": "samples.bakehouse.sales_transactions",
                "description": [
                    "Transaction data including products purchased, prices, payment methods, and timestamps. ",
                    "Each row represents one transaction. ",
                    "Use for revenue analysis, product popularity, and payment method trends."
                ],
                "column_configs": [
                    {
                        "column_name": "customerID",
                        "description": ["Foreign key linking to customers table"],
                        "synonyms": ["customer id", "cust id"],
                        "exclude": False
                    },
                    {
                        "column_name": "paymentMethod",
                        "description": ["Payment method used for transaction (e.g., credit card, cash, debit)"],
                        "synonyms": ["payment type", "payment", "method"],
                        "exclude": False,
                        "get_example_values": True,
                        "build_value_dictionary": True
                    },
                    {
                        "column_name": "product",
                        "description": ["Product name purchased in this transaction"],
                        "synonyms": ["item", "product name", "item name"],
                        "exclude": False,
                        "get_example_values": True,
                        "build_value_dictionary": True
                    },
                    {
                        "column_name": "totalPrice",
                        "description": ["Total transaction amount in USD. Use for revenue calculations."],
                        "synonyms": ["price", "amount", "revenue", "sales", "total", "cost"],
                        "exclude": False
                    },
                    {
                        "column_name": "transactionTimestamp",
                        "description": ["Timestamp when transaction occurred"],
                        "synonyms": ["date", "time", "timestamp", "transaction date", "order date"],
                        "exclude": False,
                        "get_example_values": True
                    }
                ]
            }
        ]
    },

    # INSTRUCTIONS: All instruction types
    "instructions": {

        # Text instructions (max 1 item)
        "text_instructions": [
            {
                "id": text_inst_id,
                "content": [
                    "This Genie Space analyzes bakehouse sales data. ",
                    "When calculating revenue, always use the totalPrice column and round to 2 decimals. ",
                    "For time-based analysis, use transactionTimestamp. ",
                    "Customer analysis requires joining transactions with customers table on customerID. ",
                    "Payment methods and products are categorical - use exact matches from the data. ",
                    "For date filtering, use DATE type parameters, not TIMESTAMP."
                ]
            }
        ],

        # Example question SQLs with parameters (SORTED BY ID)
        # NOTE: Each line should end with space or \n for proper formatting
        "example_question_sqls": [
            {
                "id": example_sql_ids[0],
                "question": ["Show top N customers by total spending"],
                "sql": [
                    "SELECT c.first_name, c.last_name, SUM(t.totalPrice) as total_spent ",
                    "FROM samples.bakehouse.sales_transactions t ",
                    "JOIN samples.bakehouse.sales_customers c ON t.customerID = c.customerID ",
                    "GROUP BY c.first_name, c.last_name ",
                    "ORDER BY total_spent DESC ",
                    "LIMIT :limit_n"
                ],
                "parameters": [
                    {
                        "name": "limit_n",
                        "type_hint": "INTEGER",
                        "description": ["Number of customers to return"]
                    }
                ],
                "usage_guidance": ["Use this pattern for any top-N customer analysis by spending"]
            },
            {
                "id": example_sql_ids[1],
                "question": ["Revenue by payment method between dates"],
                "sql": [
                    "SELECT paymentMethod, ",
                    "       ROUND(SUM(totalPrice), 2) as total_revenue, ",
                    "       COUNT(*) as transaction_count ",
                    "FROM samples.bakehouse.sales_transactions ",
                    "WHERE DATE(transactionTimestamp) BETWEEN :start_date AND :end_date ",
                    "GROUP BY paymentMethod ",
                    "ORDER BY total_revenue DESC"
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
                    }
                ],
                "usage_guidance": ["Use for payment method analysis with date filtering. Always use DATE type for date parameters."]
            },
            {
                "id": example_sql_ids[2],
                "question": ["Product popularity with revenue using CTE"],
                "sql": [
                    "WITH product_stats AS ( ",
                    "  SELECT product, ",
                    "         COUNT(*) as purchase_count, ",
                    "         ROUND(SUM(totalPrice), 2) as total_revenue, ",
                    "         ROUND(AVG(totalPrice), 2) as avg_price ",
                    "  FROM samples.bakehouse.sales_transactions ",
                    "  GROUP BY product ",
                    ") ",
                    "SELECT * FROM product_stats ",
                    "ORDER BY purchase_count DESC"
                ],
                "usage_guidance": ["Use CTEs for complex product analysis with multiple metrics"]
            }
        ],

        # Join specifications (SORTED BY ID)
        # IMPORTANT:
        # - Only use "comment" field, NOT "instructions"
        # - SQL must include relationship type marker: --rt=FROM_RELATIONSHIP_TYPE_*--
        # - Each SQL line should end with space for proper formatting
        "join_specs": [
            {
                "id": join_spec_ids[0],
                "left": {
                    "identifier": "samples.bakehouse.sales_transactions",
                    "alias": "t"
                },
                "right": {
                    "identifier": "samples.bakehouse.sales_customers",
                    "alias": "c"
                },
                "sql": [
                    "t.customerID = c.customerID ",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
                ],
                "comment": ["MANY-TO-ONE: Multiple transactions belong to one customer. Use for customer-level analysis."]
            },
            {
                "id": join_spec_ids[1],
                "left": {
                    "identifier": "samples.bakehouse.sales_customers",
                    "alias": "c"
                },
                "right": {
                    "identifier": "samples.bakehouse.sales_transactions",
                    "alias": "t"
                },
                "sql": [
                    "c.customerID = t.customerID ",
                    "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_MANY--"
                ],
                "comment": ["ONE-TO-MANY: Each customer can have multiple transactions. Use for analyzing customer purchase history."]
            },
            {
                "id": join_spec_ids[2],
                "left": {
                    "identifier": "samples.bakehouse.sales_transactions",
                    "alias": "t1"
                },
                "right": {
                    "identifier": "samples.bakehouse.sales_transactions",
                    "alias": "t2"
                },
                "sql": [
                    "t1.customerID = t2.customerID ",
                    "AND t1.transactionTimestamp < t2.transactionTimestamp ",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--"
                ],
                "comment": ["MANY-TO-MANY (SELF-JOIN): Link transactions by same customer for sequence analysis."]
            },
            {
                "id": join_spec_ids[3],
                "left": {
                    "identifier": "samples.bakehouse.sales_customers",
                    "alias": "c1"
                },
                "right": {
                    "identifier": "samples.bakehouse.sales_customers",
                    "alias": "c2"
                },
                "sql": [
                    "c1.state = c2.state ",
                    "AND c1.customerID != c2.customerID ",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--"
                ],
                "comment": ["MANY-TO-MANY: Link customers in the same state for regional analysis."]
            },
            {
                "id": join_spec_ids[4],
                "left": {
                    "identifier": "samples.bakehouse.sales_transactions",
                    "alias": "t"
                },
                "right": {
                    "identifier": "samples.bakehouse.sales_customers",
                    "alias": "c"
                },
                "sql": [
                    "t.customerID = c.customerID ",
                    "AND DATE(t.transactionTimestamp) >= '2020-01-01' ",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
                ],
                "comment": ["MANY-TO-ONE with date filter: Recent transactions to customers."]
            }
        ],

        # SQL Snippets (ALL SORTED BY ID)
        # IMPORTANT: Include table name in SQL for context
        "sql_snippets": {
            "filters": [
                {
                    "id": filter_ids[0],
                    "sql": ["samples.bakehouse.sales_transactions.totalPrice > 10"],
                    "display_name": "High value transactions",
                    "synonyms": ["expensive", "high value", "premium", "large orders"]
                },
                {
                    "id": filter_ids[1],
                    "sql": ["samples.bakehouse.sales_transactions.paymentMethod = 'credit card'"],
                    "display_name": "Credit card payments",
                    "synonyms": ["credit", "card payments", "credit cards"]
                }
            ],
            "expressions": [
                {
                    "id": expr_ids[0],
                    "alias": "customer_full_name",
                    "sql": ["CONCAT(samples.bakehouse.sales_customers.first_name, ' ', samples.bakehouse.sales_customers.last_name)"],
                    "display_name": "Customer full name",
                    "synonyms": ["full name", "name", "customer name"]
                },
                {
                    "id": expr_ids[1],
                    "alias": "transaction_month",
                    "sql": ["DATE_TRUNC('month', samples.bakehouse.sales_transactions.transactionTimestamp)"],
                    "display_name": "Transaction month",
                    "synonyms": ["month", "monthly", "order month"]
                },
                {
                    "id": expr_ids[2],
                    "alias": "transaction_year",
                    "sql": ["YEAR(samples.bakehouse.sales_transactions.transactionTimestamp)"],
                    "display_name": "Transaction year",
                    "synonyms": ["year", "yearly", "order year"]
                }
            ],
            "measures": [
                {
                    "id": measure_ids[0],
                    "alias": "avg_transaction_value",
                    "sql": ["ROUND(AVG(samples.bakehouse.sales_transactions.totalPrice), 2)"],
                    "display_name": "Average transaction value",
                    "synonyms": ["average", "avg", "mean transaction", "average sale", "avg price"]
                },
                {
                    "id": measure_ids[1],
                    "alias": "total_revenue",
                    "sql": ["ROUND(SUM(samples.bakehouse.sales_transactions.totalPrice), 2)"],
                    "display_name": "Total revenue",
                    "synonyms": ["revenue", "sales", "total sales", "gross revenue", "total amount"]
                },
                {
                    "id": measure_ids[2],
                    "alias": "transaction_count",
                    "sql": ["COUNT(samples.bakehouse.sales_transactions.totalPrice)"],
                    "display_name": "Transaction count",
                    "synonyms": ["count", "number of transactions", "total transactions", "order count"]
                }
            ]
        }
    },

    # BENCHMARKS: Evaluation questions (SORTED BY ID)
    # NOTE: answer is an ARRAY of objects
    "benchmarks": {
        "questions": [
            {
                "id": benchmark_ids[0],
                "question": ["What is the total revenue?"],
                "answer": [
                    {
                        "format": "SQL",
                        "content": [
                            "SELECT ROUND(SUM(totalPrice), 2) as total_revenue ",
                            "FROM samples.bakehouse.sales_transactions"
                        ]
                    }
                ]
            },
            {
                "id": benchmark_ids[1],
                "question": ["Show top 5 products by sales count"],
                "answer": [
                    {
                        "format": "SQL",
                        "content": [
                            "SELECT product, COUNT(*) as sales_count ",
                            "FROM samples.bakehouse.sales_transactions ",
                            "GROUP BY product ",
                            "ORDER BY sales_count DESC ",
                            "LIMIT 5"
                        ]
                    }
                ]
            },
            {
                "id": benchmark_ids[2],
                "question": ["Which customers spent more than $100?"],
                "answer": [
                    {
                        "format": "SQL",
                        "content": [
                            "SELECT c.first_name, c.last_name, SUM(t.totalPrice) as total_spent ",
                            "FROM samples.bakehouse.sales_transactions t ",
                            "JOIN samples.bakehouse.sales_customers c ON t.customerID = c.customerID ",
                            "GROUP BY c.first_name, c.last_name ",
                            "HAVING SUM(t.totalPrice) > 100 ",
                            "ORDER BY total_spent DESC"
                        ]
                    }
                ]
            }
        ]
    }
}

# Uncomment below to create the space
final_payload = {
     "title": "Bakehouse Sales Analytics",
     "description": "Sales analytics for bakehouse transactions and customers",
     "warehouse_id": warehouse_id,
     "serialized_space": json.dumps(final_working_config)
}
response = requests.post(url, headers=headers, json=final_payload)

print("Configuration Summary:")
print(f"  - Sample questions: {len(final_working_config['config']['sample_questions'])}")
print(f"  - Tables: {len(final_working_config['data_sources']['tables'])}")
print(f"  - Column configs: {sum(len(t.get('column_configs', [])) for t in final_working_config['data_sources']['tables'])}")
print(f"  - Text instructions: {len(final_working_config['instructions']['text_instructions'])}")
print(f"  - Example question SQLs: {len(final_working_config['instructions']['example_question_sqls'])}")
print(f"  - Join specs: {len(final_working_config['instructions']['join_specs'])}")
print(f"  - SQL filters: {len(final_working_config['instructions']['sql_snippets']['filters'])}")
print(f"  - SQL expressions: {len(final_working_config['instructions']['sql_snippets']['expressions'])}")
print(f"  - SQL measures: {len(final_working_config['instructions']['sql_snippets']['measures'])}")
print(f"  - Benchmark questions: {len(final_working_config['benchmarks']['questions'])}")

print("\nKey Format Rules:")
print("  1. Join specs: use 'comment' NOT 'instructions'")
print("  2. Join SQL: must include --rt=FROM_RELATIONSHIP_TYPE_*-- marker")
print("  3. SQL lines: end with space for proper formatting")
print("  4. SQL snippets: include full table name (catalog.schema.table.column)")
print("  5. Benchmarks answer: must be an ARRAY of objects")
print("  6. All arrays with id: must be sorted by id")
print("  7. Tables: sorted by identifier")
print("  8. Column configs: sorted by column_name")
