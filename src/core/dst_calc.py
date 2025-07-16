def potency(mol_purch, mol_org):
    """
    Calculate or retrieve the potency of the drug.
    Args:
        mol_purch (float): Molecular weight of purchased drug.
        mol_org (float): Molecular weight of original drug.
    Returns:
        float: Potency value (e.g., percent or mg/mg).
    """
    return mol_purch / mol_org

def est_drugweight(conc_crit, vol_stock, potency):
    """
    Estimate the required drug weight for a given target concentration and volume, accounting for potency.
    Args:
        conc_crit (float): Critical concentration (mg/mL).
        vol_stock (float): Volume of stock solution (mL).
        potency (float): Potency of the drug (fraction or percent).
    Returns:
        float: Required drug weight (mg).
    """
    return (conc_crit * vol_stock * potency * 84) / 1000

def vol_diluent(est_drugweight, act_drugweight, desired_totalvol):
    """
    Calculate the volume of diluent needed to achieve a desired concentration with a given drug weight.
    Args:
        est_drugweight (float): Estimated drug weight (mg).
        act_drugweight (float): Actual drug weight (mg).
        desired_totalvol (float): Desired total volume (mL).
    Returns:
        float: Volume of diluent (mL).
    """
    return (est_drugweight / act_drugweight) * desired_totalvol

def conc_stock(act_drugweight, vol_diluent):
    """
    Calculate the concentration of the stock solution.
    Args:
        act_drugweight (float): Actual drug weight (mg).
        vol_diluent (float): Volume of diluent (mL).
    Returns:
        float: Stock concentration (mg/mL).
    """
    return ((act_drugweight * 1000) / vol_diluent)

def conc_mgit(crit_concentration):
    """
    Calculate the final MGIT concentration after dilution.
    Args:
        crit_concentration (float): Critical concentration (mg/mL).
    Returns:
        float: Final MGIT concentration (mg/mL).
    """
    return (crit_concentration * 8.4) / 0.1

def vol_workingsol(num_mgits):
    """
    Calculate the volume of stock solution needed to prepare a working solution of a given concentration and volume.
    Args:
        num_mgits (int): Number of MGITs to prepare.
    Returns:
        float: Volume of stock solution to use (mL).
    """
    return (num_mgits * 0.12) + 0.36

def vol_ss_to_ws(vol_workingsol, conc_mgit, conc_stock):
    """
    Calculate the volume of working solution to add to reach the target concentration in the final solution.
    Args:
        vol_workingsol (float): Volume of working solution (mL).
        conc_mgit (float): Concentration of MGIT (mg/mL).
        conc_stock (float): Concentration of stock solution (mg/mL).
    Returns:
        float: Volume of working solution to add (mL).
    """
    return (vol_workingsol * conc_mgit) / conc_stock

def vol_final_dil(vol_ss_to_ws, vol_workingsol):
    """
    Calculate the volume of stock solution and diluent needed for the final dilution step.
    Args:
        vol_ss_to_ws (float): Volume of stock solution to working solution (mL).
        vol_workingsol (float): Volume of working solution (mL).
    Returns:
        tuple: (volume of stock solution to add (mL), volume of diluent to add (mL))
    """
    return vol_workingsol - vol_ss_to_ws

def vol_ssleft(vol_ss_to_ws, vol_diluent):
    """
    Calculate the volume of stock solution left after the final dilution step.
    Args:
        vol_ss_to_ws (float): Volume of stock solution to working solution (mL).
        vol_final_dil (float): Volume of final dilution (mL).
    Returns:
        float: Volume of stock solution left (mL).
    """
    return vol_diluent - vol_ss_to_ws