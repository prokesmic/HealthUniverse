"""Semantic verifier for the evidence corpus.

For every (edge, evidence) pair with a PMID, fetches the real PubMed
title via E-utilities, computes a cosine similarity between the edge's
(factor_name + " and " + outcome_name) and the actual paper title using
Ollama nomic-embed-text, and writes:

  evidence.real_title         — fetched title
  evidence.relevance_score    — cosine similarity in [0, 1]
  evidence.relevance_status   — 'verified' | 'weak' | 'flagged' | 'missing'

Also rolls each result up to the edge level. If a tier-A/B edge has no
verified evidence rows after the pass, the edge is demoted to
review_status='needs_recheck' so the live site can hide / badge it.

Run:
  python verify_evidence.py audit --tier A           # tier-A only (fastest)
  python verify_evidence.py audit --tier A,B         # both top tiers
  python verify_evidence.py audit                    # everything
  python verify_evidence.py audit --limit 200        # cap for testing
  python verify_evidence.py report                   # print summary
  python verify_evidence.py rollback-bad             # revert PMIDs flagged by audit

Thresholds (tunable):
  >= 0.65  → 'verified'
  >= 0.45  → 'weak'    (kept, badged)
  <  0.45  → 'flagged' (excluded from tier counts)
  no PMID or fetch failed → 'missing'
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DB_PATH = ROOT / "data" / "healthuniverse.db"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("HU_EMBED_MODEL", "nomic-embed-text:latest")
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")

THRESH_VERIFIED = 0.65
THRESH_WEAK = 0.45

# ─── E-utilities ──────────────────────────────────────────────────────


def _eutils_titles(pmids: list[str]) -> dict[str, str]:
    """Batch-fetch PubMed titles for up to ~200 PMIDs at a time."""
    if not pmids:
        return {}
    qs = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    if NCBI_API_KEY:
        qs["api_key"] = NCBI_API_KEY
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
           + urllib.parse.urlencode(qs))
    out: dict[str, str] = {}
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthUniverse-verifier/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            res = data.get("result", {}) or {}
            for pid in pmids:
                rec = res.get(str(pid), {})
                t = rec.get("title") or ""
                if t:
                    out[str(pid)] = t.strip()
            return out
        except Exception as e:
            if attempt == 3:
                print(f"  ! eutils failed after 4 tries: {e}", file=sys.stderr)
                return out
            time.sleep(2 * (attempt + 1))
    return out


# ─── Ollama embeddings ────────────────────────────────────────────────


def _embed(text: str) -> list[float]:
    """Return a normalized embedding from Ollama. Raises on failure."""
    body = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        j = json.loads(resp.read())
    v = j.get("embedding") or []
    if not v:
        raise RuntimeError(f"empty embedding from ollama for: {text[:60]!r}")
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ─── Audit pass ───────────────────────────────────────────────────────


def _decide(score: float | None) -> str:
    if score is None:
        return "missing"
    if score >= THRESH_VERIFIED:
        return "verified"
    if score >= THRESH_WEAK:
        return "weak"
    return "flagged"


def cmd_audit(args: argparse.Namespace) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    where = "1=1"
    params: list = []
    if args.tier:
        tiers = args.tier.split(",")
        where += " AND e.tier IN ({})".format(",".join(["?"] * len(tiers)))
        params.extend(tiers)
    if args.only_unverified:
        where += " AND (ev.relevance_status IS NULL OR ev.relevance_status = '')"

    sql = f"""
        SELECT ev.id AS evidence_id, ev.pmid, ev.citation, ev.year,
               e.id AS edge_id, e.tier,
               f.name AS factor_name, o.name AS outcome_name
        FROM evidence ev
        JOIN edge e ON e.id = ev.edge_id
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE {where} AND ev.pmid IS NOT NULL AND TRIM(ev.pmid) != ''
        ORDER BY e.tier, e.id
    """
    if args.limit:
        sql += f" LIMIT {int(args.limit)}"

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    print(f"[audit] candidates: {len(rows)}")
    if not rows:
        return

    # Pre-cache edge embeddings (factor + outcome).
    edge_keys: dict[int, str] = {}
    edge_emb: dict[int, list[float]] = {}
    for r in rows:
        if r["edge_id"] not in edge_keys:
            edge_keys[r["edge_id"]] = (
                f"Health evidence on the relationship between "
                f"{r['factor_name']} and {r['outcome_name']}."
            )
    print(f"[audit] embedding {len(edge_keys)} unique edge prompts...")
    t0 = time.time()
    for i, (eid, txt) in enumerate(edge_keys.items(), 1):
        try:
            edge_emb[eid] = _embed(txt)
        except Exception as e:
            print(f"  ! embed failed for edge {eid}: {e}")
        if i % 50 == 0:
            print(f"    {i}/{len(edge_keys)} embedded ({time.time()-t0:.0f}s)")

    # Batch PubMed title fetches in groups of 100.
    pmid_to_title: dict[str, str] = {}
    pmids = sorted({r["pmid"] for r in rows})
    print(f"[audit] fetching {len(pmids)} PubMed titles in batches of 100...")
    for i in range(0, len(pmids), 100):
        chunk = pmids[i : i + 100]
        pmid_to_title.update(_eutils_titles(chunk))
        if i % 500 == 0:
            print(f"    {i+len(chunk)}/{len(pmids)} fetched")
        time.sleep(0.4)

    # Score every evidence row.
    print(f"[audit] scoring {len(rows)} evidence rows...")
    cur = conn.cursor()
    counts = {"verified": 0, "weak": 0, "flagged": 0, "missing": 0}
    audit_rows: list[tuple] = []
    t0 = time.time()
    for i, r in enumerate(rows, 1):
        title = pmid_to_title.get(r["pmid"], "")
        emb_e = edge_emb.get(r["edge_id"])
        score: float | None = None
        if title and emb_e:
            try:
                emb_t = _embed(title)
                score = _cos(emb_e, emb_t)
            except Exception:
                score = None
        decision = _decide(score)
        counts[decision] += 1
        cur.execute(
            "UPDATE evidence SET real_title=?, relevance_score=?, relevance_status=? WHERE id=?",
            (title or None, score, decision, r["evidence_id"]),
        )
        audit_rows.append(
            (
                r["edge_id"],
                r["evidence_id"],
                r["pmid"],
                title,
                r["citation"],
                r["factor_name"],
                r["outcome_name"],
                score,
                decision,
                datetime.now().isoformat(timespec="seconds"),
            )
        )
        if i % 100 == 0:
            print(f"    {i}/{len(rows)} ({time.time()-t0:.0f}s) "
                  f"verified={counts['verified']} weak={counts['weak']} "
                  f"flagged={counts['flagged']} missing={counts['missing']}")
    cur.executemany(
        """INSERT INTO verifier_audit
        (edge_id, evidence_id, pmid, pubmed_title, stored_citation,
         factor_name, outcome_name, relevance_score, decision, checked_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        audit_rows,
    )
    conn.commit()

    # Roll up to edge.review_status.
    print("[audit] rolling up to edge.review_status...")
    edge_ids = list(edge_keys.keys())
    bad_edges = 0
    for eid in edge_ids:
        c = conn.execute(
            "SELECT relevance_status, COUNT(*) FROM evidence WHERE edge_id=? GROUP BY relevance_status",
            (eid,),
        ).fetchall()
        by = {row[0]: row[1] for row in c}
        ver = by.get("verified", 0)
        weak = by.get("weak", 0)
        flagged = by.get("flagged", 0)
        if ver == 0 and weak == 0:
            conn.execute("UPDATE edge SET review_status='needs_recheck' WHERE id=?", (eid,))
            bad_edges += 1
        elif ver >= 1:
            conn.execute("UPDATE edge SET review_status='verified_evidence' WHERE id=?", (eid,))
        else:
            conn.execute("UPDATE edge SET review_status='weak_evidence' WHERE id=?", (eid,))
    conn.commit()

    print(f"[audit] done. counts={counts}  edges_demoted_needs_recheck={bad_edges}")
    print(f"        elapsed: {time.time()-t0:.0f}s")


