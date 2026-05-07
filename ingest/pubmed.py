"""PubMed E-utilities client. No API key needed for low volume (3 req/s)."""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Iterator

import httpx

import os, random
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Without an API key NCBI allows 3 req/sec.  With a key, 10 req/sec.
# We're conservative either way; bursts spike easily past the limit.
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "").strip() or None
RATE_LIMIT_S = 0.12 if NCBI_API_KEY else 0.45


def _request_with_retry(c: httpx.Client, url: str, params: dict,
                         max_retries: int = 4):
    """GET with exponential backoff on 429 + 5xx. Returns the response or
    raises after max_retries. Adds API key if available."""
    if NCBI_API_KEY:
        params = {**params, "api_key": NCBI_API_KEY}
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            r = c.get(url, params=params)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                # Backoff: 0.8s, 2s, 4s, 8s + jitter
                delay = (0.8 * (2 ** attempt)) + random.uniform(0, 0.4)
                time.sleep(delay)
                continue
            r.raise_for_status()
            return r
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            last_exc = exc
            time.sleep((0.8 * (2 ** attempt)) + random.uniform(0, 0.4))
    if last_exc:
        raise last_exc
    raise RuntimeError(f"PubMed unreachable after {max_retries} retries")


# PubMed publication-type filter applied to every search by default.
# Drops opinion pieces, animal-only studies, in-vitro work, comments,
# and letters at the source — Gemma never burns a call on noise.
QUALITY_FILTER = (
    "AND ("
    "\"meta-analysis\"[Publication Type] OR "
    "\"systematic review\"[Publication Type] OR "
    "\"randomized controlled trial\"[Publication Type] OR "
    "\"clinical trial\"[Publication Type] OR "
    "\"observational study\"[Publication Type] OR "
    "\"cohort studies\"[MeSH Terms] OR "
    "\"case-control studies\"[MeSH Terms]"
    ") AND humans[Filter] NOT (review[Publication Type] NOT "
    "(\"meta-analysis\"[Publication Type] OR \"systematic review\"[Publication Type]))"
)


def search(term: str, *, days_back: int = 1, retmax: int = 50,
           quality_filter: bool = True) -> list[str]:
    """Search PubMed and return PMIDs (newest first).

    `quality_filter=True` (default) applies QUALITY_FILTER so Gemma sees
    only high-evidence publication types restricted to humans. Set False
    for manual diagnostic searches that need raw breadth.
    """
    full_term = f"({term}) {QUALITY_FILTER}" if quality_filter else term
    params = {
        "db": "pubmed", "term": full_term, "retmax": retmax, "retmode": "json",
        "sort": "date", "reldate": days_back, "datetype": "edat",
    }
    with httpx.Client(timeout=30.0) as c:
        r = _request_with_retry(c, f"{EUTILS}/esearch.fcgi", params)
    time.sleep(RATE_LIMIT_S)
    return r.json().get("esearchresult", {}).get("idlist", [])


def fetch_abstracts(pmids: list[str]) -> Iterator[dict]:
    """Yield {pmid, title, abstract, journal, year, doi} for each PMID.

    Skips chunks that fail after retries instead of raising — one bad
    fetch must not abort an 8-hour burst run.
    """
    if not pmids:
        return
    for chunk_start in range(0, len(pmids), 50):
        chunk = pmids[chunk_start:chunk_start + 50]
        params = {"db": "pubmed", "id": ",".join(chunk),
                  "rettype": "abstract", "retmode": "xml"}
        try:
            with httpx.Client(timeout=60.0) as c:
                r = _request_with_retry(c, f"{EUTILS}/efetch.fcgi", params)
            root = ET.fromstring(r.text)
        except Exception as exc:
            print(f"  [pubmed] efetch chunk {chunk[:3]}…: {exc}", flush=True)
            time.sleep(2.0)
            continue
        for art in root.findall(".//PubmedArticle"):
            yield _parse(art)
        time.sleep(RATE_LIMIT_S)


def _parse(art: ET.Element) -> dict:
    pmid_el = art.find(".//PMID")
    title_el = art.find(".//ArticleTitle")
    journal_el = art.find(".//Journal/Title")
    year_el = art.find(".//PubDate/Year") or art.find(".//PubDate/MedlineDate")
    doi_el = art.find(".//ArticleId[@IdType='doi']")
    abstract_parts = [
        ((seg.attrib.get("Label", "") + ": ") if seg.attrib.get("Label") else "")
        + (seg.text or "")
        for seg in art.findall(".//Abstract/AbstractText")
    ]
    year_text = (year_el.text or "") if year_el is not None else ""
    year = int(year_text[:4]) if year_text[:4].isdigit() else None
    return {
        "pmid":      pmid_el.text if pmid_el is not None else None,
        "title":     "".join(title_el.itertext()) if title_el is not None else "",
        "abstract":  "\n".join(p for p in abstract_parts if p),
        "journal":   journal_el.text if journal_el is not None else "",
        "year":      year,
        "doi":       doi_el.text if doi_el is not None else None,
        "source":    "pubmed",
    }


def search_for_entity(name: str, *, days_back: int = 1, retmax: int = 25) -> list[str]:
    """Search PubMed for a factor or outcome name with sensible filters.
    Filters down to humans + last `days_back` days."""
    term = f'("{name}"[Title/Abstract]) AND humans[MeSH Terms]'
    return search(term, days_back=days_back, retmax=retmax)
