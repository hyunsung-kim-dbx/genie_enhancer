"""
Genie Space Enhancement Tool - Databricks Apps Edition

Databricks Apps compatible Streamlit application for enhancing Genie Spaces.

Features:
- Auto-authentication via Databricks SDK (uses injected service principal credentials)
- Three-space architecture (production, dev-best, dev-working)
- Category-based fix generation (9 LLM calls)
- Batch fix application
- Safe promotion workflow

Deployment:
    databricks apps create genie-enhancer
    databricks sync . "/Users/$USER/genie-enhancer"
    databricks apps deploy genie-enhancer --source-code-path "/Workspace/Users/$USER/genie-enhancer"
"""

import streamlit as st
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# Add directory to path for imports
# Works both locally and in Databricks Apps
app_dir = Path(__file__).parent

# Check if lib exists in app directory (Databricks Apps deployment)
if (app_dir / "lib").exists():
    # Databricks Apps: lib is bundled with app
    sys.path.insert(0, str(app_dir))
    project_root = app_dir
else:
    # Local development: lib is in parent directory
    project_root = app_dir.parent
    sys.path.insert(0, str(project_root))

# Databricks SDK for authentication
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.config import Config
    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    DATABRICKS_SDK_AVAILABLE = False

from lib.genie_client import GenieConversationalClient
from lib.space_cloner import SpaceCloner
from lib.scorer import BenchmarkScorer
from lib.llm import DatabricksLLMClient
from lib.sql import SQLExecutor
from lib.category_enhancer import CategoryEnhancer
from lib.applier import BatchApplier

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Genie Enhancement",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Databricks Authentication Helper
# ============================================================================

def get_user_token():
    """
    Get user's access token from forwarded headers.

    In Databricks Apps, user credentials are forwarded:
    - X-Forwarded-Access-Token: User's OAuth token
    - X-Forwarded-Email: User's email
    """
    try:
        return st.context.headers.get('X-Forwarded-Access-Token')
    except Exception:
        return None


def get_user_email():
    """Get user's email from forwarded headers."""
    try:
        return st.context.headers.get('X-Forwarded-Email')
    except Exception:
        return None


def get_databricks_config():
    """
    Get Databricks configuration using SDK unified authentication.

    In Databricks Apps, credentials are auto-injected:
    - DATABRICKS_HOST (workspace URL)
    - DATABRICKS_CLIENT_ID (service principal)
    - DATABRICKS_CLIENT_SECRET (service principal secret)

    The SDK auto-detects these environment variables.

    For user operations, we use X-Forwarded-Access-Token from headers.
    """
    if not DATABRICKS_SDK_AVAILABLE:
        return None, "Databricks SDK not installed"

    try:
        # SDK auto-detects credentials from environment (Service Principal)
        w = WorkspaceClient()

        # Get host from SDK config
        host = w.config.host
        if host:
            host = host.replace("https://", "").replace("http://", "").rstrip("/")

        # Get user token from forwarded headers
        user_token = get_user_token()
        user_email = get_user_email()

        return {
            "host": host,
            "workspace_client": w,  # SP client for admin operations
            "auth_type": w.config.auth_type,
            "user_token": user_token,  # User token for data queries
            "user_email": user_email,
        }, None
    except Exception as e:
        return None, str(e)


