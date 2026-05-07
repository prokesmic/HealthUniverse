"""Claude tier-audit pass on recently added edges.

Picks every tier-A and tier-B edge created/updated in the last N days,
sends each one to Claude with the deterministic tier rules + the
supporting evidence rows, and asks Claude to confirm or recommend a
re-tiering. Output is logged to data/audits/tier-audit-{YYYY-WWW}.json
for human review — never auto-applied.

    python audit_tiers.py --since 7
    python audit_tiers.py --since 30 --max 50

Cost: ~$0.05 per edge (Claude Sonnet, ~600 in / 200 out tokens).
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                              # noqa: E402
from claude_client import call as claude_call        # noqa: E402

AUDIT_DIR = ROOT / "data" / "audits"

SYSTEM = """You are a careful evidence-grading assistant. You apply the
deterministic Health Universe tier rules to a single edge and decide
whether the assigned tier is correct.

Tier rules:
- A (Strong): >=2 high-quality meta-analyses or systematic reviews,
  total score >=12, consistent direction, no major contradictions.
- B (Moderate): >=1 SR/meta-analysis + >=2 cohorts or RCTs, total score >=7.
- C (Emerging): multiple consistent observational studies or one RCT;
  promising but not yet replicated.
- X (Contested): the literature is genuinely split, meta-analyses disagree.
- D (Limited): mechanism-only, animal studies, single small trial.

Score per evidence row:
- meta_analysis quality high: 4
- systematic_review quality high: 3
- rct n>=500 quality high: 3
- rct n<500: 1.5
- cohort n>=5000: 2
- cohort n<5000: 1
- case_control: 1
- cross_sectional: 0.5
- mechanistic / animal: 0.25

Return STRICT JSON only:
{
  "decision": "confirm" | "demote" | "promote",
  "suggested_tier": "A" | "B" | "C" | "X" | "D",
  "reason": "one short sentence explaining the call",
  "computed_score": <number>
}
No markdown, no commentary. JSON only.
"""


def fmt_evidence(rows: list[dict]) -> str:
    lines = []
    for r in rows[:8]:
        n = f", n={r['n_participants']:,}" if r.get("n_participants") else ""
        lines.append(
            f"- {r.get('citation','')[:100]} "
            f"({r.get('study_type','?')}{n}, quality {r.get('quality','?')})")
    return "\n".join(lines) or "  (no evidence rows)"


def audit_edge(edge: dict) -> dict:
    user_msg = (
        f"EDGE id={edge['id']}\n"
        f"Factor: {edge['f_name']}\n"
        f"Outcome: {edge['o_name']}\n"
        f"Population: {edge.get('population','general adult')}\n"
        f"Direction: {edge['direction']}\n"
        f"Current tier: {edge['tier']}\n"
        f"Effect size: {edge.get('effect_size','?')}\n"
        f"Summary: {(edge.get('summary') or '')[:300]}\n\n"
        f"EVIDENCE ROWS ({len(edge['evidence'])}):\n{fmt_evidence(edge['evidence'])}\n\n"
        "Apply the tier rules and return JSON."
    )
    text, _u = claude_call(system=SYSTEM, user=user_msg,
                           operation="tier-audit", max_tokens=300,
                           temperature=0.0)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"): text = text[4:].strip()
    return json.loads(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=7,
                    help="Audit edges modified in last N days")
    ap.add_argument("--max", type=int, default=50,
                    help="Maximum edges to audit (cost cap)")
    args = ap.parse_args()

    cutoff = (datetime.now() - timedelta(days=args.since)).strftime("%Y-%m-%d")
    with connect() as conn:
        rows = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                   e.population, e.created_at, e.updated_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE e.tier IN ('A','B') AND
                  (e.created_at >= ? OR e.updated_at >= ?)
            ORDER BY e.tier, e.updated_at DESC
            LIMIT ?""", (cutoff, cutoff, args.max)).fetchall()
        edges = []
        for r in rows:
            d = dict(r)
            d["evidence"] = [dict(ev) for ev in conn.execute(
                "SELECT citation, study_type, n_participants, quality "
                "FROM evidence WHERE edge_id=? "
                "ORDER BY CASE study_type "
                "  WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2 "
                "  WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END "
                "LIMIT 8", (d["id"],)).fetchall()]
            edges.append(d)

    print(f"[audit] {len(edges)} tier-A/B edges to audit (since {cutoff})")
    if not edges:
        return

    results = []
    confirms = demotes = promotes = errors = 0
    for i, e in enumerate(edges, 1):
        try:
            r = audit_edge(e)
            r["edge_id"] = e["id"]
            r["current_tier"] = e["tier"]
            r["pair"] = f"{e['f_name']} → {e['o_name']}"
            results.append(r)
            if r["decision"] == "confirm":   confirms += 1
            elif r["decision"] == "demote":  demotes += 1
            elif r["decision"] == "promote": promotes += 1
            print(f"  [{i:3}/{len(edges)}] {e['tier']} {e['f_name']} → {e['o_name']}: "
                  f"{r['decision']} ({r.get('suggested_tier','?')})")
        except Exception as exc:
            errors += 1
            print(f"  [{i:3}/{len(edges)}] ERR {exc}")

    iso_year, iso_week, _ = datetime.now().isocalendar()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AUDIT_DIR / f"tier-audit-{iso_year}-W{iso_week:02d}.json"
    out_file.write_text(json.dumps({
        "ran_at": datetime.now().isoformat(),
        "since_days": args.since,
        "n_audited": len(results),
        "confirms": confirms, "demotes": demotes, "promotes": promotes,
        "errors": errors,
        "results": results,
    }, indent=2))
    print(f"[audit] Wrote {out_file}: {confirms} confirm, {demotes} demote, {promotes} promote, {errors} error")


if __name__ == "__main__":
    main()
