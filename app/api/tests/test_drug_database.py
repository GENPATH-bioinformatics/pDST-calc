import json

import pytest
import pandas as pd

from app.api.database import DatabaseManager
from app.api import drug_database as dd


@pytest.fixture()
def db(tmp_path):
    return DatabaseManager(db_path=str(tmp_path / "test_dstcalc.db"))


def test_load_drug_data_empty(db):
    # Fresh DB has default drugs populated by initializer
    df = dd.load_drug_data()
    assert isinstance(df, pd.DataFrame)
    assert set(["Drug", "OrgMolecular_Weight", "Diluent", "Critical_Concentration", "Available"]).issubset(df.columns)
    assert len(df) >= 1


def test_get_available_drugs_structure(db):
    drugs = dd.get_available_drugs()
    assert isinstance(drugs, list)
    assert {"name", "default_molecular_weight", "default_dilution", "critical_value", "available"}.issubset(drugs[0].keys())


def test_session_helpers(db):
    uid = db.insert_user("tina", "pw")
    sid = db.get_or_create_session(uid, "S")
    # Ensure adapter returns correct shapes
    all_sessions = dd.get_session_data(uid)
    assert isinstance(all_sessions, list)
    if all_sessions:
        s0 = all_sessions[0]
        assert {"session_id", "session_date", "preparation"}.issubset(s0.keys())
    # Specific session
    specific = dd.get_session_data(uid, sid)
    assert isinstance(specific, list)
    if specific:
        assert specific[0]["session_id"] == sid


def test_get_user_sessions(db):
    uid = db.insert_user("kim", "pw")
    db.get_or_create_session(uid, "A")
    rows = dd.get_user_sessions(uid)
    assert isinstance(rows, list)
    if rows:
        assert {"session_id", "session_name", "session_date"}.issubset(rows[0].keys())

