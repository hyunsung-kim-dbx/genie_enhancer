#!/usr/bin/env python3
"""
Stop local Genie Lamp Agent development servers.

This script stops the backend and frontend servers running locally.
It identifies processes by port number and stops them gracefully
(or forcefully if needed).

Usage:
    python stop_local.py
    python stop_local.py --backend-only
    python stop_local.py --force
"""

import os
import sys
import argparse
import subprocess
import time
from typing import List, Optional


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


def find_process_on_port(port: int) -> Optional[List[int]]:
    """
    Find process IDs listening on the given port.

    Args:
        port: Port number to check

    Returns:
        List of PIDs or None if no process found
    """
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            return pids if pids else None
        return None
    except Exception as e:
        print_error(f"Error finding process on port {port}: {e}")
        return None


def stop_process(pid: int, force: bool = False, timeout: int = 5) -> bool:
    """
    Stop a process gracefully or forcefully.

    Args:
        pid: Process ID to stop
        force: If True, use SIGKILL immediately
        timeout: Seconds to wait for graceful shutdown

    Returns:
        True if process was stopped, False otherwise
    """
    try:
        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 checks if process exists
        except ProcessLookupError:
            return True  # Process already gone
        except PermissionError:
            print_error(f"No permission to stop process {pid}")
            return False

        if force:
            # Force kill immediately
            os.kill(pid, 9)  # SIGKILL
            time.sleep(0.5)
            return True
        else:
            # Try graceful shutdown first
            os.kill(pid, 15)  # SIGTERM

            # Wait for process to stop
            for _ in range(timeout * 2):  # Check every 0.5 seconds
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    return True  # Process stopped

            # If still running, force kill
            print_warning(f"Process {pid} didn't stop gracefully, force killing...")
            try:
                os.kill(pid, 9)  # SIGKILL
                time.sleep(0.5)
                return True
            except ProcessLookupError:
                return True
            except Exception as e:
                print_error(f"Failed to force kill process {pid}: {e}")
                return False
    except Exception as e:
        print_error(f"Error stopping process {pid}: {e}")
        return False


def stop_server(port: int, name: str, force: bool = False) -> bool:
    """
    Stop server running on the given port.

    Args:
        port: Port number the server is running on
        name: Display name of the server
        force: If True, force kill immediately

    Returns:
        True if stopped successfully, False otherwise
    """
    print_info(f"Checking for {name} on port {port}...")

    pids = find_process_on_port(port)

    if not pids:
        print_info(f"No {name} found on port {port}")
        return True

    print_success(f"Found {name} (PID{'s' if len(pids) > 1 else ''}: {', '.join(map(str, pids))})")

    all_stopped = True
    for pid in pids:
        print_info(f"Stopping {name} (PID: {pid})...")
        if stop_process(pid, force):
            print_success(f"{name} stopped (PID: {pid})")
        else:
            print_error(f"Failed to stop {name} (PID: {pid})")
            all_stopped = False

    return all_stopped


def verify_port_free(port: int) -> bool:
    """
    Verify that a port is free.

    Args:
        port: Port number to check

    Returns:
        True if port is free, False otherwise
    """
    pids = find_process_on_port(port)
    return pids is None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stop local Genie Lamp Agent development servers",
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
        "--backend-only",
        action="store_true",
        help="Stop only backend server"
    )

    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Stop only frontend server"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force kill processes without graceful shutdown"
    )

    args = parser.parse_args()

    print_header("Stopping Local Genie Lamp Agent Servers")

    backend_stopped = True
    frontend_stopped = True

    # Stop backend
    if not args.frontend_only:
        backend_stopped = stop_server(
            args.backend_port,
            "backend server",
            args.force
        )

    # Stop frontend
    if not args.backend_only:
        frontend_stopped = stop_server(
            args.frontend_port,
            "frontend server",
            args.force
        )

    # Verify ports are free
    print_header("Verification")

    backend_free = True
    frontend_free = True

    if not args.frontend_only:
        backend_free = verify_port_free(args.backend_port)
        if backend_free:
            print_success(f"Backend port {args.backend_port} is free")
        else:
            print_error(f"Backend port {args.backend_port} is still in use")

    if not args.backend_only:
        frontend_free = verify_port_free(args.frontend_port)
        if frontend_free:
            print_success(f"Frontend port {args.frontend_port} is free")
        else:
            print_error(f"Frontend port {args.frontend_port} is still in use")

    # Summary
    print_header("Summary")

    all_success = backend_stopped and frontend_stopped and backend_free and frontend_free

    if all_success:
        print_success("All servers stopped successfully")
        if not args.frontend_only:
            print(f"  • Backend (port {args.backend_port}): {Colors.OKGREEN}Stopped{Colors.ENDC}")
        if not args.backend_only:
            print(f"  • Frontend (port {args.frontend_port}): {Colors.OKGREEN}Stopped{Colors.ENDC}")
    else:
        print_warning("Some servers may still be running")
        if not args.frontend_only:
            status = "Stopped" if backend_free else "Still running"
            color = Colors.OKGREEN if backend_free else Colors.FAIL
            print(f"  • Backend (port {args.backend_port}): {color}{status}{Colors.ENDC}")
        if not args.backend_only:
            status = "Stopped" if frontend_free else "Still running"
            color = Colors.OKGREEN if frontend_free else Colors.FAIL
            print(f"  • Frontend (port {args.frontend_port}): {color}{status}{Colors.ENDC}")

        print()
        print_info("To manually stop remaining processes:")
        if not backend_free:
            print(f"  lsof -ti:{args.backend_port} | xargs kill -9")
        if not frontend_free:
            print(f"  lsof -ti:{args.frontend_port} | xargs kill -9")

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
