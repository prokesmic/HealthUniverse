#!/usr/bin/env python3
"""Repair evidence rows whose PMID points to a different paper (18.10.2026).

edge_audit.citation_ok() found 558 rows (5 %) where the citation says e.g.
"Monami M et al 2022 Diabetologia" but the stored PMID resolves to another
paper — same topic and year, wrong article — so the PubMed link on the edge
page sends readers elsewhere. Mostly the Codex "manual" batches.

For each such row, search PubMed for the cited paper (author + year ±1 +
journal) and accept a hit only if the author is on its author list and its
title shares topic words with the edge. Exactly one acceptable hit → replace
pmid/url/real_title/doi. None or several → clear pmid and url (the citation
text stays, without a misleading link) and set relevance_status =
'citation_mismatch'. Every change is written to edge_history with the reason.

  python scripts/fix_citation_pmids.py --dry
  python scripts/fix_citation_pmids.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import edge_audit as ea  # noqa: E402

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
STOP = set("with from that this were among risk effect effects study studies trial analysis meta "
           "systematic review association associated patients adults versus and the for".split())


def _connect():
    from db import connect  # type: ignore
    return connect()


def esearch(term: str) -> list[str]:
    url = f"{ESEARCH}?{urllib.parse.urlencode({'db': 'pubmed', 'term': term, 'retmax': 20, 'retmode': 'json'})}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                out = json.loads(r.read())["esearchresult"]["idlist"]
            time.sleep(0.4)
            return out
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return []


def parse_citation(cit: str) -> tuple[str, int | None, str]:
    """('Monami', 2022, 'Diabetologia') from 'Monami M et al 2022 Diabetologia'."""
    s = re.sub(r"(?<=[a-z])[A-Z]{1,3}\b", "", cit or "")          # MonamiM → Monami
    m = re.match(r"\s*([A-Z][A-Za-z'\-]+(?:[ -][A-Z][a-z'\-]+)?)", s)
    surname = m.group(1) if m else ""
    y = re.search(r"\b(19|20)\d{2}\b", cit or "")
    year = int(y.group(0)) if y else None
    journal = cit[y.end():].strip(" .,;") if y else ""
    return surname, year, journal


def topic_words(*texts: str) -> set[str]:
    return {w[:6] for t in texts for w in re.findall(r"[a-z]{4,}", (t or "").lower()) if w not in STOP}


_JABBR = {"nejm": "n engl j med", "jama": "jama", "bmj": "bmj", "plos one": "plos one", "pnas": "proc natl acad sci u s a"}


def journal_match(cited: str, iso: str) -> bool:
    """'Nature Communications' ~ 'Nat Commun'; 'NEJM' ~ 'N Engl J Med'."""
    c = ea._norm(cited).strip()
    c = _JABBR.get(c, c)
    ct, it = c.split(), ea._norm(iso).split()
    if not it:
        return True
    hit = sum(1 for i in it if any(w.startswith(i) or i.startswith(w) for w in ct))
    return hit / len(it) >= 0.6


def find(cit: str, year_hint, edge_words: tuple[set[str], set[str]]) -> tuple[str | None, str]:
    surname, year, journal = parse_citation(cit)
    year = year or (int(year_hint) if str(year_hint or "").isdigit() else None)
    if not surname or not year:
        return None, "unparseable citation"
    terms = []
    yr = f"{year - 1}:{year + 1}[dp]"
    if journal:
        terms.append(f'{surname}[au] AND {yr} AND "{journal}"[ta]')
    terms.append(f"{surname}[au] AND {yr}")
    ids: list[str] = []
    for t in terms:
        ids = esearch(t)
        if ids:
            break
    if not ids:
        return None, "not found on PubMed"
    recs = ea.fetch(ids[:20])
    flat_name = re.sub(r"[^a-z]", "", ea._norm(surname))
    ok = []
    for pmid, r in recs.items():
        authors = {re.sub(r"[^a-z]", "", ea._norm(a)) for a in r.get("authors", [])}
        if flat_name not in authors:
            continue
        if not str(r.get("year", "")).isdigit() or abs(int(r["year"]) - year) > 1:
            continue
        if journal and r.get("journal") and not journal_match(journal, r["journal"]):
            continue
        tw = topic_words(r["title"])
        fhit, ohit = len(tw & edge_words[0]), len(tw & edge_words[1])
        # Both ends of the edge must be in the title (names only, not notes):
        # the 1-word rule "repaired" glutamine → permeability to a pulmonary-vein paper.
        if fhit >= 1 and ohit >= 1:
            ok.append((fhit + ohit, pmid, r))
    if not ok:
        return None, "no candidate by that author on this topic"
    ok.sort(key=lambda t: -t[0])
    if len(ok) > 1 and ok[0][0] == ok[1][0]:
        return None, "ambiguous: several papers by that author on this topic"
    return ok[0][1], ok[0][2]["title"]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)
    cache = ea.load_cache()
    with _connect() as conn:
        rows = conn.execute("""SELECT ev.id, ev.edge_id, ev.pmid, ev.citation, ev.year, ev.notes,
                                      f.name AS f_name, o.name AS o_name
                               FROM evidence ev JOIN edge e ON e.id = ev.edge_id
                               JOIN entity f ON f.id = e.factor_id JOIN entity o ON o.id = e.outcome_id
                               WHERE ev.pmid IS NOT NULL AND ev.pmid != ''""").fetchall()
        bad = [r for r in rows if ea.citation_ok(r["citation"], r["year"], cache.get(r["pmid"])) == "mismatch"]
        if args.limit:
            bad = bad[: args.limit]
        print(f"→ {len(bad)} evidence rows whose PMID is a different paper")
        st = Counter()
        for n, r in enumerate(bad, 1):
            fw, ow = topic_words(r["f_name"]), topic_words(r["o_name"])
            words = (fw - ow or fw, ow - fw or ow)   # "PCOS" on both ends must not count twice
            new, why = find(r["citation"], r["year"], words)
            if new and new != r["pmid"]:
                st["repaired"] += 1
                print(f"[{n}] ✓ {r['citation'][:50]} {r['pmid']} → {new} ({why[:60]})")
                if not args.dry:
                    conn.execute("""UPDATE evidence SET pmid=?, url=?, real_title=?, relevance_status=NULL,
                                    relevance_score=NULL WHERE id=?""",
                                 (new, f"https://pubmed.ncbi.nlm.nih.gov/{new}/", why, r["id"]))
                    conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason)
                                    VALUES (?, 'evidence.pmid', ?, ?, ?)""",
                                 (r["edge_id"], r["pmid"], new,
                                  f"PMID resolved to a different paper; re-found '{r['citation'][:80]}' on PubMed"))
            else:
                st["cleared"] += 1
                print(f"[{n}] ✗ {r['citation'][:50]} {r['pmid']} cleared ({why})")
                if not args.dry:
                    conn.execute("""UPDATE evidence SET pmid=NULL, url=NULL, relevance_status='citation_mismatch'
                                    WHERE id=?""", (r["id"],))
                    conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason)
                                    VALUES (?, 'evidence.pmid', ?, NULL, ?)""",
                                 (r["edge_id"], r["pmid"],
                                  f"PMID resolved to a different paper and '{r['citation'][:80]}' could not be "
                                  f"re-found unambiguously ({why}); link removed, citation kept"))
            if not args.dry and n % 25 == 0:
                conn.commit()
        if not args.dry:
            conn.commit()
    print(dict(st))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
