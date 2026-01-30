"""
Batch Fix Applier

Applies ALL fixes at once in a single Genie Space update.
No sequential one-at-a-time - batch application only.
"""

import json
import copy
import uuid
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BatchApplier:
    """
    Applies all fixes in one batch update to Genie Space.

    Fix application order within batch:
    1. Metric Views (create in Unity Catalog first)
    2. Metadata (table/column descriptions, synonyms)
    3. Sample Queries
    4. Instructions
    """

    FIX_ORDER = ["metric_view", "metadata", "sample_query", "instruction"]

    def __init__(self, space_api, sql_executor=None, config: Dict = None):
        """
        Initialize batch applier.

        Args:
            space_api: Space API client for import/export
            sql_executor: SQL executor for metric views (optional)
            config: Configuration options
                - metric_view_prefix: Prefix for metric view names
                - default_catalog: Default catalog for metric views
                - default_schema: Default schema for metric views
        """
        self.space_api = space_api
        self.sql_executor = sql_executor
        self.config = config or {}

        self.metric_view_prefix = self.config.get("metric_view_prefix", "mv_")
        self.default_catalog = self.config.get("catalog", "")
        self.default_schema = self.config.get("schema", "")

    def apply_all(
        self,
        space_id: str,
        grouped_fixes: Dict[str, List[Dict]],
        dry_run: bool = False
    ) -> Dict:
        """
        Apply ALL fixes in one batch update.

        Args:
            space_id: Genie Space ID
            grouped_fixes: Fixes grouped by category
            dry_run: If True, don't actually apply changes

        Returns:
            {
                "success": bool,
                "applied": List[Dict],  # Successfully applied fixes
                "failed": List[Dict],   # Failed to apply
                "config_before": Dict,
                "config_after": Dict
            }
        """
        logger.info("=" * 80)
        logger.info("Batch Fix Application")
        logger.info("=" * 80)

        # Load current config
        logger.info("Loading current space configuration...")
        config_before = self.space_api.export_space(space_id)
        config_after = copy.deepcopy(config_before)

        applied = []
        failed = []

        # Apply fixes in order
        for category in self.FIX_ORDER:
            fixes = grouped_fixes.get(category, [])
            if not fixes:
                continue

            logger.info(f"\nApplying {len(fixes)} {category} fixes...")

            for fix in fixes:
                fix_type = fix.get("type", "unknown")
                try:
                    success = self._apply_fix(config_after, fix)
                    if success:
                        applied.append({**fix, "_category": category})
                        logger.info(f"  ✓ {fix_type}")
                    else:
                        failed.append({**fix, "_category": category, "error": "Apply returned False"})
                        logger.warning(f"  ✗ {fix_type}: Apply failed")
                except Exception as e:
                    failed.append({**fix, "_category": category, "error": str(e)})
                    logger.error(f"  ✗ {fix_type}: {e}")

        # Update space (single API call)
        if applied and not dry_run:
            logger.info(f"\nUpdating Genie Space with {len(applied)} changes...")
            try:
                self.space_api.update_space(space_id, config_after)
                logger.info("✅ Genie Space updated successfully")
            except Exception as e:
                logger.error(f"❌ Failed to update space: {e}")
                return {
                    "success": False,
                    "applied": [],
                    "failed": applied + failed,
                    "config_before": config_before,
                    "config_after": config_before,
                    "error": str(e)
                }
        elif dry_run:
            logger.info(f"\n[DRY RUN] Would apply {len(applied)} changes")
        else:
            logger.info("\nNo changes to apply")

        # Summary
        logger.info("=" * 80)
        logger.info(f"Applied: {len(applied)} | Failed: {len(failed)}")
        logger.info("=" * 80)

        return {
            "success": True,
            "applied": applied,
            "failed": failed,
            "config_before": config_before,
            "config_after": config_after if not dry_run else config_before
        }

    def _apply_fix(self, config: Dict, fix: Dict) -> bool:
        """Apply a single fix to the configuration (in memory)."""
        fix_type = fix.get("type", "")

        if fix_type == "add_synonym":
            return self._add_synonym(config, fix)
        elif fix_type == "delete_synonym":
            return self._delete_synonym(config, fix)
        elif fix_type == "add_column_description":
            return self._add_column_description(config, fix)
        elif fix_type == "add_table_description":
            return self._add_table_description(config, fix)
        elif fix_type == "add_example_query":
            return self._add_example_query(config, fix)
        elif fix_type == "delete_example_query":
            return self._delete_example_query(config, fix)
        elif fix_type == "create_metric_view":
            return self._create_metric_view(config, fix)
        elif fix_type == "delete_metric_view":
            return self._delete_metric_view(config, fix)
        elif fix_type == "update_text_instruction":
            return self._update_text_instruction(config, fix)
        else:
            logger.warning(f"Unknown fix type: {fix_type}")
            return False

    # =========================================================================
    # Fix Application Methods
    # =========================================================================

    def _add_synonym(self, config: Dict, fix: Dict) -> bool:
        """Add synonym to a column."""
        table_id = fix.get("table")
        column_name = fix.get("column")
        synonym = fix.get("synonym")

        if not all([table_id, column_name, synonym]):
            return False

        tables = config.setdefault("data_sources", {}).setdefault("tables", [])
        for table in tables:
            if table.get("identifier") == table_id:
                column_configs = table.setdefault("column_configs", [])
                column_config = next(
                    (c for c in column_configs if c.get("column_name") == column_name),
                    None
                )
                if not column_config:
                    column_config = {"column_name": column_name}
                    column_configs.append(column_config)

                synonyms = column_config.setdefault("synonyms", [])
                if synonym not in synonyms:
                    synonyms.append(synonym)
                return True
        return False

    def _delete_synonym(self, config: Dict, fix: Dict) -> bool:
        """Delete synonym from a column."""
        table_id = fix.get("table")
        column_name = fix.get("column")
        synonym = fix.get("synonym")

        tables = config.get("data_sources", {}).get("tables", [])
        for table in tables:
            if table.get("identifier") == table_id:
                column_configs = table.get("column_configs", [])
                for col in column_configs:
                    if col.get("column_name") == column_name:
                        synonyms = col.get("synonyms", [])
                        if synonym in synonyms:
                            synonyms.remove(synonym)
                            return True
        return False

    def _add_column_description(self, config: Dict, fix: Dict) -> bool:
        """Add or update column description."""
        table_id = fix.get("table")
        column_name = fix.get("column")
        description = fix.get("description")

        if not all([table_id, column_name, description]):
            return False

        tables = config.setdefault("data_sources", {}).setdefault("tables", [])
        for table in tables:
            if table.get("identifier") == table_id:
                column_configs = table.setdefault("column_configs", [])
                column_config = next(
                    (c for c in column_configs if c.get("column_name") == column_name),
                    None
                )
                if not column_config:
                    column_config = {"column_name": column_name}
                    column_configs.append(column_config)

                column_config["description"] = [description] if isinstance(description, str) else description
                return True
        return False

    def _add_table_description(self, config: Dict, fix: Dict) -> bool:
        """Add or update table description."""
        table_id = fix.get("table")
        description = fix.get("description")

        if not all([table_id, description]):
            return False

        tables = config.setdefault("data_sources", {}).setdefault("tables", [])
        for table in tables:
            if table.get("identifier") == table_id:
                table["description"] = [description] if isinstance(description, str) else description
                return True
        return False

    def _add_example_query(self, config: Dict, fix: Dict) -> bool:
        """Add example query."""
        instructions = config.setdefault("instructions", {})
        example_sqls = instructions.setdefault("example_question_sqls", [])

        example = {
            "id": uuid.uuid4().hex,
            "question": fix.get("question", []),
            "sql": fix.get("sql", ""),
            "parameters": fix.get("parameters", []),
            "usage_guidance": fix.get("usage_guidance", [])
        }

        example_sqls.append(example)
        return True

    def _delete_example_query(self, config: Dict, fix: Dict) -> bool:
        """Delete example query by pattern name."""
        pattern_name = fix.get("pattern_name")
        if not pattern_name:
            return False

        instructions = config.get("instructions", {})
        example_sqls = instructions.get("example_question_sqls", [])

        for i, example in enumerate(example_sqls):
            question = example.get("question", [])
            question_text = question[0] if isinstance(question, list) and question else str(question)
            if pattern_name in question_text or example.get("id") == pattern_name:
                example_sqls.pop(i)
                return True
        return False

    def _create_metric_view(self, config: Dict, fix: Dict) -> bool:
        """Create metric view in Unity Catalog and add to config."""
        import yaml

        base_name = fix.get("metric_view_name", "")
        catalog = fix.get("catalog") or self.default_catalog
        schema = fix.get("schema") or self.default_schema

        if not base_name.startswith(self.metric_view_prefix):
            metric_view_name = f"{self.metric_view_prefix}{base_name}"
        else:
            metric_view_name = base_name

        fqn = f"{catalog}.{schema}.{metric_view_name}"

        # Create in Unity Catalog if executor available
        if self.sql_executor:
            yaml_definition = fix.get("yaml_definition", {})
            source_table = fix.get("source_table")

            yaml_dict = {"version": 1.1}
            if fix.get("table_description"):
                desc = fix["table_description"]
                yaml_dict["comment"] = desc if isinstance(desc, str) else desc[0]
            if source_table:
                yaml_dict["source"] = source_table
            if yaml_definition.get("dimensions"):
                yaml_dict["dimensions"] = yaml_definition["dimensions"]
            if yaml_definition.get("measures"):
                yaml_dict["measures"] = yaml_definition["measures"]

            yaml_str = yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False, indent=2)

            create_sql = f"""CREATE OR REPLACE VIEW {fqn}
WITH METRICS
LANGUAGE YAML
AS $$
{yaml_str}$$"""

            try:
                result = self.sql_executor.execute(create_sql, timeout=120)
                if result.get("status") != "SUCCEEDED":
                    logger.warning(f"Metric view SQL failed: {result.get('error')}")
            except Exception as e:
                logger.warning(f"Could not create metric view in UC: {e}")

        # Add to Genie Space config
        tables = config.setdefault("data_sources", {}).setdefault("tables", [])

        # Remove if exists
        tables[:] = [t for t in tables if t.get("identifier") != fqn]

        metric_view_table = {
            "identifier": fqn,
            "column_configs": []
        }

        if fix.get("table_description"):
            desc = fix["table_description"]
            metric_view_table["description"] = [desc] if isinstance(desc, str) else desc

        tables.append(metric_view_table)
        return True

    def _delete_metric_view(self, config: Dict, fix: Dict) -> bool:
        """Remove metric view from configuration."""
        metric_view_name = fix.get("metric_view_name")
        if not metric_view_name:
            return False

        tables = config.get("data_sources", {}).get("tables", [])
        for i, table in enumerate(tables):
            if table.get("identifier") == metric_view_name:
                tables.pop(i)
                return True
        return False

    def _update_text_instruction(self, config: Dict, fix: Dict) -> bool:
        """Update text instruction."""
        content = fix.get("content", [])
        if not content:
            return False

        instructions = config.setdefault("instructions", {})
        text_instructions = instructions.setdefault("text_instructions", [])

        if text_instructions:
            text_instructions[0]["content"] = content
        else:
            text_instructions.append({
                "id": uuid.uuid4().hex,
                "content": content
            })
        return True
