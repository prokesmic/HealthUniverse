#!/usr/bin/env python3
"""Deepen edges with PubMed evidence (18.10.2026).

The graph grew 814 edges in 30 days, almost all tier C/D, and half of all
edges stand on one study. Breadth is not what makes it useful; depth is. For
the edges VitalShield relies on (its priority list + hu_link factors), this:

  1. searches PubMed for meta-analyses, systematic reviews and RCTs on the
     edge's factor AND outcome (humans), skipping PMIDs already attached;
  2. lets the local model judge each abstract: is it about this exposure and
     this outcome, what design, how many people, which direction, and the
     effect estimate quoted from the abstract;
  3. keeps a row only if the model said relevant AND the quoted effect's
     numbers are in the abstract AND the title names both ends of the edge;
  4. adds the rows as evidence (edge_history records each one), recomputes
     the deterministic tier score from audit_tiers.py's rules, and
       - applies a promotion when the rules clearly support it and the
         direction is consistent,
       - only *logs* a demotion or a contested signal for human review
         (data/audits/tier-suggestions-<date>.json) — the project's rule is
         that tier cuts are never auto-applied.
  5. replaces effect_quant with the best grounded quote when the current
     text carries numbers that are not in any of the edge's abstracts.

Local model only (no API spend). Progress is per edge; safe to stop.

  python scripts/deepen_edges.py --limit 40
  python scripts/deepen_edges.py --edge 728 --dry
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import edge_audit as ea  # noqa: E402
from breakthrough_enrich import ollama_json, pubmed_search  # noqa: E402

PRIORITY = ROOT / "data" / "vitalshield_priority.json"
STATE = ROOT / "data" / "cache" / "deepen_state.json"
SUGGEST = ROOT / "data" / "audits" / f"tier-suggestions-{date.today().isoformat()}.json"
TIER_RANK = {"D": 0, "C": 1, "B": 2, "A": 3}
STUDY_MAP = {"meta-analysis": "meta_analysis", "meta_analysis": "meta_analysis",
             "systematic review": "systematic_review", "systematic_review": "systematic_review",
             "rct": "rct", "randomized controlled trial": "rct", "cohort": "cohort",
             "case-control": "case_control", "case_control": "case_control",
             "cross-sectional": "cross_sectional", "cross_sectional": "cross_sectional"}


def _connect():
    from db import connect  # type: ignore
    return connect()


# ─── deterministic tier rules (audit_tiers.py SYSTEM prompt, as code) ───

def row_score(r) -> float:
    st, q, n = r["study_type"], r["quality"], r["n_participants"] or 0
    if st == "meta_analysis":
        return {"high": 4, "moderate": 3}.get(q, 2)
    if st == "systematic_review":
        return {"high": 3, "moderate": 2}.get(q, 1.5)
    if st == "rct":
        return 3 if (n >= 500 and q == "high") else 1.5
    if st == "cohort":
        return 2 if n >= 5000 else 1
    if st == "case_control":
        return 1
    if st == "cross_sectional":
        return 0.5
    if st in ("mechanistic", "animal"):
        return 0.25
    return 0.0


def rule_tier(rows, direction: str) -> tuple[str, float, str]:
    """(tier, score, note) from evidence rows; 'X' when syntheses disagree."""
    rows = [r for r in rows if not r["is_counter"]]
    score = sum(row_score(r) for r in rows)
    synth = [r for r in rows if r["study_type"] in ("meta_analysis", "systematic_review")]
    dirs = Counter((r["direction"] or "").lower() for r in synth if r["direction"])
    if len([d for d in dirs if d in ("protective", "harmful")]) > 1 and min(
            dirs["protective"], dirs["harmful"]) >= 1 and min(dirs["protective"], dirs["harmful"]) / max(
            sum(dirs.values()), 1) >= 0.34:
        return "X", score, f"syntheses disagree {dict(dirs)}"
    consistent = all((r["direction"] or direction) in (direction, "") for r in synth)
    hq_synth = [r for r in synth if r["quality"] == "high"]
    trials = [r for r in rows if r["study_type"] in ("cohort", "rct")]
    if len(hq_synth) >= 2 and score >= 12 and consistent:
        return "A", score, "≥2 high-quality syntheses, score ≥12"
    if len(synth) >= 1 and len(trials) >= 2 and score >= 7:
        return "B", score, "≥1 synthesis + ≥2 cohorts/RCTs, score ≥7"
    if len(trials) >= 2 or any(r["study_type"] == "rct" for r in rows) or synth:
        return "C", score, "consistent observational studies or an RCT"
    return "D", score, "limited"


# ─── PubMed + model judgement ──────────────────────────────────────────

def clean_name(s: str) -> str:
    s = re.sub(r"\(.*?\)", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


# Qualifiers that make an entity name precise for the graph but absent from
# papers: "Chronic psychological stress", "High HbA1c", "Deliberate cold
# exposure", "Endothelial dysfunction by flow-mediated dilation". On 19–25.10
# 48 of the last 60 edges found nothing, mostly because of these.
_LEAD = re.compile(r"^(high|higher|low|lower|elevated|reduced|chronic|acute|deliberate|regular|habitual|daily|"
                   r"long-term|short-term|excess|excessive|poor|"
                   r"increased|decreased|frequent)\s+", re.I)
_TAIL = re.compile(r"\s+(in (humans|adults|older adults|women|men|children|athletes|healthy adults)|"
                   r"decline|elevation|levels?|rate|score|control|reclassification|outcomes?|risk|incidence|"
                   r"by [a-z -]+|per [a-z -]+)$", re.I)


# Dose words stay ("moderate-dose exercise" is not "exercise"); a lone generic word is no search term.
_GENERIC = {"exercise", "cardiovascular", "health", "function", "disease", "stress", "sleep", "diet", "activity",
            "metabolic", "cognitive", "mental", "physical", "inflammation", "mortality risk"}


def variants(name: str, aliases=None) -> list[str]:
    """Search forms of an entity: the clean name, the name without qualifiers,
    and its aliases. Longest first; at most five."""
    out = []
    for raw in [name] + [a for a in (aliases or []) if isinstance(a, str)]:
        v = clean_name(raw).strip(" ,;")
        for _ in range(3):
            if not v:
                break
            if v.lower() not in (x.lower() for x in out):
                out.append(v)
            w = _TAIL.sub("", _LEAD.sub("", v)).strip(" ,;")
            if w == v or len(w) < 3 or w.lower() in _GENERIC:
                break
            v = w
    for v in list(out):   # "Nuts" → "Nut" ("Nut consumption and risk of hypertension")
        sg = singular(v)
        if sg and sg.lower() not in (x.lower() for x in out):
            out.append(sg)
    us = []
    for v in out:   # papers are mostly American: "Dietary fibre → LDL" found nothing on 25.10
        w = v
        for uk, am in _SPELL:
            w = re.sub(uk, am, w, flags=re.I)
        if w.lower() not in (x.lower() for x in out + us):
            us.append(w)
    return (out + us)[:6]


_SPELL = [(r"fibre", "fiber"), (r"oestrogen", "estrogen"), (r"haem", "hem"), (r"anaemi", "anemi"),
          (r"oedema", "edema"), (r"paediatric", "pediatric"), (r"behaviour", "behavior"), (r"tumour", "tumor"),
          (r"ageing", "aging"), (r"leukaemi", "leukemi"), (r"diarrhoea", "diarrhea"), (r"coeliac", "celiac")]


# Words that turn a food into something else: betel/areca nut is a stimulant,
# nutmeg a spice, red yeast rice a statin source, "fish oil" is not fish.
_FALSE_FRIENDS = {"betel", "areca", "kola", "nutmeg", "doughnut", "butternut", "yeast"}


def false_friend(title: str, factor_variants: list[str]) -> bool:
    t = set(re.findall(r"[a-z]+", title.lower()))
    mine = set(re.findall(r"[a-z]+", " ".join(factor_variants).lower()))
    return bool((t & _FALSE_FRIENDS) - mine)


_NOT_PLURAL = {"diabetes", "measles", "herpes", "rickets", "mumps", "species", "series", "news", "lens"}


def singular(v: str) -> str | None:
    """Singular of the last word, or None: berries → berry, nuts → nut; not diabetes, sepsis, virus."""
    head, _, last = v.rpartition(" ")
    lw = last.lower()
    if len(lw) < 4 or lw in _NOT_PLURAL or lw.endswith(("ss", "is", "us")) or not lw.endswith("s"):
        return None
    sg = last[:-3] + "y" if lw.endswith("ies") else last[:-1]
    return f"{head} {sg}".strip()


def _aliases(conn, name: str) -> list[str]:
    r = conn.execute("SELECT aliases FROM entity WHERE name=? LIMIT 1", (name,)).fetchone()
    try:
        return json.loads(r[0] or "[]") if r else []
    except Exception:
        return []


_JUDGE = """{question}

