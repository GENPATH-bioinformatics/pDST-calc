## Directory Structure

```
───src/
    ├── __init__.py           # Package initialization and version
    ├── core/                 # Core calculation functionality
    │   └── dst_calc.py
    ├── cli/                  # Command-line interface
    │   └── main.py
    └──  data/                 # Data handling and I/O
    │   └── excel_handler.py
```

## Module Descriptions

### Core Module (`core/dst_calc.py`)
- Handles drug preparation calculations
- Manages default drug concentrations
- Provides dilution calculations
- Validates drug concentrations

### CLI Module (`cli/main.py`)
- Implements command-line interface using Click
- Supports single calculations and batch processing
- Provides user-friendly output formatting
- Handles error reporting

### Data Module (`data/excel_handler.py`)
- Manages Excel file operations
- Handles batch data processing
- Supports template-based output
- Validates input data structure

## Dependencies
- numpy: Numerical computations
- pandas: Data manipulation
- openpyxl: Excel file handling
- click: CLI interface
- pytest: Testing framework
