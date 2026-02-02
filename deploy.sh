#!/bin/bash
# Databricks Apps Deployment Script
#
# Prerequisites:
#   1. Databricks CLI installed and configured
#   2. Authentication set up (databricks auth login)
#
# Usage:
#   ./deploy.sh                    # Deploy to your workspace
#   ./deploy.sh --app-name myapp   # Custom app name

set -e

# Default values
APP_NAME="${APP_NAME:-genie-enhancer}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --app-name)
            APP_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./deploy.sh [--app-name NAME]"
            echo ""
            echo "Options:"
            echo "  --app-name NAME   Name for the Databricks App (default: genie-enhancer)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "================================================"
echo "Deploying Genie Enhancer to Databricks Apps"
echo "================================================"
echo ""
echo "App Name: $APP_NAME"
echo ""

# Get current user
DATABRICKS_USER=$(databricks current-user me 2>/dev/null | jq -r '.userName' || echo "")

if [ -z "$DATABRICKS_USER" ]; then
    echo "Error: Could not get Databricks user. Please run: databricks auth login"
    exit 1
fi

echo "Databricks User: $DATABRICKS_USER"
WORKSPACE_PATH="/Users/$DATABRICKS_USER/$APP_NAME"
echo "Workspace Path: $WORKSPACE_PATH"
echo ""

# Step 1: Create app (if not exists)
echo "[1/4] Creating app (if not exists)..."
databricks apps create "$APP_NAME" 2>/dev/null || echo "App already exists or created"

# Step 2: Sync entire project (app needs lib, prompts)
echo ""
echo "[2/4] Syncing project to workspace..."
echo "  Syncing: app/, lib/, prompts/, requirements.txt"

# Sync directories needed by the app
databricks sync . "$WORKSPACE_PATH" \
    --include "app/**" \
    --include "lib/**" \
    --include "prompts/**" \
    --include "requirements.txt" \
    --exclude "**/__pycache__/**" \
    --exclude "*.pyc" \
    --exclude ".git/**" \
    --exclude "benchmarks/**" \
    --exclude "docs/**" \
    --exclude "workflows/**" \
    --exclude "schema/**" \
    --exclude "utils/**" \
    --watch=false

# Step 3: Move app.yaml to root for Databricks Apps
echo ""
echo "[3/4] Preparing app configuration..."

# Step 4: Deploy
echo ""
echo "[4/4] Deploying app..."
databricks apps deploy "$APP_NAME" --source-code-path "/Workspace$WORKSPACE_PATH/app"

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Your app should be available at:"
echo "  https://<workspace-host>/apps/$APP_NAME"
echo ""
echo "To check status:"
echo "  databricks apps get $APP_NAME"
echo ""
echo "To view logs:"
echo "  databricks apps get-events $APP_NAME"
echo ""
echo "To delete:"
echo "  databricks apps delete $APP_NAME"
echo ""