ABSTRACT (PMID {pmid}): {title}
{abstract}

Return JSON only:
{{"relevant": true|false,             // answers the question above, human data
  "participants_had_outcome": true|false,  // did the participants already have {outcome} at the start?
  "study_type": "meta-analysis|systematic review|rct|cohort|case-control|cross-sectional|other",
  "n_participants": integer or null,  // as stated in the abstract
  "direction": "protective|harmful|neutral|mixed",  // effect of MORE {factor} on {outcome} risk/health
  "effect": "the main effect estimate copied from the abstract, e.g. 'RR 0.82 (95% CI 0.74-0.91)', or ''"}}"""


def candidates(f_name: str, o_name: str, have: set[str], k: int = 6, risk: bool = False,
               f_alias=None, o_alias=None) -> list[dict]:
    fv, ov = variants(f_name, f_alias), variants(o_name, o_alias)
    if not fv or not ov:
        return []
    orq = lambda vs: "(" + " OR ".join(f'"{v}"[tiab]' for v in vs) + ")"
    syn = '(meta-analysis[pt] OR systematic review[pt])'
    designs = f'({syn[1:-1]} OR randomized controlled trial[pt])'
    terms = []
    if risk:   # risk of developing the disease: syntheses of cohorts first, then any synthesis
        terms.append(f'{orq(fv)} AND {orq(ov)} AND {syn} AND (risk[tiab] OR incidence[tiab])')
        terms.append(f'{orq(fv)} AND {orq(ov)} AND {syn}')
    else:
        terms.append(f'{orq(fv)} AND {orq(ov)} AND {designs}')
    # PubMed's own term mapping (MeSH) on the shortest forms, as a last resort
    terms.append(f'({fv[-1]}) AND ({ov[-1]}) AND {syn}')
    ids: list[str] = []
    for term in terms:
        for i in pubmed_search(term, retmax=12):
            if i not in have and i not in ids:
                ids.append(i)
        if len(ids) >= 8:
            break
    if not ids:
        return []
    recs = ea.fetch(ids[:16])
    fw = set().union(*(ea_words(v) for v in fv))
    ow = set().union(*(ea_words(v) for v in ov))
    out = []
    for pmid in ids:
        r = recs.get(pmid)
        if not r or not r.get("abstract"):
            continue
        tw = ea_words(r["title"])
        if false_friend(r["title"], fv):
            continue                     # "betel nut chewing" is not nuts (25.10)
        if tw & fw and tw & ow:          # both ends named in the title, not just the abstract
            out.append({"pmid": pmid, **r})
        if len(out) >= k:
            break
    return out


def ea_words(s: str) -> set[str]:
    stop = {"with", "from", "risk", "intake", "level", "levels", "high", "higher", "low", "lower",
            "chronic", "daily", "adults", "adult", "disease", "health", "total", "week",
            # 3-letter words count now ("nut", "fat", "tea"), so the glue words must not
            "and", "the", "for", "per", "via", "its", "not", "are", "was", "but", "all", "use", "non",
            "pre", "who", "how", "may", "can", "new", "two", "one", "has", "had", "our", "out", "off", "own"}
    stem = lambda w: (w[:-1] if w.endswith("s") and not w.endswith("ss") else w)[:6]
    return {stem(w) for w in re.findall(r"[a-z]{3,}", (s or "").lower()) if w not in stop and len(stem(w)) >= 3}


RISK_KINDS = {"condition"}
_PATIENTS = re.compile(r"\b(in|among|for|of)\s+(people|patients|persons|individuals|adults|subjects|"
                       r"women|men|children|those|survivors)\s+(with|living with|diagnosed with|after)\b", re.I)


_PATIENT_POP = re.compile(r"\b(with|patients?|diagnosed|survivors?|living with|after)\b", re.I)


def risk_question(o_kind: str | None, population: str | None) -> bool:
    """The edge asks about the risk of getting a disease, not about treating it:
    a condition outcome in a population that is not described as patients
    ("adult women" and "older adults" are risk questions; "adults with CKD" is not)."""
    return o_kind in RISK_KINDS and (md_generic(population) or not _PATIENT_POP.search(population or ""))


def md_generic(pop: str | None) -> bool:
    import merge_duplicate_edges as md
    return md.generic(pop)


_TREATS = re.compile(r"\b(treat\w*|therapy|therapies|cpap|positive airway|management of|intervention)\b", re.I)


def judge(f_name: str, o_name: str, c: dict, risk: bool = False, factor_is_condition: bool = False) -> dict | None:
    f, o = clean_name(f_name), clean_name(o_name)
    if factor_is_condition and _TREATS.search(c["title"]) and (ea_words(f) & ea_words(c["title"])):
        return None   # "Cognitive effects of treating sleep apnea" answers the inverse question
    if risk:
        q = (f'Does this abstract show whether more "{f}" changes the RISK OF DEVELOPING "{o}" in people who '
             f'did not have it? Studies that treat or rehabilitate people who already have "{o}" do NOT count.')
        if _PATIENTS.search(c["title"]) and (ea_words(o) & ea_words(c["title"])):
            return None   # "aerobic exercise in people with Parkinson's disease" is treatment, not risk
    else:
        q = f'Is this abstract direct evidence on the effect of "{f}" on "{o}" in humans?'
    j = ollama_json(_JUDGE.format(question=q, factor=f, outcome=o, pmid=c["pmid"],
                                  title=c["title"], abstract=c["abstract"][:2600]), num_predict=240)
    if not j or not j.get("relevant"):
        return None
    if risk and j.get("participants_had_outcome") is not False:
        return None
    st = STUDY_MAP.get(str(j.get("study_type", "")).lower())
    if not st:
        return None
    eff = (j.get("effect") or "").strip()
    if len(eff) > 220:
        eff = ""                                  # a paragraph, not an estimate
    if eff and ea.nums(eff) - ea.nums(c["abstract"] + " " + c["title"]):
        eff = ""                                  # quote with numbers not in the abstract
    n = j.get("n_participants")
    n = n if isinstance(n, int) and n > 0 and str(n) in re.sub(r"(?<=\d),(?=\d{3})", "", c["abstract"]) else None
    d = j.get("direction") if j.get("direction") in ("protective", "harmful", "neutral", "mixed") else None
    quality = {"meta_analysis": "high", "systematic_review": "moderate", "rct": "moderate"}.get(st, "low")
    if st == "rct" and n and n >= 500:
        quality = "high"
    return {"study_type": st, "n": n, "direction": d, "effect": eff, "quality": quality}


def citation(c: dict) -> str:
    au = (c.get("authors") or [c.get("first_author") or "Anon"])[0]
    return f"{au} et al {c.get('year', '')} {c.get('journal', '')}".strip()


# ─── per edge ───────────────────────────────────────────────────────────

def deepen(conn, edge_id: int, dry: bool = False) -> dict:
    e = conn.execute("""SELECT e.*, f.name AS f_name, f.kind AS f_kind, o.name AS o_name, o.kind AS o_kind FROM edge e
                        JOIN entity f ON f.id=e.factor_id JOIN entity o ON o.id=e.outcome_id
                        WHERE e.id=?""", (edge_id,)).fetchone()
    ev = conn.execute("SELECT * FROM evidence WHERE edge_id=?", (edge_id,)).fetchall()
    have = {r["pmid"] for r in ev if r["pmid"]}
    added = []
    risk = risk_question(e["o_kind"], e["population"])
    seen_titles = {ea._norm(r["real_title"] or "") for r in ev if r["real_title"]}
    for c in candidates(e["f_name"], e["o_name"], have, risk=risk,
                        f_alias=_aliases(conn, e["f_name"]), o_alias=_aliases(conn, e["o_name"])):
        t = ea._norm(c["title"])
        if t in seen_titles:
            continue      # Cochrane updates and reprints carry one title under several PMIDs
        j = judge(e["f_name"], e["o_name"], c, risk=risk, factor_is_condition=e["f_kind"] == "condition")
        if not j or j["study_type"] not in ("meta_analysis", "systematic_review"):
            continue      # syntheses only: individual trials were the noisy quarter on 18.10
        seen_titles.add(t)
        added.append((c, j))
    res = {"edge": edge_id, "pair": f"{e['f_name']} → {e['o_name']}", "tier": e["tier"],
           "added": len(added), "new_tier": None, "suggest": None}
    if dry:
        res["rows"] = [(c["pmid"], j["study_type"], j["direction"], j["effect"]) for c, j in added]
        return res
    for c, j in added:
        conn.execute("""INSERT INTO evidence (edge_id, citation, url, pmid, year, study_type, n_participants,
                          direction, quality, notes, real_title, relevance_status, is_counter)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?, 'verified', ?)""",
                     (edge_id, citation(c), f"https://pubmed.ncbi.nlm.nih.gov/{c['pmid']}/", c["pmid"],
                      int(c["year"]) if str(c.get("year", "")).isdigit() else None, j["study_type"], j["n"],
                      j["direction"], j["quality"], j["effect"] or None, c["title"],
                      1 if (j["direction"] and e["direction"] in ("protective", "harmful")
                            and j["direction"] in ("protective", "harmful") and j["direction"] != e["direction"])
                      else 0))
        conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                        VALUES (?, 'evidence', NULL, ?, ?, 'deepen_rules')""",
                     (edge_id, c["pmid"], f"added {j['study_type']} from PubMed search; model-judged relevant, "
                                          f"effect quote checked against abstract"))
    rows = conn.execute("SELECT * FROM evidence WHERE edge_id=?", (edge_id,)).fetchall()
    tier, score, note = rule_tier(rows, e["direction"])
    cur = e["tier"]
    new_synth = [j for _, j in added if j["study_type"] in ("meta_analysis", "systematic_review")
                 and j["direction"] == e["direction"]]
    if tier in TIER_RANK and cur in TIER_RANK and TIER_RANK[tier] > TIER_RANK[cur] and new_synth:
        # Promotion needs a newly found synthesis agreeing with the edge — RCTs
        # on "alters the microbiota" lifted resistant starch to A on 18.10.
        # One step per run: the relevance call is a local model's, so C→A in one
        # pass would rest on it alone. The next run can take the next step.
        tier = [t for t, v in TIER_RANK.items() if v == TIER_RANK[cur] + 1][0]
        conn.execute("UPDATE edge SET tier=?, updated_at=datetime('now'), last_reviewed=datetime('now') WHERE id=?",
                     (tier, edge_id))
        conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                        VALUES (?, 'tier', ?, ?, ?, 'deepen_rules')""",
                     (edge_id, cur, tier, f"deterministic tier rules: {note} (score {score:g}) after adding "
                                          f"{len(added)} PubMed rows"))
        res["new_tier"] = tier
    elif tier != cur and cur in TIER_RANK | {"X": 9}:
        res["suggest"] = {"from": cur, "to": tier, "score": score, "note": note}
    # Ungrounded numbers in effect_quant → best grounded quote, if we have one.
    abstracts = " ".join((ea.load_cache().get(r["pmid"] or "", {}) or {}).get("abstract", "") for r in rows) \
        + " " + " ".join(c["abstract"] for c, _ in added)
    if e["effect_quant"] and ea.material(ea.nums(e["effect_quant"]) - ea.nums(abstracts)):
        best = next((j["effect"] for c, j in sorted(added, key=lambda t: -row_score(
            {"study_type": t[1]["study_type"], "quality": t[1]["quality"], "n_participants": t[1]["n"]}))
                     if j["effect"] and j["direction"] == e["direction"]), None)
        if best:
            conn.execute("UPDATE edge SET effect_quant=? WHERE id=?", (best, edge_id))
            conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                            VALUES (?, 'effect_quant', ?, ?, ?, 'deepen_rules')""",
                         (edge_id, e["effect_quant"], best, "old figures not found in any cited abstract; "
                                                            "replaced with a quote from a PubMed abstract"))
            res["effect_fixed"] = True
    conn.commit()
    return res


