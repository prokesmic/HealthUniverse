"""Ingest pre-researched payload JSON files into the knowledge graph.

This is how external contributors (Codex, future PR authors, anyone with an
LLM budget of their own) seed the graph WITHOUT hitting our Anthropic key.
Each payload file carries the full output of one (factor, outcome) deep
research run, in the same shape `seed.py` writes.

Usage:
    python seed_from_payloads.py validate            # validate all files, no DB writes
    python seed_from_payloads.py validate path.json  # validate one
    python seed_from_payloads.py ingest              # write everything to DB
    python seed_from_payloads.py ingest --dry-run    # show what would change
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect, upsert_entity   # noqa: E402

PAYLOAD_DIR = ROOT / "data" / "seed_payloads"
SOURCE_TAG  = "manual"   # uses existing seed_source enum; tag origin in summary

VALID_DIRECTIONS = {"protective", "harmful", "neutral", "u_shaped", "mixed"}
VALID_TIERS      = {"A", "B", "C", "D", "X"}
VALID_KINDS      = {"food", "nutrient", "supplement", "drug", "activity",
                    "behavior", "environmental", "pathogen", "gene",
                    "biomarker", "condition", "process"}
VALID_STUDY_TYPES = {"meta_analysis", "systematic_review", "rct", "cohort",
                     "case_control", "cross_sectional", "mechanistic",
                     "animal", "case_report", "expert_opinion"}
VALID_QUALITIES  = {"high", "moderate", "low", "very_low"}


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------

def validate_payload(p: dict, *, known_factor_slugs: set[str] | None = None,
                     known_outcome_slugs: set[str] | None = None) -> list[str]:
    """Return a list of error strings. Empty list = valid."""
    errors: list[str] = []

    # Header
    if p.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    # Optional new entities
    new_ents = p.get("new_entities", []) or []
    new_slugs: set[str] = set()
    if not isinstance(new_ents, list):
        errors.append("new_entities must be a list")
    else:
        for i, e in enumerate(new_ents):
            for k in ("slug", "name", "kind"):
                if not e.get(k):
                    errors.append(f"new_entities[{i}].{k} required")
            if e.get("kind") and e["kind"] not in VALID_KINDS:
                errors.append(f"new_entities[{i}].kind invalid: {e['kind']}")
            new_slugs.add(e.get("slug", ""))

    # Edges
    edges = p.get("edges")
    if not isinstance(edges, list) or not edges:
        errors.append("edges must be a non-empty list")
        return errors

    for i, e in enumerate(edges):
        prefix = f"edges[{i}]"
        for k in ("factor_slug", "outcome_slug", "direction", "tier",
                 "summary", "mechanism", "evidence"):
            if e.get(k) in (None, ""):
                errors.append(f"{prefix}.{k} required")
        if e.get("direction") and e["direction"] not in VALID_DIRECTIONS:
            errors.append(f"{prefix}.direction invalid: {e['direction']}")
        if e.get("tier") and e["tier"] not in VALID_TIERS:
            errors.append(f"{prefix}.tier invalid: {e['tier']}")

        # Slug must be either known or in this payload's new_entities
        f_slug, o_slug = e.get("factor_slug"), e.get("outcome_slug")
        if f_slug and known_factor_slugs is not None:
            if f_slug not in known_factor_slugs and f_slug not in new_slugs:
                errors.append(f"{prefix}.factor_slug '{f_slug}' is not a known entity "
                              f"and not declared in new_entities")
        if o_slug and known_outcome_slugs is not None:
            if o_slug not in known_outcome_slugs and o_slug not in new_slugs:
                errors.append(f"{prefix}.outcome_slug '{o_slug}' is not a known entity "
                              f"and not declared in new_entities")

        # Evidence
        ev = e.get("evidence") or []
        if not isinstance(ev, list) or not ev:
            errors.append(f"{prefix}.evidence must be a non-empty list")
        else:
            if len(ev) < 3:
                errors.append(f"{prefix}.evidence must have >=3 rows (found {len(ev)})")
            for j, r in enumerate(ev):
                if not r.get("citation"):
                    errors.append(f"{prefix}.evidence[{j}].citation required")
                if r.get("study_type") and r["study_type"] not in VALID_STUDY_TYPES:
                    errors.append(f"{prefix}.evidence[{j}].study_type invalid: {r['study_type']}")
                if r.get("quality") and r["quality"] not in VALID_QUALITIES:
                    errors.append(f"{prefix}.evidence[{j}].quality invalid: {r['quality']}")
                if r.get("direction") and r["direction"] not in VALID_DIRECTIONS:
                    errors.append(f"{prefix}.evidence[{j}].direction invalid")

        # Anti-fabrication heuristics
        if len(e.get("summary", "")) < 80:
            errors.append(f"{prefix}.summary too short (need 2-4 sentences)")
        if len(e.get("mechanism", "")) < 60:
            errors.append(f"{prefix}.mechanism too short")

    return errors


def _known_slugs(conn) -> tuple[set[str], set[str]]:
    factors = {r["slug"] for r in conn.execute(
        "SELECT slug FROM entity WHERE kind IN "
        "('food','nutrient','supplement','drug','activity','behavior',"
        "'environmental','pathogen','gene')").fetchall()}
    outcomes = {r["slug"] for r in conn.execute(
        "SELECT slug FROM entity WHERE kind IN "
        "('condition','process','biomarker')").fetchall()}
    return factors, outcomes


def validate_dir(payload_dir: Path = PAYLOAD_DIR) -> tuple[int, int]:
    if not payload_dir.exists():
        print(f"No payload dir at {payload_dir}"); return (0, 0)
    files = sorted(payload_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]
    with connect() as conn:
        kf, ko = _known_slugs(conn)
    ok = bad = 0
    for f in files:
        try:
            p = json.loads(f.read_text())
        except Exception as e:
            print(f"[FAIL] {f.name}: cannot parse JSON: {e}"); bad += 1; continue
        errs = validate_payload(p, known_factor_slugs=kf, known_outcome_slugs=ko)
        if errs:
            print(f"[FAIL] {f.name}:"); [print(f"  - {e}") for e in errs]
            bad += 1
        else:
            print(f"[OK]   {f.name} ({len(p.get('edges', []))} edge(s))")
            ok += 1
    print(f"\n{ok} ok, {bad} failed, {len(files)} total")
    return ok, bad


# ----------------------------------------------------------------------------
# Ingestion
# ----------------------------------------------------------------------------

def _persist_edge(conn, e: dict, file_name: str) -> tuple[int, str]:
    """Insert/update one edge + its evidence. Returns (edge_id, action)."""
    fid = conn.execute("SELECT id FROM entity WHERE slug=?",
                       (e["factor_slug"],)).fetchone()
    oid = conn.execute("SELECT id FROM entity WHERE slug=?",
                       (e["outcome_slug"],)).fetchone()
    if not fid or not oid:
        raise ValueError(f"unknown slug in {file_name}: "
                         f"{e['factor_slug']} or {e['outcome_slug']}")

    population = e.get("population", "general adult")
    existing = conn.execute(
        "SELECT id FROM edge WHERE factor_id=? AND outcome_id=? AND population=?",
        (fid["id"], oid["id"], population)).fetchone()
    summary = e.get("summary", "")
    if "[seeded by Codex]" not in summary and "[codex" not in summary.lower():
        # Tag externally-seeded edges so we can tell them apart later
        # without changing the schema enum.
        summary = summary  # keep as-is; we tag in edge_history.reason instead

    if existing:
        conn.execute(
            "UPDATE edge SET direction=?, tier=?, effect_size=?, effect_quant=?, "
            "  mechanism=?, summary=?, caveats=?, "
            "  updated_at=datetime('now'), last_reviewed=datetime('now') WHERE id=?",
            (e["direction"], e["tier"], e.get("effect_size", "unknown"),
             e.get("effect_quant", ""), e["mechanism"], summary,
             e.get("caveats", ""), existing["id"]))
        edge_id = existing["id"]
        action = "updated"
    else:
        cur = conn.execute(
            "INSERT INTO edge (factor_id, outcome_id, direction, tier, "
            "effect_size, effect_quant, population, mechanism, summary, "
            "caveats, seed_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (fid["id"], oid["id"], e["direction"], e["tier"],
             e.get("effect_size", "unknown"), e.get("effect_quant", ""),
             population, e["mechanism"], summary, e.get("caveats", ""),
             SOURCE_TAG))
        edge_id = cur.lastrowid
        action = "created"

    # Replace evidence wholesale
    conn.execute("DELETE FROM evidence WHERE edge_id=?", (edge_id,))
    for ev in e["evidence"]:
        conn.execute(
            "INSERT INTO evidence (edge_id, citation, year, study_type, "
            "n_participants, direction, quality, notes) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (edge_id, ev.get("citation", ""), ev.get("year"),
             ev.get("study_type"), ev.get("n_participants"),
             ev.get("direction"), ev.get("quality"), ev.get("notes", "")))

    conn.execute(
        "INSERT INTO edge_history (edge_id, field, old_value, new_value, "
        "reason, actor) VALUES (?, 'seed', NULL, ?, ?, 'codex_payload')",
        (edge_id, json.dumps({"tier": e["tier"], "direction": e["direction"]}),
         f"payload import: {file_name}"))
    return edge_id, action


def ingest_dir(payload_dir: Path = PAYLOAD_DIR, *, dry_run: bool = False) -> dict:
    summary = {"created": 0, "updated": 0, "new_entities": 0,
               "files": 0, "errors": []}
    files = sorted(payload_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]

    for f in files:
        try:
            p = json.loads(f.read_text())
        except Exception as e:
            summary["errors"].append(f"{f.name}: {e}"); continue
        with connect() as conn:
            kf, ko = _known_slugs(conn)
        errs = validate_payload(p, known_factor_slugs=kf, known_outcome_slugs=ko)
        if errs:
            summary["errors"].append(f"{f.name}: {len(errs)} validation error(s)")
            continue
        if dry_run:
            print(f"[dry] would import {f.name}: "
                  f"{len(p.get('new_entities', []))} new entities, "
                  f"{len(p.get('edges', []))} edges")
            summary["files"] += 1; continue

        with connect() as conn:
            for ent in p.get("new_entities", []) or []:
                upsert_entity(conn, slug=ent["slug"], name=ent["name"],
                              kind=ent["kind"], aliases=ent.get("aliases") or [],
                              description=ent.get("description", ""))
                summary["new_entities"] += 1
            for e in p["edges"]:
                try:
                    _, action = _persist_edge(conn, e, f.name)
                    summary[action] += 1
                except Exception as exc:
                    summary["errors"].append(f"{f.name}: {exc}")
        summary["files"] += 1

    print(f"[ingest] {summary}")
    return summary


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("validate", "ingest"))
    ap.add_argument("path", nargs="?", help="single file to validate")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.cmd == "validate":
        if a.path:
            p = json.loads(Path(a.path).read_text())
            with connect() as conn:
                kf, ko = _known_slugs(conn)
            errs = validate_payload(p, known_factor_slugs=kf, known_outcome_slugs=ko)
            if errs:
                print(f"[FAIL] {a.path}:"); [print(f"  - {e}") for e in errs]; sys.exit(1)
            print(f"[OK] {a.path}")
        else:
            ok, bad = validate_dir()
            sys.exit(1 if bad else 0)
    else:
        ingest_dir(dry_run=a.dry_run)


if __name__ == "__main__":
    main()
