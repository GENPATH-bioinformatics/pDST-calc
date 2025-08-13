from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
from lib.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight

# Unit conversion functions
def convert_molecular_weight(value, from_unit, to_unit):
    """Convert molecular weight between different units."""
    if from_unit == to_unit:
        return value
    
    # Convert to g/mol as base unit
    if from_unit == "g/mol":
        base_value = value
    elif from_unit == "kg/mol":
        base_value = value * 1000
    elif from_unit == "mg/mol":
        base_value = value / 1000
    else:
        base_value = value
    
    # Convert from base unit to target unit
    if to_unit == "g/mol":
        return base_value
    elif to_unit == "kg/mol":
        return base_value / 1000
    elif to_unit == "mg/mol":
        return base_value * 1000
    else:
        return base_value

def convert_volume(value, from_unit, to_unit):
    """Convert volume between different units."""
    if from_unit == to_unit:
        return value
    
    # Convert to ml as base unit
    if from_unit == "ml":
        base_value = value
    elif from_unit == "L":
        base_value = value * 1000
    elif from_unit == "μl":
        base_value = value / 1000
    else:
        base_value = value
    
    # Convert from base unit to target unit
    if to_unit == "ml":
        return base_value
    elif to_unit == "L":
        return base_value / 1000
    elif to_unit == "μl":
        return base_value * 1000
    else:
        return base_value

def convert_concentration(value, from_unit, to_unit):
    """Convert concentration between different units."""
    if from_unit == to_unit:
        return value
    
    # Convert to mg/ml as base unit
    if from_unit == "mg/ml":
        base_value = value
    elif from_unit == "g/L":
        base_value = value
    elif from_unit == "μg/ml":
        base_value = value / 1000
    elif from_unit == "ng/ml":
        base_value = value / 1000000
    else:
        base_value = value
    
    # Convert from base unit to target unit
    if to_unit == "mg/ml":
        return base_value
    elif to_unit == "g/L":
        return base_value
    elif to_unit == "μg/ml":
        return base_value * 1000
    elif to_unit == "ng/ml":
        return base_value * 1000000
    else:
        return base_value

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

# Read the first column from the CSV file
drug_options = load_drug_data()
drug_selection = drug_options.iloc[:, 0].dropna().tolist()

# Track current step
current_step = reactive.Value(1)
# Track if calculate button has been clicked
calculate_clicked = reactive.Value(False)

