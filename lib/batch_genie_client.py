"""
Batch Genie Client with Safety Measures

Handles concurrent Genie API calls with:
- Rate limiting (semaphore-based)
- Retry logic with exponential backoff
- Circuit breaker for cascading failures
- Graceful degradation
- Per-query timeout handling
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Too many failures, stop batching
    HALF_OPEN = "half_open"  # Testing if service recovered


class BatchGenieClient:
    """
    Batch Genie API caller with safety measures.

    Safety features:
    1. Semaphore: Limits concurrent Genie calls
    2. Retry: Exponential backoff for failures
    3. Circuit Breaker: Falls back to sequential on cascading failures
    4. Timeout: Per-query timeout handling
    5. Graceful Degradation: Continue with partial results
    """

    def __init__(
        self,
        genie_client,
        config: Optional[Dict] = None
    ):
        """
        Initialize batch Genie client.

        Args:
            genie_client: Base Genie client instance
            config: Configuration dict:
                - max_concurrent: Max concurrent Genie calls (default: 3)
                - retry_attempts: Max retry attempts per query (default: 2)
                - retry_delay: Initial retry delay in seconds (default: 5)
                - query_timeout: Timeout per query in seconds (default: 120)
                - circuit_breaker_threshold: Failures before circuit opens (default: 5)
                - circuit_breaker_timeout: Seconds before retry (default: 60)
                - fallback_to_sequential: Fall back to sequential on circuit open (default: True)
        """
        self.genie_client = genie_client
        self.config = config or {}

        # Concurrency control
        self.max_concurrent = self.config.get("max_concurrent", 3)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        # Retry configuration
        self.retry_attempts = self.config.get("retry_attempts", 2)
        self.retry_delay = self.config.get("retry_delay", 5)

        # Timeout configuration
        self.query_timeout = self.config.get("query_timeout", 120)

        # Circuit breaker
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.circuit_breaker_threshold = self.config.get("circuit_breaker_threshold", 5)
        self.circuit_breaker_timeout = self.config.get("circuit_breaker_timeout", 60)
        self.circuit_open_time = None
        self.fallback_to_sequential = self.config.get("fallback_to_sequential", True)

        logger.info(f"BatchGenieClient initialized: max_concurrent={self.max_concurrent}, "
                   f"retry_attempts={self.retry_attempts}, circuit_threshold={self.circuit_breaker_threshold}")

    async def batch_ask(self, benchmarks: List[Dict]) -> List[Dict]:
        """
        Ask Genie multiple questions in batch with safety measures.

        Args:
            benchmarks: List of benchmark dicts with 'question' field

        Returns:
            List of response dicts (same order as input):
                {
                    "benchmark_id": str,
                    "question": str,
                    "success": bool,
                    "response": dict or None,  # Genie response if success
                    "error": str or None,      # Error message if failed
                    "attempts": int,           # Number of attempts made
                    "duration": float          # Time taken in seconds
                }
        """
        total = len(benchmarks)
        logger.info(f"Starting batch Genie calls for {total} questions")

        # Check circuit breaker
        if self.circuit_state == CircuitState.OPEN:
            if self._should_close_circuit():
                logger.info("Circuit breaker: Attempting to recover (HALF_OPEN)")
                self.circuit_state = CircuitState.HALF_OPEN
            elif self.fallback_to_sequential:
                logger.warning("Circuit breaker OPEN - falling back to sequential mode")
                return await self._sequential_fallback(benchmarks)
            else:
                logger.error("Circuit breaker OPEN - aborting batch operation")
                return self._create_circuit_open_responses(benchmarks)

        # Execute batch with safety measures
        start_time = time.time()

        tasks = [
            self._ask_with_safety(i, benchmark)
            for i, benchmark in enumerate(benchmarks)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and update circuit breaker
        processed_results = []
        success_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Exception not caught by safety wrapper
                processed_results.append({
                    "benchmark_id": benchmarks[i].get("id", f"benchmark_{i}"),
                    "question": benchmarks[i]["question"],
                    "success": False,
                    "response": None,
                    "error": f"Unhandled exception: {str(result)}",
                    "attempts": 1,
                    "duration": 0
                })
                self._record_failure()
            else:
                processed_results.append(result)
                if result["success"]:
                    success_count += 1
                    self._record_success()
                else:
                    self._record_failure()

        duration = time.time() - start_time

        logger.info(f"Batch complete: {success_count}/{total} succeeded in {duration:.1f}s "
                   f"(circuit: {self.circuit_state.value})")

        return processed_results

    async def _ask_with_safety(self, index: int, benchmark: Dict) -> Dict:
        """
        Ask Genie with safety measures: semaphore, retry, timeout.

        Args:
            index: Index in batch
            benchmark: Benchmark dict

        Returns:
            Response dict
        """
        benchmark_id = benchmark.get("id", f"benchmark_{index}")
        question = benchmark["question"]

        # Acquire semaphore (limit concurrent calls)
        async with self.semaphore:
            logger.debug(f"[{index}] Acquired slot for: {question[:50]}...")

            # Retry loop
            for attempt in range(1, self.retry_attempts + 1):
                try:
                    start_time = time.time()

                    # Call Genie with timeout
                    response = await asyncio.wait_for(
                        self._call_genie_async(question),
                        timeout=self.query_timeout
                    )

                    duration = time.time() - start_time

                    logger.info(f"[{index}] ✅ Success in {duration:.1f}s (attempt {attempt})")

                    return {
                        "benchmark_id": benchmark_id,
                        "question": question,
                        "success": True,
                        "response": response,
                        "error": None,
                        "attempts": attempt,
                        "duration": duration
                    }

                except asyncio.TimeoutError:
                    logger.warning(f"[{index}] ⏱️ Timeout after {self.query_timeout}s (attempt {attempt})")
                    error = f"Timeout after {self.query_timeout}s"

                except Exception as e:
                    logger.warning(f"[{index}] ❌ Error: {str(e)} (attempt {attempt})")
                    error = str(e)

                # Retry with exponential backoff
                if attempt < self.retry_attempts:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"[{index}] Retrying in {delay}s...")
                    await asyncio.sleep(delay)

            # All attempts failed
            logger.error(f"[{index}] ❌ Failed after {self.retry_attempts} attempts")

            return {
                "benchmark_id": benchmark_id,
                "question": question,
                "success": False,
                "response": None,
                "error": error,
                "attempts": self.retry_attempts,
                "duration": 0
            }

    async def _call_genie_async(self, question: str) -> Dict:
        """
        Async wrapper for Genie client call.

        Args:
            question: Question to ask

        Returns:
            Genie response dict
        """
        # If genie_client.ask is sync, run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.genie_client.ask(question, timeout=self.query_timeout)
        )

    def _record_success(self):
        """Record successful call for circuit breaker."""
        if self.circuit_state == CircuitState.HALF_OPEN:
            # Recovered! Close circuit
            logger.info("Circuit breaker: Service recovered (CLOSED)")
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.circuit_state == CircuitState.CLOSED:
            # Decay failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    def _record_failure(self):
        """Record failed call for circuit breaker."""
        self.failure_count += 1

        if self.failure_count >= self.circuit_breaker_threshold:
            if self.circuit_state == CircuitState.CLOSED:
                logger.error(f"Circuit breaker: Too many failures ({self.failure_count}) - OPENING circuit")
                self.circuit_state = CircuitState.OPEN
                self.circuit_open_time = time.time()
            elif self.circuit_state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker: Still failing - back to OPEN")
                self.circuit_state = CircuitState.OPEN
                self.circuit_open_time = time.time()

    def _should_close_circuit(self) -> bool:
        """Check if enough time has passed to try closing circuit."""
        if self.circuit_open_time is None:
            return False

        elapsed = time.time() - self.circuit_open_time
        return elapsed >= self.circuit_breaker_timeout

    async def _sequential_fallback(self, benchmarks: List[Dict]) -> List[Dict]:
        """
        Fallback to sequential mode when circuit is open.

        Args:
            benchmarks: List of benchmarks

        Returns:
            List of response dicts
        """
        logger.info("Executing in SEQUENTIAL fallback mode")
        results = []

        for i, benchmark in enumerate(benchmarks):
            logger.info(f"[{i+1}/{len(benchmarks)}] Sequential call...")

            # Reset circuit for this attempt
            old_state = self.circuit_state
            self.circuit_state = CircuitState.HALF_OPEN

            result = await self._ask_with_safety(i, benchmark)
            results.append(result)

            # Restore circuit state if still failing
            if not result["success"]:
                self.circuit_state = old_state

            # Delay between calls
            if i < len(benchmarks) - 1:
                await asyncio.sleep(3)

        return results

    def _create_circuit_open_responses(self, benchmarks: List[Dict]) -> List[Dict]:
        """
        Create error responses for all benchmarks when circuit is open.

        Args:
            benchmarks: List of benchmarks

        Returns:
            List of error response dicts
        """
        return [
            {
                "benchmark_id": b.get("id", f"benchmark_{i}"),
                "question": b["question"],
                "success": False,
                "response": None,
                "error": "Circuit breaker OPEN - Genie API unavailable",
                "attempts": 0,
                "duration": 0
            }
            for i, b in enumerate(benchmarks)
        ]


# Synchronous wrapper for compatibility
class SyncBatchGenieClient:
    """Synchronous wrapper for BatchGenieClient."""

    def __init__(self, genie_client, config: Optional[Dict] = None):
        self.batch_client = BatchGenieClient(genie_client, config)

    def batch_ask(self, benchmarks: List[Dict]) -> List[Dict]:
        """Synchronous batch_ask using asyncio.run."""
        return asyncio.run(self.batch_client.batch_ask(benchmarks))
