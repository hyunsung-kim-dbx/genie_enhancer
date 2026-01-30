"""
Genie Space Interactive Enhancement Tool V2

Three-Space Architecture with Sequential Fixes

Features:
- Three-space architecture (production, dev-best, dev-working)
- Sequential fix application with real-time progress
- Only 4 fix types (metric views, metadata, sample queries, instructions)
- User decides final promotion to production
"""

import streamlit as st
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.genie_client import GenieConversationalClient
from pipeline.space_updater import SpaceUpdater
from pipeline.benchmark_scorer import BenchmarkScorer
from pipeline.databricks_llm import DatabricksLLMClient
from pipeline.space_cloner import SpaceCloner
from pipeline.sequential_enhancer import SequentialEnhancer
from pipeline.sql_executor import SQLExecutor

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Genie Enhancement V2",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'step': 'upload',  # upload, configure, setup, analyze, running, complete
        'benchmarks': None,
        'config': None,
        'clients': None,
        # Three-space architecture
        'production_id': None,
        'dev_working_id': None,
        'dev_best_id': None,
        'production_name': None,
        'initial_config': None,
        # Scores
        'initial_score': 0.0,
        'current_score': 0.0,
        'best_score': 0.0,
        'scores_history': [],
        # Fixes
        'grouped_fixes': None,
        'current_phase': None,
        'current_fix_index': 0,
        'fixes_applied': [],
        'fixes_rejected': [],
        # Progress log
        'progress_log': [],
        # Results
        'loop_result': None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# Utility Functions
# ============================================================================

