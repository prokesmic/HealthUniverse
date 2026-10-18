#!/usr/bin/env python3
"""Link breakthrough cards to the edge graph (18.10.2026).

Every card was an "orphan": match_corpus() only matched when the model's
invented slugs (e.g. "pancreatic_cancer_drug") were byte-identical to an
entity slug, which never happened — 79 of 79. The graph has 1,757 entities
and 5,428 graded edges; most are risk factors (diet, behaviour, exposures),
while most cards are treatments, so the useful link is usually the
condition ("what else our graph says about pancreatic cancer") and, when it
exists, the intervention (intravenous iron, SGLT2 inhibitors…).

  1. Candidates: local embeddings (Ollama bge-m3) of entity name + aliases,
     cosine against the card's intervention / condition / headline.
  2. Confirmation: the local model picks the entity that is the same concept
     or its direct class, or none. A slug outside the candidate list is ignored.
  3. Edges: the exact factor→outcome edge if it exists, then the strongest
     edges for the condition and for the intervention (tier, review status).

The result is stored on the card as `corpus` (Vercel is read-only, so this
is computed here, not per request). Entity vectors are cached in
data/cache/entity_emb.json (gitignored), keyed by the embedded text.

Usage:
  python scripts/breakthrough_corpus.py --all
  python scripts/breakthrough_corpus.py --id br_xxx --dry
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from web.breakthroughs import load_feed, save_feed  # noqa: E402
from breakthrough_enrich import ollama_json  # noqa: E402

OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("BX_EMBED_MODEL", "bge-m3")
CACHE = ROOT / "data" / "cache" / "entity_emb.json"
OUTCOME_KINDS = {"condition", "biomarker", "process"}
TIER_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "X": 4}
REVIEW_ORDER = {"verified_evidence": 0, "weak_evidence": 1, "unreviewed": 2, "needs_recheck": 3}
MIN_COS = 0.45      # candidate shortlist
OUTCOME_COS = 0.68  # outcome texts are longer ("adults with anaemia undergoing cardiac surgery")
PICK_COS = 0.65     # a confirmed match must also be this close (18.10: "ACE inhibitors"
                    # for rivaroxaban scored 0.34; real matches scored 0.65-0.98)


def _connect():
    from db import connect  # type: ignore
    return connect()


def embed(texts: list[str]) -> list[list[float]]:
    req = urllib.request.Request(f"{OLLAMA}/api/embed",
                                 data=json.dumps({"model": EMBED_MODEL, "input": texts}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["embeddings"]


def _norm(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _text(e: dict) -> str:
    al = ", ".join(e["aliases"]) if e["aliases"] else ""
    return f"{e['name']}" + (f" ({al})" if al else "")


def entities() -> list[dict]:
    """All entities with a unit vector each (cached by text + model)."""
    with _connect() as conn:
        rows = conn.execute("SELECT id, slug, name, kind, aliases FROM entity").fetchall()
    ents = []
    for r in rows:
        try:
            al = json.loads(r["aliases"] or "[]")
        except Exception:
            al = []
        ents.append({"id": r["id"], "slug": r["slug"], "name": r["name"], "kind": r["kind"],
                     "aliases": [a for a in al if isinstance(a, str)]})
    try:
        cache = json.loads(CACHE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    key = lambda e: hashlib.sha1(f"{EMBED_MODEL}|{_text(e)}".encode()).hexdigest()[:16]
    missing = [e for e in ents if key(e) not in cache]
    for i in range(0, len(missing), 64):
        chunk = missing[i:i + 64]
        for e, v in zip(chunk, embed([_text(e) for e in chunk])):
            cache[key(e)] = [round(x, 5) for x in _norm(v)]
        print(f"  embedded {min(i + 64, len(missing))}/{len(missing)} entities", flush=True)
    if missing:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(cache))
        os.replace(tmp, CACHE)
    for e in ents:
        e["vec"] = cache[key(e)]
    return ents


def candidates(queries: list[str], pool: list[dict], k: int = 10) -> list[tuple[float, dict]]:
    queries = [q for q in queries if q and q.strip()]
    if not queries:
        return []
    qv = [_norm(v) for v in embed(queries)]
    scored = []
    for e in pool:
        s = max(sum(a * b for a, b in zip(q, e["vec"])) for q in qv)
        if s >= MIN_COS:
            scored.append((s, e))
    scored.sort(key=lambda t: -t[0])
    return scored[:k]


_PICK = """A health-news card must be linked to entities in our evidence graph.

