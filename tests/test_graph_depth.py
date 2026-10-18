"""Graph depth tools (18.10.2026): citation check, PMID repair matching,
tier rules, duplicate merge, seeding filter. No network, no model."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import edge_audit as ea  # noqa: E402
import fix_citation_pmids as fx  # noqa: E402
import deepen_edges as de  # noqa: E402
import merge_duplicate_edges as md  # noqa: E402
import seed_from_breakthroughs as sd  # noqa: E402


def rec(title, authors, year, journal=""):
    return {"title": title, "abstract": "", "authors": authors, "year": str(year), "journal": journal}


def test_citation_check_catches_wrong_paper_and_accepts_glued_initials_and_titles():
    ok = rec("Sleep duration and risk of all-cause mortality", ["García-Perdomo", "Zapata"], 2019)
    assert ea.citation_ok("GarciaPerdomoHA et al 2019 Epidemiol Psychiatr Sci", 2019, ok) == "ok"
    assert ea.citation_ok("Zapata et al 2019 X", 2019, ok) == "ok"                 # any author, not only first
    assert ea.citation_ok("Sleep duration and risk of all-cause mortality: a meta", None, ok) == "ok"
    wrong = rec("Implementation of a novel three-tier triage tool in Papua New Guinea", ["Kingston"], 2021)
    assert ea.citation_ok("Reynolds et al. 2019 Lancet", 2019, wrong) == "mismatch"


def test_material_numbers_skip_small_counts():
    assert ea.material({"2", "0.74", "25"}) == {"0.74", "25"}
    assert "3" not in ea.nums("omega-3 and B12 at 20 mg")


def test_journal_match_and_citation_parse():
    assert fx.journal_match("Nature Communications", "Nat Commun")
    assert fx.journal_match("NEJM", "N Engl J Med")
    assert not fx.journal_match("Nature Communications", "Rev Med Suisse")
    assert fx.parse_citation("MonamiM et al 2022 Diabetologia") == ("Monami", 2022, "Diabetologia")


def row(st, q="high", n=0, d="protective", counter=0):
    return {"study_type": st, "quality": q, "n_participants": n, "direction": d, "is_counter": counter}


def test_tier_rules():
    assert de.rule_tier([row("meta_analysis"), row("meta_analysis"), row("meta_analysis")], "protective")[0] == "A"
    assert de.rule_tier([row("meta_analysis"), row("cohort", n=9000), row("rct", n=100)],
                        "protective")[0] == "B"                                      # 4 + 2 + 1.5
    assert de.rule_tier([row("meta_analysis", "moderate"), row("cohort", n=9000), row("rct", n=100)],
                        "protective")[0] == "C"                                      # 6.5 < 7
    assert de.rule_tier([row("systematic_review", "moderate")], "protective")[0] == "C"   # a synthesis is ≥ C
    assert de.rule_tier([row("cross_sectional")], "protective")[0] == "D"
    assert de.rule_tier([row("meta_analysis"), row("meta_analysis", d="harmful")], "protective")[0] == "X"


def test_merge_only_when_populations_are_generic():
    E = lambda p: {"population": p}
    assert md.mergeable([E("general adult"), E("General adult; associations observed across men and women")])
    assert md.mergeable([E(None), E("adults"), E("adults with type 2 diabetes")])
    assert not md.mergeable([E("adult women"), E("older men")])


def test_merge_moves_evidence_redirects_and_keeps_strongest(tmp_path, monkeypatch):
    db = sqlite3.connect(tmp_path / "m.db")
    db.row_factory = sqlite3.Row
    db.executescript("""
      CREATE TABLE edge (id INTEGER PRIMARY KEY, factor_id INT, outcome_id INT, tier TEXT, population TEXT);
      CREATE TABLE evidence (id INTEGER PRIMARY KEY, edge_id INT, pmid TEXT);
      CREATE TABLE edge_history (id INTEGER PRIMARY KEY, edge_id INT, field TEXT, old_value TEXT,
                                 new_value TEXT, reason TEXT, actor TEXT);
      INSERT INTO edge VALUES (18,1,2,'A','General adult population'),(1248,1,2,'A','general adult'),
                              (900,3,4,'C','adult women'),(901,3,4,'D','older men');
      INSERT INTO evidence VALUES (1,18,'111'),(2,1248,'111'),(3,1248,'222');
    """)
    class C:
        def __enter__(self): return db
        def __exit__(self, *a): return False
    monkeypatch.setattr(md, "_connect", lambda: C())
    md.main([])
    # same tier → the one with more evidence stays; the PMID both had is not duplicated
    assert [r[0] for r in db.execute("SELECT id FROM edge ORDER BY id")] == [900, 901, 1248]
    assert sorted(r[0] for r in db.execute("SELECT pmid FROM evidence WHERE edge_id=1248")) == ["111", "222"]
    assert db.execute("SELECT new_id FROM edge_redirect WHERE old_id=18").fetchone()[0] == 1248


def test_seed_only_cards_naming_two_entities_without_an_edge():
    card = lambda **c: {"id": "x", "corpus": {"factor": None, "outcome": None, "pair": [], **c}, "detail": {}}
    f, o = {"slug": "vaping"}, {"slug": "quit_rate"}
    got = sd.candidates_from_feed([card(factor=f, outcome=o), card(factor=f), card(factor=f, outcome=o, pair=[{"id": 1}]),
                                   {**card(factor=f, outcome=o), "detail": {"no_results": True}}])
    assert len(got) == 1


def test_risk_edges_reject_treatment_studies(monkeypatch):
    assert de.risk_question("condition", "general adult") and not de.risk_question("biomarker", "general adult")
    assert not de.risk_question("condition", "adults with type 2 diabetes")
    assert de.risk_question("condition", "adult women")
    calls = []
    monkeypatch.setattr(de, "ollama_json", lambda p, num_predict=0: calls.append(p) or {
        "relevant": True, "participants_had_outcome": True, "study_type": "rct", "direction": "protective",
        "effect": "", "n_participants": None})
    treat = {"pmid": "1", "title": "Aerobic exercise in people with Parkinson's disease: an RCT", "abstract": "x"}
    assert de.judge("Aerobic exercise", "Parkinson's disease", treat, risk=True) is None and not calls  # title rule
    other = {"pmid": "2", "title": "Exercise and motor function: an RCT", "abstract": "x"}
    assert de.judge("Aerobic exercise", "Parkinson's disease", other, risk=True) is None              # model says patients
    assert de.judge("Aerobic exercise", "Parkinson's disease", other, risk=False) is not None         # treatment edge ok


def test_treating_the_factor_is_not_evidence_for_it(monkeypatch):
    monkeypatch.setattr(de, "ollama_json", lambda p, num_predict=0: {
        "relevant": True, "participants_had_outcome": False, "study_type": "meta-analysis",
        "direction": "harmful", "effect": "", "n_participants": None})
    c = {"pmid": "1", "title": "Cognitive Effects of Treating Obstructive Sleep Apnea: A Meta-Analysis", "abstract": "x"}
    assert de.judge("Obstructive sleep apnea", "Cognitive function", c, factor_is_condition=True) is None
    assert de.judge("Obstructive sleep apnea", "Cognitive function", c, factor_is_condition=False) is not None
