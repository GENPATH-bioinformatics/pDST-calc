from datetime import datetime, timedelta
from math import floor
from shiny import reactive
from shiny.express import input, render, ui
from shiny import ui as shiny_ui
import pandas as pd
import sys
import os
import io

# Add the project root to Python path so we can import from app.api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.api.drug_database import load_drug_data
from lib.dst_calc import (
    potency, est_drugweight, vol_diluent, conc_stock, conc_ws, vol_workingsol, 
    vol_ss_to_ws, calc_volume_difference, calc_adjusted_volume, calc_stock_factor, 
    calc_volume_divided_by_factor, calc_concentration_times_factor,
    calc_intermediate_factor, calc_intermediate_volume
)
from lib.supp_calc import ml_to_ul, ul_to_ml
from app.api.auth import register_user, login_user
from app.api.database import db_manager

# Import PDF generation functions from the separate module
from app.shiny.generate_pdf import generate_step2_pdf as generate_step2_pdf_module, generate_step4_pdf as generate_step4_pdf_backend

# Helper functions for common operations
def get_drug_inputs(drug_index, fallback_session_data=None):
    """Get all inputs for a specific drug with session fallback."""
    try:
        inputs = {
            'custom_crit': input[f"custom_critical_{drug_index}"](),
            'purch_molw': input[f"purchased_molw_{drug_index}"](),
            'stock_vol': input[f"stock_volume_{drug_index}"](),
            'actual_weight': input[f"actual_weight_{drug_index}"](),
            'mgit_tubes': input[f"mgit_tubes_{drug_index}"]()
        }
        
        # Apply session fallbacks for None values
        if fallback_session_data:
            for key, session_key in [
                ('custom_crit', 'Crit_Conc(mg/ml)'),
                ('purch_molw', 'PurMol_W(g/mol)'),
                ('stock_vol', 'St_Vol(ml)'),
                ('actual_weight', 'Act_DrugW(mg)'),
                ('mgit_tubes', 'Total Mgit tubes')
            ]:
                if inputs[key] is None and session_key in fallback_session_data:
                    inputs[key] = fallback_session_data[session_key]
        
        return inputs
    except Exception as e:
        print(f"Error getting drug inputs for index {drug_index}: {e}")
        return None

def build_step2_data_structure():
    """Build standardized Step 2 data structure for PDF generation."""
    return {
        'CriticalConc': Step2_CriticalConc,
        'Purch': Step2_Purch,
        'MgitTubes': Step2_MgitTubes,
        'Potencies': Step2_Potencies,
        'ConcWS': Step2_ConcWS,
        'VolWS': Step2_VolWS,
        'CalEstWeights': Step2_CalEstWeights,
        'num_aliquots': Step2_num_aliquots,
        'mlperAliquot': Step2_mlperAliquot,
        'TotalStockVolumes': Step2_TotalStockVolumes,
        'StocktoWS': Step2_StocktoWS,
        'DiltoWS': Step2_DiltoWS,
        'Factors': Step2_Factors,
        'EstWeights': Step2_EstWeights,
        'PracWeights': Step2_PracWeights,
        'PracVol': Step2_PracVol
    }

# UI reactive prefs
make_stock_pref = reactive.Value(False)
potency_method_pref = reactive.Value("mol_weight")

# Unit constants (base units)
def weight_unit():
    return "mg"
def volume_unit():
    return "ml"

# Global variables to store calculation results
calculation_results = reactive.Value({})
Step2_CalEstWeights = [None] * 21
Step2_EstWeights = [None] * 21
Step2_TotalStockVolumes = [None] * 21
Step2_ConcWS = [None] * 21
Step2_VolWS = [None] * 21
Step2_Potencies = [None] * 21
Step2_MgitTubes = [None] * 21
Step2_mlperAliquot = [None] * 21
Step2_num_aliquots = [None] * 21
Step3_ActDrugWeights = [None] * 21
Step2_CriticalConc = [None] * 21
Step2_StocktoWS = [None] * 21
Step2_DiltoWS = [None] * 21
Step2_Factors = [None] * 21
Step2_PracWeights = [None] * 21
Step2_PracVol = [None] * 21
Step2_Purch = [None] * 21

# Variables for session results view
show_results_view = reactive.Value(False)
session_data = reactive.Value({})
session_inputs = reactive.Value({})

# Flag to prevent multiple calculations
weights_calculated = reactive.Value(False)

# Reactive effect to calculate weights for restored sessions
@reactive.effect
def calculate_weights_for_restored_session():
    if current_step() == 3:
        cs = current_session()
        if cs and not weights_calculated.get():
            print("Reactive effect: Calculating estimated weights for restored session")
            try:
                # Get session data
                with db_manager.get_connection() as conn:
                    cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                    row = cur.fetchone()
                    if row and row[0]:
                        import json
                        preparation = json.loads(row[0])
                        inputs = preparation.get('inputs', {})
                        selected = preparation.get('selected_drugs', [])
                        
                        # Calculate estimated weights from session data
                        estimated_weights = []
                        drug_data = load_drug_data()
                        
                        for i, drug_name in enumerate(selected):
                            drug_inputs = inputs.get(str(i), {})
                            if drug_inputs:
                                # Get values from session
                                custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', 1)
                                stock_vol = drug_inputs.get('St_Vol(ml)', 20)
                                purch_molw = drug_inputs.get('PurMol_W(g/mol)', 558)
                                
                                # Get drug data
                                drug_row = drug_data[drug_data['Drug'] == drug_name]
                                if not drug_row.empty:
                                    org_molw = drug_row.iloc[0]['OrgMolecular_Weight']
                                    
                                    # Calculate potency
                                    # [1] potency calculation from dst-calc.py
                                    pot = potency(purch_molw, org_molw)
                                    
                                    # Calculate estimated drug weight
                                    # [2] est_drugweight calculation from dst-calc.py
                                    est_dw = est_drugweight(custom_crit, stock_vol, pot)
                                    
                                    est_dw_user_unit = est_dw
                                    estimated_weights.append(est_dw_user_unit)
                                else:
                                    estimated_weights.append(0)
                            else:
                                estimated_weights.append(0)
                        
                        # Store calculated weights
                        calculation_results.set({'estimated_weights': estimated_weights})
                        weights_calculated.set(True)
                        print(f"Reactive effect: Calculated estimated weights: {estimated_weights}")
            except Exception as e:
                print(f"Reactive effect: Error calculating estimated weights: {e}")

# Variables for session results view
show_results_view = reactive.Value(False)
session_data = reactive.Value({})
session_inputs = reactive.Value({})

# Flag to prevent multiple calculations
weights_calculated = reactive.Value(False)

# Reactive effect to calculate weights for restored sessions
@reactive.effect
def calculate_weights_for_restored_session():
    if current_step() == 3:
        cs = current_session()
        if cs and not weights_calculated.get():
            print("Reactive effect: Calculating estimated weights for restored session")
            try:
                # Get session data
                with db_manager.get_connection() as conn:
                    cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                    row = cur.fetchone()
                    if row and row[0]:
                        import json
                        preparation = json.loads(row[0])
                        inputs = preparation.get('inputs', {})
                        selected = preparation.get('selected_drugs', [])
                        
                        # Calculate estimated weights from session data
                        estimated_weights = []
                        drug_data = load_drug_data()
                        
                        for i, drug_name in enumerate(selected):
                            drug_inputs = inputs.get(str(i), {})
                            if drug_inputs:
                                # Get values from session
                                custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', 1)
                                stock_vol = drug_inputs.get('St_Vol(ml)', 20)
                                purch_molw = drug_inputs.get('PurMol_W(g/mol)', 558)
                                
                                # Get drug data
                                drug_row = drug_data[drug_data['Drug'] == drug_name]
                                if not drug_row.empty:
                                    org_molw = drug_row.iloc[0]['OrgMolecular_Weight']
                                    
                                    # Calculate potency
                                    # [1] potency calculation from dst-calc.py
                                    pot = potency(purch_molw, org_molw)
                                    
                                    # Calculate estimated drug weight
                                    # [2] est_drugweight calculation from dst-calc.py
                                    est_dw = est_drugweight(custom_crit, stock_vol, pot)
                                    
                                    est_dw_user_unit = est_dw
                                    estimated_weights.append(est_dw_user_unit)
                                else:
                                    estimated_weights.append(0)
                            else:
                                estimated_weights.append(0)
                        
                        # Store calculated weights
                        calculation_results.set({'estimated_weights': estimated_weights})
                        weights_calculated.set(True)
                        print(f"Reactive effect: Calculated estimated weights: {estimated_weights}")
            except Exception as e:
                print(f"Reactive effect: Error calculating estimated weights: {e}")

def get_estimated_weight(drug_index):
    """Get the estimated weight for a drug from previous calculations."""
    results = calculation_results.get()
    if results and 'estimated_weights' in results:
        estimated_weights = results['estimated_weights']
        if isinstance(estimated_weights, list) and drug_index < len(estimated_weights):
            return estimated_weights[drug_index]
    return 0

def build_step4_data_tables(final_results, make_stock):
    """Build HTML tables for Step 4 data that match the PDF tables."""
    drug_data = load_drug_data()
    
    tables = {}
    
    # Table 1: Stock Solution Calculations
    if make_stock:
        table1_data = []
        for result in final_results:
            drug_name = result.get('Drug', '')
            drug_row = drug_data[drug_data['Drug'] == drug_name]
            diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
            
            table1_data.append({
                'Drug': drug_name,
                'Diluent': diluent,
                'Drug_Weight': f"{result.get('Act_Weight', 0):.2f}",
                'Total_Stock_Vol': f"{result.get('Total_Stock_Vol', 0):.2f}",
                'Stock_Conc': f"{result.get('Stock_Conc', 0):.2f}",
                'Dilution_Factor': f"{result.get('Stock_Factor', 0):.1f}"
            })
        tables['stock_solution'] = table1_data
    
    # Table 2: Intermediate Solutions
    intermediate_data = []
    for result in final_results:
        if result.get('Intermediate') == True:
            drug_name = result.get('Drug', '')
            drug_row = drug_data[drug_data['Drug'] == drug_name]
            diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
            
            intermediate_data.append({
                'Drug': drug_name,
                'Diluent': diluent,
                'Stock_to_Add': f"{result.get('Stock_to_Inter', 0):.2f}",
                'Diluent_to_Add': f"{result.get('Dil_to_Inter', 0):.2f}",
                'Intermediate_Vol': f"{result.get('Dil_to_Inter', 0):.2f}",
                'Intermediate_Conc': f"{result.get('Inter_Conc', 0):.2f}",
                'Dilution_Factor': f"{result.get('Inter_Factor', 0):.1f}"
            })
    if intermediate_data:
        tables['intermediate_solution'] = intermediate_data
    
    # Table 3: Working Solution from Intermediate
    ws_intermediate_data = []
    for result in final_results:
        if result.get('Intermediate') == True:
            drug_name = result.get('Drug', '')
            drug_row = drug_data[drug_data['Drug'] == drug_name]
            diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
            
            ws_intermediate_data.append({
                'Drug': drug_name,
                'Diluent': diluent,
                'Intermediate_to_Add': f"{result.get('Vol_Inter_to_WS', 0):.2f}",
                'Diluent_to_Add': f"{result.get('Dil_to_WS', 0):.4f}",
                'Volume_WS': f"{result.get('Dil_to_WS', 0) + result.get('Vol_Inter_to_WS', 0):.4f}",
                'Conc_WS': f"{result.get('Conc_Ws', 0):.2f}"
            })
    if ws_intermediate_data:
        tables['working_solution_intermediate'] = ws_intermediate_data
    
    # Table 4: Working Solution from Stock
    ws_stock_data = []
    for result in final_results:
        if make_stock and result.get('Intermediate') == False:
            drug_name = result.get('Drug', '')
            drug_row = drug_data[drug_data['Drug'] == drug_name]
            diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
            
            ws_stock_data.append({
                'Drug': drug_name,
                'Diluent': diluent,
                'Stock_to_Add': f"{result.get('Stock_to_WS', 0):.2f}",
                'Diluent_to_Add': f"{result.get('Dil_to_WS', 0):.2f}",
                'Volume_WS': f"{result.get('Dil_to_WS', 0) + result.get('Stock_to_WS', 0):.2f}",
                'Conc_WS': f"{result.get('Conc_Ws', 0):.2f}"
            })
    if ws_stock_data:
        tables['working_solution_stock'] = ws_stock_data
    
    # Table 5: Working Solution No Stock
    ws_no_stock_data = []
    for result in final_results:
        if not make_stock:
            drug_name = result.get('Drug', '')
            drug_row = drug_data[drug_data['Drug'] == drug_name]
            diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else 'Unknown'
            
            ws_no_stock_data.append({
                'Drug': drug_name,
                'Diluent': diluent,
                'Drug_Weight': f"{result.get('Act_Weight', 0):.4f}",
                'Diluent_to_Add': f"{result.get('Final_Vol_Dil', 0):.4f}",
                'Conc_WS': f"{result.get('Conc_Ws', 0):.2f}"
            })
    if ws_no_stock_data:
        tables['working_solution_no_stock'] = ws_no_stock_data
    
    # Table 6: Aliquoting
    if make_stock:
        aliquot_data = []
        for result in final_results:
            drug_name = result.get('Drug', '')
            aliquot_data.append({
                'Drug': drug_name,
                'Number_of_Aliquots': f"{result.get('Number_of_Ali', 0):.0f}",
                'Volume_per_Aliquot': f"{result.get('ml_aliquot', 0):.1f}"
            })
        tables['aliquoting'] = aliquot_data
    
    # Table 7: MGIT Tube Preparation
    mgit_data = []
    for result in final_results:
        drug_name = result.get('Drug', '')
        mgit_data.append({
            'Drug': drug_name,
            'Number_of_MGITs': f"{result.get('MGIT_Tubes', 0):.0f}",
            'Volume_WS_per_MGIT': "0.1",
            'Volume_OADC_per_MGIT': "0.8",
            'Volume_Culture_per_MGIT': "0.5"
        })
    tables['mgit_preparation'] = mgit_data
    
    return tables

def create_html_table(data, headers, table_style="", header_style="", row_style=""):
    """Create an HTML table from data."""
    if not data:
        return ui.tags.div()
    
    # Create header row
    header_row = ui.tags.tr(
        *[ui.tags.th(header, style=f"padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; text-align: center; {header_style}") 
          for header in headers]
    )
    
    # Create data rows
    data_rows = []
    for row_data in data:
        cells = []
        for header in headers:
            # Convert header to key format - specific mapping for each header
            key_mapping = {
                'Drug': 'Drug',
                'Diluent': 'Diluent',
                'Drug Weight\n(mg)': 'Drug_Weight',
                'Total Stock\nVolume (ml)': 'Total_Stock_Vol',
                'Stock\nConcentration\n(μg/ml)': 'Stock_Conc',
                'Dilution Factor': 'Dilution_Factor',
                'Stock to\nAdd (ml)': 'Stock_to_Add',
                'Diluent to\nAdd(ml)': 'Diluent_to_Add',
                'Intermediate\nVol. (ml)': 'Intermediate_Vol',
                'Intermediate\nConc. (μg/ml)': 'Intermediate_Conc',
                'Intermediate to\nAdd (ml)': 'Intermediate_to_Add',
                'Volume WS\n(ml)': 'Volume_WS',
                'Conc. WS\n(μg/ml)': 'Conc_WS',
                'Number of\nAliquots': 'Number_of_Aliquots',
                'Volume per\nAliquot (ml)': 'Volume_per_Aliquot',
                'Number of\nMGITs': 'Number_of_MGITs',
                'Volume WS\nper MGIT (ml)': 'Volume_WS_per_MGIT',
                'Volume OADC\nper MGIT (ml)': 'Volume_OADC_per_MGIT',
                'Volume Culture\nper MGIT (ml)': 'Volume_Culture_per_MGIT'
            }
            
            key = key_mapping.get(header, header)
            value = row_data.get(key, '')
            cells.append(ui.tags.td(str(value), style=f"padding: 8px; border: 1px solid #ddd; text-align: center; {row_style}"))
        data_rows.append(ui.tags.tr(*cells))
    
    # Create complete table
    return ui.tags.table(
        header_row,
        *data_rows,
        style=f"border-collapse: collapse; margin: 15px 0; width: 100%; {table_style}"
    )

