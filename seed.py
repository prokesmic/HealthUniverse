"""Seed researcher: ask Claude for a deep, structured research summary
on one (factor, outcome) pair and persist it as an edge + evidence rows.

Usage:
    python seed.py --pair magnesium,sleep_quality
    python seed.py --pair magnesium,sleep_quality --dry-run
    python seed.py --next               # take next pending row from seed_topic
    python seed.py --next --limit 5     # take up to N pending rows
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any

from claude_client import CostCapExceeded, call, extract_json
from db import connect


SYSTEM_PROMPT = """You are a careful evidence-grading research assistant for a \
health-knowledge product. For a given (FACTOR -> OUTCOME) pair you produce a \
single rigorous summary of the current peer-reviewed evidence base.

You MUST:
- Weigh evidence by study quality (meta-analyses & large RCTs > cohorts > \
small RCTs > observational > mechanistic/animal).
- Flag conflicting evidence honestly. If the evidence is mixed, say so.
- Note populations (age, sex, comorbidity, genotype) where effect differs.
- Avoid hype. Default to the most boring claim the evidence supports.
- Never fabricate citations. Only include studies you are confident exist; \
omit specific PMIDs/DOIs unless you are certain.
- Return ONLY a single JSON object inside a ```json code fence. No prose \
outside the fence."""


USER_TEMPLATE = """Research this pair and return a structured JSON summary.

FACTOR:  {factor_name}  (slug: {factor_slug}, kind: {factor_kind})
OUTCOME: {outcome_name} (slug: {outcome_slug}, kind: {outcome_kind})

Return JSON with exactly this shape:

{{
  "direction": "protective" | "harmful" | "neutral" | "u_shaped" | "mixed",
  "tier":      "A" | "B" | "C" | "D" | "X",
  "effect_size":  "trivial" | "small" | "moderate" | "large" | "unknown",
  "effect_quant": "<short quantitative effect with CI if known, else empty>",
  "population":   "<who this applies to; 'general adult' if no specific scope>",
  "mechanism":    "<one short paragraph, plain English, what's biologically going on>",
  "summary":      "<2-4 sentence card body for a non-expert reader>",
  "caveats":      "<key cautions, dose ranges, who should NOT do this, ~2 sentences>",
  "evidence": [
    {{
      "citation":   "<authors year journal short>",
      "year":       <int>,
      "study_type": "meta_analysis" | "systematic_review" | "rct" | "cohort"
                  | "case_control" | "cross_sectional" | "mechanistic"
                  | "animal" | "case_report" | "expert_opinion",
      "n_participants": <int or null>,
      "direction":  "<direction this study supports>",
      "quality":    "high" | "moderate" | "low" | "very_low",
      "notes":      "<one-line takeaway>"
    }}
  ]
}}

Tier rubric:
  A = >=2 high-quality meta-analyses or large RCTs, consistent direction, mechanism known
  B = multiple cohorts + plausible mechanism, minor conflicts
  C = early RCTs / strong observational, mechanism plausible
  D = mechanistic/animal/single study only
  X = evidence genuinely split between directions

Aim for 4-10 evidence items, prioritizing the highest-quality ones.
"""


REQUIRED_KEYS = {"direction", "tier", "effect_size", "population",
                 "mechanism", "summary", "evidence"}
VALID_DIRECTIONS = {"protective", "harmful", "neutral", "u_shaped", "mixed"}
VALID_TIERS = {"A", "B", "C", "D", "X"}


def _validate(payload: dict[str, Any]) -> None:
    missing = REQUIRED_KEYS - payload.keys()
    if missing:
        raise ValueError(f"Missing required keys: {missing}")
    if payload["direction"] not in VALID_DIRECTIONS:
        raise ValueError(f"Bad direction: {payload['direction']}")
    if payload["tier"] not in VALID_TIERS:
        raise ValueError(f"Bad tier: {payload['tier']}")
    if not isinstance(payload["evidence"], list) or not payload["evidence"]:
        raise ValueError("Evidence must be a non-empty list")


def research_pair(factor_slug: str, outcome_slug: str, *, dry_run: bool = False) -> dict:
    with connect() as conn:
        factor = conn.execute("SELECT * FROM entity WHERE slug = ?",
                              (factor_slug,)).fetchone()
        outcome = conn.execute("SELECT * FROM entity WHERE slug = ?",
                               (outcome_slug,)).fetchone()
    if not factor or not outcome:
        raise SystemExit(f"Unknown entity: {factor_slug if not factor else outcome_slug}. "
                         f"Run `python topics.py` first.")

    user = USER_TEMPLATE.format(
        factor_name=factor["name"], factor_slug=factor["slug"], factor_kind=factor["kind"],
        outcome_name=outcome["name"], outcome_slug=outcome["slug"], outcome_kind=outcome["kind"],
    )
    ref = f"{factor_slug}->{outcome_slug}"
    print(f"[seed] researching {ref} ...", file=sys.stderr)
    text, usage = call(system=SYSTEM_PROMPT, user=user, operation="seed",
                       ref=ref, max_tokens=4096, temperature=0.2)
    payload = extract_json(text)
    _validate(payload)
    print(f"[seed] {ref}: tier={payload['tier']} dir={payload['direction']} "
          f"evidence={len(payload['evidence'])} cost=${usage.usd:.4f}",
          file=sys.stderr)

    if dry_run:
        return payload

    edge_id = _persist(factor["id"], outcome["id"], payload)
    _mark_topic_done(factor_slug, outcome_slug, edge_id, usage.usd)
    return payload | {"_edge_id": edge_id}


def _persist(factor_id: int, outcome_id: int, p: dict) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO edge (factor_id, outcome_id, direction, tier, effect_size, "
            "effect_quant, population, mechanism, summary, caveats, seed_source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'claude_seed') "
            "ON CONFLICT(factor_id, outcome_id, population) DO UPDATE SET "
            "  direction=excluded.direction, tier=excluded.tier, "
            "  effect_size=excluded.effect_size, effect_quant=excluded.effect_quant, "
            "  mechanism=excluded.mechanism, summary=excluded.summary, "
            "  caveats=excluded.caveats, updated_at=datetime('now'), "
            "  last_reviewed=datetime('now') "
            "RETURNING id",
            (factor_id, outcome_id, p["direction"], p["tier"],
             p.get("effect_size", "unknown"), p.get("effect_quant", ""),
             p.get("population", "general adult"), p.get("mechanism", ""),
             p.get("summary", ""), p.get("caveats", "")),
        )
        edge_id = cur.fetchone()["id"]
        conn.execute("DELETE FROM evidence WHERE edge_id = ?", (edge_id,))
        for ev in p["evidence"]:
            conn.execute(
                "INSERT INTO evidence (edge_id, citation, year, study_type, "
                "n_participants, direction, quality, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (edge_id, ev.get("citation", ""), ev.get("year"),
                 ev.get("study_type"), ev.get("n_participants"),
                 ev.get("direction"), ev.get("quality"), ev.get("notes", "")),
            )
        conn.execute(
            "INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
            "VALUES (?, 'seed', NULL, ?, 'initial Claude seed research', 'claude_seed')",
            (edge_id, json.dumps({"tier": p["tier"], "direction": p["direction"]})),
        )
        return edge_id


def _mark_topic_done(factor_slug: str, outcome_slug: str, edge_id: int, cost: float) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE seed_topic SET status='done', edge_id=?, cost_usd=?, "
            "finished_at=datetime('now') WHERE factor_slug=? AND outcome_slug=?",
            (edge_id, cost, factor_slug, outcome_slug),
        )


def _next_pending(limit: int) -> list[tuple[str, str]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT factor_slug, outcome_slug FROM seed_topic WHERE status='pending' "
            "ORDER BY priority ASC, id ASC LIMIT ?",
            (limit,),
        ).fetchall()
    return [(r["factor_slug"], r["outcome_slug"]) for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pair", help="factor_slug,outcome_slug")
    g.add_argument("--next", action="store_true", help="take pending from seed_topic")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pairs: list[tuple[str, str]]
    if args.pair:
        f, o = args.pair.split(",", 1)
        pairs = [(f.strip(), o.strip())]
    else:
        pairs = _next_pending(args.limit)
        if not pairs:
            print("No pending topics."); return

    for f, o in pairs:
        try:
            result = research_pair(f, o, dry_run=args.dry_run)
            if args.dry_run:
                print(json.dumps(result, indent=2))
        except CostCapExceeded as e:
            print(f"[seed] STOP: {e}", file=sys.stderr); sys.exit(2)
        except Exception as e:
            print(f"[seed] FAIL {f}->{o}: {e}", file=sys.stderr)
            with connect() as conn:
                conn.execute(
                    "UPDATE seed_topic SET status='failed', error=?, "
                    "finished_at=datetime('now') WHERE factor_slug=? AND outcome_slug=?",
                    (str(e), f, o),
                )


if __name__ == "__main__":
    main()
