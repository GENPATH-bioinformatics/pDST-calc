# Development Log: DST Calculator

## Overview
This log tracks the development progress, major milestones, and key decisions for the DST Calculator project.

---
## Week 1

### Features Added
- Project directory setup done.
- Excel formulas and project flow sketched and defined.
- Drugs data from excel loaded into CSV for easy updates in data/.
- Drug database import created in "lib/src/drug_database.py".
- Drug calculation functions created in "lib/src/dst_calc.py".
- CLI tool with interactive drug selection and critical value entry created in "app/cli/main.py".
- Error handling for invalid selections and missing data.
- Shiny for Python app skeleton added created in "app/shiny/app.py".
- USER_MANUAL.md added in docs/.
- tests/ added with unit tests for cli/main.py.
- Added first steps to packaging, just added setup.py, pyproject.toml and "__init__.py" to core/ files.
- Created README.md's.
- Created .gitignore.
- README.md's updated
- Added Hypothesis testing (Property-based testing)
- User input of PurchMolecular_Weight- and Stock_Volume values entry created in "app/cli/main.py".
- Input correction added.
- Tabulate implemented for readability.
- User input of MGIT tubes created in "app/cli/main.py".
- Input correction added.
- Output Summary Tables updated/refined.

### Notes for Future Work
[ ] Check calculation logic in `dst_calc.py` functions with Emilyn.
[x] Ask Abi about enforcing version control either tox / nox (Multi-env test automation), or pyenv (.python-version).
[ ] Expand test coverage.
[ ] Implement feature that if first part is done in prev session, that user can continue to second half by entering certain values.
[ ] Make step 4 & 7 result table printable.
[x] Create log files
[ ] Be explicit about database
[ ] PDST_DEBUG = 1, to show tables
[ ] with input files, implement that if multiple drugs are chosen in not ascending order, that the values down the line are still corresponding
[ ] also allow half input file and rest command line
[ ] Work on user personalised drug database implentation
[ ] Work on selected drugs in input file format
[ ] Think of how output should look for multiple lined files / test output
---

