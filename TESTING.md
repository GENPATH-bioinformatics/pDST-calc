# Testing Guide for pDST Calculator

This document describes the comprehensive testing setup for the pDST Calculator package, which is now self-contained and no longer requires `pixi.toml` for testing.

## Overview

The testing framework includes:
- **Unit tests**: Individual function testing
- **Integration tests**: Complete workflow testing  
- **Property-based tests**: Using Hypothesis for edge cases
- **Code quality tools**: Linting, formatting, type checking

## Quick Start

### Prerequisites

```bash
# Install the package with development dependencies
uv sync --group dev --group test --group lint
```

### Running Tests

**Option 1: Using Make (recommended)**
```bash
# Run all tests with coverage
make test

# Quick tests without coverage
make test-quick

# See all available commands
make help
```

**Option 2: Using the test runner script**
```bash
# Run all tests with coverage
python scripts/test_runner.py test

# See all available commands
python scripts/test_runner.py help
```

**Option 3: Direct pytest/unittest commands**
```bash
# Run all tests
python -m pytest --cov=lib test/lib/ -v

# Run specific module tests
python -m unittest test.lib.test_dst_calc -v
```

## Available Test Commands

### Core Testing
- `make test` - Run all tests with coverage
- `make test-quick` - Quick test run without coverage  
- `make test-coverage` - Generate HTML coverage report

### Module-Specific Tests
- `make test-dst-calc` - DST calculation module tests
- `make test-drug-db` - Drug database module tests
- `make test-supp-calc` - Supplementary calculation module tests

### Property-Based Tests (Hypothesis)
- `make test-hypothesis` - All hypothesis tests
- `make test-dst-calc-hypothesis` - DST calc hypothesis tests
- `make test-drug-db-hypothesis` - Drug DB hypothesis tests
- `make test-supp-calc-hypothesis` - Supp calc hypothesis tests

### Integration & Development
- `make test-integration` - Integration tests only
- `make test-watch` - Continuous testing (requires pytest-watch)
- `make lint` - Code linting with flake8
- `make format` - Code formatting with black
- `make type-check` - Type checking with mypy
- `make test-clean` - Clean up test artifacts

## Test Structure

```
test/
├── lib/
│   ├── test_dst_calc.py              # Unit tests for DST calculations
│   ├── test_dst_calc_hypothesis.py   # Property-based tests for DST calc
│   ├── test_drug_database.py         # Unit tests for drug database
│   ├── test_drug_database_hypothesis.py
│   ├── test_supp_calc.py             # Unit tests for supplementary calc
│   └── test_supp_calc_hypothesis.py
└── app/                              # Application-level tests
```

## Test Categories

### Unit Tests (`test_*.py`)
- Test individual functions with known values
- Verify mathematical correctness
- Check edge cases and error handling
- Fast execution, high coverage

### Property-Based Tests (`*_hypothesis.py`)
- Use Hypothesis library for automatic test case generation
- Test mathematical properties and invariants
- Verify behavior across wide input ranges
- Catch edge cases that manual tests might miss

### Integration Tests
- Test complete calculation workflows
- Verify end-to-end functionality
- Check data flow between components
- Validate realistic usage scenarios

## Configuration

### Pytest Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
addopts = "--maxfail=1 --cov=lib --cov-report=term --cov-report=html"
testpaths = ["test"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests for individual functions",
    "integration: Integration tests for workflow", 
    "hypothesis: Property-based tests using Hypothesis",
    "slow: Tests that take longer to run",
]
```

### Coverage Configuration
- Coverage reports are generated for the `lib/` directory
- HTML reports are saved to `htmlcov/`
- Terminal reports show coverage summary

## Dependencies

### Runtime Dependencies
- Core calculation libraries (numpy, pandas)
- Testing framework (pytest, unittest)
- Property-based testing (hypothesis)

### Development Dependencies  
- Code quality (ruff, flake8, black, mypy)
- Test coverage (pytest-cov)
- Continuous testing (pytest-watch)
- Documentation (included in dev group)

## Tips for Writing Tests

### Unit Tests
```python
def test_function_with_known_values(self):
    """Test function with specific expected outputs."""
    result = my_function(input_val)
    self.assertAlmostEqual(result, expected_val, places=7)
```

### Property-Based Tests
```python
@given(value=floats(min_value=0.001, max_value=1000))
def test_property_always_holds(self, value):
    """Test that a mathematical property always holds."""
    result = my_function(value)
    assert result > 0  # Property: output always positive
```

### Integration Tests
```python
def test_complete_workflow(self):
    """Test the entire calculation pipeline."""
    # Setup inputs
    inputs = {...}
    
    # Run workflow
    results = complete_calculation(**inputs)
    
    # Verify properties
    assert all(r > 0 for r in results.values())
    assert abs(sum(results.values()) - expected_total) < tolerance
```

## Continuous Integration

The testing setup is designed to work in CI environments:
- All dependencies are specified in `pyproject.toml`
- Tests can be run with simple commands (`make test`)
- Coverage reports can be generated for CI dashboards
- Exit codes properly indicate test success/failure

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're running from the package root directory
2. **Missing dependencies**: Run `uv sync --group dev --group test`
3. **Hypothesis slow**: Use `@settings(max_examples=10)` for faster testing during development
4. **Coverage issues**: Check that the `lib/` directory structure matches coverage configuration

### Test Failures

1. **Floating-point precision**: The integration tests use tolerances of 1e-6 for accumulated errors
2. **Random test failures**: Property-based tests may reveal edge cases - examine the failing inputs
3. **Slow tests**: Use `make test-quick` for faster feedback during development

## Migration from pixi.toml

The testing commands previously defined in `pixi.toml` have been moved to:
- `pyproject.toml`: Dependencies and pytest configuration
- `Makefile`: Easy command access
- `scripts/test_runner.py`: Programmatic test execution
- `TESTING.md`: Documentation (this file)

This makes the package self-contained and removes the dependency on pixi for testing.
