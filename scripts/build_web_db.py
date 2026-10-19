#!/usr/bin/env python3
"""Publish the slim, web-only copy of the graph DB that Vercel serves.

data/healthuniverse.db is the local working DB. Ingest, bursts, deepening
and ~/Health read and write it, and it keeps everything: ~11k ingested
abstracts with their extraction JSON, verifier audits and edge embeddings.
It reached 76.6 MB on 19.10.2026, and GitHub rejects files over 100 MB, so
it is no longer committed.

The site needs none of those three things (semantic search needs local
Ollama, which Vercel does not have). This script copies the working DB
(a consistent snapshot through the sqlite backup API), empties
ingested_paper and verifier_audit, nulls edge/entity embeddings, VACUUMs, checks
that every web table kept its row count, and atomically replaces
data/healthuniverse.web.db. That file is what the nightly jobs commit.

Size guard: above --warn-mb it sends an ntfy warning (at most once a day).
At or above --max-mb it keeps the previous web DB, warns, and exits 3 so
the caller skips a push GitHub would reject anyway.

Exit codes: 0 built (safe to push), 3 too big (do not push), 1 error.
`--alert MSG` only sends MSG to the same ntfy topic (a failed git push).

    .venv/bin/python scripts/build_web_db.py            # build + guard
    .venv/bin/python scripts/build_web_db.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "healthuniverse.db"
DST = ROOT / "data" / "healthuniverse.web.db"
STAMP = ROOT / "data" / "cache" / "web_db_size_warned"

# Offline-only tables: emptied but kept, so a stray query gets no rows
# rather than "no such table".
STRIP_TABLES = ("ingested_paper", "verifier_audit")
# Embedding BLOBs are only for local semantic search/dedupe (Ollama).
EMBEDDING_TABLES = ("edge", "entity")
# Tables the site reads; their row counts must survive the strip unchanged.
KEEP_TABLES = ("entity", "edge", "evidence", "evidence_status", "edge_history",
               "edge_redirect", "entity_redirect")

WARN_MB = float(os.getenv("HU_WEB_DB_WARN_MB", "60"))
MAX_MB = float(os.getenv("HU_WEB_DB_MAX_MB", "90"))

NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("HU_NTFY_TOPIC", "aimon-gG9ITzfi4BNBklO3")


class BuildError(RuntimeError):
    pass


def ntfy(title: str, body: str) -> bool:
    if not NTFY_TOPIC:
        return False
    req = urllib.request.Request(
        f"{NTFY_URL}/{NTFY_TOPIC}", data=body.encode(), method="POST",
        headers={"Title": title.encode("latin-1", "ignore").decode("latin-1"),
                 "Tags": "warning", "Priority": "high"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return 200 <= r.status < 300
    except Exception as e:  # noqa: BLE001 — a failed alert must not break the build
        print(f"ntfy failed: {e}", file=sys.stderr)
        return False


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _counts(conn: sqlite3.Connection, tables) -> dict[str, int]:
    have = _tables(conn)
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in tables if t in have}


def build(src: Path, out: Path) -> dict:
    """Write the slim copy of `src` to `out` (overwritten). Returns stats."""
    if not src.exists():
        raise BuildError(f"working DB missing: {src}")
    out.unlink(missing_ok=True)
    s = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=60)
    d = sqlite3.connect(out)
    try:
        s.backup(d)
    finally:
        s.close()
    try:
        before = _counts(d, KEEP_TABLES)
        if not before.get("edge"):
            raise BuildError("working DB snapshot has no edges")
        have = _tables(d)
        for t in STRIP_TABLES:
            if t in have:
                d.execute(f"DELETE FROM {t}")
        for t in EMBEDDING_TABLES:
            cols = {r[1] for r in d.execute(f"PRAGMA table_info({t})")}
            if "embedding" in cols:
                d.execute(f"UPDATE {t} SET embedding = NULL WHERE embedding IS NOT NULL")
        d.commit()
        d.execute("VACUUM")
        after = _counts(d, KEEP_TABLES)
        if after != before:
            raise BuildError(f"web tables changed in the strip: {before} -> {after}")
        ok = d.execute("PRAGMA integrity_check").fetchone()[0]
        if ok != "ok":
            raise BuildError(f"integrity_check: {ok}")
    finally:
        d.close()
    return {"counts": after, "bytes": out.stat().st_size}


def _warn_once(title: str, body: str, today: str, force: bool = False) -> None:
    """One size warning a day: both nightly jobs call this script."""
    try:
        if not force and STAMP.read_text().strip() == today:
            return
    except OSError:
        pass
    if ntfy(title, body):
        STAMP.parent.mkdir(parents=True, exist_ok=True)
        STAMP.write_text(today)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--dst", type=Path, default=DST)
    ap.add_argument("--warn-mb", type=float, default=WARN_MB)
    ap.add_argument("--max-mb", type=float, default=MAX_MB)
    ap.add_argument("--dry-run", action="store_true",
                    help="build to a temp file, report, replace nothing, notify nobody")
    ap.add_argument("--alert", metavar="MSG",
                    help="only send MSG to ntfy (nightly scripts: failed push)")
    a = ap.parse_args(argv)
    if a.alert:
        return 0 if ntfy("Health Universe: nightly push FAILED", a.alert) else 1

    tmp = a.dst.with_name(a.dst.name + ".tmp")
    try:
        stats = build(a.src, tmp)
    except (BuildError, sqlite3.Error) as e:
        tmp.unlink(missing_ok=True)
        print(f"✗ web DB build failed: {e}", file=sys.stderr)
        if not a.dry_run:
            ntfy("Health Universe: web DB build FAILED",
                 f"{e}\nNothing pushed; the live site keeps the previous DB.")
        return 1

    mb = stats["bytes"] / 1e6
    src_mb = a.src.stat().st_size / 1e6
    print(f"web DB {mb:.1f} MB (working DB {src_mb:.1f} MB); "
          + ", ".join(f"{k}={v}" for k, v in stats["counts"].items()))
    today = dt.date.today().isoformat()

    if mb >= a.max_mb:
        tmp.unlink(missing_ok=True)
        msg = (f"Web DB would be {mb:.1f} MB (limit {a.max_mb:g}, GitHub rejects "
               f">100). Kept the previous web DB, skipped the push: the live site is "
               f"NOT updating. Prune edge_history/evidence or strip more in "
               f"scripts/build_web_db.py.")
        print(f"✗ {msg}", file=sys.stderr)
        if not a.dry_run:
            _warn_once("Health Universe: web DB too big, push skipped", msg, today,
                       force=True)
        return 3

    if mb >= a.warn_mb:
        msg = (f"Web DB is {mb:.1f} MB; pushes stop at {a.max_mb:g} MB. "
               f"Act before then (scripts/build_web_db.py).")
        print(f"! {msg}")
        if not a.dry_run:
            _warn_once("Health Universe: web DB growing", msg, today)

    if a.dry_run:
        tmp.unlink(missing_ok=True)
        print("dry run: nothing replaced")
        return 0
    os.replace(tmp, a.dst)
    print(f"✓ wrote {a.dst.relative_to(ROOT) if a.dst.is_relative_to(ROOT) else a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
