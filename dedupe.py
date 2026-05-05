"""Find and merge near-duplicate entities and edges using embeddings.

Two failure modes this catches:

  1. Entity-level: two entity slugs that mean the same thing
     (e.g. `coffee_low` vs `coffee_low_intake`) — we want to merge so
     evidence and edges aren't fragmented across both.
  2. Edge-level: two `(factor, outcome)` edges where the outcomes are
     semantically equivalent (e.g. `apple → cvd` and `apple → cardiovascular_disease`).

Usage:
    python dedupe.py embed                # backfill embeddings (run first)
    python dedupe.py scan                 # find candidates, no writes
    python dedupe.py scan --threshold 0.92
    python dedupe.py merge --kind entity --keep coffee --drop coffee_low_intake
    python dedupe.py merge --kind edge   --keep 14 --drop 312
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                                # noqa: E402
from embeddings import EmbeddingsUnavailable, cosine, embed, pack, unpack  # noqa: E402

# Default similarity threshold for "almost certainly the same thing"
THRESHOLD = 0.92


# ---------------------------------------------------------------------------
# Backfill embeddings
# ---------------------------------------------------------------------------

_KIND_CONTEXT = {
    "food":          "a food or dietary input studied for its effect on chronic disease risk",
    "nutrient":      "a nutrient studied for its effect on chronic disease risk",
    "supplement":    "a dietary supplement studied for its effect on chronic disease risk",
    "drug":          "a pharmaceutical drug studied for its effect on chronic disease risk and as an exposure",
    "activity":      "a physical activity or behaviour studied for its effect on chronic disease risk",
    "behavior":      "a behavioural pattern studied for its effect on chronic disease risk",
    "environmental": "an environmental exposure or hazard studied for its effect on chronic disease risk",
    "pathogen":      "a pathogen, infectious organism, or microbial factor",
    "gene":          "a genetic variant or polymorphism modulating risk",
    "biomarker":     "a measurable biomarker, lab value, or physiological metric",
    "condition":     "a clinical condition or chronic disease as an outcome",
    "process":       "a biological or physiological process as an outcome",
}


def _entity_text(row) -> str:
    """Build embedding input text. Includes the slug AND name (slug helps
    differentiate; nomic-embed-text collapses some bare 'X disease' phrases
    to identical vectors), plus aliases and any free-text description."""
    aliases = ""
    try:
        a = json.loads(row["aliases"] or "[]")
        if a: aliases = " (also: " + ", ".join(a) + ")"
    except Exception: pass
    context = _KIND_CONTEXT.get(row["kind"], row["kind"])
    desc = (": " + row["description"]) if row["description"] else ""
    return (f"{row['slug']}: {row['name']}{desc}{aliases}. "
            f"Health-knowledge entity ({row['kind']}); {context}.")


def _edge_text(row) -> str:
    return (f"{row['f_name']} -> {row['o_name']}: "
            f"{row['summary'] or ''} "
            f"({row['direction']} | tier {row['tier']})")


def embed_all(limit: int = 9999, only_missing: bool = True) -> dict:
    """Embed entities + edges that don't yet have an embedding. Idempotent."""
    counts = {"entities": 0, "edges": 0, "errors": 0}
    with connect() as conn:
        ents = conn.execute(
            "SELECT id, name, kind, aliases, description, embedding "
            "FROM entity WHERE ? OR embedding IS NULL LIMIT ?",
            (0 if only_missing else 1, limit)).fetchall()
        ents = [r for r in ents if not r["embedding"]] if only_missing else list(ents)
    print(f"[embed] {len(ents)} entities to embed")
    for r in ents:
        try:
            v = embed(_entity_text(r))
            with connect() as conn:
                conn.execute(
                    "UPDATE entity SET embedding=?, embedded_at=datetime('now') "
                    "WHERE id=?", (pack(v), r["id"]))
            counts["entities"] += 1
        except EmbeddingsUnavailable as e:
            print(f"  STOP: {e}"); return counts
        except Exception as e:
            print(f"  fail entity {r['id']}: {e}"); counts["errors"] += 1
        if counts["entities"] % 25 == 0 and counts["entities"]:
            print(f"  ... {counts['entities']}/{len(ents)} entities")

    with connect() as conn:
        edges = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.embedding,
                   f.name AS f_name, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE ? OR e.embedding IS NULL LIMIT ?""",
            (0 if only_missing else 1, limit)).fetchall()
        edges = [r for r in edges if not r["embedding"]] if only_missing else list(edges)
    print(f"[embed] {len(edges)} edges to embed")
    for r in edges:
        try:
            v = embed(_edge_text(r))
            with connect() as conn:
                conn.execute(
                    "UPDATE edge SET embedding=?, embedded_at=datetime('now') "
                    "WHERE id=?", (pack(v), r["id"]))
            counts["edges"] += 1
        except EmbeddingsUnavailable as e:
            print(f"  STOP: {e}"); return counts
        except Exception as e:
            print(f"  fail edge {r['id']}: {e}"); counts["errors"] += 1
        if counts["edges"] % 25 == 0 and counts["edges"]:
            print(f"  ... {counts['edges']}/{len(edges)} edges")
    print(f"[embed] done: {counts}")
    return counts


# ---------------------------------------------------------------------------
# Scan for near-duplicates
# ---------------------------------------------------------------------------

def scan(threshold: float = THRESHOLD) -> dict:
    """Pairwise compare embeddings within entity (by kind) and within edge.
    O(n²) but n is small (hundreds, not millions). Fine for our scale."""
    out: dict = {"entity_pairs": [], "edge_pairs": []}
    with connect() as conn:
        ents = conn.execute("""
            SELECT id, slug, name, kind, embedding,
                   (SELECT COUNT(*) FROM edge WHERE factor_id=entity.id OR outcome_id=entity.id) AS edge_count
            FROM entity WHERE embedding IS NOT NULL""").fetchall()
        edges = conn.execute("""
            SELECT e.id, e.tier, e.embedding,
                   f.id AS f_id, f.slug AS f_slug, f.kind AS f_kind,
                   o.id AS o_id, o.slug AS o_slug, o.kind AS o_kind
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.embedding IS NOT NULL""").fetchall()

    # Entity pairs — only compare within same kind (food vs food, not food vs gene)
    by_kind: dict[str, list] = {}
    for r in ents:
        by_kind.setdefault(r["kind"], []).append(r)
    for kind, rows in by_kind.items():
        vecs = [(r, unpack(r["embedding"])) for r in rows]
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                sim = cosine(vecs[i][1], vecs[j][1])
                if sim >= threshold:
                    a, b = vecs[i][0], vecs[j][0]
                    # keep the one with more edges
                    keep, drop = (a, b) if a["edge_count"] >= b["edge_count"] else (b, a)
                    out["entity_pairs"].append({
                        "kind": kind, "sim": round(sim, 4),
                        "keep_slug": keep["slug"], "keep_id": keep["id"],
                        "drop_slug": drop["slug"], "drop_id": drop["id"],
                        "keep_edges": keep["edge_count"], "drop_edges": drop["edge_count"],
                    })

    # Edge pairs — same factor (or same factor entity), same outcome kind, similar embedding
    # We only flag edges where (factor matches OR factors are themselves duplicates)
    # Simpler initial pass: same factor entity, similar embedding => likely outcome dupe.
    by_factor: dict[int, list] = {}
    for r in edges:
        by_factor.setdefault(r["f_id"], []).append(r)
    for fid, rows in by_factor.items():
        if len(rows) < 2:
            continue
        vecs = [(r, unpack(r["embedding"])) for r in rows]
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                if vecs[i][0]["o_id"] == vecs[j][0]["o_id"]:
                    continue  # same edge logically
                sim = cosine(vecs[i][1], vecs[j][1])
                if sim >= threshold:
                    out["edge_pairs"].append({
                        "sim": round(sim, 4),
                        "edge_a": vecs[i][0]["id"], "edge_b": vecs[j][0]["id"],
                        "factor": vecs[i][0]["f_slug"],
                        "outcome_a": vecs[i][0]["o_slug"],
                        "outcome_b": vecs[j][0]["o_slug"],
                    })

    out["entity_pairs"].sort(key=lambda x: -x["sim"])
    out["edge_pairs"].sort(key=lambda x: -x["sim"])

    print(f"[scan] threshold={threshold}")
    print(f"  entity-level near-dupes: {len(out['entity_pairs'])}")
    for p in out["entity_pairs"][:30]:
        print(f"    {p['sim']}  {p['kind']:12s}  KEEP {p['keep_slug']:35s} ({p['keep_edges']} edges)  "
              f"DROP {p['drop_slug']:35s} ({p['drop_edges']} edges)")
    print(f"  edge-level outcome-dupes: {len(out['edge_pairs'])}")
    for p in out["edge_pairs"][:30]:
        print(f"    {p['sim']}  factor={p['factor']:25s}  {p['outcome_a']:25s}  ~  {p['outcome_b']}")
    return out


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_entity(keep_slug: str, drop_slug: str, *, dry_run: bool = False) -> dict:
    """Re-point everything from drop onto keep, then delete drop."""
    with connect() as conn:
        keep = conn.execute("SELECT * FROM entity WHERE slug=?", (keep_slug,)).fetchone()
        drop = conn.execute("SELECT * FROM entity WHERE slug=?", (drop_slug,)).fetchone()
        if not keep or not drop:
            raise SystemExit(f"unknown slug: {keep_slug if not keep else drop_slug}")
        if keep["id"] == drop["id"]:
            raise SystemExit("keep == drop, nothing to merge")

        # Find edges that would conflict (same other-side entity & population)
        # We'll fold those into the keep edge instead of duplicating.
        as_factor = conn.execute("SELECT id, outcome_id, population FROM edge WHERE factor_id=?", (drop["id"],)).fetchall()
        as_outcome = conn.execute("SELECT id, factor_id, population FROM edge WHERE outcome_id=?", (drop["id"],)).fetchall()
        log: list[str] = []
        if not dry_run:
            for r in as_factor:
                existing = conn.execute(
                    "SELECT id FROM edge WHERE factor_id=? AND outcome_id=? AND population=?",
                    (keep["id"], r["outcome_id"], r["population"])).fetchone()
                if existing:
                    # fold evidence + history into existing, then delete the dup edge
                    conn.execute("UPDATE evidence SET edge_id=? WHERE edge_id=?", (existing["id"], r["id"]))
                    conn.execute("UPDATE edge_history SET edge_id=? WHERE edge_id=?", (existing["id"], r["id"]))
                    conn.execute("DELETE FROM edge WHERE id=?", (r["id"],))
                    log.append(f"folded edge#{r['id']} into edge#{existing['id']}")
                else:
                    conn.execute("UPDATE edge SET factor_id=? WHERE id=?", (keep["id"], r["id"]))
                    log.append(f"repointed edge#{r['id']} factor -> {keep_slug}")
            for r in as_outcome:
                existing = conn.execute(
                    "SELECT id FROM edge WHERE factor_id=? AND outcome_id=? AND population=?",
                    (r["factor_id"], keep["id"], r["population"])).fetchone()
                if existing:
                    conn.execute("UPDATE evidence SET edge_id=? WHERE edge_id=?", (existing["id"], r["id"]))
                    conn.execute("UPDATE edge_history SET edge_id=? WHERE edge_id=?", (existing["id"], r["id"]))
                    conn.execute("DELETE FROM edge WHERE id=?", (r["id"],))
                    log.append(f"folded edge#{r['id']} into edge#{existing['id']}")
                else:
                    conn.execute("UPDATE edge SET outcome_id=? WHERE id=?", (keep["id"], r["id"]))
                    log.append(f"repointed edge#{r['id']} outcome -> {keep_slug}")

            # Carry aliases forward
            keep_aliases = json.loads(keep["aliases"] or "[]")
            drop_aliases = json.loads(drop["aliases"] or "[]")
            merged = sorted(set(keep_aliases + drop_aliases + [drop["name"], drop_slug]))
            conn.execute("UPDATE entity SET aliases=? WHERE id=?",
                         (json.dumps(merged), keep["id"]))
            conn.execute("DELETE FROM entity WHERE id=?", (drop["id"],))
            conn.execute(
                "INSERT INTO seed_topic (factor_slug, outcome_slug, status, error) "
                "SELECT factor_slug, outcome_slug, 'merged', 'merged into "+keep_slug+"' "
                "FROM seed_topic WHERE factor_slug=? OR outcome_slug=?",
                (drop_slug, drop_slug))
        else:
            log.append(f"[dry-run] would re-point {len(as_factor)} factor edges and "
                       f"{len(as_outcome)} outcome edges, then delete {drop_slug}")
    return {"keep": keep_slug, "drop": drop_slug, "ops": len(log), "log": log}


def merge_edge(keep_id: int, drop_id: int, *, dry_run: bool = False) -> dict:
    """Fold drop's evidence into keep, delete drop."""
    with connect() as conn:
        keep = conn.execute("SELECT * FROM edge WHERE id=?", (keep_id,)).fetchone()
        drop = conn.execute("SELECT * FROM edge WHERE id=?", (drop_id,)).fetchone()
        if not keep or not drop:
            raise SystemExit("unknown id")
        if dry_run:
            n = conn.execute("SELECT COUNT(*) c FROM evidence WHERE edge_id=?", (drop_id,)).fetchone()["c"]
            return {"keep": keep_id, "drop": drop_id, "would_move_evidence": n}
        conn.execute("UPDATE evidence SET edge_id=? WHERE edge_id=?", (keep_id, drop_id))
        conn.execute("UPDATE edge_history SET edge_id=? WHERE edge_id=?", (keep_id, drop_id))
        conn.execute("DELETE FROM edge WHERE id=?", (drop_id,))
        conn.execute("INSERT INTO edge_history (edge_id, field, old_value, new_value, "
                     "reason, actor) VALUES (?, 'merged', ?, NULL, "
                     "'merged duplicate edge', 'dedupe')",
                     (keep_id, str(drop_id)))
    return {"keep": keep_id, "drop": drop_id, "merged": True}


