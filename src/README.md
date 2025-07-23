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
python -m shiny run --port 37469 --reload --autoreload-port 42857 /home/bea-loubser/Desktop/dstcalc/src/shinyapp/app.py
```

For more details, see the main `README.md` in the project root.
