# User Manual: DST Calculator

## Introduction
The DST Calculator is a tool for drug susceptibility testing calculations, available as both a command-line interface (CLI) and a Shiny for Python web app. It helps users select drugs, view and customize critical concentrations, and perform calculations for laboratory preparation.

## Installation
See the main [README.md](../README.md) for installation instructions and requirements.

### About requirements.txt, setup.py, and pyproject.toml
- **requirements.txt**: For quick setup and installing dependencies directly with `pip install -r requirements.txt`. Useful for development and platforms that expect this file.
- **setup.py** and **pyproject.toml**: Used for packaging the project and for local installation as a Python package. After running `pip install -e .`, you can use the `dstcalc` command from anywhere.

## Running the CLI Tool
1. Open a terminal and navigate to the project root directory.
2. Run:
   ```bash
   uv run python app/cli/main.py
   # or simply:
   uv run pdst-calc
   ```
3. Follow the prompts to select drugs by number. You can enter numbers separated by commas or spaces (e.g., `1,3,5` or `2 4 6`).
4. If you enter an invalid number, you will see an error message (e.g., `44 is not in drug selection`).
5. After selection, confirm your choices or reselect as needed.
6. Optionally, enter custom critical values for selected drugs when prompted.

## Running the Shiny Web App
1. From the project root, run:
   ```bash
   uv run shiny app/shiny/app.py
   ```
   If port 8000 is in use, specify another port:
   ```bash
   uv run shiny --port 8001 app/shiny/app.py
   ```
2. Open your browser and go to the address shown in the terminal (usually `http://127.0.0.1:8000`).
3. Use the web interface to select drugs and view their properties.

## Customizing Drug Data
- The drug data is stored in `data/drug_data.csv`.
- You can edit this file in a spreadsheet editor to add, remove, or update drugs, molecular weights, diluents, or critical concentrations.
- Changes will be reflected the next time you run the CLI or Shiny app.

## Troubleshooting
- **ModuleNotFoundError:** Use `uv run` to automatically handle Python path and dependencies.
- **Port already in use:** Use the `--port` option to specify a different port.
- **Data not found:** Make sure `drug_data.csv` is in the `data/` directory.
- **Dependency issues:** Reinstall requirements with `pip install -r requirements.txt` or `pip install -e .`.

## Getting Help
- For more details, see the [README.md](../README.md) and other documentation in the `docs/` folder.
- If you encounter issues, check the Troubleshooting section or contact the project maintainer. 