"""
Genie Space Enhancement Tool - Redirect

This file exists for backwards compatibility.
The main app has been moved to app.py for Databricks Apps compatibility.

Run with:
    streamlit run app/app.py

Or for Databricks Apps deployment:
    databricks apps deploy genie-enhancer --source-code-path /Workspace/Users/xxx/genie_enhancer/app
"""

import sys
import os

# Redirect to app.py
print("=" * 60)
print("NOTICE: main.py has been replaced by app.py")
print("=" * 60)
print()
print("For local development:")
print("  streamlit run app/app.py")
print()
print("For Databricks Apps deployment:")
print("  1. databricks apps create genie-enhancer")
print("  2. databricks sync ./app /Workspace/Users/$USER/genie-enhancer")
print("  3. databricks apps deploy genie-enhancer \\")
print("       --source-code-path /Workspace/Users/$USER/genie-enhancer")
print()
print("=" * 60)

# Run app.py
if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    os.system(f"streamlit run {app_path}")
