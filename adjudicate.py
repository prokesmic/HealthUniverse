"""Claude adjudicator for tier-A/B promotions and demotions.

The daily ingest re-scores edges from evidence weights. When an edge crosses
into tier A or B (or falls out of A), we want a careful human-grade pass
before publishing the change. That's expensive judgment Gemma can't reliably
do — so we ask Claude. This is the ONLY other place Claude is allowed.

Usage:
    python adjudicate.py --pending           # show queued items
    python adjudicate.py --run --limit 5     # adjudicate up to N
"""
from __future__ import annotations

import argparse
import json
import sys

from claude_client import CostCapExceeded, call, extract_json
from db import connect


SYSTEM = """You are an evidence-grading adjudicator for a health knowledge \
graph. You receive an edge (factor → outcome) plus its evidence list, and \
you decide the correct confidence tier (A/B/C/D/X) and an updated card-style \
summary. Be conservative; only assign A or B if the rubric clearly fits. \
Return JSON only inside a ```json fence."""

USER_TMPL = """Edge: {factor} -> {outcome}
Current tier: {old_tier} (Gemma proposed: {new_tier})
Direction: {direction}
Population: {population}

Evidence rows (n={n}):
{evidence_json}

Tier rubric:
  A = >=2 high-quality meta-analyses or large RCTs, consistent direction, mechanism known
  B = multiple cohorts + plausible mechanism, minor conflicts
  C = early RCTs / strong observational, mechanism plausible
  D = mechanistic/animal/single study only
  X = evidence genuinely split

Return JSON with this exact shape:
{{
  "tier":      "A"|"B"|"C"|"D"|"X",
  "direction": "protective"|"harmful"|"neutral"|"u_shaped"|"mixed",
  "summary":   "<2-4 sentence card body, plain English>",
  "mechanism": "<one short paragraph>",
  "caveats":   "<key cautions ~2 sentences>",
  "reason":    "<why this tier given the evidence>"
}}"""


def _pending(conn) -> list[dict]:
    """Edges flagged for adjudication: most recent jumps into A/B."""
    rows = conn.execute("""
        SELECT e.id, e.tier, e.direction, e.population,
               f.name AS factor, o.name AS outcome,
               (SELECT COUNT(*) FROM evidence v WHERE v.edge_id=e.id) AS n
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        JOIN edge_history h ON h.edge_id = e.id
        WHERE h.field = 'tier'
          AND h.actor = 'gemma_daily'
          AND h.new_value IN ('A','B')
          AND NOT EXISTS (
            SELECT 1 FROM edge_history h2
            WHERE h2.edge_id = e.id AND h2.actor = 'claude_adjudicator'
              AND h2.changed_at > h.changed_at
          )
        GROUP BY e.id
        ORDER BY h.changed_at DESC""").fetchall()
    return [dict(r) for r in rows]


def adjudicate_edge(edge_id: int) -> dict:
    with connect() as conn:
        e = conn.execute("""
            SELECT e.*, f.name AS factor, o.name AS outcome
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.id = ?""", (edge_id,)).fetchone()
        ev = conn.execute(
            "SELECT citation, year, study_type, n_participants, direction, quality, notes "
            "FROM evidence WHERE edge_id=? ORDER BY year DESC", (edge_id,)).fetchall()
        prev_tier_row = conn.execute(
            "SELECT old_value FROM edge_history WHERE edge_id=? AND field='tier' "
            "ORDER BY changed_at DESC LIMIT 1", (edge_id,)).fetchone()

    user = USER_TMPL.format(
        factor=e["factor"], outcome=e["outcome"],
        old_tier=prev_tier_row["old_value"] if prev_tier_row else "—",
        new_tier=e["tier"], direction=e["direction"], population=e["population"],
        n=len(ev), evidence_json=json.dumps([dict(r) for r in ev], indent=2),
    )
    text, usage = call(system=SYSTEM, user=user, operation="adjudicate",
                       ref=str(edge_id), max_tokens=2000, temperature=0.1)
    payload = extract_json(text)

    with connect() as conn:
        old_tier = e["tier"]
        conn.execute(
            "UPDATE edge SET tier=?, direction=?, summary=?, mechanism=?, "
            "caveats=?, last_reviewed=datetime('now'), updated_at=datetime('now') "
            "WHERE id=?",
            (payload["tier"], payload["direction"], payload.get("summary", ""),
             payload.get("mechanism", ""), payload.get("caveats", ""), edge_id))
        conn.execute(
            "INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor) "
            "VALUES (?, 'tier', ?, ?, ?, 'claude_adjudicator')",
            (edge_id, old_tier, payload["tier"], payload.get("reason", "")))
    return {"edge_id": edge_id, "old": old_tier, "new": payload["tier"],
            "cost_usd": usage.usd}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args()

    with connect() as conn:
        pend = _pending(conn)
    print(f"{len(pend)} edge(s) pending adjudication")
    for r in pend[:20]:
        print(f"  edge#{r['id']} tier={r['tier']} {r['factor']} -> {r['outcome']} (n={r['n']})")

    if not a.run: return
    for r in pend[: a.limit]:
        try:
            res = adjudicate_edge(r["id"])
            print(f"  adjudicated edge#{res['edge_id']}: {res['old']} -> {res['new']} (${res['cost_usd']:.4f})")
        except CostCapExceeded as e:
            print(f"STOP: {e}"); sys.exit(2)
        except Exception as e:
            print(f"FAIL edge#{r['id']}: {e}")


if __name__ == "__main__":
    main()
