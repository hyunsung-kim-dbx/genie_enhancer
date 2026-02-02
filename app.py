"""
Genie Space Enhancement System

Single-page Streamlit app for enhancing Genie Spaces with batch scoring.
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add lib directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.genie_client import GenieConversationalClient
from lib.space_cloner import SpaceCloner
from lib.scorer import BenchmarkScorer
from lib.batch_scorer import BatchBenchmarkScorer
from lib.benchmark_parser import BenchmarkLoader
from lib.llm import DatabricksLLMClient
from lib.sql import SQLExecutor
from lib.category_enhancer import CategoryEnhancer
from lib.applier import BatchApplier

logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Genie Space Enhancement",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("🧞 Genie Space Enhancement")
st.markdown("Automated improvement system with batch scoring (13x faster)")

# Initialize session state
if 'enhancement_running' not in st.session_state:
    st.session_state.enhancement_running = False
    st.session_state.results = None

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Databricks connection
    st.subheader("🔐 Databricks")
    databricks_host = st.text_input(
        "Workspace URL",
        value="https://krafton-sandbox.cloud.databricks.com",
        help="Your Databricks workspace URL"
    )
    databricks_token = st.text_input(
        "Personal Access Token",
        type="password",
        help="PAT for authentication"
    )

    # Fetch SQL Warehouses if credentials provided
    warehouses = []
    if databricks_host and databricks_token:
        try:
            import requests
            response = requests.get(
                f"{databricks_host}/api/2.0/sql/warehouses",
                headers={"Authorization": f"Bearer {databricks_token}"},
                timeout=5
            )
            if response.status_code == 200:
                warehouses = [
                    (w['id'], w['name'])
                    for w in response.json().get('warehouses', [])
                    if w.get('state') == 'RUNNING' or w.get('state') == 'STOPPED'
                ]
        except:
            pass

    if warehouses:
        warehouse_options = {f"{name} ({wid[:8]}...)": wid for wid, name in warehouses}
        selected = st.selectbox("SQL Warehouse", options=list(warehouse_options.keys()))
        warehouse_id = warehouse_options[selected]
    else:
        warehouse_id = st.text_input("SQL Warehouse ID", help="For metric view creation")

    st.divider()

    # Genie Space config
    st.subheader("🧞 Genie Space")

    # Fetch Genie Spaces if credentials provided
    spaces = []
    if databricks_host and databricks_token:
        try:
            import requests
            response = requests.get(
                f"{databricks_host}/api/2.0/genie/spaces",
                headers={"Authorization": f"Bearer {databricks_token}"},
                timeout=5
            )
            if response.status_code == 200:
                spaces = [
                    (s['space_id'], s.get('display_name', s['space_id']))
                    for s in response.json().get('spaces', [])
                ]
        except:
            pass

    if spaces:
        space_options = {f"{name} ({sid[:8]}...)": sid for sid, name in spaces}
        selected_space = st.selectbox("Select Genie Space", options=list(space_options.keys()))
        space_id = space_options[selected_space]
    else:
        space_id = st.text_input(
            "Space ID",
            value="01f0f5c840c118b9824acd167525a768",
            help="Genie Space to enhance"
        )

    st.divider()

    # Benchmark selection
    st.subheader("📊 Benchmarks")
    benchmark_file = st.selectbox(
        "Select Benchmark",
        options=[
            "benchmarks/kpi_benchmark.json",
            "benchmarks/social_benchmark.json",
            "benchmarks/benchmark.json"
        ]
    )

    st.divider()

    # Enhancement settings
    st.subheader("⚙️ Settings")
    target_score = st.slider("Target Score", 0.0, 1.0, 0.90, 0.05)
    max_loops = st.number_input("Max Loops", 1, 10, 3)

    # Batch mode settings
    use_batch = st.checkbox("🚀 Use Batch Scoring", value=True, help="13x faster!")

    if use_batch:
        turbo_mode = st.checkbox(
            "⚡ TURBO MODE",
            value=False,
            help="Maximum speed! May hit rate limits."
        )

        if turbo_mode:
            st.warning("⚡ TURBO: Max concurrency!")
            genie_concurrent = 10
            sql_concurrent = 25
        else:
            genie_concurrent = st.slider(
                "Genie Concurrent",
                min_value=1,
                max_value=15,
                value=5,
                help="Try 5-8 for best speed"
            )
            sql_concurrent = st.slider(
                "SQL Concurrent",
                min_value=1,
                max_value=30,
                value=15
            )
    else:
        st.warning("⚠️ Sequential mode is 13x slower")
        genie_concurrent = 1
        sql_concurrent = 1

    st.divider()

    # Start button
    start_button = st.button(
        "🚀 Start Enhancement",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.enhancement_running
    )

# Main content area
if not databricks_host or not databricks_token or not warehouse_id:
    st.info("👈 Configure Databricks connection in the sidebar")

    with st.expander("📖 How It Works", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Phase 1: Score")
            st.markdown("Run benchmarks through Genie and compare results")

        with col2:
            st.markdown("### Phase 2: Fix")
            st.markdown("Generate targeted improvements based on failures")

        with col3:
            st.markdown("### Phase 3: Validate")
            st.markdown("Re-score and measure improvement")

        st.markdown("---")
        st.markdown("### 🚀 Batch Scoring Performance")

        perf_data = {
            "Mode": ["Sequential", "Parallel", "Batch"],
            "20 Benchmarks": ["~7 min", "~1.5 min", "~30s"],
            "Speedup": ["1x", "4.6x", "13x"]
        }
        st.table(perf_data)

elif start_button:
    st.session_state.enhancement_running = True

    try:
        st.markdown("## 🔄 Enhancement Running")

        # Build batch config
        batch_config = {
            "genie_max_concurrent": genie_concurrent,
            "sql_max_concurrent": sql_concurrent,
            "genie_retry_attempts": 1,
            "genie_timeout": 45,
            "sql_timeout": 30,
            "eval_chunk_size": 5
        }

        # Initialize clients
        with st.status("Initializing...", expanded=True) as status:
            st.write("🔌 Connecting to Databricks...")

            space_cloner = SpaceCloner(host=databricks_host, token=databricks_token)

            st.write("📦 Cloning space to dev-working...")
            dev_working_id = space_cloner.create_dev_working_space(space_id)
            st.success(f"✅ Dev space: {dev_working_id}")

            llm_client = DatabricksLLMClient(
                host=databricks_host,
                token=databricks_token,
                endpoint_name="databricks-meta-llama-3-1-70b-instruct"
            )

            sql_executor = SQLExecutor(
                host=databricks_host,
                token=databricks_token,
                warehouse_id=warehouse_id
            )

            genie_client = GenieConversationalClient(
                host=databricks_host,
                token=databricks_token,
                space_id=dev_working_id
            )

            benchmark_loader = BenchmarkLoader()
            benchmarks = benchmark_loader.load_from_file(project_root / benchmark_file)
            st.success(f"✅ Loaded {len(benchmarks)} benchmarks")

            status.update(label="✅ Initialization complete", state="complete")

        # Progress callback
        progress_bar = st.progress(0)
        phase_text = st.empty()

        def update_progress(phase, current, total, message):
            phase_names = {
                "genie": "🧞 Genie Queries",
                "sql": "💾 SQL Execution",
                "eval": "🤖 LLM Evaluation"
            }
            progress = current / total if total > 0 else 0
            progress_bar.progress(progress)
            phase_text.write(f"**{phase_names.get(phase, phase)}**: {message}")

        # Initialize scorer
        if use_batch:
            scorer = BatchBenchmarkScorer(
                genie_client=genie_client,
                llm_client=llm_client,
                sql_executor=sql_executor,
                config=batch_config,
                progress_callback=update_progress
            )
        else:
            scorer = BenchmarkScorer(
                genie_client=genie_client,
                llm_client=llm_client,
                sql_executor=sql_executor,
                config={"parallel_workers": 0}
            )

        # Run scoring
        st.markdown("### 📊 Scoring Benchmarks")
        start_time = datetime.now()
        score_results = scorer.score(benchmarks)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Clear progress
        progress_bar.empty()
        phase_text.empty()

        # Show results
        st.success(f"✅ Scoring complete in {elapsed:.1f}s")

        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{score_results['score']:.1%}")
        col2.metric("Passed", f"{score_results['passed']}/{score_results['total']}")
        col3.metric("Time", f"{elapsed:.1f}s")

        # Show details
        with st.expander("📋 Detailed Results", expanded=False):
            for r in score_results['results']:
                if not r['passed']:
                    st.markdown(f"**❌ {r['question']}**")
                    st.markdown(f"- Reason: {r.get('failure_reason', 'N/A')}")
                    st.markdown(f"- Category: {r.get('failure_category', 'N/A')}")

        st.session_state.results = score_results
        st.session_state.enhancement_running = False

    except Exception as e:
        st.session_state.enhancement_running = False
        st.error(f"❌ Error: {str(e)}")
        logger.exception("Enhancement failed")

elif st.session_state.results:
    st.markdown("## 📈 Latest Results")
    results = st.session_state.results

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{results['score']:.1%}")
    col2.metric("Passed", f"{results['passed']}/{results['total']}")
    col3.metric("Duration", f"{results.get('duration_seconds', 0):.1f}s")

    with st.expander("📋 Detailed Results"):
        for r in results['results']:
            if not r['passed']:
                st.markdown(f"**❌ {r['question']}**")
                st.markdown(f"- Reason: {r.get('failure_reason', 'N/A')}")
