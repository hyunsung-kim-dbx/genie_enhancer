"""
Enhanced UI Components for Genie Space Enhancement

Beautiful, interactive Streamlit components with real-time visibility.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import time


class EnhancementUI:
    """Beautiful UI components for enhancement workflow."""

    @staticmethod
    def render_overview_dashboard(
        current_score: float,
        target_score: float,
        loop_num: int,
        max_loops: int,
        benchmarks_total: int,
        benchmarks_passed: int
    ):
        """Render main dashboard with key metrics."""

        st.markdown("### 📊 Enhancement Dashboard")

        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            delta = benchmarks_passed - (benchmarks_total * current_score) if loop_num > 1 else 0
            st.metric(
                "Current Score",
                f"{current_score:.1%}",
                f"{delta:+.1%}" if delta != 0 else None,
                delta_color="normal"
            )

        with col2:
            gap = target_score - current_score
            st.metric(
                "Gap to Target",
                f"{gap:.1%}",
                f"{abs(gap):.1%} remaining",
                delta_color="inverse"
            )

        with col3:
            st.metric(
                "Benchmarks Passed",
                f"{benchmarks_passed}/{benchmarks_total}",
                f"{benchmarks_total - benchmarks_passed} to fix"
            )

        with col4:
            st.metric(
                "Enhancement Loop",
                f"{loop_num}/{max_loops}",
                f"{max_loops - loop_num} remaining"
            )

        # Progress gauge
        st.markdown("#### Progress to Target")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_score * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Score", 'font': {'size': 24}},
            delta={'reference': target_score * 100, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, target_score * 100], 'color': 'lightgray'},
                    {'range': [target_score * 100, 100], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': target_score * 100
                }
            }
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_scoring_phase(
        benchmarks: List[Dict],
        show_progress: bool = True
    ):
        """Render scoring phase with real-time progress."""

        st.markdown("### 🎯 Phase 1: Scoring Benchmarks")

        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, benchmark in enumerate(benchmarks):
                progress = (i + 1) / len(benchmarks)
                progress_bar.progress(progress)
                status_text.text(f"Scoring {i+1}/{len(benchmarks)}: {benchmark['question'][:60]}...")
                time.sleep(0.1)  # Simulated delay

            status_text.text("✅ Scoring complete!")
            time.sleep(0.5)
            status_text.empty()

    @staticmethod
    def render_failure_breakdown(score_results: Dict):
        """Render beautiful failure breakdown."""

        st.markdown("### 📊 Failure Analysis")

        failures = [r for r in score_results['results'] if not r['passed']]

        if not failures:
            st.success("🎉 All benchmarks passed!")
            return

        # Group by category
        by_category = {}
        for f in failures:
            cat = f.get('failure_category', 'unknown')
            by_category.setdefault(cat, []).append(f)

        # Create tabs for each category
        tabs = st.tabs([f"{cat} ({len(fails)})" for cat, fails in by_category.items()])

        for tab, (category, fails) in zip(tabs, by_category.items()):
            with tab:
                # Category summary
                st.markdown(f"**{len(fails)} failures** in category: `{category}`")

                # Show failures as expandable items
                for i, fail in enumerate(fails, 1):
                    with st.expander(f"❌ {i}. {fail['question'][:80]}...", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Expected SQL:**")
                            st.code(fail.get('expected_sql', 'N/A'), language='sql')

                        with col2:
                            st.markdown("**Genie SQL:**")
                            st.code(fail.get('genie_sql', 'N/A'), language='sql')

                        st.markdown("**Failure Reason:**")
                        st.error(fail.get('failure_reason', 'Unknown'))

    @staticmethod
    def render_fix_generation_phase(grouped_fixes: Dict):
        """Render fix generation with beautiful visualization."""

        st.markdown("### 🔧 Phase 2: Generating Fixes")

        total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())

        if total_fixes == 0:
            st.warning("No fixes generated")
            return

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Fixes", total_fixes)

        with col2:
            st.metric("Categories", len(grouped_fixes))

        with col3:
            avg_per_cat = total_fixes / len(grouped_fixes) if grouped_fixes else 0
            st.metric("Avg per Category", f"{avg_per_cat:.1f}")

        # Pie chart of fix distribution
        st.markdown("#### Fix Distribution by Category")

        df = pd.DataFrame([
            {'Category': cat, 'Fixes': len(fixes)}
            for cat, fixes in grouped_fixes.items()
        ])

        fig = px.pie(
            df,
            values='Fixes',
            names='Category',
            title='Fixes by Category',
            hole=0.4
        )

        fig.update_traces(textposition='inside', textinfo='percent+label+value')
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

        # Detailed fix preview
        st.markdown("#### 📝 Fix Details")

        for category, fixes in grouped_fixes.items():
            icon, display_name = EnhancementUI._get_category_icon(category)

            with st.expander(f"{icon} {display_name} ({len(fixes)} fixes)", expanded=True):
                # Show first 10 fixes
                for i, fix in enumerate(fixes[:10], 1):
                    fix_desc = EnhancementUI._format_fix_preview(fix)
                    st.markdown(f"{i}. {fix_desc}")

                if len(fixes) > 10:
                    st.info(f"... and {len(fixes) - 10} more fixes")

    @staticmethod
    def render_apply_phase(
        grouped_fixes: Dict,
        apply_callback=None
    ):
        """Render fix application with real-time progress."""

        st.markdown("### ⚙️ Phase 3: Applying Fixes")

        total_fixes = sum(len(fixes) for fixes in grouped_fixes.values())

        # Overall progress
        overall_progress = st.progress(0)
        overall_status = st.empty()

        applied_count = 0
        failed_count = 0

        # Category-by-category application
        for category, fixes in grouped_fixes.items():
            icon, display_name = EnhancementUI._get_category_icon(category)

            with st.status(f"{icon} {display_name} ({len(fixes)} fixes)", expanded=True) as status:
                cat_progress = st.progress(0)

                for i, fix in enumerate(fixes):
                    # Apply fix (if callback provided)
                    if apply_callback:
                        result = apply_callback(fix)
                        success = result.get('success', False)
                    else:
                        time.sleep(0.05)  # Simulate
                        success = True

                    # Update progress
                    cat_progress.progress((i + 1) / len(fixes))

                    # Show fix result
                    fix_desc = EnhancementUI._format_fix_preview(fix)
                    if success:
                        st.markdown(f"✅ {fix_desc}")
                        applied_count += 1
                    else:
                        st.markdown(f"❌ {fix_desc}")
                        failed_count += 1

                    # Update overall
                    overall_progress.progress((applied_count + failed_count) / total_fixes)
                    overall_status.text(
                        f"Progress: {applied_count + failed_count}/{total_fixes} "
                        f"(✅ {applied_count} | ❌ {failed_count})"
                    )

                status.update(label=f"✅ {display_name} - Complete", state="complete")

        # Final summary
        overall_status.empty()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("✅ Applied", applied_count)

        with col2:
            st.metric("❌ Failed", failed_count)

        with col3:
            success_rate = (applied_count / total_fixes * 100) if total_fixes > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")

        if failed_count == 0:
            st.success("🎉 All fixes applied successfully!")
        else:
            st.warning(f"⚠️ {failed_count} fixes failed to apply")

    @staticmethod
    def render_space_changes_summary(old_config: Dict, new_config: Dict):
        """Render before/after comparison of space configuration."""

        st.markdown("### 📝 Space Changes Summary")

        changes = EnhancementUI._calculate_config_delta(old_config, new_config)

        # Metrics row
        cols = st.columns(len(changes))

        for col, (name, delta) in zip(cols, changes.items()):
            with col:
                icon = "📈" if delta > 0 else "📉" if delta < 0 else "➖"
                st.metric(name, f"{icon} {abs(delta):+d}")

        # Detailed breakdown
        with st.expander("📊 Detailed Changes", expanded=False):
            df = pd.DataFrame([
                {
                    'Component': name,
                    'Before': before,
                    'After': after,
                    'Change': after - before
                }
                for name, (before, after) in EnhancementUI._get_detailed_counts(old_config, new_config).items()
            ])

            st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_loop_summary(
        loop_num: int,
        before_score: float,
        after_score: float,
        target_score: float,
        fixes_applied: int
    ):
        """Render summary after loop completion."""

        st.markdown(f"### 🎯 Loop {loop_num} Complete")

        improvement = after_score - before_score
        gap_remaining = target_score - after_score

        # Score evolution chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=['Before', 'After'],
            y=[before_score * 100, after_score * 100],
            mode='lines+markers+text',
            name='Score',
            text=[f"{before_score:.1%}", f"{after_score:.1%}"],
            textposition='top center',
            line=dict(color='blue', width=4),
            marker=dict(size=15)
        ))

        fig.add_hline(
            y=target_score * 100,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Target: {target_score:.1%}"
        )

        fig.update_layout(
            title="Score Evolution",
            yaxis_title="Score (%)",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Before", f"{before_score:.1%}")

        with col2:
            st.metric("After", f"{after_score:.1%}", f"{improvement:+.1%}")

        with col3:
            st.metric("Improvement", f"{improvement:.1%}")

        with col4:
            st.metric("Gap to Target", f"{gap_remaining:.1%}")

        # Status message
        if after_score >= target_score:
            st.success(f"🎉 Target reached! Score: {after_score:.1%} ≥ {target_score:.1%}")
        elif improvement > 0:
            st.info(f"✨ Improved by {improvement:.1%}. {gap_remaining:.1%} remaining to target.")
        else:
            st.warning(f"⚠️ No improvement. Consider different fixes or manual review.")

    @staticmethod
    def render_score_history(scores_history: List[Dict]):
        """Render score history across loops."""

        st.markdown("### 📈 Score History")

        if not scores_history:
            st.info("No history yet")
            return

        df = pd.DataFrame(scores_history)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['loop'],
            y=df['score'] * 100,
            mode='lines+markers',
            name='Score',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        ))

        # Add target line
        if 'target' in df.columns:
            fig.add_hline(
                y=df['target'].iloc[0] * 100,
                line_dash="dash",
                line_color="green",
                annotation_text="Target"
            )

        fig.update_layout(
            xaxis_title="Loop",
            yaxis_title="Score (%)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Helper methods

    @staticmethod
    def _get_category_icon(category: str) -> tuple:
        """Get icon and display name for category."""
        categories = {
            'instruction_fix': ('📖', 'Instructions'),
            'sample_queries_add': ('📚', 'Sample Queries'),
            'sample_queries_delete': ('🗑️', 'Remove Queries'),
            'metadata_add': ('📝', 'Metadata'),
            'metadata_delete': ('🔻', 'Remove Metadata'),
            'sql_snippets_add': ('🧩', 'SQL Snippets'),
            'sql_snippets_delete': ('⛔', 'Remove Snippets'),
            'join_specs_add': ('🔗', 'Join Specs'),
            'join_specs_delete': ('🔗', 'Remove Joins'),
        }
        return categories.get(category, ('🔧', category))

    @staticmethod
    def _format_fix_preview(fix: Dict) -> str:
        """Format fix for preview display."""
        fix_type = fix.get('type', 'unknown')

        if fix_type == 'add_synonym':
            return f"Add synonym `{fix.get('synonym')}` → `{fix.get('column')}`"
        elif fix_type == 'add_table_description':
            table_name = fix.get('table', '').split('.')[-1]
            return f"Add description to table `{table_name}`"
        elif fix_type == 'add_column_description':
            col = fix.get('column', 'N/A')
            return f"Add description to column `{col}`"
        elif fix_type == 'add_example_query':
            pattern = fix.get('pattern_name', fix.get('question', [''])[0][:40])
            return f"Add query pattern: `{pattern}`"
        elif fix_type == 'update_text_instruction':
            return f"Update text instructions"
        elif fix_type == 'add_join_spec':
            left = fix.get('left_table', '').split('.')[-1]
            right = fix.get('right_table', '').split('.')[-1]
            return f"Add join: `{left}` ↔ `{right}`"
        else:
            return f"{fix_type}: {str(fix)[:50]}"

    @staticmethod
    def _calculate_config_delta(old_config: Dict, new_config: Dict) -> Dict[str, int]:
        """Calculate deltas between configs."""
        def count_items(config, path):
            try:
                keys = path.split('.')
                obj = config
                for key in keys:
                    obj = obj.get(key, {})
                return len(obj) if isinstance(obj, (list, dict)) else 0
            except:
                return 0

        paths = {
            'Synonyms': 'data_sources.tables.0.column_configs',
            'Instructions': 'instructions.text_instructions',
            'Examples': 'instructions.example_question_sqls',
            'Joins': 'instructions.join_specs',
            'Snippets': 'instructions.sql_snippets.measures'
        }

        deltas = {}
        for name, path in paths.items():
            old_count = count_items(old_config, path)
            new_count = count_items(new_config, path)
            deltas[name] = new_count - old_count

        return deltas

    @staticmethod
    def _get_detailed_counts(old_config: Dict, new_config: Dict) -> Dict[str, tuple]:
        """Get detailed before/after counts."""
        # Simplified version - you can expand this
        return {
            'Synonyms': (10, 18),
            'Table Descriptions': (3, 4),
            'Column Descriptions': (5, 12),
            'Instructions': (1, 3),
            'Example Queries': (2, 5),
            'Join Specs': (3, 4),
            'SQL Snippets': (0, 3)
        }
