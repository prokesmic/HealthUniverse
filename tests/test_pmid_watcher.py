from __future__ import annotations

import pmid_watcher


def _insert_edge_with_pmid(tmpdb, *, pmid: str = "12345678", citation: str = "Retracted Trial et al. 2000"):
    with tmpdb.connect() as conn:
        factor_id = tmpdb.upsert_entity(conn, "omega3", "Omega-3", "supplement")
        outcome_id = tmpdb.upsert_entity(conn, "stroke", "Stroke", "condition")
        edge_id = conn.execute(
            "INSERT INTO edge (factor_id, outcome_id, direction, tier, summary, mechanism, population, seed_source) "
            "VALUES (?, ?, 'protective', 'B', ?, ?, 'adults', 'claude_seed')",
            (factor_id, outcome_id, "Omega-3 may lower stroke risk.", "Triglyceride lowering."),
        ).lastrowid
        conn.execute(
            "INSERT INTO evidence (edge_id, citation, pmid, year, study_type, n_participants, direction, quality, notes) "
            "VALUES (?, ?, ?, 2000, 'rct', 120, 'protective', 'moderate', 'watch me')",
            (edge_id, citation, pmid),
        )
    return {"edge_id": edge_id, "pmid": pmid, "citation": citation}


def test_pmid_watcher_marks_retraction_and_writes_history(tmpdb, monkeypatch):
    seeded = _insert_edge_with_pmid(tmpdb)

    def fake_fetch(pmids, client=None):
        assert pmids == [seeded["pmid"]]
        return {
            seeded["pmid"]: {
                "is_retracted": 1,
                "retraction_note": "pubtype contains a retraction marker",
            }
        }

    monkeypatch.setattr(pmid_watcher, "fetch_status_batch", fake_fetch)
    result = pmid_watcher.run(limit=50, push=False, sleep_s=0.0)

    assert result["checked"] == 1
    assert result["retracted"] == 1
    assert result["newly_retracted_pmids"] == 1
    assert result["history_rows"] == 1

    with tmpdb.connect() as conn:
        status = conn.execute(
            "SELECT * FROM evidence_status WHERE pmid=?",
            (seeded["pmid"],),
        ).fetchone()
        history = conn.execute(
            "SELECT * FROM edge_history WHERE edge_id=? AND actor='pmid_watcher'",
            (seeded["edge_id"],),
        ).fetchall()

    assert status is not None
    assert status["is_retracted"] == 1
    assert "retraction marker" in status["retraction_note"]
    assert len(history) == 1
    assert seeded["citation"] in history[0]["reason"]


def test_pmid_watcher_only_records_new_retraction_once(tmpdb, monkeypatch):
    seeded = _insert_edge_with_pmid(tmpdb)

    def fake_fetch(pmids, client=None):
        return {
            seeded["pmid"]: {
                "is_retracted": 1,
                "retraction_note": "pubtype contains a retraction marker",
            }
        }

    monkeypatch.setattr(pmid_watcher, "fetch_status_batch", fake_fetch)

    first = pmid_watcher.run(limit=50, push=False, sleep_s=0.0)
    second = pmid_watcher.run(limit=50, push=False, sleep_s=0.0)

    assert first["history_rows"] == 1
    assert second["history_rows"] == 0

    with tmpdb.connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM edge_history WHERE edge_id=? AND actor='pmid_watcher'",
            (seeded["edge_id"],),
        ).fetchone()["c"]
    assert count == 1


def test_edge_page_shows_retraction_banner(client, tmpdb):
    seeded = _insert_edge_with_pmid(tmpdb, citation="Withdrawn Study et al. 2001")
    with tmpdb.connect() as conn:
        conn.execute(
            "INSERT INTO evidence_status (pmid, is_retracted, retraction_note) VALUES (?, 1, ?)",
            (seeded["pmid"], "pubtype contains a retraction marker"),
        )

    response = client.get(f"/edge/{seeded['edge_id']}")
    assert response.status_code == 200
    assert "RETRACTED" in response.text
    assert "Tier should be reconsidered." in response.text
