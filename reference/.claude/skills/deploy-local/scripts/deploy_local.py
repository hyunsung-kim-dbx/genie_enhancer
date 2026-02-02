#!/usr/bin/env python3
"""
Local deployment script for Genie Lamp Agent.

This script automates local development setup:
1. Checks prerequisites (Python, Node.js, npm, venv)
2. Installs dependencies (backend + frontend)
3. Validates environment configuration
4. Starts backend FastAPI server (uvicorn)
5. Starts frontend Next.js dev server
6. Provides access URLs and instructions

Usage:
    python deploy_local.py
    python deploy_local.py --backend-port 8080 --frontend-port 3001
    python deploy_local.py --skip-install
    python deploy_local.py --backend-only
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def check_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a command is available in PATH.

    Returns:
        Tuple of (is_available, version_or_error)
    """
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return True, version
        return False, result.stderr.strip()
    except FileNotFoundError:
        return False, f"{command} not found in PATH"


def check_prerequisites(project_root: Path) -> bool:
    """
    Check all prerequisites for local deployment.

    Returns:
        True if all prerequisites are met, False otherwise
    """
    print_header("Checking Prerequisites")

    all_ok = True

    # Check Python
    python_ok, python_version = check_command("python3")
    if python_ok:
        print_success(f"Python: {python_version}")
    else:
        print_error(f"Python 3.8+ required: {python_version}")
        all_ok = False

    # Check Node.js
    node_ok, node_version = check_command("node")
    if node_ok:
        print_success(f"Node.js: {node_version}")
    else:
        print_error(f"Node.js 18+ required: {node_version}")
        all_ok = False

    # Check npm
    npm_ok, npm_version = check_command("npm")
    if npm_ok:
        print_success(f"npm: {npm_version}")
    else:
        print_error(f"npm required: {npm_version}")
        all_ok = False

    # Check virtual environment
    venv_path = project_root / ".venv"
    if venv_path.exists():
        print_success(f"Virtual environment: {venv_path}")
    else:
        print_error(f"Virtual environment not found: {venv_path}")
        print_info("Create with: python3 -m venv .venv")
        all_ok = False

    # Check project structure
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"

    if backend_dir.exists():
        print_success(f"Backend directory: {backend_dir}")
    else:
        print_error(f"Backend directory not found: {backend_dir}")
        all_ok = False

    if frontend_dir.exists():
        print_success(f"Frontend directory: {frontend_dir}")
    else:
        print_error(f"Frontend directory not found: {frontend_dir}")
        all_ok = False

    return all_ok


def validate_environment(project_root: Path, skip_check: bool = False) -> bool:
    """
    Validate environment variables.

    Returns:
        True if environment is valid, False otherwise
    """
    if skip_check:
        print_info("Skipping environment validation")
        return True

    print_header("Validating Environment")

    env_file = project_root / ".env"

    if not env_file.exists():
        print_error(f".env file not found: {env_file}")
        print_info("Create with: cp .env.example .env")
        print_info("Then edit .env with your Databricks credentials")
        return False

    print_success(f".env file found: {env_file}")

    # Load .env file
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    # Check required variables
    required_vars = ['DATABRICKS_HOST', 'DATABRICKS_TOKEN']
    all_ok = True

    for var in required_vars:
        if var in env_vars and env_vars[var]:
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is not set or empty")
            all_ok = False

    return all_ok


def install_backend_dependencies(project_root: Path, skip_install: bool = False) -> bool:
    """
    Install backend Python dependencies.

    Returns:
        True if installation successful, False otherwise
    """
    if skip_install:
        print_info("Skipping backend dependency installation")
        return True

    print_header("Installing Backend Dependencies")

    backend_dir = project_root / "backend"
    requirements_file = backend_dir / "requirements.txt"

    if not requirements_file.exists():
        print_error(f"requirements.txt not found: {requirements_file}")
        return False

    venv_python = project_root / ".venv" / "bin" / "python"

    try:
        print_info("Installing backend requirements...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            cwd=str(project_root)
        )
        print_success("Backend dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install backend dependencies: {e}")
        return False


def install_frontend_dependencies(project_root: Path, skip_install: bool = False) -> bool:
    """
    Install frontend npm dependencies.

    Returns:
        True if installation successful, False otherwise
    """
    if skip_install:
        print_info("Skipping frontend dependency installation")
        return True

    print_header("Installing Frontend Dependencies")

    frontend_dir = project_root / "frontend"
    package_json = frontend_dir / "package.json"

    if not package_json.exists():
        print_error(f"package.json not found: {package_json}")
        return False

    try:
        print_info("Running npm install...")
        subprocess.run(
            ["npm", "install"],
            check=True,
            cwd=str(frontend_dir)
        )
        print_success("Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install frontend dependencies: {e}")
        return False


