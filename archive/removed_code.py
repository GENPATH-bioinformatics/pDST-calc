"""
Archived input-file logic removed from the CLI and utilities.
This file keeps the old implementations for reference.
It is not imported by the app.
"""

# --- From app/cli/main.py ---

EXPECTED_FIELDS = [
    "id",
    "logfile_name",
    "selected_numerals",
    "reselect_numerals",
    "own_cc",
    "cc_values",
    "purch_mol_weights",
    "stock_vol",
    "results_filename",
    "weighed_drug",
    "mgit_tubes",
    "final_results_filename",
]

def parse_input_file(input_file):
    """
    Parse a semicolon-separated CSV input file for automated CLI testing.
    If the first row does not contain the expected field names, treat it as data.
    Args:
        input_file (str): Path to the input CSV file.
    Returns:
        list[dict]: List of rows as dictionaries, one per test case.
    """
    import csv
    with open(input_file, newline='') as csvfile:
        first_line = csvfile.readline()
        csvfile.seek(0)
        has_header = all(field in first_line for field in EXPECTED_FIELDS)
        if has_header:
            reader = csv.DictReader(csvfile, delimiter=';')
            return list(reader)
        else:
            reader = csv.reader(csvfile, delimiter=';')
            rows = list(reader)
            return [dict(zip(EXPECTED_FIELDS, row)) for row in rows if any(cell.strip() for cell in row)]


    # Not function but unused multimode logic
        # Handle different modes
        test_rows = []
        error_log = None
        
        if args.single_test_input:
            print_step("","Single Test Mode")
            # Single test input mode - run one test case
            logger.info(f"Running single test with input file: {args.single_test_input}")
            test_rows = parse_input_file(args.single_test_input)
            if args.test_output:
                error_log = open(args.test_output, 'w')
                logger.info(f"Error log will be written to: {args.test_output}")
            
            if test_rows:
                # Use only the first row for single test
                test_case = test_rows[0]
                logger.info(f"Running single test case")
                run_calculation(df, session_name, test_case, error_log, logger, user_id)
                print_success("Single test completed successfully")
            else:
                logger.error("No test data found in single test input file")
                print_error("No test data found in single test input file")
            
            if error_log:
                error_log.close()
        else:
            # Interactive mode
            print_step("","Interactive Mode")
            run_calculation(df, session_name, None, None, logger, user_id, resume_preparation)
            print_success("Interactive session completed successfully")

# --- From lib/supp_calc.select_drugs (test/auto branches) ---

def select_drugs_file_modes_note():
    return (
        "select_drugs used to support input_file/error_log for automated tests; "
        "that logic has been removed from runtime and archived here."
    )


