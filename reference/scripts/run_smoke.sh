#!/usr/bin/env bash
set -euo pipefail

echo "Running tests..."
.venv/bin/python -m pytest tests/ -v

if [ $? -eq 0 ]; then
    date -u +"%Y-%m-%dT%H:%M:%SZ" > .last_test_run
    echo "✓ Tests passed. Stamp created: .last_test_run"
else
    echo "✗ Tests failed. No stamp created."
    exit 1
fi
