"""
Benchmark query validation service.

Validates that benchmark SQL queries execute successfully against Unity Catalog.
"""

import os
import sys
from typing import List, Dict, Any
from databricks import sql


# Add parent directory to sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)


def validate_benchmark_queries(
    benchmarks: List[Dict[str, Any]],
    databricks_server_hostname: str,
    databricks_http_path: str,
    databricks_token: str,
    limit_rows: int = 10,
    query_timeout: int = 30
) -> Dict[str, Any]:
    """
    Validate benchmark SQL queries by executing them against Unity Catalog.

    Args:
        benchmarks: List of benchmark dictionaries with 'question' and 'expected_sql' fields
        databricks_server_hostname: Databricks SQL warehouse hostname
        databricks_http_path: SQL warehouse HTTP path
        databricks_token: Databricks access token
        limit_rows: Maximum rows to fetch per query (default: 10, faster validation)
        query_timeout: Timeout per query in seconds (default: 30)

    Returns:
        Dictionary with validation results:
        {
            "has_errors": bool,
            "total_benchmarks": int,
            "passed": int,
            "failed": int,
            "results": [
                {
                    "index": int,
                    "question": str,
                    "sql": str,
                    "status": "passed" | "failed",
                    "error": str | null,
                    "row_count": int | null,
                    "execution_time_ms": float | null
                }
            ]
        }
    """
    import time
    import re
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

    def add_limit_to_query(sql: str, limit: int) -> str:
        """Add LIMIT clause to SQL query if not already present."""
        # Remove trailing semicolons and whitespace
        sql = sql.rstrip().rstrip(';').rstrip()

        # Check if query already has LIMIT
        if re.search(r'\bLIMIT\s+\d+', sql, re.IGNORECASE):
            return sql

        # Wrap in subquery if it's a complex query (has ORDER BY, GROUP BY, etc.)
        if re.search(r'\b(ORDER BY|GROUP BY|HAVING)\b', sql, re.IGNORECASE):
            return f"SELECT * FROM ({sql}) AS subquery LIMIT {limit}"
        else:
            return f"{sql} LIMIT {limit}"

    def validate_single_query(connection, idx: int, benchmark: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single benchmark query."""
        question = benchmark.get('question', benchmark.get('korean_question', ''))
        expected_sql = benchmark.get('expected_sql', '')

        if not expected_sql:
            return {
                "index": idx,
                "question": question,
                "sql": expected_sql,
                "status": "failed",
                "error": "No SQL query provided",
                "row_count": None,
                "execution_time_ms": None
            }

        # Add LIMIT to speed up query execution
        limited_sql = add_limit_to_query(expected_sql, limit_rows)

        # Execute the query with timeout
        try:
            cursor = connection.cursor()
            start_time = time.time()

            cursor.execute(limited_sql)

            # Fetch limited results
            rows = cursor.fetchmany(limit_rows)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            cursor.close()

            return {
                "index": idx,
                "question": question,
                "sql": expected_sql,
                "status": "passed",
                "error": None,
                "row_count": len(rows),
                "execution_time_ms": round(execution_time, 2)
            }

        except Exception as e:
            error_message = str(e)
            return {
                "index": idx,
                "question": question,
                "sql": expected_sql,
                "status": "failed",
                "error": error_message,
                "row_count": None,
                "execution_time_ms": None
            }

    results = []
    passed_count = 0
    failed_count = 0

    # Connect to Databricks SQL warehouse
    try:
        connection = sql.connect(
            server_hostname=databricks_server_hostname,
            http_path=databricks_http_path,
            access_token=databricks_token
        )

        # Validate queries in parallel with timeout
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for idx, benchmark in enumerate(benchmarks):
                future = executor.submit(validate_single_query, connection, idx, benchmark)
                futures.append(future)

            # Collect results with timeout
            for future in futures:
                try:
                    result = future.result(timeout=query_timeout)
                    results.append(result)
                    if result["status"] == "passed":
                        passed_count += 1
                    else:
                        failed_count += 1
                except FuturesTimeoutError:
                    idx = len(results)
                    benchmark = benchmarks[idx] if idx < len(benchmarks) else {}
                    question = benchmark.get('question', benchmark.get('korean_question', ''))
                    expected_sql = benchmark.get('expected_sql', '')
                    results.append({
                        "index": idx,
                        "question": question,
                        "sql": expected_sql,
                        "status": "failed",
                        "error": f"Query timeout after {query_timeout} seconds",
                        "row_count": None,
                        "execution_time_ms": None
                    })
                    failed_count += 1

        connection.close()

    except Exception as e:
        # Connection error - mark all as failed
        for idx, benchmark in enumerate(benchmarks):
            question = benchmark.get('question', benchmark.get('korean_question', ''))
            expected_sql = benchmark.get('expected_sql', '')
            results.append({
                "index": idx,
                "question": question,
                "sql": expected_sql,
                "status": "failed",
                "error": f"Database connection error: {str(e)}",
                "row_count": None,
                "execution_time_ms": None
            })
        failed_count = len(benchmarks)

    # Sort results by index to maintain order
    results.sort(key=lambda x: x["index"])

    return {
        "has_errors": failed_count > 0,
        "total_benchmarks": len(benchmarks),
        "passed": passed_count,
        "failed": failed_count,
        "results": results
    }
