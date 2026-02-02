"""
Databricks App Entry Point for Genie Space Enhancement System

This is the main entry point for the Databricks App.
It launches the Streamlit UI for interactive Genie Space enhancement.

Deployment:
    1. Upload this repo to Databricks Workspace
    2. Deploy as Databricks App using config/app.yaml
    3. Access via Apps UI

Local Development:
    streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from pages.enhance import render_enhancement_page

# Configure page
st.set_page_config(
    page_title="Genie Space Enhancement System",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Databricks branding
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF3621;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🧞 Genie Space Enhancement System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated improvement system using benchmark-driven evaluation and AI-powered enhancements</div>', unsafe_allow_html=True)

# Render the enhancement page
render_enhancement_page()
