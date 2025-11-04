# Testing Guide for pDST Calculator

This document describes the comprehensive testing setup for the pDST Calculator package, which supports running different categories of tests including fast unit-only tests and comprehensive property-based tests.

## Overview

The testing framework includes:
- **Unit tests**: Individual function testing
- **Integration tests**: Complete workflow testing  
- **Property-based tests**: Using Hypothesis for edge cases
- **Application tests**: CLI and Shiny app testing
- **Code quality tools**: Linting, formatting, type checking

## Quick Start

### Prerequisites

```bash
# Install all dependencies including test dependencies
uv sync
```

### Running Tests

**Quick Unit Tests (Recommended for Development)**
```bash
# Run only lib unit tests (fast, excludes hypothesis property-based tests)
uv run pytest lib/tests/test_drug_database.py lib/tests/test_dst_calc.py lib/tests/test_supp_calc.py
```

**All Tests (Comprehensive)**
```bash
# Run all tests including hypothesis property-based tests and app tests
uv run pytest
```

**Specific Test Categories**
```bash
# Run only hypothesis property-based tests
uv run pytest lib/tests/test_dst_calc_hypothesis.py lib/tests/test_supp_calc_hypothesis.py lib/tests/test_drug_database_hypothesis.py

# Run specific module tests
uv run pytest lib/tests/test_dst_calc.py -v

# Run application tests
uv run pytest app/cli/tests/ app/shiny/tests/
```

## Available Test Commands

### Core Testing

**Fast Unit Tests (Development)**
```bash
# Quick unit tests only (excludes hypothesis property-based tests)
uv run pytest lib/tests/test_drug_database.py lib/tests/test_dst_calc.py lib/tests/test_supp_calc.py
```

**Comprehensive Testing**
```bash
# All tests including hypothesis property-based tests and application tests
uv run pytest
```

### Module-Specific Tests

**Library Unit Tests**
```bash
uv run pytest lib/tests/test_dst_calc.py          # DST calculation unit tests
uv run pytest lib/tests/test_drug_database.py     # Drug database unit tests
uv run pytest lib/tests/test_supp_calc.py         # Supplementary calculation unit tests
```

**Property-Based Tests (Hypothesis)**
```bash
uv run pytest lib/tests/test_dst_calc_hypothesis.py        # DST calc hypothesis tests
uv run pytest lib/tests/test_drug_database_hypothesis.py   # Drug DB hypothesis tests
uv run pytest lib/tests/test_supp_calc_hypothesis.py       # Supp calc hypothesis tests
```

