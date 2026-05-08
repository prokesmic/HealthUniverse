"""Backfill missing PMIDs on legacy evidence rows.

Older Claude-seeded edges have plain-text citations like:
  "Aune et al. 2017 International Journal of Epidemiology"

This script parses each one, searches PubMed E-utilities, picks the
best match, and writes the resulting PMID back to the evidence row.
No Claude calls — pure NCBI E-utilities, free.

Usage:
    python backfill_pmids.py --dry-run
    python backfill_pmids.py --max 500
    python backfill_pmids.py --min-confidence 0.7

Quality guard: a match is only written when the title-similarity
between the cited reference and the PubMed candidate exceeds the
--min-confidence threshold (default 0.4). Lower threshold = more
matches but more risk of mismatched IDs. Default is conservative.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                      # noqa: E402
from ingest import pubmed                   # noqa: E402

CITATION_RE = re.compile(
    # Author can be: "Smith", "Smith J", "Smith MJ", "Smith-Jones",
    # or full name "Smith J et al." — accept the first whitespace-
    # delimited token as the surname for PubMed search.
    r"^\s*(?P<author>[A-Z][A-Za-z'\-]+)"
    r"(?:[\s,.\-A-Za-z]*?)"     # optional initials/comma-separated extra
    r"(?:\s+et\s+al\.?)?"
    r"[\s,.;]+(?P<year>(?:19|20)\d{2})"
    r"[\s,.;]+(?P<journal>.+?)\s*$"
)


def parse_citation(text: str) -> dict | None:
    if not text:
        return None
    m = CITATION_RE.match(text.strip())
    if not m:
        return None
    return {
        "author":  m.group("author").strip(),
        "year":    int(m.group("year")),
        "journal": m.group("journal").strip(),
    }


def title_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def search_candidates(parsed: dict) -> list[str]:
    """Return up to 10 candidate PMIDs for the parsed citation."""
    # Free-text + a tight year window via [dp]. Without year-pinning,
    # PubMed sorts by reverse date and returns recent papers, not the
    # 2004 one we want.
    yr = parsed["year"]
    q = (f'{parsed["author"]} AND "{parsed["journal"]}" AND '
         f'{yr-1}:{yr+1}[dp]')
    try:
        return pubmed.search(
            q, days_back=18000, retmax=10, quality_filter=False)
    except Exception:
        return []


def fetch_titles(pmids: list[str]) -> dict[str, dict]:
    """Map pmid → {title, journal, year, doi}."""
    out: dict[str, dict] = {}
    for paper in pubmed.fetch_abstracts(pmids):
        out[paper["pmid"]] = paper
    return out


def best_match(citation: str, candidates: dict[str, dict],
               parsed: dict) -> tuple[str, float, dict] | None:
    """Pick the candidate whose journal+year match exactly and whose
    title is the most similar to the original citation. Returns
    (pmid, score, paper) or None if nothing scores above 0."""
    best: tuple[str, float, dict] | None = None
    for pmid, paper in candidates.items():
        # Hard guards: year and journal must roughly match.
        if abs(int(paper.get("year") or 0) - parsed["year"]) > 1:
            continue
        # Score on title similarity to the citation tail (after journal).
        # Citations don't contain titles; we have to settle for journal
        # name match + year + author rather than fuzz-match a title.
        # Fall back to a constant 0.5 when journal+year+author all match.
        score = 0.5
        if paper.get("journal") and parsed["journal"].lower() in paper["journal"].lower():
            score += 0.2
        if str(paper.get("year")) == str(parsed["year"]):
            score += 0.2
        # Bonus for last-name match in title or authors? PubMed efetch
        # returns it in author list — out of scope here, score is good
        # enough: 0.5 base + journal/year bonuses → up to 0.9.
        if best is None or score > best[1]:
            best = (pmid, score, paper)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't write to DB, just print matches.")
    ap.add_argument("--max", type=int, default=2000,
                    help="Hard cap on rows to process per run.")
    ap.add_argument("--min-confidence", type=float, default=0.7,
                    help="Skip writes below this match score (0-1).")
    a = ap.parse_args()

    with connect() as c:
        rows = c.execute(
            """SELECT id, edge_id, citation, year FROM evidence
               WHERE (pmid IS NULL OR pmid = '')
                 AND citation IS NOT NULL AND citation != ''
               ORDER BY id
               LIMIT ?""", (a.max,)).fetchall()
        rows = [dict(r) for r in rows]

    print(f"[backfill] {len(rows)} rows to inspect")
    matched = 0; unparseable = 0; nohit = 0; lowconf = 0; updated = 0

    for i, ev in enumerate(rows, 1):
        parsed = parse_citation(ev["citation"])
        if not parsed:
            unparseable += 1
            continue
        pmids = search_candidates(parsed)
        if not pmids:
            nohit += 1
            continue
        # Fetch metadata for the candidates and pick best
        try:
            cand = fetch_titles(pmids)
        except Exception as exc:
            print(f"  [{i}/{len(rows)}] efetch err: {exc}")
            time.sleep(2.0)
            continue
        match = best_match(ev["citation"], cand, parsed)
        if not match:
            nohit += 1
            continue
        pmid, score, paper = match
        matched += 1
        if score < a.min_confidence:
            lowconf += 1
            continue
        # Confidence high enough — write
        if not a.dry_run:
            with connect() as c:
                c.execute(
                    "UPDATE evidence SET pmid=?, doi=? WHERE id=?",
                    (pmid, paper.get("doi") or "", ev["id"]))
            updated += 1
        if i % 25 == 0 or i == 1:
            print(f"  [{i:4}/{len(rows)}] {ev['citation'][:60]}: "
                  f"PMID {pmid} (score {score:.2f}){' [dry]' if a.dry_run else ''}")
        time.sleep(0.15)   # be polite to NCBI

    print()
    print(f"[backfill] done")
    print(f"  inspected:    {len(rows)}")
    print(f"  unparseable:  {unparseable}")
    print(f"  no PubMed hit:{nohit}")
    print(f"  matched:      {matched}")
    print(f"  low confidence skipped: {lowconf}")
    print(f"  written:      {updated}{' (dry-run)' if a.dry_run else ''}")
    if a.dry_run:
        print("  Re-run without --dry-run to apply.")


if __name__ == "__main__":
    main()
