"""The slim web DB (scripts/build_web_db.py) and its size guard.

The working DB is local-only; Vercel reads data/healthuniverse.web.db. These
tests pin that the copy drops what only offline jobs need, keeps every row
the site reads, refuses to publish past the size limit, and that db.py
points Vercel at it.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_web_db", ROOT / "scripts" / "build_web_db.py")
bwd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bwd)


def _working_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript((ROOT / "schema.sql").read_text())
    conn.execute("CREATE TABLE verifier_audit (id INTEGER PRIMARY KEY, edge_id INTEGER, note TEXT)")
    conn.execute("INSERT INTO entity (id, slug, name, kind, embedding) VALUES "
                 "(1,'coffee','Coffee','food',?), (2,'sleep','Sleep','process',NULL)",
                 (b"\x00" * 3072,))
    conn.execute("INSERT INTO edge (id, factor_id, outcome_id, direction, tier, seed_source, "
                 "summary, embedding) VALUES (1,1,2,'harmful','B','manual','Coffee late hurts sleep',?)",
                 (b"\x01" * 3072,))
    conn.execute("INSERT INTO edge_history (edge_id, field, old_value, new_value, reason) "
                 "VALUES (1,'tier','C','B','test')")
    conn.execute("INSERT INTO edge_redirect (old_id, new_id) VALUES (99, 1)")
    for i in range(50):
        conn.execute("INSERT INTO ingested_paper (pmid, title, abstract, extraction) "
                     "VALUES (?,?,?,?)", (str(i), f"paper {i}", "x" * 4000, "{}"))
    conn.execute("INSERT INTO verifier_audit (edge_id, note) VALUES (1, 'checked')")
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def no_ntfy(monkeypatch, tmp_path):
    sent = []
    monkeypatch.setattr(bwd, "ntfy", lambda title, body: sent.append((title, body)) or True)
    monkeypatch.setattr(bwd, "STAMP", tmp_path / "stamp")
    return sent


def test_build_strips_offline_data_and_keeps_web_rows(tmp_path):
    src = _working_db(tmp_path / "work.db")
    out = tmp_path / "web.db"
    stats = bwd.build(src, out)
    c = sqlite3.connect(out)
    assert c.execute("SELECT COUNT(*) FROM ingested_paper").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM verifier_audit").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM edge WHERE embedding IS NOT NULL").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM entity WHERE embedding IS NOT NULL").fetchone()[0] == 0
    assert c.execute("SELECT summary FROM edge WHERE id=1").fetchone()[0] == "Coffee late hurts sleep"
    assert stats["counts"]["edge_history"] == 1 and stats["counts"]["edge_redirect"] == 1
    assert out.stat().st_size < src.stat().st_size
    # The working DB is only read.
    w = sqlite3.connect(src)
    assert w.execute("SELECT COUNT(*) FROM ingested_paper").fetchone()[0] == 50
    assert w.execute("SELECT COUNT(*) FROM edge WHERE embedding IS NOT NULL").fetchone()[0] == 1


def test_build_is_byte_identical_for_unchanged_source(tmp_path):
    # The nightly scripts detect "changed" with git diff on the web DB.
    src = _working_db(tmp_path / "work.db")
    bwd.build(src, tmp_path / "a.db")
    bwd.build(src, tmp_path / "b.db")
    assert (tmp_path / "a.db").read_bytes() == (tmp_path / "b.db").read_bytes()


def test_over_limit_keeps_previous_copy_and_signals_no_push(tmp_path, no_ntfy):
    src = _working_db(tmp_path / "work.db")
    dst = tmp_path / "web.db"
    dst.write_bytes(b"previous published copy")
    rc = bwd.main(["--src", str(src), "--dst", str(dst), "--max-mb", "0.001"])
    assert rc == 3
    assert dst.read_bytes() == b"previous published copy"
    assert not (tmp_path / "web.db.tmp").exists()
    assert len(no_ntfy) == 1 and "push skipped" in no_ntfy[0][0]


def test_warning_band_publishes_and_warns_once_a_day(tmp_path, no_ntfy):
    src = _working_db(tmp_path / "work.db")
    dst = tmp_path / "web.db"
    args = ["--src", str(src), "--dst", str(dst), "--warn-mb", "0.001", "--max-mb", "50"]
    assert bwd.main(args) == 0
    assert dst.exists()
    assert bwd.main(args) == 0   # second nightly job, same day
    assert len(no_ntfy) == 1 and "growing" in no_ntfy[0][0]


def test_under_warning_is_silent(tmp_path, no_ntfy):
    src = _working_db(tmp_path / "work.db")
    assert bwd.main(["--src", str(src), "--dst", str(tmp_path / "web.db")]) == 0
    assert no_ntfy == []


def test_missing_working_db_fails_loudly(tmp_path, no_ntfy):
    dst = tmp_path / "web.db"
    dst.write_bytes(b"previous")
    assert bwd.main(["--src", str(tmp_path / "nope.db"), "--dst", str(dst)]) == 1
    assert dst.read_bytes() == b"previous"
    assert len(no_ntfy) == 1 and "FAILED" in no_ntfy[0][0]


def test_dry_run_replaces_nothing_and_notifies_nobody(tmp_path, no_ntfy):
    src = _working_db(tmp_path / "work.db")
    dst = tmp_path / "web.db"
    assert bwd.main(["--src", str(src), "--dst", str(dst), "--dry-run",
                     "--warn-mb", "0.001"]) == 0
    assert not dst.exists() and no_ntfy == []


def test_vercel_reads_the_web_db():
    env = {k: v for k, v in os.environ.items() if k != "DB_PATH"}
    env["VERCEL"] = "1"
    out = subprocess.run([sys.executable, "-c", "import db; print(db.DB_PATH)"],
                         cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == str(ROOT / "data" / "healthuniverse.web.db")


def test_web_code_does_not_read_stripped_tables():
    # These tables are empty on Vercel; a page that needs them would be blank.
    for f in list((ROOT / "web").glob("*.py")) + [ROOT / "api" / "index.py"]:
        text = f.read_text()
        for t in bwd.STRIP_TABLES:
            assert t not in text, f"{f.name} reads {t}, which the web DB does not carry"


def test_alert_only_sends_and_builds_nothing(tmp_path, no_ntfy, monkeypatch):
    # Nightly scripts call --alert when git push fails.
    monkeypatch.setattr(bwd, "build", lambda *a: pytest.fail("--alert must not build"))
    assert bwd.main(["--alert", "push failed"]) == 0
    assert no_ntfy == [("Health Universe: nightly push FAILED", "push failed")]
