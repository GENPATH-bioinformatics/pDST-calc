# pDST-calc App: How to Run (CLI and Shiny)

This guide explains, step by step, how to run the command-line (CLI) tool and the Shiny web interface.

## 1) Prerequisites

- Python 3.10+ (recommended)
- uv package manager installed
  - Install uv: https://docs.astral.sh/uv/
  - Or: pipx install uv

## 2) Set up the environment

From the project root directory:

```bash
uv sync
```

This will create/refresh a virtual environment and install dependencies using `pyproject.toml` and `uv.lock`.

## 3) Run the Shiny web app

1. Start the app:
   ```bash
   uv run shiny run app/shiny/app.py --port 8001
   ```
2. Open your browser at:
   - http://localhost:8001

Tips:
- If the port is busy, use a different one (for example `--port 8003`).
- If you see import issues, ensure you ran `uv sync` in the project root.

## 4) Run the CLI tool

There are two ways to run the CLI:

- Using the console script entry point (preferred):
  ```bash
  uv run pdst-calc
  ```

Basic flow (CLI):
1. Select drugs when prompted.
2. Provide per-drug inputs (critical values, purchased molecular weight, stock volumes) as requested.
3. Review calculated outputs and follow on-screen instructions to enter actual weights and MGIT tubes if needed.
4. Results will be printed to the terminal and written to the output files as configured by prompts/arguments.
