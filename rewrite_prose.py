"""Rewrite templated summary + mechanism on Codex-payload edges using Gemma.

The Codex v2 batch landed with verified citations but templated prose:
  - "In [pop], pooled meta-analytic evidence suggest…"
  - "may influence X through oxidative damage, inflammatory tone, hormone…"

This script picks each edge whose history shows actor='codex_payload',
asks Gemma to rewrite summary + mechanism in plain voice anchored on the
actual evidence rows, and writes back. It logs an `edge_history` row
with actor='gemma_rewrite'.

Free, runs on local Gemma. ~10s per edge → ~40 min for 250 edges.

Usage:
    python rewrite_prose.py --limit 5 --dry-run
    python rewrite_prose.py --limit 250
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                                # noqa: E402
from ollama_client import call, OllamaUnavailable     # noqa: E402

SYSTEM = """You rewrite knowledge-graph card prose. You receive a (factor → outcome) \
pair, the evidence rows that support it, and the existing draft prose. You return \
two short pieces of plain English: a 2-4 sentence summary, and a 2-3 sentence \
mechanism. Anchor on the strongest piece of evidence. Avoid filler. Never invent \
study details — work only from what's provided. Return JSON with two keys: \
'summary' and 'mechanism'."""

USER_TMPL = """FACTOR:  {factor}
OUTCOME: {outcome}
DIRECTION: {direction}
TIER: {tier}
POPULATION: {population}

EXISTING SUMMARY (often templated, please rewrite):
{summary}

EXISTING MECHANISM (often kitchen-sink, please rewrite):
{mechanism}

EVIDENCE ROWS (cite the strongest in your summary, by author/year):
{evidence_lines}

Write:
1. summary (2-4 sentences, plain voice). Anchor on the strongest evidence — \
mention it concretely, e.g. "A 2015 meta-analysis of 5.7M people…". State the \
direction clearly. No filler like "tracks with" or "appears to".
2. mechanism (2-3 sentences, factor-specific). Don't list five generic \
pathways. Pick the actual mode of action. If unsure, write "Mechanism not \
well established."

Return EXACTLY:
```json
{{"summary": "...", "mechanism": "..."}}
```"""


def _candidates(conn, limit: int) -> list[dict]:
    """Edges seeded via Codex payload that haven't been rewritten yet."""
    rows = conn.execute("""
        SELECT e.id, e.tier, e.direction, e.population, e.summary, e.mechanism,
               f.name AS factor, o.name AS outcome
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE EXISTS (SELECT 1 FROM edge_history h WHERE h.edge_id = e.id
                      AND h.actor = 'codex_payload')
          AND NOT EXISTS (SELECT 1 FROM edge_history h2 WHERE h2.edge_id = e.id
                          AND h2.actor = 'gemma_rewrite')
        ORDER BY e.id LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def _evidence_for(conn, edge_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT citation, year, study_type, n_participants, quality, notes "
        "FROM evidence WHERE edge_id=? ORDER BY "
        "CASE study_type WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2 "
        "WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 6", (edge_id,)).fetchall()
    return [dict(r) for r in rows]


def _evidence_lines(rows: list[dict]) -> str:
    out = []
    for r in rows:
        n = f", n={r['n_participants']:,}" if r.get("n_participants") else ""
        out.append(f"- {r['citation']} ({r['year'] or '—'}, {r['study_type'] or '—'}{n}, "
                   f"quality={r.get('quality') or '—'}): {r.get('notes', '')[:160]}")
    return "\n".join(out) or "- (no evidence rows available)"


def rewrite_one(conn, edge: dict) -> dict | None:
    evidence = _evidence_for(conn, edge["id"])
    if not evidence:
        return None
    user = USER_TMPL.format(
        factor=edge["factor"], outcome=edge["outcome"],
        direction=edge["direction"], tier=edge["tier"],
        population=edge["population"], summary=edge["summary"][:600],
        mechanism=edge["mechanism"][:600],
        evidence_lines=_evidence_lines(evidence),
    )
    text = call(system=SYSTEM, user=user, temperature=0.3, num_predict=1500)
    import json, re
    m = re.search(r"\{[^{}]*\"summary\"[^{}]*\}", text, re.DOTALL)
    if not m:
        # try fenced block
        m2 = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if not m2:
            return None
        m = m2.group(1)
    else:
        m = m.group(0)
    try:
        return json.loads(m)
    except Exception:
        return None


def run(*, limit: int = 250, dry_run: bool = False) -> dict:
    summary = {"considered": 0, "rewritten": 0, "skipped": 0, "errors": 0}
    with connect() as conn:
        candidates = _candidates(conn, limit)
    summary["considered"] = len(candidates)
    print(f"[rewrite] {len(candidates)} candidate edges")

    for i, e in enumerate(candidates):
        try:
            with connect() as conn:
                payload = rewrite_one(conn, e)
        except OllamaUnavailable as ex:
            print(f"[rewrite] STOP: {ex}"); return summary
        except Exception as ex:
            summary["errors"] += 1
            print(f"  fail edge#{e['id']}: {ex}")
            continue

        if not payload or not payload.get("summary") or not payload.get("mechanism"):
            summary["skipped"] += 1; continue

        new_sum = payload["summary"].strip()
        new_mech = payload["mechanism"].strip()
        if len(new_sum) < 60 or len(new_mech) < 40:
            summary["skipped"] += 1; continue

        if dry_run:
            print(f"[dry] edge#{e['id']} {e['factor']} -> {e['outcome']}")
            print(f"  new summary:   {new_sum[:160]}")
            print(f"  new mechanism: {new_mech[:160]}")
            summary["rewritten"] += 1
            continue

        with connect() as conn:
            conn.execute(
                "UPDATE edge SET summary=?, mechanism=?, updated_at=datetime('now') "
                "WHERE id=?", (new_sum, new_mech, e["id"]))
            conn.execute(
                "INSERT INTO edge_history (edge_id, field, old_value, new_value, "
                "reason, actor) VALUES (?, 'prose', ?, ?, "
                "'Gemma rewrite of templated Codex prose', 'gemma_rewrite')",
                (e["id"], (e["summary"] or "")[:400], new_sum[:400]))
        summary["rewritten"] += 1
        if (i + 1) % 10 == 0:
            print(f"  ... {i+1}/{len(candidates)} | rewritten={summary['rewritten']}")

    print(f"[rewrite] done: {summary}")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=250)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(limit=a.limit, dry_run=a.dry_run)