CARD
headline: {headline}
intervention: {intervention}
summary: {summary}

FACTOR CANDIDATES (the intervention / exposure):
{factors}

OUTCOME CANDIDATES (the disease / condition / measure):
{outcomes}

Pick at most one of each. Accept a candidate only if it is the SAME concept as the card's
intervention or condition, or its direct class (e.g. "SGLT2 inhibitors" for empagliflozin,
"Pancreatic cancer" for metastatic pancreatic adenocarcinoma). Reject merely related concepts
(a different drug, a different disease, a risk factor of the disease). If none fits, use null.

Return JSON only:
{{"factor": "slug or null", "factor_relation": "same|class", "outcome": "slug or null", "outcome_relation": "same|class"}}"""


def _edges(conn, where: str, args: tuple, limit: int) -> list[dict]:
    rows = conn.execute(f"""
        SELECT e.id, e.tier, e.direction, e.summary, e.effect_quant, e.review_status,
               f.name AS f_name, o.name AS o_name,
               (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id = e.id
                  AND COALESCE(ev.is_counter, 0) = 0) AS n_evidence
        FROM edge e JOIN entity f ON f.id = e.factor_id JOIN entity o ON o.id = e.outcome_id
        WHERE e.tier != 'deprecated' AND {where}""", args).fetchall()
    rows = sorted(rows, key=lambda r: (TIER_ORDER.get(r["tier"], 9),
                                       REVIEW_ORDER.get(r["review_status"] or "unreviewed", 9),
                                       -(r["n_evidence"] or 0)))
    return [{"id": r["id"], "tier": r["tier"], "direction": r["direction"],
             "factor": r["f_name"], "outcome": r["o_name"],
             "summary": (r["summary"] or "")[:220], "effect": r["effect_quant"] or "",
             "review": r["review_status"] or "unreviewed", "n_evidence": r["n_evidence"] or 0}
            for r in rows[:limit]]


def link(item: dict, ents: list[dict]) -> dict:
    d = item.get("detail") or {}
    words = lambda s: (s or "").replace("_", " ")
    fpool = [e for e in ents if e["kind"] not in OUTCOME_KINDS or e["kind"] == "biomarker"]
    opool = [e for e in ents if e["kind"] in OUTCOME_KINDS]
    fc = candidates([d.get("intervention"), words(item.get("factor_slug"))], fpool)
    # No headline here: "IV iron before heart surgery…" matched "major adverse cardiac events".
    oc = candidates([words(item.get("outcome_slug")), d.get("who_it_applies_to", "")[:120]], opool)
    fmt = lambda c: "\n".join(f"- {e['slug']}: {e['name']} [{e['kind']}]" for _, e in c) or "(none)"
    pick = ollama_json(_PICK.format(headline=item["headline"], intervention=d.get("intervention", ""),
                                    summary=(d.get("summary") or item.get("summary", ""))[:600],
                                    factors=fmt(fc), outcomes=fmt(oc)), num_predict=120) or {}
    fscore = {e["slug"]: sc for sc, e in fc}
    oscore = {e["slug"]: sc for sc, e in oc}
    by_slug = {e["slug"]: e for _, e in fc + oc}
    import re as _re
    toks = lambda t: set(_re.findall(r"[a-z0-9]{3,}", _re.sub(r"(?<=[a-z])-(?=\d)", "", (t or "").lower()).replace("_", " ")))
    # factor_slug is the model's own label ("pancreatic_cancer_drug") — not evidence of a name.
    ftext = toks(" ".join([d.get("intervention", ""), item["headline"]]))
    otext = toks(" ".join([words(item.get("outcome_slug")), d.get("who_it_applies_to", ""), item["headline"]]))

    def named(e, text):   # every word of the entity's name appears in the card
        return bool(toks(e["name"])) and toks(e["name"]) <= text

    # bge-m3 scores short names low even when right ("bladder cancer progression"
    # vs "Bladder cancer" 0.62 — same as breast cancer), so a model pick is kept
    # when the card names the entity, or when the vectors are clearly close.
    fp, op = by_slug.get(pick.get("factor")), by_slug.get(pick.get("outcome"))
    # No named intervention → no factor link: every wrong factor on 18.10 (opioid-use-disorder
    # care → "long-term opioid therapy", a pancreatitis drug → "omega-3") came from such cards.
    f = fp if (d.get("intervention") and fp and fp["slug"] in fscore
               and (named(fp, ftext) or fscore[fp["slug"]] >= PICK_COS)) else None
    o = op if op and op["slug"] in oscore and (named(op, otext) or oscore[op["slug"]] >= OUTCOME_COS) else None
    oq = [_norm(v) for v in embed([q for q in (words(item.get("outcome_slug")), o and o["name"]) if q])]
    ovec = {e["id"]: e["vec"] for e in opool}

    def closeness(eid: int) -> float:
        v = ovec.get(eid)
        return max(sum(a * b for a, b in zip(q, v)) for q in oq) if v and oq else 0.0
    out: dict = {"factor": None, "outcome": None, "pair": [], "outcome_edges": [], "factor_edges": [],
                 "outcome_total": 0, "factor_total": 0}
    with _connect() as conn:
        if f:
            out["factor"] = {"slug": f["slug"], "name": f["name"],
                             "relation": pick.get("factor_relation") or "same"}
            out["factor_total"] = conn.execute(
                "SELECT COUNT(*) FROM edge WHERE factor_id=? AND tier!='deprecated'", (f["id"],)).fetchone()[0]
        if o:
            out["outcome"] = {"slug": o["slug"], "name": o["name"],
                              "relation": pick.get("outcome_relation") or "same"}
            out["outcome_total"] = conn.execute(
                "SELECT COUNT(*) FROM edge WHERE outcome_id=? AND tier!='deprecated'", (o["id"],)).fetchone()[0]
        if f and o:
            out["pair"] = _edges(conn, "e.factor_id=? AND e.outcome_id=?", (f["id"], o["id"]), 3)
        if f and not out["pair"]:
            # The card's outcome often sits under another name in the graph
            # ("renal function decline" vs "chronic kidney disease"). Chosen by
            # vector closeness, not by the model: on 18.10 it picked the C/D
            # kidney edges over the tier-A one and once added heart failure.
            fe = conn.execute("""SELECT e.id, e.outcome_id FROM edge e
                                 WHERE e.factor_id=? AND e.tier!='deprecated'""", (f["id"],)).fetchall()
            # Relative, not absolute: bge-m3 puts "dementia risk"–"depression" at 0.6 too,
            # so keep only edges about as close as the best one.
            sc = {r["id"]: closeness(r["outcome_id"]) for r in fe}
            best = max(sc.values(), default=0.0)
            ids = [i for i, v in sc.items() if v >= max(0.55, best - 0.05)]
            if ids:
                out["pair"] = _edges(conn, f"e.id IN ({','.join('?' * len(ids))})", tuple(ids), 3)
        pair_ids = tuple(x["id"] for x in out["pair"]) or (-1,)
        ph = ",".join("?" * len(pair_ids))
        if o:
            out["outcome_edges"] = _edges(conn, f"e.outcome_id=? AND e.id NOT IN ({ph})",
                                          (o["id"], *pair_ids), 6)
        if f:
            out["factor_edges"] = _edges(conn, f"e.factor_id=? AND e.id NOT IN ({ph})",
                                         (f["id"], *pair_ids), 6)
    return out


def apply(item: dict, ents: list[dict]) -> dict:
    card = dict(item)
    c = link(card, ents)
    card["corpus"] = c
    card["edge_id"] = c["pair"][0]["id"] if c["pair"] else None
    card["is_orphan"] = not c["pair"]
    return card


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--missing", action="store_true")
    g.add_argument("--id", action="append")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)
    items = load_feed().get("items", [])
    if args.id:
        items = [i for i in items if i["id"] in args.id]
    elif args.missing:
        items = [i for i in items if "corpus" not in i]
    ents = entities()
    print(f"→ linking {len(items)} cards against {len(ents)} entities")
    linked = []
    for n, it in enumerate(items, 1):
        card = apply(it, ents)
        c = card["corpus"]
        print(f"[{n}/{len(items)}] {it['headline'][:60]}\n    factor={c['factor'] and c['factor']['name']} "
              f"outcome={c['outcome'] and c['outcome']['name']} pair={len(c['pair'])} "
              f"outcome_edges={c['outcome_total']} factor_edges={c['factor_total']}", flush=True)
        linked.append(card)
        if args.dry:
            print(json.dumps(c, indent=1, ensure_ascii=False)[:1500])
    if not args.dry and linked:
        feed = load_feed()   # re-read: a daily run may have appended meanwhile
        by_id = {c["id"]: c for c in linked}
        feed["items"] = [{**i, **{k: by_id[i["id"]][k] for k in ("corpus", "edge_id", "is_orphan")}}
                         if i["id"] in by_id else i for i in feed["items"]]
        save_feed(feed)
        print(f"→ saved {len(linked)} cards")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