def perform_final_calculations():
    """Perform final calculations for MGIT tubes and working solutions based on two categories:
    1. No stock solution: Recalculate diluent volume using actual weight
    2. Stock solution with aliquots: Calculate total stock volume with error margin
    """
    print("perform_final_calculations: Starting")
    
    print(f"perform_final_calculations: Processing {len(selected)} drugs")
    
    try:
        # Get selected drugs and preferences
        selected = input.drug_selection()
        if not selected:
            print("perform_final_calculations: No drugs selected")
            return []
        
        make_stock = bool(make_stock_pref())
        print(f"perform_final_calculations: Processing {len(selected)} drugs with make_stock={make_stock}")
        
        # Debug: Check if Step3 data exists
        print(f"perform_final_calculations: Step3_ActDrugWeights = {Step3_ActDrugWeights[:len(selected)]}")
        print(f"perform_final_calculations: Step2_MgitTubes = {Step2_MgitTubes[:len(selected)]}")
        
        drug_data = load_drug_data()
        final_results = []
        
        # Process each drug
        for drug_idx, drug_name in enumerate(selected):
            mgit_tubes = Step2_MgitTubes[drug_idx]
            crit_conc = Step2_CriticalConc[drug_idx]
            actual_weight = Step3_ActDrugWeights[drug_idx]
            ws_vol_ml = Step2_VolWS[drug_idx]
            ws_conc_ugml = Step2_ConcWS[drug_idx]

            if make_stock:
                # Stock solution calculations
                est_weight = Step2_EstWeights[drug_idx]
                total_stock_vol = Step2_TotalStockVolumes[drug_idx]
                pot = Step2_Potencies[drug_idx]
                ml_ali = Step2_mlperAliquot[drug_idx]

                # Use modular calculation functions
                total_volWS = calc_adjusted_volume(actual_weight, est_weight, ws_vol_ml)
                new_a_val = calc_stock_factor(actual_weight, total_stock_vol, ws_conc_ugml, pot)
                stock_vol_to_add_to_ws_ml = calc_volume_divided_by_factor(total_volWS, new_a_val)
                diluent_vol_to_add_to_ws_ml = total_volWS - stock_vol_to_add_to_ws_ml
                total_stock_left = total_stock_vol - stock_vol_to_add_to_ws_ml
                num_aliquots = floor(total_stock_left / ml_ali)
                Final_stock_conc = calc_concentration_times_factor(ws_conc_ugml, new_a_val)
                
                if stock_vol_to_add_to_ws_ml >= 0.1:
                    final_results.append({
                        'Intermediate': False,
                        'Drug': drug_name,
                        'Diluent': drug_data[drug_data['Drug'] == drug_name].iloc[0]['Diluent'],
                        'Crit_Conc': round(crit_conc, 2),
                        'Act_Weight': round(actual_weight, 2),
                        'Stock_Conc': round(Final_stock_conc, 2),
                        'Stock_Factor' : round(new_a_val, 1),
                        'Stock_to_WS_µl': ml_to_ul(stock_vol_to_add_to_ws_ml),
                        'Stock_to_WS': round(stock_vol_to_add_to_ws_ml, 2),
                        'Dil_to_WS_µl': ml_to_ul(diluent_vol_to_add_to_ws_ml),
                        'Dil_to_WS': round(diluent_vol_to_add_to_ws_ml, 2),
                        'Conc_Ws': round(ws_conc_ugml, 2),
                        'Total_Stock_Vol_µl': ml_to_ul(total_stock_vol),
                        'Total_Stock_Vol': round(total_stock_vol, 2),
                        'Total_Stock_Left_µl': ml_to_ul(total_stock_left),
                        'Total_Stock_Left': round(total_stock_left, 2),
                        'MGIT_Tubes': round(mgit_tubes),
                        'Number_of_Ali': round(num_aliquots),
                        'ml_aliquot_µl': ml_to_ul(ml_ali),
                        'ml_aliquot': round(ml_ali, 2),
                    })
                else:
                    intermediate = True
                    
                    # Use modular intermediate calculation functions
                    InterFactor = calc_intermediate_factor(new_a_val, total_volWS)
                    stock_to_inter = calc_volume_divided_by_factor(total_volWS, InterFactor)
                    total_stock_left = total_stock_vol - stock_to_inter
                    num_aliquots = floor(total_stock_left / ml_ali)
                    inter_conc = calc_concentration_times_factor(ws_conc_ugml, InterFactor)
                    Vol_of_inter = calc_intermediate_volume(stock_to_inter, Final_stock_conc, InterFactor, ws_conc_ugml)
                    dil_to_inter = calc_volume_difference(Vol_of_inter, stock_to_inter)
                    vol_inter_to_ws = calc_volume_divided_by_factor(total_volWS, InterFactor)
                    vol_dil_to_ws = calc_volume_difference(total_volWS, vol_inter_to_ws)

                    final_results.append({
                        'Intermediate': True,
                        'Drug': drug_name,
                        'Diluent': drug_data[drug_data['Drug'] == drug_name].iloc[0]['Diluent'],
                        'Crit_Conc': round(crit_conc, 2),
                        'Act_Weight': round(actual_weight, 2),
                        'Stock_Conc': round(Final_stock_conc, 2),
                        'Stock_Factor' : round(new_a_val, 2),
                        'Total_Stock_Vol_µl': ml_to_ul(total_stock_vol),
                        'Total_Stock_Vol': round(total_stock_vol, 2),
                        'Total_Stock_Left_µl': ml_to_ul(total_stock_left),
                        'Total_Stock_Left': round(total_stock_left, 2),
                        'Stock_to_Inter_µl': ml_to_ul(stock_to_inter),
                        'Stock_to_Inter': round(stock_to_inter, 2),
                        'Inter_Factor': round(InterFactor, 1),
                        'Inter_Conc': round(inter_conc, 2),
                        'Dil_to_Inter_µl': ml_to_ul(dil_to_inter),
                        'Dil_to_Inter': round(dil_to_inter, 2),
                        'Vol_Inter_to_WS_µl': ml_to_ul(vol_inter_to_ws),
                        'Vol_Inter_to_WS': round(vol_inter_to_ws, 2),
                        'Dil_to_WS_µl': ml_to_ul(vol_dil_to_ws),
                        'Dil_to_WS': round(vol_dil_to_ws, 2),
                        'Conc_Ws': round(ws_conc_ugml, 2),
                        'MGIT_Tubes': round(mgit_tubes),
                        'Number_of_Ali': round(num_aliquots),
                        'ml_aliquot_µl': ml_to_ul(ml_ali),
                        'ml_aliquot': round(ml_ali, 2),
                    })

            else:
                # No stock solution calculations
                est_weight = Step2_CalEstWeights[drug_idx]
                final_vol_diluent = calc_adjusted_volume(actual_weight, est_weight, ws_vol_ml)
                print(f"perform_final_calculations: Drug {drug_name}, actual_weight={actual_weight}, est_weight={est_weight}, ws_vol_ml={ws_vol_ml}, final_vol_diluent={final_vol_diluent}")   
                
                final_results.append({
                    'Intermediate': False,
                    'Drug': drug_name,
                    'Diluent': drug_data[drug_data['Drug'] == drug_name].iloc[0]['Diluent'],
                    'Crit_Conc': round(crit_conc, 2),
                    'Act_Weight': round(actual_weight, 2),
                    'Final_Vol_Dil_µl': ml_to_ul(final_vol_diluent),
                    'Final_Vol_Dil': round(final_vol_diluent, 2),
                    'Conc_Ws': round(ws_conc_ugml, 2),
                    'MGIT_Tubes': round(mgit_tubes),
                })
    
        
        return final_results
        
    except Exception as e:
        print(f"perform_final_calculations: Error: {e}")
        return []


def generate_step2_pdf():
    """Generate PDF for Step 2 results using modular PDF generation"""
    try:
        selected = input.drug_selection()
        make_stock = bool(make_stock_pref())
        
        # Prepare Step 2 data structure for the modular function
        step2_data = build_step2_data_structure()
        
        # Call the modular PDF generation function
        return generate_step2_pdf_module(selected, make_stock, step2_data)
        
    except Exception as e:
        print(f"Error generating Step 2 PDF: {e}")
        return None


