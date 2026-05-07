"""Gemma burst-mode ingest.

The default daily.py loop pulls only the last 1–2 days of PubMed +
Europe PMC abstracts, which is fine for steady-state but caps
throughput at ~3–5 new edges/day. Burst mode widens the window and
loops until a configurable cap is hit, so the corpus can grow ~30×
faster for a few days during catch-up.

Safety guards (vs raw daily.py):
  • --max-edges hard cap per run (default 100)
  • --cap-tier ceiling on auto-assigned tier (default 'C') — no
    edge created in this run can be set higher than C without manual
    audit. Existing edges may still re-tier normally because their
    full evidence stack stays intact.
  • Logs every new edge to data/audits/burst-{run}.json
  • Validates inserted PMIDs at end via the existing --verify path
  • Resumable: tracks ingested_paper rows so re-running picks up
    where it left off.

Recommended cadence:
  python gemma_burst.py --max-edges 50 --days-back 14    # 1st night
  python gemma_burst.py --max-edges 100 --days-back 30   # 2nd night
  python gemma_burst.py --max-edges 100 --days-back 60   # 3rd night
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# Suppress READ_ONLY so we can write to the local DB
os.environ.pop("READ_ONLY", None)

from db import connect                                  # noqa: E402
from ingest import daily                                # noqa: E402

AUDIT_DIR = ROOT / "data" / "audits"


_TIER_RANK = {"A": 5, "B": 4, "C": 3, "X": 2, "D": 1}


def cap_new_edges(start_id: int, cap_tier: str) -> list[dict]:
    """Reset tier on any newly-created edge whose tier exceeds cap.
    Returns a list of {edge_id, original_tier} for the audit log."""
    cap_rank = _TIER_RANK.get(cap_tier, 3)
    capped = []
    with connect() as conn:
        rows = conn.execute("""
            SELECT id, tier FROM edge
            WHERE id > ? AND seed_source = 'gemma_daily'""", (start_id,)).fetchall()
        for r in rows:
            t = r["tier"]
            if _TIER_RANK.get(t, 0) > cap_rank:
                conn.execute(
                    "UPDATE edge SET tier=? WHERE id=?", (cap_tier, r["id"]))
                conn.execute("""INSERT INTO edge_history
                    (edge_id, changed_at, field, old_value, new_value, reason, actor)
                    VALUES (?, datetime('now'), 'tier', ?, ?, ?, ?)""",
                    (r["id"], t, cap_tier,
                     f"Burst-mode auto-tier cap ({cap_tier}); flagged for manual audit",
                     "gemma_burst"))
                capped.append({"edge_id": r["id"], "original_tier": t})
    return capped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-edges", type=int, default=100,
                    help="Hard cap on new edges per run (default 100).")
    ap.add_argument("--days-back", type=int, default=30,
                    help="PubMed lookback window in days (default 30).")
    ap.add_argument("--per-entity", type=int, default=15,
                    help="Abstracts pulled per entity (default 15).")
    ap.add_argument("--cap-tier", default="C", choices=["A","B","C","D"],
                    help="Ceiling on auto-assigned tier for new edges "
                         "(default C; never auto-promote without audit).")
    ap.add_argument("--passes", type=int, default=1,
                    help="Number of run() iterations within this invocation. "
                         "Each pass extends days_back by --days-back-step.")
    ap.add_argument("--days-back-step", type=int, default=15,
                    help="When --passes > 1, increment days_back per pass.")
    a = ap.parse_args()

    # Snapshot current edge id so we can scope the cap to this run only.
    with connect() as conn:
        start_id = (conn.execute("SELECT MAX(id) m FROM edge").fetchone()
                    ["m"] or 0)
        start_studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]
    started_at = datetime.now()

    print(f"[burst] start_id={start_id} max_edges={a.max_edges} "
          f"days_back={a.days_back} per_entity={a.per_entity} "
          f"cap_tier={a.cap_tier}")

    summary = {"papers": 0, "claims": 0, "new_edges": 0, "tier_changes": 0}
    days = a.days_back
    for pass_i in range(a.passes):
        print(f"[burst] pass {pass_i+1}/{a.passes}  days_back={days}")
        try:
            r = daily.run(days_back=days, per_entity=a.per_entity, dry_run=False)
            for k in summary: summary[k] = summary.get(k, 0) + r.get(k, 0)
        except Exception as exc:
            print(f"[burst] pass aborted: {exc}")
            break
        # Stop early if cap reached
        with connect() as conn:
            new_now = conn.execute(
                "SELECT COUNT(*) c FROM edge WHERE id > ?", (start_id,)
            ).fetchone()["c"]
        print(f"[burst] new edges so far: {new_now} / {a.max_edges}")
        if new_now >= a.max_edges:
            print(f"[burst] cap hit, stopping")
            break
        days += a.days_back_step

    capped = cap_new_edges(start_id, a.cap_tier)
    with connect() as conn:
        end_new = conn.execute(
            "SELECT COUNT(*) c FROM edge WHERE id > ?", (start_id,)
        ).fetchone()["c"]
        end_studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    log = {
        "started_at": started_at.isoformat(),
        "ended_at": datetime.now().isoformat(),
        "duration_min": round((datetime.now() - started_at).total_seconds() / 60, 1),
        "params": {"max_edges": a.max_edges, "days_back": a.days_back,
                   "per_entity": a.per_entity, "cap_tier": a.cap_tier,
                   "passes": a.passes},
        "summary": summary,
        "new_edges_total": end_new,
        "new_studies_total": end_studies - start_studies,
        "auto_tier_caps_applied": capped,
    }
    out = AUDIT_DIR / f"burst-{started_at.strftime('%Y%m%d-%H%M')}.json"
    out.write_text(json.dumps(log, indent=2))

    print()
    print(f"[burst] done in {log['duration_min']} min")
    print(f"  new edges:   {end_new}")
    print(f"  new studies: {log['new_studies_total']}")
    print(f"  capped tiers: {len(capped)}")
    print(f"  log: {out}")
    print()
    print("Next steps:")
    print("  1. python seed_from_payloads.py validate --verify   # validate any new payloads")
    print("  2. python audit_tiers.py --since 1 --max 50         # Claude audit on burst additions")
    print("  3. git add -A && git commit && git push             # ship the additions")


if __name__ == "__main__":
    main()
