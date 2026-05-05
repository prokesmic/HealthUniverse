"""Add evidence_status for PMID retraction tracking.

Idempotent — safe to run multiple times:

    python migrations/002_add_evidence_status.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import connect


def run() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_status (
                pmid            TEXT PRIMARY KEY,
                is_retracted    INTEGER NOT NULL DEFAULT 0,
                retraction_note TEXT,
                last_checked    TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_retracted
            ON evidence_status(is_retracted)
        """)
        print("  ensured evidence_status table + idx_status_retracted")


if __name__ == "__main__":
    run()
    print("migration complete")
