"""
Enhanced Enhancement Page with Beautiful UI

Real-time visibility into the enhancement process with
interactive visualizations and progress tracking.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from components.enhancement_ui import EnhancementUI
import time


def render_enhancement_page():
    """Render the main enhancement page with beautiful UI."""

    st.title("🧞 Genie Space Enhancement")
    st.markdown("Real-time enhancement with visual feedback")

    # Initialize session state
    if 'enhancement_state' not in st.session_state:
        st.session_state.enhancement_state = 'ready'
        st.session_state.current_loop = 0
        st.session_state.current_score = 0.0
        st.session_state.scores_history = []

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        space_id = st.text_input("Genie Space ID", value="01f0f5c8...")
        target_score = st.slider("Target Score", 0.0, 1.0, 0.90, 0.05)
        max_loops = st.number_input("Max Loops", 1, 10, 3)

        batch_mode = st.checkbox("Use Batch Scoring", value=True)
        if batch_mode:
            genie_concurrent = st.slider("Genie Concurrent Calls", 1, 10, 3)

        st.divider()

        start_button = st.button("🚀 Start Enhancement", type="primary", use_container_width=True)

    # Main content area
    if start_button:
        run_enhancement_flow(
            space_id=space_id,
            target_score=target_score,
            max_loops=max_loops,
            batch_mode=batch_mode
        )
    else:
        # Show initial dashboard
        render_initial_state(target_score, max_loops)


def render_initial_state(target_score: float, max_loops: int):
    """Render initial state before enhancement starts."""

    # Overview dashboard (placeholder data)
    EnhancementUI.render_overview_dashboard(
        current_score=0.667,
        target_score=target_score,
        loop_num=1,
        max_loops=max_loops,
        benchmarks_total=12,
        benchmarks_passed=8
    )

    st.info("👈 Configure settings in sidebar and click 'Start Enhancement' to begin")

    # Show what will happen
    with st.expander("📖 Enhancement Process", expanded=False):
        st.markdown("""
        ### The enhancement process includes:

        **Phase 1: Scoring**
        - Run all benchmark questions through Genie
        - Compare results with expected outputs
        - Identify failures and categorize them

        **Phase 2: Fix Generation**
        - Analyze failure patterns
        - Generate targeted fixes by category:
          - 📝 Metadata (synonyms, descriptions)
          - 📖 Instructions (business rules)
          - 📚 Sample queries (patterns)
          - 🔗 Join specs (table relationships)

        **Phase 3: Apply Fixes**
        - Apply all fixes to dev-working space
        - Track success/failure per fix
        - Show space configuration changes

        **Phase 4: Validation**
        - Re-score to measure improvement
        - Compare before/after
        - Decide next steps (another loop or promote)
        """)


def run_enhancement_flow(
    space_id: str,
    target_score: float,
    max_loops: int,
    batch_mode: bool
):
    """Run the full enhancement flow with beautiful UI."""

    st.markdown("---")

    # Loop through enhancement cycles
    for loop_num in range(1, max_loops + 1):
        st.markdown(f"## 🔄 Enhancement Loop {loop_num}/{max_loops}")

        # Update dashboard
        EnhancementUI.render_overview_dashboard(
            current_score=st.session_state.current_score,
            target_score=target_score,
            loop_num=loop_num,
            max_loops=max_loops,
            benchmarks_total=12,
            benchmarks_passed=int(st.session_state.current_score * 12)
        )

        st.markdown("---")

        # Phase 1: Scoring
        with st.container():
            score_results = run_scoring_phase()

        # Check if target reached
        if score_results['score'] >= target_score:
            st.balloons()
            st.success(f"🎉 Target reached! Score: {score_results['score']:.1%}")
            break

        st.markdown("---")

        # Phase 2: Fix Generation
        with st.container():
            grouped_fixes = run_fix_generation_phase(score_results)

        st.markdown("---")

        # Phase 3: Apply Fixes
        with st.container():
            old_config = {'dummy': 'config'}  # Would fetch real config
            apply_result = run_apply_phase(grouped_fixes)
            new_config = {'dummy': 'config'}  # Would fetch updated config

            # Show space changes
            EnhancementUI.render_space_changes_summary(old_config, new_config)

        st.markdown("---")

        # Phase 4: Wait for indexing
        st.markdown("### ⏳ Phase 4: Waiting for Genie Indexing")

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(60):
            progress_bar.progress((i + 1) / 60)
            status_text.text(f"Waiting for indexing... {60 - i}s remaining")
            time.sleep(0.05)  # Faster for demo

        status_text.text("✅ Indexing complete")
        time.sleep(0.3)
        status_text.empty()

        st.markdown("---")

        # Loop summary
        before_score = st.session_state.current_score
        after_score = before_score + 0.10  # Simulated improvement
        st.session_state.current_score = after_score

        # Add to history
        st.session_state.scores_history.append({
            'loop': loop_num,
            'score': after_score,
            'target': target_score
        })

        EnhancementUI.render_loop_summary(
            loop_num=loop_num,
            before_score=before_score,
            after_score=after_score,
            target_score=target_score,
            fixes_applied=len(apply_result.get('applied', []))
        )

        st.markdown("---")

    # Final score history
    if st.session_state.scores_history:
        EnhancementUI.render_score_history(st.session_state.scores_history)


def run_scoring_phase():
    """Run scoring phase with UI."""

    # Mock benchmarks
    benchmarks = [
        {'id': f'bench_{i}', 'question': f'Sample question {i}'}
        for i in range(12)
    ]

    EnhancementUI.render_scoring_phase(benchmarks, show_progress=True)

    # Mock results
    score_results = {
        'score': 0.667,
        'total': 12,
        'passed': 8,
        'results': [
            {
                'passed': False,
                'question': '최근 7일간 inZOI의 일별 DAU는?',
                'failure_category': 'missing_synonym',
                'expected_sql': 'SELECT event_date, SUM(active_user) as DAU FROM ...',
                'genie_sql': 'SELECT date, COUNT(*) FROM ...',
                'failure_reason': 'Korean term "일별" not recognized'
            },
            {
                'passed': False,
                'question': '월별 DARPU 추이는?',
                'failure_category': 'wrong_calculation',
                'expected_sql': 'SELECT month, try_divide(SUM(revenue), SUM(users)) ...',
                'genie_sql': 'SELECT month, SUM(revenue) / SUM(users) ...',
                'failure_reason': 'Missing try_divide for safe division'
            },
            {
                'passed': False,
                'question': '지역별 매출 상위 10개는?',
                'failure_category': 'wrong_table',
                'expected_sql': 'SELECT region, SUM(revenue) FROM summary_daily JOIN region_meta ...',
                'genie_sql': 'SELECT country, SUM(amount) FROM transactions ...',
                'failure_reason': 'Used wrong table (transactions instead of summary_daily)'
            },
            {
                'passed': False,
                'question': '신규 유저의 D+7 리텐션은?',
                'failure_category': 'missing_pattern',
                'expected_sql': 'SELECT cohort_date, try_divide(retained, cohort_size) FROM retention WHERE day_plus = 7',
                'genie_sql': None,
                'failure_reason': 'No SQL generated - missing retention pattern'
            }
        ] + [
            {'passed': True, 'question': f'Q{i}', 'failure_category': None}
            for i in range(8)
        ]
    }

    # Render failure breakdown
    EnhancementUI.render_failure_breakdown(score_results)

    return score_results


def run_fix_generation_phase(score_results):
    """Run fix generation phase with UI."""

    st.markdown("### 🔧 Phase 2: Generating Fixes")

    # Simulate fix generation with progress
    with st.spinner("Analyzing failures and generating fixes..."):
        time.sleep(1)

    # Mock grouped fixes
    grouped_fixes = {
        'metadata_add': [
            {'type': 'add_synonym', 'synonym': '일별', 'column': 'event_date', 'table': 'summary_daily'},
            {'type': 'add_synonym', 'synonym': '매출', 'column': 'cash_revenue', 'table': 'summary_daily'},
            {'type': 'add_table_description', 'table': 'summary_daily', 'description': ['Daily summary table']},
            {'type': 'add_column_description', 'column': 'active_user', 'description': ['Daily active users']}
        ],
        'instruction_fix': [
            {'type': 'update_text_instruction', 'content': ['Date interpretation rules', 'Metric calculations']},
        ],
        'sample_queries_add': [
            {'type': 'add_example_query', 'pattern_name': 'daily_kpi_calculation'},
            {'type': 'add_example_query', 'pattern_name': 'safe_division_pattern'},
            {'type': 'add_example_query', 'pattern_name': 'retention_calculation'}
        ],
        'join_specs_add': [
            {'type': 'add_join_spec', 'left_table': 'summary_daily', 'right_table': 'region_meta'},
        ]
    }

    EnhancementUI.render_fix_generation_phase(grouped_fixes)

    return grouped_fixes


def run_apply_phase(grouped_fixes):
    """Run apply phase with UI."""

    # Mock application (no callback = simulated)
    result = EnhancementUI.render_apply_phase(
        grouped_fixes,
        apply_callback=None  # Pass real callback here in production
    )

    return {
        'applied': list(range(sum(len(fixes) for fixes in grouped_fixes.values()))),
        'failed': []
    }


if __name__ == "__main__":
    render_enhancement_page()