def generate_step4_pdf():
    """Generate PDF for Step 4 final results using modular PDF generation"""
    try:
        selected = input.drug_selection()
        make_stock = bool(make_stock_pref())
        
        final_results = perform_final_calculations()
        
        # Prepare Step 2 data structure for the modular function
        step2_data = build_step2_data_structure()
        
        # Call the modular PDF generation function with final results
        return generate_step4_pdf_backend(selected, make_stock, step2_data, Step3_ActDrugWeights, final_results)
        
    except Exception as e:
        print(f"Error generating Step 4 PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


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
            
with ui.navset_card_pill(id="tab", selected="Account & Sessions"):

    with ui.nav_panel("Account & Sessions"):
        
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

        # User's sessions cards (helper UI builder)
        def user_sessions_ui():
            user = current_user()
            if not user:
                return ui.tags.div()
            try:
                import json
                with db_manager.get_connection() as conn:
                    cur = conn.execute(
                        "SELECT session_id, session_name, session_date, preparation FROM session WHERE user_id = ? ORDER BY session_date DESC",
                        (user['user_id'],)
                    )
                    rows = cur.fetchall()
                
                if not rows:
                    return ui.tags.div(
                        ui.tags.h3("Your Sessions", style="color: #2c3e50; margin-bottom: 10px;"),
                        ui.tags.p("No sessions found. Start a new session in Tab B.", style="color: #7f8c8d; font-style: italic;"),
                        style="margin-bottom: 12px;"
                    )
                
                session_cards = []
                for sid, name, dt, prep_json in rows:
                    completed = False
                    try:
                        prep = json.loads(prep_json) if prep_json else {}
                        completed = bool(prep and prep.get('step', 0) >= 3 and prep.get('results'))
                    except Exception:
                        completed = False
                    
                    # Format date for display
                    from datetime import datetime
                    try:
                        dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                        formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = str(dt)
                    
                    # Create clickable session card
                    card_style = "border: 2px solid #e74c3c; background-color: #fdf2f2;" if completed else "border: 2px solid #3498db; background-color: #f8f9fa;"
                    button_style = "background-color: #e74c3c; color: white;" if completed else "background-color: #3498db; color: white;"
                    
                    session_cards.append(
                        ui.tags.div(
                            ui.tags.div(
                                ui.tags.h5(name or "Unnamed Session", style="margin: 0 0 4px 0; color: #2c3e50; font-size: 14px; font-weight: bold;"),
                                ui.tags.p(f"{formatted_date}", style="margin: 0 0 2px 0; color: #7f8c8d; font-size: 12px;"),
                                ui.tags.p(
                                    ui.tags.span("✓ Completed" if completed else "○ In Progress", 
                                               style=f"color: {'#27ae60' if completed else '#f39c12'}; font-weight: bold; font-size: 12px;")
                                ),
                                style="padding: 8px;"
                            ),
                            ui.tags.button(
                                "View Results" if completed else "Continue Session",
                                class_="btn",
                                style=f"{button_style} width: 100%; margin-top: 6px; padding: 4px 8px; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;",
                                onclick=f"Shiny.setInputValue('session_clicked', '{sid}', {{priority: 'event'}});"
                            ),
                            style=f"{card_style} border-radius: 6px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;",
                            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)';",
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
                        )
                    )

                return ui.tags.div(
                    ui.tags.h3("Your Sessions", style="color: #2c3e50; margin-bottom: 15px;"),
                    *session_cards,
                    style="margin-bottom: 12px;"
                )
            except Exception:
                return ui.tags.div()


        # Users table
        @render.ui
        def users_table():
            # Hide when a user is signed in
            if current_user():
                return ui.tags.div()
            try:
                with db_manager.get_connection() as conn:
                    users_cur = conn.execute("SELECT user_id, username FROM users ORDER BY user_id ASC")
                    users_rows = users_cur.fetchall()
                    header = ui.tags.tr(
                        ui.tags.th("User ID", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("Username", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("Total Sessions", style="padding: 6px; border: 1px solid #ddd;"),
                        ui.tags.th("Recent Session", style="padding: 6px; border: 1px solid #ddd;")
                    )
                    body_rows = []
                    for user_id, username in users_rows:
                        sess_cur = conn.execute(
                            "SELECT session_name FROM session WHERE user_id = ? ORDER BY session_date DESC LIMIT 1",
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

        # Toggle buttons for forms (hidden when signed in)
        @render.ui
        def auth_toggle_buttons():
            if current_user():
                return ui.tags.div()
            return ui.tags.div(
                ui.input_action_button("show_register", "Sign up", class_="btn-primary", style="margin-right: 10px;"),
                ui.input_action_button("show_login", "Login", class_="btn-success")
            )

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
                    ),
                    user_sessions_ui(),
                    style="margin-top: 16px;"
                )
            return ui.tags.div()  # none


    with ui.nav_panel("Calculator"):
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
                        "Weight Entry",
                        "Solution Guide"
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
                
                # Unit Selection Section - only shown in Step 2
                @render.ui
                def unit_preferences():
                    return ui.tags.div()
            
            # Main content area with minimal top padding
            ui.tags.div(style="padding-top: 5px;")
            
            # Main content area - render functions will be called directly
            
            # Session results view (when viewing completed sessions)
            @render.ui
            def session_results_view():
                print(f"session_results_view called, show_results_view: {show_results_view()}")
                if not show_results_view():
                    print("Returning empty div (hiding session results view)")
                    return ui.tags.div()
                
                data = session_data.get()
                if not data:
                    return ui.tags.div()
                
                preparation = data.get('preparation', {})
                selected_drugs = data.get('selected_drugs', [])
                volume_unit_val = data.get('volume_unit', 'ml')
                weight_unit_val = data.get('weight_unit', 'mg')
                inputs = data.get('inputs', {})
                
                # Get drug data for calculations
                drug_data = load_drug_data()
                
                # Get session name from current session
                cs = current_session()
                session_name = cs.get('session_name', 'Unnamed Session') if cs else 'Unnamed Session'
                
                # Build session info header
                session_info = ui.tags.div(
                    ui.tags.h2("Session Results", style="color: #2c3e50; margin-bottom: 20px;"),
                    ui.tags.div(
                        ui.tags.p(f"Session: {session_name}", style="font-weight: bold; margin-bottom: 5px;"),
                        ui.tags.p(f"Volume Unit: {volume_unit_val} | Weight Unit: {weight_unit_val}", style="color: #7f8c8d; margin-bottom: 10px;"),
                        style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;"
                    )
                )
                
                # Build selected drugs section
                drugs_section = ui.tags.div(
                    ui.tags.h4("Selected Drugs", style="color: #2c3e50; margin-bottom: 15px;"),
                    ui.tags.ul(
                        *[ui.tags.li(drug, style="margin-bottom: 5px;") for drug in selected_drugs],
                        style="list-style-type: disc; margin-left: 20px;"
                    )
                )
                
                # Build input parameters section
                # The inputs are stored with numeric indices (0, 1, 2, etc.) corresponding to the order of selected drugs
                input_sections = []
                for i, drug_name in enumerate(selected_drugs):
                    # Get the input data using the index
                    drug_inputs = inputs.get(str(i), {})
                    
                    input_sections.append(
                        ui.tags.div(
                            ui.tags.h4(f"Drug: {drug_name}", style="color: #2c3e50; margin-bottom: 10px; font-size: 16px;"),
                            ui.tags.div(
                                ui.tags.p(f"Critical Concentration: {drug_inputs.get('Crit_Conc(mg/ml)', 'N/A')} mg/ml", style="margin-bottom: 5px;"),
                                ui.tags.p(f"Purchased Molecular Weight: {drug_inputs.get('PurMol_W(g/mol)', 'N/A')} g/mol", style="margin-bottom: 5px;"),
                                ui.tags.p(f"Stock Volume: {drug_inputs.get('St_Vol(ml)', 'N/A')} {volume_unit_val}", style="margin-bottom: 5px;"),
                                ui.tags.p(f"Actual Drug Weight: {drug_inputs.get('Act_DrugW(mg)', 'N/A')} {weight_unit_val}", style="margin-bottom: 5px;"),
                                ui.tags.p(f"MGIT Tubes: {drug_inputs.get('Total Mgit tubes', 'N/A')}", style="margin-bottom: 5px;"),
                                style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 15px;"
                            )
                        )
                    )
                
                inputs_section = ui.tags.div(
                    ui.tags.h4("Input Parameters", style="color: #2c3e50; margin-bottom: 15px;"),
                    ui.tags.div(*input_sections, style="margin-bottom: 20px;")
                )
                
                # Recalculate results from saved inputs
                results_sections = []
                
                try:
                    # Step 2: Calculate estimated drug weights
                    estimated_weights = []
                    for i, drug_name in enumerate(selected_drugs):
                        # Get the input data using the index
                        drug_inputs = inputs.get(str(i), {})
                        
                        if drug_inputs:
                            # Get input values
                            stock_vol = drug_inputs.get('St_Vol(ml)', 0)
                            purch_molw = drug_inputs.get('PurMol_W(g/mol)', 0)
                            custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', 0)
                            
                            if stock_vol and purch_molw and custom_crit:
                                stock_vol_ml = stock_vol
                                purch_molw_gmol = purch_molw
                                custom_crit_mgml = custom_crit
                                
                                # Get drug data
                                drug_row = drug_data[drug_data['Drug'] == drug_name]
                                if not drug_row.empty:
                                    org_molw = drug_row.iloc[0]['OrgMolecular_Weight']
                                    
                                    # Calculate potency
                                    # [1] potency calculation from dst-calc.py
                                    pot = potency(purch_molw_gmol, org_molw)
                                    
                                    # Calculate estimated drug weight
                                    # [2] est_drugweight calculation from dst-calc.py
                                    est_dw = est_drugweight(custom_crit_mgml, stock_vol_ml, pot)
                                    
                                    est_dw_user_unit = est_dw
                                    estimated_weights.append(est_dw_user_unit)
                                else:
                                    estimated_weights.append(0)
                            else:
                                estimated_weights.append(0)
                        else:
                            estimated_weights.append(0)
                    
                    # Display Step 2 results
                    if estimated_weights:
                        results_sections.append(
                            ui.tags.div(
                                ui.tags.h3("Step 2: Estimated Drug Weights", style="color: #2c3e50; margin-bottom: 15px;"),
                                ui.tags.table(
                                    ui.tags.tr(
                                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;"),
                                        ui.tags.th(f"Estimated Weight ({weight_unit_val})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;")
                                    ),
                                    *[ui.tags.tr(
                                        ui.tags.td(selected_drugs[i], style="padding: 8px; border: 1px solid #ddd;"),
                                        ui.tags.td(f"{estimated_weights[i]:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center;")
                                    ) for i in range(min(len(selected_drugs), len(estimated_weights)))],
                                    style="border-collapse: collapse; margin-bottom: 20px;"
                                )
                            )
                        )
                    
                    # Step 3: Calculate final results
                    final_results = []
                    for i, drug_name in enumerate(selected_drugs):
                        # Get the input data using the index
                        drug_inputs = inputs.get(str(i), {})
                        
                        if drug_inputs:
                                    # Get input values in base units
                                    actual_weight_mg = drug_inputs.get('Act_DrugW(mg)', 0)
                                    mgit_tubes = drug_inputs.get('Total Mgit tubes', 0)
                                    stock_vol_ml = drug_inputs.get('St_Vol(ml)', 0)
                                    purch_molw_gmol = drug_inputs.get('PurMol_W(g/mol)', 0)
                                    custom_crit_mgml = drug_inputs.get('Crit_Conc(mg/ml)', 0)
                                    
                                    if actual_weight_mg and mgit_tubes and stock_vol_ml and purch_molw_gmol and custom_crit_mgml:                                # Get drug data
                                        drug_row = drug_data[drug_data['Drug'] == drug_name]
                                    if not drug_row.empty:
                                        org_molw = drug_row.iloc[0]['OrgMolecular_Weight']
                                    
                                    # Calculate potency
                                    # [1] potency calculation from dst-calc.py
                                    pot = potency(purch_molw_gmol, org_molw)
                                    
                                    # Calculate estimated drug weight (from step 2)
                                    # [2] est_drugweight calculation from dst-calc.py
                                    est_drug_weight_mg = est_drugweight(custom_crit_mgml, stock_vol_ml, pot)
                                    
                                    # Calculate diluent volume and stock concentration
                                    # [3] vol_diluent calculation from dst-calc.py
                                    vol_dil = vol_diluent(est_drug_weight_mg, actual_weight_mg, stock_vol_ml)
                                    # [4] conc_stock calculation from dst-calc.py
                                    conc_stock_ugml = conc_stock(actual_weight_mg, vol_dil)
                                    
                                    # Calculate final working solution parameters
                                    # [5] conc_ws calculation from dst-calc.py
                                    conc_ws_ugml = conc_ws(custom_crit_mgml)
                                    # [6] vol_workingsol calculation from dst-calc.py
                                    vol_working_sol_ml = vol_workingsol(mgit_tubes)
                                    # [7] vol_ss_to_ws calculation from dst-calc.py
                                    vol_stock_to_ws_ml = vol_ss_to_ws(vol_working_sol_ml, conc_ws_ugml, conc_stock_ugml)
                                    # [8] calc_volume_difference calculation from dst-calc.py
                                    vol_diluent_to_add_ml = calc_volume_difference(vol_working_sol_ml, vol_stock_to_ws_ml)
                                    
                                    # Keep values in base units (ml)
                                    stock_vol_user = vol_stock_to_ws_ml
                                    diluent_vol_user = vol_diluent_to_add_ml
                                    
                                    # Check for warnings
                                    if vol_diluent_to_add_ml < 0:
                                        stock_vol_user = vol_working_sol_ml
                                        diluent_vol_user = 0
                                    
                                    # Get diluent from drug data
                                    diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else "Unknown"
                                    
                                    final_results.append({
                                        'Drug': drug_name,
                                        'Diluent': diluent,
                                        'Stock_Vol': stock_vol_user,
                                        'Diluent_Vol': diluent_vol_user
                                    })
                    
                    # Display Step 3 results
                    if final_results:
                        results_sections.append(
                            ui.tags.div(
                                ui.tags.h3("Step 3: Final Results", style="color: #2c3e50; margin-bottom: 15px;"),
                                ui.tags.table(
                                    ui.tags.tr(
                                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;"),
                                        ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;"),
                                        ui.tags.th("Aliquot for Stock Solution (ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;"),
                                        ui.tags.th("Diluent to Add (ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;")
                                    ),
                                    *[ui.tags.tr(
                                        ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd;"),
                                        ui.tags.td(result['Diluent'], style="padding: 8px; border: 1px solid #ddd;"),
                                        ui.tags.td(f"{result['Stock_Vol']:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center;"),
                                        ui.tags.td(f"{result['Diluent_Vol']:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center;")
                                    ) for result in final_results],
                                    style="border-collapse: collapse; margin-bottom: 20px;"
                                )
                            )
                        )
                
                except Exception as e:
                    results_sections.append(
                        ui.tags.div(
                            ui.tags.p(f"Error recalculating results: {str(e)}", style="color: red; margin-bottom: 15px;"),
                            style="background-color: #fdf2f2; padding: 10px; border-radius: 6px; margin-bottom: 15px;"
                        )
                    )
                
                # Combine all results sections
                results_section = ui.tags.div(*results_sections) if results_sections else ui.tags.div()
                
                # Back button
                back_button = ui.tags.div(
                    ui.input_action_button("back_to_sessions", "Back to Sessions", class_="btn-secondary"),
                    style="text-align: center; margin-top: 30px;"
                )
                
                return ui.tags.div(
                    session_info,
                    drugs_section,
                    inputs_section,
                    results_section,
                    back_button,
                    style="padding: 20px;"
                )
            
            
            # Main interface that shows different content based on current step
            @render.ui
            def main_interface():
                print(f"main_interface called, show_results_view: {show_results_view()}, current_step: {current_step()}")
                if show_results_view():
                    print("Returning empty div (hiding main interface)")
                    return ui.tags.div()  # Hide when showing results
                
                if current_step() == 1:
                    print("Returning step 1 interface (drug selection)")
                    return ui.tags.div(
                        ui.tags.h2("Select Drugs", style="color: #2c3e50; margin-bottom: 20px;"),
                    ui.input_selectize(
                        "drug_selection",
                        "Select the drugs you want to calculate parameters for:",
                        drug_selection,
                        multiple=True,
                            ),
                            style="margin-bottom: 30px;"
                    )
                elif current_step() == 2:
                    print("Returning step 2 interface (input parameters)")
                    return ui.tags.h3()
                elif current_step() == 3:
                    print("Returning step 3 interface (final inputs)")
                    return ui.tags.h3()
                else:
                    print("Returning default interface")
                    return ui.tags.h3()
            
            # Display selected drugs in a table
            @render.ui
            def selected_drugs_table():
                print(f"selected_drugs_table called, show_results_view: {show_results_view()}")
                # Hide when viewing results
                if show_results_view():
                    print("Returning empty div (hiding selected_drugs_table)")
                    return ui.tags.div()

                # Always try to get drugs from session first when in a session
                selected = []
                cs = current_session()
                if cs:
                    print(f"Getting drugs from session {cs['session_id']}")
                    try:
                        with db_manager.get_connection() as conn:
                            cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                            row = cur.fetchone()
                            if row and row[0]:
                                import json
                                preparation = json.loads(row[0])
                                selected = preparation.get('selected_drugs', [])
                                print(f"Got drugs from session: {selected}")
                    except Exception as e:
                        print(f"Error getting session data: {e}")
                
                # Fallback to input if no session data
                if not selected:
                    selected = input.drug_selection()
                    print(f"Selected drugs from input: {selected}")
                
                print(f"Current step: {current_step()}")
                
                if not selected:
                    print("No drugs selected, returning message")
                    return ui.tags.div("No drugs selected yet.")
                
                # Get the full drug data
                drug_data = load_drug_data()
                
                if current_step() == 1:
                    # Create table headers for step 1
                    table_headers = ui.tags.tr(
                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                        ui.tags.th("Mol. Weight (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                        ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
                        ui.tags.th("Crit. Conc. (μg/ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;"),
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
                                    ui.tags.div(
                                        ui.input_numeric(
                                            f"custom_critical_{i}",
                                            "",
                                            value=row_data['Critical_Concentration'],
                                            min=0,
                                            step=0.1
                                        ),
                                        style="width: 90px;"
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 80px;"
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
                    print("Creating step 2 table (new flow)")
                    
                    # Get current potency method
                    current_potency_method = potency_method_pref()
                    
                    # Create table headers based on potency method
                    headers_list = [
                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                        ui.tags.th("Crit. Conc. (μg/ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                        ui.tags.th("Org. Mol. Wt. (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 140px;"),
                    ]
                    
                    # Add columns based on method
                    if current_potency_method in ["mol_weight", "both"]:
                        headers_list.append(
                            ui.tags.th("Purch. Mol. Wt. (g/mol)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 140px;")
                        )
                    if current_potency_method in ["purity", "both"]:
                        headers_list.append(
                            ui.tags.th("Purity %", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 100px;")
                        )
                    
                    headers_list.append(
                        ui.tags.th("MGIT Tubes", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;")
                    )
                    
                    table_headers = ui.tags.tr(*headers_list, style="background-color: #f8f9fa;")

                    # Create table rows for each selected drug
                    table_rows = []
                    stored_inputs = session_inputs.get()
                    print(f"Stored inputs: {stored_inputs}")
                    for i, drug_name in enumerate(selected):
                        print(f"Processing drug {i}: {drug_name}")
                        # Find the drug data in the dataframe for step 2
                        drug_row = drug_data[drug_data['Drug'] == drug_name]
                        if not drug_row.empty:
                            row_data = drug_row.iloc[0]
                            current_custom = input[f"custom_critical_{i}"]()
                            if current_custom is None:
                                current_custom = row_data['Critical_Concentration']

                        # Get stored values if they exist
                        stored_values = stored_inputs.get(str(i), {})
                        purch_molw_value = stored_values.get('PurMol_W(g/mol)', 0)
                        mgit_tubes_value = stored_values.get('Total Mgit tubes', 0)
                        purity_value = stored_values.get('Purity_%', 0)
                        
                        # Get current purity value
                        try:
                            current_purity = input[f"purity_{i}"]()
                            if current_purity is None:
                                current_purity = purity_value
                        except Exception:
                            current_purity = purity_value

                        # Build row cells dynamically based on potency method
                        row_cells = [
                            ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                            ui.tags.td(f"{current_custom:.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                            ui.tags.td(f"{row_data['OrgMolecular_Weight']:.2f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                        ]
                        
                        # Add purchased molecular weight column if needed
                        if current_potency_method in ["mol_weight", "both"]:

                            try:
                                existing_purch = input[f"purchased_molw_{i}"]()
                            except Exception:
                                existing_purch = None
                            if existing_purch is None:
                                purch_default = purch_molw_value
                            else:
                                purch_default = existing_purch

                            row_cells.append(
                                ui.tags.td(
                                    ui.tags.div(
                                        ui.input_numeric(
                                            f"purchased_molw_{i}",
                                            "",
                                            value=purch_default,
                                            min=row_data['OrgMolecular_Weight'],
                                            step=1
                                        ),
                                        style="width: 80px;"
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 60px;"
                                )
                            )
                        
                        if current_potency_method in ["purity", "both"]:
                            # Use the current input value if present to avoid overwriting user typing
                            try:
                                existing_purity_input = input[f"purity_{i}"]()
                            except Exception:
                                existing_purity_input = None
                            if existing_purity_input is None:
                                purity_default = purity_value
                            else:
                                purity_default = existing_purity_input

                            row_cells.append(
                                ui.tags.td(
                                    ui.tags.div(
                                        ui.input_numeric(
                                            f"purity_{i}",
                                            "",
                                            value=purity_default,
                                            min=1,
                                            max=100,
                                            step=1
                                        ),
                                        style="width: 80px;"
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 60px;"
                                )
                            )

                        # Always add MGIT tubes column
                        row_cells.append(
                            ui.tags.td(
                                ui.tags.div(
                                    ui.input_numeric(
                                        f"mgit_tubes_{i}",
                                        "",
                                        value=mgit_tubes_value,
                                        min=1,
                                        step=1
                                    ),
                                    style="width: 80px;"
                                ),
                                style="padding: 5px; border: 1px solid #ddd; width: 60px;"
                            )
                        )
                        
                        row = ui.tags.tr(*row_cells, style="background-color: white;")
                        table_rows.append(row)

                    return ui.tags.div(
                        ui.tags.h3("Enter Parameters", style="color: #2c3e50; margin-bottom: 15px;"),
                        ui.tags.p("Select how you want to calculate potency:", style="color: #7f8c8d; margin-bottom: 10px; font-weight: bold;"),
                        ui.tags.div(
                            ui.input_radio_buttons(
                                "potency_method_radio",
                                "",
                                choices={
                                    "mol_weight": "Molecular Weight",
                                    "purity": "Purity % ",
                                    "both": "Both (Purity % and Mol. Weight)"
                                },
                                selected=potency_method_pref(),
                                inline=True
                            ),
                            style="margin-bottom: 10px;"
                        ),
                        ui.tags.p("Enter the required parameters for each selected drug:", style="color: #7f8c8d; margin-bottom: 15px;"),
                        ui.tags.div(
                            ui.tags.table(
                                table_headers,
                                *table_rows,
                                style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                            ),
                            style="overflow-x: auto; max-width: 100%;"
                        )
                    )
                elif current_step() == 3:
                    print("Creating step 3 table")
                    # Create table headers for step 3
                    table_headers = ui.tags.tr(
                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                        ui.tags.th(f"Actual Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                    )
                    
                    # Create table rows for each selected drug
                    table_rows = []
                    stored_inputs = session_inputs.get()
                    print(f"Step 3: Creating rows for {len(selected)} drugs")
                    for i, drug_name in enumerate(selected):
                        # Get estimated weight from previous calculation
                        est_weight = get_estimated_weight(i)
                        
                        # Get stored values if they exist
                        stored_values = stored_inputs.get(str(i), {})
                        actual_weight_value = stored_values.get('Act_DrugW(mg)', 0)
                        mgit_tubes_value = stored_values.get('Total Mgit tubes', 0)
                        print(f"Step 3: Drug {i} ({drug_name}) - estimated weight: {est_weight}, stored values: actual_weight={actual_weight_value}, mgit_tubes={mgit_tubes_value}")
                        
                        row = ui.tags.tr(
                            ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                            ui.tags.td(
                                ui.input_numeric(
                                    f"actual_weight_{i}",
                                    "",
                                    value=actual_weight_value,
                                    min=0,
                                    step=0.001
                                ),
                                style="padding: 5px; border: 1px solid #ddd; width: 120px;"
                            ),
                            style="background-color: white;"
                        )
                        table_rows.append(row)
                        print(f"Step 3: Created row for drug {i}")
                    
                    print("Step 3: Returning table")
                    return ui.tags.div(
                        ui.tags.h3("Enter Actual Weights", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                        ui.tags.p("Enter the actual weighed amount for each drug", style="color: #7f8c8d; margin-bottom: 15px;"),
                        ui.tags.div(
                            ui.tags.table(
                                table_headers,
                                *table_rows,
                                style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                            ),
                            style="overflow-x: auto; max-width: 100%;"
                        )
                    )

                elif current_step() == 4:
                    try:
                        # Collect data needed for instructions
                        make_stock = bool(make_stock_pref())
                        drug_data = load_drug_data()
                        final_results = perform_final_calculations()

                        if not final_results:
                            return ui.tags.div("Please complete Step 3 first.", style="color: red;")

                        # Create instruction sections
                        instruction_sections = []

                        # Build tables data for display
                        tables = build_step4_data_tables(final_results, make_stock)

                        # 1. Safety Precautions Section
                        instruction_sections.append(
                            ui.tags.div(
                                ui.tags.h3("A. Safety Precautions", 
                                         style="color: #c0392b; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #c0392b; padding-bottom: 5px;"),
                                ui.tags.div(
                                    ui.tags.ol(
                                        ui.tags.li("Put on appropriate personal protective equipment (PPE):",
                                            ui.tags.ul(
                                                ui.tags.li("Laboratory coat"),
                                                ui.tags.li("Nitrile gloves"),
                                                ui.tags.li("Safety goggles"),
                                                ui.tags.li("Face mask (N95 or equivalent)")
                                            )
                                        ),
                                        ui.tags.li("Clean and disinfect your work area"),
                                        ui.tags.li("Ensure proper ventilation"),
                                        ui.tags.li("Have spill kit ready"),
                                        style="color: #2c3e50;"
                                    ),
                                    style="background-color: #fadbd8; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                )
                            )
                        )

                        # 2. Preparation Instructions
                        if make_stock:
                            # Stock Solution Instructions
                            instruction_sections.append(
                                ui.tags.div(
                                    ui.tags.h3("B. Stock Solution Preparation", 
                                             style="color: #8e44ad; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #8e44ad; padding-bottom: 5px;"),
                                    # Add Stock Solution table
                                    create_html_table(
                                        tables.get('stock_solution', []),
                                        ['Drug', 'Diluent', 'Drug Weight\n(mg)', 'Total Stock\nVolume (ml)', 'Stock\nConcentration\n(μg/ml)', 'Dilution Factor'],
                                        table_style="margin-bottom: 20px;"
                                    ) if 'stock_solution' in tables else ui.tags.div(),
                                    ui.tags.div(
                                        *[ui.tags.div(
                                            ui.tags.h4(f"{result['Drug']} Stock Solution",
                                                    style="color: #8e44ad; margin-top: 15px; margin-bottom: 10px;"),
                                            ui.tags.ol(
                                                *( [ui.tags.li("Use polystyrene tubes (1.5ml or 5ml) as bedaquiline binds strongly to glass surfaces, which can cause loss of drug and inaccurate (lower) effective concentrations in solution.")] if result['Drug'] == "Bedaquiline (BDQ)" else [] ),
                                                ui.tags.li(f"Label a clean tube: '{result['Drug']} Stock Solution'"),
                                                *( [ui.tags.li("DMSO is light sensitive- Wrap the tube in foil or use a light-resistant tube to protect DMSO from degradation caused by light exposure.")] if result['Diluent'] == "DMSO" else [] ),
                                                ui.tags.li(f"Record the drug details:",
                                                    ui.tags.ul(
                                                        ui.tags.li(f"Date: {datetime.now().strftime('%Y-%m-%d')}"),
                                                        ui.tags.li(f"Drug: {result['Drug']}"),
                                                        ui.tags.li(f"Diluent: {result['Diluent']}"),
                                                        ui.tags.li(f"Concentration: {result['Stock_Conc']:.2f} μg/ml"),
                                                        ui.tags.li(f"Dilution Factor: 1:{result['Stock_Factor']:.1f}"),
                                                        ui.tags.li(f"Initials")
                                                    )
                                                ),
                                                ui.tags.li(f"Add the {result['Act_Weight']:.2f} mg weighed drug powder to a clean tube"),
                                                ui.tags.li(
                                                    f"Add {result['Total_Stock_Vol']:.2f} ml (= {result['Total_Stock_Vol_µl']:.2f} µl) of {result['Diluent']} to the same tube"
                                                ),
                                                ui.tags.li("Mix thoroughly:",
                                                    ui.tags.ul(
                                                        ui.tags.li("For bedaquiline:",
                                                            ui.tags.ul(
                                                                ui.tags.li("Close the tube securely"),
                                                                ui.tags.li("Do not invert the tubes as bedaquiline may adhere to plastic surfaces"),
                                                                ui.tags.li("If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes")
                                                            )
                                                        ) if result['Drug'] == "Bedaquiline (BDQ)" else [
                                                            ui.tags.li("Close the tube securely"),
                                                            ui.tags.li("Invert tube gently 2-4 times or vortex briefly"),
                                                            ui.tags.li("Do not shake vigorously to avoid foam formation"),
                                                            ui.tags.li("Check that drug powder is completely dissolved"),
                                                            ui.tags.li("Ensure no visible particles remain"),
                                                        ],
                                                    )
                                                ),
                                                style="color: #2c3e50;"
                                            ),
                                            style="background-color: #f5eef8; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                        ) for i, result in enumerate(final_results)]
                                    )
                                )
                            )
                        
                        # Intermediate Solution Instructions
                        intermediate_results = [result for result in final_results if result.get('Intermediate') == True]
                        if intermediate_results:
                            section_title = "Intermediate Solution Preparation"
                            instruction_sections.append(
                                ui.tags.div(
                                    ui.tags.h3(section_title, 
                                            style="color: #2980b9; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #2980b9; padding-bottom: 5px;"),
                                    # Add Intermediate Solution table
                                    create_html_table(
                                        tables.get('intermediate_solution', []),
                                        ['Drug', 'Diluent', 'Stock to\nAdd (ml)', 'Diluent to\nAdd(ml)', 'Intermediate\nVol. (ml)', 'Intermediate\nConc. (μg/ml)', 'Dilution Factor'],
                                        table_style="margin-bottom: 20px;"
                                    ) if 'intermediate_solution' in tables else ui.tags.div(),
                                    ui.tags.div(
                                        *[ui.tags.div(
                                            ui.tags.h4(f"{result['Drug']} Intermediate Solution",
                                                    style="color: #2980b9; margin-top: 15px; margin-bottom: 10px;"),
                                            ui.tags.ol(
                                                *( [ui.tags.li("Use polystyrene tubes (1.5ml or 5ml) as bedaquiline binds strongly to glass surfaces, which can cause loss of drug and inaccurate (lower) effective concentrations in solution.")] if result['Drug'] == "Bedaquiline (BDQ)" else [] ),
                                                ui.tags.li(f"Label a clean tube: '{result['Drug']} Intermediate Solution'"),
                                                *( [ui.tags.li("DMSO is light sensitive- Wrap the tube in foil or use a light-resistant tube to protect DMSO from degradation caused by light exposure.")] if result['Diluent'] == "DMSO" else [] ),
                                                ui.tags.li("Record solution details:",
                                                    ui.tags.ul(
                                                        ui.tags.li(f"Date: {datetime.now().strftime('%Y-%m-%d')}"),
                                                        ui.tags.li(f"Drug: {result['Drug']}"),
                                                        ui.tags.li(f"Diluent: {result['Diluent']}"),
                                                        ui.tags.li(f"Concentration: {result['Inter_Conc']:.2f} μg/ml"),
                                                        ui.tags.li(f"Dilution Factor: 1:{result['Inter_Factor']:.1f}"),
                                                        ui.tags.li(f"Initials")
                                                    )
                                                ),
                                                *(
                                                    [
                                                        ui.tags.li(f"Add {result['Stock_to_Inter']:.2f} ml (= {result['Stock_to_Inter_µl']:.2f} µl) of stock solution to a new clean tube"),
                                                        ui.tags.li(f"Add {result['Dil_to_Inter']:.2f} ml (= {result['Dil_to_Inter_µl']:.2f} µl) of {result['Diluent']} to the same tube")
                                                    ]
                                                ),
                                                ui.tags.li("Mix solution:",
                                                    ui.tags.ul(
                                                            ui.tags.li("For bedaquiline:",
                                                                ui.tags.ul(
                                                                    ui.tags.li("Close the tube securely"),
                                                                    ui.tags.li("Do not invert the tubes as bedaquiline may adhere to plastic surfaces"),
                                                                    ui.tags.li("If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes")
                                                                )
                                                            ) if result['Drug'] == "Bedaquiline (BDQ)" else [
                                                                ui.tags.li("Close the tube securely"),
                                                                ui.tags.li("Invert tube gently 2-4 times or vortex briefly"),
                                                                ui.tags.li("Do not shake vigorously to avoid foam formation"),
                                                                ui.tags.li("Check that drug powder is completely dissolved"),
                                                                ui.tags.li("Ensure no visible particles remain"),
                                                            ],
                                                    )
                                                ),
                                                style="color: #2c3e50;"
                                            ),
                                            style="background-color: #ebf5fb; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                        ) for result in intermediate_results]
                                    )
                                )
                            )

                        # Working Solution Instructions
                        section_title = "B. Working Solution Preparation" if not make_stock else "C. Working Solution Preparation"
                        instruction_sections.append(
                            ui.tags.div(
                                ui.tags.h3(section_title, 
                                         style="color: #2980b9; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #2980b9; padding-bottom: 5px;"),
                                # Add Working Solution tables based on conditions
                                create_html_table(
                                    tables.get('working_solution_intermediate', []),
                                    ['Drug', 'Diluent', 'Intermediate to\nAdd (ml)', 'Diluent to\nAdd(ml)', 'Volume WS\n(ml)', 'Conc. WS\n(μg/ml)'],
                                    table_style="margin-bottom: 20px;"
                                ) if 'working_solution_intermediate' in tables else ui.tags.div(),
                                create_html_table(
                                    tables.get('working_solution_stock', []),
                                    ['Drug', 'Diluent', 'Stock to\nAdd (ml)', 'Diluent to\nAdd(ml)', 'Volume WS\n(ml)', 'Conc. WS\n(μg/ml)'],
                                    table_style="margin-bottom: 20px;"
                                ) if 'working_solution_stock' in tables else ui.tags.div(),
                                create_html_table(
                                    tables.get('working_solution_no_stock', []),
                                    ['Drug', 'Diluent', 'Drug Weight\n(mg)', 'Diluent to\nAdd(ml)', 'Conc. WS\n(μg/ml)'],
                                    table_style="margin-bottom: 20px;"
                                ) if 'working_solution_no_stock' in tables else ui.tags.div(),
                                ui.tags.div(
                                    *[ui.tags.div(
                                        ui.tags.h4(f"{result['Drug']} Working Solution",
                                                style="color: #2980b9; margin-top: 15px; margin-bottom: 10px;"),
                                        ui.tags.ol(
                                            *( [ui.tags.li("Use polystyrene tubes (1.5ml or 5ml) as bedaquiline binds strongly to glass surfaces, which can cause loss of drug and inaccurate (lower) effective concentrations in solution.")] if result['Drug'] == "Bedaquiline (BDQ)" else [] ),
                                            ui.tags.li(f"Label a clean tube: '{result['Drug']} Working Solution'"),
                                            *( [ui.tags.li("DMSO is light sensitive- Wrap the tube in foil or use a light-resistant tube to protect DMSO from degradation caused by light exposure.")] if result['Diluent'] == "DMSO" else [] ),
                                            ui.tags.li("Record solution details:",
                                                ui.tags.ul(
                                                    ui.tags.li(f"Date: {datetime.now().strftime('%Y-%m-%d')}"),
                                                    ui.tags.li(f"Drug: {result['Drug']}"),
                                                    ui.tags.li(f"Diluent: {result['Diluent']}"),
                                                    ui.tags.li(f"Concentration: {result['Conc_Ws']:.2f} μg/ml"),
                                                    ui.tags.li(f"Initials")
                                                )
                                            ),
                                            *(
                                                [
                                                    ui.tags.li(f"Add {result['Stock_to_WS']:.2f} ml (= {result['Stock_to_WS_µl']:.2f} µl) of stock solution to a new clean tube"),
                                                    ui.tags.li(f"Add {result['Dil_to_WS']:.2f} ml (= {result['Dil_to_WS_µl']:.2f} µl) of {result['Diluent']} to the same tube")
                                                ] if make_stock and result['Intermediate'] == False else
                                                [
                                                    ui.tags.li(f"Add {result['Vol_Inter_to_WS']:.2f} ml (= {result['Vol_Inter_to_WS_µl']:.2f} µl) of intermediate solution to a new clean tube"),
                                                    ui.tags.li(f"Add {result['Dil_to_WS']:.2f} ml (= {result['Dil_to_WS_µl']:.2f} µl) of {result['Diluent']} to the same tube")
                                                ] if result['Intermediate'] == True and make_stock else
                                                [
                                                    ui.tags.li(f"Add the {result['Act_Weight']:.2f} mg weighed drug powder to a clean tube"),
                                                    ui.tags.li(f"Add {result['Final_Vol_Dil']:.2f} ml (= {result['Final_Vol_Dil_µl']:.2f} µl) of {result['Diluent']} to the same tube")
                                                ] if not make_stock and result['Intermediate'] == False else []
                                            ),
                                            ui.tags.li("Mix solution:",
                                                ui.tags.ul(
                                                        ui.tags.li("For bedaquiline:",
                                                            ui.tags.ul(
                                                                ui.tags.li("Close the tube securely"),
                                                                ui.tags.li("Do not invert the tubes as bedaquiline may adhere to plastic surfaces"),
                                                                ui.tags.li("If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes")
                                                            )
                                                        ) if result['Drug'] == "Bedaquiline (BDQ)" else [
                                                            ui.tags.li("Close the tube securely"),
                                                            ui.tags.li("Invert tube gently 2-4 times or vortex briefly"),
                                                            ui.tags.li("Do not shake vigorously to avoid foam formation"),
                                                            ui.tags.li("Check that drug powder is completely dissolved"),
                                                            ui.tags.li("Ensure no visible particles remain"),
                                                        ],
                                                )
                                            ),
                                            style="color: #2c3e50;"
                                        ),
                                        style="background-color: #ebf5fb; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                    ) for i, result in enumerate(final_results)]
                                )
                            )
                        )

                        if make_stock:
                            # Aliquoting Instructions
                            instruction_sections.append(
                                ui.tags.div(
                                    ui.tags.h3("D. Aliquoting Remaining Stock", 
                                             style="color: #27ae60; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #27ae60; padding-bottom: 5px;"),
                                    # Add Aliquoting table
                                    create_html_table(
                                        tables.get('aliquoting', []),
                                        ['Drug', 'Number of\nAliquots', 'Volume per\nAliquot (ml)'],
                                        table_style="margin-bottom: 20px;"
                                    ) if 'aliquoting' in tables else ui.tags.div(),
                                    ui.tags.div(
                                        *[ui.tags.div(


                                            ui.tags.h4(f"{result['Drug']} Aliquots",
                                                    style="color: #27ae60; margin-top: 15px; margin-bottom: 10px;"),
                                            ui.tags.ol(
                                                ui.tags.li("Remaining stock solution:",
                                                    ui.tags.ul(
                                                        ui.tags.li(f"Total stock solution: {result['Total_Stock_Vol']:.1f} ml (= {result['Total_Stock_Vol_µl']:.2f} µl) "),
                                                        ui.tags.li(f"Used for working solution: {result['Stock_to_WS']:.2f} ml (= {result['Stock_to_WS_µl']:.2f} µl) "),
                                                        ui.tags.li(f"Remaining stock: {(result['Total_Stock_Left']):.2f} ml (= {result['Total_Stock_Left_µl']:.2f} µl) ")
                                                    ) if result['Intermediate'] == False else
                                                    ui.tags.ul(
                                                        ui.tags.li(f"Total stock solution: {result['Total_Stock_Vol']:.1f} ml (= {result['Total_Stock_Vol_µl']:.2f} µl) "),
                                                        ui.tags.li(f"Used for intermediate solution: {result['Stock_to_Inter']:.2f} ml (= {result['Stock_to_Inter_µl']:.2f} µl) "),
                                                        ui.tags.li(f"Remaining stock: {(result['Total_Stock_Left']):.2f} ml (= {result['Total_Stock_Left_µl']:.2f} µl) ")
                                                    )
                                                ),
                                                ui.tags.li(f"Prepare {result['Number_of_Ali']} sterile tubes"),
                                                ui.tags.li("Label each tube with:",
                                                    ui.tags.ul(
                                                        ui.tags.li(f"Drug name: {result['Drug']}"),
                                                        ui.tags.li("Stock solution"),
                                                        ui.tags.li(f"Volume: {result['ml_aliquot']:.1f} ml (= {result['ml_aliquot_µl']:.1f} µl)"),
                                                        ui.tags.li(f"Concentration: {result['Stock_Conc']:.2f} μg/ml"),
                                                        ui.tags.li(f"Dilution Factor: 1:{result['Stock_Factor']:.1f}"),
                                                        ui.tags.li(f"Date prepared: {datetime.now().strftime('%Y-%m-%d')}"),
                                                        ui.tags.li(f"Storage temperature: -20°C or -80°C"),
                                                        ui.tags.li(f"Expiry: {(datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')}"),
                                                        ui.tags.li(f"Initials")
                                                    )
                                                ),
                                                ui.tags.li(f"Dispense {result['ml_aliquot']:.1f} ml (= {result['ml_aliquot_µl']:.1f} µl) of remaining stock solution into each of the {result['Number_of_Ali']} tubes"),
                                                ui.tags.li("Close tubes tightly and check for proper sealing"),
                                                ui.tags.li("Storage instructions:",
                                                    ui.tags.ul(
                                                        ui.tags.li("Store aliquots at -20°C or -80°C"),
                                                        ui.tags.li("Valid for up to 6 months from preparation date"),
                                                        ui.tags.li("Avoid repeated freeze-thaw cycles")
                                                    )
                                                ),
                                                style="color: #2c3e50;"
                                            ),
                                            style="background-color: #e8f6f3; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                        ) for i, result in enumerate(final_results)]
                                    )
                                )
                            )

                        # MGIT Preparation Section
                        mgit_section_title = "C. MGIT Tube Preparation" if not make_stock else "E. MGIT Tube Preparation"
                        instruction_sections.append(
                            ui.tags.div(
                                ui.tags.h3(mgit_section_title, 
                                         style="color: #16a085; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #16a085; padding-bottom: 5px;"),
                                # Add MGIT Preparation table
                                create_html_table(
                                    tables.get('mgit_preparation', []),
                                    ['Drug', 'Number of\nMGITs', 'Volume WS\nper MGIT (ml)', 'Volume OADC\nper MGIT (ml)', 'Volume Culture\nper MGIT (ml)'],
                                    table_style="margin-bottom: 20px;"
                                ),
                                ui.tags.div(
                                    *[ui.tags.div(
                                        ui.tags.h4(f"{result['Drug']} MGIT Preparation",
                                                style="color: #16a085; margin-top: 15px; margin-bottom: 10px;"),
                                        ui.tags.ol(
                                            ui.tags.li(f"Label {result['MGIT_Tubes']} MGIT tubes with:",
                                                ui.tags.ul(
                                                    ui.tags.li(f"Drug name: {result['Drug']}"),
                                                    ui.tags.li(f"Critical concentration: {result['Crit_Conc']:.2f} μg/ml"),
                                                    ui.tags.li(f"Sample ID"),
                                                    ui.tags.li(f"Date: {datetime.now().strftime('%Y-%m-%d')}"),
                                                    ui.tags.li(f"Initials")
                                                )
                                            ),
                                            ui.tags.li("For each MGIT tube:",
                                                ui.tags.ul(
                                                    ui.tags.li("Pipette 0.1 ml (= 100 µl) of working solution"),
                                                    ui.tags.li("Add 0.8 ml (= 800 µl) of OADC (growth supplement)"),
                                                    ui.tags.li("Add 0.5 ml (= 500 µl) of culture")
                                                )
                                            ),
                                            ui.tags.li("After adding all components to each tube:",
                                                ui.tags.ul(
                                                        ui.tags.li("For bedaquiline:",
                                                            ui.tags.ul(
                                                                ui.tags.li("Close the tube securely"),
                                                                ui.tags.li("Check for proper sealing"),
                                                                ui.tags.li("Do not invert the tubes as bedaquiline may adhere to plastic surfaces"),
                                                                ui.tags.li("If crystal doesn't dissolve after 1 hour, use sonicator for ~3 minutes"),
                                                                ui.tags.li("Place in MGIT machine as soon as possible after adding culture")
                                                            )
                                                        ) if result['Drug'] == "Bedaquiline (BDQ)" else [
                                                            ui.tags.li("Close the tube securely"),
                                                            ui.tags.li("Check for proper sealing"),
                                                            ui.tags.li("Invert tube gently 2-4 times or vortex briefly"),
                                                            ui.tags.li("Do not shake vigorously to avoid foam formation"),
                                                            ui.tags.li("Check that drug powder is completely dissolved"),
                                                            ui.tags.li("Ensure no visible particles remain"),
                                                            ui.tags.li("Place in MGIT machine as soon as possible after adding culture")
                                                        ],
                                                )
                                            ),
                                            style="color: #2c3e50;"
                                        ),
                                        style="background-color: #e8f8f5; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                    ) for i, result in enumerate(final_results)]
                                )
                            )
                        )

                        # Quality Control Section
                        final_section_title = "E. Quality Control" if not make_stock else "F. Quality Control"
                        instruction_sections.append(
                            ui.tags.div(
                                ui.tags.h3(final_section_title, 
                                         style="color: #d35400; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #d35400; padding-bottom: 5px;"),
                                ui.tags.div(
                                    ui.tags.h4("Final Checks:",
                                            style="color: #d35400; margin-top: 15px; margin-bottom: 10px;"),
                                    ui.tags.ol(
                                        ui.tags.li("Verify all solutions are properly labeled"),
                                        ui.tags.li("Check all solutions for:",
                                            ui.tags.ul(
                                                ui.tags.li("Complete dissolution"),
                                                ui.tags.li("Absence of visible particles"),
                                                ui.tags.li("Proper volume measurement"),
                                                ui.tags.li("Correct labeling")
                                            )
                                        ),
                                        ui.tags.li("Document preparation in laboratory records"),
                                        ui.tags.li("Store solutions according to requirements:",
                                            ui.tags.ul(
                                                ui.tags.li("Stock solutions: Follow drug-specific storage instructions"),
                                                ui.tags.li("Working solutions: Use immediately for best results"),
                                                ui.tags.li("Aliquots: Store according to stability requirements")
                                            )
                                        ),
                                        style="color: #2c3e50;"
                                    ),
                                    style="background-color: #fef5e7; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                )
                            )
                        )

                        return ui.tags.div(
                            ui.tags.h2("Step 4: Solution Preparation Guide",
                                     style="color: #2c3e50; margin-bottom: 20px;"),
                            *instruction_sections,
                            ui.tags.div(
                                ui.tags.p("⚠️ Important: Follow all laboratory safety protocols and maintain aseptic technique throughout the procedure.",
                                       style="color: #e74c3c; margin-top: 20px; font-weight: bold;")
                            )
                        )

                    except Exception as e:
                        return ui.tags.div(f"Error generating instructions: {str(e)}", style="color: red;")
                    
            
            # Results section for step 2
            @render.ui
            def results_section():
                print(f"results_section called, show_results_view: {show_results_view()}, current_step: {current_step()}")
                
                # Try to get drugs from session first (for restored sessions)
                selected = []
                cs = current_session()
                if cs:
                    print(f"results_section: Getting drugs from session {cs['session_id']}")
                    try:
                        with db_manager.get_connection() as conn:
                            cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                            row = cur.fetchone()
                            if row and row[0]:
                                import json
                                preparation = json.loads(row[0])
                                selected = preparation.get('selected_drugs', [])
                                print(f"results_section: Got drugs from session: {selected}")
                    except Exception as e:
                        print(f"results_section: Error getting session data: {e}")
                
                # Fallback to input if no session data
                if not selected:
                    try:
                        selected = input.drug_selection()
                        print(f"results_section: Got selected drugs from input: {selected}")
                    except Exception as e:
                        # Handle SilentException - inputs not ready yet
                        print(f"results_section: SilentException - inputs not ready yet: {e}")
                        return ui.tags.h3()
                
                if not selected:
                    print("results_section: No selected drugs, returning empty div")
                    return ui.tags.div()
                    
                if current_step() == 2:
                    try:
                        purchased_mol_weights = []
                        custom_critical_values = []
                        mgit_tubes_values = []
                        drug_data = load_drug_data()
                        potency_method = potency_method_pref()
                        
                        for i, drug_name in enumerate(selected):
                            
                            # Get original molecular weight
                            org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                            
                            # Get purchased molecular weight (only if method requires it)
                            if potency_method in ["mol_weight", "both"]:
                                purch_molw = input[f"purchased_molw_{i}"]()
                                if purch_molw is None or purch_molw <= 0:
                                    return ui.tags.div("Please enter valid purchased molecular weights for all drugs.", style="color: green;")
                                elif purch_molw < org_molw:
                                    return ui.tags.div("Purchased molecular weight cannot be smaller than original molecular weight.", style="color: red;")
                                # Use g/mol directly
                                purch_molw_gmol = purch_molw
                            else:
                                # Use org_molw as default when not using mol_weight method
                                purch_molw_gmol = org_molw
                            purchased_mol_weights.append(purch_molw_gmol)
                            Step2_Purch[i] = purch_molw_gmol
                            
                            # Get MGIT tubes
                            mgit_tubes = input[f"mgit_tubes_{i}"]()
                            if mgit_tubes is None or mgit_tubes <= 0:
                                return ui.tags.div("Please enter valid MGIT tube counts for all drugs.", style="color: green;")
                            mgit_tubes_values.append(int(mgit_tubes))
                            Step2_MgitTubes[i] = int(mgit_tubes)
                            
                            # Get custom critical value
                            custom_crit = input[f"custom_critical_{i}"]()
                            if custom_crit is None or custom_crit <= 0:
                                return ui.tags.div("Please enter valid critical concentrations for all drugs.", style="color: green;")
                            # Use μg/ml directly
                            custom_crit_μgml = custom_crit
                            custom_critical_values.append(custom_crit_μgml)
                            Step2_CriticalConc[i] = custom_crit_μgml

                        # Calculate results (always when inputs valid)
                        results_data = []
                        estimated_weights = []  # step 2 main outputs
                        diluent_volumes = []    # step 2 main outputs
                        
                        for i, drug_name in enumerate(selected):
                            drug_row = drug_data[drug_data['Drug'] == drug_name]
                            if not drug_row.empty:
                                row_data = drug_row.iloc[0]
                                org_molw = row_data['OrgMolecular_Weight']

                                # [1] potency calculation - depends on selected method
                                potency_method = potency_method_pref()

                                if potency_method == "purity":
                                    # Potency from purity only: 1.0 / (purity / 100)
                                    try:
                                        purity_pct = input[f"purity_{i}"]()
                                        if purity_pct is None or purity_pct <= 0:
                                            return ui.tags.div("Please enter valid purity percentages for all drugs.", style="color: green;")
                                    except Exception:
                                        purity_pct = None
                                        
                                    try:
                                        pot = 1.0 / (purity_pct / 100.0)
                                    except Exception:
                                        pot = 1.0
                                    print(f"potency (purity) for idx={i}, purity_pct={purity_pct} -> pot={pot}")
                                elif potency_method == "both":
                                    try:
                                        purity_pct = input[f"purity_{i}"]()
                                        if purity_pct and purity_pct > 0:
                                            pot = (1.0 / (purity_pct / 100.0)) * (purchased_mol_weights[i] / org_molw)
                                        else:
                                            return ui.tags.div("Please enter valid purity percentages for all drugs.", style="color: green;")
                                    except Exception:
                                        pot = potency(purchased_mol_weights[i], org_molw)
                                else:
                                    # Traditional potency calculation from molecular weights
                                    pot = potency(purchased_mol_weights[i], org_molw)
                                
                                Step2_Potencies[i] = pot

                                # [5] conc_ws
                                ws_conc_ugml = conc_ws(custom_critical_values[i])
                                Step2_ConcWS[i] = ws_conc_ugml
                                # [6] vol_workingsol
                                vol_ws_ml = vol_workingsol(mgit_tubes_values[i])
                                Step2_VolWS[i] = vol_ws_ml
                                # [2] est_drugweight (new formula)
                                est_dw_mg = (ws_conc_ugml * vol_ws_ml * pot) / 1000.0
                                est_dw_user_unit = est_dw_mg
                                estimated_weights.append(est_dw_user_unit)
                                Step2_CalEstWeights[i] = est_dw_mg
                                # [3] vol_diluent (as vol_workingsol)
                                vol_dil_ml = vol_ws_ml
                                diluent_volumes.append(vol_dil_ml)

                                results_data.append({
                                    'Drug': drug_name,
                                    'Potency': f"{pot:.5f}",
                                    'Potency_num': pot,
                                    'Conc_WS(ug/ml)': f"{ws_conc_ugml:.4f}",
                                    'Conc_WS_ugml_num': ws_conc_ugml,
                                    'Vol_WS(ml)': f"{vol_ws_ml:.4f}",
                                    'Vol_WS_ml_num': vol_ws_ml,
                                    'Est_DrugWeight': est_dw_user_unit,
                                    'Est_DrugWeight_mg_num': est_dw_mg,
                                    'Vol_Diluent': diluent_volumes[-1]
                                })
                        
                        # Store step 2 outputs for step 3 and allow Next
                        calculation_results.set({'estimated_weights': estimated_weights, 'diluent_volumes': diluent_volumes})
                        calculate_clicked.set(True)

                        # Create results tables (split emphasis)
                        if results_data:
                                main_headers = ui.tags.tr(
                                    ui.tags.th("Drug", style="padding: 8px; border: 2px solid #3498db; background-color: #ebf5fb; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th("Potency", style="padding: 8px; border: 2px solid #3498db; background-color: #ebf5fb; font-weight: bold; font-size: 14px; width: 120px;"),
                                    ui.tags.th("Conc. of Working Solution (μg/ml)", style="padding: 8px; border: 2px solid #3498db; background-color: #ebf5fb; font-weight: bold; font-size: 14px; width: 180px;"),
                                    ui.tags.th("Total Volume of Working Solution (ml)", style="padding: 8px; border: 2px solid #3498db; background-color: #ebf5fb; font-weight: bold; font-size: 14px; width: 200px;"),
                                    style="background-color: #ebf5fb;"
                                )

                                emph_headers = ui.tags.tr(
                                    ui.tags.th("Drug", style="padding: 8px; border: 2px solid #27ae60; background-color: #eafaf1; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th(f"Calculated Drug Weight to Weigh Out ({weight_unit()})", style="padding: 8px; border: 2px solid #27ae60; background-color: #eafaf1; font-weight: bold; font-size: 14px; width: 220px;"),
                                    ui.tags.th(f"Volume of Diluent to Add ({volume_unit()})", style="padding: 8px; border: 2px solid #27ae60; background-color: #eafaf1; font-weight: bold; font-size: 14px; width: 200px;"),
                                    style="background-color: #eafaf1;"
                                )
                            
                                main_rows = []
                                emph_rows = []
                                for result in results_data:
                                    main_rows.append(
                                        ui.tags.tr(
                                            ui.tags.td(result['Drug'], style="padding: 8px; border: 2px solid #3498db; font-weight: bold; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Potency']), 4), style="padding: 8px; border: 2px solid #3498db; text-align: center; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Conc_WS(ug/ml)']), 2), style="padding: 8px; border: 2px solid #3498db; text-align: center; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Vol_WS(ml)']), 2), style="padding: 8px; border: 2px solid #3498db; text-align: center; font-size: 14px;"),
                                            style="background-color: #f8fbfe;"
                                        )
                                    )

                                    emph_rows.append(
                                        ui.tags.tr(
                                            ui.tags.td(result['Drug'], style="padding: 8px; border: 2px solid #27ae60; font-weight: bold; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Est_DrugWeight']), 4), style="padding: 8px; border: 2px solid #27ae60; text-align: center; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Vol_Diluent']), 4), style="padding: 8px; border: 2px solid #27ae60; text-align: center; font-size: 14px;"),
                                            style="background-color: #ffffff;"
                                        )
                                    )

                                # Determine if any drug has est weight < 3 mg
                                any_low_mass = any((r.get('Est_DrugWeight_mg_num') or 0) > 0 and r['Est_DrugWeight_mg_num'] < 3 for r in results_data)

                                # Build practical rows safely (avoid accessing inputs before they exist)
                                practical_rows = []
                                stock_rows = []
                                aliquot_summary_rows = []
                                stock_no_aliquot_rows = []
                                make_stock = False
                                # Calculate aliquot total volume safely and get current values
                                aliquot_total = "1.00"
                                num_aliq_val = 1
                                ml_per_aliq_val = 1.0
                                aliquot_total_num = 1.0

                                try:
                                    num_aliq_val = input.num_aliquots() if input.num_aliquots() else 1
                                    ml_per_aliq_val = input.ml_per_aliquot() if input.ml_per_aliquot() else 1.0
                                    aliquot_total_num = num_aliq_val * ml_per_aliq_val
                                    aliquot_total = f"{aliquot_total_num:.2f}"
                                except Exception:
                                    aliquot_total = "1.00"
                                    num_aliq_val = 1
                                    ml_per_aliq_val = 1.0
                                    aliquot_total_num = 1.0

                                # Validation messages
                                validation_messages = []
                                if any_low_mass:
                                    # Use persisted toggle state
                                    make_stock = bool(make_stock_pref())
                                    for idx, r in enumerate(results_data):
                                        # Default practical weight: 2.0 mg
                                        practical_val = 2.0
                                        try:
                                            v = input[f"practical_weight_{idx}"]()
                                            if v is not None and v > 0:
                                                practical_val = v
                                        except Exception:
                                            # Input not ready yet; keep default
                                            pass
                                        # Compute practical diluent volume: (x / est_dw_mg) * vol_ws_ml
                                        try:
                                            vol_needed_ml = ((practical_val or 0) / max(r['Est_DrugWeight_mg_num'], 1e-12)) * r['Vol_WS_ml_num']
                                        except Exception:
                                            vol_needed_ml = ""
                                        
                                        # Bedaquiline validation for no-stock solution case
                                        if not make_stock and r['Drug'] == "Bedaquiline (BDQ)":
                                            vol_ws_ml = r.get('Vol_WS_ml_num', 0)
                                            if vol_ws_ml > 5.0:
                                                validation_messages.append(
                                                    f"❌ {r['Drug']}: Working solution volume ({vol_ws_ml:.4f} ml) exceeds 5ml polystyrene tube limit.\nReduce the number of MGIT tubes to keep volume ≤ 5ml."
                                                )
                                        practical_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #f39c12; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    ui.input_numeric(
                                                        f"practical_weight_{idx}",
                                                        "",
                                                        value=practical_val,
                                                        min=0.001,
                                                        step=0.1
                                                    ),
                                                    style="padding: 5px; border: 2px solid #f39c12; width: 220px;"
                                                ),
                                                ui.tags.td(
                                                    f"{vol_needed_ml:.4f}" if isinstance(vol_needed_ml, (int, float)) else vol_needed_ml,
                                                    style="padding: 8px; border: 2px solid #f39c12; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )
                                        # If stock solution mode, also prepare a matching row with dilution factor
                                        try:
                                            a_val = input[f"dilution_factor_{idx}"]()
                                            if a_val is None or a_val <= 0:
                                                a_val = 2.0
                                        except Exception:
                                            a_val = 2.0
                                        
                                        # Calculate stock volume using the new formula:
                                        # Stock Volume = (conc_ws * vol_ws) / (conc_ws * dilution_factor)
                                        # Simplifies to: Stock Volume = vol_ws / dilution_factor
                                        ws_conc_ugml = r.get('Conc_WS_ugml_num', 0)
                                        vol_ws_ml = r.get('Vol_WS_ml_num', 0)
                                        try:
                                            stock_vol_ml = vol_ws_ml / a_val if a_val > 0 else 0
                                            # Diluent Volume = vol_ws - stock_volume
                                            diluent_vol_ml = vol_ws_ml - stock_vol_ml
                                        except Exception:
                                            stock_vol_ml = 0
                                            diluent_vol_ml = 0

                                        Step2_PracWeights[idx] = practical_val
                                        Step2_PracVol[idx] = vol_needed_ml

                                        Step2_StocktoWS[idx] = stock_vol_ml
                                        Step2_DiltoWS[idx] = diluent_vol_ml
                                        Step2_Factors[idx] = a_val

                                        stock_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #8e44ad; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    ui.input_numeric(
                                                        f"dilution_factor_{idx}",
                                                        "",
                                                        value=a_val,
                                                        min=1.1,
                                                        step=1
                                                    ),
                                                    style="padding: 5px; border: 2px solid #8e44ad; width: 200px;"
                                                ),
                                                ui.tags.td(
                                                    f"{stock_vol_ml:.4f}",
                                                    style="padding: 8px; border: 2px solid #8e44ad; text-align: center; font-size: 14px;"
                                                ),
                                                ui.tags.td(
                                                    f"{diluent_vol_ml:.4f}",
                                                    style="padding: 8px; border: 2px solid #8e44ad; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )
                                        
                                        # Build aliquot summary row for this drug
                                        # Total Stock Volume = (Volume of Stock)
                                        # Prefer per-drug inputs if present (num_aliquots_{idx}, ml_per_aliquot_{idx}),
                                        # otherwise fall back to the global aliquot_total_num computed earlier.
                                        try:
                                            num_aliq_idx = input[f"num_aliquots_{idx}"]()
                                            ml_per_aliq_idx = input[f"ml_per_aliquot_{idx}"]()
                                            if num_aliq_idx is None or num_aliq_idx <= 0:
                                                num_aliq_idx = 0
                                            if ml_per_aliq_idx is None or ml_per_aliq_idx <= 0:
                                                ml_per_aliq_idx = 0.0
                                            aliquot_total_num_idx = float(num_aliq_idx) * float(ml_per_aliq_idx)
                                        except Exception:
                                            # Inputs not ready or missing; use the previously computed global total
                                            aliquot_total_num_idx = aliquot_total_num
                                            ml_per_aliq_idx = 0.0  # Ensure this is always defined
                                            num_aliq_idx = 0  # Ensure this is always defined
                                        total_stock_vol = (aliquot_total_num_idx)

                                        Step2_mlperAliquot[idx] = float(ml_per_aliq_idx)
                                        Step2_num_aliquots[idx] = float(num_aliq_idx)
                                        Step2_TotalStockVolumes[idx] = total_stock_vol

                                        # Drug to weigh out = Total Stock Volume * conc_ws * dilution_factor * potency / 1000
                                        pot = r.get('Potency_num', 1.0)
                                        drug_to_weigh = (total_stock_vol * ws_conc_ugml * a_val * pot) / 1000
                                        if make_stock:
                                            Step2_EstWeights[idx] = drug_to_weigh

                                        # Validation logic depends on whether aliquots are being made
                                        if make_stock:
                                            # Validation 1: Check if drug to weigh out is less than 2 mg (WITH aliquots)
                                            if drug_to_weigh < 2.0:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Drug weight ({drug_to_weigh:.4f} mg) is less than 2 mg.\nConsider (1) increasing the number of aliquots, (2) increasing the volume per aliquot, or (3) increasing the stock concentration factor to achieve a practical weight."
                                                )
                                                # Validation 2: Check if stock volume is less than 250 microliters (0.25 ml) when aliquots are NOT being made
                                            if stock_vol_ml < 0.1:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Stock solution volume ({stock_vol_ml:.4f} ml = {stock_vol_ml * 1000:.1f} μl) might be too small to pipette.\nConsider (1) decreasing the stock concentration factor, or (2) increasing the volume of working solution by increasing the number of MGIT tubes.\nAlternatively, an intermediate dilution will be generated."
                                                )
                                            
                                            # Validation 3: Check Bedaquiline volume constraints (polystyrene tube limits)
                                            if r['Drug'] == "Bedaquiline (BDQ)":
                                                if total_stock_vol > 5.0:
                                                    validation_messages.append(
                                                        f"❌ {r['Drug']}: Total stock volume ({total_stock_vol:.4f} ml) exceeds 5ml polystyrene tube limit.\nReduce the stock concentration factor or number of aliquots tubes to keep volume ≤ 5ml."
                                                    )
                                                vol_ws_ml = r.get('Vol_WS_ml_num', 0)
                                                if vol_ws_ml > 5.0:
                                                    validation_messages.append(
                                                        f"❌ {r['Drug']}: Working solution volume ({vol_ws_ml:.4f} ml) exceeds 5ml polystyrene tube limit.\nReduce the number of MGIT tubes to keep volume ≤ 5ml."
                                                    )
                                        
                                        aliquot_summary_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #d35400; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    f"{total_stock_vol:.4f}",
                                                    style="padding: 8px; border: 2px solid #d35400; text-align: center; font-size: 14px;"
                                                ),
                                                ui.tags.td(
                                                    f"{drug_to_weigh:.4f}",
                                                    style="padding: 8px; border: 2px solid #d35400; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )

                                return ui.tags.div(
                                    ui.tags.h3("Calculations", style="color: #2c3e50; margin-top: 10px; margin-bottom: 15px;"),
                                    ui.tags.div(
                                        ui.tags.table(
                                            main_headers,
                                            *main_rows,
                                            style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                        ),
                                        style="overflow-x: auto; max-width: 100%;"
                                    ),
                                    ui.tags.h3("Working Solution Preparation", style="color: #27ae60; margin-top: 10px; margin-bottom: 10px;"),
                                    ui.tags.div(
                                        ui.tags.table(
                                            emph_headers,
                                            *emph_rows,
                                            style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                        ),
                                        style="overflow-x: auto; max-width: 100%;"
                                    ),
                                    # Practical scenario if any weight < 3 mg
                                    (
                                        ui.tags.div(
                                            # Toggle: Create Stock Solution vs No stock solution
                                            ui.tags.div(
                                                ui.input_switch("make_stock_toggle", "Create Stock Solution", value=make_stock_pref()),
                                                style="margin: 8px 0 12px;"
                                            ),
                                            (
                                                ui.tags.p(
                                                    "Note: The values above are the minimum required weight per drug based on the inputs. For practical weighing, 2 mg would be recommended, but this would in turn increase the diluent volume. Adjust the inputs below to help you decide on a practical outcome.",
                                                    style="color: #e67e22; margin: 10px 0; font-weight: 600;"
                                                )
                                            ) if not make_stock else ui.tags.div(),
                                            style="margin-bottom: 15px;"
                                        ),                                            
                                            # First show Aliquot Planning if making stock solution
                                            (ui.tags.div(
                                                ui.tags.h4("Stock Aliquot Planning", style="color: #008080; margin-top: 20px; margin-bottom: 10px;"),
                                                ui.tags.table(
                                                    ui.tags.thead(
                                                        ui.tags.tr(
                                                            ui.tags.th("Drug", style="padding: 8px; border: 2px solid #008080; background-color: #e0f2f1; font-weight: bold; font-size: 14px; width: 180px;"),
                                                            ui.tags.th("Number of Aliquots", style="padding: 8px; border: 2px solid #008080; background-color: #e0f2f1; font-weight: bold; font-size: 14px; width: 180px;"),
                                                            ui.tags.th(f"Volume per Aliquot ({volume_unit()})", style="padding: 8px; border: 2px solid #008080; background-color: #e0f2f1; font-weight: bold; font-size: 14px; width: 180px;"),
                                                            ui.tags.th(f"Total Aliquot Volume ({volume_unit()})", style="padding: 8px; border: 2px solid #008080; background-color: #e0f2f1; font-weight: bold; font-size: 14px; width: 200px;"),
                                                        )
                                                    ),
                                                    *[
                                                        (lambda idx, r: ui.tags.tr(
                                                            ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #008080; font-weight: bold; font-size: 14px;"),
                                                            ui.tags.td(
                                                                ui.input_numeric(
                                                                    f"num_aliquots_{idx}",
                                                                    None,
                                                                    value=(input[f"num_aliquots_{idx}"]() if (f"num_aliquots_{idx}" in input and callable(input[f"num_aliquots_{idx}"])) else num_aliq_val),
                                                                    min=1,
                                                                    step=1
                                                                ),
                                                                style="padding: 8px; border: 2px solid #008080;"
                                                            ),
                                                            ui.tags.td(
                                                                ui.input_numeric(
                                                                    f"ml_per_aliquot_{idx}",
                                                                    None,
                                                                    value=(input[f"ml_per_aliquots_{idx}"]() if False else (input[f"ml_per_aliquot_{idx}"]() if (f"ml_per_aliquot_{idx}" in input and callable(input[f"ml_per_aliquot_{idx}"])) else ml_per_aliq_val)),
                                                                    min=0.5,
                                                                    step=0.5
                                                                ),
                                                                style="padding: 8px; border: 2px solid #008080;"
                                                            ),
                                                            ui.tags.td(
                                                                (lambda ii=idx: (
                                                                    (lambda: (  # compute total safely
                                                                        (input[f"num_aliquots_{ii}"]() if (f"num_aliquots_{ii}" in input and callable(input[f"num_aliquots_{ii}"])) and input[f"num_aliquots_{ii}"]() is not None else num_aliq_val) *
                                                                        (input[f"ml_per_aliquot_{ii}"]() if (f"ml_per_aliquot_{ii}" in input and callable(input[f"ml_per_aliquot_{ii}"])) and input[f"ml_per_aliquot_{ii}"]() is not None else ml_per_aliq_val)
                                                                    ))()
                                                                ))(),
                                                                style="padding: 8px; border: 2px solid #008080; text-align: center; font-weight: bold; font-size: 14px;"
                                                            ),
                                                        ))(idx, r) for idx, r in enumerate(results_data)
                                                    ],
                                                    style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                                )
                                            )) if make_stock else ui.tags.div(),

                                            # Then show Stock Solution Planning table
                                            ui.tags.table(
                                                (
                                                    ui.tags.tr(
                                                        ui.tags.th("Drug", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 180px;"),
                                                        ui.tags.th("Weight to Weigh Out (mg)", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 180px;"),
                                                        ui.tags.th(f"Volume of Diluent Needed ({volume_unit()})", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 200px;"),
                                                    ) if not make_stock else (
                                                        ui.tags.h3("Stock Solution Planning", style="color: #8e44ad; margin-top: 10px; margin-bottom: 10px;"),
                                                        ui.tags.thead(
                                                            ui.tags.tr(
                                                                ui.tags.th("Drug", style="padding: 8px; border: 2px solid #8e44ad; background-color: #f5eef8; font-weight: bold; font-size: 14px; width: 180px; border-bottom: none;", rowspan="2"),
                                                                ui.tags.th("Stock Concentration Factor", style="padding: 8px; border: 2px solid #8e44ad; background-color: #f5eef8; font-weight: bold; font-size: 14px; width: 200px; border-bottom: none;", rowspan="2"),
                                                                ui.tags.th("Working Solution Make Up", style="padding: 8px; border: 2px solid #8e44ad; background-color: #f5eef8; font-weight: bold; font-size: 14px; text-align: center;", colspan="2"),
                                                            ),
                                                            ui.tags.tr(
                                                                ui.tags.th(f"Volume of Stock ({volume_unit()})", style="padding: 8px; border: 2px solid #8e44ad; background-color: #f5eef8; font-weight: bold; font-size: 14px; width: 150px;"),
                                                                ui.tags.th(f"Volume Diluent ({volume_unit()})", style="padding: 8px; border: 2px solid #8e44ad; background-color: #f5eef8; font-weight: bold; font-size: 14px; width: 150px;"),
                                                            )
                                                        )
                                                    )
                                                ),
                                                *(practical_rows if not make_stock else stock_rows),
                                                style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                            ),
                                            (
                                                ui.tags.div(
                                                    (
                                                        ui.tags.div(
                                                            ui.tags.h4("Stock Solution Preparation", style="color: #d35400; margin-top: 20px; margin-bottom: 10px;"),
                                                            ui.tags.table(
                                                                ui.tags.tr(
                                                                    ui.tags.th("Drug", style="padding: 8px; border: 2px solid #d35400; background-color: #fdf2e9; font-weight: bold; font-size: 14px; width: 200px;"),
                                                                    ui.tags.th(f"Total Stock Volume ({volume_unit()})", style="padding: 8px; border: 2px solid #d35400; background-color: #fdf2e9; font-weight: bold; font-size: 14px; width: 250px;"),
                                                                    ui.tags.th("Drug to Weigh Out (mg)", style="padding: 8px; border: 2px solid #d35400; background-color: #fdf2e9; font-weight: bold; font-size: 14px; width: 200px;"),
                                                                ),
                                                                *aliquot_summary_rows,
                                                                style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                                            ),
                                                            # Display validation messages if any
                                                            (
                                                                ui.tags.div(
                                                                    *[ui.tags.p(msg, style="color: #000000; margin: 5px 0; padding: 10px; background-color: #fff3cd; border-left: 4px solid #e67e22; border-radius: 4px; font-size: 14px;") for msg in validation_messages],
                                                                    style="margin-top: 15px;"
                                                                )
                                                            ) if validation_messages else ui.tags.div()
                                                        )
                                                    ) if make_stock else ui.tags.div()
                                                )
                                            ) if (make_stock) else ui.tags.div(),
                                        ) if any_low_mass else ui.tags.div(),
                                    ui.tags.h3("Proper Weighing Practices", 
                                             style="color: #8e44ad; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid #8e44ad; padding-bottom: 5px;"),
                                    ui.tags.div(
                                        ui.tags.ol(
                                            ui.tags.li("Ensure analytical balance is properly calibrated and leveled"),
                                            ui.tags.li("Use appropriate weighing containers:",
                                                ui.tags.ul(
                                                    ui.tags.li("Clean, dry weighing boats or papers"),
                                                    ui.tags.li("Anti-static weighing boats for fine powders"),
                                                    ui.tags.li("Tared containers when necessary")
                                                )
                                            ),
                                            ui.tags.li("Record weights immediately and accurately"),
                                            ui.tags.li("For hygroscopic drugs, weigh quickly to minimize moisture absorption"),
                                            ui.tags.li("Clean balance and work area after each use"),
                                            style="color: #2c3e50;"
                                        ),
                                        style="background-color: #f5eef8; padding: 20px; border-radius: 5px; margin-bottom: 20px;"
                                    ),
                                    ui.tags.p(
                                                    "User Action:\nWeigh out the drug according to above values, return to session and proceed to step 3. Then enter the actual drug weights.",
                                                    style="color: #8e44ad; margin: 10px 0; font-weight: 600;"
                                                )
                                )
                        
                    except Exception as e:
                        return ui.tags.div(f"Error in calculation: {str(e)}")
                
                elif current_step() == 3:
                    print("results_section: Processing step 3")
                    # Show final results with warnings only after calculation is performed
                    warning_list = warnings()
                    if warning_list:
                        warning_ui = ui.tags.div(
                            ui.tags.h4("⚠️ Warnings Detected", style="color: #e74c3c; margin-bottom: 15px;"),
                            *[ui.tags.p(warning, style="color: #000000; margin-bottom: 10px; padding: 10px; background-color: #fdf2f2; border-left: 4px solid #e74c3c; border-radius: 4px; white-space: pre-wrap;") for warning in warning_list],
                            style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px;"
                        )
                    else:
                        warning_ui = ui.tags.div()
                
                return ui.tags.div()
            
            # Function to validate all inputs
            def validate_inputs():
                selected = input.drug_selection()
                if not selected:
                    return False
                try:
                    drug_data = load_drug_data()
                    potency_method = potency_method_pref()
                    
                    for i, drug_name in enumerate(selected):
                        # Original molecular weight
                        org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                        
                        # Validate based on potency method
                        if potency_method in ["mol_weight", "both"]:
                            # Purchased molecular weight (g/mol)
                            purch_molw = input[f"purchased_molw_{i}"]()
                            if purch_molw is None or purch_molw <= 0 or purch_molw < org_molw:
                                return False
                        
                        if potency_method in ["purity", "both"]:
                            # Purity percentage
                            purity = input[f"purity_{i}"]()
                            if purity is None or purity <= 0 or purity > 100:
                                return False
                        
                        # Critical concentration (mg/ml)
                        try:
                            custom_crit = input[f"custom_critical_{i}"]()
                        except Exception:
                            custom_crit = None
                        if custom_crit is None:
                            default_crit = drug_data[drug_data['Drug'] == drug_name]['Critical_Concentration'].iloc[0]
                            custom_crit = default_crit
                        if custom_crit <= 0:
                            return False
                        # MGIT tubes
                        mgit_tubes = input[f"mgit_tubes_{i}"]()
                        if mgit_tubes is None or mgit_tubes <= 0:
                            return False
                    return True
                except Exception:
                    return False

            def validate_step3_inputs():
                """Validate that all actual weights and MGIT tubes have been entered."""
                try:
                    # Try to get drugs from session first (for restored sessions)
                    selected = []
                    cs = current_session()
                    if cs:
                        print(f"validate_step3_inputs: Getting drugs from session {cs['session_id']}")
                        try:
                            with db_manager.get_connection() as conn:
                                cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                                row = cur.fetchone()
                                if row and row[0]:
                                    import json
                                    preparation = json.loads(row[0])
                                    selected = preparation.get('selected_drugs', [])
                                    print(f"validate_step3_inputs: Got drugs from session: {selected}")
                        except Exception as e:
                            print(f"validate_step3_inputs: Error getting session data: {e}")
                    
                    # Fallback to input if no session data
                    if not selected:
                        try:
                            selected = input.drug_selection()
                            print(f"validate_step3_inputs: Got selected drugs from input: {selected}")
                        except Exception as e:
                            # Handle SilentException - inputs not ready yet
                            print(f"validate_step3_inputs: SilentException - inputs not ready yet: {e}")
                            return False
                    
                    if not selected:
                        print("validate_step3_inputs: No selected drugs")
                        return False
                    
                    print(f"validate_step3_inputs: Checking {len(selected)} drugs")
                    
                    # Check if input fields exist before trying to access them
                    for i in range(len(selected)):
                        try:
                            actual_weight = input[f"actual_weight_{i}"]()
                            Step3_ActDrugWeights[i] = actual_weight
                            print(f"validate_step3_inputs: Drug {i} - actual_weight: {actual_weight}")
                            
                            if actual_weight is None or actual_weight <= 0:
                                print(f"validate_step3_inputs: Drug {i} validation failed - actual weight too low or missing")
                                return False
                            
                        except KeyError as e:
                            print(f"validate_step3_inputs: Drug {i} input field does not exist yet: {e}")
                            return False
                        except Exception as e:
                            print(f"validate_step3_inputs: Drug {i} input error: {e}")
                            return False
                    
                    print("validate_step3_inputs: All inputs valid!")
                    return True
                except Exception as e:
                    # Handle SilentException - this means inputs are not ready yet
                    if "SilentException" in str(type(e)):
                        print("validate_step3_inputs: Inputs not ready yet (SilentException)")
                        return False
                    else:
                        print(f"validate_step3_inputs: General error: {e}")
                        print(f"validate_step3_inputs: Error type: {type(e)}")
                        import traceback
                        print(f"validate_step3_inputs: Traceback: {traceback.format_exc()}")
                        return False


            # Action buttons
            @render.ui
            def action_buttons():
                print(f"action_buttons called, show_results_view: {show_results_view()}, current_step: {current_step()}")
                # Hide buttons when viewing results
                if show_results_view():
                    print("Returning empty div (hiding action buttons)")
                    return ui.tags.div()
                
                if current_step() == 1:
                    return ui.tags.div(
                        ui.input_action_button("next_btn", "Next", class_="btn-primary", style="background-color: #3498db; border-color: #3498db; margin-right: 10px;"),
                        ui.input_action_button("reset_btn", "Reset", class_="btn-secondary"),
                        style="text-align: center; margin-top: 30px;"
                    )
                elif current_step() == 2:
                    print("Step 2 action buttons logic")
                    # Check if this is a restored session (has session data)
                    cs = current_session()
                    is_restored_session = cs is not None
                    print(f"is_restored_session: {is_restored_session}, calculate_clicked: {calculate_clicked()}")
                    
                    # For restored sessions, skip validation and show Next button directly
                    if is_restored_session:
                        print("Restored session - showing Next button directly")
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back to Account", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("next_btn", "Continue to Step 3", class_="btn-primary", style="background-color: #3498db; border-color: #3498db;"),
                            style="text-align: center; margin-top: 30px;"
                        )
                    
                    # For new sessions, validate inputs
                    if validate_inputs():
                        print("Inputs are valid")
                        if calculate_clicked():
                            print("Showing Next button (calculation done)")
                            # Show Next button and download button after calculation
                            return ui.tags.div(
                                ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                                ui.input_action_button("download_step2_btn", "Download PDF", class_="btn-info", style="background-color: #17a2b8; border-color: #17a2b8; margin-right: 10px;"),
                                ui.input_action_button("next_btn", "Next", class_="btn-primary", style="background-color: #3498db; border-color: #3498db;"),
                                style="text-align: center; margin-top: 30px;"
                            )
                        else:
                            print("Showing Calculate button")
                            # Show Calculate button initially
                            return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                                ui.input_action_button("calculate_btn", "Calculate", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                            )
                    else:
                        print("Inputs not valid, showing only back button")
                        # Show only back button if validation fails
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary"),
                            style="text-align: center; margin-top: 30px;"
                        )
                elif current_step() == 3:
                    print("Step 3 action buttons logic")
                    
                    # Validate step 3 inputs
                    if validate_step3_inputs():
                        print("Step 3 inputs valid - showing Calculate Final Results button")
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("calculate_final_btn", "Calculate Final Results", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                        )
                    elif validate_step3_inputs():
                        print("Step 3 inputs valid - showing Calculate Final Results button")
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("calculate_final_btn", "Calculate Final Results", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
                            style="text-align: center; margin-top: 30px;"
                        )
                    else:
                        print("Step 3 inputs not valid - showing only Back button")
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary"),
                            style="text-align: center; margin-top: 30px;"
                        )
                elif current_step() == 4:
                    print("Step 4 action buttons logic")
                    # Show Download and Reset buttons
                    return ui.tags.div(
                        ui.input_action_button("download_step4_btn", "Download PDF", class_="btn-info", style="background-color: #17a2b8; border-color: #17a2b8; margin-right: 10px;"),
                        ui.input_action_button("reset_btn", "Start New Calculation", class_="btn-warning", style="background-color: #f39c12; border-color: #f39c12;"),
                        style="text-align: center; margin-top: 30px;"
                    )
                else:
                    return ui.tags.div()

    with ui.nav_panel("Education & Help"):
        ui.tags.div(
            ui.tags.div(
                ui.tags.h3("About This Tool", style="color: #34495e; margin-bottom: 15px;"),
                ui.tags.p(
                    "The pDST Calculator is designed to assist laboratory professionals in calculating accurate drug concentrations "
                    "for Phenotypic Drug Susceptibility Testing (pDST) of Mycobacterium Tuberculosis. This tool follows WHO guidelines and "
                    "international standards (e.g., CLSI, EUCAST) to ensure reliable and reproducible results.",
                    style="margin-bottom: 20px; line-height: 1.6;"
                ),
                
                ui.tags.h3("Key Definitions in Drug Susceptibility Testing (DST)", style="color: #34495e; margin-bottom: 15px;"),
                ui.tags.p(
                    "The following table provides essential definitions adapted from WHO, CLSI, and EUCAST guidelines:",
                    style="margin-bottom: 15px; line-height: 1.6;"
                ),
                
                # Comprehensive definitions table
                ui.tags.div(
                    ui.tags.table(
                        ui.tags.thead(
                            ui.tags.tr(
                                ui.tags.th("Term", style="background-color: #3498db; color: white; padding: 12px; border: 1px solid #ddd; font-weight: bold;"),
                                ui.tags.th("Definition (adapted from WHO, CLSI, EUCAST)", style="background-color: #3498db; color: white; padding: 12px; border: 1px solid #ddd; font-weight: bold;"),
                                ui.tags.th("Reference", style="background-color: #3498db; color: white; padding: 12px; border: 1px solid #ddd; font-weight: bold;")
                            )
                        ),
                        ui.tags.tbody(
                            ui.tags.tr(
                                ui.tags.td("Borderline result", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A DST result that falls close to the defined breakpoint or critical concentration, where technical variability may influence interpretation (e.g., between \"susceptible\" and \"resistant\"). Such results should be repeated or confirmed using another method (e.g., sequencing or a repeat MIC test).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Clinical breakpoint", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The concentration of an anti-TB drug that separates strains likely to respond to treatment from those likely not to respond. It integrates clinical outcome data, MIC distributions, PK/PD parameters, and dosing information. When resistance can be overcome by increasing the dose up to the maximum tolerated level, a higher clinical breakpoint may be defined. Clinical breakpoints guide individual treatment decisions and are not used for resistance surveillance.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023); CLSI M23 (2022)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Clinical concentration", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The amount of drug per defined volume of body fluid, often expressed as mass per mL of plasma or serum.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Critical concentration", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The lowest concentration of an anti-TB drug that inhibits ≥99% (or 90% for pyrazinamide) of phenotypically wild-type M. tuberculosis strains in vitro. It is primarily used for surveillance and DST standardization, not clinical decision-making.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Dilution or conversion factor", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A numerical factor used to convert between concentrations or dilutions of a drug when preparing DST stock or working solutions (e.g., converting µg/mL to mg/mL or preparing serial twofold dilutions).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Drug – potency factor", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A correction factor representing the drug's true biological activity relative to its weight. The potency factor (e.g., 0.95 µg active/mg powder) is used when calculating the amount to weigh for accurate drug concentrations.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Drug – purity", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The percentage of material that is the active compound, free from impurities or contaminants. Purity ensures accurate and reliable DST results.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Drug resistance evolution", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The gradual emergence and selection of genetic mutations or adaptive mechanisms in M. tuberculosis that reduce susceptibility to anti-TB drugs, often accelerated by inadequate or incomplete treatment.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Global TB Report (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Drug", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Any chemical substance that affects biological functions of living organisms or pathogens. In DST, \"drug\" refers to anti-TB agents used to inhibit M. tuberculosis growth.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("Britannica, \"Drug – chemical agent\"; WHO TB Glossary", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("ECOFF", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The epidemiological cut-off value (ECOFF) corresponds to the highest MIC defining the phenotypically wild-type (pWT) population. Isolates with MICs above the ECOFF are considered non-wild type (pNWT) and may harbor resistance mechanisms.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023); EUCAST (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Heteroresistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The presence of subpopulations within a clonal bacterial isolate that show differing levels of susceptibility to the same antimicrobial agent. It represents an early or mixed stage of resistance development.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("ScienceDirect (2022)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("High-level resistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Resistance where the MIC is substantially above achievable serum concentrations, indicating that even high drug doses cannot overcome it.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("CLSI M23 (2022); WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Indeterminate result", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A DST result that cannot be confidently classified as susceptible or resistant due to technical issues (e.g., contamination, growth failure, or borderline MIC). Repeat testing is required.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Intermediate resistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("An MIC that falls between susceptible and resistant categories, suggesting reduced sensitivity. Clinical outcome may depend on exposure or dose adjustment.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("CLSI M23 (2022); EUCAST (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Low-level resistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Resistance characterized by MICs slightly above the susceptible range, often linked to minimal inhibitory mutations that may still be overcome by higher doses.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("Baquero F., Drug Resistance Updates (2001)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Minimum inhibitory concentration (MIC)", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The lowest concentration of an antimicrobial agent that prevents visible growth of ≥99% of bacteria in vitro. MIC defines susceptibility levels and underpins breakpoint and ECOFF definitions.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Monoresistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Resistance to a single first-line anti-TB drug while remaining susceptible to all others.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Global TB Programme", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Control", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A standard sample used in DST to verify that test conditions and reagents are performing correctly. Includes positive controls (known resistant strain) and negative controls (susceptible strain, e.g., H37Rv).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Negative control", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A drug-free condition designed to confirm the expected absence of inhibition, ensuring that observed inhibition is due to the drug rather than technical error. In M. tuberculosis DST, this is typically the drug-free control containing the reference strain (H37Rv).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023); CLSI M24 (2021); EUCAST MIC Methods (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Positive control", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A culture or sample known to show a resistant or inhibited growth outcome under test conditions. Used to verify that the assay can detect true resistance or inhibition. In M. tuberculosis DST, this typically involves a strain with a known resistance mutation (e.g., rpoB S450L for rifampicin).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023); CLSI M24 (2021); EUCAST MIC Methods (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Potency", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The biological activity or strength of an antimicrobial agent per unit weight. Laboratories must standardize drug solutions based on the potency of the specific lot, considering purity, water content, and salt form. Potency may be expressed as a percentage or in µg per mg (w/w).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("WHO Technical Manual for DST (2023)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Purity", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("The extent to which a substance is free from contaminants or inactive material, typically expressed as a percentage. High purity ensures reproducibility and accuracy in DST.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("ScienceDirect – Purity (Chemistry)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Resistant", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A category defined by an MIC or zone diameter indicating that therapeutic success is unlikely at normal or increased drug exposure, usually due to resistance mechanisms.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("CLSI M23 (2022)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Resistance", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A microorganism is categorized as \"Resistant\" when there is a high likelihood of therapeutic failure even with increased drug exposure.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("EUCAST (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Susceptible", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("A category defined by an MIC or zone diameter indicating that isolates are inhibited by drug concentrations achievable with the standard treatment regimen, predicting therapeutic success.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("CLSI M23 (2022)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Susceptible, standard dosing regimen", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Indicates a high likelihood of therapeutic success when the standard dosing regimen is used.", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("EUCAST (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            ),
                            ui.tags.tr(
                                ui.tags.td("Susceptible, increased exposure", style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f8f9fa;"),
                                ui.tags.td("Indicates a high likelihood of therapeutic success when exposure to the agent is increased (e.g., by higher dose or increased drug concentration at the infection site).", style="padding: 10px; border: 1px solid #ddd; line-height: 1.5;"),
                                ui.tags.td("EUCAST (2024)", style="padding: 10px; border: 1px solid #ddd; font-size: 0.9em;")
                            )
                        ),
                        style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 0.95em;"
                    ),
                    style="overflow-x: auto; margin-bottom: 30px;"
                ),
                
                # DST and Culture Media Section
                ui.tags.h3("Overview of Drug Susceptibility Testing (DST)", 
                          style="color: #2c3e50; margin: 40px 0 20px 0; font-size: 1.4em; border-bottom: 2px solid #3498db; padding-bottom: 10px;"),
                    
                    ui.tags.div(
                        ui.tags.h5("Definition", style="color: #7f8c8d; margin: 20px 0 10px 0; font-weight: bold;"),
                        ui.tags.p(
                            "Drug Susceptibility Testing (DST) determines whether a Mycobacterium tuberculosis isolate is susceptible, "
                            "intermediate, or resistant to one or more anti-TB agents. Testing can be performed using either solid or "
                            "liquid culture systems and interpreted according to established critical concentrations or minimum inhibitory "
                            "concentration (MIC) thresholds.",
                            style="margin-bottom: 15px; line-height: 1.6; text-align: justify;"
                        ),
                        
                        ui.tags.div(
                            ui.tags.strong("References:", style="color: #2c3e50;"),
                            ui.tags.ul(
                                ui.tags.li("WHO. Technical Manual for Drug Susceptibility Testing of Medicines Used in the Treatment of Tuberculosis (2023)"),
                                ui.tags.li("CLSI M24 (2021)"),
                                style="margin: 10px 0; padding-left: 20px;"
                            ),
                            style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0;"
                        ),
                        
                        ui.tags.div(
                            ui.tags.strong("Illustration Example:", style="color: #e67e22;"),
                            ui.tags.p(
                                "A schematic showing M. tuberculosis inoculated in tubes or wells with increasing drug concentrations. "
                                "Visible growth indicates resistance, while no growth indicates susceptibility.",
                                style="margin: 10px 0; font-style: italic;"
                            ),
                            style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0;"
                        )
                    )
                ),

                ui.tags.h3("Culture Media for Mycobacterium tuberculosis", 
                          style="color: #2c3e50; margin: 40px 0 20px 0; font-size: 1.4em; border-bottom: 2px solid #3498db; padding-bottom: 10px;"),
                ui.tags.div(
                    ui.tags.h4("Overview of Culture Media", style="color: #34495e; margin: 30px 0 15px 0; font-size: 1.2em;"),
                    ui.tags.p(
                        "Culture media are essential for the growth and maintenance of Mycobacterium tuberculosis in the laboratory. "
                        "They provide the necessary nutrients and environmental conditions for the bacteria to thrive.",
                        style="margin-bottom: 15px; line-height: 1.6; text-align: justify;"
                    )
                ),
                ui.tags.div(
                    ui.tags.h4("DST by Culture System", style="color: #34495e; margin: 30px 0 15px 0; font-size: 1.2em;"),
                    
                    ui.tags.div(
                        ui.tags.h5("1) DST in Liquid Media", style="color: #27ae60; margin: 25px 0 15px 0; font-size: 1.1em; font-weight: bold;"),
                        
                        ui.tags.div(
                            ui.tags.h6("Definition", style="color: #7f8c8d; margin: 15px 0 10px 0; font-weight: bold;"),
                            ui.tags.p(
                                "Liquid culture systems detect bacterial growth in a nutrient broth through changes in fluorescence, "
                                "turbidity, or oxygen consumption. These systems provide faster results (typically 7–14 days) and allow "
                                "quantitative MIC determination.",
                                style="margin-bottom: 15px; line-height: 1.6; text-align: justify;"
                            ),
                            
                            ui.tags.div(
                                ui.tags.strong("References:", style="color: #2c3e50;"),
                                ui.tags.p("WHO Technical Manual for DST (2023); CLSI M24 (2021)", style="margin: 5px 0;"),
                                style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #27ae60; margin: 15px 0;"
                            ),
                            
                            ui.tags.div(
                                ui.tags.strong("Illustration Example:", style="color: #e67e22;"),
                                ui.tags.p(
                                    "A MGIT tube or growth curve showing fluorescence in the control (growth) and none in drug-containing "
                                    "tubes (no growth = susceptible).",
                                    style="margin: 10px 0; font-style: italic;"
                                ),
                                style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0;"
                            )
                        ),
                        
                        # Common Liquid Media Systems
                        ui.tags.div(
                            ui.tags.h6("Common Liquid Media Systems", style="color: #2980b9; margin: 20px 0 15px 0; font-weight: bold;"),
                            
                            # MGIT
                            ui.tags.div(
                                ui.tags.h6("a. MGIT (Mycobacteria Growth Indicator Tube)", style="color: #8e44ad; margin: 15px 0 10px 0; font-weight: bold;"),
                                ui.tags.p(
                                    "MGIT is a liquid-based culture system that measures oxygen consumption via a fluorescent sensor. "
                                    "It is widely used for both culture and DST of M. tuberculosis.",
                                    style="margin-bottom: 10px; line-height: 1.6; text-align: justify;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Reference: "), "WHO Endorsed MGIT 960 System; CLSI M24 (2021)",
                                    style="font-size: 0.9em; color: #666; margin-bottom: 10px;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Example: ", style="color: #d35400;"),
                                    "For rifampicin DST, the reference strain H37Rv shows no growth in the drug-containing MGIT "
                                    "(critical concentration 1 µg/mL), but visible growth in the drug-free control tube.",
                                    style="background-color: #fdf2e9; padding: 10px; border-radius: 5px; margin: 10px 0; font-style: italic;"
                                ),
                                style="margin-left: 20px; margin-bottom: 20px;"
                            ),
                            
                            # Middlebrook 7H9
                            ui.tags.div(
                                ui.tags.h6("b. Middlebrook 7H9 Broth", style="color: #8e44ad; margin: 15px 0 10px 0; font-weight: bold;"),
                                ui.tags.p(
                                    "7H9 is a nutrient-rich liquid medium supplemented with OADC and Tween 80 to support M. tuberculosis growth. "
                                    "It is commonly used for MIC testing in 96-well microdilution plates.",
                                    style="margin-bottom: 10px; line-height: 1.6; text-align: justify;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Reference: "), "WHO Technical Manual for DST (2023)",
                                    style="font-size: 0.9em; color: #666; margin-bottom: 10px;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Example: ", style="color: #d35400;"),
                                    "Used in MIC plates to determine the inhibitory concentration of bedaquiline.",
                                    style="background-color: #fdf2e9; padding: 10px; border-radius: 5px; margin: 10px 0; font-style: italic;"
                                ),
                                style="margin-left: 20px; margin-bottom: 20px;"
                            )
                        )
                    ),
                    
                    ui.tags.div(
                        ui.tags.h5("2) DST in Solid Media", style="color: #27ae60; margin: 25px 0 15px 0; font-size: 1.1em; font-weight: bold;"),
                        
                        ui.tags.div(
                            ui.tags.h6("Definition", style="color: #7f8c8d; margin: 15px 0 10px 0; font-weight: bold;"),
                            ui.tags.p(
                                "Solid media DST measures growth of M. tuberculosis colonies on agar- or egg-based media containing defined "
                                "drug concentrations. Though slower (up to 6–8 weeks), it allows direct visual observation and confirmatory testing.",
                                style="margin-bottom: 15px; line-height: 1.6; text-align: justify;"
                            ),
                            
                            ui.tags.div(
                                ui.tags.strong("References:", style="color: #2c3e50;"),
                                ui.tags.p("WHO Technical Manual for DST (2023); CLSI M24 (2021)", style="margin: 5px 0;"),
                                style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #27ae60; margin: 15px 0;"
                            ),
                            
                            ui.tags.div(
                                ui.tags.strong("Illustration Example:", style="color: #e67e22;"),
                                ui.tags.p(
                                    "Löwenstein–Jensen (LJ) slants showing full growth in control and no growth in the isoniazid-containing "
                                    "tube (susceptible).",
                                    style="margin: 10px 0; font-style: italic;"
                                ),
                                style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0;"
                            )
                        ),
                        
                        # Common Solid Media
                        ui.tags.div(
                            ui.tags.h6("Common Solid Media", style="color: #2980b9; margin: 20px 0 15px 0; font-weight: bold;"),
                            
                            # Middlebrook 7H10
                            ui.tags.div(
                                ui.tags.h6("a. Middlebrook 7H10 Agar", style="color: #8e44ad; margin: 15px 0 10px 0; font-weight: bold;"),
                                ui.tags.p(
                                    "A transparent agar medium used in proportion method DST, allowing clear observation of colony morphology. "
                                    "It is typically supplemented with OADC.",
                                    style="margin-bottom: 10px; line-height: 1.6; text-align: justify;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Example: ", style="color: #d35400;"),
                                    "Plates showing 99% inhibition of H37Rv at 0.2 µg/mL isoniazid (1% proportion method).",
                                    style="background-color: #fdf2e9; padding: 10px; border-radius: 5px; margin: 10px 0; font-style: italic;"
                                ),
                                style="margin-left: 20px; margin-bottom: 20px;"
                            ),
                            
                            # Middlebrook 7H11
                            ui.tags.div(
                                ui.tags.h6("b. Middlebrook 7H11 Agar", style="color: #8e44ad; margin: 15px 0 10px 0; font-weight: bold;"),
                                ui.tags.p(
                                    "An enriched variant of 7H10 containing casein hydrolysate to promote faster growth, ideal for weak or slow-growing isolates.",
                                    style="margin-bottom: 10px; line-height: 1.6; text-align: justify;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Example: ", style="color: #d35400;"),
                                    "Used to confirm MICs when 7H10 plates yield sparse growth.",
                                    style="background-color: #fdf2e9; padding: 10px; border-radius: 5px; margin: 10px 0; font-style: italic;"
                                ),
                                style="margin-left: 20px; margin-bottom: 20px;"
                            ),
                            
                            # Löwenstein–Jensen
                            ui.tags.div(
                                ui.tags.h6("c. Löwenstein–Jensen (LJ) Medium", style="color: #8e44ad; margin: 15px 0 10px 0; font-weight: bold;"),
                                ui.tags.p(
                                    "An egg-based solid medium containing malachite green to suppress contaminants. Commonly used for the proportion method and culture of M. tuberculosis.",
                                    style="margin-bottom: 10px; line-height: 1.6; text-align: justify;"
                                ),
                                ui.tags.div(
                                    ui.tags.strong("Example: ", style="color: #d35400;"),
                                    ui.tags.div([
                                        "LJ slant with streptomycin (4 µg/mL):",
                                        ui.tags.ul([
                                            ui.tags.li("No colonies → susceptible"),
                                            ui.tags.li("Growth comparable to control → resistant")
                                        ], style="margin: 10px 0; padding-left: 20px;")
                                    ]),
                                    style="background-color: #fdf2e9; padding: 10px; border-radius: 5px; margin: 10px 0; font-style: italic;"
                                ),
                                style="margin-left: 20px; margin-bottom: 20px;"
                            )
                        )
                    )
                ),
                
                # Summary Table
                ui.tags.div(
                    ui.tags.h4("Summary: Common Media Types", style="color: #34495e; margin: 30px 0 15px 0; font-size: 1.2em;"),
                    ui.tags.div(
                        ui.tags.table(
                            ui.tags.thead(
                                ui.tags.tr(
                                    ui.tags.th("Liquid Media", style="background-color: #3498db; color: white; padding: 15px; border: 1px solid #ddd; font-weight: bold; text-align: center; width: 50%;"),
                                    ui.tags.th("Solid Media", style="background-color: #27ae60; color: white; padding: 15px; border: 1px solid #ddd; font-weight: bold; text-align: center; width: 50%;")
                                )
                            ),
                            ui.tags.tbody(
                                ui.tags.tr(
                                    ui.tags.td(
                                        ui.tags.ul([
                                            ui.tags.li("MGIT", style="margin: 8px 0; font-weight: bold;"),
                                            ui.tags.li("7H9 Broth", style="margin: 8px 0; font-weight: bold;")
                                        ], style="list-style-type: disc; padding-left: 20px; margin: 10px 0;"),
                                        style="padding: 20px; border: 1px solid #ddd; vertical-align: top; background-color: #f8f9fa;"
                                    ),
                                    ui.tags.td(
                                        ui.tags.ul([
                                            ui.tags.li("7H10 Agar", style="margin: 8px 0; font-weight: bold;"),
                                            ui.tags.li("7H11 Agar", style="margin: 8px 0; font-weight: bold;"),
                                            ui.tags.li("LJ Medium", style="margin: 8px 0; font-weight: bold;")
                                        ], style="list-style-type: disc; padding-left: 20px; margin: 10px 0;"),
                                        style="padding: 20px; border: 1px solid #ddd; vertical-align: top; background-color: #f0f8f0;"
                                    )
                                )
                            ),
                            style="width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                        ),
                        style="overflow-x: auto;"
                    )
                ),
                                
                ui.tags.h3("Additional Resources", style="color: #34495e; margin-bottom: 15px;"),
                ui.tags.ul(
                    ui.tags.li("WHO Technical Manual for Drug Susceptibility Testing of Medicines used in the treatment of tuberculosis (2023)"),
                    ui.tags.li("Clinical and Laboratory Standards Institute (CLSI) M23 and M24 Guidelines"),
                    ui.tags.li("European Committee on Antimicrobial Susceptibility Testing (EUCAST) Guidelines"),
                    ui.tags.li("WHO Global Tuberculosis Report (2024)"),
                    style="line-height: 1.8; margin-bottom: 30px;"
                ),
                
                style="max-width: 1200px; margin: 0 auto; padding: 20px;"
            )

# Reactive functions
@reactive.effect
@reactive.event(input.next_btn)
def next_step():
    print(f"next_step called, current_step: {current_step()}")
    
    # Use a simple approach - just check current step and move forward
    if current_step() == 1:
        print("Moving from step 1 to step 2")
        current_step.set(2)
        calculate_clicked.set(False)
    elif current_step() == 2:
        print("Moving from step 2 to step 3")
        current_step.set(3)
        calculate_clicked.set(False)
        final_calculation_done.set(False)
    elif current_step() == 3:
        print("Moving from step 3 to step 4")
        current_step.set(4)
        calculate_clicked.set(False)
        final_calculation_done.set(False)
    elif current_step() == 4:
        # At step 4, there's no next step
        pass
    else:
        print(f"next_step: unexpected step - {current_step()}")
    
    print("next_step function completed")

@reactive.effect
@reactive.event(input.back_btn)
def back_step():
    print(f"back_step called, current_step: {current_step()}")
    if current_step() == 2:
        # Check if this is a restored session
        cs = current_session()
        is_restored_session = cs is not None
        print(f"Back button - is_restored_session: {is_restored_session}")
        
        if is_restored_session:
            # For restored sessions, go back to account management (Tab A)
            print("Back button - going back to account management")
            show_results_view.set(True)
            current_session.set(None)  # Clear current session
            current_step.set(1)  # Reset to step 1
        else:
            # For new sessions, go back to step 1
            print("Back button - going back to step 1")
            current_step.set(1)
            calculate_clicked.set(False)
    elif current_step() == 3:
        print("Back button - going back to step 2")
        current_step.set(2)
        final_calculation_done.set(False)  # Reset final calculation flag
    elif current_step() == 4:
        print("Back button - going back to step 3")
        current_step.set(3)
        final_calculation_done.set(True)  # Keep final calculation result when going back

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
        try:
            cs = current_session()
            user = current_user()
            if cs and user:
                selected = input.drug_selection() or []
                if selected:
                    # Notify user that a save is happening
                    try:
                        ui.notification_show("Saving session after instruction phase...", type="message", duration=3)
                    except Exception:
                        pass
                    # Get drug data for session formatting
                    drug_data = load_drug_data()
                    
                    # Create a DataFrame-like structure for session data
                    session_data = {}
                    for i, drug_name in enumerate(selected):
                        try:
                            # Get drug ID from database
                            drug_row = drug_data[drug_data['Drug'] == drug_name]
                            if not drug_row.empty:
                                drug_id = str(drug_row.iloc[0]['drug_id']) if 'drug_id' in drug_row.columns else str(i)
                                
                                # Get input values using helper function
                                drug_inputs = get_drug_inputs(i)
                                if drug_inputs:
                                    # Store in session format similar to CLI
                                    session_data[drug_id] = {
                                        'Crit_Conc(mg/ml)': drug_inputs['custom_crit'] if drug_inputs['custom_crit'] is not None else drug_row.iloc[0]['Critical_Concentration'],
                                        'PurMol_W(g/mol)': drug_inputs['purch_molw'] if drug_inputs['purch_molw'] is not None else 0.0,
                                        'St_Vol(ml)': drug_inputs['stock_vol'] if drug_inputs['stock_vol'] is not None else 0.0,
                                        'Act_DrugW(mg)': 0.0,  # Not yet entered
                                        'Total Mgit tubes': 0  # Not yet entered
                                    }
                        except Exception as e:
                            print(f"Error processing drug {drug_name} for session: {e}")
                    
                    # Update session with preparation data
                    preparation = {
                        'selected_drugs': selected,
                        'volume_unit': volume_unit(),
                        'weight_unit': weight_unit(),
                        'step': 2,
                        'inputs': session_data
                    }
                    db_manager.update_session_data(cs['session_id'], preparation)
                    print(f"Session saved after instruction phase for {len(selected)} drugs")
                    try:
                        ui.notification_show("Session saved (instruction phase).", type="message", duration=4)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error saving session after instruction phase: {e}")
            try:
                ui.notification_show("Could not save session (instruction phase).", type="error", duration=6)
            except Exception:
                pass

@reactive.effect
@reactive.event(input.calculate_final_btn)
def calculate_final_results():
    if current_step() == 3:
        # First validate and save Step 3 inputs
        if not validate_step3_inputs():
            print("calculate_final_results: Step 3 validation failed")
            return
        
        # Mark that final calculation has been performed
        final_calculation_done.set(True)
        # Move to step 4 after final calculation
        current_step.set(4)
        try:
            cs = current_session()
            user = current_user()
            if cs and user:
                print("calculate_final_results: Starting session save")
                
                # Get selected drugs from session data (for restored sessions)
                selected = []
                preparation = None
                try:
                    with db_manager.get_connection() as conn:
                        cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                        row = cur.fetchone()
                        if row and row[0]:
                            import json
                            preparation = json.loads(row[0])
                            selected = preparation.get('selected_drugs', [])
                            print(f"calculate_final_results: Got drugs from session: {selected}")
                except Exception as e:
                    print(f"calculate_final_results: Error getting session data: {e}")
                
                # Fallback to input if no session data
                if not selected:
                    try:
                        selected = input.drug_selection()
                        print(f"calculate_final_results: Got selected drugs from input: {selected}")
                    except Exception as e:
                        print(f"calculate_final_results: SilentException - inputs not ready yet: {e}")
                        return
                
                if selected:
                    # Notify user that a save is happening
                    try:
                        ui.notification_show("Saving session after final calculation...", type="message", duration=3)
                    except Exception:
                        pass
                    
                    # Get drug data for session formatting
                    drug_data = load_drug_data()
                    
                    # Create complete session data with all inputs
                    session_data = {}
                    for i, drug_name in enumerate(selected):
                        try:
                            print(f"calculate_final_results: Processing drug {i}: {drug_name}")
                            
                            # Get drug ID from database
                            drug_row = drug_data[drug_data['Drug'] == drug_name]
                            if not drug_row.empty:
                                drug_id = str(drug_row.iloc[0]['drug_id']) if 'drug_id' in drug_row.columns else str(i)
                                
                                # Get values from session data first (for restored sessions)
                                session_drug_data = None
                                if preparation:
                                    try:
                                        session_inputs = preparation.get('inputs', {})
                                        session_drug_data = session_inputs.get(str(i), {})
                                        print(f"calculate_final_results: Got session values: {session_drug_data}")
                                    except Exception as e:
                                        print(f"calculate_final_results: Error getting session values: {e}")
                                
                                # Get all inputs using helper function with session fallback
                                drug_inputs = get_drug_inputs(i, session_drug_data)
                                if not drug_inputs:
                                    print(f"calculate_final_results: Could not get inputs for drug {i}")
                                    continue
                                
                                custom_crit = drug_inputs['custom_crit']
                                purch_molw = drug_inputs['purch_molw']
                                stock_vol = drug_inputs['stock_vol']
                                actual_weight = drug_inputs['actual_weight']
                                mgit_tubes = drug_inputs['mgit_tubes']
                                
                                print(f"calculate_final_results: Final input values - custom_crit: {custom_crit}, purch_molw: {purch_molw}, stock_vol: {stock_vol}, actual_weight: {actual_weight}, mgit_tubes: {mgit_tubes}")
                                
                                # Store complete session data
                                session_data[drug_id] = {
                                    'Crit_Conc(mg/ml)': custom_crit if custom_crit is not None else drug_row.iloc[0]['Critical_Concentration'],
                                    'PurMol_W(g/mol)': purch_molw if purch_molw is not None else 0.0,
                                    'St_Vol(ml)': stock_vol if stock_vol is not None else 0.0,
                                    'Act_DrugW(mg)': actual_weight if actual_weight is not None else 0.0,
                                    'Total Mgit tubes': mgit_tubes if mgit_tubes is not None else 0
                                }
                                print(f"calculate_final_results: Stored session data for drug {i}: {session_data[drug_id]}")
                        except Exception as e:
                            print(f"Error processing drug {drug_name} for final session: {e}")
                    
                    # Update session with complete preparation data
                    preparation = {
                        'selected_drugs': selected,
                        'volume_unit': volume_unit(),
                        'weight_unit': weight_unit(),
                        'step': 3,
                        'inputs': session_data,
                        'results': calculation_results.get()
                    }
                    db_manager.update_session_data(cs['session_id'], preparation)
                    print(f"Session saved after final calculation for {len(selected)} drugs")
                    try:
                        ui.notification_show("Session saved (final calculation).", type="message", duration=4)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error saving session after final calculation: {e}")
            try:
                ui.notification_show("Could not save session (final calculation).", type="error", duration=6)
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

# Session card event handlers
@reactive.effect
@reactive.event(input.session_clicked)
def handle_session_card_click():
    try:
        print(f"Session clicked: {input.session_clicked()}")  # Debug
        user = current_user()
        if not user:
            return
        
        clicked_sid = input.session_clicked()
        if not clicked_sid:
            return
            
        with db_manager.get_connection() as conn:
            cur = conn.execute("SELECT preparation FROM session WHERE session_id = ? AND user_id = ?", (clicked_sid, user['user_id']))
            row = cur.fetchone()
        if not row or not row[0]:
            return
            
        import json
        preparation = json.loads(row[0])
        
        # Check if session is completed
        completed = bool(preparation and preparation.get('step', 0) >= 3 and preparation.get('results'))
        
        if completed:
            # View results for completed session - show read-only results
            # Set a flag to show results view instead of editable form
            show_results_view.set(True)
            current_session.set({'session_id': int(clicked_sid), 'session_name': preparation.get('session_name') or ''})
            
            # Store the session data for the results view
            session_data.set({
                'preparation': preparation,
                'selected_drugs': preparation.get('selected_drugs', []),
                'volume_unit': preparation.get('volume_unit', 'ml'),
                'weight_unit': preparation.get('weight_unit', 'mg'),
                'inputs': preparation.get('inputs', {}),
                'results': preparation.get('results', {}),
                'step': preparation.get('step', 3)
            })
            
            ui.update_navs("tab", selected="B")
        else:
            # Continue incomplete session
            print(f"Continuing incomplete session: {clicked_sid}")
            print(f"Session preparation data: {preparation}")
            
            # Make sure we're not in results view mode
            show_results_view.set(False)
            print(f"Set show_results_view to: {show_results_view()}")
            
            # First, navigate to Tab B
            ui.update_navs("tab", selected="B")
            
            # Update current session
            current_session.set({'session_id': int(clicked_sid), 'session_name': preparation.get('session_name') or ''})
            
            # Restore session state
            if 'selected_drugs' in preparation:
                print(f"Restoring selected drugs: {preparation['selected_drugs']}")
                ui.update_selectize("drug_selection", selected=preparation['selected_drugs'])
            if 'volume_unit' in preparation:
                print(f"Restoring volume unit: {preparation['volume_unit']}")
                volume_unit.set(preparation['volume_unit'])
                ui.update_select("vol_unit", selected=preparation['volume_unit'])
            if 'weight_unit' in preparation:
                print(f"Restoring weight unit: {preparation['weight_unit']}")
                weight_unit.set(preparation['weight_unit'])
                ui.update_select("weight_unit", selected=preparation['weight_unit'])
            if 'step' in preparation:
                print(f"Restoring step: {preparation['step']}")
                current_step.set(preparation['step'])
            
            # Store inputs for later restoration after UI is ready
            if 'inputs' in preparation and preparation['inputs']:
                print(f"Restoring inputs: {preparation['inputs']}")
                # Store the inputs in a reactive value for the UI to pick up
                session_inputs.set(preparation['inputs'])
            
            # Restore results if they exist
            if 'results' in preparation and preparation['results']:
                print(f"Restoring results: {preparation['results']}")
                calculation_results.set(preparation['results'])
                if preparation.get('step', 1) >= 2:
                    calculate_clicked.set(True)
                if preparation.get('step', 1) >= 3:
                    final_calculation_done.set(True)
            else:
                # If no results but we're at step 2 or 3, trigger calculation to show estimated weights
                if preparation.get('step', 1) >= 2:
                    print("Triggering calculation for step 2+")
                    calculate_clicked.set(True)
    except Exception:
        pass

@reactive.effect
@reactive.event(input.back_to_sessions)
def back_to_sessions():
    show_results_view.set(False)
    session_data.set({})

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
            
            # Load existing session data if available
            try:
                with db_manager.get_connection() as conn:
                    session_cur = conn.execute(
                        "SELECT preparation FROM session WHERE session_id = ?",
                        (session_id,)
                    )
                    session_row = session_cur.fetchone()
                    if session_row and session_row[0]:
                        import json
                        preparation = json.loads(session_row[0])
                        
                        # Load session data into UI
                        if 'selected_drugs' in preparation:
                            ui.update_selectize("drug_selection", selected=preparation['selected_drugs'])
                        
                        if 'volume_unit' in preparation:
                            volume_unit.set(preparation['volume_unit'])
                            ui.update_select("vol_unit", selected=preparation['volume_unit'])
                        
                        if 'weight_unit' in preparation:
                            weight_unit.set(preparation['weight_unit'])
                            ui.update_select("weight_unit", selected=preparation['weight_unit'])
                        
                        if 'step' in preparation:
                            current_step.set(preparation['step'])
                        
                        if 'inputs' in preparation and preparation['inputs']:
                            # Load drug-specific inputs
                            drug_data = load_drug_data()
                            for drug_id, drug_inputs in preparation['inputs'].items():
                                # Find drug name by ID
                                drug_name = None
                                for _, row in drug_data.iterrows():
                                    if str(row.get('drug_id', '')) == drug_id:
                                        drug_name = row['Drug']
                                        break
                                
                                if drug_name:
                                    selected = input.drug_selection() or []
                                    if drug_name in selected:
                                        drug_index = selected.index(drug_name)
                                        
                                        # Update inputs based on session data
                                        if 'Crit_Conc(mg/ml)' in drug_inputs:
                                            ui.update_numeric(f"custom_critical_{drug_index}", value=drug_inputs['Crit_Conc(mg/ml)'])
                                        if 'PurMol_W(g/mol)' in drug_inputs:
                                            ui.update_numeric(f"purchased_molw_{drug_index}", value=drug_inputs['PurMol_W(g/mol)'])
                                        if 'St_Vol(ml)' in drug_inputs:
                                            ui.update_numeric(f"stock_volume_{drug_index}", value=drug_inputs['St_Vol(ml)'])
                                        if 'Act_DrugW(mg)' in drug_inputs:
                                            ui.update_numeric(f"actual_weight_{drug_index}", value=drug_inputs['Act_DrugW(mg)'])
                                        if 'Total Mgit tubes' in drug_inputs:
                                            ui.update_numeric(f"mgit_tubes_{drug_index}", value=drug_inputs['Total Mgit tubes'])
                            
                            # Load calculation results if available
                            if 'results' in preparation and preparation['results']:
                                calculation_results.set(preparation['results'])
                                if preparation.get('step', 1) >= 2:
                                    calculate_clicked.set(True)
                                if preparation.get('step', 1) >= 3:
                                    final_calculation_done.set(True)
                        
                        auth_message.set(f"Session '{name}' loaded with existing data.")
            except Exception as e:
                print(f"Error loading session data: {e}")
                auth_message.set(f"Session '{name}' started (could not load existing data).")
            
            # Switch to calculator tab B
            ui.update_navs("tab", selected="B")
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

@reactive.effect
@reactive.event(input.make_stock_toggle)
def on_make_stock_toggle():
    try:
        make_stock_pref.set(bool(input.make_stock_toggle()))
    except Exception:
        pass


@reactive.effect
@reactive.event(input.potency_method_radio)
def on_potency_method_change():
    try:
        potency_method_pref.set(input.potency_method_radio())
    except Exception:
        pass


# PDF Download handlers
@reactive.effect
@reactive.event(input.download_step2_btn)
def handle_step2_download():
    """Handle Step 2 PDF download by triggering browser download"""
    try:
        pdf_data = generate_step2_pdf()
        if pdf_data:
            import base64
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DST_Calculator_Step2_Results_{timestamp}.pdf"
            
            # Create data URL for download
            b64_data = base64.b64encode(pdf_data).decode()
            data_url = f"data:application/pdf;base64,{b64_data}"
            
            # Trigger download using JavaScript
            ui.insert_ui(
                ui.tags.script(f"""
                    (function() {{
                        const link = document.createElement('a');
                        link.href = '{data_url}';
                        link.download = '{filename}';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    }})();
                """),
                selector="body",
                where="beforeEnd"
            )
        else:
            print("No data available for Step 2 PDF")
    except Exception as e:
        print(f"Error in handle_step2_download: {e}")


@reactive.effect
@reactive.event(input.download_step4_btn)
def handle_step4_download():
    """Handle Step 4 PDF download by triggering browser download"""
    try:
        pdf_data = generate_step4_pdf()
        if pdf_data:
            import base64
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DST_Calculator_Step4_Results_{timestamp}.pdf"
            
            # Create data URL for download
            b64_data = base64.b64encode(pdf_data).decode()
            data_url = f"data:application/pdf;base64,{b64_data}"
            
            # Trigger download using JavaScript
            ui.insert_ui(
                ui.tags.script(f"""
                    (function() {{
                        const link = document.createElement('a');
                        link.href = '{data_url}';
                        link.download = '{filename}';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    }})();
                """),
                selector="body",
                where="beforeEnd"
            )
        else:
            print("No data available for Step 4 PDF")
    except Exception as e:
        print(f"Error in handle_step4_download: {e}")

# Footer
ui.tags.div(
    ui.tags.hr(),
    ui.tags.div(
        style="margin-top: 40px;"
    )
)