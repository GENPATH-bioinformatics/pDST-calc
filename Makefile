# Makefile for pDST Calculator Testing
# Provides easy access to all test commands without requiring pixi

.PHONY: help test test-quick test-coverage test-dst-calc test-drug-db test-supp-calc \
        test-hypothesis test-dst-calc-hypothesis test-drug-db-hypothesis test-supp-calc-hypothesis \
        test-integration test-watch lint format type-check test-clean install dev-install

# Default target
help:
	@echo "pDST Calculator - Available Test Commands"
	@echo "========================================"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test                    - Run all tests with coverage"
	@echo "  make test-quick             - Quick test run without coverage"
	@echo "  make test-coverage          - Run tests with coverage and generate HTML report"
	@echo "  make test-dst-calc          - Run tests for DST calculation module"
	@echo "  make test-drug-db           - Run tests for drug database module"
	@echo "  make test-supp-calc         - Run tests for supplementary calculation module"
	@echo "  make test-hypothesis        - Run hypothesis property-based tests"
	@echo "  make test-dst-calc-hypothesis    - Run hypothesis tests for DST calc"
	@echo "  make test-drug-db-hypothesis     - Run hypothesis tests for drug DB"
	@echo "  make test-supp-calc-hypothesis   - Run hypothesis tests for supp calc"
	@echo "  make test-integration       - Run integration tests only"
	@echo "  make test-watch            - Continuous testing (watch mode)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install               - Install package dependencies"
	@echo "  make dev-install           - Install package with dev dependencies"
	@echo "  make lint                  - Lint the code"
	@echo "  make format                - Format code with black"
	@echo "  make type-check            - Run type checking with mypy"
	@echo "  make test-clean            - Clean up test artifacts"
	@echo ""
	@echo "Alternative: Use the test runner directly:"
	@echo "  python scripts/test_runner.py [command]"

# Testing Commands
test:
	python -m pytest --cov=lib test/lib/ -v

test-quick:
	python -m unittest discover test/lib -v

test-coverage:
	python -m pytest --cov=lib --cov-report=html --cov-report=term test/lib/ -v

test-dst-calc:
	python -m unittest test.lib.test_dst_calc -v

test-drug-db:
	python -m unittest test.lib.test_drug_database -v

test-supp-calc:
	python -m unittest test.lib.test_supp_calc -v

test-hypothesis:
	python -m pytest test/lib/*_hypothesis.py -v

test-dst-calc-hypothesis:
	python -m pytest test/lib/test_dst_calc_hypothesis.py -v

test-drug-db-hypothesis:
	python -m pytest test/lib/test_drug_database_hypothesis.py -v

test-supp-calc-hypothesis:
	python -m pytest test/lib/test_supp_calc_hypothesis.py -v

test-integration:
	python run_tests.py --integration

test-watch:
	python -m ptw test/lib/ --runner 'pytest --cov=lib test/lib/ -v'

# Development Commands
install:
	uv sync

dev-install:
	uv sync --group dev --group test --group lint

lint:
	python -m flake8 lib/ app/ --max-line-length=100 --ignore=E501,W503

format:
	python -m black lib/ app/ test/ --line-length=100

type-check:
	python -m mypy lib/ --ignore-missing-imports

test-clean:
	rm -rf htmlcov/ .coverage .pytest_cache/ __pycache__/ */test/__pycache__/ */test/*/__pycache__/

# Alternative commands using the test runner
run-test-%:
	python scripts/test_runner.py $(subst run-,,$@)
