#!/usr/bin/env python3
"""Merge duplicate entities (18.10.2026).

40 groups of entities shared one normalized name (lowercase, parentheses and
non-alphanumerics stripped): cvd / cardiovascular_disease, t2d /
type_2_diabetes, aspirin_low / aspirin_low_dose / low_dose_aspirin … Each
half held part of the evidence, so a page or a VitalShield view that asked
for one slug saw only some of the edges.

Every group was reviewed by hand. MERGES lists the canonical slug first —
the one with the most edges, unless a clearer slug won a near-tie — and the
reason. KEEP_APART lists the groups that only look alike (osteoporosis vs
postmenopausal osteoporosis is a narrower population, not a synonym).

For each merged-away entity:
  * its edges are repointed to the canonical entity, one edge_history row
    per edge (field factor_id/outcome_id, old → new slug);
  * an edge that collides with an existing one on (factor, outcome,
    population) is folded into it right away (merge_duplicate_edges.merge_into);
  * its slug and name join the canonical entity's aliases;
  * entity_redirect(old_slug → new_slug) keeps every lookup by the old slug
    working (db.resolve_slug, /api/entities/<old> 301s), and the row is
    deleted so lists and counts show the entity once;
  * seed_topic and product rows follow it.
Then merge_duplicate_edges.merge_all folds pairs that became duplicates
(writing edge_redirect so /edge/<old> 301s), and data/breakthroughs.json
corpus slugs are rewritten through the same mapping.

  python scripts/merge_duplicate_entities.py --dry
  python scripts/merge_duplicate_entities.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

ACTOR = "merge_entities"
WHEN = "2026-10-18"
BX = ROOT / "data" / "breakthroughs.json"

# (canonical, [merged away], reason)
MERGES: list[tuple[str, list[str], str]] = [
    ("acupuncture_ivf", ["ivf_acupuncture"], "same intervention, word order"),
    ("amd", ["age_related_macular_degeneration"], "abbreviation; amd holds 10 of 11 edges"),
    ("blood_pressure_control", ["bp_control"], "abbreviation"),
    ("bone_density", ["bone_mineral_density"], "same measure (BMD); bone_density used by conditional_harms and breakthroughs"),
    ("cvd", ["cardiovascular_disease"], "abbreviation; cvd holds 126 edges and is hard-coded in categories"),
    ("cardiovascular_events", ["cv_events"], "abbreviation"),
    ("cardiovascular_outcomes", ["cv_outcomes"], "abbreviation (cv_outcomes was mis-kinded as process)"),
    ("childhood_obesity", ["child_obesity"], "same condition"),
    ("vegetables_cruciferous", ["cruciferous_vegetables"], "same food, word order; VitalShield mapped both"),
    ("flossing", ["flossing_daily"], "both named Daily flossing"),
    ("polyphenols", ["dietary_polyphenols"], "both named Dietary polyphenols; VitalShield mapped both"),
    ("digital_eye_strain", ["eye_strain"], "both named Digital eye strain; the longer slug says what it is"),
    ("prebiotic_galactooligosaccharides", ["gos_prebiotic"], "same prebiotic (GOS)"),
    ("gut_microbiome_diversity", ["gut_microbiome", "microbiome_diversity"], "all three named Gut microbiome diversity"),
    ("hearing_aids", ["hearing_aid_use"], "same exposure"),
    ("inflammatory_bowel_disease", ["ibd"], "abbreviation"),
    ("l_reuteri_dsm17938", ["lactobacillus_reuteri_dsm17938"], "same strain"),
    ("l_rhamnosus_gg", ["lactobacillus_rhamnosus_gg"], "same strain"),
    ("ldl_cholesterol", ["ldl_c"], "abbreviation; VitalShield lab_predictions lists ldl_cholesterol first"),
    ("letrozole_anovulatory_pcos", ["letrozole_anovulatory"], "same indication; the longer slug names it"),
    ("aspirin_low_dose", ["aspirin_low", "low_dose_aspirin"], "same drug and dose; interactions.json uses aspirin_low_dose"),
    ("mace", ["major_adverse_cv_events"], "abbreviation"),
    ("maternal_smoking_pregnancy", ["maternal_smoking_in_pregnancy"], "same exposure"),
    ("nac", ["n_acetylcysteine"], "abbreviation"),
    ("organophosphates", ["organophosphate_pesticides"], "both named Organophosphate pesticide exposure"),
    ("polypharmacy", ["polypharmacy_5plus"], "polypharmacy is defined as 5 or more medications"),
    ("proton_pump_inhibitors", ["ppi"], "abbreviation; PPI edges are about long-term use"),
    ("restless_legs_syndrome", ["restless_legs"], "same condition"),
    ("saccharomyces_boulardii", ["s_boulardii"], "same probiotic yeast"),
    ("ssri_with_st_johns_wort", ["ssri_with_st_john_s_wort"], "same interaction, apostrophe artefact"),
    ("strong_cyp3a4_inhibitor_with_statin", ["cyp3a4_strong_inhibitor_with_statin"], "same interaction, word order"),
    ("tart_cherry", ["cherry_juice_tart"], "both named Tart cherry supplementation"),
    ("tretinoin", ["topical_tretinoin"], "both named Topical tretinoin"),
    ("travelers_diarrhea", ["travelers_diarrhoea"], "spelling variant"),
    ("t2d", ["type_2_diabetes"], "abbreviation; t2d holds 69 edges and is hard-coded in categories"),
    ("vo2_max", ["vo2max"], "spelling variant"),
]

# Same normalized name, different thing — left separate on purpose.
KEEP_APART: dict[frozenset, str] = {
    frozenset({"atopic_dermatitis", "atopic_dermatitis_children"}): "children are a distinct population",
    frozenset({"cognitive_function", "cognitive_function_iron_deplete", "cognitive_function_older"}):
        "iron-deplete and older-adult subpopulations",
    frozenset({"osteoporosis", "osteoporosis_postmenopausal"}): "postmenopausal osteoporosis is a narrower population",
    frozenset({"quality_of_life", "quality_of_life_chronic_anemia"}): "QoL in chronic anaemia is disease-specific",
}


def norm(name: str) -> str:
    s = re.sub(r"\([^)]*\)", "", (name or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def name_groups(conn) -> list[set[str]]:
    """Sets of live slugs whose entity names normalize identically."""
    g = defaultdict(set)
    for slug, name in conn.execute("SELECT slug, name FROM entity"):
        g[norm(name)].add(slug)
    return [v for v in g.values() if len(v) > 1]


def mapping() -> dict[str, str]:
    return {old: canon for canon, olds, _ in MERGES for old in olds}


def _connect():
    from db import connect  # type: ignore
    return connect()


def ensure_schema(conn) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS entity_redirect (
                      old_slug TEXT PRIMARY KEY, new_slug TEXT NOT NULL,
                      old_id INTEGER, new_id INTEGER, old_name TEXT, reason TEXT,
                      created_at TEXT NOT NULL DEFAULT (datetime('now')))""")


