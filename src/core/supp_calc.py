from core.dst_calc import *
from tabulate import tabulate

log_base_name = None
log_index = 1

# Print only
def print_tabulate(df, *args, **kwargs):
    """
    Print a DataFrame as a formatted table using tabulate.
    Args:
        df (pd.DataFrame): DataFrame to print.
        *args, **kwargs: Arguments passed to tabulate.
    """
    table_str = tabulate(df, *args, **kwargs)
    print(table_str)

# Log only
def log_tabulate(df, *args, **kwargs):
    """
    Log a DataFrame as a formatted table to a log file in the 'logs' directory.
    Args:
        df (pd.DataFrame): DataFrame to log.
        *args, **kwargs: Arguments passed to tabulate.
    """
    global log_index, log_base_name
    table_str = tabulate(df, *args, **kwargs)
    log_filename = f"{log_base_name}_{log_index}.log"
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{log_filename}", 'a') as f:
        f.write(table_str + '\n')
        f.write('---\n')
    log_index += 1

# Print and log
def print_and_log_tabulate(df, *args, **kwargs):
    """
    Print and log a DataFrame as a formatted table.
    Args:
        df (pd.DataFrame): DataFrame to print and log.
        *args, **kwargs: Arguments passed to tabulate.
    """
    print_tabulate(df, *args, **kwargs)
    log_tabulate(df, *args, **kwargs)

def select_drugs(df, pre_supplied=None, error_log=None):
    """
    Allow the user to select drugs from a DataFrame, either interactively or using a pre-supplied string for automated testing.
    Args:
        df (pd.DataFrame): DataFrame containing drug information.
        pre_supplied (str, optional): Pre-supplied selection string for test automation.
        error_log (file, optional): File handle for logging errors.
    Returns:
        pd.DataFrame or None: DataFrame of selected drugs, or None if invalid in test mode.
    """
    while True:
        print("\nAvailable drugs:")
        for idx, drug in enumerate(df['Drug'], 1):
            print(f"{idx}. {drug}")
        print("\nEnter the numbers of the drugs you want to select (comma or space separated). Example: 1,3,5 or 2 4 6")
        if pre_supplied is not None:
            selection = pre_supplied
            print(f"[AUTO] Your selection: {selection}")
        else:
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
            msg = f"{n} is not in drug selection"
            print(msg)
            if error_log is not None:
                error_log.write(msg + '\n')
        if not selected_drugs:
            msg = "No valid drugs selected. Please try again.\n"
            print(msg)
            if error_log is not None:
                error_log.write(msg + '\n')
            if pre_supplied is not None:
                return None
            continue
        print("\nSelected drugs:")
        selected_df = df[df['Drug'].isin(selected_drugs)].copy()
        print_and_log_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        if pre_supplied is not None:
            # Assume auto-confirm for test mode
            return selected_df
        # Ask for confirmation
        confirm = input("\nDid you select the right drugs? Select 'n' to add or remove. (y to continue, n to reselect): ").strip().lower()
        if confirm == 'y':
            return selected_df
        else:
            print("Let's try again.")

def custom_critical_values(selected_df):
    """
    Prompt the user to enter custom critical values for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
    for idx, row in selected_df.iterrows():
        current_value = row['Critical_Concentration']
        prompt = f"Enter critical value for {row['Drug']} (current: {current_value}): "
        new_value = input(prompt).strip()
        if new_value:
            selected_df.at[idx, 'Critical_Concentration'] = float(new_value)

def purchased_weights(selected_df):
    """
    Prompt the user to enter purchased molecular weights for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
        #print("\nSummary of purchased molecular weights:")
        log_tabulate(selected_df[["Drug", "OrgMolecular_Weight (g/mol)", "PurchMolecular_Weight (g/mol)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        break
        # confirm = input("\nAre these purchased molecular weights correct? (y/n): ").strip().lower()
        # if confirm == 'y':
        #     break
        # else:
        #     print("Let's re-enter the purchased molecular weights.")

def stock_volume(selected_df):
    """
    Prompt the user to enter desired stock solution volumes for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
        #print("\nSummary of desired stock solution volumes:")
        log_tabulate(selected_df[["Drug", "Stock_Volume (ml)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        break
        # confirm = input("\nAre these stock solution volumes correct? (y/n): ").strip().lower()
        # if confirm == 'y':
        #     break
        # else:
        #     print("Let's re-enter the stock solution volumes.")

def cal_potency(selected_df):
    """
    Calculate potency and estimated drug weight for each selected drug and log the results.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
    log_tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
    

def act_drugweight (selected_df):
    """
    Prompt the user to enter the actual weighed drug amount for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
        # print("\nSummary of actual drug weights (mg):")
        log_tabulate(selected_df[["Drug", "Actual_DrugWeight (mg)"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        break
        # confirm = input("\nAre these drug weights correct? (y/n): ").strip().lower()
        # if confirm == 'y':
        #     break
        # else:
        #     print("Let's re-enter the drug weights.")    

def cal_stockdil(selected_df):
    """
    Calculate the volume of diluent and concentration of stock dilution for each selected drug and log the results.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
    log_tabulate(selected_df[summary_cols], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')

def mgit_tubes (selected_df):
    """
    Prompt the user to enter the number of MGIT tubes for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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
        # print("\nSummary of number of MGIT tubes:")
        log_tabulate(selected_df[["Drug", "Total Mgit tubes"]], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        break
        # confirm = input("\nAre these numbers correct? (y/n): ").strip().lower()
        # if confirm == 'y':
        #     break
        # else:
        #     print("Let's re-enter the number of MGIT tubes to be done.")

def cal_mgit_ws(selected_df):
    """
    Calculate MGIT working solution concentrations, volumes, and related values for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
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