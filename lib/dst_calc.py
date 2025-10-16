def potency(mol_purch, mol_org):
    """
    Calculate the potency of the drug based on molecular weight ratio.
    Potency represents the relative activity of the purchased drug compared to the original.
    Args:
        mol_purch (float): Molecular weight of purchased drug (g/mol).
        mol_org (float): Molecular weight of original drug (g/mol).
    Returns:
        float: Potency value as a ratio (dimensionless).
    """
    return mol_purch / mol_org

def est_drugweight(conc_crit, vol_stock, potency):
    """
    Estimate the required drug weight for a given target concentration and volume, accounting for potency.
    Formula: (critical_conc * stock_vol * potency * 84) / 1000
    Args:
        conc_crit (float): Critical concentration (mg/mL).
        vol_stock (float): Volume of stock solution (mL).
        potency (float): Potency of the drug (dimensionless ratio).
    Returns:
        float: Required drug weight (mg).
    """
    return (conc_crit * vol_stock * potency * 84) / 1000

def vol_diluent(est_drugweight, act_drugweight, desired_totalvol):
    """
    Calculate the volume of diluent needed to achieve a desired concentration with a given drug weight.
    This adjusts the total volume based on the ratio of estimated to actual drug weight.
    Args:
        est_drugweight (float): Estimated drug weight (mg).
        act_drugweight (float): Actual drug weight (mg).
        desired_totalvol (float): Desired total volume (mL).
    Returns:
        float: Volume of diluent (mL).
    """
    return (act_drugweight / est_drugweight) * desired_totalvol

def conc_stock(act_drugweight, vol_diluent):
    """
    Calculate the concentration of the stock solution.
    Formula: (actual_drug_weight * 1000) / volume_diluent
    Args:
        act_drugweight (float): Actual drug weight (mg).
        vol_diluent (float): Volume of diluent (mL).
    Returns:
        float: Stock concentration (μg/mL).
    """
    return ((act_drugweight * 1000) / vol_diluent)

def conc_ws(crit_concentration):
    """
    Calculate the final working solution concentration after dilution.
    Formula: (critical_concentration * 8.4) / 0.1
    This accounts for the dilution factor used in MGIT testing.
    Args:
        crit_concentration (float): Critical concentration (mg/mL).
    Returns:
        float: Final working solution concentration (μg/mL).
    """
    return (crit_concentration * 8.4) / 0.1 

def vol_workingsol(num_mgits):
    """
    Calculate the volume of working solution needed for a given number of MGIT tubes.
    Formula: (number_of_mgits * 0.1) + 0.2
    This includes extra volume for pipetting and ensures sufficient working solution.
    Args:
        num_mgits (int): Number of MGIT tubes to prepare.
    Returns:
        float: Volume of working solution needed (mL).
    """
    return (num_mgits * 0.1) + 0.2

def vol_ss_to_ws(vol_workingsol, conc_ws, conc_stock):
    """
    Calculate the volume of stock solution needed to prepare the working solution.
    Formula: (working_solution_volume * working_solution_concentration) / stock_concentration
    Args:
        vol_workingsol (float): Volume of working solution needed (mL).
        conc_ws (float): Target working solution concentration (μg/mL).
        conc_stock (float): Concentration of stock solution (μg/mL).
    Returns:
        float: Volume of stock solution to add to working solution (mL).
    """
    return (vol_workingsol * conc_ws) / conc_stock


def calc_adjusted_volume(actual_weight, est_weight, base_volume):
    """
    Calculate adjusted volume based on actual vs estimated weight ratio.
    This is a general function for scaling volumes when actual weight differs from estimated.
    Formula: (actual_weight / estimated_weight) * base_volume
    
    Args:
        actual_weight (float): Actual drug weight (mg).
        est_weight (float): Estimated drug weight (mg).
        base_volume (float): Base volume to adjust (mL).
    Returns:
        float: Adjusted volume (mL).
    """
    return (actual_weight / est_weight) * base_volume

def calc_stock_factor(actual_weight, total_stock_vol, ws_conc_ugml, potency):
    """
    Calculate the stock solution factor (concentration multiplier).
    Formula: (actual_weight * 1000) / (total_stock_volume * working_solution_concentration * potency)
    Args:
        actual_weight (float): Actual drug weight (mg).
        total_stock_vol (float): Total stock volume (mL).
        ws_conc_ugml (float): Working solution concentration (μg/mL).
        potency (float): Drug potency (dimensionless).
    Returns:
        float: Stock factor (dimensionless multiplier).
    """
    return (actual_weight * 1000) / (total_stock_vol * ws_conc_ugml * potency)

def calc_volume_divided_by_factor(volume, factor):
    """
    Calculate volume divided by a factor (general dilution calculation).
    Used for stock-to-working solutions, stock-to-intermediate solutions, etc.
    Formula: volume / factor
    
    Args:
        volume (float): Volume to divide (mL).
        factor (float): Factor to divide by (dimensionless).
    Returns:
        float: Divided volume (mL).
    """
    return volume / factor

def calc_concentration_times_factor(concentration, factor):
    """
    Calculate concentration multiplied by a factor (general concentration scaling).
    Used for stock concentrations, intermediate concentrations, etc.
    Formula: concentration * factor
    
    Args:
        concentration (float): Base concentration (μg/mL).
        factor (float): Multiplication factor (dimensionless).
    Returns:
        float: Scaled concentration (μg/mL).
    """
    return concentration * factor


def calc_intermediate_factor(initial_factor, total_ws_volume, min_volume_threshold=0.2):
    """
    Calculate the intermediate dilution factor for cases requiring intermediate dilutions.
    Iteratively reduces the factor until the resulting volume meets the minimum threshold.
    Args:
        initial_factor (float): Initial stock factor.
        total_ws_volume (float): Total working solution volume (mL).
        min_volume_threshold (float): Minimum volume threshold (mL). Default 0.2.
    Returns:
        float: Intermediate factor that produces volumes above threshold.
    """
    inter_factor = initial_factor
    
    # Iteratively reduce factor until we get acceptable volume
    while inter_factor > 1.1:
        inter_factor -= 0.5
        stock_to_inter = total_ws_volume / inter_factor
        
        if stock_to_inter > min_volume_threshold:
            break
    
    # If we couldn't find a valid factor, fall back to 2
    if inter_factor <= 1.1:
        inter_factor = 2
    
    return inter_factor

def calc_intermediate_volume(stock_to_inter, final_stock_conc, inter_factor, ws_conc_ugml):
    """
    Calculate the total volume of intermediate dilution.
    Formula: (stock_to_intermediate * final_stock_concentration) / (intermediate_factor * working_solution_concentration)
    Args:
        stock_to_inter (float): Volume of stock solution for intermediate (mL).
        final_stock_conc (float): Final stock concentration (μg/mL).
        inter_factor (float): Intermediate dilution factor.
        ws_conc_ugml (float): Working solution concentration (μg/mL).
    Returns:
        float: Total intermediate volume (mL).
    """
    return (stock_to_inter * final_stock_conc) / (inter_factor * ws_conc_ugml)

def calc_volume_difference(total_volume, volume_to_subtract):
    """
    Calculate the difference between two volumes (general diluent calculation).
    This is a general function for calculating diluent volumes or remaining volumes.
    Formula: total_volume - volume_to_subtract
    
    Args:
        total_volume (float): Total volume (mL).
        volume_to_subtract (float): Volume to subtract (mL).
    Returns:
        float: Volume difference (mL).
    """
    return total_volume - volume_to_subtract
