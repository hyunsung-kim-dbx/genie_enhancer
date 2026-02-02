"""
Genie Space Enhancement System - Professional UI
"""

import streamlit as st
import sys
import json
import tempfile
from pathlib import Path
import logging
from datetime import datetime

# Setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.genie_client import GenieConversationalClient
from lib.space_cloner import SpaceCloner
from lib.batch_scorer import BatchBenchmarkScorer
from lib.benchmark_parser import BenchmarkLoader
from lib.llm import DatabricksLLMClient
from lib.sql import SQLExecutor

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Genie Space Enhancement",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if 'running' not in st.session_state:
    st.session_state.running = False
    st.session_state.results = None

# Helper function to fetch resources
def fetch_warehouses(host, token):
    """Fetch SQL Warehouses from Databricks."""
    try:
        import requests
        response = requests.get(
            f"{host}/api/2.0/sql/warehouses",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            return [(w['id'], w['name']) for w in response.json().get('warehouses', [])]
    except:
        return []

def fetch_spaces(host, token):
    """Fetch Genie Spaces from Databricks."""
    try:
        import requests
        response = requests.get(
            f"{host}/api/2.0/genie/spaces",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            return [(s['space_id'], s.get('display_name', s['space_id']))
                    for s in response.json().get('spaces', [])]
    except:
        return []

# Main UI
st.title("🧞 Genie Space Enhancement")
st.markdown("Improve your Genie Space performance with automated enhancements")

# Sidebar - Configuration
with st.sidebar:
    st.header("Configuration")

    # Authentication
    with st.expander("🔐 Authentication", expanded=True):
        host = st.text_input(
            "Workspace URL",
            value="https://krafton-sandbox.cloud.databricks.com",
            help="Your Databricks workspace URL"
        )
        token = st.text_input(
            "Access Token",
            type="password",
            help="Personal Access Token"
        )

    st.divider()

    # Resources
    warehouse_id = None
    space_id = None

    if host and token:
        with st.expander("📦 Resources", expanded=True):
            # SQL Warehouse
            st.subheader("SQL Warehouse")
            warehouses = fetch_warehouses(host, token)

            if warehouses:
                warehouse_options = {name: wid for wid, name in warehouses}
                selected_warehouse = st.selectbox(
                    "Select Warehouse",
                    options=list(warehouse_options.keys()),
                    help="Required for creating metric views"
                )
                warehouse_id = warehouse_options[selected_warehouse]
            else:
                warehouse_id = st.text_input(
                    "Warehouse ID",
                    help="Enter SQL Warehouse ID manually"
                )

            st.divider()

            # Genie Space
            st.subheader("Genie Space")
            spaces = fetch_spaces(host, token)

            if spaces:
                space_options = {name: sid for sid, name in spaces}
                selected_space = st.selectbox(
                    "Select Space",
                    options=list(space_options.keys()),
                    help="Genie Space to enhance"
                )
                space_id = space_options[selected_space]
            else:
                space_id = st.text_input(
                    "Space ID",
                    help="Enter Genie Space ID manually"
                )

        st.divider()

        # Advanced Settings
        with st.expander("⚙️ Advanced Settings"):
            target_score = st.slider(
                "Target Score",
                0.0, 1.0, 0.90, 0.05,
                help="Stop when this score is reached"
            )

            use_turbo = st.checkbox(
                "⚡ Turbo Mode",
                value=False,
                help="Maximum speed (may hit rate limits)"
            )

            if use_turbo:
                st.warning("⚡ Maximum concurrency enabled")
                genie_concurrent = 10
                sql_concurrent = 25
            else:
                genie_concurrent = st.slider("Genie Concurrent", 1, 10, 5)
                sql_concurrent = st.slider("SQL Concurrent", 1, 25, 15)

# Main content
if not host or not token:
    st.info("👈 Please configure authentication in the sidebar")
    st.stop()

if not warehouse_id or not space_id:
    st.warning("👈 Please select SQL Warehouse and Genie Space")
    st.stop()

# Benchmark upload
st.subheader("📊 Benchmark Questions")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload Benchmark File (JSON)",
        type=['json'],
        help="Upload a JSON file with benchmark questions"
    )

with col2:
    st.markdown("**Format:**")
    st.code("""[
  {
    "question": "...",
    "expected_sql": "..."
  }
]""", language="json")

# Start button
if uploaded_file:
    if st.button("🚀 Start Enhancement", type="primary", use_container_width=True, disabled=st.session_state.running):
        st.session_state.running = True

        try:
            # Parse benchmark file
            benchmark_data = json.loads(uploaded_file.read())

            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(benchmark_data, f)
                temp_benchmark_path = f.name

            st.markdown("---")
            st.markdown("## 🔄 Enhancement in Progress")

            # Initialize clients
            with st.status("Initializing...", expanded=False) as status:
                space_cloner = SpaceCloner(host=host, token=token)
                dev_working_id = space_cloner.create_dev_working_space(space_id)

                llm_client = DatabricksLLMClient(
                    host=host,
                    token=token,
                    endpoint_name="databricks-meta-llama-3-1-70b-instruct"
                )

                sql_executor = SQLExecutor(
                    host=host,
                    token=token,
                    warehouse_id=warehouse_id
                )

                genie_client = GenieConversationalClient(
                    host=host,
                    token=token,
                    space_id=dev_working_id
                )

                benchmark_loader = BenchmarkLoader()
                benchmarks = benchmark_loader.load_from_file(temp_benchmark_path)

                status.update(label="✅ Ready", state="complete")

            # Progress tracking
            progress_bar = st.progress(0)
            phase_text = st.empty()

            def update_progress(phase, current, total, message):
                phase_names = {
                    "genie": "🧞 Querying Genie",
                    "sql": "💾 Executing SQL",
                    "eval": "🤖 Evaluating Results"
                }
                progress = current / total if total > 0 else 0
                progress_bar.progress(progress)
                phase_text.write(f"**{phase_names.get(phase, phase)}**: {message}")

            # Configure and run scorer
            batch_config = {
                "genie_max_concurrent": genie_concurrent,
                "sql_max_concurrent": sql_concurrent,
                "genie_retry_attempts": 1,
                "genie_timeout": 45,
                "sql_timeout": 30,
                "eval_chunk_size": 5
            }

            scorer = BatchBenchmarkScorer(
                genie_client=genie_client,
                llm_client=llm_client,
                sql_executor=sql_executor,
                config=batch_config,
                progress_callback=update_progress
            )

            # Run scoring
            start_time = datetime.now()
            results = scorer.score(benchmarks)
            elapsed = (datetime.now() - start_time).total_seconds()

            # Clear progress
            progress_bar.empty()
            phase_text.empty()

            # Show results
            st.markdown("---")
            st.markdown("## 📈 Results")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Score", f"{results['score']:.1%}")
            col2.metric("Passed", f"{results['passed']}/{results['total']}")
            col3.metric("Failed", results['failed'])
            col4.metric("Duration", f"{elapsed:.1f}s")

            # Failed questions
            if results['failed'] > 0:
                st.markdown("### ❌ Failed Questions")

                for r in results['results']:
                    if not r['passed']:
                        with st.expander(f"❌ {r['question']}"):
                            st.markdown(f"**Reason:** {r.get('failure_reason', 'N/A')}")
                            st.markdown(f"**Category:** {r.get('failure_category', 'N/A')}")

                            if r.get('expected_sql'):
                                st.markdown("**Expected SQL:**")
                                st.code(r['expected_sql'], language="sql")

                            if r.get('genie_sql'):
                                st.markdown("**Genie SQL:**")
                                st.code(r['genie_sql'], language="sql")
            else:
                st.success("🎉 All questions passed!")

            st.session_state.results = results
            st.session_state.running = False

        except Exception as e:
            st.session_state.running = False
            st.error(f"❌ Error: {str(e)}")
            logger.exception("Enhancement failed")

# Show previous results
elif st.session_state.results:
    st.markdown("---")
    st.markdown("## 📈 Previous Results")

    results = st.session_state.results

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score", f"{results['score']:.1%}")
    col2.metric("Passed", f"{results['passed']}/{results['total']}")
    col3.metric("Failed", results['failed'])
    col4.metric("Duration", f"{results.get('duration_seconds', 0):.1f}s")
