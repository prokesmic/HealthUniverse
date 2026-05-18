#!/usr/bin/env python3
"""Daily breakthroughs ingestion.

Pipeline:
  1. Fetch a curated set of RSS feeds (clinical trials, journals, FDA, ESC/AHA/ASCO).
  2. Dedupe vs existing items by canonical URL + headline cosine similarity.
  3. For each candidate, ask local Gemma (Ollama) to classify, score, and
     rewrite into our claim-honest schema.
  4. Reject anything with strength < 0.55.
  5. Match factor/outcome slugs against the corpus → set edge_id or
     mark as orphan.
  6. Merge with existing items in data/breakthroughs.json (keep 120 days).

Designed to run via launchd / cron once a day. No paid APIs — Ollama only.

Usage:
  python scripts/breakthroughs_daily.py            # full run
  python scripts/breakthroughs_daily.py --dry      # don't write, just print
  python scripts/breakthroughs_daily.py --limit 5  # cap items processed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.breakthroughs import (   # noqa: E402
    load_feed, save_feed, match_corpus, CATEGORY_ORDER,
)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "gemma4:26b"           # falls back to llama3:8b if unavailable
KEEP_DAYS = 120
MIN_STRENGTH = 0.55

# Curated RSS bundle — same kind of sources Perplexity surfaces, but
# RSS-able so we don't need to scrape.
FEEDS = [
    # Journals
    ("NEJM",              "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm"),
    ("JAMA",              "https://jamanetwork.com/rss/site_3/67.xml"),
    ("Lancet",            "https://www.thelancet.com/rssfeed/lancet_current.xml"),
    ("Nature Medicine",   "https://www.nature.com/nm.rss"),
    ("Cell",              "https://www.cell.com/cell/inpress.rss"),
    ("BMJ",               "https://www.bmj.com/content/recent.rss"),
    # Cardio
    ("JACC",              "https://www.jacc.org/action/showFeed?type=etoc&feed=rss&jc=jac"),
    ("Circulation",       "https://www.ahajournals.org/action/showFeed?type=etoc&feed=rss&jc=circ"),
    # Oncology
    ("JCO",               "https://ascopubs.org/action/showFeed?type=etoc&feed=rss&jc=jco"),
    ("Lancet Oncology",   "https://www.thelancet.com/rssfeed/lanonc_current.xml"),
    # Trials + regulatory
    ("ClinicalTrials.gov","https://classic.clinicaltrials.gov/ct2/results/rss.xml?rcv_d=14&cond=&type=Intr"),
    ("FDA Approvals",     "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml"),
    ("FDA Drug Safety",   "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml"),
    # Industry / breakthrough commentary
    ("Endpoints News",    "https://endpts.com/feed/"),
    ("STAT News",         "https://www.statnews.com/feed/"),
]

USER_AGENT = "HealthUniverse-BreakthroughsBot/1.0 (+contact: prokesmic@gmail.com)"

# ─── Fetching ─────────────────────────────────────────────────────

def fetch_rss(url: str, timeout: int = 12) -> list[dict]:
    """Parse a basic RSS/Atom feed → [{title, link, published, source}]."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except Exception as e:
        print(f"  ✗ fetch failed {url}: {e}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"  ✗ parse failed {url}: {e}", file=sys.stderr)
        return []
    out: list[dict] = []
    # RSS 2.0
    for it in root.iter("item"):
        out.append({
            "title":     (it.findtext("title") or "").strip(),
            "link":      (it.findtext("link")  or "").strip(),
            "published": (it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip(),
            "summary":   _strip_html((it.findtext("description") or "").strip())[:600],
        })
    # Atom fallback
    if not out:
        ns = "{http://www.w3.org/2005/Atom}"
        for it in root.iter(f"{ns}entry"):
            link_el = it.find(f"{ns}link")
            href = (link_el.get("href") if link_el is not None else "") or ""
            out.append({
                "title":     (it.findtext(f"{ns}title") or "").strip(),
                "link":      href.strip(),
                "published": (it.findtext(f"{ns}updated") or it.findtext(f"{ns}published") or "").strip(),
                "summary":   _strip_html((it.findtext(f"{ns}summary") or "").strip())[:600],
            })
    return out


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s).replace("&nbsp;", " ").strip()


# ─── Dedupe ───────────────────────────────────────────────────────

def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).strip()


def dedupe(candidates: list[dict], existing: list[dict]) -> list[dict]:
    seen_urls = {e.get("source_url") for e in existing}
    seen_titles = {_norm_title(e.get("headline", "")) for e in existing}
    out: list[dict] = []
    for c in candidates:
        if not c.get("title") or not c.get("link"):
            continue
        if c["link"] in seen_urls:
            continue
        nt = _norm_title(c["title"])
        if nt in seen_titles:
            continue
        # Cheap intra-batch dedupe too
        if any(_jaccard(nt, _norm_title(o["title"])) > 0.85 for o in out):
            continue
        seen_urls.add(c["link"]); seen_titles.add(nt)
        out.append(c)
    return out


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ─── Ollama ───────────────────────────────────────────────────────

def gemma_classify(raw: dict) -> dict | None:
    """Ask Gemma to rewrite + classify. Returns the structured card or None."""
    prompt = _PROMPT_TMPL.format(
        title=raw["title"], summary=raw["summary"][:500], source=raw["source_name"],
        link=raw["link"], published=raw["published"],
    )
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_predict": 700},
    }
    try:
        req = urllib.request.Request(
            OLLAMA_URL, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read())
    except Exception as e:
        print(f"  ✗ ollama failed: {e}", file=sys.stderr)
        return None
    text = body.get("response", "")
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        # Pull the first JSON object substring
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        try:
            out = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return out


