import os
import tempfile
import json

import pytest

from app.api.database import DatabaseManager


@pytest.fixture()
def temp_db_path(tmp_path):
    return str(tmp_path / "test_dstcalc.db")


@pytest.fixture()
def db(temp_db_path):
    # Each test gets a fresh database
    return DatabaseManager(db_path=temp_db_path)


def test_init_creates_tables(db: DatabaseManager):
    # Query sqlite_master to ensure expected tables exist
    with db.get_connection() as conn:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users','session','drugs')"
        )
        names = {row[0] for row in cur.fetchall()}
        assert {"users", "session", "drugs"}.issubset(names)


def test_user_insert_and_lookup(db: DatabaseManager):
    uid = db.insert_user("alice", "hash123")
    assert isinstance(uid, int)
    user = db.get_user_by_username("alice")
    assert user is not None
    assert user["username"] == "alice"
    assert user["password_hash"] == "hash123"


def test_get_or_create_session_and_update(db: DatabaseManager):
    # Create a user and a session
    uid = db.insert_user("bob", "h")
    assert uid
    sid = db.get_or_create_session(uid, "sess1")
    assert isinstance(sid, int)
    # Second call returns same session id
    sid2 = db.get_or_create_session(uid, "sess1")
    assert sid2 == sid
    # Update session preparation JSON
    ok = db.update_session_data(sid, {"foo": {"bar": 1}})
    assert ok is True
    # Verify JSON written
    with db.get_connection() as conn:
        cur = conn.execute("SELECT preparation FROM session WHERE session_id=?", (sid,))
        (prep_str,) = cur.fetchone()
        assert json.loads(prep_str) == {"foo": {"bar": 1}}


def test_drug_crud_and_list(db: DatabaseManager):
    did = db.insert_drug(
        name="DrugX",
        default_dilution="Water",
        default_molecular_weight=123.4,
        critical_value=0.5,
        available=True,
    )
    assert isinstance(did, int)

    drugs = db.get_all_drugs()
    assert any(d["name"] == "DrugX" for d in drugs)

    # Toggle availability
    ok = db.update_drug_availability(did, False)
    assert ok is True
    drugs = db.get_all_drugs()
    found = next(d for d in drugs if d["name"] == "DrugX")
    assert found["available"] is False

    # Delete
    ok = db.delete_drug(did)
    assert ok is True
    drugs = db.get_all_drugs()
    assert not any(d["name"] == "DrugX" for d in drugs)


def test_get_sessiones_by_user(db: DatabaseManager):
    uid = db.insert_user("eve", "p")
    s1 = db.get_or_create_session(uid, "s1")
    s2 = db.get_or_create_session(uid, "s2")
    sessions = db.get_sessiones_by_user(uid)
    assert isinstance(sessions, list)
    assert len(sessions) >= 2