**Application Tests**
```bash
# CLI tests
uv run pytest app/cli/tests/test_argument_parsing.py      # CLI argument parsing
uv run pytest app/cli/tests/test_cli_main.py              # CLI main functionality
uv run pytest app/cli/tests/test_error_handling.py        # CLI error handling
uv run pytest app/cli/tests/test_input_validation.py      # CLI input validation
uv run pytest app/cli/tests/test_integration.py           # CLI integration tests
uv run pytest app/cli/tests/test_logging.py               # CLI logging tests

# Shiny app tests
uv run pytest app/shiny/tests/test_shiny_app.py           # Shiny app functionality
uv run pytest app/shiny/tests/test_runner.py              # Shiny test runner
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
├── __init__.py
├── app/                              # Legacy test directory
├── db/                               # Database tests
lib/tests/
├── __init__.py
├── test_dst_calc.py                  # Unit tests for DST calculations
├── test_dst_calc_hypothesis.py       # Property-based tests for DST calc
├── test_drug_database.py             # Unit tests for drug database
├── test_drug_database_hypothesis.py  # Property-based tests for drug DB
├── test_supp_calc.py                 # Unit tests for supplementary calc
└── test_supp_calc_hypothesis.py      # Property-based tests for supp calc
app/cli/tests/
├── __init__.py
├── test_argument_parsing.py          # CLI argument parsing tests
├── test_cli_main.py                  # CLI main functionality tests
├── test_error_handling.py            # CLI error handling tests
├── test_input_validation.py          # CLI input validation tests
├── test_integration.py               # CLI integration tests
├── test_logging.py                   # CLI logging tests
└── data/                             # Test data files
app/shiny/tests/
├── __init__.py
├── test_shiny_app.py                 # Shiny app tests
├── test_runner.py                    # Shiny test runner
└── README.md                         # Shiny testing documentation
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

### CLI Tests
- **Purpose**: Test command-line interface functionality
- **Characteristics**: Input validation, argument parsing, workflow testing
- **Content**: CLI argument handling, error scenarios, integration workflows
- **Location**: `app/cli/tests/`

### Shiny App Tests
- **Purpose**: Test web application functionality
- **Characteristics**: UI component testing, session management, reactive behavior
- **Content**: App initialization, user interactions, session handling
- **Location**: `app/shiny/tests/`

## Performance Comparison

| Test Type | Duration | Coverage | Use Case |
|-----------|----------|----------|----------|
| Unit Tests Only | ~1-2 seconds | 95%+ | Development iteration |
| All Tests | ~30-60 seconds | 96%+ | Pre-commit, CI/CD |
| Hypothesis Only | ~10-20 seconds | Edge cases | Property validation |
| CLI Tests | ~5-10 seconds | CLI coverage | CLI development |
| Shiny Tests | ~10-20 seconds | App coverage | UI development |

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

### Dependencies

The project uses uv's dependency groups for organized testing dependencies:

```toml
[dependency-groups]
test = [
    "pytest>=8",
    "pytest-cov>=6.0.0",
    "pytest-watch>=4.2.0",
    "hypothesis>=6.135.32",
]
dev = [
    "nbwipers>=0.6.1",
    "pytest>=8",
    "pytest-cov>=6.0.0",
    "pytest-watch>=4.2.0",
    "pre-commit>=4.1.0",
    "typos>=1.29.4",
    "hypothesis>=6.135.32",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    # ... additional dev tools
]
```

### Coverage Configuration
- Coverage reports can be enabled with `--cov=lib --cov=app --cov-report=term --cov-report=html`
- HTML reports are saved to `htmlcov/` when coverage is enabled
- Terminal reports show coverage summary
- Coverage is optional to allow faster unit test runs during development

## Testing Workflows

### Development Workflow
1. **During active development**: Use unit tests only for fast feedback
   ```bash
   uv run pytest lib/tests/test_dst_calc.py
   ```

2. **Testing CLI changes**: Run CLI-specific tests
   ```bash
   uv run pytest app/cli/tests/
   ```

3. **Testing Shiny app changes**: Run Shiny-specific tests
   ```bash
   uv run pytest app/shiny/tests/
   ```

4. **Before committing**: Run comprehensive tests
   ```bash
   uv run pytest
   ```

### Continuous Integration
The testing setup is designed for CI environments:
- All dependencies specified in `pyproject.toml`
- Organized dependency groups for targeted testing
- Exit codes properly indicate test success/failure
- Coverage reports can be generated for CI dashboards

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

### CLI Tests
```python
def test_cli_argument_parsing():
    """Test CLI argument parsing."""
    args = parse_args(['--drug', 'rifampicin', '--concentration', '1.0'])
    assert args.drug == 'rifampicin'
    assert args.concentration == 1.0
```

### Shiny App Tests
```python
def test_app_initialization():
    """Test Shiny app initializes correctly."""
    from app.shiny.app import app
    # Test app components and initial state
    assert app is not None
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're running from the package root directory
2. **Missing dependencies**: Run `uv sync` to install all dependency groups
3. **Hypothesis slow**: Use unit tests only for development: `pytest lib/tests/test_*.py`
4. **ModuleNotFoundError**: Check that you're using the correct test paths

### Test Failures

1. **Floating-point precision**: Integration tests use relative tolerances (5e-3) for accumulated errors
2. **Random test failures**: Property-based tests may reveal edge cases - examine failing inputs
3. **Slow tests**: Use targeted test commands for faster feedback during development
4. **CLI test failures**: Check that CLI dependencies and data files are available
5. **Shiny test failures**: Ensure Shiny dependencies are installed and app components are importable

## Best Practices

### Test Organization
- **Unit tests** (`test_*.py`): Keep focused on individual functions
- **Hypothesis tests** (`*_hypothesis.py`): Test mathematical properties and edge cases  
- **CLI tests**: Focus on argument parsing, validation, and workflow integration
- **Shiny tests**: Test UI components, session management, and user interactions
- **Use markers**: `@pytest.mark.integration`, `@pytest.mark.slow`, etc.

### Performance Tips
- Use unit tests during development for sub-second feedback
- Reserve hypothesis tests for pre-commit and CI/CD pipelines
- Run specific test directories rather than using marker filters to avoid import issues
- Consider using `@settings(max_examples=10)` in hypothesis tests during development
- Use targeted test commands: `pytest lib/tests/` vs `pytest app/cli/tests/` vs `pytest app/shiny/tests/`

### Code Coverage
- Aim for >95% coverage on core calculation functions
- CLI tests should cover argument parsing and error handling
- Shiny tests should cover critical user workflows
- Use coverage reports to identify untested code paths:
  ```bash
  uv run pytest --cov=lib --cov=app --cov-report=html
  ```