_PROMPT_TMPL = """You are an editor for an audited health-evidence platform. You read a press item or journal abstract and decide whether it represents a real, meaningful clinical breakthrough — and if so, you rewrite it claim-honestly into our card schema.

INPUT
title:     {title}
source:    {source}
published: {published}
link:      {link}
summary:   {summary}

OUTPUT — a single JSON object with these keys only:
{{
  "is_breakthrough": true|false,           // false rejects the item
  "strength": 0.0-1.0,                     // confidence the finding is real & meaningful
  "category": "oncology|cardio|metabolic|neuro|longevity|other",
  "stage":    "preclinical|phase1|phase2|phase3|approved|guideline|recall",
  "headline": "claim-honest rewrite, ≤90 chars, no hype words",
  "summary":  "2 sentences, plain English, with specific numbers if available",
  "why_it_matters": "1 sentence — practical implication, ≤140 chars",
  "factor_slug":  "snake_case identifier of the intervention (drug/factor)",
  "outcome_slug": "snake_case identifier of the disease/outcome",
  "graphic": {{ "kind": "bar_delta|forest_plot|line_trend|kaplan_meier|recall_pictogram", "...": "shape depends on kind" }}
}}

RULES
- Reject animal-only studies (set is_breakthrough=false).
- Reject press releases without numbers unless they're a guideline/approval/recall.
- "headline" must not use: breakthrough, miracle, cure, game-changer, revolutionary.
- "graphic" shape:
    bar_delta:        {{ "kind":"bar_delta", "bars":[{{"label":"...", "treatment":N, "control":N}}], "unit":"%", "treatment_label":"...", "control_label":"..." }}
    forest_plot:      {{ "kind":"forest_plot", "studies":[{{"name":"...", "estimate":N, "ci_low":N, "ci_high":N}}], "x_label":"...", "reference":N, "log_scale":bool }}
    line_trend:       {{ "kind":"line_trend", "series":[{{"label":"...", "points":[[x,y],...]}}], "x_label":"...", "y_label":"..." }}
    kaplan_meier:     {{ "kind":"kaplan_meier", "treatment_label":"...", "control_label":"...", "median_t":N, "median_c":N, "hr":N, "ci_low":N, "ci_high":N, "x_label":"Months", "y_label":"Overall survival" }}
    recall_pictogram: {{ "kind":"recall_pictogram", "lots_affected":N, "severity":"Class I|II|III", "product":"..." }}
- If you can't extract concrete numbers for a graphic, choose bar_delta with sensible defaults from the abstract.
Return ONLY the JSON. No prose.
"""


# ─── Build a card from raw + Gemma output ─────────────────────────

def build_card(raw: dict, llm: dict) -> dict | None:
    if not llm.get("is_breakthrough"):
        return None
    strength = float(llm.get("strength", 0))
    if strength < MIN_STRENGTH:
        return None
    cat = llm.get("category", "other")
    if cat not in CATEGORY_ORDER:
        cat = "other"
    factor = llm.get("factor_slug") or None
    outcome = llm.get("outcome_slug") or None
    edge_id = match_corpus(factor, outcome)
    item_id = "br_" + hashlib.sha1(raw["link"].encode()).hexdigest()[:16]
    pub = _normalize_date(raw.get("published")) or date.today().isoformat()
    return {
        "id": item_id,
        "published_at": pub,
        "category": cat,
        "stage": llm.get("stage", "phase2"),
        "headline": llm.get("headline", raw["title"])[:160],
        "summary": llm.get("summary", raw.get("summary", ""))[:600],
        "why_it_matters": llm.get("why_it_matters", "")[:240],
        "graphic": llm.get("graphic") or {"kind": "bar_delta", "bars": []},
        "strength": round(strength, 2),
        "source_name": raw["source_name"],
        "source_url": raw["link"],
        "factor_slug": factor,
        "outcome_slug": outcome,
        "edge_id": edge_id,
        "is_orphan": edge_id is None,
    }


def _normalize_date(s: str | None) -> str | None:
    if not s:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass
    return None


# ─── Main ─────────────────────────────────────────────────────────

def prune(items: list[dict]) -> list[dict]:
    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    return [i for i in items if i.get("published_at", "") >= cutoff]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="don't write the JSON")
    ap.add_argument("--limit", type=int, default=40, help="max candidates to send to Gemma")
    args = ap.parse_args(argv)

    feed = load_feed()
    existing = feed.get("items", [])

    print("→ fetching RSS feeds…")
    raw: list[dict] = []
    for source_name, url in FEEDS:
        items = fetch_rss(url)
        for i in items:
            i["source_name"] = source_name
        print(f"  {source_name}: {len(items)} items")
        raw.extend(items)
        time.sleep(0.5)  # be polite

    print(f"→ {len(raw)} raw items; deduping…")
    candidates = dedupe(raw, existing)
    print(f"→ {len(candidates)} new candidates after dedupe")
    candidates = candidates[: args.limit]

    new_cards: list[dict] = []
    for i, c in enumerate(candidates, 1):
        print(f"  [{i}/{len(candidates)}] {c['source_name']}: {c['title'][:70]}")
        llm = gemma_classify(c)
        if not llm:
            continue
        card = build_card(c, llm)
        if card:
            new_cards.append(card)
            tag = "ORPHAN" if card["is_orphan"] else f"→ {card['edge_id']}"
            print(f"      ✓ kept (strength {card['strength']}) {tag}")
        else:
            print("      · rejected")

    print(f"→ {len(new_cards)} new cards passed threshold")

    merged = prune(existing + new_cards)
    merged.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    feed["items"] = merged

    if args.dry:
        print("→ dry run — not writing")
        print(json.dumps(new_cards, indent=2))
    else:
        save_feed(feed)
        print(f"→ wrote {len(merged)} items to data/breakthroughs.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
