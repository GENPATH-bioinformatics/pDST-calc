import logging
logger = logging.getLogger("pdst-calc")
# Use absolute import instead of relative import for standalone package
try:
    from dst_calc import *
except:
    from .dst_calc import *
from tabulate import tabulate

try:
    from app.cli.styling import print_input_prompt, print_success, print_error, print_warning
except ImportError:
    # Fallback implementations for standalone library use
    def print_input_prompt(message, example=None):
        """Fallback implementation for input prompts."""
        print(f"\n{message}")
        if example:
            print(f"Example: {example}")
    
    def print_success(message):
        """Fallback implementation for success messages."""
        print(f"✓ {message}")
    
    def print_error(message):
        """Fallback implementation for error messages."""
        print(f"✗ Error: {message}")
    
    def print_warning(message):
        """Fallback implementation for warning messages."""
        print(f"⚠ Warning: {message}")


def format_session_data(selected_df, drugs, include_partial=True):
    """
    Build a simple session JSON structure keyed by drug_id:
    {
      "drug_id": {
        "Crit_Conc(mg/ml)": float,
        "PurMol_W(g/mol)": float,
        "St_Vol(ml)": float,
        "Act_DrugW(mg)": float,
        "Total Mgit tubes": int
      }
    }
    - Uses default critical concentration from DB if not customized.
    - Allows partial values; missing fields are 0.
    """
    name_to_id = {d['name']: str(d['drug_id']) for d in drugs}

    def to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    def to_int(v, default=0):
        try:
            return int(float(v))
        except Exception:
            return default

    session_data = {}
    for _, row in selected_df.iterrows():
        drug_name = row['Drug']
        drug_id = name_to_id.get(drug_name)
        if not drug_id:
            continue

        # Default CC if not set
        crit_conc = row.get('Crit_Conc(mg/ml)')
        if crit_conc is None or (hasattr(crit_conc, 'isna') and crit_conc.isna()):
            drug_info = next((d for d in drugs if d['name'] == drug_name), None)
            crit_conc = drug_info['critical_value'] if drug_info else 0.0

        drug_data = {
            'Crit_Conc(mg/ml)': to_float(crit_conc),
            'PurMol_W(g/mol)': to_float(row.get('PurMol_W(g/mol)')),
            'St_Vol(ml)': to_float(row.get('St_Vol(ml)')),
            'Act_DrugW(mg)': to_float(row.get('Act_DrugW(mg)')),
            'Total Mgit tubes': to_int(row.get('Total Mgit tubes')),
        }

        if include_partial or any(v != 0.0 for v in drug_data.values()):
            session_data[drug_id] = drug_data

    return session_data

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
        # Parse the selection string
        try:
            numbers = []
            for s in selection.replace(',', ' ').split():
                s = s.strip()
                if s.isdigit():
                    numbers.append(int(s))
                elif s:  # Non-empty but not a digit
                    print_error(f"'{s}' is not a valid number. Please enter only numbers separated by commas or spaces.")
                    if input_file is not None:
                        return None
                    continue
        except ValueError:
            print_error("Invalid input format. Please enter numbers separated by commas or spaces.")
            if input_file is not None:
                return None
            continue
        selected_drugs = []
        invalid_numbers = []
        for n in numbers:
            if 1 <= n <= len(df):
                selected_drugs.append(df.iloc[n - 1]['Drug'])
            else:
                invalid_numbers.append(n)
        for n in invalid_numbers:
            msg = f"Drug number {n} is not in the available selection (1-{len(df)})"
            print_error(msg)
            if error_log is not None:
                error_log.write(msg + '\n')
        
        # If there are invalid numbers and we're in test mode, return None
        if invalid_numbers and input_file is not None:
            return None
        
        if not selected_drugs:
            msg = "No valid drugs selected. Please try again."
            print_error(msg)
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
        while True:
            confirm = input("\nDid you select the right drugs? Select 'n' to add or remove. (y to continue, n to reselect): ").strip().lower()
            if confirm in ['y', 'yes']:
                print_success("Drugs selected successfully")
                return selected_df
            elif confirm in ['n', 'no']:
                print("Let's try again.")
                break
            else:
                print_error("Please enter 'y' for yes or 'n' for no.")

