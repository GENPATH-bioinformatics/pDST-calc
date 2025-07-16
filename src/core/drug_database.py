import pandas as pd
from pathlib import Path

def load_drug_data(filepath=None):
    if filepath is None:
        filepath = Path(__file__).resolve().parent.parent.parent / "data" / "tb_drugs.csv"
    return pd.read_csv(filepath)