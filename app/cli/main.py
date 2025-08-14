import argparse
import pandas as pd
# Import from published pdst-calc-lib package
try:
    # The published package exposes the modules directly
    import drug_database
    import dst_calc
    import supp_calc
    from drug_database import load_drug_data
    from dst_calc import *
    from supp_calc import (
        print_and_log_tabulate, select_drugs, custom_critical_values, 
        purchased_weights, stock_volume, cal_potency, act_drugweight,
        cal_stockdil, mgit_tubes, cal_mgit_ws
    )
except ImportError:
    # Fallback to relative imports for development
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
    from drug_database import load_drug_data
    from dst_calc import *
    from supp_calc import (
        print_and_log_tabulate, select_drugs, custom_critical_values, 
        purchased_weights, stock_volume, cal_potency, act_drugweight,
        cal_stockdil, mgit_tubes, cal_mgit_ws
    )

from tabulate import tabulate
from styling import (print_header, print_success, print_error, print_warning, print_step, print_completion, print_help_text, print_input_prompt)
import logging
import os
import csv
import re
import signal

num_drugs = 0

def clean_filename(filename):
    if not filename:
        return "untitled"
    
    filename = str(filename)
    invalid_chars = r'[<>:"|?*\\/\[\]{}()&%$#@!~`^]'
    cleaned = re.sub(invalid_chars, '_', filename)
    
    # Replace multiple underscores with single underscore
    cleaned = re.sub('_+', '_', cleaned)
    
    # Remove leading/trailing underscores and whitespace
    cleaned = cleaned.strip('_ ')
    
    return cleaned

# Expected field names for test input files
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
    "final_results_filename"
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
    with open(input_file, newline='') as csvfile:
        # Peek at the first row
        first_line = csvfile.readline()
        csvfile.seek(0)
        
        # Check if the first row contains all expected fields
        has_header = all(field in first_line for field in EXPECTED_FIELDS)
        
        if has_header:
            reader = csv.DictReader(csvfile, delimiter=';')
            return list(reader)
        else:
            # No header: treat as data, use expected_fields as keys
            reader = csv.reader(csvfile, delimiter=';')
            rows = list(reader)
            return [dict(zip(EXPECTED_FIELDS, row)) for row in rows if any(cell.strip() for cell in row)]

def setup_logger(session_name="default"):
    # Create logs directory in user's home directory
    home_dir = os.path.expanduser("~")
    log_dir = os.path.join(home_dir, ".pdst-calc", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"pdst-calc-{session_name}.log")

    logger = logging.getLogger("pdst-calc")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def signal_handler(signum, frame):
    print("\n\npDST-calc stopped, Goodbye!")
    exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    # Print cool header
    print_header()
    
    # Show help text for first-time users
    print_help_text()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="DST Calculator CLI - Drug Susceptibility Testing Calculator")
    parser.add_argument('--drug-data', type=str, help='Path to input file with drug data (CSV format)')
    parser.add_argument('--single-test-input', type=str, help='Path to single test input CSV for one-time automated run')
    parser.add_argument('--test-output', type=str, help='Path to test output/error log file')
    parser.add_argument('--session-name', type=str, help='Session name for logging (default: interactive prompt)')
    args = parser.parse_args()

    try:
        # Get session name
        if args.session_name:
            session_name = clean_filename(args.session_name)
            print_success(f"Using session name: {session_name}")
        else:
            print_input_prompt("Enter a name for this session", example="Name_Experiment_Date")
            session_name = input("Session name: ").strip()
            if not session_name:
                session_name = "default"
            else:
                session_name = clean_filename(session_name)
        
        logger = setup_logger(session_name)
        logger.info(f"\nApplication started for session: {session_name}\n")

        # Load drug data
        print_step("0","Loading Drug Data")
        if args.drug_data:
            logger.info(f"Loading drug data from file: {args.drug_data}")
            df = pd.read_csv(args.drug_data)
            print_success(f"Drug data loaded from: {args.drug_data}")
        else:
            logger.info("Loading drug data from database")
            df = load_drug_data()
            print_success("Drug data loaded from database")

        # Handle different modes
        test_rows = []
        error_log = None
        
        if args.single_test_input:
            print_step("0","Single Test Mode")
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
                run_calculation(df, test_case, error_log, logger)
                print_success("Single test completed successfully")
            else:
                logger.error("No test data found in single test input file")
                print_error("No test data found in single test input file")
            
            if error_log:
                error_log.close()
        else:
            # Interactive mode
            print_step("0","Interactive Mode")
            run_calculation(df, None, None, logger)
            print_success("Interactive session completed successfully")
            
    except KeyboardInterrupt:
        print("\n\npDST-calc stopped, Goodbye!")
        exit(0)
    except EOFError:
        print("\n\npDST-calc stopped, Goodbye!")
        exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("pDST-calc terminated due to an error.")
        exit(1)

