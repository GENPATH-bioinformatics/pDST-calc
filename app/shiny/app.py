from shiny import reactive
from shiny.express import input, render, ui
import pandas as pd
from lib.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight

# Read the first column from the CSV file
drug_options = load_drug_data()
drug_selection = drug_options.iloc[:, 0].dropna().tolist()

# Track current step
current_step = reactive.Value(1)
# Track if calculate button has been clicked
calculate_clicked = reactive.Value(False)

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
        ui.tags.h4("References", style="color: #2c3e50; margin-bottom: 10px;")
        ui.tags.p("The pDST Calculator is created for drug susceptibility testing calculations.", style="color: #7f8c8d; font-size: 12px;")
    
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
                    ui.tags.th("Mol. Weight", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                    ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                    ui.tags.th("Crit. C", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
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
            else:
                # Create table headers for step 2
                table_headers = ui.tags.tr(
                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                    ui.tags.th("Stock Vol.", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                    ui.tags.th("Purch. Mol. Wt.", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
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
                                    min=0,
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
                        return ui.tags.div("Please enter valid stock volumes for all drugs.")
                    stock_volumes.append(stock_vol)
                    
                    # Get original molecular weight
                    org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                    
                    # Get purchased molecular weight
                    purch_molw = input[f"purchased_molw_{i}"]()
                    if purch_molw is None or purch_molw <= 0 or purch_molw < org_molw:
                        return ui.tags.div("Please enter valid purchased molecular weights for all drugs.")
                    purchased_mol_weights.append(purch_molw)
                    
                    # Get custom critical value
                    custom_crit = input[f"custom_critical_{i}"]()
                    if custom_crit is None or custom_crit <= 0:
                        return ui.tags.div("Please enter valid critical concentrations for all drugs.")
                    custom_critical_values.append(custom_crit)
                
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
                                'Est_DrugWeight (mg)': f"{est_dw:.5f}"
                            })
                
                    # Create results table
                    if results_data:
                        table_headers = ui.tags.tr(
                            ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                            ui.tags.th("Potency", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                            ui.tags.th("Est. Drug Weight (mg)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 150px;"),
                            style="background-color: #f8f9fa;"
                        )
                    
                        table_rows = []
                        for result in results_data:
                            row = ui.tags.tr(
                                ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                ui.tags.td(result['Potency'], style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                ui.tags.td(result['Est_DrugWeight (mg)'], style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
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
                            ui.tags.div("INSTRUCTION: Please go weigh out the following estimated drug weights for each drug, then return to input the actual weighed values:", style="color: #1e90ff; margin-top: 30px; margin-bottom: 15px; font-weight: bold;")
                        )
                
            except Exception as e:
                return ui.tags.div(f"Error in calculation: {str(e)}")
        
        return ui.tags.div()
    
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
            # Check if calculate button has been clicked to show different button text
            button_text = "Enter Actual drug weights" if calculate_clicked() else "Calculate drug weights"
            return ui.tags.div(
                ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                ui.input_action_button("calculate_btn", button_text, class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
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

# Footer
ui.tags.div(
    ui.tags.hr(),
    ui.tags.div(
        style="margin-top: 40px;"
    )
)