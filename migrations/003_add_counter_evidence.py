"""Add is_counter flag to evidence — supports counter-evidence panel.

Idempotent. Safe to run multiple times.

Codex Track D will produce ~80–120 counter-evidence payloads on top of
this scaffold. This migration + the small demo set seeded inline make
sure the UI renders meaningfully even before that lands.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import connect


def _has_column(conn, table: str, col: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == col for r in rows)


def run() -> None:
    with connect() as conn:
        if not _has_column(conn, "evidence", "is_counter"):
            conn.execute("ALTER TABLE evidence ADD COLUMN is_counter INTEGER NOT NULL DEFAULT 0")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_counter "
                "ON evidence(edge_id, is_counter)")
            print("  added evidence.is_counter")
        else:
            print("  evidence.is_counter already exists, skipping")


if __name__ == "__main__":
    run()
    print("migration complete")
