"""Daily ingestion pipeline.

For each (factor, outcome) entity in the graph:
  1. Pull new abstracts from PubMed + Europe PMC (last N days)
  2. Skip ones we've ingested before (by PMID/DOI)
  3. Gemma extracts (factor_slug, outcome_slug, direction, study_type, quality)
     claim tuples — only if relevant to entities we know about
  4. For each extracted claim:
     - If it matches an existing edge → re-score; if it would cross A/B
       boundary, queue for Claude adjudication
     - Else create a new edge at tier C/D with Gemma's summary
  5. Persist + write to edge_history

This is the work that makes the graph "living". Costs $0 (Gemma local).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from db import connect          # noqa: E402
from ollama_client import call_json, OllamaUnavailable  # noqa: E402
from ingest import pubmed, europepmc  # noqa: E402
try:
    from dedupe import find_near_edge      # noqa: E402
    from embeddings import embed, pack     # noqa: E402
    EMBED_OK = True
except Exception:
    EMBED_OK = False


# ----------------------------------------------------------------------------
# Gemma extraction prompts
# ----------------------------------------------------------------------------

EXTRACT_SYSTEM = """You extract structured health-research claims from study \
abstracts. You know about a fixed set of factors and outcomes; ignore \
abstracts that are not about any of them. Never fabricate. Return JSON only."""

EXTRACT_USER_TMPL = """KNOWN FACTORS (slug: name):
{factors}

KNOWN OUTCOMES (slug: name):
{outcomes}

ABSTRACT:
Title: {title}
Journal: {journal} ({year})
Body: {abstract}

Return a JSON object:
{{
  "relevant": <bool>,
  "claims": [
    {{
      "factor_slug":  "<one of the known factors>",
      "outcome_slug": "<one of the known outcomes>",
      "direction":    "protective"|"harmful"|"neutral"|"u_shaped"|"mixed",
      "study_type":   "meta_analysis"|"systematic_review"|"rct"|"cohort"|"case_control"|"cross_sectional"|"mechanistic"|"animal"|"case_report"|"expert_opinion",
      "n_participants": <int or null>,
      "quality":      "high"|"moderate"|"low"|"very_low",
      "notes":        "<one short sentence summary>"
    }}
  ]
}}