# Unit selection reactive values
molecular_weight_unit = reactive.Value("g/mol")
volume_unit = reactive.Value("ml")
concentration_unit = reactive.Value("mg/ml")
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
        steps = [
            "Calculator"
        ]
        
        for i, step in enumerate(steps):
            step_style = "color: #3498db; font-weight: bold;" if i == 0 else "color: #7f8c8d;"
            ui.tags.div(
                ui.tags.p(step, style=step_style),
                style="margin-bottom: 8px;"
            )
        
        ui.tags.div(style="margin-top: 30px;")
        
        # Unit Selection Section
        ui.tags.div(style="margin-top: 30px;")
        ui.tags.h4("Unit Preferences", style="color: #2c3e50; margin-bottom: 15px;")
        
        ui.tags.p("Select your preferred units:", style="color: #7f8c8d; font-size: 12px; margin-bottom: 10px;")
        
        ui.input_select(
            "mol_weight_unit",
            "Molecular Weight:",
            choices=["g/mol", "kg/mol", "mg/mol"],
            selected="g/mol"
        )
        
        ui.input_select(
            "vol_unit",
            "Volume:",
            choices=["ml", "L", "μl"],
            selected="ml"
        )
        
        ui.input_select(
            "conc_unit",
            "Concentration:",
            choices=["mg/ml", "g/L", "μg/ml", "ng/ml"],
            selected="mg/ml"
        )
        
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
                    ui.tags.th(f"Mol. Weight ({molecular_weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                    ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                    ui.tags.th(f"Crit. Conc. ({concentration_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
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
                            ui.tags.td(f"{convert_molecular_weight(row_data['OrgMolecular_Weight'], 'g/mol', molecular_weight_unit()):.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                            ui.tags.td(row_data['Diluent'], style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                            ui.tags.td(
                                ui.input_numeric(
                                    f"custom_critical_{i}",
                                    "",
                                    value=convert_concentration(row_data['Critical_Concentration'], 'mg/ml', concentration_unit()),
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
            else:
                # Create table headers for step 2
                table_headers = ui.tags.tr(
                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                    ui.tags.th(f"Stock Vol. ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                    ui.tags.th(f"Purch. Mol. Wt. ({molecular_weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
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
                                    value=convert_molecular_weight(row_data['OrgMolecular_Weight'], 'g/mol', molecular_weight_unit()),
                                    min=convert_molecular_weight(row_data['OrgMolecular_Weight'], 'g/mol', molecular_weight_unit()),
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
    
    # Results section for step 2
    @render.ui
    def results_section():
        if current_step() == 2:
            selected = input.drug_selection()
            if not selected:
                return ui.tags.div()
            
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
                    # Convert to g/mol for calculations
                    purch_molw_gmol = convert_molecular_weight(purch_molw, molecular_weight_unit(), "g/mol")
                    if purch_molw_gmol < org_molw:
                        return ui.tags.div("Please enter valid purchased molecular weights for all drugs.", style="color: red;")
                    purchased_mol_weights.append(purch_molw_gmol)
                    
                    # Get custom critical value
                    custom_crit = input[f"custom_critical_{i}"]()
                    if custom_crit is None or custom_crit <= 0:
                        return ui.tags.div("Please enter valid critical concentrations for all drugs.", style="color: red;")
                    # Convert to mg/ml for calculations
                    custom_crit_mgml = convert_concentration(custom_crit, concentration_unit(), "mg/ml")
                    custom_critical_values.append(custom_crit_mgml)
                
                if calculate_clicked():
                    # Calculate results
                    results_data = []
                    for i, drug_name in enumerate(selected):
                        drug_row = drug_data[drug_data['Drug'] == drug_name]
                        if not drug_row.empty:
                            row_data = drug_row.iloc[0]
                        
                            # Calculate potency
                            pot = potency(purchased_mol_weights[i], row_data['OrgMolecular_Weight'])
                        
                            # Calculate estimated drug weight
                            est_dw = est_drugweight(custom_critical_values[i], stock_volumes[i], pot)
                        
                            results_data.append({
                                'Drug': drug_name,
                                'Potency': f"{pot:.5f}",
                                'Est_DrugWeight': convert_weight(est_dw, "mg", weight_unit())
                            })
                
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

    # Action buttons
    @render.ui
    def action_buttons():
        if current_step() == 1:
            return ui.tags.div(
                ui.input_action_button("next_btn", "Next", class_="btn-primary", style="background-color: #3498db; border-color: #3498db; margin-right: 10px;"),
                ui.input_action_button("reset_btn", "Reset", class_="btn-secondary"),
                style="text-align: center; margin-top: 30px;"
            )
        else:
            # Only show calculate button if all inputs are valid
            if validate_inputs():
                # Check if calculate button has been clicked to show different button text
                button_text = "Enter Actual drug weights" if calculate_clicked() else "Calculate drug weights"
                return ui.tags.div(
                    ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                    ui.input_action_button("calculate_btn", button_text, class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                    style="text-align: center; margin-top: 30px;"
                )
            else:
                # Show only back button if validation fails
                return ui.tags.div(
                    ui.input_action_button("back_btn", "Back", class_="btn-secondary"),
                    style="text-align: center; margin-top: 30px;"
                )

# Reactive functions
@reactive.effect
@reactive.event(input.next_btn)
def next_step():
    selected = input.drug_selection()
    if selected and current_step() == 1:
        current_step.set(2)
        calculate_clicked.set(False)

@reactive.effect
@reactive.event(input.back_btn)
def back_step():
    if current_step() == 2:
        current_step.set(1)
        calculate_clicked.set(False)

@reactive.effect
@reactive.event(input.reset_btn)
def reset_selection():
    current_step.set(1)
    calculate_clicked.set(False)
    ui.update_selectize("drug_selection", selected=[])

@reactive.effect
@reactive.event(input.calculate_btn)
def calculate_results():
    calculate_clicked.set(True)

# Unit selection reactive effects
@reactive.effect
@reactive.event(input.mol_weight_unit)
def update_mol_weight_unit():
    molecular_weight_unit.set(input.mol_weight_unit())

@reactive.effect
@reactive.event(input.vol_unit)
def update_volume_unit():
    volume_unit.set(input.vol_unit())

@reactive.effect
@reactive.event(input.conc_unit)
def update_concentration_unit():
    concentration_unit.set(input.conc_unit())

@reactive.effect
@reactive.event(input.weight_unit)
def update_weight_unit():
    weight_unit.set(input.weight_unit())

# Footer
ui.tags.div(
    ui.tags.hr(),
    ui.tags.div(
        style="margin-top: 40px;"
    )
)