"""
Enhancement Planner

Analyzes benchmark failures and generates ALL fixes at once.
No sequential application - just planning.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class EnhancementPlanner:
    """
    Analyzes failures and generates enhancement fixes.

    Produces a complete fix plan for batch application.
    Four fix categories:
    1. Metric Views (create/delete)
    2. Metadata (table/column descriptions, synonyms)
    3. Sample Queries (parameterized templates)
    4. Instructions (text instructions)
    """

    FIX_CATEGORIES = ["metric_view", "metadata", "sample_query", "instruction"]

    def __init__(self, llm_client, prompts_dir: Path = None):
        """
        Initialize enhancement planner.

        Args:
            llm_client: LLM client for generating fixes
            prompts_dir: Directory containing prompt templates
        """
        self.llm_client = llm_client

        # Load prompts
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"

        self.prompts = {}
        for category in self.FIX_CATEGORIES:
            prompt_file = prompts_dir / f"{category}_analysis.txt"
            if prompt_file.exists():
                self.prompts[category] = prompt_file.read_text()
            else:
                logger.warning(f"Prompt file not found: {prompt_file}")
                self.prompts[category] = ""

    def generate_plan(
        self,
        failed_benchmarks: List[Dict],
        space_config: Dict,
        parallel_workers: int = 1
    ) -> Dict[str, List[Dict]]:
        """
        Generate ALL fixes for failed benchmarks.

        Args:
            failed_benchmarks: List of failed benchmark results
            space_config: Current Genie Space configuration
            parallel_workers: Number of parallel LLM calls

        Returns:
            {
                "metric_view": [fix1, fix2, ...],
                "metadata": [fix1, fix2, ...],
                "sample_query": [fix1, fix2, ...],
                "instruction": [fix1, fix2, ...]
            }
        """
        logger.info("=" * 80)
        logger.info("Generating Enhancement Plan")
        logger.info("=" * 80)

        grouped_fixes = {category: [] for category in self.FIX_CATEGORIES}
        total_tasks = len(failed_benchmarks) * len(self.FIX_CATEGORIES)

        logger.info(f"Analyzing {len(failed_benchmarks)} failures")
        logger.info(f"Total LLM calls: {total_tasks} ({parallel_workers} parallel)")

        # Build task list
        tasks = []
        for i, failure in enumerate(failed_benchmarks):
            for category in self.FIX_CATEGORIES:
                tasks.append((i, failure, category))

        # Run analysis in parallel
        def analyze_task(task):
            idx, failure, category = task
            try:
                fixes = self._analyze_failure(failure, space_config, category)
                return category, fixes or [], failure
            except Exception as e:
                logger.error(f"Error analyzing {category}: {e}")
                return category, [], failure

        completed = 0
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            futures = {executor.submit(analyze_task, task): task for task in tasks}

            for future in as_completed(futures):
                category, fixes, failure = future.result()
                completed += 1

                if fixes:
                    for fix in fixes:
                        fix["source_failure"] = {
                            "benchmark_id": failure.get("benchmark_id"),
                            "question": failure.get("question"),
                            "failure_category": failure.get("failure_category")
                        }
                    grouped_fixes[category].extend(fixes)

                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{total_tasks}")

        # Deduplicate
        for category in self.FIX_CATEGORIES:
            grouped_fixes[category] = self._deduplicate_fixes(grouped_fixes[category])

        # Summary
        logger.info("=" * 80)
        logger.info("Enhancement Plan Complete")
        logger.info("=" * 80)
        total = 0
        for category, fixes in grouped_fixes.items():
            count = len(fixes)
            total += count
            if count > 0:
                logger.info(f"  {category}: {count} fixes")
        logger.info(f"  TOTAL: {total} fixes")

        return grouped_fixes

    def _analyze_failure(
        self,
        failure: Dict,
        space_config: Dict,
        category: str
    ) -> List[Dict]:
        """Analyze a single failure for one fix category."""
        prompt_template = self.prompts.get(category, "")
        if not prompt_template:
            return []

        prompt = prompt_template.format(
            question=failure.get("question", ""),
            expected_sql=failure.get("expected_sql", ""),
            genie_sql=failure.get("genie_sql") or "None (Genie did not generate SQL)",
            space_config=json.dumps(space_config, indent=2)
        )

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )
            analysis = self._parse_llm_response(response)
            return analysis.get("recommended_fixes", [])
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return []

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response."""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"recommended_fixes": []}

    def _deduplicate_fixes(self, fixes: List[Dict]) -> List[Dict]:
        """Remove duplicate fixes."""
        seen = set()
        unique = []

        for fix in fixes:
            fix_type = fix.get("type", "")

            if fix_type == "add_synonym":
                key = (fix_type, fix.get("table"), fix.get("column"), fix.get("synonym"))
            elif fix_type == "delete_synonym":
                key = (fix_type, fix.get("table"), fix.get("column"), fix.get("synonym"))
            elif fix_type == "add_column_description":
                key = (fix_type, fix.get("table"), fix.get("column"))
            elif fix_type == "add_table_description":
                key = (fix_type, fix.get("table"))
            elif fix_type == "add_example_query":
                key = (fix_type, fix.get("pattern_name"))
            elif fix_type == "delete_example_query":
                key = (fix_type, fix.get("pattern_name"))
            elif fix_type == "create_metric_view":
                key = (fix_type, fix.get("metric_view_name"))
            elif fix_type == "delete_metric_view":
                key = (fix_type, fix.get("metric_view_name"))
            elif fix_type == "update_text_instruction":
                key = (fix_type,)
            else:
                key = json.dumps(fix, sort_keys=True)

            if key not in seen:
                seen.add(key)
                unique.append(fix)

        return unique