Rules:
- Set relevant=false if no factor AND outcome from the lists above is studied.
- Use ONLY slugs from the lists. Never invent slugs.
- Multiple claims allowed if the abstract reports several pairings.
- Quality: meta-analysis/large RCT = high; small RCT or cohort = moderate; \
cross-sectional/observational = low; animal/mechanistic = very_low.
"""


# ----------------------------------------------------------------------------
# Tier scoring
# ----------------------------------------------------------------------------

# Numeric weight per study type * quality, summed across an edge's evidence
# rows, gives a score we map back to a tier.
_TYPE_W = {
    "meta_analysis":     6.0, "systematic_review": 5.0, "rct": 4.0,
    "cohort":            2.5, "case_control": 1.8, "cross_sectional": 1.2,
    "mechanistic":       0.8, "animal": 0.6, "case_report": 0.4,
    "expert_opinion":    0.5,
}
_QUAL_W = {"high": 1.0, "moderate": 0.7, "low": 0.4, "very_low": 0.2}


def score_edge(evidence_rows: list[dict]) -> float:
    s = 0.0
    for ev in evidence_rows:
        s += _TYPE_W.get(ev.get("study_type") or "", 0.5) * \
             _QUAL_W.get(ev.get("quality") or "low", 0.4)
    return s


def score_to_tier(score: float, n_evidence: int, has_meta_or_large_rct: bool) -> str:
    if has_meta_or_large_rct and score >= 12 and n_evidence >= 4:
        return "A"
    if score >= 7 and n_evidence >= 3:
        return "B"
    if score >= 3:
        return "C"
    return "D"


def has_high_tier_evidence(evidence_rows: list[dict]) -> bool:
    return any(
        (ev.get("study_type") in ("meta_analysis", "systematic_review")) or
        (ev.get("study_type") == "rct" and (ev.get("n_participants") or 0) >= 500)
        for ev in evidence_rows
    )


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------

def _entity_lists(conn) -> tuple[str, str, dict, dict]:
    """Returns (factors_text, outcomes_text, factor_lookup, outcome_lookup)."""
    factors = conn.execute(
        "SELECT slug, name FROM entity WHERE kind IN "
        "('food','nutrient','supplement','activity','behavior','environmental','drug')"
    ).fetchall()
    outcomes = conn.execute(
        "SELECT slug, name FROM entity WHERE kind IN ('condition','process','biomarker')"
    ).fetchall()
    fmap = {r["slug"]: r["name"] for r in factors}
    omap = {r["slug"]: r["name"] for r in outcomes}
    fact_lines = "\n".join(f"  {s}: {n}" for s, n in fmap.items())
    out_lines = "\n".join(f"  {s}: {n}" for s, n in omap.items())
    return fact_lines, out_lines, fmap, omap


def _papers_for_today(conn, days_back: int = 2, per_entity: int = 8) -> list[dict]:
    """Fetch fresh abstracts for top-priority entities, dedupe by PMID/DOI."""
    seen: set[str] = set()
    papers: list[dict] = []
    rows = conn.execute(
        "SELECT slug, name FROM entity WHERE kind IN "
        "('food','nutrient','supplement','condition','process','behavior','activity') "
        "ORDER BY id LIMIT 60").fetchall()
    for r in rows:
        try:
            pmids = pubmed.search_for_entity(r["name"], days_back=days_back, retmax=per_entity)
        except Exception as e:
            print(f"  [pubmed] search {r['name']}: {e}", file=sys.stderr); pmids = []
        try:
            for p in pubmed.fetch_abstracts(pmids):
                key = p.get("pmid") or p.get("doi")
                if not key or key in seen: continue
                seen.add(key); papers.append(p)
        except Exception as e:
            print(f"  [pubmed] fetch {r['name']}: {e}", file=sys.stderr)
        try:
            for p in europepmc.search(r["name"], page_size=per_entity, days_back=days_back):
                key = p.get("pmid") or p.get("doi")
                if not key or key in seen: continue
                seen.add(key); papers.append(p)
        except Exception as e:
            print(f"  [epmc] {r['name']}: {e}", file=sys.stderr)
    return papers


def _already_ingested(conn, p: dict) -> bool:
    if p.get("pmid"):
        if conn.execute("SELECT 1 FROM ingested_paper WHERE pmid=?",
                        (p["pmid"],)).fetchone(): return True
    if p.get("doi"):
        if conn.execute("SELECT 1 FROM ingested_paper WHERE doi=?",
                        (p["doi"],)).fetchone(): return True
    return False


def _record_paper(conn, p: dict, extraction: dict) -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO ingested_paper "
        "(pmid, doi, title, abstract, journal, year, processed_at, extraction) "
        "VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)",
        (p.get("pmid"), p.get("doi"), p["title"], p.get("abstract", ""),
         p.get("journal", ""), p.get("year"), json.dumps(extraction)),
    )
    return cur.lastrowid


VALID_STUDY_TYPES = {
    "meta_analysis", "systematic_review", "rct", "cohort", "case_control",
    "cross_sectional", "mechanistic", "animal", "case_report", "expert_opinion",
}
VALID_DIRECTIONS = {"protective", "harmful", "neutral", "u_shaped", "mixed"}
VALID_QUALITY    = {"high", "moderate", "low", "very_low"}

# Map common Gemma drift values to the closest valid enum, so a single
# CHECK-constraint violation doesn't abort the whole run.
_STUDY_TYPE_ALIASES = {
    "review": "systematic_review",
    "narrative_review": "expert_opinion",
    "scoping_review": "systematic_review",
    "umbrella_review": "systematic_review",
    "trial": "rct",
    "randomised_controlled_trial": "rct",
    "randomized_controlled_trial": "rct",
    "controlled_trial": "rct",
    "clinical_trial": "rct",
    "observational": "cohort",
    "longitudinal": "cohort",
    "prospective_cohort": "cohort",
    "retrospective_cohort": "cohort",
    "case_series": "case_report",
    "in_vitro": "mechanistic",
    "in_vivo": "animal",
    "preclinical": "mechanistic",
    "ecological": "cross_sectional",
    "survey": "cross_sectional",
    "guideline": "expert_opinion",
    "consensus": "expert_opinion",
}


def _coerce_study_type(raw: str | None) -> str | None:
    """Return a valid study_type or None. Maps known aliases; otherwise
    drops claims with unrecognised values rather than crashing on insert."""
    if not raw:
        return None
    s = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if s in VALID_STUDY_TYPES:
        return s
    return _STUDY_TYPE_ALIASES.get(s)


def _apply_claim(conn, paper: dict, claim: dict, fmap: dict, omap: dict) -> dict | None:
    """Insert/update an edge based on a Gemma-extracted claim. Returns
    {edge_id, old_tier, new_tier, escalate} for anything interesting."""
    fslug, oslug = claim.get("factor_slug"), claim.get("outcome_slug")
    if fslug not in fmap or oslug not in omap:
        return None  # invalid slugs, skip silently
    # Coerce / validate Gemma-emitted enum fields BEFORE we hit the DB.
    coerced_st = _coerce_study_type(claim.get("study_type"))
    if not coerced_st:
        return None       # drop the claim, don't crash the run
    claim["study_type"] = coerced_st
    direction = (claim.get("direction") or "").strip().lower()
    if direction not in VALID_DIRECTIONS:
        return None
    quality = (claim.get("quality") or "low").strip().lower()
    if quality not in VALID_QUALITY:
        quality = "low"
    claim["quality"] = quality
    f = conn.execute("SELECT id FROM entity WHERE slug=?", (fslug,)).fetchone()
    o = conn.execute("SELECT id FROM entity WHERE slug=?", (oslug,)).fetchone()
    if not f or not o:
        return None

    edge = conn.execute(
        "SELECT * FROM edge WHERE factor_id=? AND outcome_id=? AND population='general adult'",
        (f["id"], o["id"]),
    ).fetchone()

    citation = f"{paper.get('journal','')} ({paper.get('year','')})"
    ev_row = {
        "citation":       paper.get("title", citation)[:280],
        "year":           paper.get("year"),
        "study_type":     claim.get("study_type"),
        "n_participants": claim.get("n_participants"),
        "direction":      claim.get("direction"),
        "quality":        claim.get("quality"),
        "notes":          claim.get("notes", ""),
        "doi":            paper.get("doi"),
        "pmid":           paper.get("pmid"),
    }

    if edge is None:
        # Before creating a new edge, check if a near-duplicate already exists
        # for this factor (e.g. another outcome that means the same thing).
        # If so, fold the evidence into that edge instead of creating a dupe.
        folded_into = None
        if EMBED_OK:
            try:
                folded_into = find_near_edge(
                    f["id"], o["id"], claim.get("notes", "") or omap.get(oslug, ""),
                    threshold=0.93)
            except Exception:
                folded_into = None
        if folded_into:
            edge_id = folded_into
            old_tier = conn.execute("SELECT tier FROM edge WHERE id=?",
                                    (folded_into,)).fetchone()["tier"]
        else:
            # Create new edge at C/D from this single piece of evidence
            score = score_edge([ev_row])
            new_tier = score_to_tier(score, 1, has_high_tier_evidence([ev_row]))
            cur = conn.execute(
                "INSERT INTO edge (factor_id, outcome_id, direction, tier, "
                "summary, mechanism, population, seed_source) "
                "VALUES (?, ?, ?, ?, ?, '', 'general adult', 'gemma_daily')",
                (f["id"], o["id"], claim.get("direction", "mixed"), new_tier,
                 claim.get("notes", "")),
            )
            edge_id = cur.lastrowid
            old_tier = None
            # Embed the new edge so future near-dup checks can match it.
            if EMBED_OK:
                try:
                    text = (f"{fmap[fslug]} -> {omap[oslug]}: "
                            f"{claim.get('notes','')} ({claim.get('direction')})")
                    conn.execute(
                        "UPDATE edge SET embedding=?, embedded_at=datetime('now') "
                        "WHERE id=?", (pack(embed(text)), edge_id))
                except Exception:
                    pass
    else:
        edge_id = edge["id"]
        old_tier = edge["tier"]

    conn.execute(
        "INSERT INTO evidence (edge_id, citation, year, study_type, "
        "n_participants, direction, quality, notes, doi, pmid) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (edge_id, ev_row["citation"], ev_row["year"], ev_row["study_type"],
         ev_row["n_participants"], ev_row["direction"], ev_row["quality"],
         ev_row["notes"], ev_row["doi"], ev_row["pmid"]),
    )

    # Re-score the edge from all its evidence
    rows = conn.execute(
        "SELECT study_type, n_participants, quality FROM evidence WHERE edge_id=?",
        (edge_id,),
    ).fetchall()
    rows = [dict(r) for r in rows]
    new_score = score_edge(rows)
    new_tier = score_to_tier(new_score, len(rows), has_high_tier_evidence(rows))
    if old_tier and new_tier != old_tier:
        conn.execute(
            "UPDATE edge SET tier=?, last_reviewed=datetime('now'), updated_at=datetime('now') WHERE id=?",
            (new_tier, edge_id))
        conn.execute(
            "INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
            "VALUES (?, 'tier', ?, ?, 'Gemma daily re-score', 'gemma_daily')",
            (edge_id, old_tier, new_tier))
    elif old_tier:
        conn.execute("UPDATE edge SET last_reviewed=datetime('now') WHERE id=?", (edge_id,))

    escalate = (old_tier in (None, "C", "D") and new_tier in ("A", "B"))
    return {"edge_id": edge_id, "old_tier": old_tier, "new_tier": new_tier,
            "escalate": escalate, "factor": fslug, "outcome": oslug}


def run(*, days_back: int = 2, per_entity: int = 6, dry_run: bool = False) -> dict:
    summary = {"papers": 0, "claims": 0, "new_edges": 0, "tier_changes": 0,
               "escalations": []}
    with connect() as conn:
        fact_lines, out_lines, fmap, omap = _entity_lists(conn)

    print(f"[ingest] entities: {len(fmap)} factors, {len(omap)} outcomes", flush=True)
    print(f"[ingest] fetching abstracts (days_back={days_back}) ...", flush=True)
    with connect() as conn:
        papers = _papers_for_today(conn, days_back=days_back, per_entity=per_entity)
    print(f"[ingest] {len(papers)} unique papers fetched")
    summary["papers"] = len(papers)

    for i, p in enumerate(papers):
        with connect() as conn:
            if _already_ingested(conn, p):
                continue
        title = (p.get("title") or "")[:80]
        if not p.get("abstract"):
            continue
        user_prompt = EXTRACT_USER_TMPL.format(
            factors=fact_lines, outcomes=out_lines,
            title=p.get("title",""), journal=p.get("journal",""),
            year=p.get("year",""), abstract=p.get("abstract","")[:6000],
        )
        extraction = None
        last_err: Exception | None = None
        # Up to 2 attempts: first normal, second with stricter "JSON only,
        # no thinking" prompt + larger num_predict.
        for attempt in range(2):
            try:
                extraction = call_json(
                    system=EXTRACT_SYSTEM if attempt == 0
                        else EXTRACT_SYSTEM + " /no_think Return ONLY the JSON object. Do not think out loud, do not explain, do not add any prose before or after.",
                    user=user_prompt,
                    temperature=0.0 if attempt == 1 else 0.1,
                    num_predict=3000 if attempt == 0 else 4500,
                )
                break
            except OllamaUnavailable as e:
                print(f"[ingest] STOP: {e}"); return summary
            except Exception as e:
                last_err = e
                continue
        if extraction is None:
            print(f"[ingest] extract fail '{title}': {last_err}")
            with connect() as conn:
                _record_paper(conn, p, {"_extract_error": str(last_err)[:200]})
            continue

        if not isinstance(extraction, dict) or not extraction.get("relevant"):
            with connect() as conn:
                _record_paper(conn, p, extraction if isinstance(extraction, dict) else {})
            continue

        claims = extraction.get("claims") or []
        summary["claims"] += len(claims)
        if dry_run:
            print(f"[dry] {title} -> {len(claims)} claim(s)"); continue

        with connect() as conn:
            _record_paper(conn, p, extraction)
            for cl in claims:
                res = _apply_claim(conn, p, cl, fmap, omap)
                if not res: continue
                if res["old_tier"] is None: summary["new_edges"] += 1
                if res["old_tier"] and res["new_tier"] != res["old_tier"]:
                    summary["tier_changes"] += 1
                if res["escalate"]:
                    summary["escalations"].append(res)
        if (i + 1) % 10 == 0:
            print(f"  ... {i+1}/{len(papers)}")

    print(f"[ingest] done: {summary}")
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--days-back", type=int, default=2)
    ap.add_argument("--per-entity", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(days_back=a.days_back, per_entity=a.per_entity, dry_run=a.dry_run)
