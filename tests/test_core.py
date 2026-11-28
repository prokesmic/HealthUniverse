"""The public levels (web/core.py), the narrowed site and their off-switches.

28.11.2026. What these pin: only core edges are recommended anywhere; an
unchecked edge never leaves the working DB; a published DB without a core
is refused; and both environment switches really bring the old behaviour
back (the rollback path).
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from web import core

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_web_db_core", ROOT / "scripts" / "build_web_db.py")
bwd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bwd)


def _edge(conn, db, factor, outcome, *, tier="B", status="verified_evidence",
          verified_rows=2, seed="manual", tier_actor=None, direction="protective"):
    f = db.upsert_entity(conn, slug=factor.lower().replace(" ", "_"), name=factor, kind="supplement")
    o = db.upsert_entity(conn, slug=outcome.lower().replace(" ", "_"), name=outcome, kind="condition")
    eid = conn.execute(
        "INSERT INTO edge (factor_id, outcome_id, direction, tier, summary, population, "
        "seed_source, review_status) VALUES (?,?,?,?,?, 'general adult', ?, ?)",
        (f, o, direction, tier, f"{factor} and {outcome} summary.", seed, status)).lastrowid
    for i in range(verified_rows):
        conn.execute("INSERT INTO evidence (edge_id, citation, pmid, study_type, relevance_status) "
                     "VALUES (?,?,?, 'meta_analysis', 'verified')", (eid, f"Cite {eid}-{i}", f"{eid}00{i}"))
    if tier_actor:
        conn.execute("INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
                     "VALUES (?, 'tier', 'C', ?, 'test', ?)", (eid, tier, tier_actor))
    return eid


@pytest.fixture
def graph(tmpdb, monkeypatch):
    monkeypatch.setattr(core, "HIDDEN_FILE", Path("/nonexistent/hidden_edges.json"))
    with tmpdb.connect() as conn:
        ids = {
            "core": _edge(conn, tmpdb, "Corefactor", "Coreoutcome"),
            "local_model": _edge(conn, tmpdb, "Gemmafactor", "Gemmaoutcome", tier="A", seed="gemma_daily"),
            "local_promoted": _edge(conn, tmpdb, "Promofactor", "Promooutcome", tier="A",
                                    seed="claude_seed", tier_actor="gemma_daily"),
            "one_row": _edge(conn, tmpdb, "Onerowfactor", "Onerowoutcome", tier="A", verified_rows=1),
            "weak": _edge(conn, tmpdb, "Weakfactor", "Weakoutcome", status="weak_evidence"),
            "tier_c": _edge(conn, tmpdb, "Emergingfactor", "Emergingoutcome", tier="C"),
            "unchecked": _edge(conn, tmpdb, "Uncheckedfactor", "Uncheckedoutcome", tier="A",
                               status="unreviewed"),
            "recheck": _edge(conn, tmpdb, "Recheckfactor", "Recheckoutcome", status="needs_recheck"),
        }
    return ids


def _levels(db) -> dict[int, str]:
    with db.connect() as conn:
        return {r[0]: r[1] for r in conn.execute(f"SELECT e.id, {core.level_sql('e')} FROM edge e")}


def test_levels(graph, tmpdb, monkeypatch):
    lv = _levels(tmpdb)
    assert lv[graph["core"]] == "core"
    # The approved definition: tier, verified, two verified citations.
    assert lv[graph["local_model"]] == "core"
    assert lv[graph["local_promoted"]] == "core"
    # Optional stricter rule: an A/B tier the local model set alone is not core.
    monkeypatch.setenv("HU_CORE_STRICT_PROMOTION", "1")
    strict = _levels(tmpdb)
    assert strict[graph["core"]] == "core"
    assert strict[graph["local_model"]] == "labelled"
    assert strict[graph["local_promoted"]] == "labelled"
    assert lv[graph["one_row"]] == "labelled"
    assert lv[graph["weak"]] == "labelled"
    assert lv[graph["tier_c"]] == "labelled"
    assert lv[graph["unchecked"]] == "hidden"
    assert lv[graph["recheck"]] == "hidden"


def test_home_and_discoveries_recommend_only_core(graph, client, monkeypatch):
    for path in ("/", "/discoveries"):
        html = client.get(path).text
        assert "Corefactor" in html, path
        for name in ("Onerowfactor", "Weakfactor",
                     "Emergingfactor", "Uncheckedfactor", "Recheckfactor"):
            assert name not in html, (path, name)
    # The switch really is the rollback: gate off, the old selection is back.
    monkeypatch.setenv("HU_CORE_GATE", "0")
    assert "Onerowfactor" in client.get("/").text


def test_rss_carries_only_core(graph, tmpdb, client):
    with tmpdb.connect() as conn:
        for key in ("core", "weak"):
            conn.execute("INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
                         "VALUES (?, 'tier', 'C', 'B', 'new synthesis', 'claude_adjudicator')",
                         (graph[key],))
    xml = client.get("/feed.rss").text
    assert "Corefactor" in xml and "Weakfactor" not in xml


def test_stack_brief_shows_core_and_counts_the_rest(graph, client, monkeypatch):
    html = client.get("/stack?items=Corefactor,Weakfactor,Uncheckedfactor").text
    assert "Coreoutcome" in html
    assert "Weakoutcome" not in html
    assert "Nothing in the verified core for this item yet" in html
    assert "1 lower-confidence" in html                # the weak edge is counted, not shown
    assert "Uncheckedoutcome" not in html
    monkeypatch.setenv("HU_CORE_GATE", "0")
    assert "Weakoutcome" in client.get("/stack?items=Weakfactor").text


def test_lists_label_non_core_and_drop_hidden(graph, client):
    html = client.get("/tier/A").text
    assert "Onerowfactor" in html and "not in verified core" in html
    assert "Uncheckedfactor" not in html
    html_b = client.get("/tier/B").text
    assert "Corefactor" in html_b and "verified core" in html_b
    assert "Recheckfactor" not in html_b


def test_hidden_edge_has_no_page(graph, client, monkeypatch, tmp_path):
    assert client.get(f"/edge/{graph['unchecked']}").status_code == 404
    assert client.get(f"/edge/{graph['core']}").status_code == 200
    assert "Verified core" in client.get(f"/edge/{graph['core']}").text
    assert "Not in verified core" in client.get(f"/edge/{graph['weak']}").text
    # The manual list hides an edge the automatic checks let through.
    f = tmp_path / "hidden_edges.json"
    f.write_text(json.dumps({"edges": [{"id": graph["core"], "reason": "test"}]}))
    monkeypatch.setattr(core, "HIDDEN_FILE", f)
    assert client.get(f"/edge/{graph['core']}").status_code == 404


def _copy_working_db(tmpdb, tmp_path) -> Path:
    src = tmp_path / "work.db"
    s = sqlite3.connect(tmpdb.DB_PATH)
    d = sqlite3.connect(src)
    s.backup(d)
    s.close(); d.close()
    return src


def test_builder_stores_levels_and_leaves_hidden_edges_out(graph, tmpdb, tmp_path, monkeypatch):
    monkeypatch.setattr(core, "CORE_FLOOR", 1)
    hidden_file = tmp_path / "hidden_edges.json"
    hidden_file.write_text(json.dumps({"edges": [{"id": graph["tier_c"], "reason": "by hand"}]}))
    monkeypatch.setattr(core, "HIDDEN_FILE", hidden_file)
    src = _copy_working_db(tmpdb, tmp_path)
    out = tmp_path / "web.db"
    stats = bwd.build(src, out)
    c = sqlite3.connect(out)
    got = {r[0]: r[1] for r in c.execute("SELECT id, public_level FROM edge")}
    assert got[graph["core"]] == "core"
    assert got[graph["weak"]] == "labelled"
    for key in ("unchecked", "recheck", "tier_c"):
        assert graph[key] not in got, key
        assert c.execute("SELECT COUNT(*) FROM evidence WHERE edge_id=?", (graph[key],)).fetchone()[0] == 0
    assert stats["hidden_removed"] == 3 and stats["levels"]["core"] == 3
    # The working DB is only read: nothing removed, no column added.
    w = sqlite3.connect(src)
    assert w.execute("SELECT COUNT(*) FROM edge").fetchone()[0] == len(graph)
    assert not core.has_column(w)


def test_builder_refuses_a_db_without_a_core(graph, tmpdb, tmp_path, monkeypatch):
    """Verifier state lost (statuses wiped) must not replace the live DB."""
    monkeypatch.setattr(core, "CORE_FLOOR", 4)          # the fixture has three core edges
    src = _copy_working_db(tmpdb, tmp_path)
    with pytest.raises(bwd.BuildError, match="core edges"):
        bwd.build(src, tmp_path / "web.db")
    dst = tmp_path / "live.db"
    dst.write_bytes(b"previous")
    monkeypatch.setattr(bwd, "ntfy", lambda *a, **k: True)
    assert bwd.main(["--src", str(src), "--dst", str(dst)]) == 1
    assert dst.read_bytes() == b"previous"


def test_builder_gate_off_publishes_everything(graph, tmpdb, tmp_path):
    src = _copy_working_db(tmpdb, tmp_path)
    out = tmp_path / "web.db"
    stats = bwd.build(src, out, gate=False)
    assert stats["counts"]["edge"] == len(graph) and stats["hidden_removed"] == 0


@pytest.mark.parametrize("path", ["/labs", "/me/data", "/prevent", "/my-plan", "/start",
                                  "/coach", "/claim-check", "/products", "/protocols", "/score"])
def test_narrowed_pages_go_home_and_come_back_with_the_switch(client, path, monkeypatch):
    r = client.get(path, follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/"
    monkeypatch.setenv("HU_NARROW", "0")
    assert client.get(path, follow_redirects=False).status_code != 302


def test_narrowed_api_and_forms_answer_404(client):
    assert client.post("/api/me/parse-lab-image").status_code == 404
    assert client.post("/api/pro-waitlist", data={"email": "a@example.com"}).status_code == 404
    assert client.post("/api/claim-check", json={"claim": "x"}).status_code == 404
    assert client.get("/api/me/snp-evidence?rsid=rs1&genotype=AA").status_code == 404
    assert client.get("/api/me/stack?items=").status_code == 200      # the brief's JSON twin stays


def test_narrowed_navigation(client, monkeypatch):
    html = client.get("/").text
    nav = html[html.index('aria-label="Primary"'): html.index("</nav>", html.index('aria-label="Primary"'))]
    assert nav.count("<a ") == 5
    for gone in ("/me/data", "/me/wearables", "/start", "/my-plan"):
        assert f'href="{gone}"' not in html
    assert "location.replace('/start" not in html       # no A/B redirect off the home page
    monkeypatch.setenv("HU_NARROW", "0")
    assert 'href="/me/data"' in client.get("/").text


def test_is_off_matches_whole_segments_only():
    assert core.is_off("/me") and core.is_off("/me/data") and core.is_off("/api/me/account")
    assert not core.is_off("/methodology") and not core.is_off("/stack") and not core.is_off("/")
    assert not core.is_off("/api/me/stack") and not core.is_off("/briefs") and not core.is_off("/breakthroughs")


def test_same_event_from_three_sources_is_one_card():
    from web import breakthroughs as bx
    def card(i, source, intervention, day="2026-11-25", stage="approved", cat="oncology"):
        return {"id": i, "source_name": source, "source_url": f"https://x/{i}", "published_at": day,
                "stage": stage, "category": cat, "detail": {"intervention": intervention}}
    rows = [
        card("stat", "STAT News", "Ekitna (bezuclastinib) with Sutent"),
        card("fda", "FDA Drug Safety", "bezuclastinib and sunitinib", day="2026-11-24"),
        card("other", "FDA Approvals", "giredestrant"),
        card("late", "Endpoints News", "bezuclastinib", day="2026-12-20"),           # a later event
        card("trial", "JAMA", "bezuclastinib", stage="phase3"),                      # another stage
        card("vague", "STAT News", "new treatment combination therapy"),             # nothing named
        card("vague2", "JAMA", "new treatment combination therapy"),
    ]
    out = bx.collapse_same_event(rows)
    assert [r["id"] for r in out] == ["fda", "other", "late", "trial", "vague", "vague2"]
    assert [s["id"] for s in out[0]["also_sources"]] == ["stat"]
    assert "also_sources" not in rows[1]                # the stored feed is not touched


def test_verifier_rollup_does_not_condemn_what_it_could_not_check(tmpdb, monkeypatch):
    """PubMed or Ollama down: rows come back 'missing'. That is not a verdict,
    and the rows are tried again next run."""
    import verify_evidence as ve
    with tmpdb.connect() as conn:
        eid = _edge(conn, tmpdb, "Outagefactor", "Outageoutcome", status="unreviewed", verified_rows=0)
        conn.execute("INSERT INTO evidence (edge_id, citation, pmid) VALUES (?, 'A', '111')", (eid,))
        conn.execute("CREATE TABLE IF NOT EXISTS verifier_audit (edge_id, evidence_id, pmid, pubmed_title, "
                     "stored_citation, factor_name, outcome_name, relevance_score, decision, checked_at)")
    monkeypatch.setattr(ve, "DB_PATH", tmpdb.DB_PATH)
    monkeypatch.setattr(ve, "_embed", lambda text: [1.0, 0.0])
    monkeypatch.setattr(ve.time, "sleep", lambda s: None)
    args = type("A", (), {"tier": "", "limit": 0, "only_unverified": True})()

    monkeypatch.setattr(ve, "_eutils_titles", lambda pmids: {})          # outage
    ve.cmd_audit(args)
    with tmpdb.connect() as conn:
        assert conn.execute("SELECT review_status FROM edge WHERE id=?", (eid,)).fetchone()[0] == "unreviewed"
        assert conn.execute("SELECT relevance_status FROM evidence WHERE edge_id=?", (eid,)).fetchone()[0] == "missing"

    monkeypatch.setattr(ve, "_eutils_titles", lambda pmids: {p: "Outagefactor and Outageoutcome" for p in pmids})
    ve.cmd_audit(args)                                                    # back up: retried
    with tmpdb.connect() as conn:
        assert conn.execute("SELECT review_status FROM edge WHERE id=?", (eid,)).fetchone()[0] == "verified_evidence"


def test_stack_brief_does_not_guess_a_different_factor(tmpdb, client):
    """'berberine' used to be answered with the evidence for 'Berries'."""
    with tmpdb.connect() as conn:
        _edge(conn, tmpdb, "Berries", "Bloodpressureoutcome")
        _edge(conn, tmpdb, "Magnesium", "Sleepoutcome")
    html = client.get("/stack?items=berberine,magnesum,berries").text
    assert "couldn't match <b>berberine</b>" in html
    assert "Sleepoutcome" in html                      # a real typo still matches
    assert html.count("Bloodpressureoutcome") >= 1     # asked for by its own name
    wrote = html.split("You wrote")
    berberine = next(b for b in wrote if b.lstrip(": ").startswith("<b>berberine") or "berberine</" in b[:80])
    assert "Bloodpressureoutcome" not in berberine


def test_restore_review_puts_back_only_the_check_state(graph, tmpdb, tmp_path):
    spec2 = importlib.util.spec_from_file_location("restore_review", ROOT / "scripts" / "restore_review.py")
    rr = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(rr)
    backup = _copy_working_db(tmpdb, tmp_path)
    with tmpdb.connect() as conn:                       # a verifier run, then new data
        conn.execute("UPDATE edge SET review_status='needs_recheck' WHERE id=?", (graph["core"],))
        conn.execute("UPDATE evidence SET relevance_status='flagged', relevance_score=0.1 WHERE edge_id=?",
                     (graph["core"],))
        new = _edge(conn, tmpdb, "Laterfactor", "Lateroutcome", status="weak_evidence")
    assert rr.restore(tmpdb.DB_PATH, backup, write=False) == {"edges": 1, "evidence": 2}
    assert _levels(tmpdb)[graph["core"]] == "hidden"    # report only: nothing written
    rr.restore(tmpdb.DB_PATH, backup, write=True)
    lv = _levels(tmpdb)
    assert lv[graph["core"]] == "core"
    assert lv[new] == "labelled"                        # added after the backup: untouched
