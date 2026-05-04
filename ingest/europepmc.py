"""Europe PMC client. Free, no key needed."""
from __future__ import annotations

import httpx

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def search(query: str, *, page_size: int = 25, days_back: int = 1) -> list[dict]:
    q = f'({query}) AND FIRST_PDATE:[NOW-{days_back}DAYS TO NOW]'
    params = {"query": q, "format": "json", "pageSize": page_size,
              "resultType": "core"}
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"{BASE}/search", params=params)
        r.raise_for_status()
    out = []
    for h in r.json().get("resultList", {}).get("result", []):
        out.append({
            "pmid":     h.get("pmid"),
            "doi":      h.get("doi"),
            "title":    h.get("title", ""),
            "abstract": h.get("abstractText", ""),
            "journal":  h.get("journalTitle", ""),
            "year":     int(h["pubYear"]) if h.get("pubYear", "").isdigit() else None,
            "source":   "europepmc",
        })
    return out