def _hist(conn, edge_id, field, old, new, reason):
    conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                    VALUES (?, ?, ?, ?, ?, ?)""", (edge_id, field, old, new, reason, ACTOR))


def merge_entity(conn, canon: str, old: str, reason: str) -> dict:
    from merge_duplicate_edges import RANK, merge_into  # type: ignore
    keep = conn.execute("SELECT * FROM entity WHERE slug=?", (canon,)).fetchone()
    drop = conn.execute("SELECT * FROM entity WHERE slug=?", (old,)).fetchone()
    if not keep:
        raise SystemExit(f"canonical entity missing: {canon}")
    if not drop:
        return {"old": old, "skipped": "already merged"}
    why = f"entity {old} merged into {canon} ({reason})"
    out = {"old": old, "new": canon, "repointed": 0, "folded": 0, "self_loops": 0}
    for col, other in (("factor_id", "outcome_id"), ("outcome_id", "factor_id")):
        for e in conn.execute(f"SELECT * FROM edge WHERE {col}=?", (drop["id"],)).fetchall():
            f_id = keep["id"] if col == "factor_id" else e["factor_id"]
            o_id = keep["id"] if col == "outcome_id" else e["outcome_id"]
            if f_id == o_id:
                # Both ends in the same merge group: a loop says nothing.
                _hist(conn, e["id"], col, old, canon, why)
                _hist(conn, e["id"], "tier", e["tier"], "deprecated", why + "; edge became a self-loop")
                conn.execute(f"UPDATE edge SET {col}=?, tier='deprecated', updated_at=datetime('now') "
                             "WHERE id=?", (keep["id"], e["id"]))
                out["self_loops"] += 1
                continue
            clash = conn.execute("""SELECT e.id, e.tier, e.population,
                                           (SELECT COUNT(*) FROM evidence v WHERE v.edge_id=e.id) n
                                      FROM edge e WHERE factor_id=? AND outcome_id=?
                                       AND population IS ? AND id != ?""",
                                 (f_id, o_id, e["population"], e["id"])).fetchone()
            if clash:
                out["folded"] += 1
                rr = f"entity {old} merged into {canon} {WHEN}"
                n_e = conn.execute("SELECT COUNT(*) FROM evidence WHERE edge_id=?", (e["id"],)).fetchone()[0]
                if (-RANK.get(e["tier"], 0), -n_e, e["id"]) > (-RANK.get(clash["tier"], 0), -clash["n"], clash["id"]):
                    merge_into(conn, clash, e, reason=f"{why}; same pair and population as this edge",
                               redirect_reason=rr)
                    continue
                # The moving edge is the stronger one: it absorbs the clash, then moves.
                merge_into(conn, e, clash, reason=f"{why}; same pair and population as this edge",
                           redirect_reason=rr)
            conn.execute(f"UPDATE edge SET {col}=?, updated_at=datetime('now') WHERE id=?",
                         (keep["id"], e["id"]))
            _hist(conn, e["id"], col, old, canon, why)
            out["repointed"] += 1
    aliases = json.loads(keep["aliases"] or "[]") + json.loads(drop["aliases"] or "[]")
    for a in (old, drop["name"]):
        if a and a != keep["name"]:
            aliases.append(a)
    seen, merged = set(), []
    for a in aliases:
        if a and a != canon and a.lower() not in seen:
            seen.add(a.lower())
            merged.append(a)
    desc = keep["description"] or drop["description"]
    conn.execute("UPDATE entity SET aliases=?, description=?, updated_at=datetime('now') WHERE id=?",
                 (json.dumps(merged), desc, keep["id"]))
    conn.execute("""INSERT OR REPLACE INTO entity_redirect (old_slug, new_slug, old_id, new_id, old_name, reason)
                    VALUES (?,?,?,?,?,?)""", (old, canon, drop["id"], keep["id"], drop["name"], reason))
    conn.execute("UPDATE entity_redirect SET new_slug=?, new_id=? WHERE new_slug=?", (canon, keep["id"], old))
    for col in ("factor_slug", "outcome_slug"):
        conn.execute(f"UPDATE OR IGNORE seed_topic SET {col}=? WHERE {col}=?", (canon, old))
        # A queue row left behind duplicates one the canonical slug already has.
        conn.execute(f"DELETE FROM seed_topic WHERE {col}=?", (old,))
    conn.execute("UPDATE product SET entity_slug=? WHERE entity_slug=?", (canon, old))
    conn.execute("DELETE FROM entity WHERE id=?", (drop["id"],))
    return out


def rewrite_breakthroughs(m: dict[str, str], path: Path = BX, dry: bool = False,
                          edge_redirects: dict[int, int] | None = None) -> int:
    """Point breakthrough cards' corpus.factor/outcome at canonical slugs and
    their listed edges at the edge each one was folded into (no duplicates)."""
    if not path.exists():
        return 0
    data = json.loads(path.read_text())
    n = 0
    red = edge_redirects or {}
    for it in data.get("items", []):
        c = it.get("corpus") or {}
        for k in ("pair", "outcome_edges", "factor_edges"):
            if not isinstance(c.get(k), list):
                continue
            ids = lambda e: e.get("id") if isinstance(e, dict) else None
            have = {ids(e) for e in c[k] if ids(e) not in red}
            keep = []
            for e in c[k]:
                if ids(e) in red:
                    n += 1
                    if red[ids(e)] in have:
                        continue  # the surviving edge is already listed with its own text
                    e["id"] = red[ids(e)]
                    have.add(e["id"])
                keep.append(e)
            c[k] = keep
        if it.get("seeded_edge") in red:
            it["seeded_edge"] = red[it["seeded_edge"]]
            n += 1
        for k in ("factor", "outcome"):
            ent = c.get(k)
            if isinstance(ent, dict) and ent.get("slug") in m:
                ent["slug"] = m[ent["slug"]]
                n += 1
        for k in ("factor_slug", "outcome_slug"):
            if it.get(k) in m:
                it[k] = m[it[k]]
                n += 1
    if n and not dry:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2))  # same format as web/breakthroughs.py
        tmp.replace(path)
    return n


def run(conn, dry: bool = False, bx_path: Path = BX) -> dict:
    from merge_duplicate_edges import merge_all  # type: ignore
    ensure_schema(conn)
    results = [merge_entity(conn, canon, old, reason)
               for canon, olds, reason in MERGES for old in olds]
    edges = merge_all(conn)
    m = mapping()
    left = [sorted(g) for g in name_groups(conn) if frozenset(g) not in KEEP_APART]
    summary = {"entities_merged": sum(1 for r in results if "new" in r),
               "edges_repointed": sum(r.get("repointed", 0) for r in results),
               "edges_folded": sum(r.get("folded", 0) for r in results),
               "self_loops_deprecated": sum(r.get("self_loops", 0) for r in results),
               "pair_merge": edges, "groups_left": left}
    red = dict(conn.execute("SELECT old_id, new_id FROM edge_redirect").fetchall())
    if dry:
        conn.rollback()
    summary["breakthrough_refs_rewritten"] = rewrite_breakthroughs(m, bx_path, dry, red)
    return summary


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    with _connect() as conn:
        out = run(conn, a.dry)
        if not a.dry:
            conn.commit()
    print(json.dumps(out, indent=1))
    return 1 if out["groups_left"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
