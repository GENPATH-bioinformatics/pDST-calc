from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
import sys
import os

# Add the project root to Python path so we can import from app.api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.api.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock, conc_mgit, vol_workingsol, vol_ss_to_ws, vol_final_dil
from app.api.auth import register_user, login_user
from app.api.database import db_manager

# Unit conversion functions

def convert_volume(value, from_unit, to_unit):
    """Convert volume between different units."""
    if from_unit == to_unit:
        return value
    
    # Convert to ml as base unit
    if from_unit == "ml":
        base_value = value
    
    elif from_unit == "μl":
        base_value = value / 1000
    else:
        base_value = value
    
    # Convert from base unit to target unit
    if to_unit == "ml":
        return base_value
    
    elif to_unit == "μl":
        return base_value * 1000
    else:
        return base_value

def convert_concentration(value, from_unit, to_unit):
    # Deprecated: concentration is fixed to mg/ml now. Keep for compatibility.
    return value

def convert_weight(value, from_unit, to_unit):
    """Convert weight between different units."""
    if from_unit == to_unit:
        return value
    
    # Convert to mg as base unit
    if from_unit == "mg":
        base_value = value
    elif from_unit == "g":
        base_value = value * 1000
    elif from_unit == "μg":
        base_value = value / 1000
    else:
        base_value = value
    
    # Convert from base unit to target unit
    if to_unit == "mg":
        return base_value
    elif to_unit == "g":
        return base_value / 1000
    elif to_unit == "μg":
        return base_value * 1000
    else:
        return base_value

# Global variables to store calculation results
calculation_results = reactive.Value({})

def get_estimated_weight(drug_index):
    """Get the estimated weight for a drug from previous calculations."""
    results = calculation_results.get()
    if results and 'estimated_weights' in results:
        estimated_weights = results['estimated_weights']
        if isinstance(estimated_weights, list) and drug_index < len(estimated_weights):
            return estimated_weights[drug_index]
    return 0

def perform_initial_calculations():
    """Perform initial calculations for estimated weights."""
    selected = input.drug_selection()
    if not selected:
        return {}
    
    try:
        drug_data = load_drug_data()
        estimated_weights = []
        
        for i, drug_name in enumerate(selected):
            # Get input values
            stock_vol = input[f"stock_volume_{i}"]()
            purch_molw = input[f"purchased_molw_{i}"]()
            custom_crit = input[f"custom_critical_{i}"]()
            
            if stock_vol and purch_molw and custom_crit:
                # Convert to standard units for calculations
                stock_vol_ml = convert_volume(stock_vol, volume_unit(), "ml")
                purch_molw_gmol = purch_molw
                # Critical concentration is already in mg/ml
                custom_crit_mgml = custom_crit
                
                # Calculate potency
                pot = potency(purch_molw_gmol, drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0])
                
                # Calculate estimated drug weight
                est_dw = est_drugweight(custom_crit_mgml, stock_vol_ml, pot)
                
                # Convert to user's preferred weight unit
                est_dw_user_unit = convert_weight(est_dw, "mg", weight_unit())
                estimated_weights.append(est_dw_user_unit)
            else:
                estimated_weights.append(0)
        
        return {'estimated_weights': estimated_weights}
    except Exception as e:
        print(f"Error in calculations: {e}")
        return {}

