"""
Standalone Demo of Enhanced Streamlit UI

Run this to see the beautiful enhancement UI in action:
    streamlit run app/demo_ui.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from pages.enhance_real import render_enhancement_page  # Using REAL batch scorer, not mock

# Configure page
st.set_page_config(
    page_title="Genie Enhancement Demo",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Run the enhancement page
render_enhancement_page()
