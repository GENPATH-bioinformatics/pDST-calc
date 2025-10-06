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
    Formula: (number_of_mgits * 0.12) + 0.36
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

def vol_final_dil(vol_ss_to_ws, vol_workingsol):
    """
    Calculate the volume of diluent needed to complete the working solution.
    Formula: working_solution_volume - stock_solution_volume
    Args:
        vol_ss_to_ws (float): Volume of stock solution added to working solution (mL).
        vol_workingsol (float): Total volume of working solution (mL).
    Returns:
        float: Volume of diluent to add (mL).
    """
    return vol_workingsol - vol_ss_to_ws

def vol_ssleft(vol_ss_to_ws, vol_diluent):
    """
    Calculate the volume of stock solution remaining after preparing working solution.
    Formula: total_diluent_volume - stock_solution_volume_used
    Args:
        vol_ss_to_ws (float): Volume of stock solution used for working solution (mL).
        vol_diluent (float): Total volume of diluent originally prepared (mL).
    Returns:
        float: Volume of stock solution remaining (mL).
    """
    return vol_diluent - vol_ss_to_ws