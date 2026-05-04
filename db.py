"""SQLite access layer for Health Universe."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

_PROJECT_ROOT = Path(__file__).parent.resolve()
_default_db = _PROJECT_ROOT / "data" / "healthuniverse.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db))).resolve()
SCHEMA_PATH = _PROJECT_ROOT / "schema.sql"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


READ_ONLY = bool(os.getenv("VERCEL") or os.getenv("HU_READ_ONLY"))


@contextmanager
def connect():
    if READ_ONLY:
        uri = f"file:{DB_PATH}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not READ_ONLY:
        conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        if not READ_ONLY:
            conn.commit()
    finally:
        conn.close()


def upsert_entity(conn: sqlite3.Connection, slug: str, name: str, kind: str,
                  aliases: list[str] | None = None, description: str = "") -> int:
    cur = conn.execute("SELECT id FROM entity WHERE slug = ?", (slug,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO entity (slug, name, kind, aliases, description) VALUES (?, ?, ?, ?, ?)",
        (slug, name, kind, json.dumps(aliases or []), description),
    )
    return cur.lastrowid


def upsert_source(conn: sqlite3.Connection, slug: str, name: str, kind: str,
                  trust_weight: float, homepage: str = "", notes: str = "") -> int:
    cur = conn.execute("SELECT id FROM source WHERE slug = ?", (slug,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO source (slug, name, kind, trust_weight, homepage, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (slug, name, kind, trust_weight, homepage, notes),
    )
    return cur.lastrowid


def total_spent_usd(conn: sqlite3.Connection) -> float:
    row = conn.execute("SELECT COALESCE(SUM(usd), 0) AS t FROM cost_ledger").fetchone()
    return float(row["t"])


def record_cost(conn: sqlite3.Connection, *, provider: str, model: str, operation: str,
                input_tokens: int, output_tokens: int, usd: float, ref: str = "") -> None:
    conn.execute(
        "INSERT INTO cost_ledger (provider, model, operation, input_tokens, "
        "output_tokens, usd, ref) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (provider, model, operation, input_tokens, output_tokens, usd, ref),
    )


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
