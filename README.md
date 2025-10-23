# DST Calculator

A comprehensive **Phenotypic Drug Susceptibility Testing (pDST) Calculator** for tuberculosis research and clinical laboratories. This project provides both command-line and web-based interfaces for calculating drug concentrations, solution preparations, and laboratory protocols.

## Key Features

- **🧪 4-Step Laboratory Workflow:** Drug selection → Parameters → Weight entry → Solution preparation guide
- **👤 User Authentication & Sessions:** Secure user accounts with persistent session management
- **🔄 Intelligent Session Restoration:** Automatically resume work at the correct step based on saved data
- **📊 Comprehensive Calculations:** Stock solutions, working solutions, intermediate dilutions with safety considerations
- **📄 PDF Protocol Generation:** Professional laboratory protocols for Steps 2 and 4
- **⚡ Real-time Validation:** Input validation with helpful warnings and error messages
- **🔧 Flexible Unit Support:** Customizable units for weight, volume, and concentration measurements
- **💻 Dual Interface:** Full-featured web app and command-line interface for different workflows

## Quick Start

1. **Clone and install:**
   ```bash
   git clone <repo-url> dstcalc
   cd dstcalc
   uv sync
   ```

2. **Launch the web app:**
   ```bash
   uv run shiny run app/shiny/app.py --port 8001
   ```

3. **Open your browser:** http://localhost:8001

4. **Get started:**
   - Sign up for an account in the "Account & Sessions" tab
   - Create a new session and start calculating!

## Educational Resources

🧪 **[DST Educational Guide](docs/DST_EDUCATIONAL_GUIDE.md)** - Comprehensive terminology and reference guide for Drug Susceptibility Testing, including:

- **Glossary of Terms:** 27+ essential DST definitions with authoritative sources
- **Clinical Context:** Critical concentrations, breakpoints, MIC interpretations
- **Laboratory Methods:** Culture systems, potency calculations, quality control
- **Reference Standards:** Links to WHO, CLSI, and EUCAST guidelines

Perfect for students, researchers, and laboratory professionals working with tuberculosis DST.

## User Feedback

We value your feedback! Help us improve the pDST Calculator by sharing your experience, reporting issues, or suggesting new features.

