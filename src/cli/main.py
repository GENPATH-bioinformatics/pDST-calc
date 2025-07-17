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
            selected_df.at[idx, 'Critical_Concentration'] = float(new_value)

def purchased_weights(selected_df):
    while True:
        purch_weights = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter purchased molecular weight for {row['Drug']} (original: {row['OrgMolecular_Weight (g/mol)']}): ").strip()
                    purch_weight = float(value)
                    purch_weights.append(purch_weight)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["PurchMolecular_Weight (g/mol)"] = purch_weights
        # Show summary and ask for confirmation
        print("\nSummary of purchased molecular weights:")
        print(tabulate(selected_df[["Drug", "OrgMolecular_Weight (g/mol)", "PurchMolecular_Weight (g/mol)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        confirm = input("\nAre these purchased molecular weights correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Let's re-enter the purchased molecular weights.")

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

def cal_potency(selected_df):
    potencies = []
    est_drugweights = []
    for idx, row in selected_df.iterrows():
        try:
            mol_purch = float(row.get('PurchMolecular_Weight (g/mol)'))
            mol_org = float(row.get('OrgMolecular_Weight (g/mol)'))
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

def act_drugweight (selected_df):
    print("\n")
    while True:
        drugweights = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter actual weight for {row['Drug']}: ").strip()
                    drugweight = float(value)
                    drugweights.append(drugweight)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["Actual_DrugWeight (mg)"] = drugweights
        # Show summary and ask for confirmation
        print("\nSummary of actual drug weights (mg):")
        print(tabulate(selected_df[["Drug", "Actual_DrugWeight (mg)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        confirm = input("\nAre these drug weights correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Let's re-enter the drug weights.")    

def cal_stockdil(selected_df):
    vol_dils = []
    conc_stockdiluent = []
    for idx, row in selected_df.iterrows():
        try:
            drugweight_est = float(row.get('Est_DrugWeight (mg)'))
            drugweight_act = float(row.get('Actual_DrugWeight (mg)'))
            stock_vol = float(row.get('Stock_Volume (ml)'))
            vol_dil = vol_diluent(drugweight_est,drugweight_act,stock_vol)
            conc_stdil= conc_stock(drugweight_act,vol_dil)
        except Exception as e:
            vol_dil = None
            conc_stdil = None
        vol_dils.append(vol_dil)
        conc_stockdiluent.append(conc_stdil)
    selected_df['Volume_Dilutent (ml)'] = vol_dils
    selected_df['Concentration_stock_dilution (ug/ml)'] = conc_stockdiluent

    summary_cols = [
        'Drug',
        'Est_DrugWeight (mg)',
        'Actual_DrugWeight (mg)',
        'Volume_Dilutent (ml)',
        'Concentration_stock_dilution (ug/ml)'
    ]
    print("\nSummary Table:")
    print(tabulate(selected_df[summary_cols], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

def mgit_tubes (selected_df):
    while True:
        num_mgit = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter number of MGIT tubes to be done for {row['Drug']}: ").strip()
                    num = float(value)
                    num_mgit.append(num)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["Total Mgit tubes"] = num_mgit
        # Show summary and ask for confirmation
        print("\nSummary of number of MGIT tubes:")
        print(tabulate(selected_df[["Drug", "Total Mgit tubes"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))
        confirm = input("\nAre these numbers correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Let's re-enter the number of MGIT tubes to be done.")

def cal_mgit_ws(selected_df):
    conc_mgits = []
    vol_ws = []
    vol_ws_ali = []
    vol_diluents = []
    vol_left = []

    for idx, row in selected_df.iterrows():
        try:
            cc_val = float(row.get('Critical_Concentration'))
            concentration_mgit = conc_mgit(cc_val)
            num_mgit = float(row.get('Total Mgit tubes'))
            volume_ws = vol_workingsol(num_mgit)
            conc_st = float(row.get('Concentration_stock_dilution (ug/ml)'))
            print(conc_st)
            vol_stws = vol_ss_to_ws(volume_ws,concentration_mgit,conc_st)
            vol_dil_toadd = vol_final_dil(vol_stws,volume_ws)
            vol_st = float(row.get('Volume_Dilutent (ml)'))
            vol_st_lft = vol_ssleft(vol_stws,vol_st)
            
        except Exception as e:
            vol_dil = None
            conc_stdil = None
        conc_mgits.append(concentration_mgit)
        vol_ws.append(volume_ws)
        vol_ws_ali.append(vol_stws)
        vol_diluents.append(vol_dil_toadd)
        vol_left.append(vol_st_lft)

    selected_df['WorkingSol_Conc_MGIT'] = conc_mgits
    selected_df['WorkingSol_Volume (ml)'] = vol_ws
    selected_df['Volume_WorkingSol_to_aliquot (ml)'] = vol_ws_ali
    selected_df['Volume_Dil_to_Add (ml)'] = vol_diluents
    selected_df['Volume_Stock_Left (ml)'] = vol_left

    summary_cols = [
        'Drug',
        'Total Mgit tubes',
        'WorkingSol_Conc_MGIT',
        'WorkingSol_Volume (ml)',
        'Volume_WorkingSol_to_aliquot (ml)',
        'Volume_Dil_to_Add (ml)',
        'Volume_Stock_Left (ml)'
    ]
    print("\nSummary Table:")
    print(tabulate(selected_df[summary_cols], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

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
    #print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

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
    #print(tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left'))

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
        print(f"  - {row['Drug']}: Volume of Stock solution to be added for working solution is {round(row['Volume_of_Working_Solution_to_aliquot (ml)'],8)} ml, and volume of diluent to be added is {round(row['Volume_Dilutent_to_Add (ml)'],8)} ml")    

if __name__ == "__main__":
    main()
