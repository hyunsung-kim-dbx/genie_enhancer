"""
Genie Enhancement Library v3.0

Batch-oriented enhancement with 4-stage Databricks Job support.

Modules:
- genie_client: Genie Conversational API
- space_api: Genie Space import/export
- scorer: Benchmark scoring with LLM judge
- enhancer: Fix generation (batch)
- applier: Fix application (batch)
- llm: Databricks LLM client
- sql: SQL executor
- state: Job state management (Delta tables)
"""

from lib.genie_client import GenieConversationalClient
from lib.space_api import SpaceUpdater
from lib.scorer import BenchmarkScorer
from lib.benchmark_parser import BenchmarkParser, BenchmarkLoader
from lib.llm import DatabricksLLMClient
from lib.sql import SQLExecutor
from lib.enhancer import EnhancementPlanner
from lib.applier import BatchApplier
from lib.state import JobState, get_job_state
from lib.reporter import ProgressReporter
from lib.space_cloner import SpaceCloner
from lib.sequential_enhancer import SequentialEnhancer

__all__ = [
    # API Clients
    "GenieConversationalClient",
    "SpaceUpdater",
    "DatabricksLLMClient",
    "SQLExecutor",
    # Scoring
    "BenchmarkScorer",
    "BenchmarkParser",
    "BenchmarkLoader",
    # Enhancement (Batch)
    "EnhancementPlanner",
    "BatchApplier",
    # Enhancement (Sequential)
    "SpaceCloner",
    "SequentialEnhancer",
    # State & Reporting
    "JobState",
    "get_job_state",
    "ProgressReporter",
]

__version__ = "3.0.0"
