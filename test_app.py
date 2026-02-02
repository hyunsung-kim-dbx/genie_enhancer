"""
Simple test app to verify Databricks Apps deployment works.
"""
import streamlit as st

st.set_page_config(
    page_title="Test App",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Databricks App Test")
st.write("If you can see this, the app deployment is working!")

st.success("Deployment successful!")

st.markdown("---")
st.write("Next step: Load the full Genie Enhancement UI")