def get_auth_headers(workspace_client):
    """Get authentication headers from workspace client."""
    try:
        return workspace_client.config.authenticate()
    except Exception as e:
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def list_genie_spaces(_host: str, _token: str) -> list:
    """List all Genie Spaces in the workspace (handles pagination)."""
    import requests
    try:
        all_spaces = []
        page_token = None
        api_headers = {"Authorization": f"Bearer {_token}"}

        while True:
            url = f"https://{_host}/api/2.0/genie/spaces"
            params = {"page_size": 100}  # Max allowed
            if page_token:
                params["page_token"] = page_token

            response = requests.get(url, headers=api_headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            spaces = data.get("spaces", [])
            all_spaces.extend(spaces)

            # Check for next page
            page_token = data.get("next_page_token")
            if not page_token:
                break

        return [(s.get("space_id"), s.get("title", "Untitled")) for s in all_spaces]
    except Exception as e:
        st.warning(f"Failed to list Genie Spaces: {e}")
        return []


@st.cache_data(ttl=300)  # Cache for 5 minutes
def list_sql_warehouses(_host: str, _token: str) -> list:
    """List all SQL Warehouses in the workspace."""
    import requests
    try:
        url = f"https://{_host}/api/2.0/sql/warehouses"
        api_headers = {"Authorization": f"Bearer {_token}"}
        response = requests.get(url, headers=api_headers, timeout=30)
        response.raise_for_status()
        warehouses = response.json().get("warehouses", [])
        return [(w.get("id"), f"{w.get('name', 'Unknown')} ({w.get('state', 'UNKNOWN')})") for w in warehouses]
    except Exception as e:
        st.warning(f"Failed to list SQL Warehouses: {e}")
        return []


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'step': 'configure',  # configure, upload, setup, analyze, running, complete
        'benchmarks': None,
        'config': None,
        'clients': None,
        'auth_config': None,
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

    descriptions = {
        'add_synonym': lambda f: f"Add synonym '{f.get('synonym')}' to {f.get('table')}.{f.get('column')}",
        'delete_synonym': lambda f: f"Remove synonym '{f.get('synonym')}' from {f.get('table')}.{f.get('column')}",
        'add_column_description': lambda f: f"Add description to {f.get('table')}.{f.get('column')}",
        'add_table_description': lambda f: f"Add description to {f.get('table')}",
        'add_example_query': lambda f: f"Add query pattern: {f.get('pattern_name', 'N/A')}",
        'delete_example_query': lambda f: f"Remove query pattern: {f.get('pattern_name', f.get('id', 'N/A'))}",
        'update_text_instruction': lambda f: "Update text instructions",
        'add_filter': lambda f: f"Add filter: {f.get('display_name', 'N/A')}",
        'delete_filter': lambda f: f"Remove filter: {f.get('display_name', f.get('id', 'N/A'))}",
        'add_expression': lambda f: f"Add expression: {f.get('alias', f.get('display_name', 'N/A'))}",
        'delete_expression': lambda f: f"Remove expression: {f.get('alias', f.get('id', 'N/A'))}",
        'add_measure': lambda f: f"Add measure: {f.get('alias', f.get('display_name', 'N/A'))}",
        'delete_measure': lambda f: f"Remove measure: {f.get('alias', f.get('id', 'N/A'))}",
        'add_join_spec': lambda f: f"Add join: {f.get('left_table')} ↔ {f.get('right_table')}",
        'delete_join_spec': lambda f: f"Remove join: {f.get('left_table')} ↔ {f.get('right_table')}",
    }

    formatter = descriptions.get(fix_type, lambda f: fix_type)
    return formatter(fix)


def get_fix_category_display(category: str) -> tuple:
    """Get icon and Korean name for fix category."""
    categories = {
        'instruction_fix': ('📖', '지침 수정'),
        'sample_queries_delete': ('🗑️', '샘플 쿼리 삭제'),
        'sample_queries_add': ('📚', '샘플 쿼리 추가'),
        'metadata_delete': ('🔻', '메타데이터 삭제'),
        'metadata_add': ('📝', '메타데이터 추가'),
        'sql_snippets_delete': ('⛔', 'SQL 스니펫 삭제'),
        'sql_snippets_add': ('🧩', 'SQL 스니펫 추가'),
        'join_specs_delete': ('🔗', '조인 스펙 삭제'),
        'join_specs_add': ('🔗', '조인 스펙 추가'),
    }
    return categories.get(category, ('🔧', category))


# ============================================================================
# Main UI
# ============================================================================

st.title("🧞 Genie Space Enhancement")
st.markdown("**Databricks Apps Edition** - Three-Space Architecture with Batch Fixes")

# Sidebar: Progress Status
with st.sidebar:
    st.header("📋 Progress")

    steps = {
        'configure': '1️⃣ Configure',
        'upload': '2️⃣ Upload Benchmarks',
        'setup': '3️⃣ Setup Three-Space',
        'analyze': '4️⃣ Analyze & Plan',
        'running': '5️⃣ Apply Fixes',
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
        st.caption(f"Production: `{st.session_state.production_id[:8]}...`")
        if st.session_state.dev_best_id:
            st.caption(f"Dev-Best: `{st.session_state.dev_best_id[:8]}...`")
        if st.session_state.dev_working_id:
            st.caption(f"Dev-Working: `{st.session_state.dev_working_id[:8]}...`")

    # Score history
    if st.session_state.scores_history:
        st.markdown("---")
        st.subheader("📈 Scores")
        for i, score in enumerate(st.session_state.scores_history[-5:]):
            st.caption(f"Round {i+1}: **{score:.1%}**")

# ============================================================================
# Step 1: Configure
# ============================================================================

if st.session_state.step == 'configure':
    st.header("1️⃣ Configuration")

    # Try auto-authentication first
    auth_config, auth_error = get_databricks_config()

    if auth_config:
        st.success(f"✅ Auto-authenticated via {auth_config['auth_type']}")
        st.info(f"Workspace: `{auth_config['host']}`")

        # Show user info if available
        if auth_config.get('user_email'):
            st.caption(f"👤 User: {auth_config['user_email']}")

        # Store auth config
        st.session_state.auth_config = auth_config

        # Use SP token for listing resources (admin operations)
        # User token is only for data queries later
        try:
            auth_headers = auth_config['workspace_client'].config.authenticate()
            api_token = auth_headers.get('Authorization', '').replace('Bearer ', '')
        except:
            api_token = None

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Genie Space")

            # List available Genie Spaces
            if api_token:
                genie_spaces = list_genie_spaces(auth_config['host'], api_token)
            else:
                genie_spaces = []

            if genie_spaces:
                space_options = {f"{name} ({sid[:8]}...)": sid for sid, name in genie_spaces}
                selected_space = st.selectbox(
                    "Production Space",
                    options=list(space_options.keys()),
                    help="Select the Genie Space to enhance"
                )
                space_id = space_options.get(selected_space, '')
            else:
                default_space_id = os.getenv('GENIE_SPACE_ID', '')
                space_id = st.text_input(
                    "Production Space ID",
                    value=default_space_id,
                    help="The Genie Space to enhance"
                )

            # List available SQL Warehouses
            if api_token:
                warehouses = list_sql_warehouses(auth_config['host'], api_token)
            else:
                warehouses = []

            if warehouses:
                wh_options = {f"{name}": wid for wid, name in warehouses}
                selected_wh = st.selectbox(
                    "SQL Warehouse",
                    options=list(wh_options.keys()),
                    help="Select a SQL Warehouse"
                )
                warehouse_id = wh_options.get(selected_wh, '')
            else:
                default_warehouse = os.getenv('DATABRICKS_WAREHOUSE_ID', '')
                warehouse_id = st.text_input(
                    "SQL Warehouse ID",
                    value=default_warehouse,
                    help="For executing SQL queries"
                )

        with col2:
            st.subheader("Enhancement Settings")

            default_llm = os.getenv('LLM_ENDPOINT', 'databricks-claude-sonnet-4')
            llm_endpoint = st.text_input("LLM Endpoint", value=default_llm)

            # Use integer slider (0-100) for proper percentage display
            target_score_pct = st.slider(
                "Target Score",
                min_value=0,
                max_value=100,
                value=90,
                step=5,
                format="%d%%"
            )
            target_score = target_score_pct / 100.0  # Convert to decimal

            max_loops = st.number_input(
                "Max Enhancement Loops",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of score→plan→apply cycles"
            )

            indexing_wait = st.number_input(
                "Indexing Wait (seconds)",
                30, 120, 60,
                help="Time to wait after applying fixes"
            )

        st.markdown("---")

        if st.button("Next →", type="primary"):
            if not space_id or not warehouse_id:
                st.error("Please provide Space ID and Warehouse ID")
            else:
                st.session_state.config = {
                    'databricks_host': auth_config['host'],
                    'workspace_client': auth_config['workspace_client'],
                    'user_token': auth_config.get('user_token'),  # User token for data queries
                    'user_email': auth_config.get('user_email'),
                    'space_id': space_id,
                    'warehouse_id': warehouse_id,
                    'target_score': target_score,
                    'max_loops': max_loops,
                    'indexing_wait': indexing_wait,
                    'llm_endpoint': llm_endpoint,
                }
                st.session_state.step = 'upload'
                st.rerun()

    else:
        st.warning("⚠️ Auto-authentication not available. Please provide credentials manually.")
        if auth_error:
            st.caption(f"Reason: {auth_error}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Databricks Connection")

            databricks_host = st.text_input(
                "Host",
                placeholder="workspace.cloud.databricks.com"
            )

            databricks_token = st.text_input(
                "Personal Access Token",
                type="password"
            )

            space_id = st.text_input(
                "Production Space ID",
                help="The Genie Space to enhance"
            )

            warehouse_id = st.text_input(
                "SQL Warehouse ID",
                help="For executing SQL queries"
            )

        with col2:
            st.subheader("Enhancement Settings")

            llm_endpoint = st.text_input(
                "LLM Endpoint",
                value="databricks-claude-sonnet-4"
            )

            # Use integer slider (0-100) for proper percentage display
            target_score_pct = st.slider(
                "Target Score",
                min_value=0,
                max_value=100,
                value=90,
                step=5,
                format="%d%%",
                key="manual_target_score"
            )
            target_score = target_score_pct / 100.0  # Convert to decimal

            max_loops = st.number_input(
                "Max Enhancement Loops",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of score→plan→apply cycles",
                key="manual_max_loops"
            )

            indexing_wait = st.number_input(
                "Indexing Wait (seconds)",
                30, 120, 60,
                key="manual_indexing_wait"
            )

        st.markdown("---")

        if st.button("Next →", type="primary", key="manual_next"):
            if not all([databricks_host, databricks_token, space_id, warehouse_id]):
                st.error("Please fill all required fields")
            else:
                st.session_state.config = {
                    'databricks_host': databricks_host.replace("https://", "").replace("http://", ""),
                    'databricks_token': databricks_token,
                    'space_id': space_id,
                    'warehouse_id': warehouse_id,
                    'target_score': target_score,
                    'max_loops': max_loops,
                    'indexing_wait': indexing_wait,
                    'llm_endpoint': llm_endpoint,
                }
                st.session_state.step = 'upload'
                st.rerun()

# ============================================================================
# Step 2: Upload Benchmarks
# ============================================================================

elif st.session_state.step == 'upload':
    st.header("2️⃣ Upload Benchmarks")

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
                st.error("Invalid format: must be a non-empty array")
            else:
                st.session_state.benchmarks = benchmarks
                st.success(f"✅ Loaded {len(benchmarks)} benchmarks")

                with st.expander("Preview (first 3)"):
                    for bm in benchmarks[:3]:
                        q = bm.get('korean_question') or bm.get('question', 'N/A')
                        st.markdown(f"**{q}**")
                        st.code(bm.get('expected_sql', 'N/A')[:200], language='sql')

        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {e}")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("← Back"):
            st.session_state.step = 'configure'
            st.rerun()

    with col2:
        if st.button("Setup Three-Space →", type="primary", disabled=st.session_state.benchmarks is None):
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
        # Get authentication
        host = config['databricks_host']

        # Prefer user token (user-assumed auth) for all operations
        # This way the app acts with user's permissions
        user_token = config.get('user_token')

        if not user_token:
            # Fallback to SP token if user token not available
            if 'workspace_client' in config:
                headers = config['workspace_client'].config.authenticate()
                user_token = headers.get('Authorization', '').replace('Bearer ', '')
            else:
                user_token = config.get('databricks_token')

        if not user_token:
            st.error("❌ No authentication token available")
            st.stop()

        # Initialize clients - ALL use user token (user-assumed auth)
        status.markdown("🔄 Initializing clients...")
        progress.progress(0.2)

        # Space cloning uses USER token (user's permissions)
        space_cloner = SpaceCloner(host=host, token=user_token)

        progress.progress(0.3)
        status.markdown("🔄 Cloning production space...")

        # Setup three spaces
        setup_result = space_cloner.setup_three_spaces(
            production_space_id=config['space_id']
        )

        progress.progress(0.7)

        if not setup_result['success']:
            st.error(f"Setup failed: {setup_result['error']}")
            st.stop()

        # Store results
        st.session_state.production_id = setup_result['production_id']
        st.session_state.dev_working_id = setup_result['dev_working_id']
        st.session_state.dev_best_id = setup_result['dev_best_id']
        st.session_state.production_name = setup_result['production_name']
        st.session_state.initial_config = setup_result['initial_config']

        progress.progress(0.8)
        status.markdown("🔄 Initializing analysis clients...")

        # Initialize LLM client (for analysis step)
        llm_client = DatabricksLLMClient(
            host=host,
            token=user_token,
            endpoint_name=config['llm_endpoint'],
            request_delay=10.0,
            rate_limit_base_delay=90.0
        )

        # SQL executor uses USER token
        sql_executor = SQLExecutor(
            host=host,
            token=user_token,
            warehouse_id=config['warehouse_id']
        )

        # Genie client uses USER token
        genie_client = GenieConversationalClient(
            host=host,
            token=user_token,
            space_id=setup_result['dev_working_id']
        )

        scorer = BenchmarkScorer(
            genie_client=genie_client,
            llm_client=llm_client,
            sql_executor=sql_executor,
            config={"parallel_workers": 0}
        )

        planner = CategoryEnhancer(llm_client, project_root / "prompts")

        # Applier uses space_cloner (user token) for space modifications
        applier = BatchApplier(
            space_api=space_cloner,
            sql_executor=sql_executor,
        )

        # Store token and clients
        st.session_state.user_token = user_token
        st.session_state.clients = {
            'space_cloner': space_cloner,
            'genie_client': genie_client,
            'llm_client': llm_client,
            'scorer': scorer,
            'sql_executor': sql_executor,
            'planner': planner,
            'applier': applier,
        }

        progress.progress(1.0)
        status.markdown("✅ Three-Space Architecture Ready!")

        time.sleep(1)

        st.session_state.step = 'analyze'
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())
        if st.button("Retry"):
            st.rerun()

# ============================================================================
# Step 4: Analyze Failures & Generate Plan
# ============================================================================

elif st.session_state.step == 'analyze':
    st.header("4️⃣ Analyze & Generate Enhancement Plan")

    clients = st.session_state.clients
    scorer = clients['scorer']
    planner = clients['planner']

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

    progress.progress(0.3)

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

    failed_results = [r for r in initial_results['results'] if not r['passed']]

    grouped_fixes = planner.generate_plan(
        failed_benchmarks=failed_results,
        space_config=st.session_state.initial_config,
        parallel_workers=3
    )

    st.session_state.grouped_fixes = grouped_fixes
    progress.progress(1.0)

    # Display fix summary
    st.subheader("Generated Fixes (9 Categories)")

    FIX_CATEGORIES = [
        'instruction_fix',
        'join_specs_delete', 'join_specs_add',
        'sql_snippets_delete', 'sql_snippets_add',
        'metadata_delete', 'metadata_add',
        'sample_queries_delete', 'sample_queries_add',
    ]

    total_fixes = 0
    for category in FIX_CATEGORIES:
        fixes = grouped_fixes.get(category, [])
        total_fixes += len(fixes)

        icon, name = get_fix_category_display(category)

        with st.expander(f"{icon} {name} ({len(fixes)} fixes)", expanded=len(fixes) > 0):
            if fixes:
                for i, fix in enumerate(fixes[:10], 1):
                    st.markdown(f"{i}. {format_fix_description(fix)}")
                if len(fixes) > 10:
                    st.caption(f"... and {len(fixes) - 10} more")
            else:
                st.caption("No fixes of this type")

    st.markdown(f"**Total: {total_fixes} fixes**")

    if total_fixes == 0:
        st.warning("No fixes generated. Check your benchmarks or space configuration.")
    else:
        st.info(f"""
        ⏱️ **Estimated time:** ~{(st.session_state.config['indexing_wait'] + 30) / 60:.0f} minutes

        All fixes will be applied in one batch, then validated.
        """)

        if st.button("Apply All Fixes →", type="primary"):
            st.session_state.step = 'running'
            st.rerun()

# ============================================================================
# Step 5: Enhancement Loop (Apply → Evaluate → Fix → Repeat)
# ============================================================================

elif st.session_state.step == 'running':
    st.header("5️⃣ Enhancement Loop")

    clients = st.session_state.clients
    applier = clients['applier']
    scorer = clients['scorer']
    planner = clients['planner']
    space_cloner = clients['space_cloner']

    config = st.session_state.config
    max_loops = config.get('max_loops', 3)
    target_score = config['target_score']
    wait_time = config['indexing_wait']

    # Initialize loop tracking in session state
    if 'current_loop' not in st.session_state:
        st.session_state.current_loop = 1
        st.session_state.all_fixes_applied = []
        st.session_state.all_fixes_failed = []

    # Display loop status
    loop_status = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    metrics_container = st.container()
    log_container = st.container()

    try:
        current_loop = st.session_state.current_loop
        current_score = st.session_state.current_score
        grouped_fixes = st.session_state.grouped_fixes

        while current_loop <= max_loops:
            loop_status.markdown(f"### 🔄 Loop {current_loop}/{max_loops}")

            # Calculate overall progress
            loop_progress_base = (current_loop - 1) / max_loops
            loop_progress_range = 1 / max_loops

            # --- Step A: Apply Fixes ---
            with log_container:
                st.markdown(f"**Loop {current_loop}:** Applying fixes...")

            status_text.markdown(f"🔧 **Loop {current_loop}:** Applying {sum(len(f) for f in grouped_fixes.values())} fixes...")
            progress_bar.progress(loop_progress_base + loop_progress_range * 0.1)

            apply_result = applier.apply_all(
                space_id=st.session_state.dev_working_id,
                grouped_fixes=grouped_fixes,
                dry_run=False
            )

            st.session_state.all_fixes_applied.extend(apply_result['applied'])
            st.session_state.all_fixes_failed.extend(apply_result['failed'])

            with log_container:
                st.markdown(f"  ✅ Applied: {len(apply_result['applied'])} | ❌ Failed: {len(apply_result['failed'])}")

            # --- Step B: Wait for Indexing ---
            status_text.markdown(f"⏳ **Loop {current_loop}:** Waiting {wait_time}s for Genie indexing...")
            progress_bar.progress(loop_progress_base + loop_progress_range * 0.3)

            for remaining in range(wait_time, 0, -5):
                time.sleep(5)
                pct = (wait_time - remaining) / wait_time
                progress_bar.progress(loop_progress_base + loop_progress_range * (0.3 + 0.2 * pct))
                status_text.markdown(f"⏳ **Loop {current_loop}:** Waiting... {remaining - 5}s remaining")

            # --- Step C: Evaluate ---
            status_text.markdown(f"📊 **Loop {current_loop}:** Evaluating...")
            progress_bar.progress(loop_progress_base + loop_progress_range * 0.6)

            eval_results = scorer.score(st.session_state.benchmarks)
            new_score = eval_results['score']
            st.session_state.scores_history.append(new_score)

            # Update metrics display
            with metrics_container:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Loop", f"{current_loop}/{max_loops}")
                col2.metric("Current Score", f"{new_score:.1%}", f"{new_score - current_score:+.1%}")
                col3.metric("Target", f"{target_score:.0%}")
                col4.metric("Best", f"{st.session_state.best_score:.1%}")

            with log_container:
                st.markdown(f"  📊 Score: **{new_score:.1%}** (was {current_score:.1%})")

            # Update best score
            if new_score > st.session_state.best_score:
                st.session_state.best_score = new_score
                space_cloner.update_dev_best()
                with log_container:
                    st.markdown(f"  🏆 New best score! Saved to dev-best.")

            current_score = new_score
            st.session_state.current_score = new_score

            # --- Check if Target Reached ---
            if new_score >= target_score:
                with log_container:
                    st.success(f"🎉 **Target reached!** Score: {new_score:.1%} >= {target_score:.0%}")
                progress_bar.progress(1.0)
                break

            # --- Step D: Generate New Fixes for Remaining Failures ---
            if current_loop < max_loops:
                status_text.markdown(f"🔍 **Loop {current_loop}:** Analyzing remaining failures...")
                progress_bar.progress(loop_progress_base + loop_progress_range * 0.8)

                failed_results = [r for r in eval_results['results'] if not r['passed']]

                if not failed_results:
                    with log_container:
                        st.info("No more failures to fix!")
                    break

                with log_container:
                    st.markdown(f"  🔍 Analyzing {len(failed_results)} remaining failures...")

                # Get current config for context
                current_config = space_cloner.get_dev_working_config()

                grouped_fixes = planner.generate_plan(
                    failed_benchmarks=failed_results,
                    space_config=current_config,
                    parallel_workers=3
                )

                total_new_fixes = sum(len(f) for f in grouped_fixes.values())

                if total_new_fixes == 0:
                    with log_container:
                        st.warning("No new fixes generated. Stopping loop.")
                    break

                with log_container:
                    st.markdown(f"  📝 Generated {total_new_fixes} new fixes")

                st.session_state.grouped_fixes = grouped_fixes

            progress_bar.progress(loop_progress_base + loop_progress_range)
            current_loop += 1
            st.session_state.current_loop = current_loop

        # --- Loop Complete ---
        progress_bar.progress(1.0)
        status_text.markdown("✅ **Enhancement loop complete!**")

        # Store final results
        st.session_state.loop_result = {
            'initial_score': st.session_state.initial_score,
            'final_score': st.session_state.current_score,
            'loops_completed': current_loop - 1 if current_loop <= max_loops else max_loops,
            'target_reached': st.session_state.current_score >= target_score,
            'fixes_applied': st.session_state.all_fixes_applied,
            'fixes_rejected': st.session_state.all_fixes_failed,
        }

        # Clean up loop state
        del st.session_state.current_loop
        del st.session_state.all_fixes_applied
        del st.session_state.all_fixes_failed

        time.sleep(2)
        st.session_state.step = 'complete'
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())
        if st.button("Continue to Results"):
            # Clean up loop state
            if 'current_loop' in st.session_state:
                del st.session_state.current_loop
            if 'all_fixes_applied' in st.session_state:
                del st.session_state.all_fixes_applied
            if 'all_fixes_failed' in st.session_state:
                del st.session_state.all_fixes_failed
            st.session_state.step = 'complete'
            st.rerun()