def custom_critical_values(selected_df):
    """
    Prompt the user to enter custom critical values for each selected drug.
    Args:
        selected_df (pd.DataFrame): DataFrame of selected drugs.
    """
    for idx, row in selected_df.iterrows():
        current_value = row['Crit_Conc(mg/ml)']
        while True:
            prompt = f"Enter critical value for {row['Drug']} (current: {current_value}): "
            new_value = input(prompt).strip()
            try:
                new_value_float = float(new_value)
                if new_value_float <= 0:
                    print_error("Critical value must be greater than 0.")
                    continue
                selected_df.at[idx, 'Crit_Conc(mg/ml)'] = new_value_float
                print_success(f"Critical value updated to {new_value_float}")
                break
            except ValueError:
                print_error("Invalid input. Please enter a positive numeric value.")
                continue
            
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
                    
                    # Validate that purchased molecular weight is not negative or zero
                    if purch_weight <= 0:
                        print_error("Purchased molecular weight must be greater than 0.")
                        continue
                    
                    # Check if purchased weight is smaller than original weight
                    org_weight = float(row['OrgMol_W(g/mol)'])
                    if purch_weight < org_weight:
                        print_warning(f"Purchased molecular weight ({purch_weight}) is smaller than original weight ({org_weight}). This may indicate an issue with the drug purity or molecular weight.")
                        confirm = input("Do you want to continue with this value? (y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    
                    purch_weights.append(purch_weight)
                    print_success(f"Purchased molecular weight set to {purch_weight}")
                    break
                except ValueError:
                    print_error("Invalid input. Please enter a numeric value.")
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
                    
                    # Validate that stock volume is not negative or zero
                    if stock_volume <= 0:
                        print_error("Stock volume must be greater than 0.")
                        continue
                    
                    stock_volumes.append(stock_volume)
                    print_success(f"Stock volume set to {stock_volume} ml")
                    break
                except ValueError:
                    print_error("Invalid input. Please enter a numeric value.")
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
            
            # Validate inputs before calculation
            if mol_purch <= 0 or mol_org <= 0 or crit_conc <= 0 or stock_vol <= 0:
                print_error(f"Invalid values for {row['Drug']}: mol_purch={mol_purch}, mol_org={mol_org}, crit_conc={crit_conc}, stock_vol={stock_vol}")
                pot = None
                est_dw = None
            else:
                pot = potency(mol_purch, mol_org)
                est_dw = est_drugweight(crit_conc, stock_vol, pot)
                
                # Validate calculated values
                if pot is not None and (pot <= 0 or pot > 10):
                    print_warning(f"Potency for {row['Drug']} is {pot:.3f}, which seems unusual. Please verify your molecular weight values.")
                
                if est_dw is not None and est_dw <= 0:
                    print_error(f"Estimated drug weight for {row['Drug']} is {est_dw:.3f} mg, which is invalid. Please check your input values.")
                
        except Exception as e:
            print_error(f"Error calculating values for {row['Drug']}: {str(e)}")
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
                    
                    # Validate that actual drug weight is not negative or zero
                    if drugweight <= 0:
                        print_error("Actual drug weight must be greater than 0.")
                        continue
                    
                    # Check if actual weight is significantly different from estimated weight
                    if 'Est_DrugW(mg)' in selected_df.columns:
                        est_weight = selected_df.at[idx, 'Est_DrugW(mg)']
                        if est_weight is not None:
                            diff_percent = abs(drugweight - est_weight) / est_weight * 100
                            if diff_percent > 200:  # More than 200% difference
                                print_warning(f"Actual weight ({drugweight:.3f} mg) differs significantly from estimated weight ({est_weight:.3f} mg) by {diff_percent:.1f}%. Please verify your measurement.")
                                confirm = input("Do you want to continue with this value? (y/n): ").strip().lower()
                                if confirm != 'y':
                                    continue
                    
                    drugweights.append(drugweight)
                    print_success(f"Actual weight set to {drugweight} mg")
                    break
                except ValueError:
                    print_error("Invalid input. Please enter a numeric value.")
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
            
            # Validate inputs before calculation
            if drugweight_est <= 0 or drugweight_act <= 0 or stock_vol <= 0:
                print_error(f"Invalid values for {row['Drug']}: est_weight={drugweight_est}, act_weight={drugweight_act}, stock_vol={stock_vol}")
                vol_dil = None
                conc_stdil = None
            else:
                vol_dil = vol_diluent(drugweight_est,drugweight_act,stock_vol)
                conc_stdil= conc_stock(drugweight_act,vol_dil)
                
                # Validate calculated values
                if vol_dil is not None and vol_dil < 0:
                    print_error(f"Volume of diluent for {row['Drug']} is negative ({vol_dil:.3f} ml). This indicates an error in the calculation.")
                
                if conc_stdil is not None and conc_stdil <= 0:
                    print_error(f"Stock dilution concentration for {row['Drug']} is {conc_stdil:.3f} ug/ml, which is invalid.")
                
        except Exception as e:
            print_error(f"Error calculating stock dilution for {row['Drug']}: {str(e)}")
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
                    # Show input prompt
                    prompt = f"Enter number of MGIT tubes to be done for {row['Drug']}: "
                    
                    value = input(prompt).strip()
                    logger.info(f"\nNumber of MGIT tubes entered for {row['Drug']}: {value} \n ")
                    num = float(value)
                    
                    # Validate that number of MGIT tubes is not negative or zero
                    if num <= 0:
                        print_error("Number of MGIT tubes must be greater than 0.")
                        continue
                    
                    # Check if number is not a whole number
                    if num != int(num):
                        print_warning(f"Number of MGIT tubes should be a whole number. You entered {num}. This will be rounded to {int(num)}.")
                        num = int(num)
                    
                    # Validate that the number of tubes won't result in negative diluent volume
                    try:
                        # Get required values for calculation
                        cc_val = float(row.get('Crit_Conc(mg/ml)'))
                        concentration_mgit = conc_mgit(cc_val)
                        conc_st = float(row.get('Conc_st_dil(ug/ml)'))
                        
                        # Calculate working solution volume
                        volume_ws = vol_workingsol(num)
                        
                        # Calculate required stock solution volume
                        vol_stws = vol_ss_to_ws(volume_ws, concentration_mgit, conc_st)
                        
                        # Calculate diluent volume
                        vol_dil_toadd = vol_final_dil(vol_stws, volume_ws)
                        
                        # Check if diluent volume would be negative
                        if vol_dil_toadd < 0:
                            print_error(f"Number of MGIT tubes ({num}) is too high for {row['Drug']}. This would result in a negative diluent volume ({vol_dil_toadd:.3f} ml).")
                            
                            # Calculate a rough estimate of maximum tubes for guidance
                            try:
                                max_tubes_estimate = int((conc_st / concentration_mgit - 0.36) / 0.12)
                                if max_tubes_estimate > 0:
                                    print_error(f"Maximum recommended tubes for {row['Drug']}: {max_tubes_estimate}")
                                else:
                                    print_error(f"Stock solution for {row['Drug']} is too concentrated for any MGIT tubes.")
                            except:
                                print_error(f"Stock solution for {row['Drug']} is too concentrated for the requested number of tubes.")
                            continue
                    
                    except Exception as e:
                        # If calculation fails, still allow the input but warn
                        print_warning(f"Could not validate MGIT tube count for {row['Drug']}: {str(e)}")
                    
                    num_mgit.append(num)
                    print_success(f"Number of MGIT tubes set to {num}")
                    break
                except ValueError:
                    print_error("Invalid input. Please enter a numeric value.")
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
            
            # Validate calculated values
            if concentration_mgit is not None and concentration_mgit <= 0:
                print_error(f"MGIT working solution concentration for {row['Drug']} is {concentration_mgit:.3f} ug/ml, which is invalid.")
            
            if volume_ws is not None and volume_ws <= 0:
                print_error(f"Working solution volume for {row['Drug']} is {volume_ws:.3f} ml, which is invalid.")
            
            if vol_stws is not None and vol_stws < 0:
                print_error(f"Volume of stock solution to working solution for {row['Drug']} is negative ({vol_stws:.3f} ml).")
            
            if vol_dil_toadd is not None and vol_dil_toadd < 0:
                print_error(f"Volume of diluent to add for {row['Drug']} is negative ({vol_dil_toadd:.3f} ml).")
            
            if vol_st_lft is not None and vol_st_lft < 0:
                print_warning(f"Volume of stock solution left for {row['Drug']} is negative ({vol_st_lft:.3f} ml). This may indicate insufficient stock solution.")
            
        except Exception as e:
            print_error(f"Error calculating MGIT working solution for {row['Drug']}: {str(e)}")
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
