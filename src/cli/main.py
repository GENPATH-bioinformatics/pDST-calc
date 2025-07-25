import argparse
import pandas as pd
from core.drug_database import load_drug_data
from core.dst_calc import *
from tabulate import tabulate
from core.supp_calc import (
    print_and_log_tabulate, select_drugs, custom_critical_values, 
    purchased_weights, stock_volume, cal_potency, act_drugweight,
    cal_stockdil, mgit_tubes, cal_mgit_ws
)
import logging
import os

def setup_logger(session_name="default"):
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    log_dir = os.path.abspath(log_dir)
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

def main():
    # Get user session name at the start
    session_name = input("Enter a name for this session (e.g., your name or experiment ID): ").strip()
    if not session_name:
        session_name = "default"
    
    logger = setup_logger(session_name)
    logger.info(f"\nApplication started for session: {session_name}\n")

    df = load_drug_data()

#---------------------------------------------STOCK SOLUTION

    # 1) User selects desired drugs
    selected_df = select_drugs(df)

    # Rename original column for clarity and add unit
    if 'Critical_Concentration' in selected_df.columns:
        selected_df.rename(columns={"Critical_Concentration": "Crit_Conc(mg/ml)"}, inplace=True)

    # 1.3) Ask if user wants to enter their own critical values
    response = input("\nWould you like to enter your own critical values for any of the selected drugs? (y/n): ").strip().lower()
    if response == 'y':
        custom_critical_values(selected_df)
        print("\nUpdated selected drugs with custom critical values:")
        print_and_log_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

    # Rename original column for clarity and add unit
    if 'OrgMolecular_Weight' in selected_df.columns:
        selected_df.rename(columns={"OrgMolecular_Weight": "OrgMol_W(g/mol)"}, inplace=True)

    # 2) Prompt user to enter purchased molecular weight for each drug
    print("\nNow, please enter the purchased molecular weight for each selected drug.")
    purchased_weights(selected_df)

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
    print("\nFinally, enter desired stock solution volume (ml).")
    stock_volume(selected_df)

    # 4) Calculate Potency and Estimated Drug Weight for each drug
    cal_potency(selected_df)

    # 5) Instruct user to weigh out the estimated drug weights
    print("\nINSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:")
    for idx, row in selected_df.iterrows():
        print(f"  - {row['Drug']}: {round(row['Est_DrugW(mg)'],8)} mg")

    act_drugweight(selected_df)

    # Calculate new volume of dilutent and new concentration of stock dilution for each drug
    cal_stockdil(selected_df)
    
#---------------------------------------------WORKING SOLUTION

    # 6) Prompt user to enter the number of MGIT Tubes to be used
    print("\nNow that we have a completed STOCK SOLUTION, enter the number of MGIT tubes you would like to fill.")
    mgit_tubes(selected_df)

    # Calculate MGIT conc, volume of working solution needed, volume of working solution to aliquot, volume of diluent and volume of stock solution left
    cal_mgit_ws(selected_df)

    # 7) Output final values of Volume of Working Solution to Aliquot and Volume of Diluent to be added
    print("\n----------------------------\nRESULT\n----------------------------\n\n Final Values:")
    logger.info("\nFinal Values:\n")
    for idx, row in selected_df.iterrows():
        logger.info(f"\n  - {row['Drug']}: Volume of Stock solution to be added for working solution is {round(row['Vol_WSol_ali(ml)'],8)} ml, and volume of diluent to be added is {round(row['Vol_Dil_Add(ml)'],8)} ml\n")    
        print(f"  - {row['Drug']}: Volume of Stock solution to be added for working solution is {round(row['Vol_WSol_ali(ml)'],8)} ml, and volume of diluent to be added is {round(row['Vol_Dil_Add(ml)'],8)} ml")    
    print("\n----------------------------\nEND\n----------------------------\n")
    logger.info("\nEND\n")

if __name__ == "__main__":
    main()
