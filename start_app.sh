#!/bin/bash
# Startup script for Databricks App

# Set Python path to include source code directory
export PYTHONPATH="/app/python/source_code:$PYTHONPATH"

# Change to source code directory
cd /app/python/source_code

# Start uvicorn
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
