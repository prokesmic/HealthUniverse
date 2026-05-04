from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
import web.app as web_app


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "healthuniverse.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(db, "READ_ONLY", False)
    monkeypatch.setattr(web_app, "OG_CACHE_DIR", tmp_path / "cache" / "og")
    db.init_db()
    return db_path


@pytest.fixture
def client(isolated_db):
    return TestClient(web_app.app)


@pytest.fixture
def seeded_edge(isolated_db):
    with db.connect() as conn:
        factor_id = db.upsert_entity(
            conn,
            slug="magnesium",
            name="Magnesium",
            kind="supplement",
            aliases=["Mg"],
            description="Mineral supplement",
        )
        outcome_id = db.upsert_entity(
            conn,
            slug="sleep_quality",
            name="Sleep quality",
            kind="process",
            aliases=["sleep"],
            description="Sleep architecture and restfulness",
        )
        edge_id = conn.execute(
            "INSERT INTO edge (factor_id, outcome_id, direction, tier, effect_size, effect_quant, "
            "population, mechanism, summary, caveats, seed_source) "
            "VALUES (?, ?, 'protective', 'B', 'small', 'RR 0.90', 'general adult', "
            "'Supports muscle and nervous system function.', "
            "'Magnesium may support sleep quality in some populations.', "
            "'Dose and deficiency status matter.', 'claude_seed')",
            (factor_id, outcome_id),
        ).lastrowid
        conn.execute(
            "INSERT INTO evidence (edge_id, citation, year, study_type, n_participants, direction, quality, notes) "
            "VALUES (?, 'Smith 2024 Sleep Journal', 2024, 'rct', 180, 'protective', 'moderate', "
            "'Improved subjective sleep scores in deficient adults.')",
            (edge_id,),
        )
        conn.execute(
            "INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
            "VALUES (?, 'seed', NULL, '{\"tier\":\"B\"}', 'seeded', 'claude_seed')",
            (edge_id,),
        )
    return edge_id