def log_progress(message: str, level: str = "info"):
    """Add message to progress log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.progress_log.append({
        "timestamp": timestamp,
        "message": message,
        "level": level
    })

def format_fix_description(fix: dict) -> str:
    """Format a fix for display."""
    fix_type = fix.get('type', 'unknown')

    if fix_type == 'add_synonym':
        return f"Add synonym '{fix['synonym']}' to {fix['table']}.{fix['column']}"
    elif fix_type == 'delete_synonym':
        return f"Remove synonym '{fix['synonym']}' from {fix['table']}.{fix['column']}"
    elif fix_type == 'add_column_description':
        return f"Add description to {fix['table']}.{fix['column']}"
    elif fix_type == 'add_table_description':
        return f"Add description to {fix['table']}"
    elif fix_type == 'add_example_query':
        return f"Add query pattern: {fix.get('pattern_name', 'N/A')}"
    elif fix_type == 'delete_example_query':
        return f"Remove query pattern: {fix.get('pattern_name', 'N/A')}"
    elif fix_type == 'create_metric_view':
        return f"Create metric view: {fix['catalog']}.{fix['schema']}.{fix['metric_view_name']}"
    elif fix_type == 'delete_metric_view':
        return f"Remove metric view: {fix.get('metric_view_name')}"
    elif fix_type == 'update_text_instruction':
        return "Update text instructions"
    else:
        return f"{fix_type}"

def get_fix_category_icon(category: str) -> str:
    """Get icon for fix category."""
    icons = {
        'metric_view': '📊',
        'metadata': '📝',
        'sample_query': '📚',
        'instruction': '📖'
    }
    return icons.get(category, '🔧')

def get_fix_category_korean(category: str) -> str:
    """Get Korean name for fix category."""
    names = {
        'metric_view': '메트릭 뷰',
        'metadata': '메타데이터',
        'sample_query': '샘플 쿼리',
        'instruction': '지침'
    }
    return names.get(category, category)

# ============================================================================
# Main UI
# ============================================================================

st.title("🧞 Genie Space Enhancement V2")
st.markdown("**Three-Space Architecture** with **Sequential Fixes**")

# Sidebar: Progress Status
with st.sidebar:
    st.header("📋 Progress")

    steps = {
        'upload': '1️⃣ Upload Benchmarks',
        'configure': '2️⃣ Configure',
        'setup': '3️⃣ Setup Three-Space',
        'analyze': '4️⃣ Analyze Failures',
        'running': '5️⃣ Sequential Fixes',
        'complete': '✅ Complete'
    }

    current_step = st.session_state.step
    for key, label in steps.items():
        if key == current_step:
            st.markdown(f"**→ {label}**")
        else:
            st.markdown(f"　 {label}")

    # Three-space status
    if st.session_state.production_id:
        st.markdown("---")
        st.subheader("🏗️ Three Spaces")
        st.markdown(f"**Production:** `{st.session_state.production_id[:8]}...`")
        st.markdown(f"**Dev-Best:** `{st.session_state.dev_best_id[:8] if st.session_state.dev_best_id else 'N/A'}...`")
        st.markdown(f"**Dev-Working:** `{st.session_state.dev_working_id[:8] if st.session_state.dev_working_id else 'N/A'}...`")

    # Score history
    if st.session_state.scores_history:
        st.markdown("---")
        st.subheader("📈 Score Trend")
        for i, score in enumerate(st.session_state.scores_history[-5:]):
            st.markdown(f"Step {i+1}: **{score:.1%}**")

# ============================================================================
# Step 1: Upload Benchmarks
# ============================================================================

if st.session_state.step == 'upload':
    st.header("1️⃣ Upload Benchmarks")

    st.markdown("""
    Upload a JSON file with benchmark questions:
    ```json
    [{"id": "1", "question": "...", "expected_sql": "SELECT ..."}]
    ```
    """)

    uploaded_file = st.file_uploader("Choose benchmark JSON file", type=['json'])

    if uploaded_file is not None:
        try:
            benchmarks = json.load(uploaded_file)

            if not isinstance(benchmarks, list) or len(benchmarks) == 0:
                st.error("❌ Invalid format: must be a non-empty array")
            else:
                st.session_state.benchmarks = benchmarks
                st.success(f"✅ Loaded {len(benchmarks)} benchmarks")

                with st.expander("Preview (first 3)"):
                    for bm in benchmarks[:3]:
                        st.markdown(f"**{bm.get('question', 'N/A')}**")
                        st.code(bm.get('expected_sql', 'N/A'), language='sql')

                if st.button("Next →", type="primary"):
                    st.session_state.step = 'configure'
                    st.rerun()

        except json.JSONDecodeError as e:
            st.error(f"❌ JSON parsing error: {e}")

# ============================================================================
# Step 2: Configure
# ============================================================================

elif st.session_state.step == 'configure':
    st.header("2️⃣ Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Databricks Connection")

        databricks_host = st.text_input(
            "Host",
            placeholder="workspace.cloud.databricks.com"
        )

        databricks_token = st.text_input(
            "Token",
            type="password"
        )

        space_id = st.text_input(
            "Production Space ID",
            help="The original Genie Space to enhance"
        )

        warehouse_id = st.text_input(
            "SQL Warehouse ID",
            help="Required for creating metric views in Unity Catalog"
        )

    with col2:
        st.subheader("Enhancement Settings")

        target_score = st.slider(
            "Target Score",
            0.0, 1.0, 0.90, 0.05,
            format="%.0f%%"
        )

        indexing_wait = st.number_input(
            "Indexing Wait (seconds)",
            30, 120, 60,
            help="Time to wait after each change for Genie indexing"
        )

        llm_endpoint = st.text_input(
            "LLM Endpoint",
            value="databricks-claude-sonnet-4"
        )

    st.markdown("---")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("← Back"):
            st.session_state.step = 'upload'
            st.rerun()

    with col2:
        if st.button("Setup Three-Space →", type="primary"):
            if not all([databricks_host, databricks_token, space_id, warehouse_id]):
                st.error("❌ Please fill all required fields (including Warehouse ID for metric views)")
            else:
                st.session_state.config = {
                    'databricks_host': databricks_host,
                    'databricks_token': databricks_token,
                    'space_id': space_id,
                    'warehouse_id': warehouse_id,
                    'target_score': target_score,
                    'indexing_wait': indexing_wait,
                    'llm_endpoint': llm_endpoint
                }
                st.session_state.step = 'setup'
                st.rerun()

# ============================================================================
# Step 3: Setup Three-Space Architecture
# ============================================================================

elif st.session_state.step == 'setup':
    st.header("3️⃣ Setting Up Three-Space Architecture")

    config = st.session_state.config

    st.info("""
    Creating three Genie Spaces:
    - **Production** (original, never modified)
    - **Dev-Best** (holds best configuration)
    - **Dev-Working** (where changes are tested)
    """)

    progress = st.progress(0)
    status = st.empty()

    try:
        # Initialize clients
        status.markdown("🔄 Initializing clients...")
        progress.progress(0.2)

        space_cloner = SpaceCloner(
            host=config['databricks_host'],
            token=config['databricks_token']
        )

        llm_client = DatabricksLLMClient(
            host=config['databricks_host'],
            token=config['databricks_token'],
            endpoint_name=config['llm_endpoint']
        )

        if not llm_client.test_connection():
            st.error("❌ LLM connection failed")
            st.stop()

        progress.progress(0.4)
        status.markdown("🔄 Cloning production space...")

        # Setup three spaces
        setup_result = space_cloner.setup_three_spaces(
            production_space_id=config['space_id']
        )

        progress.progress(0.8)

        if not setup_result['success']:
            st.error(f"❌ Setup failed: {setup_result['error']}")
            st.stop()

        # Store results
        st.session_state.production_id = setup_result['production_id']
        st.session_state.dev_working_id = setup_result['dev_working_id']
        st.session_state.dev_best_id = setup_result['dev_best_id']
        st.session_state.production_name = setup_result['production_name']
        st.session_state.initial_config = setup_result['initial_config']

        # Initialize remaining clients
        genie_client = GenieConversationalClient(
            host=config['databricks_host'],
            token=config['databricks_token'],
            space_id=setup_result['dev_working_id']
        )

        scorer = BenchmarkScorer(
            genie_client=genie_client,
            llm_client=llm_client
        )

        # Create SQL executor for metric views
        sql_executor = SQLExecutor(
            host=config['databricks_host'],
            token=config['databricks_token'],
            warehouse_id=config['warehouse_id']
        )

        sequential_enhancer = SequentialEnhancer(
            llm_client=llm_client,
            space_cloner=space_cloner,
            scorer=scorer,
            sql_executor=sql_executor
        )

        st.session_state.clients = {
            'space_cloner': space_cloner,
            'genie_client': genie_client,
            'llm_client': llm_client,
            'scorer': scorer,
            'sql_executor': sql_executor,
            'sequential_enhancer': sequential_enhancer
        }

        progress.progress(1.0)
        status.markdown("✅ Three-Space Architecture Ready!")

        time.sleep(1)

        st.session_state.step = 'analyze'
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {e}")
        if st.button("Retry"):
            st.rerun()

# ============================================================================
# Step 4: Analyze Failures
# ============================================================================

elif st.session_state.step == 'analyze':
    st.header("4️⃣ Analyzing Failures")

    clients = st.session_state.clients
    scorer = clients['scorer']
    sequential_enhancer = clients['sequential_enhancer']

    # Initial scoring
    st.subheader("Initial Benchmark Scoring")

    progress = st.progress(0)
    status = st.empty()

    status.markdown("🔄 Scoring benchmarks on dev-working space...")

    initial_results = scorer.score(st.session_state.benchmarks)
    st.session_state.initial_score = initial_results['score']
    st.session_state.best_score = initial_results['score']
    st.session_state.current_score = initial_results['score']
    st.session_state.scores_history.append(initial_results['score'])

    progress.progress(0.5)

    # Display initial results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Initial Score", f"{initial_results['score']:.1%}")
    with col2:
        st.metric("Passed", f"{initial_results['passed']}/{initial_results['total']}")
    with col3:
        st.metric("Failed", initial_results['failed'])

    # Check if already at target
    if initial_results['score'] >= st.session_state.config['target_score']:
        st.success("🎉 Already at target score!")
        st.session_state.step = 'complete'
        st.rerun()

    # Analyze failures
    status.markdown("🔄 Analyzing failures and generating fixes...")

    grouped_fixes = sequential_enhancer.analyze_all_failures(
        benchmark_results=initial_results,
        space_config=st.session_state.initial_config
    )

    st.session_state.grouped_fixes = grouped_fixes
    progress.progress(1.0)

    # Display fix summary
    st.subheader("Generated Fixes (4 Types Only)")

    total_fixes = 0
    for category in ['metric_view', 'metadata', 'sample_query', 'instruction']:
        fixes = grouped_fixes.get(category, [])
        total_fixes += len(fixes)

        icon = get_fix_category_icon(category)
        name = get_fix_category_korean(category)

        with st.expander(f"{icon} {name} ({len(fixes)} fixes)", expanded=len(fixes) > 0):
            if fixes:
                for i, fix in enumerate(fixes, 1):
                    st.markdown(f"{i}. {format_fix_description(fix)}")
                    if fix.get('reasoning'):
                        st.caption(f"   💡 {fix['reasoning'][:100]}...")
            else:
                st.markdown("No fixes of this type")

    st.markdown(f"**Total: {total_fixes} fixes**")

    if total_fixes == 0:
        st.warning("No fixes generated. Check your benchmarks or space configuration.")
    else:
        st.info(f"""
        ⏱️ **Estimated time:** ~{total_fixes * (st.session_state.config['indexing_wait'] + 30) / 60:.0f} minutes

        Each fix will be applied one at a time, evaluated, and either kept or rolled back.
        """)

        if st.button("Start Sequential Enhancement →", type="primary"):
            st.session_state.step = 'running'
            st.rerun()

# ============================================================================
# Step 5: Running Sequential Enhancement
# ============================================================================

elif st.session_state.step == 'running':
    st.header("5️⃣ Sequential Enhancement in Progress")

    clients = st.session_state.clients
    space_cloner = clients['space_cloner']
    scorer = clients['scorer']
    sequential_enhancer = clients['sequential_enhancer']

    # Run the sequential loop
    st.info("Applying fixes one at a time. This will take a while...")

    # Progress display
    progress_container = st.container()
    log_container = st.container()

    with progress_container:
        col1, col2, col3 = st.columns(3)
        score_metric = col1.empty()
        best_metric = col2.empty()
        progress_metric = col3.empty()

        progress_bar = st.progress(0)
        current_status = st.empty()

    # Run the loop
    try:
        loop_result = sequential_enhancer.run_sequential_loop(
            benchmarks=st.session_state.benchmarks,
            grouped_fixes=st.session_state.grouped_fixes,
            indexing_wait_time=st.session_state.config['indexing_wait']
        )

        st.session_state.loop_result = loop_result
        st.session_state.best_score = loop_result['final_score']
        st.session_state.fixes_applied = loop_result['fixes_applied']
        st.session_state.fixes_rejected = loop_result['fixes_rejected']

        st.session_state.step = 'complete'
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error during enhancement: {e}")
        if st.button("Continue to Results"):
            st.session_state.step = 'complete'
            st.rerun()

# ============================================================================
# Step 6: Complete
# ============================================================================

elif st.session_state.step == 'complete':
    st.header("✅ Enhancement Complete")

    # Results summary
    loop_result = st.session_state.loop_result

    if loop_result:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Initial Score",
                f"{loop_result['initial_score']:.1%}"
            )

        with col2:
            st.metric(
                "Final Score",
                f"{loop_result['final_score']:.1%}",
                f"{loop_result['final_score'] - loop_result['initial_score']:+.1%}"
            )

        with col3:
            st.metric(
                "Fixes Applied",
                len(loop_result['fixes_applied'])
            )

        with col4:
            st.metric(
                "Fixes Rejected",
                len(loop_result['fixes_rejected'])
            )

    # Three-space status
    st.markdown("---")
    st.subheader("🏗️ Three-Space Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Production** (unchanged)")
        st.code(st.session_state.production_id)

    with col2:
        st.markdown("**Dev-Best** (best config)")
        st.code(st.session_state.dev_best_id)

    with col3:
        st.markdown("**Dev-Working** (testing)")
        st.code(st.session_state.dev_working_id)

    # Action buttons
    st.markdown("---")
    st.subheader("📋 What would you like to do?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Promote to Production", type="primary", use_container_width=True):
            with st.spinner("Promoting dev-best to production..."):
                space_cloner = st.session_state.clients['space_cloner']
                result = space_cloner.promote_to_production()

                if result['success']:
                    space_cloner.cleanup_dev_spaces()
                    st.success("✅ Production updated with best configuration!")
                    st.balloons()
                else:
                    st.error(f"❌ Failed: {result['error']}")

    with col2:
        if st.button("🔍 Keep for Review", use_container_width=True):
            st.info(f"""
            Spaces kept for manual review:
            - Production: `{st.session_state.production_id}`
            - Dev-Best: `{st.session_state.dev_best_id}`
            - Dev-Working: `{st.session_state.dev_working_id}`
            """)

    with col3:
        if st.button("🗑️ Delete Dev Spaces", use_container_width=True):
            with st.spinner("Deleting dev spaces..."):
                space_cloner = st.session_state.clients['space_cloner']
                result = space_cloner.cleanup_dev_spaces()

                if result['success']:
                    st.success("✅ Dev spaces deleted")
                else:
                    st.warning(f"⚠️ {result['error']}")

    # Applied fixes detail
    if loop_result and loop_result['fixes_applied']:
        st.markdown("---")
        st.subheader("📝 Applied Fixes")

        for i, fix in enumerate(loop_result['fixes_applied'], 1):
            st.markdown(f"{i}. {format_fix_description(fix)}")

    # Rejected fixes detail
    if loop_result and loop_result['fixes_rejected']:
        with st.expander(f"❌ Rejected Fixes ({len(loop_result['fixes_rejected'])})"):
            for i, fix in enumerate(loop_result['fixes_rejected'], 1):
                st.markdown(f"{i}. {format_fix_description(fix)}")
                if fix.get('rejection_reason'):
                    st.caption(f"   Reason: {fix['rejection_reason']}")

    # Restart button
    st.markdown("---")
    if st.button("🔄 Start New Enhancement", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
