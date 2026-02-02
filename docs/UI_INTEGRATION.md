# UI Integration Guide

How to connect the beautiful Streamlit UI to the real enhancement system.

## Overview

The UI components in `app/components/enhancement_ui.py` are designed to be modular and easy to integrate with the actual enhancement logic.

## Quick Integration

### 1. Update Main App

Edit `app/app.py` to use the enhanced UI:

```python
from components.enhancement_ui import EnhancementUI
from lib.batch_scorer import BatchBenchmarkScorer
from lib.category_enhancer import CategoryEnhancer
from lib.applier import BatchApplier

# In your main enhancement flow
def run_enhancement():
    """Run enhancement with beautiful UI."""

    # Phase 1: Scoring with UI
    with st.container():
        st.markdown("### 🎯 Phase 1: Scoring")

        # Show progress
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        # Real scoring
        def update_progress(current, total, question):
            progress_placeholder.progress(current / total)
            status_placeholder.text(f"Scoring {current}/{total}: {question}...")

        scorer = BatchBenchmarkScorer(...)
        score_results = scorer.score(
            benchmarks,
            progress_callback=update_progress  # Add this to scorer
        )

        # Render results with UI
        EnhancementUI.render_failure_breakdown(score_results)

    # Phase 2: Fix generation with UI
    with st.container():
        st.markdown("### 🔧 Phase 2: Fix Generation")

        # Real fix generation
        with st.spinner("Analyzing failures..."):
            enhancer = CategoryEnhancer(...)
            grouped_fixes = enhancer.generate_plan(
                failed_benchmarks=failed_results,
                space_config=space_config
            )

        # Render with UI
        EnhancementUI.render_fix_generation_phase(grouped_fixes)

    # Phase 3: Apply with UI
    with st.container():
        st.markdown("### ⚙️ Phase 3: Applying Fixes")

        # Get old config for comparison
        old_config = space_cloner.get_dev_working_config()

        # Real application with UI callback
        def apply_callback(fix):
            result = applier.apply_single(fix)
            return result

        EnhancementUI.render_apply_phase(
            grouped_fixes,
            apply_callback=apply_callback
        )

        # Get new config
        new_config = space_cloner.get_dev_working_config()

        # Show changes
        EnhancementUI.render_space_changes_summary(old_config, new_config)
```

### 2. Add Progress Callbacks to Batch Scorer

Update `lib/batch_scorer.py` to support UI callbacks:

```python
class BatchBenchmarkScorer:
    def score(
        self,
        benchmarks: List[Dict],
        progress_callback=None  # NEW
    ) -> Dict:
        """Score benchmarks with optional progress callback."""

        # During scoring phase
        for i, benchmark in enumerate(benchmarks):
            # Call progress callback
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=len(benchmarks),
                    question=benchmark['question']
                )

            # Do actual scoring
            result = self._score_single_benchmark(benchmark)
            results.append(result)

        return summary
```

### 3. Add Real-time Updates to Applier

Update `lib/applier.py` to provide fix-by-fix updates:

```python
class BatchApplier:
    def apply_all(
        self,
        space_id: str,
        grouped_fixes: Dict,
        fix_callback=None  # NEW
    ) -> Dict:
        """Apply fixes with optional per-fix callback."""

        applied = []
        failed = []

        for category, fixes in grouped_fixes.items():
            for fix in fixes:
                try:
                    # Apply fix
                    result = self._apply_single_fix(space_id, fix)

                    if result['success']:
                        applied.append(fix)
                    else:
                        failed.append(fix)

                    # Callback for UI update
                    if fix_callback:
                        fix_callback(
                            fix=fix,
                            result=result,
                            category=category
                        )

                except Exception as e:
                    failed.append(fix)
                    if fix_callback:
                        fix_callback(
                            fix=fix,
                            result={'success': False, 'error': str(e)},
                            category=category
                        )

        return {'applied': applied, 'failed': failed}
```

### 4. Use Streamlit Session State

Store enhancement state across reruns:

```python
# Initialize session state
if 'enhancement_state' not in st.session_state:
    st.session_state.enhancement_state = {
        'current_loop': 0,
        'scores_history': [],
        'current_score': 0.0,
        'target_score': 0.90,
        'benchmarks': [],
        'grouped_fixes': None,
        'space_id': None
    }

# Update during enhancement
st.session_state.enhancement_state['current_score'] = score_results['score']
st.session_state.enhancement_state['scores_history'].append({
    'loop': loop_num,
    'score': score_results['score'],
    'target': target_score
})
```

