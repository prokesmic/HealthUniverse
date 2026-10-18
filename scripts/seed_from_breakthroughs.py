#!/usr/bin/env python3
"""Breakthrough cards → candidate edges (18.10.2026).

The weekly orphan brief (78 candidates) was a queue nobody cleared. Instead:
when a card's intervention AND condition both matched graph entities
(breakthrough_corpus.py) but the graph has no edge between them, look for
the edge's evidence on PubMed the same way deepen_edges.py does
(meta-analyses / systematic reviews / RCTs, model-judged relevance, effect
quotes checked against the abstract) and, if at least one synthesis or RCT
holds up, create the edge — tier from the deterministic rules, direction from
the judged rows, review_status 'unreviewed', every row with its PMID.

Deliberately narrow: only factors that already exist as graph entities.
The graph encodes "factor → risk of condition"; a new cancer drug linked to
"Pancreatic cancer" would read as prevention, so treatment-only drugs are not
seeded. The news card is the trigger, never the evidence.

  python scripts/seed_from_breakthroughs.py --dry
  python scripts/seed_from_breakthroughs.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import deepen_edges as de  # noqa: E402
from web.breakthroughs import load_feed, save_feed  # noqa: E402


def _connect():
    from db import connect  # type: ignore
    return connect()


def candidates_from_feed(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        c = it.get("corpus") or {}
        if c.get("factor") and c.get("outcome") and not c.get("pair") \
                and not (it.get("detail") or {}).get("no_results") and not it.get("seeded_edge"):
            out.append(it)
    return out


def seed(conn, item: dict, dry: bool = False) -> dict:
    c = item["corpus"]
    f = conn.execute("SELECT id, name FROM entity WHERE slug=?", (c["factor"]["slug"],)).fetchone()
    o = conn.execute("SELECT id, name, kind FROM entity WHERE slug=?", (c["outcome"]["slug"],)).fetchone()
    res = {"card": item["id"], "pair": f"{f['name']} → {o['name']}", "edge": None, "rows": 0}
    if conn.execute("SELECT 1 FROM edge WHERE factor_id=? AND outcome_id=?", (f["id"], o["id"])).fetchone():
        res["why"] = "edge already exists"
        return res
    judged = []
    risk = de.risk_question(o["kind"], "general adult")
    for cand in de.candidates(f["name"], o["name"], set(), risk=risk):
        j = de.judge(f["name"], o["name"], cand, risk=risk)
        if j:
            judged.append((cand, j))
    # A new edge needs a synthesis that takes a side and quotes its estimate —
    # one neutral review of "exercise to help quit vaping" seeded vaping → quitting on 18.10.
    strong = [x for x in judged if x[1]["study_type"] in ("meta_analysis", "systematic_review")
              and x[1]["direction"] in ("protective", "harmful") and x[1]["effect"]]
    if not strong:
        res["why"] = "no synthesis with a direction and a quoted estimate held up on PubMed"
        return res
    dirs = Counter(j["direction"] for _, j in judged if j["direction"])
    direction = dirs.most_common(1)[0][0] if dirs else "mixed"
    rows = [{"study_type": j["study_type"], "quality": j["quality"], "n_participants": j["n"],
             "direction": j["direction"], "is_counter": 0} for _, j in judged]
    tier, score, note = de.rule_tier(rows, direction)
    best = next((j["effect"] for _, j in judged if j["effect"] and j["direction"] == direction), "")
    res.update({"rows": len(judged), "tier": tier, "direction": direction})
    if dry:
        return res
    cur = conn.execute("""INSERT INTO edge (factor_id, outcome_id, direction, tier, effect_quant, population,
                            summary, seed_source, review_status)
                          VALUES (?,?,?,?,?,?,?, 'gemma_daily', 'unreviewed')""",
                       (f["id"], o["id"], direction, tier, best or None, "general adult",
                        f"Seeded from the news item “{item['headline'][:120]}” and backed by "
                        f"{len(judged)} PubMed {'study' if len(judged) == 1 else 'studies'} "
                        f"({', '.join(sorted({j['study_type'].replace('_', ' ') for _, j in judged}))})."))
    eid = cur.lastrowid
    for cand, j in judged:
        conn.execute("""INSERT INTO evidence (edge_id, citation, url, pmid, year, study_type, n_participants,
                          direction, quality, notes, real_title, relevance_status, is_counter)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?, 'verified', ?)""",
                     (eid, de.citation(cand), f"https://pubmed.ncbi.nlm.nih.gov/{cand['pmid']}/", cand["pmid"],
                      int(cand["year"]) if str(cand.get("year", "")).isdigit() else None, j["study_type"], j["n"],
                      j["direction"], j["quality"], j["effect"] or None, cand["title"],
                      1 if j["direction"] in ("protective", "harmful") and direction in ("protective", "harmful")
                      and j["direction"] != direction else 0))
    conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                    VALUES (?, 'created', NULL, ?, ?, 'seed_from_breakthroughs')""",
                 (eid, tier, f"news card {item['id']} named both ends; {note} (score {score:g}) "
                             f"from {len(judged)} PubMed rows"))
    conn.commit()
    res["edge"] = eid
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    items = load_feed().get("items", [])
    todo = candidates_from_feed(items)
    print(f"→ {len(todo)} cards name two graph entities with no edge between them")
    made = {}
    with _connect() as conn:
        for it in todo:
            r = seed(conn, it, dry=a.dry)
            print(f"  {r['pair']}: {('edge #' + str(r['edge']) + ' ' + r.get('tier', '')) if r['edge'] else r.get('why', r)}"
                  f" ({r['rows']} rows)")
            if r["edge"]:
                made[it["id"]] = r["edge"]
    if made and not a.dry:
        feed = load_feed()
        for i in feed["items"]:
            if i["id"] in made:
                i["seeded_edge"] = made[i["id"]]
                i["edge_id"] = made[i["id"]]
                i["is_orphan"] = False
        save_feed(feed)
    print({"seeded": len(made)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
