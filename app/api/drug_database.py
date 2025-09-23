"""
Drug database module for DST Calculator.
Provides access to drug data from SQLite database.
"""

import pandas as pd
import json
from typing import Optional, List, Dict, Any
from app.api.database import db_manager


def load_drug_data(filepath=None):
    """Load drug data from database with proper error handling.

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

def get_session_data(user_id: int, session_id: int = None) -> List[Dict[str, Any]]:
    """Get session data for a user.
    
    Args:
        user_id: ID of the user
        session_id: Optional specific session ID to retrieve
        
    Returns:
        List of session dictionaries with preparation data
    """
    try:
        if session_id:
            # Get specific session
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT session_id, session_name, session_date, preparation FROM session WHERE user_id = ? AND session_id = ?",
                    (user_id, session_id)
                )
                row = cursor.fetchone()
                if row:
                    return [{
                        'session_id': row[0],
                        'session_name': row[1],
                        'session_date': row[2],
                        'preparation': json.loads(row[3]) if row[3] else {}
                    }]
                return []
        else:
            # Get all sessions for user
            return db_manager.get_sessiones_by_user(user_id)
    except Exception as e:
        raise

def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """Return all sessions for a given user (convenience wrapper)."""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT session_id, session_name, session_date FROM session WHERE user_id = ?",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    'session_id': r[0],
                    'session_name': r[1],
                    'session_date': r[2],
                }
                for r in rows
            ]
    except Exception as e:
        raise