**📝 [Submit Feedback](https://forms.office.com/r/sMfCywFy4H)**

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Option 1: Using uv (Recommended)
1. Clone the repository:
   ```bash
   git clone <repo-url> dstcalc
   cd dstcalc
   ```
2. Install dependencies:
   ```bash
   uv sync
   ```

### Option 2: Using pip
1. Clone the repository:
   ```bash
   git clone <repo-url> dstcalc
   cd dstcalc
   ```
2. Create virtual environment and install:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

## Using the CLI

The command-line interface provides a text-based workflow for automated processing and batch operations:

### Interactive Mode

Run the CLI interactively with step-by-step prompts:

```bash
uv run python app/cli/main.py
```

**Features:**
- **User Authentication:** Login to existing accounts or create new ones
- **Session Management:** Create and load previous calculation sessions  
- **Step-by-step Input:** Guided prompts for all calculation parameters
- **Automatic Calculations:** Real-time computation of drug weights and dilutions
- **File Output:** Results saved to structured log files and CSV formats

**Interactive Workflow:**
1. **Authentication:** Sign in or create account
2. **Session Selection:** Start new session or continue existing one
3. **Drug Selection:** Choose from comprehensive drug database
4. **Parameter Input:** Enter critical concentrations, molecular weights, volumes
5. **Weight Entry:** Input actual weighed amounts and tube counts
6. **Results:** View formatted results and save to files

#### With Custom Session Name

Bypass the interactive session name prompt:

```bash
uv run pdst-calc --session-name "experiment_001"
```

## Using the Shiny App

1. **Start the application:**
   ```bash
   uv run shiny run app/shiny/app.py --port 8001
   ```
   
2. **Open your web browser and visit:** `http://localhost:8001`

### Application Workflow

pDST-Calc features a comprehensive 4-step workflow with user authentication and session management:

#### Account & Sessions Tab
- **User Authentication:** 
  - Sign up for a new account or log in to existing credentials
  - User management with secure password handling
- **Session Management:** 
  - View all your calculation sessions in organized cards
  - Create new sessions with custom names
  - Sessions show completion status (In Progress vs Completed)
- **Intelligent Session Restoration:** 
  - Click any session to continue exactly where you left off
  - Automatic step detection based on saved data:
    - **Empty sessions** → Start at Step 1 (Drug Selection)
    - **Drugs selected, no actual weights** → Resume at Step 3 (Weight Entry)
    - **Complete sessions** → View in Step 4 results format
  - All inputs and calculations are automatically preserved

#### Calculator Tab
**Step 1 - Drug Selection:**
- Choose one or more drugs from the comprehensive database
- View drug properties: molecular weight, default diluent, critical concentrations
- Selected drugs displayed in organized summary table

**Step 2 - Parameters:**
- Input calculation parameters for each selected drug:
  - Critical concentrations (customizable)
  - Purchased molecular weights
  - Stock solution volumes  
  - Number of MGIT tubes
- Calculate estimated drug weights and working solution parameters
- **Stock Solution Option:** Toggle to create stock solutions for practical weighing when estimated weights are too small
- Download Step 2 results as formatted PDF protocol

**Step 3 - Weight Entry:**
- Enter actual weighed drug amounts for each compound
- Input actual MGIT tube counts (if different from planned)
- Real-time validation of required inputs

**Step 4 - Solution Guide:**
- Comprehensive laboratory preparation instructions
- **Safety Precautions:** PPE requirements, ventilation, spill procedures
- **Step-by-step Protocols:** 
  - Stock solution preparation (when applicable)
  - Working solution preparation
  - Intermediate dilutions (for very concentrated solutions)
- **Final Results Tables:** Precise volumes and concentrations for laboratory use
- Download complete Step 4 protocol as formatted PDF

#### Advanced Features
- **Unit Preferences (Sidebar):** Customize display units for all measurements
  - Molecular Weight: g/mol, kg/mol, mg/mol
  - Volume: ml, L, μl  
  - Concentration: mg/ml, g/L, μg/ml, ng/ml
  - Weight: mg, g, μg
- **Smart Calculations:** Internal calculations use standard units (mg/ml, ml, mg) with automatic conversions
- **Validation & Warnings:** Real-time feedback for infeasible calculations (insufficient stock, negative diluent volumes, etc.)
- **Session Persistence:** All work automatically saved, supporting interrupted workflows and collaborative use

## Logging

All operations are logged to:
- **Console output**: Real-time progress and results
- **Log files**: `~/.pdst-calc/logs/pdst-calc-{session_name}.log` in user's home directory
- **Log files**: `logs/pdst-calc-{session_name}.log` in the project root
- **Output files**: `results/{filename}.txt` 

## Running Tests

If you have test files (e.g., in `tests/`):
```bash
uv run pytest --cov=lib
```

## Project Structure

### Core Components
- **`lib/`** — Core calculation library and data utilities
  - `dst_calc.py` — Primary DST calculation functions
  - `supp_calc.py` — Supplementary calculation and UI functions
  - `tests/` — Comprehensive unit and property-based tests

- **`app/`** — Application interfaces and APIs
  - `api/` — Backend services and database management
    - `auth.py` — User authentication system
    - `database.py` — SQLite database operations
    - `drug_database.py` — Drug data management
  - `cli/` — Command-line interface (`main.py`)
  - `shiny/` — Web application
    - `app.py` — Main Shiny application with 4-step workflow
    - `session_handler.py` — Session management and restoration logic
    - `generate_pdf.py` — PDF protocol generation
    - `tests/` — Shiny app test suite

### Docs
- **`docs/`** — Comprehensive documentation
  - `USER_MANUAL.md` — Detailed usage instructions
  - `DEVELOPMENT_LOG.md` — Development history and changes
  - `TESTING.md` — Testing procedures and guidelines
  - `CALCULATION_FORMULAE.md` — Mathematical formulations

### Development and Distribution
- **`pyproject.toml`** — Modern Python packaging and dependency management
- **`uv.lock`** — Lockfile for reproducible environments
- **`tests/`** — Integration tests and test data
- **`publication/`** — Academic publication materials

## Documentation

- [User Manual](docs/USER_MANUAL.md) — Complete usage instructions for CLI and Shiny app
- [Calculation Formulae](docs/CALCULATION_FORMULAE.md) — Mathematical formulations and algorithms
- [Development Log](docs/DEVELOPMENT_LOG.md) — Development history and changelog  
- [Testing Guide](docs/TESTING.md) — Testing procedures and guidelines

---
For more details, see the documentation in `docs/`.
