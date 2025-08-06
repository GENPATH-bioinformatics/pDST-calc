#!/usr/bin/env python3
"""
Comprehensive Test Runner for pDST Calculator

This script provides all the test commands that were previously defined in pixi.toml,
making the package self-contained for testing purposes.

Usage:
    python scripts/test_runner.py [command] [options]
    
Available Commands:
    test                - Run all tests with coverage
    test-quick         - Quick test run without coverage
    test-coverage      - Run tests with coverage and generate HTML report
    test-dst-calc      - Run tests for DST calculation module
    test-drug-db       - Run tests for drug database module
    test-supp-calc     - Run tests for supplementary calculation module
    test-hypothesis    - Run hypothesis property-based tests
    test-dst-calc-hypothesis     - Run hypothesis tests for DST calc
    test-drug-db-hypothesis      - Run hypothesis tests for drug DB
    test-supp-calc-hypothesis    - Run hypothesis tests for supp calc
    test-integration   - Run integration tests only
    test-watch         - Continuous testing (watch mode)
    lint               - Lint the code
    format             - Format code with black
    type-check         - Run type checking with mypy
    test-clean         - Clean up test artifacts
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and handle errors."""
    if description:
        print(f"Running: {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DST Calculator Test Runner")
    parser.add_argument(
        "command", 
        nargs="?",
        default="test",
        help="Test command to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Define test commands (equivalent to pixi.toml tasks)
    commands = {
        "test": {
            "cmd": "python -m pytest --cov=lib test/lib/ -v",
            "desc": "Run all tests with coverage"
        },
        "test-quick": {
            "cmd": "python -m unittest discover test/lib -v",
            "desc": "Quick test run without coverage"
        },
        "test-coverage": {
            "cmd": "python -m pytest --cov=lib --cov-report=html --cov-report=term test/lib/ -v",
            "desc": "Run tests with coverage and generate HTML report"
        },
        "test-dst-calc": {
            "cmd": "python -m unittest test.lib.test_dst_calc -v",
            "desc": "Run tests for DST calculation module"
        },
        "test-drug-db": {
            "cmd": "python -m unittest test.lib.test_drug_database -v",
            "desc": "Run tests for drug database module"
        },
        "test-supp-calc": {
            "cmd": "python -m unittest test.lib.test_supp_calc -v",
            "desc": "Run tests for supplementary calculation module"
        },
        "test-hypothesis": {
            "cmd": "python -m pytest test/lib/*_hypothesis.py -v",
            "desc": "Run hypothesis property-based tests"
        },
        "test-dst-calc-hypothesis": {
            "cmd": "python -m pytest test/lib/test_dst_calc_hypothesis.py -v",
            "desc": "Run hypothesis tests for DST calc"
        },
        "test-drug-db-hypothesis": {
            "cmd": "python -m pytest test/lib/test_drug_database_hypothesis.py -v",
            "desc": "Run hypothesis tests for drug DB"
        },
        "test-supp-calc-hypothesis": {
            "cmd": "python -m pytest test/lib/test_supp_calc_hypothesis.py -v",
            "desc": "Run hypothesis tests for supp calc"
        },
        "test-integration": {
            "cmd": "python run_tests.py --integration",
            "desc": "Run integration tests only"
        },
        "test-watch": {
            "cmd": "python -m ptw test/lib/ --runner 'pytest --cov=lib test/lib/ -v'",
            "desc": "Continuous testing (watch mode) - requires pytest-watch"
        },
        "lint": {
            "cmd": "python -m flake8 lib/ app/ --max-line-length=100 --ignore=E501,W503",
            "desc": "Lint the code"
        },
        "format": {
            "cmd": "python -m black lib/ app/ test/ --line-length=100",
            "desc": "Format code with black"
        },
        "type-check": {
            "cmd": "python -m mypy lib/ --ignore-missing-imports",
            "desc": "Run type checking with mypy"
        },
        "test-clean": {
            "cmd": "rm -rf htmlcov/ .coverage .pytest_cache/ __pycache__/ */test/__pycache__/ */test/*/__pycache__/",
            "desc": "Clean up test artifacts"
        },
    }
    
    # Handle help/list commands
    if args.command in ["help", "--help", "-h", "list"]:
        print("Available test commands:")
        for cmd_name, cmd_info in commands.items():
            print(f"  {cmd_name:<25} - {cmd_info['desc']}")
        return 0
    
    # Execute the requested command
    if args.command in commands:
        cmd_info = commands[args.command]
        cmd = cmd_info["cmd"]
        desc = cmd_info["desc"]
        
        # Add verbose flag if requested
        if args.verbose and "--verbose" not in cmd and "-v" not in cmd:
            cmd += " -v"
        
        success = run_command(cmd, desc)
        return 0 if success else 1
    else:
        print(f"Unknown command: {args.command}")
        print("Use 'python scripts/test_runner.py help' to see available commands")
        return 1


if __name__ == "__main__":
    sys.exit(main())
