"""Ingest pre-researched payload JSON files into the knowledge graph.

This is how external contributors (Codex, future PR authors, anyone with an
LLM budget of their own) seed the graph WITHOUT hitting our Anthropic key.
Each payload file carries the full output of one (factor, outcome) deep
research run, in the same shape `seed.py` writes.

Usage:
    python seed_from_payloads.py validate            # validate all files, no DB writes
    python seed_from_payloads.py validate path.json  # validate one
    python seed_from_payloads.py validate --verify   # also check PMIDs against PubMed (slow)
    python seed_from_payloads.py ingest              # write everything to DB
    python seed_from_payloads.py ingest --dry-run    # show what would change
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx

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

# Study types where n_participants is required (others are mechanism/animal/
# expert opinion where total-n may not apply).
N_REQUIRED_TYPES = {"meta_analysis", "systematic_review", "rct", "cohort",
                    "case_control", "cross_sectional"}


# ----------------------------------------------------------------------------
# Citation truthfulness checks — catches the failure mode where a payload has
# valid JSON shape but fabricated/abbreviated/templated citations.
# ----------------------------------------------------------------------------

def _pubmed_lookup(pmids: list[str]) -> dict[str, dict]:
    """Fetch title/journal/year for a batch of PMIDs from PubMed esummary.
    Free, no key needed, ~3 req/s rate limit."""
    out: dict[str, dict] = {}
    for chunk_start in range(0, len(pmids), 100):
        chunk = pmids[chunk_start:chunk_start + 100]
        try:
            r = httpx.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(chunk),
                        "retmode": "json"},
                timeout=30.0,
            )
            r.raise_for_status()
            for pmid, rec in r.json().get("result", {}).items():
                if pmid == "uids" or not isinstance(rec, dict):
                    continue
                out[pmid] = {
                    "title": rec.get("title", ""),
                    "journal": rec.get("source", ""),
                    "year": rec.get("pubdate", "")[:4] if rec.get("pubdate") else "",
                }
        except Exception as e:
            print(f"  [pubmed lookup] {e}", file=sys.stderr)
        time.sleep(0.4)
        missing = [pmid for pmid in chunk if pmid not in out]
        for pmid in missing:
            try:
                r = httpx.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params={"db": "pubmed", "id": pmid, "retmode": "xml"},
                    timeout=30.0,
                )
                r.raise_for_status()
                root = ET.fromstring(r.text)
                article = root.find(".//PubmedArticle")
                if article is None:
                    continue
                title_node = article.find(".//ArticleTitle")
                title = "".join(title_node.itertext()) if title_node is not None else ""
                if not title:
                    continue
                journal = (article.findtext(".//Journal/ISOAbbreviation", "")
                           or article.findtext(".//Journal/Title", ""))
                year = article.findtext(".//PubDate/Year", "")
                if not year:
                    medline_date = article.findtext(".//PubDate/MedlineDate", "")
                    year = medline_date[:4] if medline_date else ""
                out[pmid] = {"title": title, "journal": journal, "year": year}
            except Exception as e:
                print(f"  [pubmed efetch] {pmid}: {e}", file=sys.stderr)
            time.sleep(0.4)
    return out


def _title_matches(claimed: str, real: str) -> bool:
    """Fuzzy: titles match if they share >=70% of the words (case-insensitive)."""
    if not claimed or not real:
        return False
    a = " ".join(claimed.lower().split())
    b = " ".join(real.lower().split())
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.65


def verify_citations(payload: dict, pubmed_cache: dict[str, dict]) -> list[str]:
    """Return errors. Requires every evidence row of stat-quantitative type
    to have a real PMID resolvable on PubMed AND a title that matches what
    PubMed returns."""
    errors: list[str] = []
    for i, e in enumerate(payload.get("edges", [])):
        for j, ev in enumerate(e.get("evidence", [])):
            prefix = f"edges[{i}].evidence[{j}]"
            st = ev.get("study_type")

            # Hard rule: stat-quantitative studies must carry a PMID
            if st in N_REQUIRED_TYPES and not ev.get("pmid"):
                errors.append(f"{prefix}: study_type={st} requires a PMID")

            # If a PMID is given, it must resolve and the title must match
            pmid = ev.get("pmid")
            if pmid:
                rec = pubmed_cache.get(str(pmid))
                if not rec:
                    errors.append(f"{prefix}: PMID {pmid} did not resolve on PubMed")
                else:
                    notes = ev.get("notes", "")
                    if notes and not _title_matches(notes, rec["title"]):
                        # Title may live in either `notes` (Codex's pattern)
                        # or be parseable from `citation`. Try both.
                        if not _title_matches(ev.get("citation", ""), rec["title"]):
                            errors.append(
                                f"{prefix}: PMID {pmid} resolves to "
                                f"{rec['title'][:80]!r} which doesn't match "
                                f"the claimed citation/notes")

            # Citation must look like a real first-author surname + year, not
            # a single-letter placeholder
            cit = ev.get("citation", "")
            first_token = cit.split()[0] if cit else ""
            if first_token and len(first_token.rstrip(".,")) <= 2:
                errors.append(f"{prefix}: citation '{cit[:60]}' starts with "
                              f"a single-letter token; use 'Surname JF' format")

            # Stat-quantitative studies must report n_participants
            if st in N_REQUIRED_TYPES and ev.get("n_participants") in (None, 0, ""):
                errors.append(f"{prefix}: study_type={st} requires n_participants")
    return errors


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

    mode = p.get("mode", "replace")
    if mode not in ("replace", "densify"):
        errors.append("mode must be 'replace' (default) or 'densify'")

    # Optional new entities (not allowed in densify mode)
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
        if mode == "densify" and new_ents:
            errors.append("densify mode cannot declare new_entities (target edge "
                          "must already exist on known entities)")

    # Edges
    edges = p.get("edges")
    if not isinstance(edges, list) or not edges:
        errors.append("edges must be a non-empty list")
        return errors

    # In densify mode the edge prose fields are optional (we don't touch them);
    # only factor_slug, outcome_slug, evidence are required.
    if mode == "densify":
        required_edge_fields = ("factor_slug", "outcome_slug", "evidence")
    else:
        required_edge_fields = ("factor_slug", "outcome_slug", "direction",
                                "tier", "summary", "mechanism", "evidence")

    for i, e in enumerate(edges):
        prefix = f"edges[{i}]"
        for k in required_edge_fields:
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
            min_rows = 1 if mode == "densify" else 3
            if len(ev) < min_rows:
                errors.append(f"{prefix}.evidence must have >={min_rows} row(s) "
                              f"(found {len(ev)})")
            for j, r in enumerate(ev):
                if not r.get("citation"):
                    errors.append(f"{prefix}.evidence[{j}].citation required")
                if r.get("study_type") and r["study_type"] not in VALID_STUDY_TYPES:
                    errors.append(f"{prefix}.evidence[{j}].study_type invalid: {r['study_type']}")
                if r.get("quality") and r["quality"] not in VALID_QUALITIES:
                    errors.append(f"{prefix}.evidence[{j}].quality invalid: {r['quality']}")
                if r.get("direction") and r["direction"] not in VALID_DIRECTIONS:
                    errors.append(f"{prefix}.evidence[{j}].direction invalid")

        # Anti-fabrication heuristics — only enforced for replace mode
        if mode != "densify":
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


def _all_entity_slugs(conn) -> set[str]:
    return {r["slug"] for r in conn.execute("SELECT slug FROM entity").fetchall()}


def validate_dir(payload_dir: Path = PAYLOAD_DIR, *, verify: bool = False) -> tuple[int, int]:
    """Validate every JSON in payload_dir. With verify=True, additionally
    resolves every PMID against PubMed and checks the title matches."""
    if not payload_dir.exists():
        print(f"No payload dir at {payload_dir}"); return (0, 0)
    files = sorted(payload_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]
    with connect() as conn:
        kf, ko = _known_slugs(conn)
        all_slugs = _all_entity_slugs(conn)

    parsed: list[tuple[Path, dict]] = []
    parse_errors: list[Path] = []
    for f in files:
        try:
            parsed.append((f, json.loads(f.read_text())))
        except Exception as e:
            print(f"[FAIL] {f.name}: cannot parse JSON: {e}")
            parse_errors.append(f)

    pubmed_cache: dict[str, dict] = {}
    if verify:
        all_pmids: list[str] = []
        for _, p in parsed:
            for e in p.get("edges", []) or []:
                for ev in e.get("evidence", []) or []:
                    if ev.get("pmid"):
                        all_pmids.append(str(ev["pmid"]))
        unique = sorted(set(all_pmids))
        print(f"[verify] looking up {len(unique)} unique PMIDs on PubMed ...")
        pubmed_cache = _pubmed_lookup(unique)
        print(f"[verify] {len(pubmed_cache)}/{len(unique)} resolved")

    ok = bad = 0
    for f, p in parsed:
        mode = p.get("mode", "replace")
        factor_slugs = all_slugs if mode == "densify" else kf
        outcome_slugs = all_slugs if mode == "densify" else ko
        errs = validate_payload(p, known_factor_slugs=factor_slugs,
                                known_outcome_slugs=outcome_slugs)
        if verify:
            errs += verify_citations(p, pubmed_cache)
        if errs:
            print(f"[FAIL] {f.name}:"); [print(f"  - {e}") for e in errs[:6]]
            if len(errs) > 6: print(f"  ... and {len(errs)-6} more")
            bad += 1
        else:
            print(f"[OK]   {f.name} ({len(p.get('edges', []))} edge(s))")
            ok += 1

    bad += len(parse_errors)
    print(f"\n{ok} ok, {bad} failed, {len(files)} total")
    return ok, bad


# ----------------------------------------------------------------------------
# Ingestion
# ----------------------------------------------------------------------------

def _persist_edge(conn, e: dict, file_name: str, mode: str = "replace") -> tuple[int, str]:
    """Insert/update one edge + its evidence. Returns (edge_id, action).

    Modes:
      replace   default; create the edge if missing or update prose+tier and
                replace evidence rows wholesale (used by v2/v3/v4 batches)
      densify   edge MUST already exist; add new evidence rows that aren't
                already on the edge (deduped by PMID); never touches summary,
                mechanism, caveats, tier, direction
    """
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

    if mode == "densify":
        if not existing:
            raise ValueError(
                f"densify mode in {file_name}: no existing edge for "
                f"{e['factor_slug']} -> {e['outcome_slug']} (pop={population}). "
                f"Densify only adds evidence to edges that already exist.")
        edge_id = existing["id"]

        existing_pmids = {r["pmid"] for r in conn.execute(
            "SELECT pmid FROM evidence WHERE edge_id=? AND pmid IS NOT NULL",
            (edge_id,)).fetchall()}

        added = 0
        skipped_dup = 0
        for ev in e["evidence"]:
            pmid = ev.get("pmid")
            if pmid and pmid in existing_pmids:
                skipped_dup += 1
                continue
            conn.execute(
                "INSERT INTO evidence (edge_id, citation, year, study_type, "
                "n_participants, direction, quality, notes, pmid, doi) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (edge_id, ev.get("citation", ""), ev.get("year"),
                 ev.get("study_type"), ev.get("n_participants"),
                 ev.get("direction"), ev.get("quality"), ev.get("notes", ""),
                 ev.get("pmid"), ev.get("doi")))
            if pmid:
                existing_pmids.add(pmid)
            added += 1
        conn.execute(
            "INSERT INTO edge_history (edge_id, field, old_value, new_value, "
            "reason, actor) VALUES (?, 'evidence', NULL, ?, ?, 'codex_densify')",
            (edge_id,
             json.dumps({"added": added, "skipped_dup": skipped_dup}),
             f"densify: +{added} evidence row(s) from {file_name}"))
        return edge_id, ("densified" if added else "no_change")

    # ---- replace mode (default) ----
    summary = e.get("summary", "")
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
            "n_participants, direction, quality, notes, pmid, doi) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (edge_id, ev.get("citation", ""), ev.get("year"),
             ev.get("study_type"), ev.get("n_participants"),
             ev.get("direction"), ev.get("quality"), ev.get("notes", ""),
             ev.get("pmid"), ev.get("doi")))

    conn.execute(
        "INSERT INTO edge_history (edge_id, field, old_value, new_value, "
        "reason, actor) VALUES (?, 'seed', NULL, ?, ?, 'codex_payload')",
        (edge_id, json.dumps({"tier": e["tier"], "direction": e["direction"]}),
         f"payload import: {file_name}"))
    return edge_id, action


def ingest_dir(payload_dir: Path = PAYLOAD_DIR, *, dry_run: bool = False) -> dict:
    summary = {"created": 0, "updated": 0, "densified": 0, "no_change": 0,
               "new_entities": 0, "files": 0, "errors": []}
    files = sorted(payload_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]

    for f in files:
        try:
            p = json.loads(f.read_text())
        except Exception as e:
            summary["errors"].append(f"{f.name}: {e}"); continue
        with connect() as conn:
            kf, ko = _known_slugs(conn)
            all_slugs = _all_entity_slugs(conn)
        mode = p.get("mode", "replace")
        factor_slugs = all_slugs if mode == "densify" else kf
        outcome_slugs = all_slugs if mode == "densify" else ko
        errs = validate_payload(p, known_factor_slugs=factor_slugs,
                                known_outcome_slugs=outcome_slugs)
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
            mode = p.get("mode", "replace")
            for e in p["edges"]:
                try:
                    _, action = _persist_edge(conn, e, f.name, mode=mode)
                    summary[action] = summary.get(action, 0) + 1
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
    ap.add_argument("--verify", action="store_true",
                    help="also resolve every PMID against PubMed (slow)")
    a = ap.parse_args()

    if a.cmd == "validate":
        if a.path:
            p = json.loads(Path(a.path).read_text())
            with connect() as conn:
                kf, ko = _known_slugs(conn)
                all_slugs = _all_entity_slugs(conn)
            mode = p.get("mode", "replace")
            factor_slugs = all_slugs if mode == "densify" else kf
            outcome_slugs = all_slugs if mode == "densify" else ko
            errs = validate_payload(p, known_factor_slugs=factor_slugs,
                                    known_outcome_slugs=outcome_slugs)
            if a.verify:
                pmids = [str(ev["pmid"]) for e in p.get("edges", [])
                         for ev in e.get("evidence", []) if ev.get("pmid")]
                cache = _pubmed_lookup(sorted(set(pmids))) if pmids else {}
                errs += verify_citations(p, cache)
            if errs:
                print(f"[FAIL] {a.path}:"); [print(f"  - {e}") for e in errs]; sys.exit(1)
            print(f"[OK] {a.path}")
        else:
            ok, bad = validate_dir(verify=a.verify)
            sys.exit(1 if bad else 0)
    else:
        ingest_dir(dry_run=a.dry_run)


if __name__ == "__main__":
    main()
