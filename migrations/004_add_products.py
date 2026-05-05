"""Add the product table for the supplement quality layer.

Idempotent. Safe to run multiple times.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from db import connect


def run() -> None:
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS product (
            id              INTEGER PRIMARY KEY,
            slug            TEXT NOT NULL UNIQUE,
            name            TEXT NOT NULL,
            brand           TEXT,
            entity_slug     TEXT,
            form            TEXT,
            typical_dose_mg INTEGER,
            notes           TEXT,
            label_accuracy_score        INTEGER,
            label_accuracy_note         TEXT,
            contamination_score         INTEGER,
            contamination_note          TEXT,
            dosage_alignment_score      INTEGER,
            dosage_alignment_note       TEXT,
            third_party_tested          INTEGER,
            third_party_org             TEXT,
            formulation_concerns        TEXT,
            last_reviewed               TEXT,
            created_at                  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_product_entity ON product(entity_slug);
        """)
        print("  ensured product table")


if __name__ == "__main__":
    run()
    print("migration complete")
