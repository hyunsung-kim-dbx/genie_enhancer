#!/usr/bin/env python3
"""
Genie Lamp Agent - Unified CLI for Databricks Genie Space Creation

This is the main entry point for creating and managing Databricks Genie spaces.

Usage:
    # Full pipeline (recommended)
    python genie.py create --requirements data/demo_requirements.md
    
    # Individual steps
    python genie.py generate --requirements data/demo_requirements.md
    python genie.py validate
    python genie.py deploy
"""

import argparse
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from genie.pipeline import generate_config, validate_config, deploy_space, parse_documents


def update_config_catalog_schema_table(
    config_path: str,
    old_catalog: str,
    old_schema: str,
    old_table: str,
    new_catalog: str,
    new_schema: str,
    new_table: str
):
    """
    Update catalog, schema, and table name in configuration file.

    Args:
        config_path: Path to the configuration JSON file
        old_catalog: Old catalog name
        old_schema: Old schema name
        old_table: Old table name
        new_catalog: New catalog name
        new_schema: New schema name
        new_table: New table name

    Returns:
        Dictionary with counts of updated items
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Get the genie_space_config
    if "genie_space_config" in config:
        genie_config = config["genie_space_config"]
    else:
        genie_config = config

    # Build old and new full table identifiers
    old_full_table = f"{old_catalog}.{old_schema}.{old_table}"
    new_full_table = f"{new_catalog}.{new_schema}.{new_table}"

    # Update tables
    updated_count = 0
    for table_def in genie_config.get("tables", []):
        if (table_def.get("catalog_name") == old_catalog and
            table_def.get("schema_name") == old_schema and
            table_def.get("table_name") == old_table):
            table_def["catalog_name"] = new_catalog
            table_def["schema_name"] = new_schema
            table_def["table_name"] = new_table
            updated_count += 1

    # Update SQL snippets - replace full table references
    sql_expr_count = 0
    sql_snippets = genie_config.get("sql_snippets", {})
    
    # Update filters
    for filt in sql_snippets.get("filters", []):
        if "sql" in filt and old_full_table in filt["sql"]:
            filt["sql"] = filt["sql"].replace(old_full_table, new_full_table)
            sql_expr_count += 1
    
    # Update expressions
    for expr in sql_snippets.get("expressions", []):
        if "sql" in expr and old_full_table in expr["sql"]:
            expr["sql"] = expr["sql"].replace(old_full_table, new_full_table)
            sql_expr_count += 1
    
    # Update measures
    for measure in sql_snippets.get("measures", []):
        if "sql" in measure and old_full_table in measure["sql"]:
            measure["sql"] = measure["sql"].replace(old_full_table, new_full_table)
            sql_expr_count += 1

    # Update example queries - replace full table references
    example_query_count = 0
    for query in genie_config.get("example_sql_queries", []):
        if "sql_query" in query and old_full_table in query["sql_query"]:
            query["sql_query"] = query["sql_query"].replace(old_full_table, new_full_table)
            example_query_count += 1

    # Update benchmark questions
    benchmark_count = 0
    for benchmark in genie_config.get("benchmark_questions", []):
        updated_this_benchmark = False

        # Update expected_sql field (may be null for FAQ items)
        if "expected_sql" in benchmark and benchmark["expected_sql"] and old_full_table in benchmark["expected_sql"]:
            benchmark["expected_sql"] = benchmark["expected_sql"].replace(old_full_table, new_full_table)
            updated_this_benchmark = True

        # Update table field (contains backtick-quoted table names)
        if "table" in benchmark and benchmark["table"]:
            old_table_ref = f"`{old_full_table}`"
            new_table_ref = f"`{new_full_table}`"
            if old_table_ref in benchmark["table"]:
                benchmark["table"] = benchmark["table"].replace(old_table_ref, new_table_ref)
                updated_this_benchmark = True

        if updated_this_benchmark:
            benchmark_count += 1

    # Update instructions - replace full table references
    instruction_count = 0
    for instruction in genie_config.get("instructions", []):
        if "content" in instruction and old_full_table in instruction["content"]:
            instruction["content"] = instruction["content"].replace(old_full_table, new_full_table)
            instruction_count += 1

    # Update joins if they reference this table
    join_count = 0
    for join in genie_config.get("joins", []):
        updated_this_join = False

        if join.get("left_table") == old_full_table:
            join["left_table"] = new_full_table
            join["left_alias"] = new_table
            updated_this_join = True

        if join.get("right_table") == old_full_table:
            join["right_table"] = new_full_table
            join["right_alias"] = new_table
            updated_this_join = True

        # Update join condition
        if "join_condition" in join and old_full_table in join["join_condition"]:
            join["join_condition"] = join["join_condition"].replace(old_full_table, new_full_table)
            updated_this_join = True

        # Also replace old table alias references in join condition
        if "join_condition" in join:
            old_alias_pattern = f"{old_table}."
            new_alias_pattern = f"{new_table}."
            if old_alias_pattern in join["join_condition"]:
                join["join_condition"] = join["join_condition"].replace(old_alias_pattern, new_alias_pattern)
                updated_this_join = True

        if updated_this_join:
            join_count += 1

    # Update join_specifications if they exist (alternative format)
    join_spec_count = 0
    for join_spec in genie_config.get("join_specifications", []):
        updated_this_spec = False

        if join_spec.get("left_table") == old_full_table:
            join_spec["left_table"] = new_full_table
            updated_this_spec = True

        if join_spec.get("right_table") == old_full_table:
            join_spec["right_table"] = new_full_table
            updated_this_spec = True

        # Update join condition
        if "join_condition" in join_spec and old_full_table in join_spec["join_condition"]:
            join_spec["join_condition"] = join_spec["join_condition"].replace(old_full_table, new_full_table)
            updated_this_spec = True

        # Also replace table aliases in join condition
        if "join_condition" in join_spec:
            old_alias_pattern = f"{old_table}."
            new_alias_pattern = f"{new_table}."
            if old_alias_pattern in join_spec["join_condition"]:
                join_spec["join_condition"] = join_spec["join_condition"].replace(old_alias_pattern, new_alias_pattern)
                updated_this_spec = True

        if updated_this_spec:
            join_spec_count += 1

    # Save back to file
    if "genie_space_config" in config:
        config["genie_space_config"] = genie_config
    else:
        config = genie_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return {
        'tables': updated_count,
        'sql_expressions': sql_expr_count,
        'example_queries': example_query_count,
        'benchmark_questions': benchmark_count,
        'instructions': instruction_count,
        'joins': join_count,
        'join_specifications': join_spec_count
    }


def update_config_catalog_schema(config_path: str, old_catalog: str, old_schema: str, new_catalog: str, new_schema: str):
    """
    Update catalog and schema in configuration file (legacy function, kept for backwards compatibility).
    This function updates ALL tables with matching catalog.schema.

    For individual table updates, use update_config_catalog_schema_table instead.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Get the genie_space_config
    if "genie_space_config" in config:
        genie_config = config["genie_space_config"]
    else:
        genie_config = config

    # Update tables
    updated_count = 0
    for table_def in genie_config.get("tables", []):
        if table_def.get("catalog_name") == old_catalog and table_def.get("schema_name") == old_schema:
            table_def["catalog_name"] = new_catalog
            table_def["schema_name"] = new_schema
            updated_count += 1

    # Update SQL snippets
    sql_expr_count = 0
    old_prefix = f"{old_catalog}.{old_schema}."
    new_prefix = f"{new_catalog}.{new_schema}."
    
    sql_snippets = genie_config.get("sql_snippets", {})
    
    # Update filters
    for filt in sql_snippets.get("filters", []):
        if "sql" in filt and old_prefix in filt["sql"]:
            filt["sql"] = filt["sql"].replace(old_prefix, new_prefix)
            sql_expr_count += 1
    
    # Update expressions
    for expr in sql_snippets.get("expressions", []):
        if "sql" in expr and old_prefix in expr["sql"]:
            expr["sql"] = expr["sql"].replace(old_prefix, new_prefix)
            sql_expr_count += 1
    
    # Update measures
    for measure in sql_snippets.get("measures", []):
        if "sql" in measure and old_prefix in measure["sql"]:
            measure["sql"] = measure["sql"].replace(old_prefix, new_prefix)
            sql_expr_count += 1

    # Update example queries
    example_query_count = 0
    for query in genie_config.get("example_sql_queries", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        if "sql_query" in query and old_prefix in query["sql_query"]:
            query["sql_query"] = query["sql_query"].replace(old_prefix, new_prefix)
            example_query_count += 1

    # Update benchmark questions
    benchmark_count = 0
    for benchmark in genie_config.get("benchmark_questions", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        updated_this_benchmark = False

        # Update expected_sql field (may be null for FAQ items)
        if "expected_sql" in benchmark and benchmark["expected_sql"] and old_prefix in benchmark["expected_sql"]:
            benchmark["expected_sql"] = benchmark["expected_sql"].replace(old_prefix, new_prefix)
            updated_this_benchmark = True

        # Update table field (contains backtick-quoted table names)
        if "table" in benchmark and benchmark["table"]:
            old_table_ref = f"`{old_catalog}.{old_schema}."
            new_table_ref = f"`{new_catalog}.{new_schema}."
            if old_table_ref in benchmark["table"]:
                benchmark["table"] = benchmark["table"].replace(old_table_ref, new_table_ref)
                updated_this_benchmark = True

        if updated_this_benchmark:
            benchmark_count += 1

    # Update instructions
    instruction_count = 0
    for instruction in genie_config.get("instructions", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        if "content" in instruction and old_prefix in instruction["content"]:
            instruction["content"] = instruction["content"].replace(old_prefix, new_prefix)
            instruction_count += 1

    # Update joins
    join_count = 0
    for join in genie_config.get("joins", []):
        updated_this_join = False
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."

        if "left_table" in join and old_prefix in join["left_table"]:
            join["left_table"] = join["left_table"].replace(old_prefix, new_prefix)
            updated_this_join = True

        if "right_table" in join and old_prefix in join["right_table"]:
            join["right_table"] = join["right_table"].replace(old_prefix, new_prefix)
            updated_this_join = True

        if "join_condition" in join and old_prefix in join["join_condition"]:
            join["join_condition"] = join["join_condition"].replace(old_prefix, new_prefix)
            updated_this_join = True

        if updated_this_join:
            join_count += 1

    # Update join_specifications
    join_spec_count = 0
    for join_spec in genie_config.get("join_specifications", []):
        updated_this_spec = False
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."

        if "left_table" in join_spec and old_prefix in join_spec["left_table"]:
            join_spec["left_table"] = join_spec["left_table"].replace(old_prefix, new_prefix)
            updated_this_spec = True

        if "right_table" in join_spec and old_prefix in join_spec["right_table"]:
            join_spec["right_table"] = join_spec["right_table"].replace(old_prefix, new_prefix)
            updated_this_spec = True

        if "join_condition" in join_spec and old_prefix in join_spec["join_condition"]:
            join_spec["join_condition"] = join_spec["join_condition"].replace(old_prefix, new_prefix)
            updated_this_spec = True

        if updated_this_spec:
            join_spec_count += 1

    # Save back to file
    if "genie_space_config" in config:
        config["genie_space_config"] = genie_config
    else:
        config = genie_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return {
        'tables': updated_count,
        'sql_expressions': sql_expr_count,
        'example_queries': example_query_count,
        'benchmark_questions': benchmark_count,
        'instructions': instruction_count,
        'joins': join_count,
        'join_specifications': join_spec_count
    }


def remove_table_from_config(config_path: str, catalog: str, schema: str, table: str):
    """
    Remove a table and all its references from the configuration.

    Args:
        config_path: Path to the configuration JSON file
        catalog: Catalog name
        schema: Schema name
        table: Table name

    Returns:
        Dictionary with counts of removed items
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Get the genie_space_config
    if "genie_space_config" in config:
        genie_config = config["genie_space_config"]
    else:
        genie_config = config

    full_table = f"{catalog}.{schema}.{table}"

    # Remove from tables array
    tables_before = len(genie_config.get("tables", []))
    genie_config["tables"] = [
        t for t in genie_config.get("tables", [])
        if not (t.get("catalog_name") == catalog and
                t.get("schema_name") == schema and
                t.get("table_name") == table)
    ]
    tables_removed = tables_before - len(genie_config.get("tables", []))

    # Remove SQL expressions that reference this table
    sql_snippets = genie_config.get("sql_snippets", {})

    filters_before = len(sql_snippets.get("filters", []))
    sql_snippets["filters"] = [
        f for f in sql_snippets.get("filters", [])
        if full_table not in f.get("sql", "")
    ]
    filters_removed = filters_before - len(sql_snippets.get("filters", []))

    expressions_before = len(sql_snippets.get("expressions", []))
    sql_snippets["expressions"] = [
        e for e in sql_snippets.get("expressions", [])
        if full_table not in e.get("sql", "")
    ]
    expressions_removed = expressions_before - len(sql_snippets.get("expressions", []))

    measures_before = len(sql_snippets.get("measures", []))
    sql_snippets["measures"] = [
        m for m in sql_snippets.get("measures", [])
        if full_table not in m.get("sql", "")
    ]
    measures_removed = measures_before - len(sql_snippets.get("measures", []))

    # Remove example queries that reference this table
    queries_before = len(genie_config.get("example_sql_queries", []))
    genie_config["example_sql_queries"] = [
        q for q in genie_config.get("example_sql_queries", [])
        if full_table not in q.get("sql_query", "")
    ]
    queries_removed = queries_before - len(genie_config.get("example_sql_queries", []))

    # Remove benchmark questions that reference this table
    benchmarks_before = len(genie_config.get("benchmark_questions", []))
    genie_config["benchmark_questions"] = [
        b for b in genie_config.get("benchmark_questions", [])
        if full_table not in b.get("expected_sql", "") and
           f"`{full_table}`" not in b.get("table", "")
    ]
    benchmarks_removed = benchmarks_before - len(genie_config.get("benchmark_questions", []))

    # Remove instructions that reference this table
    instructions_before = len(genie_config.get("instructions", []))
    genie_config["instructions"] = [
        i for i in genie_config.get("instructions", [])
        if full_table not in i.get("content", "")
    ]
    instructions_removed = instructions_before - len(genie_config.get("instructions", []))

    # Remove joins that reference this table
    joins_before = len(genie_config.get("joins", []))
    genie_config["joins"] = [
        j for j in genie_config.get("joins", [])
        if j.get("left_table") != full_table and j.get("right_table") != full_table
    ]
    joins_removed = joins_before - len(genie_config.get("joins", []))

    # Remove join_specifications that reference this table
    join_specs_before = len(genie_config.get("join_specifications", []))
    genie_config["join_specifications"] = [
        js for js in genie_config.get("join_specifications", [])
        if js.get("left_table") != full_table and js.get("right_table") != full_table
    ]
    join_specs_removed = join_specs_before - len(genie_config.get("join_specifications", []))

    # Save back to file
    if "genie_space_config" in config:
        config["genie_space_config"] = genie_config
    else:
        config = genie_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return {
        'tables': tables_removed,
        'sql_filters': filters_removed,
        'sql_expressions': expressions_removed,
        'sql_measures': measures_removed,
        'example_queries': queries_removed,
        'benchmark_questions': benchmarks_removed,
        'instructions': instructions_removed,
        'joins': joins_removed,
        'join_specifications': join_specs_removed
    }


def prompt_catalog_schema_replacement(report, config_path: str) -> bool:
    """
    Prompt user for catalog/schema/table replacement when tables are not found.

    Supports two modes:
    1. Bulk replacement: Replace catalog.schema for all tables at once
    2. Individual replacement: Replace catalog.schema.table one by one

    Returns:
        True if configuration was updated, False otherwise
    """
    # Find table_not_found errors and table_reference_invalid warnings
    table_issues = [
        issue for issue in report.issues
        if (issue.severity == "error" and issue.type == "table_not_found") or
           (issue.severity == "warning" and issue.type == "table_reference_invalid")
    ]

    if not table_issues:
        return False

    # Extract failed tables with full details
    failed_tables = []
    for issue in table_issues:
        if issue.table:
            parts = issue.table.split('.')
            if len(parts) == 3:
                catalog, schema, table = parts
                failed_tables.append({
                    'full_name': issue.table,
                    'catalog': catalog,
                    'schema': schema,
                    'table': table
                })

    if not failed_tables:
        return False

    print()
    print("=" * 80)
    print("⚠️  TABLE VALIDATION ISSUES FOUND")
    print("=" * 80)
    print()
    print(f"Found {len(failed_tables)} table(s) with issues:")
    print()

    for i, table_info in enumerate(failed_tables, 1):
        print(f"  {i}. {table_info['full_name']}")

    print()
    print("Choose replacement mode:")
    print("  1. Bulk replacement (replace catalog.schema for all tables)")
    print("  2. Individual replacement (replace catalog.schema.table one by one)")
    print("  3. Cancel")

    mode = input("Enter choice [1/2/3]: ").strip()

    if mode == "3" or not mode:
        return False

    updated = False

    if mode == "1":
        # Bulk replacement mode - group by catalog.schema
        failed_schemas = {}
        for table_info in failed_tables:
            key = f"{table_info['catalog']}.{table_info['schema']}"
            if key not in failed_schemas:
                failed_schemas[key] = []
            failed_schemas[key].append(table_info['table'])

        for schema_key, tables in failed_schemas.items():
            old_catalog, old_schema = schema_key.split('.')

            print()
            print(f"Replacing: {schema_key}")
            print(f"  Affects {len(tables)} table(s): {', '.join(tables[:3])}" + ("..." if len(tables) > 3 else ""))
            new_catalog = input(f"  New catalog (current: {old_catalog}, press Enter to keep): ").strip()
            new_schema = input(f"  New schema (current: {old_schema}, press Enter to keep): ").strip()

            # Use existing values if user pressed Enter
            if not new_catalog:
                new_catalog = old_catalog
            if not new_schema:
                new_schema = old_schema

            # Only update if something changed
            if new_catalog != old_catalog or new_schema != old_schema:
                print(f"  Updating {old_catalog}.{old_schema} → {new_catalog}.{new_schema}...")
                counts = update_config_catalog_schema(
                    config_path,
                    old_catalog,
                    old_schema,
                    new_catalog,
                    new_schema
                )
                print(f"  ✓ Updated:")
                print(f"     - {counts['tables']} table(s)")
                print(f"     - {counts['sql_expressions']} SQL expression(s)")
                print(f"     - {counts['example_queries']} example query/queries")
                print(f"     - {counts['benchmark_questions']} benchmark question(s)")
                print(f"     - {counts['instructions']} instruction(s)")
                print(f"     - {counts['joins']} join(s)")
                print(f"     - {counts['join_specifications']} join specification(s)")
                updated = True
            else:
                print(f"  Skipping {schema_key} (no changes)")

    elif mode == "2":
        # Individual table replacement mode
        print()
        print("Individual table replacement mode:")
        print("  Press Enter to keep current value")
        print("  Type new value to replace")
        print()

        for i, table_info in enumerate(failed_tables, 1):
            print(f"Table {i}/{len(failed_tables)}: {table_info['full_name']}")

            new_catalog = input(f"  New catalog (current: {table_info['catalog']}): ").strip()
            new_schema = input(f"  New schema (current: {table_info['schema']}): ").strip()
            new_table = input(f"  New table (current: {table_info['table']}): ").strip()

            # Use existing values if user pressed Enter
            if not new_catalog:
                new_catalog = table_info['catalog']
            if not new_schema:
                new_schema = table_info['schema']
            if not new_table:
                new_table = table_info['table']

            # Only update if something changed
            if (new_catalog != table_info['catalog'] or
                new_schema != table_info['schema'] or
                new_table != table_info['table']):

                print(f"  Updating {table_info['full_name']} → {new_catalog}.{new_schema}.{new_table}...")
                counts = update_config_catalog_schema_table(
                    config_path,
                    table_info['catalog'],
                    table_info['schema'],
                    table_info['table'],
                    new_catalog,
                    new_schema,
                    new_table
                )
                print(f"  ✓ Updated:")
                print(f"     - {counts['tables']} table(s)")
                print(f"     - {counts['sql_expressions']} SQL expression(s)")
                print(f"     - {counts['example_queries']} example query/queries")
                print(f"     - {counts['benchmark_questions']} benchmark question(s)")
                print(f"     - {counts['instructions']} instruction(s)")
                print(f"     - {counts['joins']} join(s)")
                print(f"     - {counts['join_specifications']} join specification(s)")
                updated = True
            else:
                print(f"  Skipping (no changes)")

            print()

    else:
        print("Invalid choice. Cancelling.")
        return False

    return updated


def cmd_create(args):
    """Run full pipeline: generate → validate → deploy."""
    print("=" * 80)
    print("🧞 Genie Lamp Agent - Full Pipeline")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Generate configuration
        print("📝 Step 1/3: Generating configuration...")
        print("-" * 80)
        
        config_data = generate_config(
            requirements_path=args.requirements,
            output_path=args.output,
            model=args.model,
            endpoint=args.endpoint,
            context_doc=args.context_doc,
            output_doc=args.output_doc,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            benchmark_batch_size=args.benchmark_batch_size,
            skip_benchmark_sql=args.skip_benchmark_sql,
            verbose=True
        )
        
        print()
        print("✓ Configuration generated successfully!")
        print()
        
        # Step 2: Validate tables (unless skipped)
        if not args.skip_validation:
            print("✓ Step 2/3: Validating tables and columns...")
            print("-" * 80)
            
            max_validation_attempts = 3
            validation_attempt = 0
            
            while validation_attempt < max_validation_attempts:
                validation_attempt += 1
                
                report = validate_config(
                    config_path=args.output,
                    databricks_host=args.databricks_host,
                    databricks_token=args.databricks_token,
                    verbose=True
                )
                
                if report.has_errors():
                    print()
                    print("❌ Validation failed with errors!")
                    print()
                    print("Validation Report:")
                    print(report.summary())
                    
                    # Prompt for catalog/schema replacement
                    if not args.yes and validation_attempt < max_validation_attempts:
                        updated = prompt_catalog_schema_replacement(report, args.output)
                        
                        if updated:
                            print()
                            print("=" * 80)
                            print("🔄 Configuration updated. Re-validating...")
                            print("=" * 80)
                            print()
                            continue
                    
                    print()
                    print("Please fix the errors and try again.")
                    return 1
                
                if report.has_warnings():
                    print()
                    print("⚠️  Validation completed with warnings.")
                    print()

                    # Show warning details
                    warning_issues = [i for i in report.issues if i.severity == 'warning']
                    if warning_issues:
                        print("Warnings found:")
                        for issue in warning_issues:
                            print(f"  • {issue.message}")
                            if issue.table:
                                print(f"    Table: {issue.table}")
                            if issue.location:
                                print(f"    Location: {issue.location}")
                    print()

                    # Ask user if they want to fix the issues
                    if not args.yes and validation_attempt < max_validation_attempts:
                        print("Options:")
                        print("  1. Fix issues (replace invalid table references)")
                        print("  2. Continue anyway (warnings will be ignored)")
                        print("  3. Cancel")
                        print()
                        choice = input("Enter choice [1/2/3]: ").strip()

                        if choice == "1":
                            # Try to fix the issues
                            updated = prompt_catalog_schema_replacement(report, args.output)

                            if updated:
                                print()
                                print("=" * 80)
                                print("🔄 Configuration updated. Re-validating...")
                                print("=" * 80)
                                print()
                                continue
                            else:
                                print("No changes made.")
                        elif choice == "3":
                            print("Deployment cancelled.")
                            return 0
                        # choice == "2" or any other input continues with deployment
                
                # Validation passed
                break
            
            print()
            print("✓ Validation passed!")
            print()
        else:
            print("⚠️  Step 2/3: Validation skipped (--skip-validation)")
            print()
        
        # Step 3: Deploy space
        print("🚀 Step 3/3: Deploying Genie space...")
        print("-" * 80)
        
        result = deploy_space(
            config_path=args.output,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            parent_path=args.parent_path,
            verbose=True
        )
        
        # Save result
        if args.result_output:
            result_path = Path(args.result_output)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   Result saved to: {args.result_output}")
        
        print()
        print("=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print()
        print(f"Your Genie space is ready!")
        print()
        print(f"Space ID:  {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return 130
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        
        if args.verbose:
            import traceback
            print("Full traceback:")
            traceback.print_exc()
        
        return 1


def cmd_generate(args):
    """Generate configuration only."""
    print("=" * 80)
    print("📝 Genie Configuration Generator")
    print("=" * 80)
    print()
    
    try:
        config_data = generate_config(
            requirements_path=args.requirements,
            output_path=args.output,
            model=args.model,
            endpoint=args.endpoint,
            context_doc=args.context_doc,
            output_doc=args.output_doc,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            benchmark_batch_size=args.benchmark_batch_size,
            skip_benchmark_sql=args.skip_benchmark_sql,
            verbose=True
        )
        
        print()
        print("=" * 80)
        print("✓ Configuration Summary")
        print("=" * 80)
        
        config = config_data.get("genie_space_config", config_data)
        print(f"\nSpace Name: {config['space_name']}")
        print(f"Description: {config['description'][:100]}...")
        print(f"\nComponents:")
        print(f"  Tables: {len(config['tables'])}")
        print(f"  Instructions: {len(config['instructions'])}")
        print(f"  Example SQL Queries: {len(config['example_sql_queries'])}")
        
        # Count SQL snippets
        sql_snippets = config.get('sql_snippets', {})
        num_sql_snippets = (
            len(sql_snippets.get('filters', [])) +
            len(sql_snippets.get('expressions', [])) +
            len(sql_snippets.get('measures', []))
        )
        print(f"  SQL Snippets: {num_sql_snippets} (filters, expressions, measures)")
        
        print(f"  Benchmark Questions: {len(config['benchmark_questions'])}")
        print()
        print(f"Configuration saved to: {args.output}")
        print()
        print("Next steps:")
        print(f"  1. Validate: python genie.py validate")
        print(f"  2. Deploy:   python genie.py deploy")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_validate(args):
    """Validate configuration only."""
    print("=" * 80)
    print("✓ Genie Configuration Validator")
    print("=" * 80)
    print()
    
    try:
        max_validation_attempts = 3
        validation_attempt = 0
        
        while validation_attempt < max_validation_attempts:
            validation_attempt += 1
            
            report = validate_config(
                config_path=args.config,
                databricks_host=args.databricks_host,
                databricks_token=args.databricks_token,
                verbose=True
            )
            
            print()
            print("=" * 80)
            print("Validation Report")
            print("=" * 80)
            print()
            print(report.summary())
            print()
            
            if report.has_errors():
                # Prompt for catalog/schema replacement
                if validation_attempt < max_validation_attempts:
                    updated = prompt_catalog_schema_replacement(report, args.config)

                    if updated:
                        print()
                        print("=" * 80)
                        print("🔄 Configuration updated. Re-validating...")
                        print("=" * 80)
                        print()
                        continue

                print("Next steps:")
                print("  1. Fix the errors in your configuration")
                print("  2. Run validation again")
                return 1

            if report.has_warnings():
                print()
                print("⚠️  Validation completed with warnings.")
                print()

                # Show warning details
                warning_issues = [i for i in report.issues if i.severity == 'warning']
                if warning_issues:
                    print("Warnings found:")
                    for issue in warning_issues:
                        print(f"  • {issue.message}")
                        if issue.table:
                            print(f"    Table: {issue.table}")
                        if issue.location:
                            print(f"    Location: {issue.location}")
                print()

                # Ask user if they want to fix the issues
                if validation_attempt < max_validation_attempts:
                    print("Options:")
                    print("  1. Fix issues (replace invalid table references)")
                    print("  2. Continue anyway (warnings will be ignored)")
                    print("  3. Cancel")
                    print()
                    choice = input("Enter choice [1/2/3]: ").strip()

                    if choice == "1":
                        # Try to fix the issues
                        updated = prompt_catalog_schema_replacement(report, args.config)

                        if updated:
                            print()
                            print("=" * 80)
                            print("🔄 Configuration updated. Re-validating...")
                            print("=" * 80)
                            print()
                            continue
                        else:
                            print("No changes made.")
                    elif choice == "3":
                        print("Validation cancelled.")
                        return 1
                    # choice == "2" or any other input continues

            # Validation passed (or user chose to continue with warnings)
            print("Next steps:")
            print(f"  Deploy: python genie.py deploy --config {args.config}")
            return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_deploy(args):
    """Deploy existing configuration."""
    print("=" * 80)
    print("🚀 Genie Space Deployer")
    print("=" * 80)
    print()
    
    try:
        result = deploy_space(
            config_path=args.config,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            parent_path=args.parent_path,
            verbose=True
        )
        
        # Save result
        if args.result_output:
            result_path = Path(args.result_output)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   Result saved to: {args.result_output}")
        
        print()
        print("=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print()
        print(f"Space ID:  {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_parse(args):
    """Parse documents into structured requirements format."""
    print("=" * 80)
    print("📄 Document Parser")
    print("=" * 80)
    print()
    
    try:
        result = parse_documents(
            input_dir=args.input_dir,
            output_path=args.output,
            llm_model=args.llm_model,
            vision_model=args.vision_model,
            use_llm=not args.no_llm,
            domain=args.domain,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            verbose=True,
            max_concurrent_pdfs=args.max_concurrent,
            force=args.force,
            cache_file=args.cache_file,
            no_cache=args.no_cache
        )
        
        print()
        print("=" * 80)
        if result.get('cache_used'):
            print("✓ Parsing Summary (from cache)")
        else:
            print("✓ Parsing Summary")
        print("=" * 80)
        print()
        print(f"Output file: {result['output_path']}")
        print()
        
        # Only show detailed stats if not using cache (cache doesn't track these)
        if not result.get('cache_used'):
            print(f"Extracted content:")
            print(f"  Questions: {result['questions_count']}")
            print(f"  Tables: {result['tables_count']}")
            print(f"  SQL Queries: {result['queries_count']}")
            print(f"  Sections: {result['sections_count']}")
            print()
        
        print(f"LLM enrichment: {'Yes' if result['used_llm'] else 'No'}")
        print(f"Domain: {result['domain']}")
        
        if result.get('cache_used'):
            print(f"Cache status: Used (cached at {result.get('cached_timestamp', 'unknown')})")
        elif not args.no_cache:
            print(f"Cache status: Updated ({args.cache_file})")
        else:
            print(f"Cache status: Disabled")
        
        print()
        print("Next steps:")
        print(f"  Generate config: python genie.py generate --requirements {result['output_path']}")
        print(f"  Full pipeline:   python genie.py create --requirements {result['output_path']}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="genie",
        description="Genie Lamp Agent - Automated Databricks Genie Space Creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline (recommended)
  %(prog)s create --requirements data/demo_requirements.md
  
  # With custom model
  %(prog)s create --requirements data/demo.md --model llama-3-1-70b
  
  # Step by step
  %(prog)s generate --requirements data/demo.md
  %(prog)s validate
  %(prog)s deploy

Environment Variables:
  DATABRICKS_HOST    Databricks workspace URL (required)
  DATABRICKS_TOKEN   Databricks personal access token (required)
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # =========================================================================
    # CREATE command (full pipeline)
    # =========================================================================
    create_parser = subparsers.add_parser(
        "create",
        help="Full pipeline: generate → validate → deploy",
        description="Generate configuration, validate tables, and deploy Genie space in one command"
    )
    
    # Required arguments
    create_parser.add_argument(
        "--requirements",
        type=str,
        required=True,
        help="Path to requirements document"
    )
    
    # Output paths
    create_parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Output path for generated configuration (default: output/genie_space_config.json)"
    )
    create_parser.add_argument(
        "--result-output",
        type=str,
        default="output/genie_space_result.json",
        help="Output path for deployment result (default: output/genie_space_result.json)"
    )
    
    # LLM configuration
    create_parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model name (default: databricks-gpt-5-2)"
    )
    create_parser.add_argument(
        "--endpoint",
        type=str,
        help="Custom serving endpoint (alternative to --model)"
    )
    create_parser.add_argument(
        "--max-tokens",
        type=int,
        default=24000,
        help="Maximum tokens to generate (default: 24000)"
    )
    create_parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature 0.0-1.0 (default: 0.1)"
    )
    
    # Template paths
    create_parser.add_argument(
        "--context-doc",
        type=str,
        default="genie/prompt/templates/curate_effective_genie.md",
        help="Path to context document"
    )
    create_parser.add_argument(
        "--output-doc",
        type=str,
        default="genie/prompt/templates/genie_api.md",
        help="Path to output format document"
    )
    
    # Benchmark extraction
    create_parser.add_argument(
        "--skip-benchmark-sql",
        action="store_true",
        help="Skip benchmark SQL generation (for testing)"
    )
    create_parser.add_argument(
        "--benchmark-batch-size",
        type=int,
        default=10,
        help="Batch size for benchmark SQL generation (default: 10)"
    )

    # Validation options
    create_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip table validation (faster but risky)"
    )
    create_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    # Deployment options
    create_parser.add_argument(
        "--parent-path",
        type=str,
        help="Parent workspace path for the space"
    )
    
    # Databricks credentials
    create_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL (overrides DATABRICKS_HOST)"
    )
    create_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token (overrides DATABRICKS_TOKEN)"
    )
    
    create_parser.set_defaults(func=cmd_create)
    
    # =========================================================================
    # GENERATE command
    # =========================================================================
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate configuration only",
        description="Generate Genie space configuration from requirements"
    )
    
    generate_parser.add_argument(
        "--requirements",
        type=str,
        required=True,
        help="Path to requirements document"
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Output path (default: output/genie_space_config.json)"
    )
    generate_parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model name (default: databricks-gpt-5-2)"
    )
    generate_parser.add_argument(
        "--endpoint",
        type=str,
        help="Custom serving endpoint"
    )
    generate_parser.add_argument(
        "--max-tokens",
        type=int,
        default=24000,
        help="Maximum tokens (default: 24000)"
    )
    generate_parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature 0.0-1.0 (default: 0.1)"
    )
    generate_parser.add_argument(
        "--context-doc",
        type=str,
        default="genie/prompt/templates/curate_effective_genie.md",
        help="Context document path"
    )
    generate_parser.add_argument(
        "--output-doc",
        type=str,
        default="genie/prompt/templates/genie_api.md",
        help="Output format document path"
    )
    generate_parser.add_argument(
        "--skip-benchmark-sql",
        action="store_true",
        help="Skip benchmark SQL generation (for testing)"
    )
    generate_parser.add_argument(
        "--benchmark-batch-size",
        type=int,
        default=10,
        help="Batch size for benchmark SQL generation (default: 10)"
    )
    generate_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    generate_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )

    generate_parser.set_defaults(func=cmd_generate)
    
    # =========================================================================
    # VALIDATE command
    # =========================================================================
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration only",
        description="Validate tables and columns in configuration"
    )
    
    validate_parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Configuration file path (default: output/genie_space_config.json)"
    )
    validate_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    validate_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )
    
    validate_parser.set_defaults(func=cmd_validate)
    
    # =========================================================================
    # DEPLOY command
    # =========================================================================
    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Deploy existing configuration",
        description="Deploy Genie space from existing configuration"
    )
    
    deploy_parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Configuration file path (default: output/genie_space_config.json)"
    )
    deploy_parser.add_argument(
        "--result-output",
        type=str,
        default="output/genie_space_result.json",
        help="Result output path (default: output/genie_space_result.json)"
    )
    deploy_parser.add_argument(
        "--parent-path",
        type=str,
        help="Parent workspace path"
    )
    deploy_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    deploy_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )
    
    deploy_parser.set_defaults(func=cmd_deploy)
    
    # =========================================================================
    # PARSE command
    # =========================================================================
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse documents into structured requirements",
        description="Parse PDF and markdown files into structured requirements format"
    )
    
    parse_parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing PDF and markdown files"
    )
    parse_parser.add_argument(
        "--output",
        type=str,
        default="real_requirements/parsed/parsed_requirements.md",
        help="Output path for generated markdown (default: real_requirements/parsed/parsed_requirements.md)"
    )
    parse_parser.add_argument(
        "--llm-model",
        type=str,
        default=os.getenv("LLM_MODEL", "databricks-gpt-5-2"),
        help="Foundation model for text-based LLM enrichment (default: databricks-gpt-5-2)"
    )
    parse_parser.add_argument(
        "--vision-model",
        type=str,
        default=os.getenv("VISION_MODEL", "databricks-claude-sonnet-4"),
        help="Foundation model for image-based PDF parsing (default: databricks-claude-sonnet-4)"
    )
    parse_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM enrichment (faster but less intelligent)"
    )
    parse_parser.add_argument(
        "--domain",
        type=str,
        choices=["social_analytics", "kpi_analytics", "combined"],
        default="combined",
        help="Domain type (default: combined)"
    )
    parse_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL (required if using LLM)"
    )
    parse_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token (required if using LLM)"
    )
    parse_parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum number of PDFs to process concurrently (default: 3)"
    )
    parse_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-parsing even if cache is valid"
    )
    parse_parser.add_argument(
        "--cache-file",
        type=str,
        default=".parse_cache.json",
        help="Cache file location (default: .parse_cache.json)"
    )
    parse_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching entirely"
    )
    
    parse_parser.set_defaults(func=cmd_parse)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
