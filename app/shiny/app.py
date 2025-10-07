from shiny import reactive
from shiny.express import input, render, ui
from shiny import ui as shiny_ui
import pandas as pd
import sys
import os

# Add the project root to Python path so we can import from app.api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.api.drug_database import load_drug_data
from lib.dst_calc import potency, est_drugweight, vol_diluent, conc_stock, conc_ws, vol_workingsol, vol_ss_to_ws, vol_final_dil
from app.api.auth import register_user, login_user
from app.api.database import db_manager

# Unit conversion functions
# UI reactive prefs
make_stock_pref = reactive.Value(False)
make_aliquot_pref = reactive.Value(False)
potency_method_pref = reactive.Value("mol_weight")

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
                                    
                                    # Convert to user's preferred weight unit
                                    est_dw_user_unit = convert_weight(est_dw, "mg", weight_unit())
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
                # [1] potency calculation from dst-calc.py
                pot = potency(purch_molw_gmol, drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0])
                
                # Calculate estimated drug weight
                # [2] est_drugweight calculation from dst-calc.py
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
    print("perform_final_calculations: Starting")
    
    # Try to get drugs from session first (for restored sessions)
    selected = []
    preparation = None
    cs = current_session()
    if cs:
        print(f"perform_final_calculations: Getting drugs from session {cs['session_id']}")
        try:
            with db_manager.get_connection() as conn:
                cur = conn.execute("SELECT preparation FROM session WHERE session_id = ?", (cs['session_id'],))
                row = cur.fetchone()
                if row and row[0]:
                    import json
                    preparation = json.loads(row[0])
                    selected = preparation.get('selected_drugs', [])
                    print(f"perform_final_calculations: Got drugs from session: {selected}")
        except Exception as e:
            print(f"perform_final_calculations: Error getting session data: {e}")
    
    # Fallback to input if no session data
    if not selected:
        try:
            selected = input.drug_selection()
            print(f"perform_final_calculations: Got selected drugs from input: {selected}")
        except Exception as e:
            print(f"perform_final_calculations: SilentException - inputs not ready yet: {e}")
            return []
    
    if not selected:
        print("perform_final_calculations: No selected drugs")
        return []
    
    print(f"perform_final_calculations: Processing {len(selected)} drugs")
    
    try:
        drug_data = load_drug_data()
        final_results = []
        
        for i, drug_name in enumerate(selected):
            try:
                print(f"perform_final_calculations: Processing drug {i}: {drug_name}")
                
                # Get actual weight and MGIT tubes
                actual_weight = input[f"actual_weight_{i}"]()
                mgit_tubes = input[f"mgit_tubes_{i}"]()
                
                print(f"perform_final_calculations: Drug {i} - actual_weight: {actual_weight}, mgit_tubes: {mgit_tubes}")
                
                if actual_weight and mgit_tubes:
                    # Convert actual weight to mg for calculations
                    actual_weight_mg = convert_weight(actual_weight, weight_unit(), "mg")
                    
                    # Get original values for calculations from session data
                    stock_vol = None
                    purch_molw = None
                    custom_crit = None
                    
                    # Try to get values from session data first
                    if cs:
                        try:
                            session_inputs = preparation.get('inputs', {})
                            drug_inputs = session_inputs.get(str(i), {})
                            stock_vol = drug_inputs.get('St_Vol(ml)', None)
                            purch_molw = drug_inputs.get('PurMol_W(g/mol)', None)
                            custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', None)
                            print(f"perform_final_calculations: Got values from session - stock_vol: {stock_vol}, purch_molw: {purch_molw}, custom_crit: {custom_crit}")
                        except Exception as e:
                            print(f"perform_final_calculations: Error getting session values: {e}")
                    
                    # Fallback to input fields if session data not available
                    if stock_vol is None or purch_molw is None or custom_crit is None:
                        try:
                            stock_vol = input[f"stock_volume_{i}"]()
                            purch_molw = input[f"purchased_molw_{i}"]()
                            custom_crit = input[f"custom_critical_{i}"]()
                            print(f"perform_final_calculations: Got values from input - stock_vol: {stock_vol}, purch_molw: {purch_molw}, custom_crit: {custom_crit}")
                        except Exception as e:
                            print(f"perform_final_calculations: Error getting input values: {e}")
                            continue
                    
                    stock_vol_ml = convert_volume(stock_vol, volume_unit(), "ml")
                    purch_molw_gmol = purch_molw
                    # Critical concentration is already in mg/ml
                    custom_crit_mgml = custom_crit
                    
                    # Calculate potency
                    # [1] potency calculation from dst-calc.py
                    org_molw = drug_data[drug_data['Drug'] == drug_name]['OrgMolecular_Weight'].iloc[0]
                    pot = potency(purch_molw_gmol, org_molw)
                    
                    # Step 1: Calculate estimated drug weight (from step 2)
                    # [2] est_drugweight calculation from dst-calc.py
                    est_drug_weight_mg = est_drugweight(custom_crit_mgml, stock_vol_ml, pot)
                    
                    # Step 2: Calculate diluent volume and stock concentration
                    # [3] vol_diluent calculation from dst-calc.py
                    vol_dil = vol_diluent(est_drug_weight_mg, actual_weight_mg, stock_vol_ml)
                    # [4] conc_stock calculation from dst-calc.py
                    conc_stock_ugml = conc_stock(actual_weight_mg, vol_dil)
                    
                    # Step 3: Calculate MGIT working solution
                    # [5] conc_ws calculation from dst-calc.py
                    conc_ws_ugml = conc_ws(custom_crit_mgml)  # conc_ws expects mg/ml input, returns μg/ml output
                    # [6] vol_workingsol calculation from dst-calc.py
                    vol_working_sol_ml = vol_workingsol(mgit_tubes)
                    # [7] vol_ss_to_ws calculation from dst-calc.py
                    vol_stock_to_ws_ml = vol_ss_to_ws(vol_working_sol_ml, conc_ws_ugml, conc_stock_ugml)
                    # [8] vol_final_dil calculation from dst-calc.py
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


    with ui.nav_panel("B"):
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
                                # Convert to standard units for calculations
                                stock_vol_ml = convert_volume(stock_vol, volume_unit_val, "ml")
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
                                    
                                    # Convert to user's preferred weight unit
                                    est_dw_user_unit = convert_weight(est_dw, "mg", weight_unit_val)
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
                            # Get input values
                            actual_weight = drug_inputs.get('Act_DrugW(mg)', 0)
                            mgit_tubes = drug_inputs.get('Total Mgit tubes', 0)
                            stock_vol = drug_inputs.get('St_Vol(ml)', 0)
                            purch_molw = drug_inputs.get('PurMol_W(g/mol)', 0)
                            custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', 0)
                            
                            if actual_weight and mgit_tubes and stock_vol and purch_molw and custom_crit:
                                # Convert actual weight to mg for calculations
                                actual_weight_mg = convert_weight(actual_weight, weight_unit_val, "mg")
                                
                                # Convert to standard units
                                stock_vol_ml = convert_volume(stock_vol, volume_unit_val, "ml")
                                purch_molw_gmol = purch_molw
                                custom_crit_mgml = custom_crit
                                
                                # Get drug data
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
                                    # [8] vol_final_dil calculation from dst-calc.py
                                    vol_diluent_to_add_ml = vol_final_dil(vol_stock_to_ws_ml, vol_working_sol_ml)
                                    
                                    # Convert volumes to user's preferred unit
                                    stock_vol_user = convert_volume(vol_stock_to_ws_ml, "ml", volume_unit_val)
                                    diluent_vol_user = convert_volume(vol_diluent_to_add_ml, "ml", volume_unit_val)
                                    
                                    # Check for warnings
                                    if vol_diluent_to_add_ml < 0:
                                        stock_vol_user = convert_volume(vol_working_sol_ml, "ml", volume_unit_val)
                                        diluent_vol_user = convert_volume(0, "ml", volume_unit_val)
                                    
                                    # Get diluent from drug data
                                    diluent = drug_row['Diluent'].iloc[0] if not drug_row.empty else "Unknown"
                                    
                                    final_results.append({
                                        'Drug': drug_name,
                                        'Diluent': diluent,
                                        'Stock_Vol_Aliquot': stock_vol_user,
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
                                        ui.tags.th(f"Aliquot for Stock Solution ({volume_unit_val})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;"),
                                        ui.tags.th(f"Diluent to Add ({volume_unit_val})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold;")
                                    ),
                                    *[ui.tags.tr(
                                        ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd;"),
                                        ui.tags.td(result['Diluent'], style="padding: 8px; border: 1px solid #ddd;"),
                                        ui.tags.td(f"{result['Stock_Vol_Aliquot']:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center;"),
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
                    return ui.tags.div(
                        ui.tags.h2("Input Parameters", style="color: #2c3e50; margin-bottom: 20px;"),
                        ui.tags.p("Enter the required parameters for each drug:", style="color: #7f8c8d; margin-bottom: 20px;"),
                        style="margin-bottom: 30px;"
                    )
                elif current_step() == 3:
                    print("Returning step 3 interface (final inputs)")
                    return ui.tags.div(
                        ui.tags.h2("Final Inputs", style="color: #2c3e50; margin-bottom: 20px;"),
                        ui.tags.p("Enter the actual drug weight and MGIT tube count:", style="color: #7f8c8d; margin-bottom: 20px;"),
                        style="margin-bottom: 30px;"
                    )
                else:
                    print("Returning default interface")
                    return ui.tags.div()
            
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
                        purity_value = stored_values.get('Purity_%', 100)
                        
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
                            row_cells.append(
                                ui.tags.td(
                                    ui.input_numeric(
                                        f"purchased_molw_{i}",
                                        "",
                                        value=0,
                                        min=row_data['OrgMolecular_Weight'],
                                        step=0.01
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 140px;"
                                )
                            )
                        
                        # Add purity column if needed
                        if current_potency_method in ["purity", "both"]:
                            row_cells.append(
                                ui.tags.td(
                                    ui.input_numeric(
                                        f"purity_{i}",
                                        "",
                                        value=0,
                                        min=0.01,
                                        max=100,
                                        step=0.1
                                    ),
                                    style="padding: 5px; border: 1px solid #ddd; width: 100px;"
                                )
                            )
                        
                        # Always add MGIT tubes column
                        row_cells.append(
                            ui.tags.td(
                                ui.input_numeric(
                                    f"mgit_tubes_{i}",
                                    "",
                                    value=mgit_tubes_value,
                                    min=1,
                                    step=1
                                ),
                                style="padding: 5px; border: 1px solid #ddd; width: 120px;"
                            )
                        )
                        
                        row = ui.tags.tr(*row_cells, style="background-color: white;")
                        table_rows.append(row)

                    return ui.tags.div(
                        ui.tags.h3("Enter Parameters", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
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
                            style="margin-bottom: 20px;"
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
                    # Get estimated weight for display (calculated by reactive effect)
                    est_weight = get_estimated_weight(0) if selected else 0
                    print(f"Step 3: Estimated weight: {est_weight}")
                    
                    # Create table headers for step 3
                    table_headers = ui.tags.tr(
                        ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                        ui.tags.th(f"Est. Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                        ui.tags.th(f"Actual Weight ({weight_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                        style="background-color: #f8f9fa;"
                    )
                    
                    # Create table rows for each selected drug
                    table_rows = []
                    stored_inputs = session_inputs.get()
                    print(f"Step 3: Creating rows for {len(selected)} drugs")
                    for i, drug_name in enumerate(selected):
                        # Get estimated weight from previous calculation
                        est_weight = get_estimated_weight(i) if i == 0 else get_estimated_weight(i)
                        
                        # Get stored values if they exist
                        stored_values = stored_inputs.get(str(i), {})
                        actual_weight_value = stored_values.get('Act_DrugW(mg)', 0)
                        mgit_tubes_value = stored_values.get('Total Mgit tubes', 0)
                        print(f"Step 3: Drug {i} ({drug_name}) - estimated weight: {est_weight}, stored values: actual_weight={actual_weight_value}, mgit_tubes={mgit_tubes_value}")
                        
                        row = ui.tags.tr(
                            ui.tags.td(drug_name, style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                            ui.tags.td(f"{est_weight:.4f}", style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
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
                        return ui.tags.div()
                
                if not selected:
                    print("results_section: No selected drugs, returning empty div")
                    return ui.tags.div()
                    
                if current_step() == 2:
                    # Get input values (new Step 2 flow)
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
                            
                            # Get MGIT tubes
                            mgit_tubes = input[f"mgit_tubes_{i}"]()
                            if mgit_tubes is None or mgit_tubes <= 0:
                                return ui.tags.div("Please enter valid MGIT tube counts for all drugs.", style="color: green;")
                            mgit_tubes_values.append(int(mgit_tubes))
                            
                            # Get custom critical value
                            custom_crit = input[f"custom_critical_{i}"]()
                            if custom_crit is None or custom_crit <= 0:
                                return ui.tags.div("Please enter valid critical concentrations for all drugs.", style="color: green;")
                            # Use mg/ml directly
                            custom_crit_mgml = custom_crit
                            custom_critical_values.append(custom_crit_mgml)
                        
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
                                        if purity_pct and purity_pct > 0:
                                            pot = 1.0 / (purity_pct / 100.0)
                                        else:
                                            pot = 1.0
                                    except Exception:
                                        pot = 1.0
                                elif potency_method == "both":
                                    # Potency from both: (1.0 / (purity / 100)) * (purch_molw / org_molw)
                                    try:
                                        purity_pct = input[f"purity_{i}"]()
                                        if purity_pct and purity_pct > 0:
                                            pot = (1.0 / (purity_pct / 100.0)) * (purchased_mol_weights[i] / org_molw)
                                        else:
                                            pot = potency(purchased_mol_weights[i], org_molw)
                                    except Exception:
                                        pot = potency(purchased_mol_weights[i], org_molw)
                                else:  # "mol_weight" (default)
                                    # Traditional potency calculation from molecular weights
                                    pot = potency(purchased_mol_weights[i], org_molw)
                                # [5] conc_ws
                                ws_conc_ugml = conc_ws(custom_critical_values[i])
                                # [6] vol_workingsol
                                vol_ws_ml = vol_workingsol(mgit_tubes_values[i])
                                # [2] est_drugweight (new formula)
                                est_dw_mg = (ws_conc_ugml * vol_ws_ml * pot) / 1000.0
                                est_dw_user_unit = convert_weight(est_dw_mg, "mg", weight_unit())
                                estimated_weights.append(est_dw_user_unit)
                                # [3] vol_diluent (as vol_workingsol)
                                vol_dil_ml = vol_ws_ml
                                diluent_volumes.append(convert_volume(vol_dil_ml, "ml", volume_unit()))

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
                                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th("Potency", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                                    ui.tags.th("Conc. of Working Solution (μg/ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 180px;"),
                                    ui.tags.th("Total Volume of Working Solution (ml)", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                                    style="background-color: #f8f9fa;"
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
                                            ui.tags.td(result['Drug'], style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Potency']), 4), style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Conc_WS(ug/ml)']), 2), style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                            ui.tags.td(round(float(result['Vol_WS(ml)']), 2), style="padding: 8px; border: 1px solid #ddd; text-align: center; font-size: 14px;"),
                                            style="background-color: white;"
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
                                        # Default practical weight: 3.0 mg
                                        practical_val = 3.0
                                        try:
                                            v = input[f"practical_weight_{idx}"]()
                                            if v is not None and v > 0:
                                                practical_val = v
                                        except Exception:
                                            # Input not ready yet; keep default
                                            pass
                                        # Compute practical diluent volume: (x / est_dw_mg) * vol_ws_ml
                                        try:
                                            vol_needed_ml = convert_volume(((practical_val or 0) / max(r['Est_DrugWeight_mg_num'], 1e-12)) * r['Vol_WS_ml_num'], "ml", volume_unit())
                                        except Exception:
                                            vol_needed_ml = ""
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
                                        
                                        stock_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #2c3e50; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    ui.input_numeric(
                                                        f"dilution_factor_{idx}",
                                                        "",
                                                        value=a_val,
                                                        min=1.1,
                                                        step=1
                                                    ),
                                                    style="padding: 5px; border: 2px solid #2c3e50; width: 200px;"
                                                ),
                                                ui.tags.td(
                                                    f"{stock_vol_ml:.4f}",
                                                    style="padding: 8px; border: 2px solid #2c3e50; text-align: center; font-size: 14px;"
                                                ),
                                                ui.tags.td(
                                                    f"{diluent_vol_ml:.4f}",
                                                    style="padding: 8px; border: 2px solid #2c3e50; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )
                                        
                                        # Build aliquot summary row for this drug
                                        # Total Stock Volume (+ 10% error) = (Total Aliquot Volume + Stock Volume) * 1.1
                                        total_stock_vol_with_error = (aliquot_total_num + stock_vol_ml) * 1.1
                                        
                                        # Drug to weigh out = Total Stock Volume * conc_ws * dilution_factor * potency / 1000
                                        pot = r.get('Potency_num', 1.0)
                                        drug_to_weigh = (total_stock_vol_with_error * ws_conc_ugml * a_val * pot) / 1000
                                        
                                        # Build stock without aliquot summary row (drug weight for stock solution only)
                                        # Drug to weigh out for stock (without aliquots) = Stock Volume × conc_ws × dilution_factor × potency / 1000
                                        drug_to_weigh_stock_only = (stock_vol_ml * ws_conc_ugml * a_val * pot) / 1000

                                        # Validation logic depends on whether aliquots are being made
                                        if bool(make_aliquot_pref()):
                                            # Validation 1: Check if drug to weigh out is less than 2 mg (WITH aliquots)
                                            if drug_to_weigh < 2.0:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Drug weight ({drug_to_weigh:.4f} mg) is less than 2 mg. Consider increasing the number of aliquots or ml per aliquot to achieve a more realistic weighing value."
                                                )
                                                # Validation 2: Check if stock volume is less than 250 microliters (0.25 ml) when aliquots are NOT being made
                                            if stock_vol_ml < 0.25:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Stock solution volume ({stock_vol_ml:.4f} ml = {stock_vol_ml * 1000:.1f} μl) might be too small to pipette. Consider decreasing the stock concentration factor, otherwise an intermediate dilution will be needed."
                                                )
                                        else:
                                            # Validation for stock without aliquots
                                            # Check if drug weight is less than 2 mg
                                            if drug_to_weigh_stock_only < 2.0:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Drug weight ({drug_to_weigh_stock_only:.4f} mg) is less than 2 mg. Consider making aliquots to increase the total drug weight needed."
                                                )
                                            # Check if stock volume is less than 250 microliters (0.25 ml)
                                            if stock_vol_ml < 0.25:
                                                validation_messages.append(
                                                    f"⚠️ {r['Drug']}: Stock solution volume ({stock_vol_ml:.4f} ml = {stock_vol_ml * 1000:.1f} μl) might be too small to pipette. Consider decreasing the stock concentration factor or making aliquots, otherwise an intermediate dilution will be needed."
                                                )

                                        stock_no_aliquot_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #2c3e50; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    f"{drug_to_weigh_stock_only:.4f}",
                                                    style="padding: 8px; border: 2px solid #2c3e50; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )
                                        
                                        aliquot_summary_rows.append(
                                            ui.tags.tr(
                                                ui.tags.td(r['Drug'], style="padding: 8px; border: 2px solid #16a085; font-weight: bold; font-size: 14px;"),
                                                ui.tags.td(
                                                    f"{total_stock_vol_with_error:.4f}",
                                                    style="padding: 8px; border: 2px solid #16a085; text-align: center; font-size: 14px;"
                                                ),
                                                ui.tags.td(
                                                    f"{drug_to_weigh:.4f}",
                                                    style="padding: 8px; border: 2px solid #16a085; text-align: center; font-size: 14px;"
                                                ),
                                                style="background-color: #ffffff;"
                                            )
                                        )

                                return ui.tags.div(
                                    ui.tags.h3("Step 2 Calculations", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                                    ui.tags.div(
                                        ui.tags.table(
                                            main_headers,
                                            *main_rows,
                                            style="width: auto; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;"
                                        ),
                                        style="overflow-x: auto; max-width: 100%;"
                                    ),
                                    ui.tags.h3("Prepare These", style="color: #27ae60; margin-top: 10px; margin-bottom: 10px;"),
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
                                            ui.tags.p("Note: The values above are ideal. For practical weighing, 3 mg would be recommended, but this would in turn increase the diluent volume. Toggle the inputs below to help you decide on a realistic outcome.",
                                                      style="color: #e67e22; margin: 10px 0; font-weight: 600;"),
                                            # Toggle: Create Stock Solution vs No stock solution
                                            ui.tags.div(
                                                ui.input_switch("make_stock_toggle", "Create Stock Solution", value=make_stock_pref()),
                                                style="margin: 8px 0 12px;"
                                            ),
                                            # Second toggle: Create Aliquots (only shown when make_stock is True)
                                            ui.tags.div(
                                                ui.input_switch("make_aliquot_toggle", "Create Aliquots", value=make_aliquot_pref()),
                                                style="margin: 8px 0 12px;"
                                            ) if make_stock else ui.tags.div(),
                                            ui.tags.table(
                                                (
                                                    ui.tags.tr(
                                                        ui.tags.th("Drug", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 180px;"),
                                                        ui.tags.th("Weight to Weigh Out (mg)", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 180px;"),
                                                        ui.tags.th(f"Volume of Diluent Needed ({volume_unit()})", style="padding: 8px; border: 2px solid #f39c12; background-color: #fff7e6; font-weight: bold; font-size: 14px; width: 200px;"),
                                                    ) if not make_stock else
                                                    ui.tags.tr(
                                                        ui.tags.th("Drug", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 180px;"),
                                                        ui.tags.th("Stock Concentration Increase Factor", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 200px;"),
                                                        ui.tags.th(f"Stock Volume ({volume_unit()})", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 150px;"),
                                                        ui.tags.th(f"Volume Diluent to dilute stock ({volume_unit()})", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 150px;"),
                                                    )
                                                ),
                                                *(practical_rows if not make_stock else stock_rows),
                                                style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                            ),
                                            # Stock without aliquots summary table (shown when make_stock is True but make_aliquot is False)
                                            (
                                                ui.tags.div(
                                                    ui.tags.h4("Stock Solution Preparation", style="color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"),
                                                    ui.tags.table(
                                                        ui.tags.tr(
                                                            ui.tags.th("Drug", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 200px;"),
                                                            ui.tags.th("Drug to Weigh Out (mg)", style="padding: 8px; border: 2px solid #2c3e50; background-color: #ecf5ff; font-weight: bold; font-size: 14px; width: 200px;"),
                                                        ),
                                                        *stock_no_aliquot_rows,
                                                        style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                                    )
                                                )
                                            ) if (make_stock and not bool(make_aliquot_pref())) else ui.tags.div(),
                                            # Aliquot table (only shown when make_stock AND make_aliquot are both True)
                                            (
                                                ui.tags.div(
                                                    ui.tags.h4("Aliquot Planning", style="color: #16a085; margin-top: 20px; margin-bottom: 10px;"),
                                                    ui.tags.table(
                                                        ui.tags.tr(
                                                            ui.tags.th("Number of Aliquots", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 180px;"),
                                                            ui.tags.th(f"ml per Aliquot ({volume_unit()})", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 180px;"),
                                                            ui.tags.th(f"Total Aliquot Volume ({volume_unit()})", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 200px;"),
                                                        ),
                                                        ui.tags.tr(
                                                            ui.tags.td(
                                                                ui.input_numeric("num_aliquots", None, value=num_aliq_val, min=1, step=1),
                                                                style="padding: 8px; border: 2px solid #16a085;"
                                                            ),
                                                            ui.tags.td(
                                                                ui.input_numeric("ml_per_aliquot", None, value=ml_per_aliq_val, min=0.5, step=1),
                                                                style="padding: 8px; border: 2px solid #16a085;"
                                                            ),
                                                            ui.tags.td(
                                                                aliquot_total,
                                                                style="padding: 8px; border: 2px solid #16a085; text-align: center; font-weight: bold; font-size: 14px;"
                                                            ),
                                                        ),
                                                        style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                                    ),
                                                    # Aliquot Summary table (only shown when make_aliquot is True)
                                                    (
                                                        ui.tags.div(
                                                            ui.tags.h4("Stock Solution Preparation Summary", style="color: #16a085; margin-top: 20px; margin-bottom: 10px;"),
                                                            ui.tags.table(
                                                                ui.tags.tr(
                                                                    ui.tags.th("Drug", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 200px;"),
                                                                    ui.tags.th(f"Total Stock Volume (+ 10% error) ({volume_unit()})", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 250px;"),
                                                                    ui.tags.th("Drug to Weigh Out (mg)", style="padding: 8px; border: 2px solid #16a085; background-color: #e8f8f5; font-weight: bold; font-size: 14px; width: 200px;"),
                                                                ),
                                                                *aliquot_summary_rows,
                                                                style="width: auto; border-collapse: collapse; margin: 10px 0 20px; table-layout: fixed;"
                                                            ),
                                                            # Display validation messages if any
                                                            (
                                                                ui.tags.div(
                                                                    *[ui.tags.p(msg, style="color: #e67e22; margin: 5px 0; padding: 10px; background-color: #fff3cd; border-left: 4px solid #e67e22; border-radius: 4px; font-size: 14px;") for msg in validation_messages],
                                                                    style="margin-top: 15px;"
                                                                )
                                                            ) if validation_messages else ui.tags.div()
                                                        )
                                                    ) if bool(make_aliquot_pref()) else ui.tags.div()
                                                )
                                            ) if (make_stock and bool(make_aliquot_pref())) else ui.tags.div(),
                                            # Validation message for stock volume without aliquots
                                            (
                                                ui.tags.div(
                                                    *[ui.tags.p(msg, style="color: #e67e22; margin: 5px 0; padding: 10px; background-color: #fff3cd; border-left: 4px solid #e67e22; border-radius: 4px; font-size: 14px;") for msg in validation_messages],
                                                    style="margin-top: 15px;"
                                                )
                                            ) if (make_stock and not bool(make_aliquot_pref()) and validation_messages) else ui.tags.div()
                                        ) if any_low_mass else ui.tags.div()
                                    ),
                                    ui.tags.div("INSTRUCTION: Weigh out drug according to above values. Then proceed to Step 3 to enter the actual weights.", style="color: #1e90ff; margin-top: 10px; margin-bottom: 15px; font-weight: bold; font-size: 16px;")
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
                            *[ui.tags.p(warning, style="color: #2c3e50; margin-bottom: 10px; padding: 10px; background-color: #fdf2f2; border-left: 4px solid #e74c3c; border-radius: 4px;") for warning in warning_list],
                            style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px;"
                        )
                    else:
                        warning_ui = ui.tags.div()
                    print(f"results_section: final_calculation_done: {final_calculation_done()}")
                    if final_calculation_done():
                        try:
                            final_results = perform_final_calculations()
                            
                            if final_results:
                                
                                table_headers = ui.tags.tr(
                                    ui.tags.th("Drug", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 200px;"),
                                    ui.tags.th("Diluent", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 120px;"),
                                    ui.tags.th(f"Aliquot for Stock Solution ({volume_unit()})", style="padding: 8px; border: 1px solid #ddd; background-color: #f8f9fa; font-weight: bold; font-size: 14px; width: 180px;"),
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
                        print("results_section: Showing step 3 instruction text")
                        return ui.tags.div(
                            warning_ui,  # Show warnings if any
                            ui.tags.h3("Enter Final Parameters", style="color: #2c3e50; margin-top: 30px; margin-bottom: 15px;"),
                            ui.tags.p("Please enter the actual weights for each selected drug, then click 'Calculate Final Results'.", style="color: #7f8c8d; margin-bottom: 20px;")
                        )
                
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
                            mgit_tubes = input[f"mgit_tubes_{i}"]()
                            print(f"validate_step3_inputs: Drug {i} - actual_weight: {actual_weight}, mgit_tubes: {mgit_tubes}")
                            
                            if actual_weight is None or actual_weight <= 0 or mgit_tubes is None or mgit_tubes <= 0:
                                print(f"validate_step3_inputs: Drug {i} validation failed - values too low")
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
                            # Show Next button after calculation
                            return ui.tags.div(
                                ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
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
                    print(f"final_calculation_done: {final_calculation_done()}")
                    
                    # Validate step 3 inputs
                    if final_calculation_done():
                        print("Final calculation done - showing New Calculation button")
                        # After results are shown, replace with New Calculation
                        return ui.tags.div(
                            ui.input_action_button("back_btn", "Back", class_="btn-secondary", style="margin-right: 10px;"),
                            ui.input_action_button("new_calc_btn", "New Calculation", class_="btn-success", style="background-color: #27ae60; border-color: #27ae60;"),
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
                else:
                    return ui.tags.div()

    with ui.nav_panel("C"):
        pass

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
                                
                                # Get input values
                                custom_crit = input[f"custom_critical_{i}"]()
                                purch_molw = input[f"purchased_molw_{i}"]()
                                stock_vol = input[f"stock_volume_{i}"]()
                                
                                # Store in session format similar to CLI
                                session_data[drug_id] = {
                                    'Crit_Conc(mg/ml)': custom_crit if custom_crit is not None else drug_row.iloc[0]['Critical_Concentration'],
                                    'PurMol_W(g/mol)': purch_molw if purch_molw is not None else 0.0,
                                    'St_Vol(ml)': stock_vol if stock_vol is not None else 0.0,
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
        # Mark that final calculation has been performed
        final_calculation_done.set(True)
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
                                custom_crit = None
                                purch_molw = None
                                stock_vol = None
                                actual_weight = None
                                mgit_tubes = None
                                
                                if preparation:
                                    try:
                                        session_inputs = preparation.get('inputs', {})
                                        drug_inputs = session_inputs.get(str(i), {})
                                        custom_crit = drug_inputs.get('Crit_Conc(mg/ml)', None)
                                        purch_molw = drug_inputs.get('PurMol_W(g/mol)', None)
                                        stock_vol = drug_inputs.get('St_Vol(ml)', None)
                                        print(f"calculate_final_results: Got session values - custom_crit: {custom_crit}, purch_molw: {purch_molw}, stock_vol: {stock_vol}")
                                    except Exception as e:
                                        print(f"calculate_final_results: Error getting session values: {e}")
                                
                                # Get actual weight and MGIT tubes from input (these are step 3 inputs)
                                try:
                                    actual_weight = input[f"actual_weight_{i}"]()
                                    mgit_tubes = input[f"mgit_tubes_{i}"]()
                                    print(f"calculate_final_results: Got input values - actual_weight: {actual_weight}, mgit_tubes: {mgit_tubes}")
                                except Exception as e:
                                    print(f"calculate_final_results: Error getting input values: {e}")
                                    continue
                                
                                # Fallback to input fields if session data not available
                                if custom_crit is None or purch_molw is None or stock_vol is None:
                                    try:
                                        custom_crit = input[f"custom_critical_{i}"]()
                                        purch_molw = input[f"purchased_molw_{i}"]()
                                        stock_vol = input[f"stock_volume_{i}"]()
                                        print(f"calculate_final_results: Got fallback input values - custom_crit: {custom_crit}, purch_molw: {purch_molw}, stock_vol: {stock_vol}")
                                    except Exception as e:
                                        print(f"calculate_final_results: Error getting fallback input values: {e}")
                                        continue
                                
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
@reactive.event(input.make_aliquot_toggle)
def on_make_aliquot_toggle():
    try:
        make_aliquot_pref.set(bool(input.make_aliquot_toggle()))
    except Exception:
        pass

@reactive.effect
@reactive.event(input.potency_method_radio)
def on_potency_method_change():
    try:
        potency_method_pref.set(input.potency_method_radio())
    except Exception:
        pass

# Footer
ui.tags.div(
    ui.tags.hr(),
    ui.tags.div(
        style="margin-top: 40px;"
    )
)