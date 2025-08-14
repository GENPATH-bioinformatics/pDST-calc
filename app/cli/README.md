# pDST-calc CLI

Command-line interface for the Drug Susceptibility Testing (DST) calculator.

## Installation

From TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pdst-calc-cli
```

## Usage

After installation, you can run the CLI tool:

```bash
pdst-calc
```

### Command-line Options

- `--drug-data`: Path to input file with drug data (CSV format)
- `--single-test-input`: Path to single test input CSV for one-time automated run
- `--test-output`: Path to test output/error log file
- `--session-name`: Session name for logging

### Examples

Interactive mode:
```bash
pdst-calc --session-name "my_experiment"
```

Automated test mode:
```bash
pdst-calc --single-test-input test_data.csv --test-output results.log --session-name "automated_test"
```

## Dependencies

This CLI tool depends on the `pdst-calc-lib` library, which provides the core DST calculation functionality.

## License

MIT License - see LICENSE file for details.