## Detailed Integration Examples

### Example 1: Scoring Phase with Progress

```python
def run_scoring_phase_with_ui(benchmarks: List[Dict]) -> Dict:
    """Run scoring phase with beautiful UI and progress."""

    # Render phase header
    st.markdown("### 🎯 Phase 1: Scoring Benchmarks")

    # Create placeholders for real-time updates
    progress_bar = st.progress(0)
    status_text = st.empty()
    metrics_container = st.container()

    with metrics_container:
        col1, col2, col3 = st.columns(3)
        completed_metric = col1.empty()
        passed_metric = col2.empty()
        failed_metric = col3.empty()

    # Progress callback
    completed = 0
    passed = 0
    failed = 0

    def update_progress(current, total, question, result=None):
        nonlocal completed, passed, failed

        completed = current
        if result:
            if result.get('passed'):
                passed += 1
            else:
                failed += 1

        # Update UI
        progress_bar.progress(current / total)
        status_text.text(f"Scoring {current}/{total}: {question[:60]}...")

        completed_metric.metric("Completed", f"{completed}/{total}")
        passed_metric.metric("Passed", passed, delta=None, delta_color="off")
        failed_metric.metric("Failed", failed, delta=None, delta_color="off")

    # Run actual scoring
    scorer = BatchBenchmarkScorer(
        genie_client=st.session_state.genie_client,
        llm_client=st.session_state.llm_client,
        sql_executor=st.session_state.sql_executor
    )

    # Custom scoring loop with UI updates
    results = []
    for i, benchmark in enumerate(benchmarks):
        update_progress(i, len(benchmarks), benchmark['question'])

        # Score single benchmark
        result = scorer._score_single_benchmark(benchmark)
        results.append(result)

        update_progress(i + 1, len(benchmarks), benchmark['question'], result)

    # Final update
    status_text.text("✅ Scoring complete!")
    time.sleep(0.5)
    status_text.empty()

    # Calculate summary
    score_summary = {
        'score': passed / len(benchmarks) if benchmarks else 0,
        'total': len(benchmarks),
        'passed': passed,
        'failed': failed,
        'results': results
    }

    # Render failure breakdown
    EnhancementUI.render_failure_breakdown(score_summary)

    return score_summary
```

### Example 2: Apply Phase with Real-time Updates

```python
def run_apply_phase_with_ui(
    space_id: str,
    grouped_fixes: Dict[str, List[Dict]]
) -> Dict:
    """Apply fixes with beautiful UI and real-time updates."""

    st.markdown("### ⚙️ Phase 3: Applying Fixes")

    # Get old config
    old_config = st.session_state.space_cloner.get_dev_working_config()

    # Overall progress
    total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())
    overall_progress = st.progress(0)
    overall_status = st.empty()

    applied_count = 0
    failed_count = 0
    applied_fixes = []
    failed_fixes = []

    # Process each category
    for category, fixes in grouped_fixes.items():
        icon, display_name = EnhancementUI._get_category_icon(category)

        # Category status box
        with st.status(f"{icon} {display_name} ({len(fixes)} fixes)", expanded=True) as status:
            cat_progress = st.progress(0)

            for i, fix in enumerate(fixes):
                # Apply fix
                try:
                    result = st.session_state.applier.apply_single(space_id, fix)
                    success = result.get('success', False)

                    if success:
                        applied_fixes.append(fix)
                        applied_count += 1
                        fix_icon = "✅"
                    else:
                        failed_fixes.append(fix)
                        failed_count += 1
                        fix_icon = "❌"

                except Exception as e:
                    failed_fixes.append(fix)
                    failed_count += 1
                    fix_icon = "❌"

                # Update category progress
                cat_progress.progress((i + 1) / len(fixes))

                # Show fix result
                fix_desc = EnhancementUI._format_fix_preview(fix)
                st.markdown(f"{fix_icon} {fix_desc}")

                # Update overall progress
                overall_progress.progress((applied_count + failed_count) / total_fixes)
                overall_status.text(
                    f"Progress: {applied_count + failed_count}/{total_fixes} "
                    f"(✅ {applied_count} | ❌ {failed_count})"
                )

            # Complete category
            status.update(label=f"✅ {display_name} - Complete", state="complete")

    # Clear overall status
    overall_status.empty()

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Applied", applied_count)
    col2.metric("❌ Failed", failed_count)
    success_rate = (applied_count / total_fixes * 100) if total_fixes > 0 else 0
    col3.metric("Success Rate", f"{success_rate:.1f}%")

    # Get new config and show changes
    new_config = st.session_state.space_cloner.get_dev_working_config()
    EnhancementUI.render_space_changes_summary(old_config, new_config)

    return {
        'applied': applied_fixes,
        'failed': failed_fixes,
        'success_rate': success_rate
    }
```

