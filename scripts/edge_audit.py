#!/usr/bin/env python3
"""Edge text audit (18.10.2026) — are the numbers on edge pages in their sources?

The breakthroughs feed turned out to carry invented numbers (72/77 charts).
Edge summaries were written by the same kind of local model, so this checks
every edge whose summary / effect_quant / mechanism / caveats / population
contains a number: each number must appear in the abstracts, titles,
citations, notes or years of that edge's own evidence rows.

Read-only on the DB. Abstracts for evidence PMIDs come from ingested_paper,
else PubMed efetch, cached in data/cache/abstracts.json (gitignored).

  python scripts/edge_audit.py                 # audit, write data/audits/edge-numbers-<date>.json
  python scripts/edge_audit.py --sample 20     # also print examples
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CACHE = ROOT / "data" / "cache" / "abstracts.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
TEXT_FIELDS = ("summary", "effect_quant", "mechanism", "caveats", "population")


def _connect():
    from db import connect  # type: ignore
    return connect()


def load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(c: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(c))
    os.replace(tmp, CACHE)


def fetch(pmids: list[str]) -> dict[str, dict]:
    """PubMed title+abstract for up to 200 PMIDs; {} on failure (retried later)."""
    key = os.getenv("NCBI_API_KEY", "").strip()
    params = {"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}
    if key:
        params["api_key"] = key
    data = urllib.parse.urlencode(params).encode()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(EUTILS, data=data), timeout=60) as r:
                root = ET.fromstring(r.read())
            break
        except Exception as e:
            print(f"  efetch retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    else:
        return {}
    out = {}
    for art in root.findall(".//PubmedArticle"):
        pmid = "".join(art.find(".//PMID").itertext())
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        ab = " ".join("".join(s.itertext()) for s in art.findall(".//Abstract/AbstractText"))
        authors = ["".join(x.itertext()) for x in art.findall(".//AuthorList/Author/LastName")]
        au = art.find(".//AuthorList/Author/LastName")
        yr = art.find(".//PubDate/Year")
        md = art.find(".//PubDate/MedlineDate")
        jt = art.find(".//Journal/ISOAbbreviation")
        out[pmid] = {"title": title, "abstract": ab,
                     "first_author": "".join(au.itertext()) if au is not None else "",
                     "year": ("".join(yr.itertext()) if yr is not None else
                              ("".join(md.itertext())[:4] if md is not None else "")),
                     "journal": "".join(jt.itertext()) if jt is not None else "",
                     "authors": authors}
    return out


def abstracts(pmids: set[str]) -> dict[str, dict]:
    cache = load_cache()
    with _connect() as conn:
        for r in conn.execute("SELECT pmid, title, abstract FROM ingested_paper WHERE pmid IS NOT NULL"):
            if r["pmid"] in pmids and r["pmid"] not in cache and r["abstract"]:
                cache[r["pmid"]] = {"title": r["title"] or "", "abstract": r["abstract"]}
    todo = sorted(p for p in pmids if p not in cache or "authors" not in cache[p])
    for i in range(0, len(todo), 200):
        got = fetch(todo[i:i + 200])
        for p in todo[i:i + 200]:
            cache[p] = got.get(p, {"title": "", "abstract": "", "missing": True})
        print(f"  fetched {min(i + 200, len(todo))}/{len(todo)}", flush=True)
        time.sleep(0.4)
    if todo:
        save_cache(cache)
    return cache


_NUM = re.compile(r"(?<![A-Za-z\-/])\d+(?:[.,]\d+)?(?![A-Za-z\d])")


def nums(s: str) -> set[str]:
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s or "")
    out = set()
    for n in _NUM.findall(s):
        n = n.replace(",", ".")
        out.add(n)
        if "." in n:
            out.add(n.rstrip("0").rstrip("."))
    return out


def material(extra: set[str]) -> set[str]:
    """Numbers worth flagging: decimals, percents-sized values, anything > 10.
    Small integers (2 studies, type 2) are too often derived wording."""
    return {n for n in extra if "." in n or float(n) > 10}


def _norm(s: str) -> str:
    import unicodedata
    return re.sub(r"[^a-z0-9 ]+", " ", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())


def citation_ok(citation: str, year, rec: dict) -> str:
    """'ok' | 'mismatch' | 'unknown' — does the PMID's PubMed record match the citation?"""
    if not rec or rec.get("missing") or not rec.get("title"):
        return "unknown"
    cit, title = _norm(citation), _norm(rec["title"])
    cw, tw = set(cit.split()), set(title.split())
    if len(tw) >= 4 and len(cw & tw) / len(tw) >= 0.6:          # citation is the title
        return "ok"
    # "HuG et al", "GarciaPerdomoHA et al": initials glued on, hyphens dropped.
    glued = re.sub(r"(?<=[a-z])[A-Z]{1,3}\b", "", citation or "")
    flat = re.sub(r"[^a-z]", "", _norm(glued)[:80])
    names = {re.sub(r"[^a-z]", "", _norm(a)) for a in rec.get("authors", []) if a}
    named = any(len(n) >= 2 and n in flat for n in names)
    py = int(rec["year"]) if str(rec.get("year", "")).isdigit() else None
    cy = re.search(r"\b(19|20)\d{2}\b", citation or "")
    cy = int(cy.group(0)) if cy else (int(year) if str(year or "").isdigit() else None)
    year_ok = not (py and cy) or abs(py - cy) <= 1
    if named and year_ok:
        return "ok"
    if re.match(r"^\s*[A-Z][A-Za-z'\- ]+\b(et al|and|&)?\b.*\b(19|20)\d{2}\b", citation or "") and not named:
        return "mismatch"
    return "unknown"


