# Testing Guide for pDST Calculator

This document describes the comprehensive testing setup for the pDST Calculator package, which supports running different categories of tests including fast unit-only tests and comprehensive property-based tests.

## Overview

The testing framework includes:
- **Unit tests**: Individual function testing
- **Integration tests**: Complete workflow testing
- **Property-based tests**: Using Hypothesis for edge cases
- **Code quality tools**: Linting, formatting, type checking

## Quick Start

### Prerequisites

```bash
# Use uv directly:
uv sync --group dev --group test --group lint
```

### Running Tests

**Quick Unit Tests (Recommended for Development)**
```bash
# Run only unit tests (fast, excludes hypothesis property-based tests)
uv run pytest test/lib/test_drug_database.py test/lib/test_dst_calc.py test/lib/test_supp_calc.py
```

**All Tests (Comprehensive)**
```bash
# Run all tests including hypothesis property-based tests
uv run pytest
```

**Specific Test Categories**
```bash
# Run only hypothesis property-based tests
uv run pytest test/lib/test_dst_calc_hypothesis.py test/lib/test_supp_calc_hypothesis.py test/lib/test_drug_database_hypothesis.py

# Run specific module tests
uv run pytest test/lib/test_dst_calc.py -v
```

## Available Test Commands

### Core Testing

**Fast Unit Tests (Development)**
```bash
# Quick unit tests only (excludes hypothesis property-based tests)
uv run pytest test/lib/test_drug_database.py test/lib/test_dst_calc.py test/lib/test_supp_calc.py
```

**Comprehensive Testing**
```bash
# All tests including hypothesis property-based tests
uv run pytest
```

### Module-Specific Tests

**Unit Tests**
```bash
uv run pytest test/lib/test_dst_calc.py          # DST calculation unit tests
uv run pytest test/lib/test_drug_database.py     # Drug database unit tests
uv run pytest test/lib/test_supp_calc.py         # Supplementary calculation unit tests
```

**Property-Based Tests (Hypothesis)**
```bash
uv run pytest test/lib/test_dst_calc_hypothesis.py        # DST calc hypothesis tests
uv run pytest test/lib/test_drug_database_hypothesis.py   # Drug DB hypothesis tests
uv run pytest test/lib/test_supp_calc_hypothesis.py       # Supp calc hypothesis tests
```

### Test Categories Using Markers

*Note: Markers work when all dependencies (including hypothesis) are available*
```bash
uv run pytest -m 'not hypothesis'    # Unit tests only
uv run pytest -m hypothesis          # Hypothesis tests only
uv run pytest -m integration         # Integration tests only
uv run pytest -m 'not slow'          # Exclude slow tests
```

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
- **Purpose**: Test individual functions with known values
- **Characteristics**: Fast execution (~1-2 seconds), high coverage
- **Content**: Mathematical correctness, edge cases, error handling
- **When to use**: During development for quick feedback
- **Files**: `test_dst_calc.py`, `test_drug_database.py`, `test_supp_calc.py`

### Property-Based Tests (`*_hypothesis.py`)
- **Purpose**: Use Hypothesis library for automatic test case generation
- **Characteristics**: Slower execution (~10-30 seconds), comprehensive coverage
- **Content**: Mathematical properties, invariants, extreme edge cases
- **When to use**: Before commits, CI/CD, comprehensive testing
- **Files**: `test_*_hypothesis.py`

### Integration Tests
- **Purpose**: Test complete calculation workflows
- **Characteristics**: End-to-end validation, realistic scenarios
- **Content**: Data flow between components, workflow verification
- **When to use**: Before releases, regression testing
- **Markers**: `@pytest.mark.integration`

## Performance Comparison

| Test Type | Duration | Coverage | Use Case |
|-----------|----------|----------|----------|
| Unit Tests Only | ~1-2 seconds | 95%+ | Development iteration |
| All Tests | ~15-30 seconds | 96%+ | Pre-commit, CI/CD |
| Hypothesis Only | ~10-20 seconds | Edge cases | Property validation |

## Configuration

### Pytest Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
addopts = "--maxfail=1"
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
- Coverage reports can be enabled with `--cov=lib --cov-report=term --cov-report=html`
- HTML reports are saved to `htmlcov/` when coverage is enabled
- Terminal reports show coverage summary
- Coverage is optional to allow faster unit test runs during development

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
3. **Hypothesis slow**: Use unit tests only for development: `pytest test/lib/test_*.py`
4. **ModuleNotFoundError for hypothesis**: This is expected when running unit tests with filtering - use file-specific commands instead

### Test Failures

1. **Floating-point precision**: The integration tests use relative tolerances (5e-3) for accumulated floating-point errors
2. **Random test failures**: Property-based tests may reveal edge cases - examine the failing inputs in the test output
3. **Slow tests**: Use unit tests only for faster feedback: `pytest test/lib/test_*.py`
4. **Hypothesis test failures**: These tests use extreme value ranges and may uncover edge cases in mathematical calculations

## Best Practices

### Development Workflow
1. **During active development**: Use unit tests only for fast feedback
   ```bash
   uv run pytest test/lib/test_dst_calc.py
   ```

2. **Before committing**: Run all tests to ensure comprehensive coverage
   ```bash
   uv run pytest
   ```

3. **Debugging specific issues**: Run individual test methods
   ```bash
   uv run pytest test/lib/test_dst_calc.py::TestDstCalc::test_potency_calculation -v
   ```

### Test Organization
- **Unit tests** (`test_*.py`): Keep focused on individual functions
- **Hypothesis tests** (`*_hypothesis.py`): Test mathematical properties and edge cases
- **Use markers**: `@pytest.mark.integration` for workflow tests, `@pytest.mark.slow` for time-consuming tests

### Performance Tips
- Use unit tests during development for sub-second feedback
- Reserve hypothesis tests for pre-commit and CI/CD pipelines
- Run specific test files rather than using marker filters to avoid import issues
- Consider using `@settings(max_examples=10)` in hypothesis tests during development