### Example 3: Full Enhancement Loop

```python
def run_full_enhancement_loop():
    """Run full enhancement loop with integrated UI."""

    st.title("🧞 Genie Space Enhancement")

    # Configuration sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        space_id = st.text_input("Space ID", st.session_state.get('space_id', ''))
        target_score = st.slider("Target Score", 0.0, 1.0, 0.90, 0.05)
        max_loops = st.number_input("Max Loops", 1, 10, 3)

        start_button = st.button("🚀 Start Enhancement", type="primary")

    if not start_button:
        # Show initial dashboard
        EnhancementUI.render_overview_dashboard(
            current_score=st.session_state.get('current_score', 0.0),
            target_score=target_score,
            loop_num=1,
            max_loops=max_loops,
            benchmarks_total=len(st.session_state.get('benchmarks', [])),
            benchmarks_passed=0
        )
        return

    # Initialize clients
    initialize_clients(space_id)

    # Load benchmarks
    benchmarks = load_benchmarks()

    # Enhancement loop
    for loop_num in range(1, max_loops + 1):
        st.markdown(f"## 🔄 Enhancement Loop {loop_num}/{max_loops}")

        # Update dashboard
        EnhancementUI.render_overview_dashboard(
            current_score=st.session_state.current_score,
            target_score=target_score,
            loop_num=loop_num,
            max_loops=max_loops,
            benchmarks_total=len(benchmarks),
            benchmarks_passed=int(st.session_state.current_score * len(benchmarks))
        )

        st.markdown("---")

        # Phase 1: Scoring
        score_results = run_scoring_phase_with_ui(benchmarks)

        # Check target
        if score_results['score'] >= target_score:
            st.balloons()
            st.success(f"🎉 Target reached! Score: {score_results['score']:.1%}")
            break

        st.markdown("---")

        # Phase 2: Fix generation
        grouped_fixes = run_fix_generation_phase_with_ui(score_results)

        st.markdown("---")

        # Phase 3: Apply
        apply_result = run_apply_phase_with_ui(space_id, grouped_fixes)

        st.markdown("---")

        # Phase 4: Wait for indexing
        wait_for_indexing_with_ui()

        st.markdown("---")

        # Loop summary
        before_score = st.session_state.current_score
        after_score = score_results['score']
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
            fixes_applied=len(apply_result['applied'])
        )

    # Show final history
    if st.session_state.scores_history:
        EnhancementUI.render_score_history(st.session_state.scores_history)
```

## Testing

Test the UI components independently:

```python
# Test scoring phase UI
def test_scoring_ui():
    mock_benchmarks = [
        {'question': f'Test question {i}'}
        for i in range(10)
    ]

    mock_results = {
        'score': 0.7,
        'total': 10,
        'passed': 7,
        'results': [...]  # Mock result data
    }

    EnhancementUI.render_failure_breakdown(mock_results)

# Test apply phase UI
def test_apply_ui():
    mock_fixes = {
        'metadata_add': [
            {'type': 'add_synonym', 'synonym': 'test', 'column': 'col1'}
        ]
    }

    def mock_callback(fix):
        time.sleep(0.1)
        return {'success': True}

    EnhancementUI.render_apply_phase(mock_fixes, apply_callback=mock_callback)
```

## Deployment

1. **Local testing:**
   ```bash
   streamlit run app/demo_ui.py
   ```

2. **Databricks Apps:**
   ```bash
   databricks apps create genie-enhancer
   databricks apps deploy genie-enhancer
   ```

## Next Steps

1. Replace demo data with real data sources
2. Add error handling and logging
3. Add authentication/authorization
4. Add state persistence (database/file)
5. Add export capabilities (PDF reports, etc.)
6. Add notification system (email, Slack)
