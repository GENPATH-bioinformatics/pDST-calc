# Memo: Test Cases for Input Validation

This CSV file contains 50 test cases designed to validate a system processing chemical or experimental data with the specified arguments. Each test case is a single line with semicolon-separated arguments, and the ID enumerates each test uniquely. The arguments are:

1. **logfile_name**: A string representing the logfile name (e.g., log1.txt).
2. **selected_numerals**: A comma- or space-separated list of integers (1 to 21, 1 to 21 numerals).
3. **reselect_numerals**: 'y' or 'n', indicating whether to reselect numerals (if 'n', new numerals should be passed).
4. **own_cc**: 'y' or 'n', indicating if custom cc values are provided (if 'y', provide cc values equal to the count of selected numerals).
5. **cc_values**: Float values (0 to 20) matching the count of selected numerals if own_cc is 'y'.
6. **purch_mol_weights**: Float values (137 to 823) matching the count of selected numerals.
7. **stock_vol**: A float value (0 to 1000) for stock volume.
8. **results_filename**: A string for the results file name.
9. **weighed_drug**: A float value (0 to 100) for the weighed drug amount.
10. **mgit_tubes**: An integer (0 to 100) for the number of MGIT tubes.
11. **final_results_filename**: A string for the final results file name.

The test cases cover:
- **Valid cases**: Tests 1–7, 31, and 39 are within specified ranges, testing various numeral counts (1 to 21) and cc values when applicable.
- **Edge cases**: Tests 5 (max 9 numerals with cc values), 6 (min 1 numeral), 7 (max 20 numerals with cc values), and boundary values (e.g., 0.0, 1000.0 for stock_vol; 0, 100 for mgit_tubes).
- **Outliers and invalid cases**:
  - Invalid numerals: Tests 8 (0), 9 (22), 44 (-1), 45 (23 numerals), 46 (non-numeric 'a'), 30 (duplicate numerals).
  - Invalid cc values: Tests 10 (cc > 20), 11 (cc < 0), 12 (cc > 20), 13 (wrong cc count), 32 (wrong cc count), 33 (wrong cc count), 35 (missing cc values), 36 (extra cc values).
  - Invalid purch_mol_weights: Tests 23 (< 137), 24 (> 823), 37 (wrong count), 38 (extra count), 40 (wrong count), 47 (< 137), 48 (> 823).
  - Invalid reselect_numerals: Test 25 (invalid 'x').
  - Invalid own_cc: Test 26 (invalid 'x').
  - Invalid stock_vol: Tests 14 (< 0), 15 (> 1000).
  - Invalid weighed_drug: Tests 16 (< 0), 17 (> 100).
  - Invalid mgit_tubes: Tests 18 (< 0), 19 (> 100), 50 (non-numeric 'abc').
  - Missing arguments: Tests 20 (missing numerals), 27 (missing logfile_name), 28 (missing results_filename), 29 (missing final_results_filename).
  - Non-numeric stock_vol: Test 49 (non-numeric 'abc').

These cases ensure thorough testing of input validation, boundary conditions, and error handling for the system.