"""Add embedding columns to entity and edge.

Idempotent — checks if columns exist before adding. Run anytime:

    python migrations/001_add_embeddings.py
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
        for table in ("entity", "edge"):
            if not _has_column(conn, table, "embedding"):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN embedding BLOB")
                conn.execute(f"ALTER TABLE {table} ADD COLUMN embedded_at TEXT")
                print(f"  added embedding columns to {table}")
            else:
                print(f"  {table}.embedding already exists, skipping")


if __name__ == "__main__":
    run()
    print("migration complete")
