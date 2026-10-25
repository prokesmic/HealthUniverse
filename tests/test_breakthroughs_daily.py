"""breakthroughs_daily: grounding gate, judged-item memory, fair share per source.

Everything external is stubbed before main() runs: RSS, Ollama, the feed
file and the seen file all live in tmp_path / memory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import breakthroughs_daily as bd  # noqa: E402

DESIGN = "This randomized trial assesses the effect of A on B among older adults."


def item(src, n, summary="In 400 patients, A reduced B by 20%."):
    return {"title": f"{src} item {n}", "link": f"https://{src}.example/{n}",
            "summary": summary, "published": "2026-10-05", "source_name": src}


# ─── grounding gate ───────────────────────────────────────────────

def test_gate_rejects_design_only_and_invented_numbers():
    assert "design" in bd.ungrounded(item("j", 1, DESIGN), {"headline": "A helps", "summary": "A improved B."})
    assert "30" in bd.ungrounded(item("j", 2), {"headline": "A cuts B 30%", "summary": "x"})
    assert "letter" in bd.ungrounded({"title": "x", "summary": "To the Editor Dr X", "link": "l"}, {})
    assert bd.ungrounded(item("j", 3), {"headline": "A cuts B by 20%", "summary": "400 patients."}) is None


# ─── interleave ───────────────────────────────────────────────────

def test_interleave_is_round_robin_and_keeps_feed_order():
    c = [item("jama", i) for i in range(5)] + [item("fda", 0), item("stat", 0), item("stat", 1)]
    got = [(x["source_name"], x["title"][-1]) for x in bd.interleave(c)][:5]
    assert got == [("jama", "0"), ("fda", "0"), ("stat", "0"), ("jama", "1"), ("stat", "1")]


# ─── main(): memory of judged links ───────────────────────────────

@pytest.fixture
def world(tmp_path, monkeypatch):
    feeds = {"jama": [item("jama", i) for i in range(30)],
             "fda": [item("fda", i) for i in range(3)]}
    state = {"feed": {"items": []}, "calls": [], "fail": set()}
    monkeypatch.setattr(bd, "FEEDS", [(k, k) for k in feeds])
    monkeypatch.setattr(bd, "fetch_rss", lambda url: [dict(i) for i in feeds[url]])
    monkeypatch.setattr(bd.time, "sleep", lambda s: None)
    monkeypatch.setattr(bd, "load_feed", lambda: json.loads(json.dumps(state["feed"])))
    monkeypatch.setattr(bd, "save_feed", lambda f: state.__setitem__("feed", f))
    monkeypatch.setattr(bd, "match_corpus", lambda f, o: None)
    monkeypatch.setattr(bd, "SEEN_PATH", tmp_path / "cache" / "seen.json")
    monkeypatch.setattr(bd, "enrich", lambda card, teaser="": {**card, "detail": {"summary": "stub"}})
    monkeypatch.setattr(bd, "link_corpus", lambda card: card)

    def classify(raw):
        state["calls"].append(raw["link"])
        if raw["link"] in state["fail"]:
            return None                       # Ollama error / unparseable
        return {"is_breakthrough": False, "strength": 0.1}
    monkeypatch.setattr(bd, "gemma_classify", classify)
    return state


def test_fda_is_reached_even_when_jama_fills_the_limit(world):
    bd.main(["--limit", "6"])
    assert sum("fda" in c for c in world["calls"]) == 3


def test_judged_items_are_not_sent_again(world):
    bd.main(["--limit", "6"])
    first = list(world["calls"]); world["calls"].clear()
    bd.main(["--limit", "6"])
    assert not set(first) & set(world["calls"])
    seen = json.loads(bd.SEEN_PATH.read_text())
    assert set(first) <= set(seen) and seen[first[0]]["verdict"] == "rejected"


def test_ollama_failure_is_retried_not_remembered(world):
    world["fail"].add("https://fda.example/0")
    bd.main(["--limit", "6"])
    assert "https://fda.example/0" not in json.loads(bd.SEEN_PATH.read_text())
    world["calls"].clear(); world["fail"].clear()
    bd.main(["--limit", "6"])
    assert "https://fda.example/0" in world["calls"]


def test_removed_card_never_comes_back(world):
    bd.SEEN_PATH.parent.mkdir(parents=True)
    bd.SEEN_PATH.write_text(json.dumps({"https://fda.example/1": {"verdict": "removed", "at": "2026-01-01"}}))
    bd.main(["--limit", "40"])
    assert "https://fda.example/1" not in world["calls"]
    assert "https://fda.example/1" in json.loads(bd.SEEN_PATH.read_text())  # old, but kept


def test_dry_run_writes_no_memory(world):
    bd.main(["--dry", "--limit", "6"])
    assert not bd.SEEN_PATH.exists()


# ─── charts and detail must be grounded (17.10.2026) ──────────────

import breakthrough_enrich as be  # noqa: E402

BAR = {"kind": "bar_delta", "bars": [{"label": "OS", "treatment": 12, "control": 10}],
       "unit": "months", "treatment_label": "With drug", "control_label": "Without"}


def test_invented_chart_is_dropped_grounded_chart_kept():
    teaser = {"title": "EU recommends drug X", "summary": "Regulators recommended approval of X."}
    assert bd.grounded_graphic(teaser, {"graphic": BAR}) is None
    trial = {"title": "X trial", "summary": "Median survival 12 months vs 10 months with placebo."}
    assert bd.grounded_graphic(trial, {"graphic": BAR}) == BAR
    assert bd.grounded_graphic(trial, {"graphic": {"kind": "bar_delta", "bars": []}}) is None


def test_ground_detail_drops_only_the_ungrounded_parts():
    src = "Drug X extended survival: in 500 patients median OS was 13.2 vs 6.6 months; hazard ratio 0.40."
    raw = {"summary": "X extended survival. Median OS was 13.2 vs 6.6 months. It cut deaths by 45%. "
                      "Sessions were delivered by trained physiotherapists at a single academic centre.",
           "key_findings": ["OS 13.2 vs 6.6 months", "Response rate 38%"],
           "study": {"participants": "500 patients", "follow_up": "24 months"},
           "graphic": {"kind": "kaplan_meier", "median_t": 13.2, "median_c": 6.6,
                       "hr": 0.40, "ci_low": 0.32, "ci_high": 0.5}}
    d, g, dropped = be.ground_detail(raw, src)
    assert d["summary"] == "X extended survival. Median OS was 13.2 vs 6.6 months."
    assert d["key_findings"] == ["OS 13.2 vs 6.6 months"]
    assert d["study"] == {"participants": "500 patients"}
    assert g["median_t"] == 13.2 and g["hr"] == 0.4 and "ci_low" not in g
    assert any("ci_low" in x for x in dropped)


def test_kept_card_gets_detail(world, monkeypatch):
    monkeypatch.setattr(bd, "gemma_classify", lambda raw: {
        "is_breakthrough": True, "strength": 0.9, "headline": "A cuts B", "summary": "A reduced B by 20%.",
        "graphic": BAR})
    monkeypatch.setattr(bd, "FEEDS", [("fda", "fda")])
    bd.main(["--limit", "1"])
    card = world["feed"]["items"][0]
    assert card["detail"] == {"summary": "stub"} and card["graphic"] is None


def test_detail_page_renders_sections_and_hides_missing_chart(monkeypatch):
    from fastapi.testclient import TestClient
    from web import app as webapp
    card = {"id": "br_t", "published_at": "2026-10-16", "category": "oncology", "stage": "approved",
            "audience": "general", "headline": "Drug X recommended", "summary": "short",
            "why_it_matters": "w", "graphic": None, "strength": 0.9, "source_name": "STAT",
            "source_url": "https://s.example", "factor_slug": None, "outcome_slug": None,
            "detail": {"intervention": "Rasonque (daraxonrasib)", "summary": "Long summary.",
                       "key_findings": ["OS 13.2 vs 6.6 months"], "study": {"trial_name": "RASolute 302"},
                       "caveats": ["Open-label"], "evidence": [{"pmid": "1", "title": "T", "journal": "NEJM",
                       "year": "2026", "url": "https://pubmed.ncbi.nlm.nih.gov/1/"}]}}
    monkeypatch.setattr(webapp.bx, "get", lambda i: card if i == "br_t" else None)
    html = TestClient(webapp.app).get("/breakthroughs/br_t").text
    for s in ("Rasonque (daraxonrasib)", "RASolute 302", "OS 13.2 vs 6.6 months", "Open-label", "PMID 1", "AT A GLANCE"):
        assert s in html
    assert "bx-detail-graphic" not in html


# ─── graph linking (18.10.2026) ───────────────────────────────────

import sqlite3  # noqa: E402
import breakthrough_corpus as bc  # noqa: E402


@pytest.fixture
def graph(tmp_path, monkeypatch):
    db = sqlite3.connect(tmp_path / "g.db")
    db.row_factory = sqlite3.Row
    db.executescript("""
      CREATE TABLE entity (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, kind TEXT, aliases TEXT);
      CREATE TABLE edge (id INTEGER PRIMARY KEY, factor_id INT, outcome_id INT, direction TEXT, tier TEXT,
                         summary TEXT, effect_quant TEXT, review_status TEXT);
      CREATE TABLE evidence (id INTEGER PRIMARY KEY, edge_id INT, is_counter INT);
      INSERT INTO entity VALUES (1,'sglt2_inhibitors','SGLT2 inhibitors','drug','[]'),
        (2,'chronic_kidney_disease','Chronic kidney disease','condition','[]'),
        (3,'heart_failure','Heart failure','condition','[]'),
        (4,'ace_inhibitors','ACE inhibitors','drug','[]'),
        (5,'bladder_cancer','Bladder cancer','condition','[]'),
        (6,'smoking','Smoking','behavior','[]');
      INSERT INTO edge VALUES (728,1,2,'protective','A','s','', 'verified_evidence'),
        (729,1,3,'protective','A','s','', 'verified_evidence'),
        (900,6,5,'harmful','A','smoking raises bladder cancer risk','', 'verified_evidence');
      INSERT INTO evidence VALUES (1,728,0),(2,728,0),(3,900,0);
    """)
    class Conn:
        def __enter__(self): return db
        def __exit__(self, *a): return False
    monkeypatch.setattr(bc, "_connect", lambda: Conn())
    vec = {"SGLT2 inhibitors": [1, 0, 0, 0], "Chronic kidney disease": [0, 1, 0, 0],
           "Heart failure": [0, 0, 1, 0], "ACE inhibitors": [0, 0, 0.85, 0.53], "Bladder cancer": [0, 0.62, 0.62, 0.48],
           "Smoking": [0, 0, 0, 1]}
    ents = [{"id": i, "slug": s, "name": n, "kind": k, "aliases": [], "vec": bc._norm(vec[n])}
            for i, s, n, k in [(1, "sglt2_inhibitors", "SGLT2 inhibitors", "drug"),
                               (2, "chronic_kidney_disease", "Chronic kidney disease", "condition"),
                               (3, "heart_failure", "Heart failure", "condition"),
                               (4, "ace_inhibitors", "ACE inhibitors", "drug"),
                               (5, "bladder_cancer", "Bladder cancer", "condition"),
                               (6, "smoking", "Smoking", "behavior")]]
    q = {"rivaroxaban": [0.2, 0, 0, 0.98], "empagliflozin": [0.95, 0.1, 0, 0], "kidney decline": [0, 0.9, 0.1, 0],
         "bladder cancer progression": [0, 0.62, 0.62, 0.48]}
    monkeypatch.setattr(bc, "embed", lambda texts: [q.get(t, [0.01, 0.01, 0.01, 0.01]) for t in texts])
    return ents


def card(intervention, outcome_slug, headline):
    return {"id": "x", "headline": headline, "summary": "", "factor_slug": "", "outcome_slug": outcome_slug,
            "detail": {"intervention": intervention, "summary": "", "who_it_applies_to": ""}}


def test_unrelated_pick_is_rejected_named_low_score_pick_is_kept(graph, monkeypatch):
    # model picks ACE inhibitors for a rivaroxaban card: not named, far → rejected
    monkeypatch.setattr(bc, "ollama_json", lambda p, num_predict=0: {"factor": "ace_inhibitors", "outcome": None})
    c = bc.apply(card("rivaroxaban", "", "Blood thinner beats metoprolol"), graph)["corpus"]
    assert c["factor"] is None
    # "bladder cancer" scores low on vectors but the card names it → kept, with its edges
    monkeypatch.setattr(bc, "ollama_json", lambda p, num_predict=0: {"factor": None, "outcome": "bladder_cancer"})
    out = bc.apply(card("", "bladder cancer progression", "New bladder cancer treatment"), graph)
    assert out["corpus"]["outcome"]["slug"] == "bladder_cancer"
    assert [e["id"] for e in out["corpus"]["outcome_edges"]] == [900] and out["is_orphan"]


def test_pair_edge_found_under_another_outcome_name(graph, monkeypatch):
    monkeypatch.setattr(bc, "ollama_json", lambda p, num_predict=0: {"factor": "sglt2_inhibitors", "outcome": None})
    out = bc.apply(card("empagliflozin", "kidney decline", "SGLT2 drugs protect kidneys"), graph)
    # 729 (heart failure) is not near the card's outcome
    assert [e["id"] for e in out["corpus"]["pair"]] == [728]
    assert out["edge_id"] == 728 and not out["is_orphan"]


# ─── Circulation via E-utilities (25.10.2026) ─────────────────────

def test_pubmed_feed_goes_through_eutils_not_rss(monkeypatch):
    called = []
    monkeypatch.setattr(bd, "fetch_pubmed", lambda term: called.append(term) or [])
    monkeypatch.setattr(bd.urllib.request, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("RSS must not be fetched")))
    assert bd.fetch_rss("pubmed:Circulation[ta]") == [] and called == ["Circulation[ta]"]
    assert ("Circulation", "pubmed:Circulation[ta]") in bd.FEEDS


def test_paper_judged_under_old_rss_link_is_not_judged_again(world, monkeypatch):
    world["feed"]["items"] = [{"id": "x", "headline": "old", "published_at": "2026-10-20",
                               "source_url": "https://pubmed.ncbi.nlm.nih.gov/42677492/?utm_source=Chrome&utm_medium=rss"}]
    new = {"title": "Noninvasive Thrombus Imaging", "link": "https://pubmed.ncbi.nlm.nih.gov/42677492/",
           "summary": "In 100 patients A reduced B by 20%.", "published": "2026-10-20"}
    monkeypatch.setattr(bd, "FEEDS", [("Circulation", "pubmed:x")])
    monkeypatch.setattr(bd, "fetch_rss", lambda url: [dict(new)])
    bd.main(["--limit", "5"])
    assert world["calls"] == []
