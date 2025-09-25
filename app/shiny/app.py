from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
from lib.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock, conc_mgit, vol_workingsol, vol_ss_to_ws, vol_final_dil

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

# Add top whitespace
ui.tags.div(style="margin-top: 50px;")

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
                    ui.tags.h3("Selected Drugs", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
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
                    ui.tags.th(f"Stock Vol. ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                    ui.tags.th("Purch. Mol. Wt. (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
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
                            ui.tags.td(
                                ui.input_numeric(
                                    f"purchased_molw_{i}",
                                    "",
                                    value=row_data['OrgMolecular_Weight'],
                                    min=row_data['OrgMolecular_Weight'],
                                    step=0.01
                                ),
                                style="padding: 5px; border: 1px solid #ddd; width: 120px;"
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
                                value=round(est_weight, 4),
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
                    # Get stock volume
                    stock_vol = input[f"stock_volume_{i}"]()
                    if stock_vol is None or stock_vol <= 0:
                        return ui.tags.div("Please enter valid stock volumes for all drugs.", style="color: red;")
                    # Convert to ml for calculations
                    stock_vol_ml = convert_volume(stock_vol, volume_unit(), "ml")
                    stock_volumes.append(stock_vol_ml)
                    
                    # Get original molecular weight
                    org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                    
                    # Get purchased molecular weight
                    purch_molw = input[f"purchased_molw_{i}"]()
                    if purch_molw is None or purch_molw <= 0:
                        return ui.tags.div("Please enter valid purchased molecular weights for all drugs.", style="color: red;")
                    # Use g/mol directly
                    purch_molw_gmol = purch_molw
                    if purch_molw_gmol < org_molw:
                        return ui.tags.div("Please enter valid purchased molecular weights for all drugs.", style="color: red;")
                    purchased_mol_weights.append(purch_molw_gmol)
                    
                    # Get custom critical value
                    custom_crit = input[f"custom_critical_{i}"]()
                    if custom_crit is None or custom_crit <= 0:
                        return ui.tags.div("Please enter valid critical concentrations for all drugs.", style="color: red;")
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

@reactive.effect
@reactive.event(input.calculate_final_btn)
def calculate_final_results():
    if current_step() == 3:
        # Mark that final calculation has been performed
        final_calculation_done.set(True)

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