def run_calculation(df, test_case=None, error_log=None, logger=None):
    """
    Run the main calculation workflow.
    Args:
        df: DataFrame with drug data
        test_case: Dictionary with test inputs (None for interactive mode)
        error_log: File handle for error logging (None for interactive mode)
        logger: Logger instance
    """
    # 1) User selects desired drugs
    print_step("Step 1","Drug Selection")
    if test_case:
        drugs_input = test_case.get('selected_numerals')
        selected_df = select_drugs(df, input_file=drugs_input, error_log=error_log)
        if selected_df is None:
            logger.error("Failed to select drugs from test input")
            print("Failed to select drugs from test input")
            return
    else:
        selected_df = select_drugs(df)

    global num_drugs
    num_drugs = len(selected_df)
    
    # Rename original column for clarity and add unit
    if 'Critical_Concentration' in selected_df.columns:
        selected_df.rename(columns={"Critical_Concentration": "Crit_Conc(mg/ml)"}, inplace=True)

    # 1.3) Ask if user wants to enter their own critical values
    print_step("Step 2","Critical Values")
    if test_case:
        custom_critical_response = test_case.get('own_cc', 'n')
    else:
        response = input("\nWould you like to enter your own critical values for any of the selected drugs? (y/n): ").strip().lower()
        custom_critical_response = response
    
    if custom_critical_response == 'y':
        if test_case:
            print(f"\n[AUTO] Your Critical Concentration selection: {test_case.get('cc_values', '')}")
            # Handle custom critical values from test case
            custom_values = test_case.get('cc_values', '')
            if (custom_values != num_drugs):
                print(f"Number of custom critical values does not match number of selected drugs: {custom_values} != {num_drugs}")
                return
            if custom_values:
                values = [float(x.strip()) for x in custom_values.split(',') if x.strip()]
                for idx, value in enumerate(values):
                    if idx < len(selected_df):
                        selected_df.iloc[idx, selected_df.columns.get_loc('Crit_Conc(mg/ml)')] = value
        else:
            custom_critical_values(selected_df)
            print("\nUpdated selected drugs with custom critical values:")
            print_and_log_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

    # Rename original column for clarity and add unit
    if 'OrgMolecular_Weight' in selected_df.columns:
        selected_df.rename(columns={"OrgMolecular_Weight": "OrgMol_W(g/mol)"}, inplace=True)

    # 2) Prompt user to enter purchased molecular weight for each drug
    print_step("Step 3","Purchased Molecular Weights")
    if test_case:
        print(f"\n[AUTO] Your Purchased Molecular Weight selection: {test_case.get('purch_mol_weights', '')}")
        purchased_weights_input = test_case.get('purch_mol_weights', '')
        if purchased_weights_input:
            weights = [float(x.strip()) for x in purchased_weights_input.split(',') if x.strip()]
            selected_df["PurMol_W(g/mol)"] = weights
            if (len(weights) != num_drugs):
                print(f"Number of purchased molecular weights does not match number of selected drugs: {len(weights)} != {num_drugs}")
                return
    else:
        print("\nNow, please enter the purchased molecular weight for each selected drug.")
        purchased_weights(selected_df)
    # Purchased molecular weights entered (success messages handled in supp_calc.py)

    # Reorder columns so PurMol_W(g/mol) is next to OrgMol_W(g/mol)
    cols = list(selected_df.columns)
    if 'OrgMol_W(g/mol)' in cols and 'PurMol_W(g/mol)' in cols:
        # Remove both columns
        cols.remove('OrgMol_W(g/mol)')
        cols.remove('PurMol_W(g/mol)')
        # Insert after 'Drug'
        new_order = ['Drug', 'OrgMol_W(g/mol)', 'PurMol_W(g/mol)'] + [c for c in cols if c != 'Drug']
        selected_df = selected_df[new_order]

    # 3) Prompt user to enter desired stock solution volume
    print_step("Step 4","Stock Solution Volume")
    if test_case:   
        print(f"[AUTO] Your Stock Solution Volume selection: {test_case.get('stock_vol', '')}")
        stock_volumes_input = test_case.get('stock_vol', '')
        if stock_volumes_input:
            volumes = [float(x.strip()) for x in stock_volumes_input.split(',') if x.strip()]
            if (len(volumes) != num_drugs):
                print(f"Number of stock solution volumes does not match number of selected drugs: {len(volumes)} != {num_drugs}")
                return
            selected_df["St_Vol(ml)"] = volumes
    else:
        print("\nFinally, enter desired stock solution volume (ml).")
        stock_volume(selected_df)


    # 4) Calculate Potency and Estimated Drug Weight for each drug
    print_step("Step 5","Calculate Potency and Estimated Drug Weight")
    cal_potency(selected_df)

    # 5) Instruct user to weigh out the estimated drug weights
    print_step("Step 6","Drug Weight Instructions")
    if not test_case:
        # Prepare output file
        output_filename = input("\nEnter filename for drug weight output (e.g., drug_weights): ").strip()
        if not output_filename:
            output_filename = "drug_weights"
        else:
            output_filename = clean_filename(output_filename)

        if not output_filename.endswith('.txt'):
            output_filename += '.txt'

        # Create results directory in project root
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
        results_dir = os.path.abspath(results_dir)
        os.makedirs(results_dir, exist_ok=True)

        output_path = os.path.join(results_dir, output_filename)
        with open(output_path, 'w') as output_file:
            output_file.write("----------------------------\n")
            output_file.write("INSTRUCTION:\n")
            output_file.write("----------------------------\n\n")
            output_file.write("Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:\n")
            print("\nINSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:")
            for idx, row in selected_df.iterrows():
                print(f"  - {row['Drug']}: {round(row['Est_DrugW(mg)'],8)} mg")
                output_file.write(f"  - {row['Drug']}: {round(row['Est_DrugW(mg)'],8)} mg")
            output_file.write("\n\n----------------------------\n")
            output_file.write("END\n")
            output_file.write("----------------------------\n")
            print(f"\nYour drug weight output filename: {output_filename}")

    print_success("Drug weight instructions generated")

    # Get actual drug weights
    print_step("Step 7","Actual Drug Weights")
    if test_case:
        print(f"[AUTO] Your Weighed Drug selection: {test_case.get('weighed_drug', '')}")
        actual_weights_input = test_case.get('weighed_drug', '')
        if actual_weights_input:
            weights = [float(x.strip()) for x in actual_weights_input.split(',') if x.strip()]
            if (len(weights) != num_drugs):
                print(f"Number of actual weighed drug weights does not match number of selected drugs: {len(weights)} != {num_drugs}")
                return
            selected_df["Act_DrugW(mg)"] = weights
    else:
        act_drugweight(selected_df)


    # Calculate new volume of dilutent and new concentration of stock dilution for each drug
    cal_stockdil(selected_df)

    # 6) Prompt user to enter the number of MGIT Tubes to be used
    print_step("Step 8","MGIT Tubes")
    if test_case:
        print(f"[AUTO] Your MGIT Tubes selection: {test_case.get('mgit_tubes', '')}")
        mgit_tubes_input = test_case.get('mgit_tubes', '')
        if mgit_tubes_input:
            tubes = [float(x.strip()) for x in mgit_tubes_input.split(',') if x.strip()]
            if (len(tubes) != num_drugs):
                print(f"Number of MGIT tubes does not match number of selected drugs: {len(tubes)} != {num_drugs}")
                return
            selected_df["Total Mgit tubes"] = tubes
    else:
        print("\nNow that we have a completed STOCK SOLUTION, enter the number of MGIT tubes you would like to fill.")
        mgit_tubes(selected_df)

    # Calculate MGIT conc, volume of working solution needed, volume of working solution to aliquot, volume of diluent and volume of stock solution left
    cal_mgit_ws(selected_df)

    # 7) Output final values of Volume of Working Solution to Aliquot and Volume of Diluent to be added
    print_step("Step 9","Final Results")
    print("\n----------------------------\nRESULT\n----------------------------\n\n Final Values:")
    logger.info("\nFinal Values:\n")
    
    # Prepare output file
    if test_case:
        output_filename = test_case.get('final_results_filename', 'final_results')
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'

        # Create results directory in project root
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
        results_dir = os.path.abspath(results_dir)
        os.makedirs(results_dir, exist_ok=True)
    else:
        output_filename = input("Enter filename for final results (e.g., final_results): ").strip()
        if not output_filename:
            output_filename = "final_results"
        else:
            output_filename = clean_filename(output_filename)
        
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
    
        
    # Write to output file
    output_path = os.path.join(results_dir, output_filename)
    with open(output_path, 'w') as output_file:
        output_file.write("----------------------------\n")
        output_file.write("RESULT\n")
        output_file.write("----------------------------\n")
        output_file.write("\nFinal Values:\n")
        
        for idx, row in selected_df.iterrows():
            result_line = f"  - {row['Drug']}:\n\tVolume of Stock solution to be added for working solution is {round(row['Vol_WSol_ali(ml)'],8)} ml,\n\tand volume of diluent to be added is {round(row['Vol_Dil_Add(ml)'],8)} ml,\n\tand volume of remaining stock solution is {round(row['Vol_St_Left(ml)'],8)} ml"
            logger.info(f"\n  - {row['Drug']}:Volume of Stock solution to be added for working solution is {round(row['Vol_WSol_ali(ml)'],8)} ml, and volume of diluent to be added is {round(row['Vol_Dil_Add(ml)'],8)} ml, and volume of remaining stock solution is {round(row['Vol_St_Left(ml)'],8)} ml\n")    
            print(f"  - {row['Drug']}:\n\tVolume of Stock solution to be added for working solution is {round(row['Vol_WSol_ali(ml)'],8)} ml,\n\tand volume of diluent to be added is {round(row['Vol_Dil_Add(ml)'],8)} ml,\n\tand volume of remaining stock solution is {round(row['Vol_St_Left(ml)'],8)} ml")
            output_file.write(result_line + "\n")
        
        output_file.write("\n----------------------------\n")
        output_file.write("END\n")
        output_file.write("----------------------------\n")
    
    print(f"\n----------------------------\nEND\n----------------------------\n")
    logger.info("\nEND\n")
    print(f"Final results written to: {output_path}\n")
    print_success("Calculation workflow completed successfully!")

if __name__ == "__main__":
    main()
