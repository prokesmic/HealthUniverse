#!/usr/bin/env python3
"""Put the citation-check state of the working DB back to what a backup had.

The verifier (verify_evidence.py) writes four things: evidence.real_title,
evidence.relevance_score, evidence.relevance_status and edge.review_status.
The public levels (web/core.py) are computed from them. This script copies
those four columns from a backup DB into the working DB for every row that
exists in both, and touches nothing else: edges and evidence added since
the backup stay, with whatever state they have.

    .venv/bin/python scripts/restore_review.py --from ~/HealthUniverse-backups/<file>.db
    .venv/bin/python scripts/restore_review.py --from <file>.db --yes     # write

Without --yes it only reports what would change. Rebuild the web DB after
(scripts/build_web_db.py) to publish the restored state.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "healthuniverse.db"


def restore(db: Path, backup: Path, write: bool) -> dict[str, int]:
    conn = sqlite3.connect(db, timeout=120)
    try:
        conn.execute("ATTACH DATABASE ? AS bak", (f"file:{backup}?mode=ro",))
        changed = {
            "edges": conn.execute(
                "SELECT COUNT(*) FROM edge e JOIN bak.edge b ON b.id = e.id "
                "WHERE COALESCE(e.review_status,'') != COALESCE(b.review_status,'')").fetchone()[0],
            "evidence": conn.execute(
                "SELECT COUNT(*) FROM evidence e JOIN bak.evidence b ON b.id = e.id "
                "WHERE COALESCE(e.relevance_status,'') != COALESCE(b.relevance_status,'') "
                "   OR COALESCE(e.relevance_score,-1) != COALESCE(b.relevance_score,-1)").fetchone()[0],
        }
        if write:
            conn.execute(
                "UPDATE edge SET review_status = (SELECT b.review_status FROM bak.edge b WHERE b.id = edge.id) "
                "WHERE id IN (SELECT id FROM bak.edge)")
            conn.execute(
                "UPDATE evidence SET (real_title, relevance_score, relevance_status) = "
                "(SELECT b.real_title, b.relevance_score, b.relevance_status FROM bak.evidence b "
                " WHERE b.id = evidence.id) WHERE id IN (SELECT id FROM bak.evidence)")
            conn.commit()
        return changed
    finally:
        conn.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="backup", type=Path, required=True)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--yes", action="store_true", help="write (default: report only)")
    a = ap.parse_args(argv)
    if not a.backup.exists():
        print(f"backup not found: {a.backup}", file=sys.stderr)
        return 1
    changed = restore(a.db, a.backup, a.yes)
    verb = "restored" if a.yes else "would restore"
    print(f"{verb}: review_status on {changed['edges']} edges, "
          f"citation-check result on {changed['evidence']} evidence rows")
    if not a.yes:
        print("report only; pass --yes to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
