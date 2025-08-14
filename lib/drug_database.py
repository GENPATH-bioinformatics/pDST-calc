import pandas as pd
from pathlib import Path

def load_drug_data(filepath=None):
    """Load drug data from CSV file with proper error handling.

    Args:
        filepath (str or Path, optional): Path to CSV file. If None, uses default data file.

    Returns:
        pd.DataFrame: DataFrame containing drug data. Returns empty DataFrame if file is empty.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file exists but cannot be parsed as valid CSV.
    """
    if filepath is None:
        filepath = Path(__file__).resolve().parent.parent / "data" / "tb_drugs.csv"

    try:
        return pd.read_csv(filepath)
    except pd.errors.EmptyDataError:
        # Return empty DataFrame with expected columns for empty files
        return pd.DataFrame(columns=['Drug', 'OrgMolecular_Weight', 'Diluent', 'Critical_Concentration'])
    except Exception as e:
        # Re-raise other exceptions (like FileNotFoundError) as-is
        raise