def perform_final_calculations():
    """Perform final calculations for MGIT tubes and working solutions."""
    selected = input.drug_selection()
    if not selected:
        return []
    
    try:
        drug_data = load_drug_data()
        final_results = []
        
        for i, drug_name in enumerate(selected):
            try:
                # Get actual weight and MGIT tubes
                actual_weight = input[f"actual_weight_{i}"]()
                mgit_tubes = input[f"mgit_tubes_{i}"]()
                
                if actual_weight and mgit_tubes:
                    # Convert actual weight to mg for calculations
                    actual_weight_mg = convert_weight(actual_weight, weight_unit(), "mg")
                    
                    # Get original values for calculations
                    stock_vol = input[f"stock_volume_{i}"]()
                    purch_molw = input[f"purchased_molw_{i}"]()
                    custom_crit = input[f"custom_critical_{i}"]()
                    
                    stock_vol_ml = convert_volume(stock_vol, volume_unit(), "ml")
                    purch_molw_gmol = purch_molw
                    # Critical concentration is already in mg/ml
                    custom_crit_mgml = custom_crit
                    
                    # Calculate potency
                    org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                    pot = potency(purch_molw_gmol, org_molw)
                    
                    # Step 1: Calculate estimated drug weight (from step 2)
                    est_drug_weight_mg = est_drugweight(custom_crit_mgml, stock_vol_ml, pot)
                    
                    # Step 2: Calculate diluent volume and stock concentration
                    vol_dil = vol_diluent(est_drug_weight_mg, actual_weight_mg, stock_vol_ml)
                    conc_stock_ugml = conc_stock(actual_weight_mg, vol_dil)
                    
                    # Step 3: Calculate MGIT working solution
                    conc_mgit_ugml = conc_mgit(custom_crit_mgml)  # conc_mgit expects mg/ml input, returns μg/ml output
                    vol_working_sol_ml = vol_workingsol(mgit_tubes)
                    vol_stock_to_ws_ml = vol_ss_to_ws(vol_working_sol_ml, conc_mgit_ugml, conc_stock_ugml)
                    vol_diluent_to_add_ml = vol_final_dil(vol_stock_to_ws_ml, vol_working_sol_ml)
                    
                    # Convert volumes to user's preferred unit
                    stock_vol_user = convert_volume(vol_stock_to_ws_ml, "ml", volume_unit())
                    diluent_vol_user = convert_volume(vol_diluent_to_add_ml, "ml", volume_unit())
                    
                    # Check for warnings
                    warning_message = ""
                    if vol_diluent_to_add_ml < 0:
                        warning_message = f"Warning for {drug_name}: Stock concentration too low. Using full working volume as stock solution."
                        stock_vol_user = convert_volume(vol_working_sol_ml, "ml", volume_unit())
                        diluent_vol_user = convert_volume(0, "ml", volume_unit())
                    
                    # Check if stock volume to aliquot exceeds available stock volume
                    if vol_stock_to_ws_ml > stock_vol_ml:
                        if warning_message:
                            warning_message += f" Additionally, stock volume to aliquot ({vol_stock_to_ws_ml:.4f} ml) exceeds available stock volume ({stock_vol_ml:.4f} ml)."
                        else:
                            warning_message = f"Warning for {drug_name}: Stock volume to aliquot ({vol_stock_to_ws_ml:.4f} ml) exceeds available stock volume ({stock_vol_ml:.4f} ml). This calculation is not possible with the current parameters."
                        print(f"WARNING TRIGGERED for {drug_name}: {warning_message}")
                    
                    drug_row = drug_data[drug_data['Drug'] == drug_name]
                    diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else "Unknown"
                    
                    final_results.append({
                        'Drug': drug_name,
                        'Diluent': diluent,
                        'Stock_Vol_Aliquot': stock_vol_user,
                        'Diluent_Vol': diluent_vol_user
                    })
                    
                    # Store warning if present
                    if warning_message:
                        current_warnings = warnings()
                        current_warnings.append(warning_message)
                        warnings.set(current_warnings)
                        print(f"WARNING STORED: {warning_message}")
                        print(f"Total warnings now: {len(warnings())}")
            except Exception as e:
                print(f"Error processing drug {drug_name}: {e}")
                import traceback
                traceback.print_exc()
        
        return final_results
    except Exception as e:
        print(f"Error in final calculations: {e}")
        import traceback
        traceback.print_exc()
        return []

# Read the first column from the CSV file
drug_options = load_drug_data()
drug_selection = drug_options.iloc[:, 0].dropna().tolist()

# Track current step
current_step = reactive.Value(1)
# Track if calculate button has been clicked
calculate_clicked = reactive.Value(False)

# Track if final calculation has been performed
final_calculation_done = reactive.Value(False)

# Track warnings for modal display
warnings = reactive.Value([])

# Unit selection reactive values
volume_unit = reactive.Value("ml")
weight_unit = reactive.Value("mg")

# Auth/user session state
current_user = reactive.Value(None)
auth_message = reactive.Value("")
auth_view = reactive.Value("none")  # one of: none | register | login
current_session = reactive.Value(None)  # {'session_id': int, 'session_name': str}

# Add top whitespace
ui.tags.div(style="margin-top: 50px;")
            
