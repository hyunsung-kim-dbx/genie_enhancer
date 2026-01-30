-- ================================================================
-- Genie Enhancement Tracking - Delta Table Schemas
-- ================================================================
-- Purpose: Track enhancement iterations, changes, and results
--          Optimized for Databricks Apps dashboards and SQL queries
-- ================================================================
--
-- ✅ TEMPLATE FILE - Values from app.yaml
--
-- This file uses template variables:
--   ${CATALOG} - Reads from app.yaml env.CATALOG
--   ${SCHEMA}  - Reads from app.yaml env.SCHEMA
--
-- To generate actual SQL:
--   python3 schema/setup_delta_tables.py
--   (Reads app.yaml and creates executable SQL)
-- ================================================================

-- ----------------------------------------------------------------
-- Table 1: enhancement_runs
-- ----------------------------------------------------------------
-- Tracks each complete enhancement job run
-- One row per job execution
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${CATALOG}.${SCHEMA}.enhancement_runs (
  -- Primary Key
  run_id STRING NOT NULL COMMENT 'Unique identifier for this enhancement run (UUID)',

  -- Job Metadata
  space_id STRING NOT NULL COMMENT 'Genie Space ID being enhanced',
  space_name STRING COMMENT 'Human-readable space name',
  started_at TIMESTAMP NOT NULL COMMENT 'When enhancement started',
  completed_at TIMESTAMP COMMENT 'When enhancement completed (NULL if running)',
  status STRING NOT NULL COMMENT 'RUNNING | COMPLETED | FAILED | STOPPED',

  -- Configuration
  target_score DOUBLE NOT NULL COMMENT 'Target benchmark pass rate (0.0-1.0)',
  max_iterations INT NOT NULL COMMENT 'Maximum iterations configured',
  llm_endpoint STRING NOT NULL COMMENT 'LLM endpoint used',
  benchmark_source STRING COMMENT 'Path to benchmark file',

  -- Results Summary
  initial_score DOUBLE COMMENT 'Score at start (0.0-1.0)',
  final_score DOUBLE COMMENT 'Score at end (0.0-1.0)',
  score_improvement DOUBLE COMMENT 'final_score - initial_score',
  iterations_completed INT COMMENT 'Number of iterations actually run',
  total_changes_applied INT COMMENT 'Total fixes applied across all iterations',

  -- Operational
  duration_seconds DOUBLE COMMENT 'Total run duration',
  error_message STRING COMMENT 'Error details if status=FAILED',
  triggered_by STRING COMMENT 'User or service principal that started run',

  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Top-level tracking of enhancement job runs'
PARTITIONED BY (DATE(started_at));

-- ----------------------------------------------------------------
-- Table 2: enhancement_iterations
-- ----------------------------------------------------------------
-- Tracks each iteration within a run
-- Multiple rows per run_id
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${CATALOG}.${SCHEMA}.enhancement_iterations (
  -- Composite Key
  run_id STRING NOT NULL COMMENT 'Links to enhancement_runs.run_id',
  iteration_number INT NOT NULL COMMENT 'Iteration sequence (1, 2, 3...)',

  -- Timing
  started_at TIMESTAMP NOT NULL COMMENT 'When iteration started',
  completed_at TIMESTAMP COMMENT 'When iteration completed',
  duration_seconds DOUBLE COMMENT 'Iteration duration',

  -- Scoring
  score DOUBLE NOT NULL COMMENT 'Benchmark pass rate (0.0-1.0)',
  score_delta DOUBLE COMMENT 'Change from previous iteration',
  total_benchmarks INT NOT NULL COMMENT 'Total benchmarks tested',
  passed INT NOT NULL COMMENT 'Number passed',
  failed INT NOT NULL COMMENT 'Number failed',

  -- Changes Applied
  num_changes INT NOT NULL COMMENT 'Number of fixes applied this iteration',
  changes_by_type MAP<STRING, INT> COMMENT 'Count by fix type: {add_synonym: 5, add_join: 2}',

  -- Failure Analysis
  failures_by_category MAP<STRING, INT> COMMENT '{missing_table: 3, wrong_join: 2, ...}',
  top_failure_category STRING COMMENT 'Most common failure category',

  -- LLM Usage
  llm_calls INT COMMENT 'Number of LLM API calls',
  llm_tokens_used INT COMMENT 'Total tokens consumed',
  llm_cost_estimate DOUBLE COMMENT 'Estimated cost in USD',

  -- State Management
  config_snapshot_path STRING COMMENT 'DBFS/S3 path to Genie config JSON snapshot',
  can_rollback BOOLEAN COMMENT 'Whether rollback to this iteration is possible',

  -- Status
  status STRING NOT NULL COMMENT 'COMPLETED | FAILED | SKIPPED',
  error_message STRING COMMENT 'Error details if failed',

  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Detailed iteration-level tracking'
PARTITIONED BY (run_id);

-- ----------------------------------------------------------------
-- Table 3: enhancement_changes
-- ----------------------------------------------------------------
-- Exploded view of individual changes/fixes
-- Enables querying "which tables got synonyms added?"
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${CATALOG}.${SCHEMA}.enhancement_changes (
  -- Links
  run_id STRING NOT NULL COMMENT 'Links to enhancement_runs.run_id',
  iteration_number INT NOT NULL COMMENT 'Links to enhancement_iterations.iteration_number',
  change_id STRING NOT NULL COMMENT 'Unique ID for this change (UUID)',

  -- Change Details
  change_type STRING NOT NULL COMMENT 'add_synonym | add_join | add_column_description | ...',
  target_table STRING COMMENT 'Fully qualified table name affected',
  target_column STRING COMMENT 'Column name (if applicable)',

  -- Change Content (denormalized for easy querying)
  change_value STRING COMMENT 'E.g., synonym text, description text',
  change_details MAP<STRING, STRING> COMMENT 'Full change details as key-value pairs',

  -- Context
  source_failure_benchmark_id STRING COMMENT 'Which benchmark failure triggered this fix',
  source_failure_question STRING COMMENT 'The question that failed',

  -- Success Tracking
  applied_successfully BOOLEAN COMMENT 'Whether change was applied without error',
  validation_status STRING COMMENT 'valid | invalid | skipped',
  error_message STRING COMMENT 'Error if application failed',

  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Individual changes/fixes applied during enhancement'
PARTITIONED BY (run_id, change_type);

-- ----------------------------------------------------------------
-- Table 4: enhancement_benchmarks
-- ----------------------------------------------------------------
-- Per-benchmark results for each iteration
-- Enables tracking "which benchmarks consistently fail?"
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${CATALOG}.${SCHEMA}.enhancement_benchmarks (
  -- Links
  run_id STRING NOT NULL COMMENT 'Links to enhancement_runs.run_id',
  iteration_number INT NOT NULL COMMENT 'Links to enhancement_iterations.iteration_number',

  -- Benchmark Identity
  benchmark_id STRING NOT NULL COMMENT 'Unique benchmark identifier',
  question STRING NOT NULL COMMENT 'The question asked',
  expected_sql STRING COMMENT 'Expected SQL query',

  -- Results
  passed BOOLEAN NOT NULL COMMENT 'Whether benchmark passed',
  genie_sql STRING COMMENT 'SQL generated by Genie',
  genie_status STRING COMMENT 'COMPLETED | FAILED | TIMEOUT',

  -- Failure Analysis
  failure_category STRING COMMENT 'missing_table | wrong_join | semantic_difference | ...',
  failure_reason STRING COMMENT 'Detailed failure explanation',

  -- Comparison Details
  comparison_confidence STRING COMMENT 'high | medium | low',
  semantic_equivalence STRING COMMENT 'LLM judge assessment',

  -- Performance
  response_time_seconds DOUBLE COMMENT 'How long Genie took to respond',

  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Per-benchmark test results for detailed analysis'
PARTITIONED BY (run_id, passed);

-- ----------------------------------------------------------------
-- Table 5: enhancement_lessons_learned
-- ----------------------------------------------------------------
-- Track lessons learned in structured format
-- Complements markdown export with queryable data
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${CATALOG}.${SCHEMA}.enhancement_lessons_learned (
  -- Identity
  lesson_id STRING NOT NULL COMMENT 'Unique lesson identifier (UUID)',

  -- Context
  run_id STRING COMMENT 'Run where lesson was learned (NULL for manual entries)',
  iteration_number INT COMMENT 'Specific iteration',

  -- Lesson Content
  pattern STRING NOT NULL COMMENT 'E.g., "missing_synonym_for_date_columns"',
  description STRING NOT NULL COMMENT 'What was learned',
  fix_type STRING COMMENT 'Which fix type resolves this',

  -- Evidence
  example_question STRING COMMENT 'Example question that triggered this lesson',
  before_sql STRING COMMENT 'What Genie generated before fix',
  after_sql STRING COMMENT 'What Genie generated after fix',

  -- Effectiveness
  times_encountered INT DEFAULT 1 COMMENT 'How many times this pattern seen',
  success_rate DOUBLE COMMENT 'How often this fix works (0.0-1.0)',

  -- Lifecycle
  status STRING DEFAULT 'active' COMMENT 'active | deprecated | superseded',
  superseded_by STRING COMMENT 'Lesson ID that replaces this one',

  -- Audit
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  created_by STRING COMMENT 'System or user who recorded lesson'
)
USING DELTA
COMMENT 'Lessons learned from enhancement iterations';

-- ================================================================
-- Views for Databricks Apps Dashboards
-- ================================================================

-- ----------------------------------------------------------------
-- View: Current Enhancement Progress
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW ${CATALOG}.${SCHEMA}.vw_current_progress AS
SELECT
  r.run_id,
  r.space_name,
  r.status,
  r.started_at,
  r.initial_score,
  i.score AS current_score,
  r.target_score,
  i.iteration_number AS current_iteration,
  r.max_iterations,
  (i.score - r.initial_score) AS score_improvement,
  CASE
    WHEN i.score >= r.target_score THEN 'Target Reached ✅'
    WHEN i.iteration_number >= r.max_iterations THEN 'Max Iterations'
    WHEN r.status = 'RUNNING' THEN 'In Progress...'
    ELSE r.status
  END AS progress_status,
  i.num_changes AS changes_this_iteration,
  r.total_changes_applied,
  TIMESTAMPDIFF(MINUTE, r.started_at, COALESCE(r.completed_at, CURRENT_TIMESTAMP())) AS duration_minutes
FROM ${CATALOG}.${SCHEMA}.enhancement_runs r
LEFT JOIN ${CATALOG}.${SCHEMA}.enhancement_iterations i
  ON r.run_id = i.run_id
  AND i.iteration_number = (
    SELECT MAX(iteration_number)
    FROM ${CATALOG}.${SCHEMA}.enhancement_iterations
    WHERE run_id = r.run_id
  )
WHERE r.status IN ('RUNNING', 'COMPLETED')
ORDER BY r.started_at DESC;

-- ----------------------------------------------------------------
-- View: Change Type Distribution
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW ${CATALOG}.${SCHEMA}.vw_change_distribution AS
SELECT
  run_id,
  change_type,
  COUNT(*) AS num_changes,
  COUNT(DISTINCT target_table) AS tables_affected,
  AVG(CASE WHEN applied_successfully THEN 1.0 ELSE 0.0 END) AS success_rate
FROM ${CATALOG}.${SCHEMA}.enhancement_changes
GROUP BY run_id, change_type
ORDER BY run_id, num_changes DESC;

-- ----------------------------------------------------------------
-- View: Failure Patterns
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW ${CATALOG}.${SCHEMA}.vw_failure_patterns AS
SELECT
  run_id,
  iteration_number,
  failure_category,
  COUNT(*) AS occurrence_count,
  COLLECT_LIST(question) AS example_questions
FROM ${CATALOG}.${SCHEMA}.enhancement_benchmarks
WHERE NOT passed
GROUP BY run_id, iteration_number, failure_category
ORDER BY run_id, iteration_number, occurrence_count DESC;

-- ----------------------------------------------------------------
-- View: Rollback Points
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW ${CATALOG}.${SCHEMA}.vw_rollback_points AS
SELECT
  run_id,
  iteration_number,
  score,
  num_changes,
  config_snapshot_path,
  started_at,
  'Iteration ' || iteration_number || ': Score ' || ROUND(score * 100, 1) || '%' AS rollback_label
FROM ${CATALOG}.${SCHEMA}.enhancement_iterations
WHERE can_rollback = TRUE
  AND status = 'COMPLETED'
ORDER BY run_id, iteration_number DESC;

-- ================================================================
-- Indexes for Query Performance
-- ================================================================

-- Optimize common queries
OPTIMIZE ${CATALOG}.${SCHEMA}.enhancement_runs;
OPTIMIZE ${CATALOG}.${SCHEMA}.enhancement_iterations;
OPTIMIZE ${CATALOG}.${SCHEMA}.enhancement_changes;
OPTIMIZE ${CATALOG}.${SCHEMA}.enhancement_benchmarks;

-- Z-order for better performance
ALTER TABLE ${CATALOG}.${SCHEMA}.enhancement_runs ZORDER BY (space_id, status);
ALTER TABLE ${CATALOG}.${SCHEMA}.enhancement_iterations ZORDER BY (run_id, iteration_number);
ALTER TABLE ${CATALOG}.${SCHEMA}.enhancement_changes ZORDER BY (change_type, target_table);
ALTER TABLE ${CATALOG}.${SCHEMA}.enhancement_benchmarks ZORDER BY (passed, failure_category);

-- ================================================================
-- Sample Queries for Databricks Apps
-- ================================================================

-- Query 1: Latest run progress
-- SELECT * FROM ${CATALOG}.${SCHEMA}.vw_current_progress LIMIT 10;

-- Query 2: What changes were made in iteration 3 of run X?
-- SELECT change_type, target_table, target_column, change_value
-- FROM ${CATALOG}.${SCHEMA}.enhancement_changes
-- WHERE run_id = 'your-run-id' AND iteration_number = 3;

-- Query 3: Which benchmarks consistently fail?
-- SELECT benchmark_id, question, failure_category, COUNT(*) AS fail_count
-- FROM ${CATALOG}.${SCHEMA}.enhancement_benchmarks
-- WHERE NOT passed
-- GROUP BY benchmark_id, question, failure_category
-- HAVING COUNT(*) >= 3
-- ORDER BY fail_count DESC;

-- Query 4: Score trend across iterations
-- SELECT iteration_number, score, score_delta, num_changes
-- FROM ${CATALOG}.${SCHEMA}.enhancement_iterations
-- WHERE run_id = 'your-run-id'
-- ORDER BY iteration_number;

-- Query 5: Which tables got the most changes?
-- SELECT target_table, COUNT(*) AS change_count,
--        COUNT(DISTINCT change_type) AS change_types
-- FROM ${CATALOG}.${SCHEMA}.enhancement_changes
-- WHERE run_id = 'your-run-id'
-- GROUP BY target_table
-- ORDER BY change_count DESC;