def targets(conn, limit: int) -> list[int]:
    slugs = set(json.loads(PRIORITY.read_text()).get("slugs", []))
    try:
        sys.path.insert(0, os.path.expanduser("~/Health"))
        import hu_link  # type: ignore
        slugs |= {m.slug for m in hu_link.MAPS}
    except Exception:
        pass
    try:
        done = set(json.loads(STATE.read_text()).get("done", []))
    except (FileNotFoundError, json.JSONDecodeError):
        done = set()
    q = ",".join("?" * len(slugs))
    rows = conn.execute(f"""SELECT e.id, e.tier, (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n
                            FROM edge e JOIN entity f ON f.id=e.factor_id
                            WHERE f.slug IN ({q}) AND e.tier != 'deprecated'""", list(slugs)).fetchall()
    order = {"B": 0, "C": 1, "A": 2, "X": 3, "D": 4}   # B/C sit nearest a promotion
    rows = sorted((r for r in rows if r["id"] not in done), key=lambda r: (r["n"] >= 6, order.get(r["tier"], 9), r["n"]))
    return [r["id"] for r in rows[:limit]]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--edge", type=int, action="append")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    st = Counter()
    suggestions = []
    with _connect() as conn:
        ids = a.edge or targets(conn, a.limit)
        print(f"→ deepening {len(ids)} edges")
        for n, eid in enumerate(ids, 1):
            t0 = time.time()
            r = deepen(conn, eid, dry=a.dry)
            st["edges"] += 1
            st["rows_added"] += r["added"]
            st["promoted"] += bool(r["new_tier"])
            st["effect_fixed"] += bool(r.get("effect_fixed"))
            if r["suggest"]:
                suggestions.append({"edge": eid, "pair": r["pair"], **r["suggest"]})
            print(f"[{n}/{len(ids)}] {r['pair'][:60]} {r['tier']}→{r['new_tier'] or r['tier']} "
                  f"+{r['added']} {'(suggest ' + r['suggest']['to'] + ')' if r['suggest'] else ''} "
                  f"{time.time() - t0:.0f}s", flush=True)
            if a.dry and r.get("rows"):
                for x in r["rows"]:
                    print("    ", x)
            if not a.dry:
                try:
                    s = json.loads(STATE.read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    s = {"done": []}
                s["done"] = sorted(set(s["done"]) | {eid})
                STATE.parent.mkdir(parents=True, exist_ok=True)
                tmp = STATE.with_suffix(".tmp")
                tmp.write_text(json.dumps(s))
                os.replace(tmp, STATE)
    if suggestions and not a.dry:
        old = json.loads(SUGGEST.read_text()) if SUGGEST.exists() else []
        SUGGEST.parent.mkdir(parents=True, exist_ok=True)
        SUGGEST.write_text(json.dumps(old + suggestions, indent=1, ensure_ascii=False))
    print(dict(st))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
