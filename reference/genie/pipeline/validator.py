"""Configuration validation module."""

import os
from pathlib import Path
from typing import Optional

from genie.validation import TableValidator
from genie.validation.table_validator import ValidationReport


def validate_config(
    config_path: str = "output/genie_space_config.json",
    databricks_host: Optional[str] = None,
    databricks_token: Optional[str] = None,
    verbose: bool = True
) -> ValidationReport:
    """
    Validate tables and columns in Genie space configuration.
    
    This function checks that all tables and columns referenced in the configuration
    actually exist in your Databricks Unity Catalog before attempting to create
    the Genie space.
    
    Args:
        config_path: Path to Genie space configuration file
        databricks_host: Databricks workspace URL (overrides env var)
        databricks_token: Databricks personal access token (overrides env var)
        verbose: Print progress messages
        
    Returns:
        ValidationReport: Validation results with details
        
    Raises:
        ValueError: If credentials are missing or config file not found
        Exception: If validation fails
    """
    # Get credentials
    host = databricks_host or os.getenv("DATABRICKS_HOST")
    token = databricks_token or os.getenv("DATABRICKS_TOKEN")
    
    if not host:
        raise ValueError(
            "DATABRICKS_HOST must be set. "
            "Either set environment variable or pass as argument."
        )
    
    if not token:
        raise ValueError(
            "DATABRICKS_TOKEN must be set. "
            "Either set environment variable or pass as argument."
        )
    
    # Check config file exists
    config_path_obj = Path(config_path)
    if not config_path_obj.exists():
        raise ValueError(f"Configuration file not found: {config_path}")
    
    if verbose:
        print(f"✓ Validating tables and columns...")
        print(f"   Config: {config_path}")
    
    # Initialize validator
    validator = TableValidator(
        databricks_host=host,
        databricks_token=token
    )
    
    # Run validation
    report = validator.validate_config(config_path)
    
    if verbose:
        # Print summary
        total_tables = report.tables_checked
        valid_tables = report.tables_valid
        total_columns = sum(len(cols) for cols in report.columns_checked.values())
        valid_columns = sum(len(cols) for cols in report.columns_valid.values())
        
        print(f"   Tables: {valid_tables}/{total_tables} valid")
        print(f"   Columns: {valid_columns}/{total_columns} valid")
        
        if report.has_errors():
            print(f"   ❌ {len([i for i in report.issues if i.severity == 'error'])} errors found")
        if report.has_warnings():
            print(f"   ⚠️  {len([i for i in report.issues if i.severity == 'warning'])} warnings found")
        
        if not report.has_errors():
            print(f"   ✓ Validation passed!")
    
    return report
