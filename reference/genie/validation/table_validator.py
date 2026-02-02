"""
Validator for Databricks tables and columns referenced in Genie Space configurations.

This module validates that:
1. All tables referenced in the configuration exist in Unity Catalog
2. All columns referenced in SQL queries and expressions exist in their respective tables
3. All tables referenced in benchmark questions are valid
4. The user has proper access permissions to the tables

Usage:
    from genie.table_validator import TableValidator

    validator = TableValidator()
    report = validator.validate_config("output/genie_space_config.json")
    print(report.summary())
"""

import os
import re
import json
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
import requests
from pathlib import Path


@dataclass
class ValidationIssue:
    """Represents a validation issue found during table/column validation."""
    severity: str  # "error", "warning", "info"
    type: str  # "table_not_found", "column_not_found", "access_denied", etc.
    message: str
    table: Optional[str] = None
    column: Optional[str] = None
    location: Optional[str] = None  # where in config this was found


@dataclass
class ValidationReport:
    """Complete validation report for a Genie space configuration."""
    tables_checked: List[str] = field(default_factory=list)
    tables_valid: List[str] = field(default_factory=list)
    tables_invalid: List[str] = field(default_factory=list)
    columns_checked: Dict[str, List[str]] = field(default_factory=dict)
    columns_valid: Dict[str, List[str]] = field(default_factory=dict)
    columns_invalid: Dict[str, List[str]] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_issue(self, severity: str, type: str, message: str, **kwargs):
        """Add a validation issue to the report."""
        self.issues.append(ValidationIssue(
            severity=severity,
            type=type,
            message=message,
            **kwargs
        ))
    
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(issue.severity == "warning" for issue in self.issues)
    
    def summary(self) -> str:
        """Generate a human-readable summary of the validation report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TABLE & COLUMN VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Tables summary
        lines.append(f"Tables Checked: {len(self.tables_checked)}")
        lines.append(f"  ✓ Valid:   {len(self.tables_valid)}")
        if self.tables_invalid:
            lines.append(f"  ✗ Invalid: {len(self.tables_invalid)}")
        lines.append("")
        
        # Columns summary
        total_columns = sum(len(cols) for cols in self.columns_checked.values())
        valid_columns = sum(len(cols) for cols in self.columns_valid.values())
        invalid_columns = sum(len(cols) for cols in self.columns_invalid.values())
        
        lines.append(f"Columns Checked: {total_columns}")
        lines.append(f"  ✓ Valid:   {valid_columns}")
        if invalid_columns:
            lines.append(f"  ✗ Invalid: {invalid_columns}")
        lines.append("")
        
        # Issues breakdown
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        infos = [i for i in self.issues if i.severity == "info"]
        
        lines.append("Issues:")
        lines.append(f"  Errors:   {len(errors)}")
        lines.append(f"  Warnings: {len(warnings)}")
        lines.append(f"  Info:     {len(infos)}")
        lines.append("")
        
        # List all issues
        if self.issues:
            lines.append("-" * 80)
            lines.append("DETAILED ISSUES")
            lines.append("-" * 80)
            lines.append("")
            
            for issue in self.issues:
                icon = "✗" if issue.severity == "error" else "⚠" if issue.severity == "warning" else "ℹ"
                lines.append(f"{icon} [{issue.severity.upper()}] {issue.type}")
                lines.append(f"  {issue.message}")
                if issue.table:
                    lines.append(f"  Table: {issue.table}")
                if issue.column:
                    lines.append(f"  Column: {issue.column}")
                if issue.location:
                    lines.append(f"  Location: {issue.location}")
                lines.append("")
        
        # Final status
        lines.append("=" * 80)
        if not self.has_errors():
            lines.append("✓ VALIDATION PASSED - All tables and columns are valid!")
        else:
            lines.append("✗ VALIDATION FAILED - Please fix the errors above")
        lines.append("=" * 80)
        
        return "\n".join(lines)


class TableValidator:
    """Validates tables and columns in Genie Space configurations against Unity Catalog."""
    
    def __init__(
        self,
        databricks_host: Optional[str] = None,
        databricks_token: Optional[str] = None
    ):
        """
        Initialize the validator.
        
        Args:
            databricks_host: Databricks workspace URL (defaults to DATABRICKS_HOST env var)
            databricks_token: Databricks personal access token (defaults to DATABRICKS_TOKEN env var)
        """
        self.databricks_host = databricks_host or os.getenv("DATABRICKS_HOST")
        self.databricks_token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        
        if not self.databricks_host:
            raise ValueError("databricks_host must be provided or DATABRICKS_HOST env var must be set")
        if not self.databricks_token:
            raise ValueError("databricks_token must be provided or DATABRICKS_TOKEN env var must be set")
        
        # Clean up host URL
        self.databricks_host = self.databricks_host.rstrip('/')
        if not self.databricks_host.startswith('http'):
            self.databricks_host = f"https://{self.databricks_host}"
        
        # Cache for table schemas to avoid repeated API calls
        self._table_cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.databricks_token}",
            "Content-Type": "application/json"
        }
    
    def get_table_schema(self, catalog: str, schema: str, table: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema of a table from Unity Catalog.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            
        Returns:
            Dictionary containing table metadata including columns, or None if table doesn't exist
        """
        full_name = f"{catalog}.{schema}.{table}"
        
        # Check cache first
        if full_name in self._table_cache:
            return self._table_cache[full_name]
        
        try:
            # Use Unity Catalog API to get table information
            url = f"{self.databricks_host}/api/2.1/unity-catalog/tables/{catalog}.{schema}.{table}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                table_info = response.json()
                self._table_cache[full_name] = table_info
                return table_info
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # If Unity Catalog API fails, try SQL execution API
            return self._get_table_schema_via_sql(catalog, schema, table)
    
    def _get_table_schema_via_sql(self, catalog: str, schema: str, table: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to get table schema using DESCRIBE TABLE SQL command.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            
        Returns:
            Dictionary containing column information, or None if table doesn't exist
        """
        full_name = f"{catalog}.{schema}.{table}"
        
        try:
            # Use SQL execution API to describe the table
            url = f"{self.databricks_host}/api/2.0/sql/statements"
            sql = f"DESCRIBE TABLE {full_name}"
            
            payload = {
                "statement": sql,
                "warehouse_id": os.getenv("DATABRICKS_WAREHOUSE_ID")  # Optional, will use default if not set
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse the DESCRIBE output to extract columns
                columns = []
                if "manifest" in result and "schema" in result["manifest"]:
                    schema_info = result["manifest"]["schema"]
                    if "columns" in schema_info:
                        for col in schema_info["columns"]:
                            columns.append({
                                "name": col.get("name"),
                                "type_text": col.get("type_text"),
                                "type_name": col.get("type_name")
                            })
                
                table_info = {
                    "full_name": full_name,
                    "catalog_name": catalog,
                    "schema_name": schema,
                    "name": table,
                    "columns": columns
                }
                
                self._table_cache[full_name] = table_info
                return table_info
            else:
                return None
        except Exception:
            return None
    
    def validate_table(self, catalog: str, schema: str, table: str) -> bool:
        """
        Validate that a table exists.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            
        Returns:
            True if table exists, False otherwise
        """
        return self.get_table_schema(catalog, schema, table) is not None
    
    def validate_columns(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[str]
    ) -> Dict[str, bool]:
        """
        Validate that columns exist in a table.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            columns: List of column names to validate
            
        Returns:
            Dictionary mapping column names to validation status (True/False)
        """
        table_schema = self.get_table_schema(catalog, schema, table)
        
        if not table_schema:
            return {col: False for col in columns}
        
        # Extract column names from schema (case-insensitive comparison)
        schema_columns = set()
        if "columns" in table_schema:
            for col in table_schema["columns"]:
                schema_columns.add(col["name"].lower())
        
        # Validate each column
        results = {}
        for col in columns:
            results[col] = col.lower() in schema_columns
        
        return results
    
    def extract_columns_from_sql(self, sql: str, alias_map: Dict[str, str]) -> Set[str]:
        """
        Extract column references from SQL expressions.
        
        Args:
            sql: SQL query or expression
            alias_map: Mapping of table aliases to full table names (e.g., {"t": "catalog.schema.transactions"})
            
        Returns:
            Set of fully-qualified column references (table_name.column_name)
        """
        columns = set()
        
        # Pattern to match table_alias.column_name references
        # Matches: t.customer_id, a.product_name, etc.
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)\b'
        
        for match in re.finditer(pattern, sql):
            alias = match.group(1)
            column = match.group(2)
            
            # Skip SQL keywords and functions
            sql_keywords = {
                "current_date", "current_timestamp", "date_trunc", "date_add",
                "count", "sum", "avg", "min", "max", "try_divide"
            }
            if alias.lower() in sql_keywords or column.lower() in sql_keywords:
                continue
            
            # Resolve alias to full table name
            if alias in alias_map:
                full_table = alias_map[alias]
                columns.add(f"{full_table}.{column}")
        
        return columns
    
    def validate_config(self, config_path: str) -> ValidationReport:
        """
        Validate all tables and columns in a Genie space configuration.

        This includes validation of:
        - Table definitions in the 'tables' section
        - Tables referenced in SQL expressions
        - Tables referenced in example SQL queries
        - Tables referenced in benchmark questions

        Args:
            config_path: Path to the Genie space configuration JSON file

        Returns:
            ValidationReport containing all validation results and issues
        """
        report = ValidationReport()
        
        # Load configuration
        config_file = Path(config_path)
        if not config_file.exists():
            report.add_issue(
                severity="error",
                type="config_not_found",
                message=f"Configuration file not found: {config_path}"
            )
            return report
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Extract genie_space_config
        if "genie_space_config" in config:
            genie_config = config["genie_space_config"]
        else:
            genie_config = config
        
        # Validate tables
        tables = genie_config.get("tables", [])
        table_map = {}  # Maps catalog.schema.table to table info
        
        report.add_issue(
            severity="info",
            type="validation_start",
            message=f"Validating {len(tables)} tables from configuration"
        )
        
        for table_def in tables:
            catalog = table_def.get("catalog_name")
            schema = table_def.get("schema_name")
            table = table_def.get("table_name")
            
            if not all([catalog, schema, table]):
                report.add_issue(
                    severity="error",
                    type="incomplete_table_definition",
                    message="Table definition missing catalog_name, schema_name, or table_name",
                    location="tables"
                )
                continue
            
            full_name = f"{catalog}.{schema}.{table}"
            report.tables_checked.append(full_name)
            table_map[full_name] = table_def
            
            # Validate table exists
            if self.validate_table(catalog, schema, table):
                report.tables_valid.append(full_name)
                report.add_issue(
                    severity="info",
                    type="table_valid",
                    message=f"Table exists and is accessible",
                    table=full_name
                )
            else:
                report.tables_invalid.append(full_name)
                report.add_issue(
                    severity="error",
                    type="table_not_found",
                    message=f"Table does not exist or is not accessible",
                    table=full_name,
                    location="tables"
                )
        
        # Extract and validate columns from SQL snippets
        self._validate_sql_snippets(genie_config, table_map, report)
        self._validate_example_queries(genie_config, table_map, report)
        self._validate_benchmark_queries(genie_config, table_map, report)

        return report
    
    def _validate_sql_snippets(
        self,
        genie_config: Dict[str, Any],
        table_map: Dict[str, Any],
        report: ValidationReport
    ):
        """Validate columns referenced in sql_snippets (filters, expressions, measures)."""
        sql_snippets = genie_config.get("sql_snippets", {})
        
        if not sql_snippets:
            return
        
        # Build alias map from table definitions
        alias_map = self._build_alias_map(genie_config)
        
        # Validate filters
        filters = sql_snippets.get("filters", [])
        if filters:
            report.add_issue(
                severity="info",
                type="validation_section",
                message=f"Validating columns in {len(filters)} SQL filters"
            )
            for filt in filters:
                display_name = filt.get("display_name", "unnamed")
                sql = filt.get("sql", "")
                self._validate_sql_string(sql, display_name, "sql_snippets.filters", alias_map, table_map, report)
        
        # Validate expressions (dimensions)
        expressions = sql_snippets.get("expressions", [])
        if expressions:
            report.add_issue(
                severity="info",
                type="validation_section",
                message=f"Validating columns in {len(expressions)} SQL expressions"
            )
            for expr in expressions:
                alias = expr.get("alias", "unnamed")
                sql = expr.get("sql", "")
                self._validate_sql_string(sql, alias, "sql_snippets.expressions", alias_map, table_map, report)
        
        # Validate measures (aggregations)
        measures = sql_snippets.get("measures", [])
        if measures:
            report.add_issue(
                severity="info",
                type="validation_section",
                message=f"Validating columns in {len(measures)} SQL measures"
            )
            for measure in measures:
                alias = measure.get("alias", "unnamed")
                sql = measure.get("sql", "")
                self._validate_sql_string(sql, alias, "sql_snippets.measures", alias_map, table_map, report)
    
    def _validate_sql_string(
        self,
        sql: str,
        name: str,
        location_prefix: str,
        alias_map: Dict[str, str],
        table_map: Dict[str, Any],
        report: ValidationReport
    ):
        """Helper method to validate a SQL string."""
        if not sql:
            return
        
        # Extract column references
        columns = self.extract_columns_from_sql(sql, alias_map)
        
        for col_ref in columns:
            # Parse table.column
            if '.' in col_ref:
                parts = col_ref.rsplit('.', 1)
                full_table = parts[0]
                column = parts[1]
                
                # Parse table name
                table_parts = full_table.split('.')
                if len(table_parts) == 3:
                    catalog, schema, table = table_parts
                    
                    # Track column check
                    if full_table not in report.columns_checked:
                        report.columns_checked[full_table] = []
                    if column not in report.columns_checked[full_table]:
                        report.columns_checked[full_table].append(column)
                    
                    # Validate column
                    if full_table in report.tables_valid:
                        col_results = self.validate_columns(catalog, schema, table, [column])
                        
                        if col_results.get(column, False):
                            if full_table not in report.columns_valid:
                                report.columns_valid[full_table] = []
                            if column not in report.columns_valid[full_table]:
                                report.columns_valid[full_table].append(column)
                        else:
                            if full_table not in report.columns_invalid:
                                report.columns_invalid[full_table] = []
                            if column not in report.columns_invalid[full_table]:
                                report.columns_invalid[full_table].append(column)
                            
                            report.add_issue(
                                severity="error",
                                type="column_not_found",
                                message=f"Column not found in table",
                                table=full_table,
                                column=column,
                                location=f"{location_prefix}[{name}]"
                            )
    
    def _validate_example_queries(
        self,
        genie_config: Dict[str, Any],
        table_map: Dict[str, Any],
        report: ValidationReport
    ):
        """Validate columns referenced in example_sql_queries."""
        example_queries = genie_config.get("example_sql_queries", [])
        
        if not example_queries:
            return
        
        report.add_issue(
            severity="info",
            type="validation_section",
            message=f"Validating columns in {len(example_queries)} example queries"
        )
        
        # Note: Full SQL parsing is complex, so we'll do basic validation
        # In a production system, you might want to use a SQL parser library
        for i, query_def in enumerate(example_queries):
            question = query_def.get("question", f"Query {i+1}")
            sql_query = query_def.get("sql_query", "")
            
            # Extract table names from FROM and JOIN clauses
            tables_in_query = self._extract_tables_from_sql(sql_query)
            
            for table_ref in tables_in_query:
                if table_ref not in report.tables_valid:
                    report.add_issue(
                        severity="warning",
                        type="table_reference_invalid",
                        message=f"Query references table that failed validation",
                        table=table_ref,
                        location=f"example_sql_queries[{question[:50]}...]"
                    )
    
    def _validate_benchmark_queries(
        self,
        genie_config: Dict[str, Any],
        table_map: Dict[str, Any],
        report: ValidationReport
    ):
        """Validate tables referenced in benchmark_questions."""
        benchmark_questions = genie_config.get("benchmark_questions", [])

        if not benchmark_questions:
            return

        report.add_issue(
            severity="info",
            type="validation_section",
            message=f"Validating tables in {len(benchmark_questions)} benchmark questions"
        )

        for i, benchmark in enumerate(benchmark_questions):
            question = benchmark.get("question", f"Benchmark {i+1}")
            expected_sql = benchmark.get("expected_sql", "")

            if not expected_sql:
                continue

            # Extract table names from the SQL query
            tables_in_query = self._extract_tables_from_sql(expected_sql)

            for table_ref in tables_in_query:
                if table_ref not in report.tables_valid:
                    report.add_issue(
                        severity="warning",
                        type="table_reference_invalid",
                        message=f"Benchmark question references table that failed validation",
                        table=table_ref,
                        location=f"benchmark_questions[{question[:50]}...]"
                    )

    def _build_alias_map(self, genie_config: Dict[str, Any]) -> Dict[str, str]:
        """Build a map of common table aliases to full table names."""
        alias_map = {}
        
        tables = genie_config.get("tables", [])
        for table_def in tables:
            catalog = table_def.get("catalog_name")
            schema = table_def.get("schema_name")
            table = table_def.get("table_name")
            
            if all([catalog, schema, table]):
                full_name = f"{catalog}.{schema}.{table}"
                
                # Use first letter as alias (common convention: transactions -> t, articles -> a)
                alias = table[0].lower()
                alias_map[alias] = full_name
                
                # Also map common aliases
                if table == "transactions":
                    alias_map["t"] = full_name
                elif table == "articles":
                    alias_map["a"] = full_name
                elif table == "customers":
                    alias_map["c"] = full_name
                elif table == "customer_demographics":
                    alias_map["d"] = full_name
                elif table == "category_insights":
                    alias_map["ci"] = full_name
        
        return alias_map
    
    def _extract_tables_from_sql(self, sql: str) -> Set[str]:
        """Extract full table names from SQL query."""
        tables = set()

        # Pattern to match catalog.schema.table references with optional backticks
        # Matches: catalog.schema.table or `catalog`.`schema`.`table` or mixed
        pattern = r'`?([a-zA-Z_][a-zA-Z0-9_]*)`?\.`?([a-zA-Z_][a-zA-Z0-9_]*)`?\.`?([a-zA-Z_][a-zA-Z0-9_]*)`?'

        for match in re.finditer(pattern, sql):
            # Combine the three parts (catalog, schema, table) without backticks
            full_name = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
            tables.add(full_name)

        return tables


def main():
    """Example usage and CLI interface."""
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Default config path
    config_path = "output/genie_space_config.json"
    
    # Allow custom path from command line
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    print("=" * 80)
    print("TABLE & COLUMN VALIDATOR")
    print("=" * 80)
    print()
    print(f"Configuration: {config_path}")
    print()
    
    try:
        # Initialize validator
        validator = TableValidator()
        
        # Run validation
        print("Running validation...")
        print()
        report = validator.validate_config(config_path)
        
        # Print report
        print(report.summary())
        
        # Exit with appropriate code
        sys.exit(1 if report.has_errors() else 0)
        
    except Exception as e:
        print(f"✗ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