def start_servers(
    project_root: Path,
    backend_port: int,
    frontend_port: int,
    backend_only: bool,
    frontend_only: bool
):
    """
    Start backend and frontend servers.

    Runs servers concurrently with live output.
    """
    print_header("Starting Local Servers")

    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"

    # Load .env file and set environment variables
    env = os.environ.copy()
    env['BACKEND_PORT'] = str(backend_port)
    env['FRONTEND_PORT'] = str(frontend_port)

    # Load environment variables from .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print_info("Loading environment variables from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
        print_success("Environment variables loaded")

    processes = []

    try:
        # Start backend
        if not frontend_only:
            print_info(f"Starting backend server on port {backend_port}...")
            venv_python = project_root / ".venv" / "bin" / "python"
            # Run from project root to support absolute imports (backend.services.*)
            backend_process = subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", str(backend_port)],
                cwd=str(project_root),
                env=env
            )
            processes.append(("Backend", backend_process))
            print_success(f"Backend started (PID: {backend_process.pid})")

        # Start frontend
        if not backend_only:
            print_info(f"Starting frontend server on port {frontend_port}...")
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev", "--", "-p", str(frontend_port)],
                cwd=str(frontend_dir),
                env=env
            )
            processes.append(("Frontend", frontend_process))
            print_success(f"Frontend started (PID: {frontend_process.pid})")

        # Print access information
        print_header("Local Deployment Ready")

        if not frontend_only:
            print(f"{Colors.BOLD}Backend API:{Colors.ENDC}")
            print(f"  • URL: {Colors.OKBLUE}http://localhost:{backend_port}{Colors.ENDC}")
            print(f"  • Swagger UI: {Colors.OKBLUE}http://localhost:{backend_port}/docs{Colors.ENDC}")
            print(f"  • Redoc: {Colors.OKBLUE}http://localhost:{backend_port}/redoc{Colors.ENDC}")
            print()

        if not backend_only:
            print(f"{Colors.BOLD}Frontend Web UI:{Colors.ENDC}")
            print(f"  • URL: {Colors.OKBLUE}http://localhost:{frontend_port}{Colors.ENDC}")
            print()

        print(f"{Colors.WARNING}Press Ctrl+C to stop servers{Colors.ENDC}")
        print()

        # Wait for processes
        for name, process in processes:
            process.wait()

    except KeyboardInterrupt:
        print_warning("\nStopping servers...")
        for name, process in processes:
            process.terminate()
            try:
                process.wait(timeout=5)
                print_success(f"{name} stopped")
            except subprocess.TimeoutExpired:
                print_warning(f"{name} did not stop gracefully, killing...")
                process.kill()
                print_success(f"{name} killed")

    except Exception as e:
        print_error(f"Error during server execution: {e}")
        for name, process in processes:
            process.terminate()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy Genie Lamp Agent locally for development",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Backend server port (default: 8000)"
    )

    parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Frontend server port (default: 3000)"
    )

    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation"
    )

    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment validation"
    )

    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only backend server"
    )

    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only frontend server"
    )

    args = parser.parse_args()

    # Get project root (should be 4 levels up from this script)
    # Script is at: .claude/skills/deploy-local/scripts/deploy_local.py
    # Project root is 4 levels up
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.parent.parent.parent

    print_header("Genie Lamp Agent - Local Deployment")
    print_info(f"Project root: {project_root}")

    # Check prerequisites
    if not check_prerequisites(project_root):
        print_error("\nPrerequisite checks failed. Please fix the issues above.")
        sys.exit(1)

    # Validate environment
    if not validate_environment(project_root, args.skip_env_check):
        print_error("\nEnvironment validation failed. Please fix the issues above.")
        sys.exit(1)

    # Install dependencies
    if not args.frontend_only:
        if not install_backend_dependencies(project_root, args.skip_install):
            print_error("\nBackend dependency installation failed.")
            sys.exit(1)

    if not args.backend_only:
        if not install_frontend_dependencies(project_root, args.skip_install):
            print_error("\nFrontend dependency installation failed.")
            sys.exit(1)

    # Start servers
    start_servers(
        project_root,
        args.backend_port,
        args.frontend_port,
        args.backend_only,
        args.frontend_only
    )


if __name__ == "__main__":
    main()
