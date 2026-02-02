#!/usr/bin/env python3
"""
Development Deployment Script for Genie Lamp Agent

Automates the complete development deployment workflow:
1. Build frontend
2. Deploy bundle to dev environment
3. Start app (initial deployment only)
4. Deploy app with dev source code path

Configuration:
- Environment: dev
- Profile: krafton-sandbox
- Source Code Path: /Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files
- App Name: genie-lamp-agent-dev
"""

import subprocess
import sys
import argparse
import os
from pathlib import Path


def run_command(command, description, cwd=None):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"   Command: {command}")
    if cwd:
        print(f"   Working directory: {cwd}")

    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)

    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"   stderr: {result.stderr}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        return False

    print(f"✅ {description} completed")
    if result.stdout:
        # For long outputs, show a preview
        lines = result.stdout.strip().split('\n')
        if len(lines) > 10:
            print(f"   Output (first 5 lines):")
            for line in lines[:5]:
                print(f"   {line}")
            print(f"   ... ({len(lines) - 10} more lines)")
            print(f"   Output (last 5 lines):")
            for line in lines[-5:]:
                print(f"   {line}")
        else:
            for line in lines:
                print(f"   {line}")

    return True


def deploy_dev(is_initial_deployment):
    """
    Deploy Genie Lamp Agent to development environment.

    Args:
        is_initial_deployment: True for first deployment, False for updates
    """

    # Hardcoded development configuration
    APP_NAME = "genie-lamp-agent-dev"
    TARGET_ENV = "dev"
    PROFILE = "krafton-sandbox"
    SOURCE_CODE_PATH = "/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files"

    print(f"\n{'='*70}")
    print(f"🚀 Genie Lamp Agent - Development Deployment")
    print(f"{'='*70}")
    print(f"   App Name: {APP_NAME}")
    print(f"   Environment: {TARGET_ENV}")
    print(f"   Profile: {PROFILE}")
    print(f"   Source Code Path: {SOURCE_CODE_PATH}")
    print(f"   Deployment Type: {'Initial' if is_initial_deployment else 'Update'}")
    print(f"{'='*70}\n")

    # Validate we're in project root
    if not os.path.isfile("databricks.yml"):
        print(f"❌ Error: databricks.yml not found in current directory")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Make sure you're running this from the project root")
        return False

    # Validate frontend directory exists
    if not os.path.isdir("frontend"):
        print(f"❌ Error: frontend directory not found")
        print(f"   Make sure you're running this from the project root")
        return False

    # Step 1: Build frontend
    print(f"\n{'='*70}")
    print(f"📦 Step 1: Building Frontend")
    print(f"{'='*70}")

    frontend_build_cmd = "npm run build"
    if not run_command(frontend_build_cmd, "Frontend build", cwd="frontend"):
        print(f"\n❌ Frontend build failed. Deployment aborted.")
        return False

    # Return to project root (subprocess already handles cwd, but print for clarity)
    print(f"\n✅ Frontend build completed successfully")

    # Step 2: Bundle deploy
    print(f"\n{'='*70}")
    print(f"📦 Step 2: Deploying Bundle")
    print(f"{'='*70}")

    bundle_cmd = f"databricks bundle deploy -t {TARGET_ENV} -p {PROFILE}"
    if not run_command(bundle_cmd, "Bundle deploy"):
        print(f"\n❌ Bundle deploy failed. Deployment aborted.")
        return False

    # Step 3: App start (only for initial deployment)
    if is_initial_deployment:
        print(f"\n{'='*70}")
        print(f"🚀 Step 3: Starting App (Initial Deployment)")
        print(f"{'='*70}")

        start_cmd = f"databricks apps start {APP_NAME} -p {PROFILE}"
        if not run_command(start_cmd, "App start"):
            print(f"\n❌ App start failed. Deployment aborted.")
            return False
    else:
        print(f"\n{'='*70}")
        print(f"⏭️  Step 3: Skipped (Update Deployment)")
        print(f"{'='*70}")
        print(f"   App start is only needed for initial deployments")

    # Step 4: App deploy
    print(f"\n{'='*70}")
    print(f"🚀 Step 4: Deploying App")
    print(f"{'='*70}")

    deploy_cmd = f"databricks apps deploy {APP_NAME} -p {PROFILE} --source-code-path {SOURCE_CODE_PATH}"
    if not run_command(deploy_cmd, "App deploy"):
        print(f"\n❌ App deploy failed. Deployment aborted.")
        return False

    # Success summary
    print(f"\n{'='*70}")
    print(f"✅ Development Deployment Completed Successfully!")
    print(f"{'='*70}\n")
    print(f"📱 Access your dev app:")
    print(f"   Workspace > Apps > {APP_NAME}")
    print(f"\n🔍 Verify deployment:")
    print(f"   databricks apps list -p {PROFILE} | grep {APP_NAME}")
    print(f"   databricks apps get {APP_NAME} -p {PROFILE}")
    print(f"\n📋 View logs (if needed):")
    print(f"   databricks apps logs {APP_NAME} -p {PROFILE}")
    print(f"\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Genie Lamp Agent to development environment with automated frontend build",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update existing dev app (most common)
  python deploy_dev.py --update

  # Initial dev deployment (first time only)
  python deploy_dev.py --initial

Development Configuration:
  Environment: dev
  Profile: krafton-sandbox
  App Name: genie-lamp-agent-dev
  Source Code Path: /Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files

Note: This script must be run from the project root directory.
        """
    )

    parser.add_argument(
        "--initial",
        action="store_true",
        help="Flag for initial deployment (includes app start command)",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Flag for update deployment (skips app start command)",
    )

    args = parser.parse_args()

    # Validate flags
    if args.initial and args.update:
        print("❌ Error: Cannot specify both --initial and --update")
        print("   Use --initial for first-time deployment")
        print("   Use --update for subsequent deployments")
        sys.exit(1)

    if not args.initial and not args.update:
        print("❌ Error: Must specify either --initial or --update")
        print("   Use --initial for first-time deployment")
        print("   Use --update for subsequent deployments")
        sys.exit(1)

    # Determine deployment type
    is_initial = args.initial

    # Deploy to development
    success = deploy_dev(is_initial_deployment=is_initial)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
