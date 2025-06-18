#!/usr/bin/env python3
"""
Test runner script for bella-api-doc-gen project.
Provides convenient commands for running different types of tests.
"""

import subprocess
import sys
import argparse


def run_command(command):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run tests for bella-api-doc-gen")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "api", "service", "database", "unit", "integration", "coverage"],
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Skip coverage reporting"
    )

    args = parser.parse_args()

    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")

    if args.test_type == "all":
        if not args.no_cov:
            base_cmd.extend(["--cov=app", "--cov-report=term-missing"])
    elif args.test_type == "coverage":
        base_cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])
    elif args.test_type in ["api", "service", "database", "unit", "integration"]:
        base_cmd.extend(["-m", args.test_type])

    success = run_command(base_cmd)
    
    if args.test_type == "coverage":
        print("\nHTML coverage report generated in htmlcov/")
        print("Open htmlcov/index.html to view detailed coverage report")

    if not success:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()