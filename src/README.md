# src Directory

```
───src/
    ├── __init__.py           # Package initialization and version
    ├── core/                 # Core logic and calculation functions
    │   └── drug_database.py
    │   └── dst_calc.py
    ├── cli/                  # Command-line interface
    │   └── main.py
    ├── shinyapp/             # Shiny for Python web app
        └── app.py    
```
## Running the CLI Tool
From the project root:
```bash
dstcalc
```
## Running the Shiny App
From the project root:
```bash
PYTHONPATH=src shiny run src/shinyapp/app.py
```

For more details, see the main `README.md` in the project root.