def audit(sample: int = 0) -> dict:
    with _connect() as conn:
        edges = conn.execute(f"""SELECT e.id, e.tier, e.seed_source, e.review_status, {', '.join('e.' + f for f in TEXT_FIELDS)},
                                        f.name AS f_name, o.name AS o_name
                                 FROM edge e JOIN entity f ON f.id=e.factor_id JOIN entity o ON o.id=e.outcome_id
                                 WHERE e.tier != 'deprecated'""").fetchall()
        ev = conn.execute("SELECT edge_id, pmid, citation, notes, year, n_participants, real_title FROM evidence").fetchall()
    by_edge: dict[int, list] = {}
    for r in ev:
        by_edge.setdefault(r["edge_id"], []).append(r)
    pmids = {r["pmid"] for r in ev if r["pmid"]}
    abs_ = abstracts(pmids)

    rows, stats = [], Counter()
    for e in edges:
        text = re.sub(r"\bPMID \d+", "", " ".join(e[f] or "" for f in TEXT_FIELDS))   # our own source labels
        n_text = nums(text)
        if not n_text:
            stats["no_numbers"] += 1
            continue
        src = []
        have_abstract = 0
        for r in by_edge.get(e["id"], []):
            a = abs_.get(r["pmid"] or "", {})
            have_abstract += bool(a.get("abstract"))
            src += [r["citation"] or "", r["notes"] or "", str(r["year"] or ""), str(r["n_participants"] or ""),
                    r["real_title"] or "", a.get("title", ""), a.get("abstract", "")]
        extra = material(n_text - nums(" ".join(src)))
        key = "grounded" if not extra else ("ungrounded_no_abstract" if not have_abstract else "ungrounded")
        stats[key] += 1
        stats[f"{key}|{e['seed_source']}"] += 1
        stats[f"{key}|tier{e['tier']}"] += 1
        if extra:
            rows.append({"edge_id": e["id"], "tier": e["tier"], "seed": e["seed_source"], "review": e["review_status"],
                         "pair": f"{e['f_name']} → {e['o_name']}", "ungrounded": sorted(extra, key=float),
                         "abstracts": have_abstract, "evidence": len(by_edge.get(e["id"], []))})
    missing = sum(1 for p in pmids if abs_.get(p, {}).get("missing"))
    report = {"date": date.today().isoformat(), "edges": len(edges), "evidence_pmids": len(pmids),
              "pmids_not_on_pubmed": missing, "stats": dict(stats), "flagged": rows}
    out = ROOT / "data" / "audits" / f"edge-numbers-{report['date']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in report.items() if k != "flagged"}, indent=1))
    for r in rows[:sample]:
        print(r)
    print(f"→ {out}")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    a = ap.parse_args()
    audit(a.sample)
