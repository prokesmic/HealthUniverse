"""Pytest fixtures — temp SQLite, no API keys needed.

We set DB_PATH BEFORE any project imports so `db.py`'s module-level
DB_PATH resolution picks it up.
"""
from __future__ import annotations

import os
import sys
import tempfile
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Critical: set test env BEFORE importing anything from the project.
_TEST_DIR = tempfile.TemporaryDirectory(prefix="hu-tests-")
TEST_DB = str(Path(_TEST_DIR.name) / "fixture.db")
os.environ["DB_PATH"]         = TEST_DB
os.environ["HU_READ_ONLY"]    = ""
os.environ["ANTHROPIC_API_KEY"] = "sk-test"
os.environ["PROFILE_SECRET"]  = "test-secret"

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    """Tests use ASGI and mocks; an accidental external call must fail."""
    def blocked(*args, **kwargs):
        raise AssertionError("External network is forbidden in tests")
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)

import db                                             # noqa: E402
db.DB_PATH = Path(TEST_DB)        # override the .env-loaded production path
db.init_db()


def _reset_db() -> None:
    if Path(TEST_DB).exists():
        Path(TEST_DB).unlink()
    db.init_db()


@pytest.fixture
def tmpdb():
    """Fresh test DB per test."""
    _reset_db()
    return db


@pytest.fixture
def client(tmpdb):
    from fastapi.testclient import TestClient
    from web.app import app
    return TestClient(app)


@pytest.fixture
def seeded(tmpdb):
    with tmpdb.connect() as conn:
        f = tmpdb.upsert_entity(conn, slug="magnesium", name="Magnesium",
                                kind="supplement")
        o = tmpdb.upsert_entity(conn, slug="sleep_quality",
                                name="Sleep quality", kind="process")
        cur = conn.execute(
            "INSERT INTO edge (factor_id, outcome_id, direction, tier, "
            "summary, mechanism, population, seed_source) "
            "VALUES (?, ?, 'protective', 'B', ?, ?, 'general adult', 'claude_seed')",
            (f, o, "Modest improvement in sleep quality.",
             "NMDA modulation."),
        )
        eid = cur.lastrowid
        for n in (332, 46, 12):
            conn.execute(
                "INSERT INTO evidence (edge_id, citation, year, study_type, "
                "n_participants, direction, quality, notes) "
                "VALUES (?, ?, 2021, 'rct', ?, 'protective', 'moderate', 'note')",
                (eid, f"Test{n} et al 2021 J Sleep", n))
    return {"factor_id": f, "outcome_id": o, "edge_id": eid}
