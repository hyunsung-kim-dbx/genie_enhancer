#!/usr/bin/env python3
"""
Genie Space Enhancement CLI

Command-line interface for the Genie Space Enhancement System.
"""

import click
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from enhancer.api.genie_client import GenieConversationalClient
from enhancer.scoring.batch_scorer import BatchBenchmarkScorer
from enhancer.scoring.benchmark_parser import BenchmarkLoader
from enhancer.enhancement.category_enhancer import CategoryEnhancer
from enhancer.enhancement.applier import BatchApplier
from enhancer.llm.llm import DatabricksLLMClient
from enhancer.utils.sql import SQLExecutor
from enhancer.api.space_api import SpaceUpdater


@click.group()
def cli():
    """Genie Space Enhancement CLI"""
    pass


@cli.command()
@click.option('--host', required=True, help='Databricks workspace URL')
@click.option('--token', required=True, help='Databricks access token')
@click.option('--space-id', required=True, help='Genie Space ID')
@click.option('--warehouse-id', required=True, help='SQL Warehouse ID')
@click.option('--benchmarks', required=True, help='Path to benchmarks JSON file')
@click.option('--llm-endpoint', default='databricks-gpt-5-2', help='LLM endpoint')
def score(host, token, space_id, warehouse_id, benchmarks, llm_endpoint):
    """Score benchmarks against Genie Space."""
    click.echo(f"🎯 Scoring benchmarks from {benchmarks}")

    # Load benchmarks
    loader = BenchmarkLoader()
    benchmark_list = loader.load_benchmarks(benchmarks)
    click.echo(f"Loaded {len(benchmark_list)} benchmarks")

    # Initialize clients
    genie_client = GenieConversationalClient(host, token, space_id)
    llm_client = DatabricksLLMClient(host, token, llm_endpoint)
    sql_executor = SQLExecutor(host, token, warehouse_id)

    # Score
    scorer = BatchBenchmarkScorer(genie_client, llm_client, sql_executor)
    results = scorer.score(benchmark_list)

    click.echo(f"\n{'='*80}")
    click.echo(f"Score: {results['score']:.1%} ({results['passed']}/{results['total']})")
    click.echo(f"{'='*80}")

    # Save results
    output_path = Path("output/score_results.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    click.echo(f"\n✅ Results saved to {output_path}")


@cli.command()
@click.option('--host', required=True, help='Databricks workspace URL')
@click.option('--token', required=True, help='Databricks access token')
@click.option('--space-id', required=True, help='Genie Space ID')
@click.option('--failed-results', required=True, help='Path to failed results JSON')
@click.option('--llm-endpoint', default='databricks-gpt-5-2', help='LLM endpoint')
def plan(host, token, space_id, failed_results, llm_endpoint):
    """Generate enhancement plan from failed benchmarks."""
    click.echo(f"🔧 Generating enhancement plan")

    # Load failed results
    with open(failed_results) as f:
        data = json.load(f)
        failed_list = [r for r in data['results'] if not r['passed']]

    click.echo(f"Analyzing {len(failed_list)} failed benchmarks")

    # Initialize clients
    llm_client = DatabricksLLMClient(host, token, llm_endpoint)
    space_api = SpaceUpdater(host, token)

    # Get space config
    space_config = space_api.export_space(space_id)

    # Generate plan
    prompts_dir = Path(__file__).parent / "prompts"
    planner = CategoryEnhancer(llm_client, prompts_dir)
    grouped_fixes = planner.generate_plan(
        failed_benchmarks=failed_list,
        space_config=space_config
    )

    total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())
    click.echo(f"\n✅ Generated {total_fixes} fixes")

    # Save plan
    output_path = Path("output/enhancement_plan.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(grouped_fixes, f, indent=2)
    click.echo(f"Plan saved to {output_path}")


@cli.command()
@click.option('--host', required=True, help='Databricks workspace URL')
@click.option('--token', required=True, help='Databricks access token')
@click.option('--space-id', required=True, help='Genie Space ID')
@click.option('--warehouse-id', required=True, help='SQL Warehouse ID')
@click.option('--plan', required=True, help='Path to enhancement plan JSON')
@click.option('--dry-run', is_flag=True, help='Simulate without applying changes')
def apply(host, token, space_id, warehouse_id, plan, dry_run):
    """Apply enhancement fixes to Genie Space."""
    click.echo(f"🚀 Applying enhancements (dry_run={dry_run})")

    # Load plan
    with open(plan) as f:
        grouped_fixes = json.load(f)

    total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())
    click.echo(f"Applying {total_fixes} fixes")

    # Initialize clients
    space_api = SpaceUpdater(host, token)
    sql_executor = SQLExecutor(host, token, warehouse_id)

    # Apply fixes
    applier = BatchApplier(space_api, sql_executor)
    if dry_run:
        click.echo("✓ Dry run complete (no changes made)")
    else:
        result = applier.apply_all_fixes(space_id, grouped_fixes)
        click.echo(f"\n✅ Applied {result.get('applied_count', 0)} fixes")


@cli.command()
@click.option('--host', required=True, help='Databricks workspace URL')
@click.option('--token', required=True, help='Databricks access token')
@click.option('--space-id', required=True, help='Genie Space ID')
@click.option('--warehouse-id', required=True, help='SQL Warehouse ID')
@click.option('--benchmarks', required=True, help='Path to benchmarks JSON file')
@click.option('--initial-score', type=float, help='Initial score for comparison')
@click.option('--target-score', type=float, default=0.90, help='Target score threshold')
@click.option('--llm-endpoint', default='databricks-gpt-5-2', help='LLM endpoint')
def validate(host, token, space_id, warehouse_id, benchmarks, initial_score, target_score, llm_endpoint):
    """Validate enhancements by re-scoring benchmarks."""
    click.echo(f"✅ Validating enhancements")

    # Load benchmarks
    loader = BenchmarkLoader()
    benchmark_list = loader.load_benchmarks(benchmarks)

    # Initialize clients
    genie_client = GenieConversationalClient(host, token, space_id)
    llm_client = DatabricksLLMClient(host, token, llm_endpoint)
    sql_executor = SQLExecutor(host, token, warehouse_id)

    # Re-score
    scorer = BatchBenchmarkScorer(genie_client, llm_client, sql_executor)
    results = scorer.score(benchmark_list)

    new_score = results['score']
    improvement = new_score - initial_score if initial_score else 0
    target_reached = new_score >= target_score

    click.echo(f"\n{'='*80}")
    if initial_score:
        click.echo(f"Initial Score:  {initial_score:.1%}")
    click.echo(f"New Score:      {new_score:.1%}")
    if initial_score:
        click.echo(f"Improvement:    {improvement:+.1%}")
    click.echo(f"Target:         {target_score:.1%}")
    click.echo(f"Status:         {'✓ REACHED' if target_reached else '✗ NOT REACHED'}")
    click.echo(f"{'='*80}")

    # Save results
    output_path = Path("output/validation_results.json")
    with open(output_path, 'w') as f:
        json.dump({
            "initial_score": initial_score,
            "new_score": new_score,
            "improvement": improvement,
            "target_score": target_score,
            "target_reached": target_reached,
            "results": results
        }, f, indent=2)
    click.echo(f"\n✅ Results saved to {output_path}")


if __name__ == '__main__':
    cli()
