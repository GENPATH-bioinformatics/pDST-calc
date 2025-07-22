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

## Using the CLI with uv

   Run the CLI from the project root using:

   ```bash
   uv run python src/cli/main.py
   ```

## Running Tests

If you have test files (e.g., in `tests/`):
```bash
uv run pytest --cov=src
```

## Troubleshooting
- **ModuleNotFoundError:** Make sure you set `PYTHONPATH=src` when running the Shiny app.
- **Port already in use:** Use a different port with `--port`.
- **Data not found:** Ensure your `drug_data.csv` is in the correct `data/` directory.
- **Dependency issues:** Reinstall requirements with `pip install -r requirements.txt` or `pip install -e .`

## Project Structure

- `src/core/` — Core logic, calculation functions, and data utilities
- `src/cli/` — Command-line interface entry point (`main.py`)
- `src/shinyapp/` — Shiny for Python web app
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
