"""
SQL Executor

Executes SQL queries on Databricks using the Databricks SDK.
"""

import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLExecutor:
    """Execute SQL queries on Databricks SQL Warehouse using SDK."""

    def __init__(self, host: str, token: str, warehouse_id: str):
        """
        Initialize SQL executor with Databricks SDK.

        Args:
            host: Databricks workspace host
            token: Personal access token (or None to use env OAuth)
            warehouse_id: SQL Warehouse ID to execute queries on
        """
        import requests

        self.host = host.replace("https://", "").replace("http://", "")
        self.warehouse_id = warehouse_id
        self.token = token

        # Use requests directly to avoid SDK auth conflicts
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
        self.base_url = f"https://{self.host}"
        logger.info(f"SQLExecutor initialized with token auth (warehouse: {warehouse_id})")

    def execute(
        self,
        sql: str,
        timeout: int = 120,
        wait_timeout: str = "50s"  # Databricks API only accepts 5-50 seconds
    ) -> Dict[str, Any]:
        """
        Execute SQL query using Databricks SQL Statement API.

        Args:
            sql: SQL query to execute
            timeout: Total timeout in seconds
            wait_timeout: How long to wait for query completion

        Returns:
            {
                "status": "SUCCEEDED" | "FAILED" | "TIMEOUT",
                "result": {
                    "columns": List[str],
                    "rows": List[Dict],
                    "row_count": int
                } or None,
                "error": str or None,
                "execution_time": float
            }
        """
        logger.debug(f"Executing SQL: {sql[:100]}...")
        start_time = time.time()

        try:
            # Execute statement using REST API
            url = f"{self.base_url}/api/2.0/sql/statements"
            payload = {
                "warehouse_id": self.warehouse_id,
                "statement": sql,
                "wait_timeout": wait_timeout
            }

            response = self.session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            execution_time = time.time() - start_time
            state = data.get("status", {}).get("state", "UNKNOWN")

            logger.debug(f"Statement state: {state}")

            if state == "SUCCEEDED":
                # Extract results
                result_data = self._extract_results(data)
                logger.debug(f"Query succeeded ({result_data['row_count']} rows, {execution_time:.2f}s)")

                return {
                    "status": "SUCCEEDED",
                    "result": result_data,
                    "error": None,
                    "execution_time": execution_time
                }

            elif state in ["FAILED", "CANCELED", "CLOSED"]:
                error_message = data.get("status", {}).get("error", {}).get("message", "Unknown error")
                logger.warning(f"Query failed: {error_message}")

                return {
                    "status": "FAILED",
                    "result": None,
                    "error": error_message,
                    "execution_time": execution_time
                }

            else:
                # Still running or pending
                logger.warning(f"Query in unexpected state: {state}")
                return {
                    "status": "TIMEOUT",
                    "result": None,
                    "error": f"Query in state: {state}",
                    "execution_time": execution_time
                }

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "status": "FAILED",
                "result": None,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def _extract_results(self, data: Dict) -> Dict:
        """
        Extract query results from REST API response.

        Args:
            data: API response dict

        Returns:
            {
                "columns": List[str],
                "rows": List[Dict],
                "row_count": int
            }
        """
        # Get column names from manifest
        columns = []
        manifest = data.get("manifest", {})
        schema = manifest.get("schema", {})
        if schema.get("columns"):
            columns = [col.get("name", f"col_{i}") for i, col in enumerate(schema["columns"])]

        # Get data
        rows = []
        result = data.get("result", {})
        data_array = result.get("data_array", [])

        for row_data in data_array:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row_data[i] if i < len(row_data) else None
            rows.append(row_dict)

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }


# Example usage
if __name__ == "__main__":
    import os

    HOST = os.getenv("DATABRICKS_HOST")
    TOKEN = os.getenv("DATABRICKS_TOKEN")
    WAREHOUSE_ID = os.getenv("WAREHOUSE_ID")

    executor = SQLExecutor(HOST, TOKEN, WAREHOUSE_ID)

    # Test query
    sql = """
    SELECT 'Hello' as greeting, 123 as number
    UNION ALL
    SELECT 'World', 456
    """

    result = executor.execute(sql)

    print(f"Status: {result['status']}")
    print(f"Execution time: {result['execution_time']:.2f}s")

    if result['status'] == 'SUCCEEDED':
        print(f"\nColumns: {result['result']['columns']}")
        print(f"Rows: {result['result']['row_count']}")
        print(f"\nData:")
        for row in result['result']['rows']:
            print(f"  {row}")
    else:
        print(f"Error: {result['error']}")
