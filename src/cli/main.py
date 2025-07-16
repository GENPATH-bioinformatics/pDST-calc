import argparse
import pandas as pd
from core.drug_database import load_drug_data
from core.dst_calc import *
from tabulate import tabulate

def select_drugs(df):
    while True:
        print("\nAvailable drugs:")
        for idx, drug in enumerate(df['Drug'], 1):
            print(f"{idx}. {drug}")
        print("\nEnter the numbers of the drugs you want to select (comma or space separated). Example: 1,3,5 or 2 4 6")
        selection = input("Your selection: ")
        numbers = [int(s) for s in selection.replace(',', ' ').split() if s.isdigit()]
        selected_drugs = []
        invalid_numbers = []
        for n in numbers:
            if 1 <= n <= len(df):
                selected_drugs.append(df.iloc[n - 1]['Drug'])
            else:
                invalid_numbers.append(n)
        for n in invalid_numbers:
            print(f"{n} is not in drug selection")
        if not selected_drugs:
            print("No valid drugs selected. Please try again.\n")
            continue
        print("\nSelected drugs:")
        selected_df = df[df['Drug'].isin(selected_drugs)].copy()
        print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        # Ask for confirmation
        confirm = input("\nDid you select the right drugs? Would you like to add or remove any? (y to continue, n to reselect): ").strip().lower()
        if confirm == 'y':
            return selected_df
        else:
            print("Let's try again.")

def custom_critical_values(selected_df):
    for idx, row in selected_df.iterrows():
        current_value = row['Critical_Concentration']
        prompt = f"Enter critical value for {row['Drug']} (current: {current_value}): "
        new_value = input(prompt).strip()
        if new_value:
            selected_df.at[idx, 'Critical_Concentration'] = new_value

def purchased_weights(selected_df):
    while True:
        purch_weights = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter purchased molecular weight for {row['Drug']} (original: {row['OrgMolecular_Weight']}): ").strip()
                    purch_weight = float(value)
                    purch_weights.append(purch_weight)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["PurchMolecular_Weight (g/mol)"] = purch_weights
        # Show summary and ask for confirmation
        print("\nSummary of purchased molecular weights:")
        print(tabulate(selected_df[["Drug", "OrgMolecular_Weight", "PurchMolecular_Weight (g/mol)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        confirm = input("\nAre these purchased molecular weights correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Let's re-enter the purchased molecular weights.")
    # Rename original column for clarity and add unit
    if 'OrgMolecular_Weight' in selected_df.columns:
        selected_df.rename(columns={"OrgMolecular_Weight": "OrgMolecular_Weight (g/mol)"}, inplace=True)

def stock_volume(selected_df):
    while True:
        stock_volumes = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter desired stock volume (ml) for {row['Drug']}: ").strip()
                    stock_volume = float(value)
                    stock_volumes.append(stock_volume)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["Stock_Volume (ml)"] = stock_volumes
        # Show summary and ask for confirmation
        print("\nSummary of desired stock solution volumes:")
        print(tabulate(selected_df[["Drug", "Stock_Volume (ml)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        confirm = input("\nAre these stock solution volumes correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Let's re-enter the stock solution volumes.")

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
        print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

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
    #print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

    # 3) Prompt user to enter desired stock solution volume
    print("\nFinally, enter desired stock solution volume (ml).")
    stock_volume(selected_df)

    # 4) Calculate Potency and Estimated Drug Weight for each drug
    potencies = []
    est_drugweights = []
    for idx, row in selected_df.iterrows():
        try:
            mol_purch = float(row.get('PurchMolecular_Weight (g/mol)', row.get('PurchMolecular_Weight')))
            mol_org = float(row.get('OrgMolecular_Weight (g/mol)', row.get('OrgMolecular_Weight')))
            crit_conc = float(row['Critical_Concentration'])
            stock_vol = float(row.get('Stock_Volume (ml)', row.get('Stock_Volume')))
            pot = potency(mol_purch, mol_org)
            est_dw = est_drugweight(crit_conc, stock_vol, pot)
        except Exception as e:
            pot = None
            est_dw = None
        potencies.append(pot)
        est_drugweights.append(est_dw)
    selected_df['Potency'] = potencies
    selected_df['Est_DrugWeight (mg)'] = est_drugweights
    print("\nTable with calculated Potency and Estimated Drug Weight:")
    print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

    # 5) Instruct user to weigh out the estimated drug weights
    print("\nINSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:")
    for idx, row in selected_df.iterrows():
        print(f"  - {row['Drug']}: {round(row['Est_DrugWeight (mg)'],8)} mg")

 
if __name__ == "__main__":
    main()
