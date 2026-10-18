"""fix_edge_numbers: unsourced numbers go, sourced claims stay (18.10.2026)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fix_edge_numbers as f  # noqa: E402
import edge_audit as ea  # noqa: E402


def test_aside_dropped_claim_kept_and_vs_not_a_sentence_end():
    src = ea.nums("21 studies")
    out = f.strip_sentences("Eating nuts—roughly a small handful (28–30 g)—is linked to lower CVD risk. "
                            "Pooled RR 1.15–1.40 vs. least sedentary.", src)
    assert out == "Eating nuts is linked to lower CVD risk."
    assert f.sentences("A vs. B was 1.2. Next one.") == ["A vs. B was 1.2.", "Next one."]


def test_rewrite_must_quote_a_real_abstract_sentence():
    asents = [(ea.nums(x), f.words(x)) for x in ["Light drinking was associated with 25% lower stroke mortality."]]
    assert f.quoted("Light drinking associated with 25% lower stroke mortality", asents)
    assert not f.quoted("Heavy drinkers had 25% higher cancer incidence", asents)


def test_estimate_quote_is_verbatim_directional_and_not_the_word_or():
    ev = [{"pmid": "1", "study_type": "meta_analysis", "citation": "Mellen PB et al 2008", "year": 2008}]
    cache = {"1": {"abstract": "or =2 to <4 h/d and 1.46 (95% CI, 1.04 to 2.05). Pooled RR 0.79 (95% CI 0.73-0.85) for CVD."}}
    assert f.estimate_quote(ev, cache, "protective") == "RR 0.79 (95% CI 0.73-0.85) (Mellen PB 2008)"
    assert f.estimate_quote(ev, cache, "harmful") is None


def test_species_abbreviations_and_brackets_do_not_split():
    assert f.sentences("H. pylori raises risk. Next.") == ["H. pylori raises risk.", "Next."]
    assert f.sentences("Adults (European cohorts; ages 18–85) were studied.") == \
        ["Adults (European cohorts; ages 18–85) were studied."]
    src = ea.nums("")
    assert f.strip_sentences("General adults (European cohorts; ages 18–85)", src) == "General adults"


def test_en_dash_ranges_survive_and_quotes_are_balanced():
    # the real case (edge 63): a range before a bracket with ranges inside
    src = ea.nums("13 17 95 0.83 0.87 0.76 0.94")
    s = "~13–17% lower T2D risk per ~28 g/day serving (RR ~0.83–0.87, 95% CI ~0.76–0.94)"
    # "28" is unsourced and not in an aside → the clause goes; it must not be cut to "~13 0.87, 95% CI …"
    assert f.strip_sentences(s, src) == ""
    ev = [{"pmid": "9", "study_type": "meta_analysis", "citation": "A very long paper title about coffee", "year": 2020}]
    cache = {"9": {"abstract": "Coffee was linked to lower risk (RR = 0.81, 95% CI 0.72-0.90)."}}
    q = f.estimate_quote(ev, cache, "protective")
    assert q.count("(") == q.count(")") and q.endswith("(PMID 9 2020)")


def test_quote_must_come_from_an_abstract_about_the_factor():
    ev = [{"pmid": "5", "study_type": "meta_analysis", "citation": "X et al", "year": 2026}]
    cache = {"5": {"abstract": "Life's Essential 10 and brain health. Higher scores lowered dementia (HR=0.59, 95% CI 0.52 to 0.67)."}}
    assert f.estimate_quote(ev, cache, "protective", "Alcohol", "All-cause mortality") is None
    assert f.estimate_quote(ev, cache, "protective", "Life's Essential 10 score", "Dementia") is not None
