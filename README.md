# DST Calculator

This project provides a Drug Susceptibility Testing (DST) calculator with both a command-line interface (CLI) and a Shiny for Python web app.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url> dstcalc
   cd dstcalc
   ```
2. Install dependencies (for development or quick setup):
   ```bash
   uv sync
   ```
   - `uv.lock` is provided for developer convenience and compatibility with tools and platforms that expect it.

## Using the CLI

The CLI supports multiple modes of operation:

### 1. Interactive Mode (Default)

Run the CLI interactively, answering prompts as you go:

```bash
uv run dstcalc
```

This will prompt you for:
- Session name for logging
- Drug selection
- Custom critical values (optional)
- Purchased molecular weights
- Stock solution volumes
- Actual weighed drug amounts
- Number of MGIT tubes

### 2. File-Based Mode

#### Using Custom Drug Data

Load drug data from a custom CSV file instead of the default database:

```bash
uv run dstcalc --drug-data data/my_drugs.csv
```

#### Single Test Input

Run one automated test case from a CSV file:

```bash
uv run dstcalc --single-test-input tests/my_test.csv
(eg. uv run dstcalc --single-test-input tests/test_2.csv)
```

#### Batch Testing

Run multiple test cases from a CSV file:

```bash
uv run dstcalc --test-input tests/batch_tests.csv --test-output results.log

```

#### With Custom Session Name

Bypass the interactive session name prompt:

```bash
uv run dstcalc --session-name "experiment_001"
```

### 3. Combined Modes

You can combine different options:

```bash
# Custom drug data + single test + custom session
uv run dstcalc --drug-data data/my_drugs.csv --single-test-input tests/test.csv --session-name "john_experiment"

# Batch testing with error logging
uv run dstcalc --test-input tests/all_tests.csv --test-output test_results.log --session-name "batch_run"
```

## Input File Formats

### Test Input CSV Format

Test input files should be semicolon-separated with these columns:

```csv
id;logfile_name;selected_numerals;reselect_numerals;own_cc;cc_values;purch_mol_weights;stock_vol;results_filename;weighed_drug;mgit_tubes;final_results_filename
1;test1;1,2;2,3;y;1.0,1.5;300,310;10,10;results1.txt;9.8,10.2;2,2;final1.txt
2;test2;3;4;n;;320;12;results2.txt;12.1;3;final2.txt
```

**Column Descriptions:**
- `id`: Test case identifier
- `logfile_name`: Name for the log file
- `selected_numerals`: Drug selection numbers (e.g., "1,2,3")
- `reselect_numerals`: Alternative drug selection if reselection needed
- `own_cc`: Whether to use custom critical values (y/n)
- `cc_values`: Custom critical concentration values (comma-separated)
- `purch_mol_weights`: Purchased molecular weights (comma-separated)
- `stock_vol`: Stock solution volumes (comma-separated)
- `results_filename`: Filename for intermediate results
- `weighed_drug`: Actual weighed drug amounts (comma-separated)
- `mgit_tubes`: Number of MGIT tubes (comma-separated)
- `final_results_filename`: Filename for final results

### Header vs No Header

The CLI supports both formats:

**With Header:**
```csv
id;logfile_name;selected_numerals;own_cc;cc_values;purch_mol_weights;stock_vol;weighed_drug;mgit_tubes
1;test1;1,2;y;1.0,1.5;300,310;10,10;9.8,10.2;2,2
```

**Without Header (just data):**
```csv
1;test1;1,2;y;1.0,1.5;300,310;10,10;9.8,10.2;2,2
```

## Logging

All operations are logged to:
- **Console output**: Real-time progress and results
- **Log files**: `logs/pdst-calc-{session_name}.log` in the project root

## Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--drug-data` | Path to custom drug data CSV | `--drug-data data/my_drugs.csv` |
| `--single-test-input` | Path to single test input CSV | `--single-test-input tests/test.csv` |
| `--test-input` | Path to batch test input CSV | `--test-input tests/batch.csv` |
| `--test-output` | Path to error log file | `--test-output results.log` |
| `--session-name` | Session name for logging | `--session-name "experiment_001"` |

## Running Tests

If you have test files (e.g., in `tests/`):
```bash
uv run pytest --cov=lib
```

## Troubleshooting
- **ModuleNotFoundError:** Use `uv run` to automatically handle Python path and dependencies.
- **Port already in use:** Use a different port with `--port`.
- **Data not found:** Ensure your `drug_data.csv` is in the correct `data/` directory.
- **Dependency issues:** Reinstall requirements with `pip install -r requirements.txt` or `pip install -e .`
- **Input file errors:** Check that your CSV file uses semicolon separators and has the correct column names or data format.

## Project Structure

- `lib/src/` — Core logic, calculation functions, and data utilities
- `app/cli/` — Command-line interface entry point (`main.py`)
- `app/shiny/` — Shiny for Python web app
- `data/` — Drug data CSV and reference files
- `requirements.txt` — Python dependencies for development and quick setup
- `setup.py` and `pyproject.toml` — Packaging and distribution configuration
- `tests/` — Unit and integration tests
- `docs/` — Documentation, user manual, and development log

## Documentation

- [User Manual](docs/USER_MANUAL.md)
- [Development Log](docs/DEVELOPMENT_LOG.md)

---
For more details, see the documentation in `docs/`.