# ─── Report ───────────────────────────────────────────────────────────


def cmd_report(args: argparse.Namespace) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("=== Evidence verification status (all tiers) ===")
    rows = conn.execute("""
        SELECT e.tier,
               SUM(CASE WHEN ev.relevance_status='verified' THEN 1 ELSE 0 END) AS v,
               SUM(CASE WHEN ev.relevance_status='weak'     THEN 1 ELSE 0 END) AS w,
               SUM(CASE WHEN ev.relevance_status='flagged'  THEN 1 ELSE 0 END) AS f,
               SUM(CASE WHEN ev.relevance_status='missing'  THEN 1 ELSE 0 END) AS m,
               SUM(CASE WHEN ev.relevance_status IS NULL    THEN 1 ELSE 0 END) AS u,
               COUNT(*) AS total
        FROM evidence ev
        JOIN edge e ON e.id = ev.edge_id
        GROUP BY e.tier
        ORDER BY e.tier
    """).fetchall()
    print(f"{'tier':<6}{'verified':>10}{'weak':>8}{'flagged':>10}{'missing':>10}{'unaudited':>12}{'total':>10}")
    for r in rows:
        print(f"{r['tier']:<6}{r['v']:>10}{r['w']:>8}{r['f']:>10}{r['m']:>10}{r['u']:>12}{r['total']:>10}")

    print()
    print("=== Edge review_status (top 5) ===")
    rows = conn.execute("""
        SELECT e.tier, e.review_status, COUNT(*) AS n
        FROM edge e
        GROUP BY e.tier, e.review_status
        ORDER BY e.tier, n DESC
    """).fetchall()
    for r in rows:
        print(f"  tier={r['tier']:<2}  {r['review_status'] or 'unreviewed':<22} n={r['n']}")

    print()
    print("=== Worst 10 flagged tier-A rows (lowest relevance) ===")
    rows = conn.execute("""
        SELECT ev.relevance_score, ev.real_title, ev.citation,
               f.name AS f, o.name AS o, e.id AS eid
        FROM evidence ev
        JOIN edge e ON e.id=ev.edge_id
        JOIN entity f ON f.id=e.factor_id
        JOIN entity o ON o.id=e.outcome_id
        WHERE e.tier='A' AND ev.relevance_status='flagged'
        ORDER BY ev.relevance_score ASC
        LIMIT 10
    """).fetchall()
    for r in rows:
        s = r['relevance_score'] or 0.0
        print(f"  edge {r['eid']:<5} score={s:.2f}  {r['f']} → {r['o']}")
        print(f"     real:   {(r['real_title'] or '')[:90]}")
        print(f"     stored: {(r['citation'] or '')[:90]}")