# ============================================================================
# Step 6: Complete
# ============================================================================

elif st.session_state.step == 'complete':
    st.header("✅ Enhancement Complete")

    loop_result = st.session_state.loop_result

    if loop_result:
        improvement = loop_result['final_score'] - loop_result['initial_score']
        loops_completed = loop_result.get('loops_completed', 1)
        target_reached = loop_result.get('target_reached', False)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Initial Score", f"{loop_result['initial_score']:.1%}")

        with col2:
            st.metric(
                "Final Score",
                f"{loop_result['final_score']:.1%}",
                f"{improvement:+.1%}"
            )

        with col3:
            st.metric("Loops", loops_completed)

        with col4:
            st.metric("Fixes Applied", len(loop_result['fixes_applied']))

        with col5:
            st.metric("Fixes Failed", len(loop_result['fixes_rejected']))

        if target_reached:
            st.success(f"🎉 Target score reached in {loops_completed} loop(s)!")
        elif improvement > 0:
            st.info(f"📈 Improved by {improvement:+.1%} over {loops_completed} loop(s)")
        else:
            st.warning(f"⚠️ No improvement after {loops_completed} loop(s)")

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
        st.markdown("**Dev-Working** (tested)")
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
                    st.success("✅ Production updated!")
                    st.balloons()
                else:
                    st.error(f"Failed: {result['error']}")

    with col2:
        if st.button("🔍 Keep for Review", use_container_width=True):
            st.info(f"""
            Spaces preserved:
            - Production: `{st.session_state.production_id}`
            - Dev-Best: `{st.session_state.dev_best_id}`
            - Dev-Working: `{st.session_state.dev_working_id}`
            """)

    with col3:
        if st.button("🗑️ Discard & Cleanup", use_container_width=True):
            with st.spinner("Cleaning up..."):
                space_cloner = st.session_state.clients['space_cloner']
                result = space_cloner.cleanup_dev_spaces()

                if result['success']:
                    st.success("✅ Dev spaces deleted. Production unchanged.")
                else:
                    st.warning(f"Warning: {result['error']}")

    # Applied fixes detail
    if loop_result and loop_result['fixes_applied']:
        st.markdown("---")
        with st.expander(f"📝 Applied Fixes ({len(loop_result['fixes_applied'])})"):
            for i, fix in enumerate(loop_result['fixes_applied'][:20], 1):
                st.markdown(f"{i}. {format_fix_description(fix)}")
            if len(loop_result['fixes_applied']) > 20:
                st.caption(f"... and {len(loop_result['fixes_applied']) - 20} more")

    # Restart button
    st.markdown("---")
    if st.button("🔄 Start New Enhancement"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