with ui.navset_card_pill(id="tab", selected="A"):
    with ui.nav_panel("A"):
        # Main layout with sidebar
        with ui.layout_sidebar():
            
            # Left sidebar panel
            with ui.sidebar():
                ui.tags.div(
                    ui.tags.h3("pDST Calculator", style="color: #2c3e50; margin-bottom: 10px;"),
                    ui.tags.p("Calculate drug susceptibility testing parameters", style="color: #7f8c8d; margin-bottom: 20px;"),
                    style="border-bottom: 1px solid #ecf0f1; padding-bottom: 20px;"
                )
                
                ui.tags.h4("Sections", style="color: #2c3e50; margin-bottom: 15px;")
                
                # Progress steps
                @render.ui
                def progress_steps():
                    steps = [
                        "Drug Selection",
                        "Parameters",
                        "Final Results"
                    ]
                
                    step_elements = []
                    for i, step in enumerate(steps):
                        step_style = "color: #3498db; font-weight: bold;" if current_step() == i + 1 else "color: #7f8c8d;"
                        step_elements.append(
                    ui.tags.div(
                        ui.tags.p(step, style=step_style),
                        style="margin-bottom: 8px;"
                    )
                        )
                    
                    return ui.tags.div(*step_elements)
                
                ui.tags.div(style="margin-top: 30px;")
                
                # Unit Selection Section
                ui.tags.div(style="margin-top: 30px;")
                ui.tags.h4("Unit Preferences", style="color: #2c3e50; margin-bottom: 15px;")
                
                ui.tags.p("Select your preferred units:", style="color: #7f8c8d; font-size: 12px; margin-bottom: 10px;")
                
                # Molecular weight fixed to g/mol
                ui.input_select(
                    "vol_unit",
                    "Volume:",
                    choices=["ml", "μl"],
                    selected="ml"
                )
                
                # Concentration fixed to mg/ml
                ui.input_select(
                    "weight_unit",
                    "Weight:",
                    choices=["mg", "g", "μg"],
                    selected="mg"
                )
            
            # Main content area with additional top padding
            ui.tags.div(style="padding-top: 30px;")
            
            # Step 1: Drug Selection
            with ui.tags.div(id="step1"):
                ui.tags.h2("Select Drugs", style="color: #2c3e50; margin-bottom: 20px;")
                ui.input_selectize(
                    "drug_selection",
                    "Select the drugs you want to calculate parameters for:",
                    drug_selection,
                    multiple=True,
                )
                
                # Display selected drugs in a table
                @render.ui
                def selected_drugs_table():

                    selected = input.drug_selection()
                    if not selected:
                        return ui.tags.div("No drugs selected yet.")
                    
                    # Get the full drug data
                    drug_data = load_drug_data()
                    
                    if current_step() == 1:
                        # Create table headers for step 1
                        table_headers = ui.tags.tr(
                            ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                            ui.tags.th("Mol. Weight (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                            ui.tags.th("Crit. Conc. (mg/ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                            style="background-color: #f8f9fa;"
                        )
                        
                        # Create table rows for each selected drug
                        table_rows = []
                        for i, drug_name in enumerate(selected):
                            # Find the drug data in the dataframe
                            drug_row = drug_data[drug_data['Drug'] == drug_name]
                            if not drug_row.empty:
                                row_data = drug_row.iloc[0]
                                row = ui.tags.tr(
                                    ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                    ui.tags.td(f"{row_data['OrgMolecular_Weight']:.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                    ui.tags.td(row_data['Diluent'], style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                    ui.tags.td(
                                        ui.input_numeric(
                                            f"custom_critical_{i}",
                                            "",
                                            value=row_data['Critical_Concentration'],
                                            min=0,
                                            step=0.01
                                        ),
                                        style="padding: 5px; border: 1px solid #ddd; width: 100px;"
                                    ),
                                    style="background-color: white;"
                                )
                                table_rows.append(row)
                        
                        return ui.tags.div(
                            ui.tags.div(
                                ui.tags.table(
                                    table_headers,
                                    *table_rows,
                                    style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                ),
                                style="overflow-x: auto; max-width: 100%;"
                            )
                        )
                    elif current_step() == 2:
                        # Create table headers for step 2
                        table_headers = ui.tags.tr(
                            ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                            ui.tags.th("Crit. Conc. (mg/ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                            ui.tags.th("Org. Mol. Wt. (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th("Purch. Mol. Wt. (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th(f"Stock Vol. ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                            style="background-color: #f8f9fa;"
                        )
                        
                        # Create table rows for each selected drug
                        table_rows = []
                        for i, drug_name in enumerate(selected):
                            # Find the drug data in the dataframe for step 2
                            drug_row = drug_data[drug_data['Drug'] == drug_name]
                            if not drug_row.empty:
                                row_data = drug_row.iloc[0]
                                row = ui.tags.tr(
                                    ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                    ui.tags.td(f"{row_data['Critical_Concentration']:.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                    ui.tags.td(f"{row_data['OrgMolecular_Weight']:.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                    ui.tags.td(
                                        ui.input_numeric(
                                            f"purchased_molw_{i}",
                                            "",
                                            value=0,
                                            min=row_data['OrgMolecular_Weight'],
                                            step=0.01
                                        ),
                                        style="padding: 5px; border: 1px solid #ddd; width: 120px;"
                                    ),
                                    ui.tags.td(
                                        ui.input_numeric(
                                            f"stock_volume_{i}",
                                            "",
                                            value=0,
                                            min=0,
                                            step=0.1
                                        ),
                                        style="padding: 5px; border: 1px solid #ddd; width: 100px;"
                                    ),
                                    style="background-color: white;"
                                )
                                table_rows.append(row)
                        
                        return ui.tags.div(
                            ui.tags.h3("Enter Parameters", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                            ui.tags.div(
                                ui.tags.table(
                                    table_headers,
                                    *table_rows,
                                    style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                ),
                                style="overflow-x: auto; max-width: 100%;"
                            )
                        )
                    else:
                        # Create table headers for step 3
                        table_headers = ui.tags.tr(
                            ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                            ui.tags.th(f"Est. Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th(f"Actual Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th("MGIT Tubes", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                            style="background-color: #f8f9fa;"
                        )
                        
                        # Create table rows for each selected drug
                        table_rows = []
                        for i, drug_name in enumerate(selected):
                            # Get estimated weight from previous calculation
                            est_weight = get_estimated_weight(i)
                            row = ui.tags.tr(
                                ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                ui.tags.td(f"{est_weight:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                ui.tags.td(
                                    ui.input_numeric(
                                        f"actual_weight_{i}",
                                        "",
                                        value=0,
                                        min=0,
                                        step=0.001
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 120px;"
                                ),
                                ui.tags.td(
                                    ui.input_numeric(
                                        f"mgit_tubes_{i}",
                                        "",
                                        value=0,
                                        min=1,
                                        step=1
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 100px;"
                                ),
                                style="background-color: white;"
                            )
                            table_rows.append(row)
                        
                        return ui.tags.div(
                            ui.tags.h3("Enter Actual Weights and MGIT Tubes", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                            ui.tags.div(
                                ui.tags.table(
                                    table_headers,
                                    *table_rows,
                                    style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                ),
                                style="overflow-x: auto; max-width: 100%;"
                            )
                        )
            
            # Results section for step 2
            @render.ui
            def results_section():
                selected = input.drug_selection()
                if not selected:
                    return ui.tags.div()
                    
                if current_step() == 2:
                    # Get input values
                    try:
                        stock_volumes = []
                        purchased_mol_weights = []
                        custom_critical_values = []
                        drug_data = load_drug_data()
                        
                        for i, drug_name in enumerate(selected):
                            
                            # Get original molecular weight
                            org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                            
                            # Get purchased molecular weight
                            purch_molw = input[f"purchased_molw_{i}"]()
                            if purch_molw is None or purch_molw <= 0:
                                return ui.tags.div("Please enter valid purchased molecular weights for all drugs.", style="color: green;")
                            elif purch_molw < org_molw:
                                return ui.tags.div("Purchased molecular weight cannot be smaller than original molecular weight.", style="color: red;")
                            # Use g/mol directly
                            purch_molw_gmol = purch_molw
                            purchased_mol_weights.append(purch_molw_gmol)
                            
                            # Get stock volume
                            stock_vol = input[f"stock_volume_{i}"]()
                            if stock_vol is None or stock_vol <= 0:
                                return ui.tags.div("Please enter valid stock volumes for all drugs.", style="color: green;")

                            # Convert to ml for calculations
                            stock_vol_ml = convert_volume(stock_vol, volume_unit(), "ml")
                            stock_volumes.append(stock_vol_ml)
                            
                            # Get custom critical value
                            custom_crit = input[f"custom_critical_{i}"]()
                            if custom_crit is None or custom_crit <= 0:
                                return ui.tags.div("Please enter valid critical concentrations for all drugs.", style="color: green;")
                            # Use mg/ml directly
                            custom_crit_mgml = custom_crit
                            custom_critical_values.append(custom_crit_mgml)
                        
                        if calculate_clicked():
                            # Calculate results
                            results_data = []
                            estimated_weights = []
                            
                            for i, drug_name in enumerate(selected):
                                drug_row = drug_data[drug_data['Drug'] == drug_name]
                                if not drug_row.empty:
                                    row_data = drug_row.iloc[0]
                                
                                    # Calculate potency
                                    pot = potency(purchased_mol_weights[i], row_data['OrgMolecular_Weight'])
                                
                                    # Calculate estimated drug weight
                                    est_dw = est_drugweight(custom_critical_values[i], stock_volumes[i], pot)
                                    est_dw_user_unit = convert_weight(est_dw, "mg", weight_unit())
                                    estimated_weights.append(est_dw_user_unit)
                                
                                    results_data.append({
                                        'Drug': drug_name,
                                        'Potency': f"{pot:.5f}",
                                        'Est_DrugWeight': est_dw_user_unit
                                    })
                            
                            # Store estimated weights for step 3
                            calculation_results.set({'estimated_weights': estimated_weights})
                        
                            # Create results table
                            if results_data:
                                table_headers = ui.tags.tr(
                                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th("Potency", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                                    ui.tags.th(f"Est. Drug Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 150px;"),
                                    style="background-color: #f8f9fa;"
                                )
                            
                                table_rows = []
                                for result in results_data:
                                    row = ui.tags.tr(
                                        ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                        ui.tags.td(round(float(result['Potency']), 4), style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                        ui.tags.td(round(float(result['Est_DrugWeight']), 4), style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                        style="background-color: white;"
                                    )
                                    table_rows.append(row)

                                return ui.tags.div(
                                    ui.tags.h3("Calculation Results", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                                    ui.tags.div(
                                        ui.tags.table(
                                            table_headers,
                                            *table_rows,
                                            style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                        ),
                                        style="overflow-x: auto; max-width: 100%;"
                                    ),
                                    ui.tags.div("INSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:", style="color: #1e90ff; margin-top: 30px; margin-bottom: 15px; font-weight: bold; font-size: 20px;")
                                )
                        
                    except Exception as e:
                        return ui.tags.div(f"Error in calculation: {str(e)}")
                
                elif current_step() == 3:
                    # Show final results with warnings only after calculation is performed
                    warning_list = warnings()
                    if warning_list:
                        warning_ui = ui.tags.div(
                            ui.tags.h4("⚠️ Warnings Detected", style="color: #e74c3c; margin-bottom: 15px;"),
                            *[ui.tags.p(warning, style="color: #2c3e50; margin-bottom: 10px; padding: 10px; background-color: #fdf2f2; border-left: 4px solid #e74c3c; border-radius: 4px;") for warning in warning_list],
                            style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px;"
                        )
                    else:
                        warning_ui = ui.tags.div()
                    if final_calculation_done():
                        try:
                            final_results = perform_final_calculations()
                            
                            if final_results:
                                
                                table_headers = ui.tags.tr(
                                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                                    ui.tags.th(f"Stock Solution to Aliquot ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 180px;"),
                                    ui.tags.th(f"Diluent to Add ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 150px;"),
                                    style="background-color: #f8f9fa;"
                                )
                                
                                table_rows = []
                                for result in final_results:
                                    row = ui.tags.tr(
                                        ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                        ui.tags.td(result['Diluent'], style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                        ui.tags.td(f"{result['Stock_Vol_Aliquot']:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                        ui.tags.td(f"{result['Diluent_Vol']:.8f}" if result['Diluent_Vol'] < 0.001 else f"{result['Diluent_Vol']:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                        style="background-color: white;"
                                    )
                                    table_rows.append(row)
                                
                                return ui.tags.div(
                                    warning_ui,  # Show warnings at the top
                                    ui.tags.h3("Final Results", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                                    ui.tags.div(
                                        ui.tags.table(
                                            table_headers,
                                            *table_rows,
                                            style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                        ),
                                        style="overflow-x: auto; max-width: 100%;"
                                    ),
                                    ui.tags.div("Final values calculated successfully! Use these volumes to prepare your working solutions.", style="color: #27ae60; margin-top: 30px; margin-bottom: 15px; font-weight: bold; font-size: 16px;")
                                )
                        except Exception as e:
                            return ui.tags.div(f"Error in final calculations: {str(e)}", style="color: red;")
                    else:
                        return ui.tags.div(
                            warning_ui,  # Show warnings if any
                            ui.tags.h3("Enter Final Parameters", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                            ui.tags.p("Please enter the actual weights and number of MGIT tubes for each selected drug, then click 'Calculate Final Results'.", style="color: #7f8c8d; margin-bottom: 20px;")
                        )
                
                return ui.tags.div()
            
            # Function to validate all inputs
            def validate_inputs():
                selected = input.drug_selection()
                if not selected:
                    return False
                
                try:
                    drug_data = load_drug_data()
                    
                    for i, drug_name in enumerate(selected):
                        # Get stock volume
                        stock_vol = input[f"stock_volume_{i}"]()
                        if stock_vol is None or stock_vol <= 0:
                            return False
                        
                        # Get original molecular weight
                        org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                        
                        # Get purchased molecular weight
                        purch_molw = input[f"purchased_molw_{i}"]()
                        if purch_molw is None or purch_molw <= 0:
                            return False
                        # Convert to g/mol for comparison
                        purch_molw_gmol = convert_molecular_weight(purch_molw, molecular_weight_unit(), "g/mol")
                        if purch_molw_gmol < org_molw:
                            return False
                        
                        # Get custom critical value
                        custom_crit = input[f"custom_critical_{i}"]()
                        if custom_crit is None or custom_crit <= 0:
                            return False
                    
                    return True
                except:
                    return False

            def validate_step3_inputs():
                """Validate that all actual weights and MGIT tubes have been entered."""
                selected = input.drug_selection()
                if not selected:
                    return False
                
                for i in range(len(selected)):
                    actual_weight = input[f"actual_weight_{i}"]()
                    mgit_tubes = input[f"mgit_tubes_{i}"]()
                    if actual_weight is None or actual_weight <= 0 or mgit_tubes is None or mgit_tubes <= 0:
                        return False
                
                return True
            def validate_step3_inputs():
                """Validate that all actual weights and MGIT tubes have been entered."""
                selected = input.drug_selection()
                if not selected:
                    return False
                
                for i in range(len(selected)):
                    actual_weight = input[f"actual_weight_{i}"]()
                    mgit_tubes = input[f"mgit_tubes_{i}"]()
                    if actual_weight is None or actual_weight <= 0 or mgit_tubes is None or mgit_tubes <= 0:
                        return False
                
                return True

            # Action buttons
            @render.ui
            def action_buttons():
                if current_step() == 1:
                    return ui.tags.div(
                        ui.input_action_button("next_btn", "Next", class_="btn-primary", style="background-color: #3498db; border-color: #3498db; margin-right: 10px;"),
                        ui.input_action_button("reset_btn", "Reset", class_="btn-secondary"),
                        style="text-align: center; margin-top: 30px;"
                    )
                elif current_step() == 2:
                    # Only show calculate button if all inputs are valid
                    if validate_inputs():
                        if calculate_clicked():
                            # Show Next button after calculation
                            return ui.tags.div(
                                ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                                ui.input_action_button("next_btn", "Next", class_="btn-primary", style="background-color: #3498db; border-color: #3498db;"),
                                style="text-align: center; margin-top: 30px;"
                            )
                        else:
                            # Show Calculate button initially
                            return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                                ui.input_action_button("calculate_btn", "Calculate", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                            )
                    else:
                        # Show only back button if validation fails
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary"),
                            style="text-align: center; margin-top: 30px;"
                        )
                elif current_step() == 3:
                    # Validate step 3 inputs
                    if final_calculation_done():
                        # After results are shown, replace with New Calculation
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("new_calc_btn", "New Calculation", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                        )
                    elif validate_step3_inputs():
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("calculate_final_btn", "Calculate Final Results", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                        )
                    else:
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary"),
                            style="text-align: center; margin-top: 30px;"
                        )
                else:
                    return ui.tags.div()

    with ui.nav_panel("B"):
        
        ui.tags.h2("Account", style="color: #2c3e50; margin-bottom: 20px;")

        @render.ui
        def account_status():
            user = current_user()
            message = auth_message()
            status_block = []
            if user:
                status_block.append(ui.tags.p(f"Signed in as: {user.get('username')}", style="color: #27ae60;"))
                status_block.append(ui.input_action_button("logout_btn", "Logout", class_="btn-secondary"))
            else:
                status_block.append(ui.tags.p("Not signed in", style="color: #7f8c8d;"))
            if message:
                status_block.append(ui.tags.p(message, style="color: #2c3e50; margin-top: 10px;"))
            return ui.tags.div(*status_block, style="margin-bottom: 20px;")

        # Users table
        @render.ui
        def users_table():
            try:
                with db_manager.get_connection() as conn:
                    users_cur = conn.execute("SELECT user_id, username FROM users ORDER BY user_id ASC")
                    users_rows = users_cur.fetchall()
                    header = ui.tags.tr(
                        ui.tags.th("User ID", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("Username", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("# Sessions", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("Recent Sessions (3)", style="padding: 6px; border: 1px solid #ddd;")
                    )
                    body_rows = []
                    for user_id, username in users_rows:
                        sess_cur = conn.execute(
                            "SELECT session_name FROM session WHERE user_id = ? ORDER BY session_date DESC LIMIT 3",
                            (user_id,)
                        )
                        recent_names = [row[0] for row in sess_cur.fetchall()]
                        count_cur = conn.execute(
                            "SELECT COUNT(*) FROM session WHERE user_id = ?",
                            (user_id,)
                        )
                        total_count = count_cur.fetchone()[0]
                        body_rows.append(
                            ui.tags.tr(
                                ui.tags.td(str(user_id), style="padding: 6px; border: 1px solid #ddd;"),
                                ui.tags.td(username, style="padding: 6px; border: 1px solid #ddd;"),
                                ui.tags.td(str(total_count), style="padding: 6px; border: 1px solid #ddd;"),
                                ui.tags.td(
                                    ", ".join(recent_names) if recent_names else "-",
                                    style="padding: 6px; border: 1px solid #ddd;"
                                )
                            )
                        )
                return ui.tags.div(
                    ui.tags.h3("Registered Users", style="color: #2c3e50; margin-bottom: 10px;"),
                    ui.tags.table(header, *body_rows, style="border-collapse: collapse; margin-bottom: 20px;")
                )
            except Exception:
                return ui.tags.div(ui.tags.p("Unable to load users."))

        # Toggle buttons for forms
        ui.input_action_button("show_register", "Sign up", class_="btn-primary", style="margin-right: 10px;")
        ui.input_action_button("show_login", "Login", class_="btn-success")

        # Conditional form render and session creation (visible only when logged in)
        @render.ui
        def auth_forms():
            view = auth_view()
            if view == "register":
                return ui.tags.div(
                    ui.tags.h3("Register", style="color: #2c3e50; margin-top: 15px; margin-bottom: 10px;"),
                    ui.input_text("reg_username", "Username", placeholder="Enter a username"),
                    ui.input_password("reg_password", "Password"),
                    ui.input_password("reg_password2", "Confirm Password"),
                    ui.input_action_button("register_btn", "Create Account", class_="btn-primary", style="margin-top: 10px;")
                )
            if view == "login":
                return ui.tags.div(
                    ui.tags.h3("Login", style="color: #2c3e50; margin-top: 15px; margin-bottom: 10px;"),
                    ui.input_text("login_username", "Username"),
                    ui.input_password("login_password", "Password"),
                    ui.input_action_button("login_btn", "Sign In", class_="btn-success", style="margin-top: 10px;")
                )
            # Show start session UI when a user is signed in
            user = current_user()
            if user:
                cs = current_session()
                return ui.tags.div(
                    ui.tags.h3("Start a Session", style="color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"),
                    ui.input_text("session_name", "Session name", placeholder="e.g. 2025-09-29 prep"),
                    ui.input_action_button("start_session_btn", "Start session", class_="btn-primary", style="margin-top: 10px; margin-right: 10px;"),
                    ui.tags.p(
                        f"Current session: {cs.get('session_name')}" if cs else "No active session",
                        style="color: #7f8c8d; margin-top: 10px;"
                    )
                )
            return ui.tags.div()  # none

    with ui.nav_panel("C"):
        pass



# Reactive functions
@reactive.effect
@reactive.event(input.next_btn)
def next_step():
    selected = input.drug_selection()
    if selected and current_step() == 1:
        current_step.set(2)
        calculate_clicked.set(False)
    elif current_step() == 2 and calculate_clicked():
        current_step.set(3)
        calculate_clicked.set(False)
        final_calculation_done.set(False)  # Reset final calculation flag

@reactive.effect
@reactive.event(input.back_btn)
def back_step():
    if current_step() == 2:
        current_step.set(1)
        calculate_clicked.set(False)
    elif current_step() == 3:
        current_step.set(2)
        final_calculation_done.set(False)  # Reset final calculation flag

@reactive.effect
@reactive.event(input.reset_btn)
def reset_selection():
    current_step.set(1)
    calculate_clicked.set(False)
    final_calculation_done.set(False)  # Reset final calculation flag
    calculation_results.set({})
    ui.update_selectize("drug_selection", selected=[])

@reactive.effect
@reactive.event(input.calculate_btn)
def calculate_results():
    if current_step() == 2:
        calculate_clicked.set(True)
        # Persist input state to session if active
        try:
            cs = current_session()
            user = current_user()
            if cs and user:
                selected = input.drug_selection() or []
                preparation = {
                    'selected_drugs': selected,
                    'volume_unit': volume_unit(),
                    'weight_unit': weight_unit(),
                    'step': 2,
                    'inputs': {}
                }
                for i, drug_name in enumerate(selected):
                    preparation['inputs'][drug_name] = {
                        'custom_critical': input.get(f"custom_critical_{i}")(),
                        'purchased_molw': input.get(f"purchased_molw_{i}")(),
                        'stock_volume': input.get(f"stock_volume_{i}")()
                    }
                db_manager.update_session_data(cs['session_id'], preparation)
        except Exception:
            pass

@reactive.effect
@reactive.event(input.calculate_final_btn)
def calculate_final_results():
    if current_step() == 3:
        # Mark that final calculation has been performed
        final_calculation_done.set(True)
        # Persist final inputs/results to session if active
        try:
            cs = current_session()
            user = current_user()
            if cs and user:
                selected = input.drug_selection() or []
                preparation = {
                    'selected_drugs': selected,
                    'volume_unit': volume_unit(),
                    'weight_unit': weight_unit(),
                    'step': 3,
                    'inputs': {},
                    'results': calculation_results.get()
                }
                for i, drug_name in enumerate(selected):
                    preparation['inputs'][drug_name] = {
                        'actual_weight': input.get(f"actual_weight_{i}")(),
                        'mgit_tubes': input.get(f"mgit_tubes_{i}")()
                    }
                db_manager.update_session_data(cs['session_id'], preparation)
        except Exception:
            pass

@reactive.effect
@reactive.event(input.new_calc_btn)
def new_calculation():
    if current_step() == 3 and final_calculation_done():
        # Reset all relevant state and return to step 1
        current_step.set(1)
        calculate_clicked.set(False)
        final_calculation_done.set(False)
        calculation_results.set({})
        warnings.set([])
        ui.update_selectize("drug_selection", selected=[])

# Unit selection reactive effects
@reactive.effect
@reactive.event(input.vol_unit)
def update_volume_unit():
    volume_unit.set(input.vol_unit())

# Removed mol_weight_unit and conc_unit reactive handlers (fixed units)

@reactive.effect
@reactive.event(input.weight_unit)
def update_weight_unit():
    weight_unit.set(input.weight_unit())

# Auth handlers
@reactive.effect
@reactive.event(input.show_register)
def toggle_register():
    auth_view.set("register")
    auth_message.set("")

@reactive.effect
@reactive.event(input.show_login)
def toggle_login():
    auth_view.set("login")
    auth_message.set("")

@reactive.effect
@reactive.event(input.register_btn)
def handle_register():
    username = (input.reg_username() or "").strip()
    pw1 = input.reg_password() or ""
    pw2 = input.reg_password2() or ""
    if not username or not pw1 or not pw2:
        auth_message.set("Please fill in all registration fields.")
        return
    if pw1 != pw2:
        auth_message.set("Passwords do not match.")
        return
    user_id = register_user(username, pw1)
    if user_id:
        # Auto-login after successful registration
        user = login_user(username, pw1)
        current_user.set(user)
        auth_message.set("Account created and signed in.")
        auth_view.set("none")
    else:
        auth_message.set("Username already exists or registration failed.")

@reactive.effect
@reactive.event(input.login_btn)
def handle_login():
    username = (input.login_username() or "").strip()
    password = input.login_password() or ""
    if not username or not password:
        auth_message.set("Please provide username and password.")
        return
    user = login_user(username, password)
    if user:
        current_user.set(user)
        auth_message.set("Signed in successfully.")
        auth_view.set("none")
    else:
        current_user.set(None)
        auth_message.set("Invalid credentials.")

@reactive.effect
@reactive.event(input.logout_btn)
def handle_logout():
    current_user.set(None)
    auth_message.set("Signed out.")
    auth_view.set("none")

# Start session -> create or get session and redirect to calculator (Tab A)
@reactive.effect
@reactive.event(input.start_session_btn)
def start_session():
    user = current_user()
    name = (input.session_name() or "").strip()
    if not user:
        auth_message.set("Please sign in first.")
        return
    if not name:
        auth_message.set("Please provide a session name.")
        return
    try:
        session_id = db_manager.get_or_create_session(user['user_id'], name)
        if session_id:
            current_session.set({'session_id': session_id, 'session_name': name})
            auth_message.set(f"Session '{name}' started.")
            # Switch to calculator tab A
            ui.update_navs("tab", selected="A")
        else:
            auth_message.set("Failed to start session.")
    except Exception:
        auth_message.set("Error starting session.")

# Warning-related reactive effects
@reactive.effect
@reactive.event(input.show_warnings)
def show_warning_modal():
    # This is now unused but keeping for compatibility
    pass

@reactive.effect
@reactive.event(input.next_btn, input.back_btn, input.reset_btn)
def clear_warnings_on_navigation():
    # Clear warnings when navigating between steps or resetting
    warnings.set([])

@reactive.effect
@reactive.event(input.calculate_final_btn)
def clear_warnings_on_recalculation():
    # Clear warnings when recalculating final results
    warnings.set([])

# Footer
ui.tags.div(
    ui.tags.hr(),
    ui.tags.div(
        style="margin-top: 40px;"
    )
)