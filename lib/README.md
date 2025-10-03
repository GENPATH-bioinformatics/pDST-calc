# pDST-calc Library

Core calculation library for the Phenotypic Drug Susceptibility Testing (pDST) Calculator.

## Installation

```bash
pip install pdst-calc-lib
```

## Library Structure

```
───lib/
    ├── __init__.py           # Package initialization and version
    ├── drug_database.py      # Drug database loading functions
    ├── dst_calc.py           # Core calculation functions
    ├── supp_calc.py          # Supplementary calculation and UI functions
    └── tests/                # Test suite
        ├── __init__.py       # Test package initialization
        ├── test_drug_database.py         # Unit tests for drug database
        ├── test_drug_database_hypothesis.py  # Property tests for drug database
        ├── test_dst_calc.py              # Unit tests for DST calculations
        ├── test_dst_calc_hypothesis.py   # Property tests for DST calculations
        ├── test_supp_calc.py             # Unit tests for supplementary functions
        └── test_supp_calc_hypothesis.py  # Property tests for supplementary functions
```

## Development

### Running Tests

The library includes comprehensive unit tests and property-based tests using Hypothesis.

```bash
# Install development dependencies
pip install -e .[test]

# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run only unit tests
pytest tests/ -m "unit"

# Run only hypothesis/property tests
pytest tests/ -m "hypothesis"

# Run tests with verbose output
pytest tests/ -v
```

### Test Structure

The tests are organized in the `tests/` directory:

- `test_drug_database.py` - Unit tests for drug database functionality
- `test_dst_calc.py` - Unit tests for DST calculation functions
- `test_supp_calc.py` - Unit tests for supplementary calculation functions
- `test_*_hypothesis.py` - Property-based tests using Hypothesis library

### Test Types

- **Unit Tests**: Traditional unit tests that verify specific functionality
- **Integration Tests**: Tests that verify module interactions
- **Property Tests**: Hypothesis-driven tests that verify mathematical properties and invariants

## Usage

```python
import drug_database
import dst_calc
import supp_calc

# Load drug data
df = drug_database.load_drug_data()

# Calculate potency
pot = dst_calc.potency(purchased_weight, original_weight)

# Estimate drug weight
est_weight = dst_calc.est_drugweight(crit_conc, vol_stock, potency)
```

For more details, see the main `README.md` in the project root.
