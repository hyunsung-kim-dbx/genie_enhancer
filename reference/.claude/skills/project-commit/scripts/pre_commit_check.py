#!/usr/bin/env python3
"""
Pre-commit validation script for Genie Lamp Agent.

Runs tests and validates code before committing.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            return False, result.stderr + "\n" + result.stdout
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False, str(e)


def main():
    """Run all pre-commit checks."""
    print("=" * 60)
    print("Pre-commit Validation for Genie Lamp Agent")
    print("=" * 60)

    # Find project root (where .git directory is)
    current_dir = Path.cwd()
    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / ".git").exists():
            break
        project_root = project_root.parent

    print(f"\n📁 Project root: {project_root}")

    # Change to project root
    import os
    os.chdir(project_root)

    all_passed = True

    # Check 1: Verify virtual environment exists
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print("\n❌ Virtual environment not found at .venv/bin/python")
        print("   Run: python -m venv .venv && .venv/bin/pip install -r requirements.txt")
        return 1

    print(f"\n✅ Virtual environment found: {venv_python}")

    # Check 2: Run pytest
    success, output = run_command(
        [str(venv_python), "-m", "pytest", "tests/", "-v"],
        "Running tests"
    )

    if not success:
        print("\n" + "=" * 60)
        print("Test Output:")
        print("=" * 60)
        print(output)
        all_passed = False

    # Check 3: Check for sensitive files
    print("\n🔍 Checking for sensitive files...")
    sensitive_patterns = [".env", "*.token", "credentials.json"]

    result = subprocess.run(
        ["git", "diff", "--staged", "--name-only"],
        capture_output=True,
        text=True,
    )

    staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
    sensitive_found = []

    for pattern in sensitive_patterns:
        for file in staged_files:
            if pattern.replace("*", "") in file:
                sensitive_found.append(file)

    if sensitive_found:
        print(f"❌ Sensitive files found in staging: {', '.join(sensitive_found)}")
        print("   Please unstage these files before committing")
        all_passed = False
    else:
        print("✅ No sensitive files detected")

    # Check 4: Verify files are staged
    if not staged_files or (len(staged_files) == 1 and staged_files[0] == ""):
        print("\n⚠️  No files are staged for commit")
        print("   Use 'git add <files>' to stage files first")
        return 1

    print(f"\n✅ {len(staged_files)} file(s) staged for commit:")
    for file in staged_files[:10]:  # Show first 10
        print(f"   - {file}")
    if len(staged_files) > 10:
        print(f"   ... and {len(staged_files) - 10} more")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All pre-commit checks passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some pre-commit checks failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
