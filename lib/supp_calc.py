import logging
logger = logging.getLogger("pdst-calc")
from lib.dst_calc import *
from tabulate import tabulate
from app.cli.styling import print_input_prompt, print_success

# Print and log
def print_and_log_tabulate(df, *args, **kwargs):
    """
    Print a DataFrame as a formatted table and log it to the logger.
    Args:
        df (pd.DataFrame): DataFrame to print and log.
        *args, **kwargs: Arguments passed to tabulate.
    """
    table_str = tabulate(df, *args, **kwargs)
    print(table_str)
    logger.info("\n" + table_str + "\n")

def print_table(df, *args, **kwargs):
    """
    Print a DataFrame as a formatted table using tabulate.
    Args:
        df (pd.DataFrame): DataFrame to print.
        *args, **kwargs: Arguments passed to tabulate.
    """
    table_str = tabulate(df, *args, **kwargs)
    print(table_str)

def select_drugs(df, input_file=None, error_log=None):
    """
    Allow the user to select drugs from a DataFrame, either interactively or using a pre-supplied string for automated testing.
    Args:
        df (pd.DataFrame): DataFrame containing drug information.
        input_file (str, optional): Pre-supplied selection string for test automation (e.g., "1,2,3").
        error_log (file, optional): File handle for logging errors during automated testing.
    Returns:
        pd.DataFrame or None: DataFrame of selected drugs, or None if invalid in test mode.
    """
    while True:
        if input_file is not None:
            selection = input_file
        else:
            print("\nAvailable drugs:")
            for idx, drug in enumerate(df['Drug'], 1):
                print(f"{idx}. {drug}")
            print("\n")
            print_input_prompt("Enter the numbers of the drugs you want to select (comma or space separated).", example="1,3,5 or 2 4 6")
            selection = input("Your selection: ")
            if selection == 'all':
                return df
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
        
        # If there are invalid numbers and we're in test mode, return None
        if invalid_numbers and input_file is not None:
            return None
        
        if not selected_drugs:
            msg = "No valid drugs selected. Please try again.\n"
            print(msg)
            if error_log is not None:
                error_log.write(msg + '\n')
            if input_file is not None:
                return None
            continue
        print("\nSelected drugs:")
        selected_df = df[df['Drug'].isin(selected_drugs)].copy()
        print_table(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left')
        logger.info("\nDrugs selected:\n"+ selected_df.to_string(index=False) + "\n")
        if input_file is not None:
            # Assume auto-confirm for test mode
            return selected_df
        # Ask for confirmation
        confirm = input("\nDid you select the right drugs? Select 'n' to add or remove. (y to continue, n to reselect): ").strip().lower()
        if confirm == 'y':
            print_success("Drugs selected successfully")
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
        current_value = row['Crit_Conc(mg/ml)']
        prompt = f"Enter critical value for {row['Drug']} (current: {current_value}): "
        new_value = input(prompt).strip()
        if new_value:
            selected_df.at[idx, 'Crit_Conc(mg/ml)'] = float(new_value)

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
                    value = input(f"Enter purchased molecular weight for {row['Drug']} (original: {row['OrgMol_W(g/mol)']}): ").strip()
                    logger.info(f"\nPurchased molecular weight entered for {row['Drug']}: {value} \n")
                    purch_weight = float(value)
                    purch_weights.append(purch_weight)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["PurMol_W(g/mol)"] = purch_weights
        break

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
                    logger.info(f"\nDesired stock volume entered for {row['Drug']}: {value} \n")
                    stock_volume = float(value)
                    stock_volumes.append(stock_volume)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["St_Vol(ml)"] = stock_volumes
        break

def cal_potency(selected_df):
    """
    Calculate potency and estimated drug weight for each selected drug and log the results.
    Potency is calculated as purchased molecular weight / original molecular weight.
    Estimated drug weight accounts for potency and target concentration.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs with molecular weights and critical concentrations.
    """
    potencies = []
    est_drugweights = []
    for idx, row in selected_df.iterrows():
        try:
            mol_purch = float(row.get('PurMol_W(g/mol)'))
            mol_org = float(row.get('OrgMol_W(g/mol)'))
            crit_conc = float(row['Crit_Conc(mg/ml)'])
            stock_vol = float(row.get('St_Vol(ml)'))
            pot = potency(mol_purch, mol_org)
            est_dw = est_drugweight(crit_conc, stock_vol, pot)
        except Exception as e:
            pot = None
            est_dw = None
        potencies.append(pot)
        est_drugweights.append(est_dw)
    selected_df['Potency'] = potencies
    selected_df['Est_DrugW(mg)'] = est_drugweights
    logger.info("\n" + tabulate(selected_df, headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left') + "\n")


def act_drugweight(selected_df):
    """
    Prompt the user to enter the actual weighed drug amount for each selected drug.
    This is the real weight measured after estimating the required amount.
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
                    logger.info(f"\nActual weight entered for {row['Drug']}: {value} \n")
                    drugweight = float(value)
                    drugweights.append(drugweight)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["Act_DrugW(mg)"] = drugweights
        break

def cal_stockdil(selected_df):
    """
    Calculate the volume of diluent and concentration of stock dilution for each selected drug.
    This adjusts the stock solution based on the difference between estimated and actual drug weights.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs with estimated and actual weights.
    """
    vol_dils = []
    conc_stockdiluent = []
    for idx, row in selected_df.iterrows():
        try:
            drugweight_est = float(row.get('Est_DrugW(mg)'))
            drugweight_act = float(row.get('Act_DrugW(mg)'))
            stock_vol = float(row.get('St_Vol(ml)'))
            vol_dil = vol_diluent(drugweight_est,drugweight_act,stock_vol)
            conc_stdil= conc_stock(drugweight_act,vol_dil)
        except Exception as e:
            vol_dil = None
            conc_stdil = None
        vol_dils.append(vol_dil)
        conc_stockdiluent.append(conc_stdil)
    selected_df['Vol_Dil(ml)'] = vol_dils
    selected_df['Conc_st_dil(ug/ml)'] = conc_stockdiluent

    # Only use columns that exist in the DataFrame
    summary_cols = [
        'Drug',
        'Est_DrugW(mg)',
        'Act_DrugW(mg)',
        'Vol_Dil(ml)',
        'Conc_st_dil(ug/ml)'
    ]
    available_cols = [col for col in summary_cols if col in selected_df.columns]
    if available_cols:
        logger.info("\n" + tabulate(selected_df[available_cols], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left') + "\n")

def mgit_tubes(selected_df):
    """
    Prompt the user to enter the number of MGIT tubes for each selected drug.
    This determines the volume of working solution needed.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
    while True:
        num_mgit = []
        for idx, row in selected_df.iterrows():
            while True:
                try:
                    value = input(f"Enter number of MGIT tubes to be done for {row['Drug']}: ").strip()
                    logger.info(f"\nNumber of MGIT tubes entered for {row['Drug']}: {value} \n ")
                    num = float(value)
                    num_mgit.append(num)
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric value.")
        selected_df["Total Mgit tubes"] = num_mgit
        break

def cal_mgit_ws(selected_df):
    """
    Calculate MGIT working solution concentrations, volumes, and related values for each selected drug.
    This includes working solution concentration, volume needed, aliquot volume, diluent volume, and remaining stock.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs with all previous calculations.
    """
    conc_mgits = []
    vol_ws = []
    vol_ws_ali = []
    vol_diluents = []
    vol_left = []

    for idx, row in selected_df.iterrows():
        try:
            cc_val = float(row.get('Crit_Conc(mg/ml)'))
            concentration_mgit = conc_mgit(cc_val)
            num_mgit = float(row.get('Total Mgit tubes'))
            volume_ws = vol_workingsol(num_mgit)
            conc_st = float(row.get('Conc_st_dil(ug/ml)'))
            vol_stws = vol_ss_to_ws(volume_ws,concentration_mgit,conc_st)
            vol_dil_toadd = vol_final_dil(vol_stws,volume_ws)
            vol_st = float(row.get('Vol_Dil(ml)'))
            vol_st_lft = vol_ssleft(vol_stws,vol_st)
            
        except Exception as e:
            concentration_mgit = None
            volume_ws = None
            vol_stws = None
            vol_dil_toadd = None
            vol_st_lft = None
        conc_mgits.append(concentration_mgit)
        vol_ws.append(volume_ws)
        vol_ws_ali.append(vol_stws)
        vol_diluents.append(vol_dil_toadd)
        vol_left.append(vol_st_lft)

    selected_df['WSol_Conc_MGIT(ug/ml)'] = conc_mgits
    selected_df['WSol_Vol(ml)'] = vol_ws
    selected_df['Vol_WSol_ali(ml)'] = vol_ws_ali
    selected_df['Vol_Dil_Add(ml)'] = vol_diluents
    selected_df['Vol_St_Left(ml)'] = vol_left

    # Only use columns that exist in the DataFrame
    summary_cols = [
        'Drug',
        'WSol_Conc_MGIT(ug/ml)',
        'WSol_Vol(ml)',
        'Vol_WSol_ali(ml)',
        'Vol_Dil_Add(ml)',
        'Vol_St_Left(ml)'
    ]
    available_cols = [col for col in summary_cols if col in selected_df.columns]
    if available_cols:
        logger.info("\n" + tabulate(selected_df[available_cols], headers='keys', tablefmt='grid', showindex=False, stralign='left', numalign='left') + "\n")
