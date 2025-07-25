import argparse
import pandas as pd
from core.drug_database import load_drug_data
from core.dst_calc import *
from tabulate import tabulate
from core.supp_calc import (
    print_tabulate, select_drugs, custom_critical_values, 
    purchased_weights, stock_volume, cal_potency, act_drugweight,
    cal_stockdil, mgit_tubes, cal_mgit_ws
)

def main():
    df = load_drug_data()

#---------------------------------------------STOCK SOLUTION

    # 1) User selects desired drugs
    selected_df = select_drugs(df)

    # 1.3) Ask if user wants to enter their own critical values
    response = input("\nWould you like to enter your own critical values for any of the selected drugs? (y/n): ").strip().lower()
    if response == 'y':
        custom_critical_values(selected_df)
        print("\nUpdated selected drugs with custom critical values:")
        print_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

    # Rename original column for clarity and add unit
    if 'OrgMolecular_Weight' in selected_df.columns:
        selected_df.rename(columns={"OrgMolecular_Weight": "OrgMolecular_Weight (g/mol)"}, inplace=True)

    # 2) Prompt user to enter purchased molecular weight for each drug
    print("\nNow, please enter the purchased molecular weight for each selected drug.")
    purchased_weights(selected_df)
    #print("\nUpdated table with purchased molecular weights:")

    # Reorder columns so PurchMolecular_Weight (g/mol) is next to OrgMolecular_Weight (g/mol)
    cols = list(selected_df.columns)
    if 'OrgMolecular_Weight (g/mol)' in cols and 'PurchMolecular_Weight (g/mol)' in cols:
        # Remove both columns
        cols.remove('OrgMolecular_Weight (g/mol)')
        cols.remove('PurchMolecular_Weight (g/mol)')
        # Insert after 'Drug'
        new_order = ['Drug', 'OrgMolecular_Weight (g/mol)', 'PurchMolecular_Weight (g/mol)'] + [c for c in cols if c != 'Drug']
        selected_df = selected_df[new_order]
    #print_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

    # 3) Prompt user to enter desired stock solution volume
    print("\nFinally, enter desired stock solution volume (ml).")
    stock_volume(selected_df)

    # 4) Calculate Potency and Estimated Drug Weight for each drug
    cal_potency(selected_df)

    # 5) Instruct user to weigh out the estimated drug weights
    print("\nINSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:")
    for idx, row in selected_df.iterrows():
        print(f"  - {row['Drug']}: {round(row['Est_DrugWeight (mg)'],8)} mg")

    act_drugweight(selected_df)
    #print_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

    # Calculate new volume of dilutent and new concentration of stock dilution for each drug
    cal_stockdil(selected_df)
    
#---------------------------------------------WORKING SOLUTION

    # 6) Prompt user to enter the number of MGIT Tubes to be used
    print("\nNow that we have a completed STOCK SOLUTION, enter the number of MGIT tubes you would like to fill.")
    mgit_tubes(selected_df)

    # Calculate MGIT conc, volume of working solution needed, volume of working solution to aliquot, volume of diluent and volume of stock solution left
    cal_mgit_ws(selected_df)

    # 7) Output final values of Volume of Working Solution to Aliquot and Volume of Diluent to be added
    print("\n----------------------------\nRESULT\n----------------------------\n Final Values:")
    for idx, row in selected_df.iterrows():
        print(f"  - {row['Drug']}: Volume of Stock solution to be added for working solution is {round(row['Volume_WorkingSol_to_aliquot (ml)'],8)} ml, and volume of diluent to be added is {round(row['Volume_Dil_to_Add (ml)'],8)} ml")    

if __name__ == "__main__":
    main()
