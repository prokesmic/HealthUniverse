#!/usr/bin/env python3
"""Merge duplicate edges (18.10.2026).

391 factor→outcome pairs had two or more edges (795 rows) — almost always one
seeded with a long population sentence and one with "general adult", e.g.
Ultra-processed food → Type 2 diabetes #18 (A) and #1248 (A). Counts,
graphs and pages showed the same claim twice, sometimes with two tiers.

A group is merged only when all but at most one of its populations are
generic ("general adult", "adults", empty); groups with two different
specific populations (adult women vs older men) are left alone.

Primary edge = highest tier, then most evidence, then oldest id. For each
other edge: evidence rows move to the primary (rows whose PMID the primary
already has are dropped), edge_history and card_reports move too, one
history row on the primary records the merge, the old id goes into
edge_redirect so /edge/<old> keeps working, and the duplicate is deleted.
Tier of the primary is kept (it is the max of the group).

  python scripts/merge_duplicate_edges.py --dry
  python scripts/merge_duplicate_edges.py
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RANK = {"A": 5, "B": 4, "C": 3, "X": 2, "D": 1}
GENERIC = re.compile(r"^\s*(general( adult)?( population)?|adults?|general adults?|all adults|"
                     r"general adult population|humans?)\s*[.;]?\s*$", re.I)


def _connect():
    from db import connect  # type: ignore
    return connect()


def generic(pop: str | None) -> bool:
    return not pop or bool(GENERIC.match(pop.split(";")[0].split(",")[0]))


def mergeable(edges) -> bool:
    return sum(1 for e in edges if not generic(e["population"])) <= 1


def ensure_schema(conn) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS edge_redirect (
                      old_id INTEGER PRIMARY KEY, new_id INTEGER NOT NULL,
                      reason TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')))""")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    with _connect() as conn:
        if not a.dry:
            ensure_schema(conn)
        rows = conn.execute("""SELECT e.id, e.factor_id, e.outcome_id, e.tier, e.population,
                                      (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n
                               FROM edge e WHERE e.tier != 'deprecated'""").fetchall()
        groups = defaultdict(list)
        for r in rows:
            groups[(r["factor_id"], r["outcome_id"])].append(r)
        groups = {k: v for k, v in groups.items() if len(v) > 1}
        merged = skipped = moved = dropped = 0
        for key, es in groups.items():
            if not mergeable(es):
                skipped += 1
                continue
            es = sorted(es, key=lambda e: (-RANK.get(e["tier"], 0), -e["n"], e["id"]))
            p, rest = es[0], es[1:]
            for d in rest:
                merged += 1
                if a.dry:
                    continue
                have = {x[0] for x in conn.execute("SELECT pmid FROM evidence WHERE edge_id=? AND pmid IS NOT NULL",
                                                   (p["id"],))}
                for ev in conn.execute("SELECT id, pmid FROM evidence WHERE edge_id=?", (d["id"],)).fetchall():
                    if ev["pmid"] and ev["pmid"] in have:
                        conn.execute("DELETE FROM evidence WHERE id=?", (ev["id"],))
                        dropped += 1
                    else:
                        conn.execute("UPDATE evidence SET edge_id=? WHERE id=?", (p["id"], ev["id"]))
                        have.add(ev["pmid"])
                        moved += 1
                for t in ("edge_history", "card_reports", "verifier_audit", "seed_topic"):
                    try:
                        conn.execute(f"UPDATE {t} SET edge_id=? WHERE edge_id=?", (p["id"], d["id"]))
                    except Exception:
                        pass
                conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                                VALUES (?, 'merged_edge', ?, ?, ?, 'merge_duplicates')""",
                             (p["id"], str(d["id"]), str(p["id"]),
                              f"duplicate of this pair (tier {d['tier']}, population "
                              f"'{(d['population'] or '')[:60]}') merged in; its evidence moved here"))
                conn.execute("INSERT OR REPLACE INTO edge_redirect (old_id, new_id, reason) VALUES (?,?,?)",
                             (d["id"], p["id"], "duplicate pair merged 2026-10-18"))
                # Redirects that pointed at the deleted edge follow it.
                conn.execute("UPDATE edge_redirect SET new_id=? WHERE new_id=?", (p["id"], d["id"]))
                conn.execute("DELETE FROM edge WHERE id=?", (d["id"],))
        if not a.dry:
            conn.commit()
    print({"groups": len(groups), "merged_edges": merged, "groups_left_alone": skipped,
           "evidence_moved": moved, "evidence_duplicates_dropped": dropped})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