# ─── Rollback ─────────────────────────────────────────────────────────


def cmd_rollback_bad(args: argparse.Namespace) -> None:
    """Strip the PMID from any evidence row classified 'flagged' so the
    site stops linking to a PubMed paper that doesn't actually support
    the claim. The citation text stays so the row isn't silently lost."""
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute(
        "SELECT COUNT(*) FROM evidence WHERE relevance_status='flagged'"
    ).fetchone()[0]
    print(f"[rollback] flagged rows: {n}")
    if not args.yes:
        print("dry run — pass --yes to actually clear PMIDs.")
        return
    conn.execute(
        "UPDATE evidence SET pmid=NULL, doi=NULL, url=NULL "
        "WHERE relevance_status='flagged'"
    )
    conn.commit()
    print(f"[rollback] cleared PMID/DOI/URL on {n} rows.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("audit", help="Run semantic verification against PubMed.")
    p.add_argument("--tier", default="", help="Comma list, e.g. A or A,B")
    p.add_argument("--limit", type=int, default=0, help="0 = all")
    p.add_argument("--only-unverified", action="store_true",
                   help="Skip evidence rows that already have a relevance_status")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("report", help="Print audit summary.")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("rollback-bad", help="Clear PMIDs on 'flagged' rows.")
    p.add_argument("--yes", action="store_true", help="Actually do it.")
    p.set_defaults(func=cmd_rollback_bad)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
