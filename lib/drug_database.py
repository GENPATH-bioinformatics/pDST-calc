"""
Drug database module for DST Calculator.
Provides access to drug data from SQLite database.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from database import db_manager


def load_drug_data(filepath=None):
    """Load drug data from database with proper error handling.
    
    This function maintains backward compatibility with the CSV-based interface
    but now loads data from the SQLite database instead.

    Args:
        filepath (str or Path, optional): Ignored for database-based loading.
            Kept for backward compatibility.

    Returns:
        pd.DataFrame: DataFrame containing drug data. Returns empty DataFrame if no drugs found.

    Raises:
        Exception: If database operations fail.
    """
    try:
        # Get all drugs from database
        drugs = db_manager.get_all_drugs()
        
        if not drugs:
            # Return empty DataFrame with expected columns for no drugs
            return pd.DataFrame(columns=['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration', 'Available'])
        
        # Convert to DataFrame with the same column structure as the original CSV
        df_data = []
        for drug in drugs:
            df_data.append({
                'Drug': drug['name'],
                'OrgMolecular_Weight': drug['default_molecular_weight'],
                'Diluent': drug['default_dilution'],
                'Critical_Concentration': drug['critical_value'],
                'Available': drug['available']
            })
        
        return pd.DataFrame(df_data)
        
    except Exception as e:
        # Re-raise exceptions
        raise


def get_available_drugs() -> List[Dict[str, Any]]:
    """Get all available drugs from the database.
    
    Returns:
        List of drug dictionaries with all fields
    """
    try:
        return db_manager.get_all_drugs()
    except Exception as e:
        raise


def get_drug_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific drug by name.
    
    Args:
        name: Drug name to search for
        
    Returns:
        Drug dictionary if found, None otherwise
    """
    try:
        return db_manager.get_drug_by_name(name)
    except Exception as e:
        raise


def add_drug(name: str, default_dilution: str = None, 
             default_molecular_weight: float = None, mol_max: float = None, 
             critical_value: float = None, available: bool = True) -> Optional[int]:
    """Add a new drug to the database.
    
    Args:
        name: Drug name
        default_dilution: Default dilution value
        default_molecular_weight: Default molecular weight
        mol_max: Maximum molecular value
        critical_value: Critical value
        available: Drug availability status
        
    Returns:
        Drug ID if successful, None if failed
    """
    try:
        return db_manager.insert_drug(
            name=name,
            default_dilution=default_dilution,
            default_molecular_weight=default_molecular_weight,
            mol_max=mol_max,
            critical_value=critical_value,
            available=available
        )
    except Exception as e:
        raise


def update_drug_availability(drug_id: int, available: bool) -> bool:
    """Update the availability status of a drug.
    
    Args:
        drug_id: ID of the drug to update
        available: New availability status
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE drugs SET available = ? WHERE drug_id = ?",
                (available, drug_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        raise


def get_available_drugs_only() -> List[Dict[str, Any]]:
    """Get only available drugs from the database.
    
    Returns:
        List of available drug dictionaries
    """
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT drug_id, name, default_dilution, default_molecular_weight, mol_max, critical_value, available FROM drugs WHERE available = 1"
            )
            drugs = []
            for row in cursor.fetchall():
                drugs.append({
                    'drug_id': row[0],
                    'name': row[1],
                    'default_dilution': row[2],
                    'default_molecular_weight': row[3],
                    'mol_max': row[4],
                    'critical_value': row[5],
                    'available': row[6]
                })
            return drugs
    except Exception as e:
        raise


def delete_drug(drug_id: int) -> bool:
    """Delete a drug from the database.
    
    Args:
        drug_id: ID of the drug to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM drugs WHERE drug_id = ?", (drug_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        raise
