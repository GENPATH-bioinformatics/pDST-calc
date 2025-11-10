# DST Calculator

A comprehensive **Phenotypic Drug Susceptibility Testing (pDST) Calculator** for tuberculosis research and clinical laboratories. This project provides both command-line and web-based interfaces for calculating drug concentrations, solution preparations, and laboratory protocols.

## 🌐 Live Demo & Educational Resources

**[Visit the Educational Guide Website](https://genpath-bioinformatics.github.io/pDST-calc/)** - Interactive web portal with comprehensive DST terminology and resources

## Key Features

- **4-Step Laboratory Workflow:** Drug selection → Parameters → Weight entry → Solution preparation guide
- **User Authentication & Sessions:** Secure user accounts with persistent session management
- **Intelligent Session Restoration:** Automatically resume work at the correct step based on saved data
- **Comprehensive Calculations:** Stock solutions, working solutions, intermediate dilutions with safety considerations
- **PDF Protocol Generation:** Professional laboratory protocols for Steps 2 and 4
- **Real-time Validation:** Input validation with helpful warnings and error messages
- **Flexible Unit Support:** Customizable units for weight, volume, and concentration measurements
- **Dual Interface:** Full-featured web app and command-line interface for different workflows

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

## 📸 Visual Guide - Application Screenshots

The pDST Calculator provides an intuitive web interface for comprehensive drug susceptibility testing calculations. Below are screenshots showing the complete workflow:

### Getting Started - Account Management & Sessions Dashboard

When you first access the application, you'll see the login interface where you can create a new account or sign in to an existing one.

After logging in, the Account & Sessions tab provides a comprehensive overview of your calculation sessions. Here you can create new sessions and manage existing ones:

Each session is displayed as a card showing the session name, creation date, and completion status. This makes it easy to organize and track your DST calculations across different projects or experiments.

![Login Interface](app/shiny/images/Screenshot%20from%202025-11-04%2011-25-07.png)

![Session Interface](app/shiny/images/Screenshot%20from%202025-11-04%2018-15-59.png)

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

The Calculator tab begins with drug selection, where you can choose from a comprehensive database of tuberculosis drugs. The interface displays each drug's properties including molecular weight, default diluent, and critical concentrations:

![Step 1 - Drug Selection](app/shiny/images/Screenshot%20from%202025-11-04%2018-16-21.png)

- Choose one or more drugs from the comprehensive database
- View drug properties: molecular weight, default diluent, critical concentrations
- Selected drugs displayed in organized summary table


**Step 2 - Parameters:**

After selecting your drugs, they appear in a clear summary table showing all relevant information.

In Step 2, you'll input the specific calculation parameters for each selected drug. This includes critical concentrations, molecular weights, stock solution volumes, and MGIT tube requirements:

![Selected Drugs Summary](app/shiny/images/Screenshot%20from%202025-11-04%2018-16-55.png)


- Input calculation parameters for each selected drug:
  - Critical concentrations (customizable)
  - Purchased molecular weights
  - Stock solution volumes  
  - Number of MGIT tubes
- Calculate estimated drug weights and working solution parameters

Downstream calculations determine the amount and concentrations of working solution needed for the dilution:

![Working Solution Calculations](app/shiny/images/Screenshot%20from%202025-11-04%2018-17-14.png)

The application provides intelligent stock solution options when estimated weights are too small for practical weighing:

![Practical Weighing](app/shiny/images/Screenshot%20from%202025-11-04%2018-17-30.png)

- **Stock Solution Option:** Toggle to create stock solutions for practical weighing when estimated weights are too small.

![Step 2 - Stock Solution Options](app/shiny/images/Screenshot%20from%202025-11-04%2018-17-50.png)
![Step 2- Stock Concentration Factor](app/shiny/images/Screenshot%20from%202025-11-04%2018-18-15.png)
![Step 2 - Validation](app/shiny/images/Screenshot%20from%202025-11-04%2018-18-26.png)

- Download Step 2 results as formatted PDF protocol

**Step 3 - Weight Entry:**

Step 3 focuses on entering the actual laboratory measurements. This is where you input the real weighed amounts and finalize tube counts:

![Step 3 - Weight Entry](app/shiny/images/Screenshot%20from%202025-11-04%2018-18-53.png)

- Enter actual weighed drug amounts for each compound
- Input actual MGIT tube counts (if different from planned)
- Real-time validation of required inputs

**Step 4 - Solution Guide:**

The final step provides comprehensive laboratory preparation instructions with detailed protocols and safety information:

![Step 4 - Solution Preparation Overview](app/shiny/images/Screenshot%20from%202025-11-04%2018-19-09.png)

- Comprehensive laboratory preparation instructions
- **Safety Precautions:** PPE requirements, ventilation, spill procedures

The solution guide includes detailed step-by-step protocols for each preparation stage:

![Step 4 - Detailed Protocols](app/shiny/images/Screenshot%20from%202025-11-04%2018-19-20.png)

![Step 4 - Detailed Protocols2](app/shiny/images/Screenshot%20from%202025-11-04%2018-19-30.png)

- **Step-by-step Protocols:** 
  - Stock solution preparation (when applicable)
  - Working solution preparation
  - Intermediate dilutions (for very concentrated solutions)

Final results are presented in professional tables with precise volumes and concentrations:

![Step 4 - Final Results Tables](app/shiny/images/Screenshot%20from%202025-11-04%2018-19-43.png)

![Step 4 - Detailed Results](app/shiny/images/Screenshot%20from%202025-11-04%2018-19-56.png)

![Step 4 - Detailed Results1](app/shiny/images/Screenshot%20from%202025-11-04%2018-20-06.png)

![Step 4 - Detailed Results2](app/shiny/images/Screenshot%20from%202025-11-04%2018-20-15.png)


- **Final Results Tables:** Precise volumes and concentrations for laboratory use
- Download complete Step 4 protocol as formatted PDF (Examples included in docs/)

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

### 📚 Core Documentation
- **[Calculation Formulae](docs/CALCULATION_FORMULAE.md)** — Comprehensive mathematical formulations and algorithms used in DST calculations
- **[Testing Guide](docs/TESTING.md)** — Testing procedures, guidelines, and validation methods

### 📖 Component Documentation
- **[Library README](lib/README.md)** — Core calculation library documentation and API reference
- **[Application README](app/README.md)** — Application-level documentation and architecture overview
- **[CLI README](app/cli/README.md)** — Command-line interface usage and examples
- **[Shiny Tests README](app/shiny/tests/README.md)** — Web application testing documentation

### 📄 Example Output Files
- **[Example Step 2 Results PDF](docs/Example_Step2_Results.pdf)** — Sample PDF output from Step 2 parameter calculations
- **[Example Step 4 Results PDF](docs/Example_Step4_Results.pdf)** — Sample PDF output from Step 4 solution preparation guide

### 🔬 Educational Resources
- **[Educational Website](https://genpath-bioinformatics.github.io/pDST-calc/)** — Interactive web portal with DST resources and terminology

### 💬 Support & Feedback
- **[User Feedback Form](https://forms.office.com/r/sMfCywFy4H)** — Submit feedback, report issues, or suggest new features

---
For more details, see the documentation in `docs/`.
