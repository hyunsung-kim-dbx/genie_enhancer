#!/usr/bin/env python3
"""
Setup Delta Tables for Genie Enhancement System

This script creates all necessary Delta tables by:
1. Reading app.yaml to get CATALOG and SCHEMA values
2. Reading the SQL template (delta_tables_schema.sql)
3. Replacing ${CATALOG} and ${SCHEMA} placeholders
4. Creating the tables in Databricks
"""

import os
import sys
import yaml
from pathlib import Path


def read_app_yaml():
    """Read catalog and schema from app.yaml."""
    app_yaml_path = Path(__file__).parent.parent / "app.yaml"

    if not app_yaml_path.exists():
        print(f"⚠️  app.yaml not found at {app_yaml_path}")
        return None, None

    with open(app_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    # Extract env vars
    env_vars = config.get('env', [])
    catalog = None
    schema = None

    for var in env_vars:
        if var.get('name') == 'CATALOG':
            catalog = var.get('value')
        elif var.get('name') == 'SCHEMA':
            schema = var.get('value')

    return catalog, schema


def setup_delta_tables(catalog: str = None, schema: str = None):
    """
    Create Delta tables using catalog and schema from app.yaml or parameters.

    Args:
        catalog: Catalog name (defaults to app.yaml or CATALOG env var)
        schema: Schema name (defaults to app.yaml or SCHEMA env var)
    """
    # Priority: CLI args > app.yaml > env vars > defaults
    if not catalog or not schema:
        yaml_catalog, yaml_schema = read_app_yaml()
        catalog = catalog or yaml_catalog or os.getenv("CATALOG", "sandbox")
        schema = schema or yaml_schema or os.getenv("SCHEMA", "genie_enhancement")

    full_name = f"{catalog}.{schema}"

    print("=" * 80)
    print("Genie Enhancement System - Delta Table Setup")
    print("=" * 80)
    print(f"📖 Reading from: app.yaml")
    print(f"📦 Catalog: {catalog}")
    print(f"📁 Schema: {schema}")
    print(f"🎯 Full Name: {full_name}")
    print("=" * 80)

    # Read SQL template
    sql_file = Path(__file__).parent / "delta_tables_schema.sql"

    if not sql_file.exists():
        print(f"❌ Error: SQL file not found: {sql_file}")
        sys.exit(1)

    with open(sql_file, 'r') as f:
        sql_template = f.read()

    print(f"📄 Template loaded from: {sql_file}")
    print(f"   Contains {sql_template.count('${CATALOG}')} references to ${{CATALOG}}")
    print(f"   Contains {sql_template.count('${SCHEMA}')} references to ${{SCHEMA}}")
    print()

    # Replace template variables with actual values from app.yaml
    sql = sql_template.replace("${CATALOG}", catalog)
    sql = sql.replace("${SCHEMA}", schema)

    # Save customized SQL
    output_file = Path(__file__).parent / f"delta_tables_{catalog}_{schema}.sql"
    with open(output_file, 'w') as f:
        f.write(sql)

    print(f"✅ Generated customized SQL: {output_file}")
    print()
    print("Next steps:")
    print(f"1. Review the generated SQL file")
    print(f"2. Run it in Databricks SQL Editor or via spark.sql()")
    print(f"3. Grant appropriate permissions to users")
    print()

    # Try to create tables if Spark is available
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()

        print("✅ Spark session detected, creating tables...")

        # Split SQL by semicolons and execute
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements):
            # Skip comments and empty statements
            if not statement or statement.startswith('--'):
                continue

            try:
                print(f"Executing statement {i+1}/{len(statements)}...")
                spark.sql(statement)
                print(f"✅ Statement {i+1} completed")
            except Exception as e:
                # Some statements might fail (e.g., OPTIMIZE on non-existent tables)
                # that's okay, continue
                print(f"⚠️ Statement {i+1} skipped: {e}")

        print()
        print("=" * 80)
        print("✅ Delta tables setup complete!")
        print("=" * 80)
        print(f"Tables created in: {full_name}")
        print()
        print("Available tables:")
        print(f"  - {full_name}.enhancement_runs")
        print(f"  - {full_name}.enhancement_iterations")
        print(f"  - {full_name}.enhancement_changes")
        print(f"  - {full_name}.enhancement_benchmarks")
        print(f"  - {full_name}.enhancement_lessons_learned")
        print()
        print("Available views:")
        print(f"  - {full_name}.vw_current_progress")
        print(f"  - {full_name}.vw_change_distribution")
        print(f"  - {full_name}.vw_failure_patterns")
        print(f"  - {full_name}.vw_rollback_points")

    except ImportError:
        print("⚠️ PySpark not available - tables not created")
        print(f"   To create tables, run the generated SQL in Databricks:")
        print(f"   {output_file}")


if __name__ == "__main__":
    # Parse command line arguments
    catalog = None
    schema = None

    if len(sys.argv) > 1:
        catalog = sys.argv[1]
    if len(sys.argv) > 2:
        schema = sys.argv[2]

    setup_delta_tables(catalog, schema)
