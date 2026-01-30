"""
Benchmark Scorer

Runs benchmark questions through Genie and scores the results using LLM judge.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.genie_client import GenieConversationalClient
from lib.sql import SQLExecutor
from prompts.prompt_loader import PromptLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkScorer:
    """Score Genie Space performance using benchmark Q&A pairs."""

    def __init__(
        self,
        genie_client: GenieConversationalClient,
        llm_client,  # LLM client for answer comparison
        sql_executor: SQLExecutor = None,  # Optional SQL executor for result comparison
        config: Dict = None
    ):
        """
        Initialize benchmark scorer.

        Args:
            genie_client: Client for asking Genie questions
            llm_client: LLM client for comparing answers
            sql_executor: Optional SQL executor for running expected queries
            config: Scorer configuration
        """
        self.genie_client = genie_client
        self.llm_client = llm_client
        self.sql_executor = sql_executor
        self.config = config or {}
        self.prompt_loader = PromptLoader()
        self.use_result_comparison = sql_executor is not None

    def score(self, benchmarks: List[Dict]) -> Dict:
        """
        Run all benchmarks and calculate score.

        Args:
            benchmarks: List of benchmark dictionaries with:
                - id: str
                - question: str
                - expected_sql: str
                - (optional) expected_result: dict

        Returns:
            {
                "score": float (0.0 to 1.0),
                "total": int,
                "passed": int,
                "failed": int,
                "results": List[Dict],
                "timestamp": str,
                "duration_seconds": float
            }
        """
        logger.info(f"Starting benchmark scoring with {len(benchmarks)} questions")
        start_time = datetime.now()

        results = []
        # Parallel workers (0 = sequential, >0 = parallel)
        parallel_workers = self.config.get("parallel_workers", 0)
        # Add delay between questions to avoid rate limiting (default 3 seconds)
        question_delay = self.config.get("question_delay", 3.0)
        # Extra delay after errors (default 5 seconds)
        error_delay = self.config.get("error_delay", 5.0)

        if parallel_workers > 0:
            # PARALLEL MODE
            logger.info(f"Running {len(benchmarks)} benchmarks in PARALLEL ({parallel_workers} workers)")
            results = self._score_parallel(benchmarks, parallel_workers)
        else:
            # SEQUENTIAL MODE (original behavior)
            for i, benchmark in enumerate(benchmarks):
                logger.info(f"[{i+1}/{len(benchmarks)}] Testing: {benchmark['question'][:80]}...")

                result = self._score_single_benchmark(benchmark)
                results.append(result)

                # Log result
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                logger.info(f"  {status} ({result.get('failure_category', 'N/A')})")

                # Delay between questions to avoid rate limiting
                if i < len(benchmarks) - 1:
                    # Longer delay after errors to let API recover
                    if result.get("failure_category") == "api_error":
                        logger.info(f"  Waiting {error_delay}s after API error...")
                        time.sleep(error_delay)
                    elif question_delay > 0:
                        time.sleep(question_delay)

        # Calculate overall score
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        score = passed / len(results) if results else 0.0

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            "score": score,
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration
        }

        logger.info(f"\n{'='*60}")
        logger.info(f"Benchmark Score: {score:.2%} ({passed}/{len(results)} passed)")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"{'='*60}\n")

        return summary

    def _score_parallel(self, benchmarks: List[Dict], max_workers: int) -> List[Dict]:
        """
        Score benchmarks in parallel using ThreadPoolExecutor.

        Args:
            benchmarks: List of benchmark dictionaries
            max_workers: Maximum number of parallel workers

        Returns:
            List of result dictionaries (in original order)
        """
        results = [None] * len(benchmarks)  # Preserve order

        def score_with_index(idx_benchmark):
            idx, benchmark = idx_benchmark
            try:
                result = self._score_single_benchmark(benchmark)
                status = "✅" if result["passed"] else "❌"
                logger.info(f"  [{idx+1}] {status} {benchmark['question'][:50]}...")
                return idx, result
            except Exception as e:
                logger.error(f"  [{idx+1}] Error: {e}")
                return idx, {
                    "benchmark_id": benchmark.get("id"),
                    "question": benchmark["question"],
                    "expected_sql": benchmark["expected_sql"],
                    "genie_sql": None,
                    "passed": False,
                    "failure_reason": str(e),
                    "failure_category": "parallel_error",
                    "response_time": 0
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(score_with_index, (i, b)): i
                for i, b in enumerate(benchmarks)
            }

            completed = 0
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result
                completed += 1
                logger.info(f"  Progress: {completed}/{len(benchmarks)} completed")

        return results

    def _score_single_benchmark(self, benchmark: Dict) -> Dict:
        """
        Score a single benchmark question.

        Args:
            benchmark: Benchmark dictionary

        Returns:
            {
                "benchmark_id": str,
                "question": str,
                "expected_sql": str,
                "genie_sql": str or None,
                "expected_result": dict or None,
                "genie_result": dict or None,
                "passed": bool,
                "failure_reason": str or None,
                "failure_category": str or None,
                "comparison_details": dict,
                "response_time": float
            }
        """
        question = benchmark["question"]
        expected_sql = benchmark["expected_sql"]

        # Ask Genie
        try:
            genie_response = self.genie_client.ask(
                question,
                timeout=self.config.get("question_timeout", 120)
            )
        except Exception as e:
            logger.error(f"Error asking Genie: {e}")
            return {
                "benchmark_id": benchmark["id"],
                "question": question,
                "expected_sql": expected_sql,
                "genie_sql": None,
                "expected_result": None,
                "genie_result": None,
                "passed": False,
                "failure_reason": f"Genie API error: {str(e)}",
                "failure_category": "api_error",
                "comparison_details": {},
                "response_time": 0
            }

        # Extract Genie's SQL and result
        genie_sql = genie_response.get("sql")
        genie_result = genie_response.get("result")

        # Execute expected SQL if executor available
        expected_result = None
        if self.use_result_comparison and expected_sql:
            logger.debug(f"Executing expected SQL for comparison...")
            try:
                expected_execution = self.sql_executor.execute(expected_sql, timeout=60)
                if expected_execution["status"] == "SUCCEEDED":
                    expected_result = expected_execution["result"]
                    logger.debug(f"Expected query returned {expected_result['row_count']} rows")
                else:
                    logger.warning(f"Expected SQL execution failed: {expected_execution['error']}")
            except Exception as e:
                logger.warning(f"Could not execute expected SQL: {e}")

        # Check if Genie generated SQL
        if genie_response["status"] != "COMPLETED":
            return {
                "benchmark_id": benchmark["id"],
                "question": question,
                "expected_sql": expected_sql,
                "genie_sql": genie_sql,
                "expected_result": None,
                "genie_result": None,
                "passed": False,
                "failure_reason": genie_response.get("error", "No SQL generated"),
                "failure_category": self._categorize_failure(genie_response, None),
                "comparison_details": {},
                "response_time": genie_response.get("response_time", 0)
            }

        # Compare answers using LLM judge (with executed results if available)
        comparison = self._compare_answers(
            question=question,
            expected_sql=expected_sql,
            genie_sql=genie_sql,
            expected_result=expected_result or benchmark.get("expected_result"),
            genie_result=genie_result
        )

        return {
            "benchmark_id": benchmark["id"],
            "question": question,
            "expected_sql": expected_sql,
            "genie_sql": genie_sql,
            "expected_result": expected_result or benchmark.get("expected_result"),
            "genie_result": genie_result,
            "passed": comparison["passed"],
            "failure_reason": comparison.get("reasoning") if not comparison["passed"] else None,
            "failure_category": self._categorize_failure(genie_response, comparison) if not comparison["passed"] else None,
            "comparison_details": comparison,
            "response_time": genie_response.get("response_time", 0)
        }

    def _compare_answers(
        self,
        question: str,
        expected_sql: str,
        genie_sql: str,
        expected_result: Dict = None,
        genie_result: Dict = None
    ) -> Dict:
        """
        Compare expected vs actual answer using LLM judge.

        Args:
            question: The question
            expected_sql: Expected SQL
            genie_sql: Genie's SQL
            expected_result: Expected query result (optional)
            genie_result: Genie's query result (optional)

        Returns:
            {
                "passed": bool,
                "confidence": "high" | "medium" | "low",
                "reasoning": str,
                "differences": List[str],
                "semantic_equivalence": str
            }
        """
        # Determine what we're comparing
        expected = expected_result or expected_sql
        actual = genie_result or genie_sql

        comparing_type = "results" if (expected_result and genie_result) else "SQL"
        logger.info(f"  Comparing {comparing_type}...")
        logger.debug(f"  Expected: {str(expected)[:200]}...")
        logger.debug(f"  Genie: {str(actual)[:200]}...")

        # Use LLM judge with fat prompt
        prompt = self.prompt_loader.format_answer_comparison_prompt(
            question=question,
            expected_result=expected,
            genie_result=actual
        )

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent judging
                max_tokens=100000
            )

            # Parse JSON response
            comparison_result = self._parse_comparison_result(response)
            logger.info(f"  LLM verdict: passed={comparison_result.get('passed')}, confidence={comparison_result.get('confidence')}")
            if not comparison_result.get('passed'):
                logger.info(f"  Reason: {comparison_result.get('reasoning', 'N/A')[:100]}")
            return comparison_result

        except Exception as e:
            logger.error(f"Error in LLM comparison: {e}")
            # Fallback: simple SQL comparison
            return self._simple_sql_comparison(expected_sql, genie_sql)

    def _parse_comparison_result(self, response: str) -> Dict:
        """
        Parse LLM comparison response.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Parsed comparison dictionary
        """
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()

            result = json.loads(response)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Return default failed comparison
            return {
                "passed": False,
                "confidence": "low",
                "reasoning": f"Failed to parse LLM response: {e}",
                "differences": ["LLM response parsing error"],
                "semantic_equivalence": "Unknown"
            }

    def _simple_sql_comparison(self, expected_sql: str, genie_sql: str) -> Dict:
        """
        Simple SQL comparison fallback.

        Args:
            expected_sql: Expected SQL
            genie_sql: Genie's SQL

        Returns:
            Comparison result
        """
        # Handle None cases
        if not genie_sql:
            return {
                "passed": False,
                "confidence": "high",
                "reasoning": "Genie did not generate any SQL",
                "differences": ["No SQL generated"],
                "semantic_equivalence": "No output"
            }

        if not expected_sql:
            return {
                "passed": False,
                "confidence": "low",
                "reasoning": "No expected SQL to compare against",
                "differences": ["Missing expected SQL"],
                "semantic_equivalence": "Unknown"
            }

        # Normalize both SQLs
        expected_normalized = self._normalize_sql(expected_sql)
        genie_normalized = self._normalize_sql(genie_sql)

        passed = expected_normalized == genie_normalized

        return {
            "passed": passed,
            "confidence": "medium" if passed else "low",
            "reasoning": "Simple SQL string comparison (LLM judge failed)",
            "differences": [] if passed else ["SQLs differ after normalization"],
            "semantic_equivalence": "Exact match" if passed else "Different"
        }

    def _normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL for comparison.

        Args:
            sql: SQL query string

        Returns:
            Normalized SQL
        """
        if not sql:
            return ""

        import re
        # Convert to uppercase
        sql = sql.upper()
        # Remove extra whitespace
        sql = re.sub(r'\s+', ' ', sql)
        # Remove trailing semicolon
        sql = sql.rstrip(';')
        # Strip
        sql = sql.strip()
        return sql

    def _categorize_failure(self, genie_response: Dict, comparison: Dict = None) -> str:
        """
        Categorize failure type for targeted fixes.

        Args:
            genie_response: Genie's response
            comparison: Comparison result (if available)

        Returns:
            Failure category string
        """
        status = genie_response.get("status")

        if status == "FAILED":
            error = genie_response.get("error", "")
            # Handle case where error is a dict or None
            if isinstance(error, dict):
                error = error.get("message", "")
            if not error:
                error = ""
            error_lower = error.lower()

            if "not found" in error_lower or "does not exist" in error_lower:
                return "missing_table_or_column"
            elif "syntax" in error_lower:
                return "sql_syntax_error"
            elif "permission" in error_lower:
                return "permission_denied"
            else:
                return "execution_failed"

        elif status == "TIMEOUT":
            return "timeout"

        elif status == "COMPLETED":
            if not genie_response.get("sql"):
                return "no_sql_generated"

            if comparison:
                differences = comparison.get("differences", [])
                reasoning = comparison.get("reasoning", "").lower()

                if "wrong" in reasoning or "different" in reasoning:
                    if "join" in reasoning:
                        return "wrong_join"
                    elif "aggregation" in reasoning:
                        return "wrong_aggregation"
                    elif "filter" in reasoning:
                        return "wrong_filter"
                    elif "column" in reasoning:
                        return "wrong_column"
                    else:
                        return "semantic_difference"

        return "unknown_failure"


# Example usage
if __name__ == "__main__":
    import os
    from lib.benchmark_parser import BenchmarkLoader

    # Configuration
    HOST = os.getenv("DATABRICKS_HOST")
    TOKEN = os.getenv("DATABRICKS_TOKEN")
    SPACE_ID = os.getenv("GENIE_SPACE_ID")

    # Mock LLM client for testing
    class MockLLMClient:
        def generate(self, prompt, temperature=0.1, max_tokens=1000):
            # Return mock comparison result
            return json.dumps({
                "passed": True,
                "confidence": "high",
                "reasoning": "Mock comparison - always passes",
                "differences": [],
                "semantic_equivalence": "Mock result"
            })

    # Create clients
    genie_client = GenieConversationalClient(HOST, TOKEN, SPACE_ID)
    llm_client = MockLLMClient()

    # Load benchmarks
    loader = BenchmarkLoader("benchmarks/benchmarks.json")
    benchmarks = loader.load()

    # Create scorer
    scorer = BenchmarkScorer(genie_client, llm_client)

    # Run scoring
    results = scorer.score(benchmarks)

    print(json.dumps(results, indent=2))
