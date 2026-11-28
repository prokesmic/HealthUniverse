"""One definition of what the public site may show (28.11.2026).

Every edge gets one of three public levels:

  core      tier A or B, evidence verified, at least CORE_MIN_VERIFIED
            verified evidence rows. The only level allowed on the home
            page, in Discoveries, the Stack Brief, the RSS feed and the
            social cron. With HU_CORE_STRICT_PROMOTION=1 an edge whose
            A/B tier was last set by the local model alone is not core
            either (off by default: it is an open owner decision).
  labelled  everything else that has been through the citation check.
            Reachable on its own page and in lists, with a label.
  hidden    never checked ('unreviewed'), 'needs_recheck', or listed in
            data/hidden_edges.json. scripts/build_web_db.py removes these
            from the web DB, so no query on the site can show them.

The level is computed at the source: build_web_db.py stores it in
edge.public_level of the published DB. A DB without that column (the
local working DB, test fixtures) gets the same answer from LEVEL_SQL
inline, so there is no second definition and no fail-open path.

Switches (environment, both default on):
  HU_CORE_GATE=0    the site stops filtering by level and the builder
                    stops removing hidden edges
  HU_NARROW=0       the switched-off pages and the old navigation return
  HU_CORE_STRICT_PROMOTION=1   (default off) see 'core' above
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIDDEN_FILE = ROOT / "data" / "hidden_edges.json"

CORE_MIN_VERIFIED = 2
# A published DB with fewer core edges than this is treated as broken
# (verifier wiped, wrong DB): the builder keeps the previous one.
CORE_FLOOR = int(os.getenv("HU_CORE_FLOOR", "300"))


def gate_on() -> bool:
    return os.getenv("HU_CORE_GATE", "1") != "0"


def narrow_on() -> bool:
    return os.getenv("HU_NARROW", "1") != "0"


def strict_promotion() -> bool:
    return os.getenv("HU_CORE_STRICT_PROMOTION", "0") == "1"


def level_sql(alias: str = "e") -> str:
    """The level of edge `alias` as an SQL expression (no stored column needed)."""
    a = alias
    local = ""
    if strict_promotion():
        local = f"""
       AND COALESCE((SELECT ch.actor FROM edge_history ch
                     WHERE ch.edge_id = {a}.id AND ch.field = 'tier'
                     ORDER BY ch.changed_at DESC, ch.id DESC LIMIT 1),
                    {a}.seed_source) NOT IN ('gemma_daily')"""
    return f"""(CASE
      WHEN COALESCE({a}.review_status,'unreviewed') IN ('unreviewed','needs_recheck')
        THEN 'hidden'
      WHEN {a}.tier IN ('A','B')
       AND {a}.review_status IN ('human_reviewed','clinician_reviewed')
        THEN 'core'
      WHEN {a}.tier IN ('A','B')
       AND {a}.review_status = 'verified_evidence'
       AND (SELECT COUNT(*) FROM evidence cv WHERE cv.edge_id = {a}.id
              AND cv.relevance_status = 'verified') >= {CORE_MIN_VERIFIED}{local}
        THEN 'core'
      ELSE 'labelled' END)"""


def hidden_ids() -> dict[int, str]:
    """{edge_id: reason} from data/hidden_edges.json (manual overrides)."""
    try:
        raw = json.loads(HIDDEN_FILE.read_text())
    except (OSError, ValueError):
        return {}
    out: dict[int, str] = {}
    for row in raw.get("edges", []):
        try:
            out[int(row["id"])] = str(row.get("reason", ""))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def has_column(conn: sqlite3.Connection) -> bool:
    return any(r[1] == "public_level" for r in conn.execute("PRAGMA table_info(edge)"))


def apply_levels(conn: sqlite3.Connection) -> dict[str, int]:
    """Store the level of every edge in edge.public_level. Returns counts."""
    if not has_column(conn):
        conn.execute("ALTER TABLE edge ADD COLUMN public_level TEXT")
    conn.execute(f"UPDATE edge SET public_level = {level_sql('edge')}")
    manual = hidden_ids()
    if manual:
        conn.executemany("UPDATE edge SET public_level = 'hidden' WHERE id = ?",
                         [(i,) for i in manual])
    conn.commit()
    return {r[0]: r[1] for r in conn.execute(
        "SELECT public_level, COUNT(*) FROM edge GROUP BY public_level")}


def prune_hidden(conn: sqlite3.Connection) -> int:
    """Remove hidden edges and their rows from a DB that is about to be
    published. Only ever called on the web copy, never on the working DB."""
    ids = [r[0] for r in conn.execute("SELECT id FROM edge WHERE public_level = 'hidden'")]
    if not ids:
        return 0
    conn.execute("CREATE TEMP TABLE _hidden(id INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO _hidden VALUES (?)", [(i,) for i in ids])
    for table in ("evidence", "edge_history"):
        conn.execute(f"DELETE FROM {table} WHERE edge_id IN (SELECT id FROM _hidden)")
    conn.execute("DELETE FROM edge WHERE id IN (SELECT id FROM _hidden)")
    conn.execute("DROP TABLE _hidden")
    conn.commit()
    return len(ids)


def write_meta(conn: sqlite3.Connection, levels: dict[str, int], hidden_removed: int) -> None:
    """What the builder did, for the Trust page of the published DB."""
    conn.execute("CREATE TABLE IF NOT EXISTS public_meta (key TEXT PRIMARY KEY, value TEXT)")
    rows = {"core": levels.get("core", 0), "labelled": levels.get("labelled", 0),
            "held_back": hidden_removed}
    conn.executemany("INSERT OR REPLACE INTO public_meta (key, value) VALUES (?, ?)",
                     [(k, str(v)) for k, v in rows.items()])
    conn.commit()


def public_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """{core, labelled, held_back}. From the builder's record when there is
    one (published DB), otherwise counted live (working DB)."""
    try:
        got = {r[0]: int(r[1]) for r in conn.execute("SELECT key, value FROM public_meta")}
        if got:
            return got
    except (sqlite3.Error, ValueError):
        pass
    by = {r[0]: r[1] for r in conn.execute(
        f"SELECT {level_sql('e')} AS lv, COUNT(*) FROM edge e GROUP BY lv")}
    return {"core": by.get("core", 0), "labelled": by.get("labelled", 0),
            "held_back": by.get("hidden", 0)}


# ─── read side (web) ──────────────────────────────────────────────────

_COLUMN: dict[str, bool] = {}


def _expr(conn: sqlite3.Connection, alias: str) -> str:
    key = str(conn.execute("PRAGMA database_list").fetchone()[2])
    if key not in _COLUMN:
        _COLUMN[key] = has_column(conn)
    return f"{alias}.public_level" if _COLUMN[key] else level_sql(alias)


def level_expr(conn: sqlite3.Connection, alias: str = "e") -> str:
    """SQL for the level of edge `alias`, to SELECT next to the edge."""
    return _expr(conn, alias)


def core_clause(conn: sqlite3.Connection, alias: str = "e") -> str:
    """' AND <edge is core>' for recommending surfaces; '' when the gate is off."""
    if not gate_on():
        return ""
    return f" AND {_expr(conn, alias)} = 'core'"


def visible_clause(conn: sqlite3.Connection, alias: str = "e") -> str:
    """' AND <edge is not hidden>'. The published DB has no hidden edges;
    this keeps a local run on the working DB honest too."""
    if not gate_on():
        return ""
    return f" AND {_expr(conn, alias)} != 'hidden'"


# ─── narrowed site ────────────────────────────────────────────────────

# Path prefixes switched off while HU_NARROW is on. GET pages redirect
# to the home page; API and POST calls answer 404.
OFF_PREFIXES = (
    "/labs", "/api/labs", "/me", "/api/me", "/sync", "/restore",
    "/prevent", "/og/prevent", "/my-plan", "/start", "/welcome", "/_variant",
    "/coach", "/today", "/diary", "/score", "/og/score", "/risk",
    "/protocols", "/protocol/", "/products", "/product/",
    "/claim-check", "/api/claim-check", "/api/pro-waitlist",
    "/handout", "/ask", "/brief", "/api/profile-brief",
    "/api/interactions", "/data-export",
    "/api/cron/proactive", "/api/vapid-key", "/digest", "/subscribe",
)
# Exceptions inside the prefixes above.
ON_EXACT = ("/api/me/stack",)


def is_off(path: str) -> bool:
    if not narrow_on():
        return False
    if path in ON_EXACT:
        return False
    for p in OFF_PREFIXES:
        if path == p or path.startswith(p if p.endswith("/") else p + "/"):
            return True
    return False
