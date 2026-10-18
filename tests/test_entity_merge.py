"""Entity merge (18.10.2026): duplicate entities fold into one, old slugs and
edge ids keep resolving, the stronger edge survives a clash, and the live DB
has no duplicate-name groups left except the deliberate ones."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import merge_duplicate_entities as me  # noqa: E402

LIVE_DB = ROOT / "data" / "healthuniverse.db"


def _edge(conn, f, o, tier, pop="general adult", pmids=()):
    eid = conn.execute(
        "INSERT INTO edge (factor_id, outcome_id, direction, tier, population, seed_source) "
        "VALUES (?, ?, 'protective', ?, ?, 'manual')", (f, o, tier, pop)).lastrowid
    for p in pmids:
        conn.execute("INSERT INTO evidence (edge_id, citation, study_type, direction, pmid) "
                     "VALUES (?, 'X et al 2020', 'rct', 'protective', ?)", (eid, p))
    return eid


def _world(tmpdb):
    """aerobic → cvd (C) and aerobic → cardiovascular_disease (A) on the same
    population; walking → cardiovascular_disease only on the old slug."""
    with tmpdb.connect() as conn:
        ids = {s: tmpdb.upsert_entity(conn, s, n, k) for s, n, k in (
            ("cvd", "Cardiovascular disease", "condition"),
            ("cardiovascular_disease", "Cardiovascular disease", "condition"),
            ("aerobic_exercise", "Aerobic exercise", "activity"),
            ("walking_daily", "Daily walking", "activity"))}
        weak = _edge(conn, ids["aerobic_exercise"], ids["cvd"], "C", pmids=("1",))
        strong = _edge(conn, ids["aerobic_exercise"], ids["cardiovascular_disease"], "A", pmids=("1", "2"))
        walk = _edge(conn, ids["walking_daily"], ids["cardiovascular_disease"], "B")
        conn.execute("INSERT INTO seed_topic (factor_slug, outcome_slug) VALUES ('walking_daily', 'cardiovascular_disease')")
    return ids, weak, strong, walk


def test_merge_repoints_folds_into_stronger_edge_and_redirects(tmpdb):
    ids, weak, strong, walk = _world(tmpdb)
    with tmpdb.connect() as conn:
        me.ensure_schema(conn)
        out = me.merge_entity(conn, "cvd", "cardiovascular_disease", "abbreviation")
    assert out["folded"] == 1 and out["repointed"] == 2
    with tmpdb.connect() as conn:
        # the A-tier edge survives the clash, moves to cvd and keeps both PMIDs once
        row = conn.execute("SELECT tier, outcome_id FROM edge WHERE id=?", (strong,)).fetchone()
        assert (row["tier"], row["outcome_id"]) == ("A", ids["cvd"])
        assert sorted(r[0] for r in conn.execute("SELECT pmid FROM evidence WHERE edge_id=?", (strong,))) == ["1", "2"]
        assert conn.execute("SELECT 1 FROM edge WHERE id=?", (weak,)).fetchone() is None
        assert conn.execute("SELECT new_id FROM edge_redirect WHERE old_id=?", (weak,)).fetchone()[0] == strong
        # walking's edge is repointed, with the change written to edge_history
        assert conn.execute("SELECT outcome_id FROM edge WHERE id=?", (walk,)).fetchone()[0] == ids["cvd"]
        h = conn.execute("SELECT old_value, new_value, actor FROM edge_history WHERE edge_id=? AND field='outcome_id'",
                         (walk,)).fetchone()
        assert tuple(h) == ("cardiovascular_disease", "cvd", "merge_entities")
        # the old row is gone, its slug is an alias and a redirect
        assert conn.execute("SELECT 1 FROM entity WHERE slug='cardiovascular_disease'").fetchone() is None
        assert "cardiovascular_disease" in json.loads(
            conn.execute("SELECT aliases FROM entity WHERE slug='cvd'").fetchone()[0])
        assert tmpdb.resolve_slug(conn, "cardiovascular_disease") == "cvd"
        assert conn.execute("SELECT outcome_slug FROM seed_topic").fetchone()[0] == "cvd"


def test_old_slug_does_not_come_back_and_chains_resolve(tmpdb):
    _world(tmpdb)
    with tmpdb.connect() as conn:
        me.ensure_schema(conn)
        me.merge_entity(conn, "cvd", "cardiovascular_disease", "abbreviation")
        cvd = conn.execute("SELECT id FROM entity WHERE slug='cvd'").fetchone()[0]
        # a seeding script that still says cardiovascular_disease gets cvd, not a new duplicate
        assert tmpdb.upsert_entity(conn, "cardiovascular_disease", "Cardiovascular disease", "condition") == cvd
        assert conn.execute("SELECT COUNT(*) FROM entity WHERE name='Cardiovascular disease'").fetchone()[0] == 1
        conn.execute("INSERT INTO entity_redirect (old_slug, new_slug) VALUES ('heart_disease', 'cardiovascular_disease')")
        assert tmpdb.resolve_slug(conn, "heart_disease") == "cvd"
        assert tmpdb.resolve_slug(conn, "no_such_thing") == "no_such_thing"


def test_old_entity_url_and_old_edge_url_redirect(client, tmpdb):
    _, weak, strong, _ = _world(tmpdb)
    with tmpdb.connect() as conn:
        me.ensure_schema(conn)
        me.merge_entity(conn, "cvd", "cardiovascular_disease", "abbreviation")
    r = client.get("/api/entities/cardiovascular_disease", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"].endswith("/api/entities/cvd")
    r = client.get(f"/edge/{weak}", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"].endswith(f"/edge/{strong}")
    assert client.get("/api/entities/cvd").json()["entity"]["slug"] == "cvd"


def test_breakthrough_cards_follow_the_mapping(tmp_path):
    p = tmp_path / "bx.json"
    p.write_text(json.dumps({"items": [
        {"id": "a", "corpus": {"factor": {"slug": "ppi"}, "outcome": {"slug": "cardiovascular_disease"},
                               "outcome_edges": [{"id": 496, "summary": "old"}, {"id": 813, "summary": "kept"},
                                                 {"id": 7, "summary": "moved"}]}},
        {"id": "b", "corpus": {"factor": {"slug": "statins"}, "outcome": None}}]}))
    assert me.rewrite_breakthroughs(me.mapping(), p, edge_redirects={496: 813, 7: 70}) == 4
    items = json.loads(p.read_text())["items"]
    assert items[0]["corpus"]["factor"]["slug"] == "proton_pump_inhibitors"
    assert items[0]["corpus"]["outcome"]["slug"] == "cvd"
    # a folded edge already listed under its surviving id is dropped, not duplicated
    assert [(e["id"], e["summary"]) for e in items[0]["corpus"]["outcome_edges"]] == [(813, "kept"), (70, "moved")]
    assert items[1]["corpus"]["factor"]["slug"] == "statins"


def test_profile_with_old_slugs_is_canonicalised(monkeypatch):
    import db
    import profile as pr
    monkeypatch.setattr(db, "_REDIRECTS", {"ppi": "proton_pump_inhibitors", "type_2_diabetes": "t2d"})
    p = pr.decode(pr.encode(pr.Profile(stack=["ppi", "magnesium", "proton_pump_inhibitors"],
                                       conditions=["type_2_diabetes"])))
    assert p.stack == ["proton_pump_inhibitors", "magnesium"]
    assert p.conditions == ["t2d"]


def test_mapping_is_consistent():
    m = me.mapping()
    canon = {c for c, _, _ in me.MERGES}
    assert not canon & set(m), "a canonical slug is itself merged away"
    assert len(m) == sum(len(o) for _, o, _ in me.MERGES), "a slug is merged twice"


def test_live_graph_has_only_deliberate_duplicate_names():
    """Fails if the merge is reverted or a seeding run re-creates a duplicate."""
    conn = sqlite3.connect(f"file:{LIVE_DB}?mode=ro", uri=True)
    left = [sorted(g) for g in me.name_groups(conn) if frozenset(g) not in me.KEEP_APART]
    assert left == []
    live = {r[0] for r in conn.execute("SELECT slug FROM entity")}
    assert not live & set(me.mapping()), "a merged-away entity is back"
    redirects = dict(conn.execute("SELECT old_slug, new_slug FROM entity_redirect"))
    assert all(redirects.get(o) == c for o, c in me.mapping().items())
    # no merged edge id points nowhere
    dangling = conn.execute("""SELECT COUNT(*) FROM edge_redirect r
                               LEFT JOIN edge e ON e.id=r.new_id WHERE e.id IS NULL""").fetchone()[0]
    assert dangling == 0
