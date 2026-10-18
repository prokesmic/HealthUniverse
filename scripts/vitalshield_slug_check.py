#!/usr/bin/env python3
"""Edge counts for every entity slug VitalShield (~/Health) uses (18.10.2026).

The VitalShield backend reads this graph by slug: hu_link.MAPS, risk_map
rules, evidence.X_SLUGS/Y_SLUGS (+ accepted garmin.edge_map rows),
lab_predictions.MARKERS, levers.PLANS and data/vitalshield_priority.json.
Merging entities must not silently drop edges from those views, so before
and after a merge we snapshot, per slug:

  edges     — non-deprecated edges with the slug as factor or outcome
  partners  — distinct entities on the other end (merging cvd into
              cardiovascular_disease collapses two edges into one, which is
              not a loss; losing a partner is)
  resolved  — the slug it resolves to through entity_redirect (itself if live)

Run with ~/Health's venv (it imports Health modules read-only):

  ~/Health/.venv/bin/python scripts/vitalshield_slug_check.py --out before.json
  ~/Health/.venv/bin/python scripts/vitalshield_slug_check.py --compare before.json
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "healthuniverse.db"
HEALTH = Path(os.path.expanduser("~/Health"))


def health_slugs() -> dict[str, list[str]]:
    """{slug: [where it is used]}."""
    sys.path.insert(0, str(HEALTH))
    out: dict[str, list[str]] = {}

    def add(s, where):
        if s:
            out.setdefault(s, []).append(where)

    import evidence  # type: ignore
    import hu_link  # type: ignore
    for m in hu_link.MAPS:
        add(m.slug, f"hu_link:{m.series}")
    for k, (fs, _f) in evidence.X_SLUGS.items():
        for s in fs:
            add(s, f"evidence.X:{k}")
    for k, ys in evidence.Y_SLUGS.items():
        for s in ys:
            add(s, f"evidence.Y:{k}")
    for k, ss in evidence.dynamic_slugs().items():
        for s in ss:
            add(s, f"edge_map:{k}")
    for mod, attr in (("risk_map", "_rules"), ("lab_predictions", "MARKERS"), ("levers", "PLANS")):
        try:
            m = __import__(mod)
            v = getattr(m, attr)
            v = v() if callable(v) else v
            for k, val in v.items():
                if mod == "lab_predictions":
                    for s in val[0]:
                        add(s, f"{mod}:{k}")
                else:
                    add(k, mod)
        except Exception as e:  # a module that fails to import is reported, not hidden
            print(f"warning: {mod}.{attr}: {e}", file=sys.stderr)
    pri = ROOT / "data" / "vitalshield_priority.json"
    if pri.exists():
        for s in json.loads(pri.read_text()).get("slugs", []):
            add(s, "priority.json")
    return out


def resolve(conn, slug: str) -> str | None:
    if conn.execute("SELECT 1 FROM entity WHERE slug=?", (slug,)).fetchone():
        return slug
    try:
        r = conn.execute("SELECT new_slug FROM entity_redirect WHERE old_slug=?", (slug,)).fetchone()
    except sqlite3.OperationalError:
        return None
    return r[0] if r else None


def snapshot() -> dict:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = {}
    for slug, where in sorted(health_slugs().items()):
        live = resolve(conn, slug)
        if not live:
            rows[slug] = {"resolved": None, "edges": 0, "partners": [], "used_in": where}
            continue
        q = conn.execute("""
            SELECT e.id, CASE WHEN f.slug=? THEN o.slug ELSE f.slug END
              FROM edge e JOIN entity f ON f.id=e.factor_id JOIN entity o ON o.id=e.outcome_id
             WHERE (f.slug=? OR o.slug=?) AND e.tier!='deprecated'""", (live, live, live)).fetchall()
        rows[slug] = {"resolved": live, "edges": len(q),
                      "partners": sorted({p for _, p in q}), "used_in": where}
    return rows


def canonical_partner(conn, slug: str) -> str:
    return resolve(conn, slug) or slug


def compare(before: dict, after: dict) -> list[str]:
    """Problems: a slug that stopped resolving, or lost a partner entity
    (partners compared after canonicalising the old ones)."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    bad = []
    for slug, b in before.items():
        a = after.get(slug)
        if a is None:
            continue  # slug no longer used by Health (map updated) — checked via its canonical
        if b["resolved"] and not a["resolved"]:
            bad.append(f"{slug}: no longer resolves")
            continue
        lost = {canonical_partner(conn, p) for p in b["partners"]} - set(a["partners"])
        lost.discard(a["resolved"])  # self-edges after a merge
        if lost:
            bad.append(f"{slug}: lost partners {sorted(lost)}")
    return bad


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--compare")
    a = ap.parse_args(argv)
    snap = snapshot()
    if a.out:
        Path(a.out).write_text(json.dumps(snap, indent=1, ensure_ascii=False))
    total = sum(r["edges"] for r in snap.values())
    print(f"{len(snap)} slugs, {total} slug-edge links, "
          f"{sum(1 for r in snap.values() if not r['resolved'])} unresolved")
    if a.compare:
        before = json.loads(Path(a.compare).read_text())
        # A slug Health dropped from its maps is checked through what replaced it.
        for slug, b in before.items():
            if slug not in snap:
                conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
                live = resolve(conn, slug)
                snap[slug] = next((r for r in snap.values() if r["resolved"] == live),
                                  {"resolved": None, "edges": 0, "partners": []})
        for slug, b in sorted(before.items()):
            n = snap[slug]
            if n["edges"] != b["edges"] or n["resolved"] != slug:
                print(f"  {slug:40s} {b['edges']:4d} → {n['edges']:4d} edges, "
                      f"{len(b['partners'])} → {len(n['partners'])} partners (via {n['resolved']})")
        bad = compare(before, snap)
        for x in bad:
            print("PROBLEM", x)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