# ---------------------------------------------------------------------------
# Auto-fold helper for the daily ingest
# ---------------------------------------------------------------------------

def find_near_edge(factor_id: int, outcome_id: int, summary_text: str,
                   threshold: float = 0.93) -> int | None:
    """Used by daily.py: before creating a new edge for (factor_id, X), check
    if a near-duplicate edge already exists with the same factor and a
    semantically equivalent outcome. Returns the existing edge_id if so."""
    if not summary_text:
        return None
    try:
        v = embed(summary_text)
    except EmbeddingsUnavailable:
        return None
    if not v:
        return None
    with connect() as conn:
        rows = conn.execute("""
            SELECT id, embedding FROM edge
            WHERE factor_id = ? AND outcome_id != ?
              AND embedding IS NOT NULL""",
            (factor_id, outcome_id)).fetchall()
    best_id, best_sim = None, 0.0
    for r in rows:
        sim = cosine(v, unpack(r["embedding"]))
        if sim > best_sim:
            best_sim, best_id = sim, r["id"]
    return best_id if best_sim >= threshold else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("embed")
    sp = sub.add_parser("scan")
    sp.add_argument("--threshold", type=float, default=THRESHOLD)
    sp.add_argument("--json", action="store_true")
    sm = sub.add_parser("merge")
    sm.add_argument("--kind", choices=("entity", "edge"), required=True)
    sm.add_argument("--keep", required=True)
    sm.add_argument("--drop", required=True)
    sm.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.cmd == "embed":
        embed_all()
    elif a.cmd == "scan":
        out = scan(threshold=a.threshold)
        if a.json:
            print(json.dumps(out, indent=2))
    elif a.cmd == "merge":
        if a.kind == "entity":
            print(merge_entity(a.keep, a.drop, dry_run=a.dry_run))
        else:
            print(merge_edge(int(a.keep), int(a.drop), dry_run=a.dry_run))


if __name__ == "__main__":
    main()
