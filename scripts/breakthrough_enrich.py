#!/usr/bin/env python3
"""Breakthrough detail enrichment (17.10.2026).

Why this exists: the daily job wrote each card from the RSS title plus a
≤500-char teaser — often one sentence ("European regulators have recommended
the approval of Revolution Medicines' Rasonque…"). The detail page therefore
had two sentences and no drug name, and 72 of 77 charts carried numbers that
appeared nowhere in what the model had read ("sensible defaults").

This step gives the model real material and then checks it mechanically:
  1. Source text — the linked page (journal abstract meta, JSON-LD body,
     article paragraphs), or the PubMed abstract for PubMed / DOI links.
  2. Background — up to 3 PubMed abstracts found for the named intervention
     and condition (paywalled news like STAT+ yields only a teaser).
  3. One local-LLM call writes the detail block: intervention, longer summary,
     key findings, study design, regulatory status, caveats, next steps,
     who it applies to, and a chart only if the numbers are reported.
  4. Grounding: every number in every field and in the chart must appear in
     the text the model was given; an abstract counts only if it names the
     intervention. Ungrounded sentences are dropped, an ungrounded chart is
     dropped (the page then shows no chart rather than an invented one).

Usage:
  python scripts/breakthrough_enrich.py --all            # backfill every card
  python scripts/breakthrough_enrich.py --missing        # only cards without detail
  python scripts/breakthrough_enrich.py --id br_xxx --dry
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.breakthroughs import load_feed, save_feed  # noqa: E402

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:30b-instruct")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SOURCE_CAP = 6000
ABSTRACT_CAP = 2200

# ─── Source text ──────────────────────────────────────────────────

_BOILER = re.compile(
    r"(cookie|subscribe|sign up|newsletter|log in|all rights reserved|copyright|"
    r"privacy policy|terms of use|advertis|you can reach|covers biotech|"
    r"want to stay on top|share this article|javascript)", re.I)


def _get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(3_000_000).decode("utf-8", "replace")


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


def _metas(page: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for tag in re.findall(r"<meta\b[^>]*>", page, re.I):
        k = re.search(r'(?:name|property)\s*=\s*["\']([^"\']+)', tag, re.I)
        v = re.search(r'content\s*=\s*"([^"]*)"', tag, re.I) or \
            re.search(r"content\s*=\s*'([^']*)'", tag, re.I)
        if k and v:
            out.setdefault(k.group(1).lower(), []).append(_clean(v.group(1)))
    return out


def extract_text(page: str) -> tuple[str, str | None]:
    """Readable text of an article page + its DOI if the page declares one."""
    m = _metas(page)
    doi = (m.get("citation_doi") or m.get("dc.identifier") or [None])[0]
    if doi and not doi.startswith("10."):
        doi = (re.search(r"10\.\d{4,}/\S+", doi) or [None])[0]
    chunks: list[str] = []
    for key in ("citation_abstract", "dc.description", "og:description", "description"):
        for v in m.get(key, []):
            if len(v) > 60 and v not in chunks:
                chunks.append(v)
    for blob in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        for body in re.findall(r'"(?:articleBody|abstract)"\s*:\s*"((?:[^"\\]|\\.)*)"', blob):
            try:
                body = json.loads(f'"{body}"')
            except Exception:
                pass
            body = _clean(body)
            if len(body) > 200:
                chunks.append(body)
    scope = page
    art = re.search(r"<article\b.*?</article>", page, re.S | re.I)
    if art and len(art.group(0)) > 2000:
        scope = art.group(0)
    scope = re.sub(r"<(script|style|nav|footer|header|aside)\b.*?</\1>", " ", scope, flags=re.S | re.I)
    for p in re.findall(r"<p\b[^>]*>(.*?)</p>", scope, re.S | re.I):
        t = _clean(p)
        if len(t) >= 80 and not _BOILER.search(t) and t not in chunks:
            chunks.append(t)
    text = "\n".join(chunks)
    return text[:SOURCE_CAP], doi


def _pubmed_id(url: str) -> str | None:
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url)
    return m.group(1) if m else None


def ctgov_text(nct: str) -> tuple[str, dict]:
    """ClinicalTrials.gov renders with JS; its v2 API has the registry record."""
    try:
        d = json.loads(_get(f"https://clinicaltrials.gov/api/v2/studies/{nct}", timeout=20))
    except Exception as e:
        print(f"    · ctgov fetch failed: {e}", file=sys.stderr)
        return "", {"kind": "ctgov"}
    p = d.get("protocolSection", {})
    idm, st, de = p.get("identificationModule", {}), p.get("statusModule", {}), p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {}).get("armGroups", [])
    outs = p.get("outcomesModule", {}).get("primaryOutcomes", [])
    lines = [idm.get("officialTitle") or idm.get("briefTitle", ""),
             f"Registry {nct}. Status: {st.get('overallStatus', '')}. Results posted: {'yes' if d.get('hasResults') else 'no'}.",
             f"Design: {de.get('studyType', '')}, phase {', '.join(de.get('phases', []))}, "
             f"{de.get('designInfo', {}).get('allocation', '')}, "
             f"masking {de.get('designInfo', {}).get('maskingInfo', {}).get('masking', '')}. "
             f"Planned enrollment: {de.get('enrollmentInfo', {}).get('count', '')}.",
             p.get("descriptionModule", {}).get("briefSummary", "")]
    lines += [f"Arm: {a.get('label', '')} — {a.get('description', '')}" for a in arms[:4]]
    lines += [f"Primary outcome: {o.get('measure', '')} ({o.get('timeFrame', '')})" for o in outs[:3]]
    return "\n".join(x for x in lines if x)[:SOURCE_CAP], {
        "kind": "ctgov", "has_results": bool(d.get("hasResults")),
        "status": st.get("overallStatus", "")}


def source_text(url: str) -> tuple[str, dict]:
    """Best readable text for the card's source link ('' if unreachable) + meta."""
    clean_url = re.sub(r"[?&]utm_[^&]+", "", url)
    nct = re.search(r"clinicaltrials\.gov/(?:study|ct2/show)/(NCT\d{8})", clean_url)
    if nct:
        return ctgov_text(nct.group(1))
    pmid = _pubmed_id(clean_url)
    if pmid:
        ab = pubmed_fetch([pmid])
        return ((ab[0]["title"] + "\n" + ab[0]["abstract"])[:SOURCE_CAP] if ab else ""), {"kind": "pubmed"}
    bmj = re.search(r"bmj\.com/content/\d+/(bmj-\d{4}-\d+)", clean_url)
    if bmj:   # BMJ answers scripts with 403; its DOI is in the URL
        ab = pubmed_fetch(pubmed_search(f'"10.1136/{bmj.group(1)}"[AID]', retmax=1))
        if ab and ab[0]["abstract"]:
            return (ab[0]["title"] + "\n" + ab[0]["abstract"])[:SOURCE_CAP], {"kind": "pubmed"}
    try:
        page = _get(clean_url)
    except Exception as e:
        print(f"    · source fetch failed: {e}", file=sys.stderr)
        return "", {"kind": "blocked"}
    text, doi = extract_text(page)
    if doi and len(text) < 1200:
        # Journals behind Cloudflare/paywalls: the DOI still finds the abstract.
        ids = pubmed_search(f'"{doi}"[AID]', retmax=1)
        ab = pubmed_fetch(ids)
        if ab and ab[0]["abstract"]:
            text = (text + "\n" + ab[0]["title"] + "\n" + ab[0]["abstract"]).strip()
    return text[:SOURCE_CAP], {"kind": "page"}


# JAMA/BMJ answer scripts with 403: find the article on PubMed instead, by
# journal + intervention + condition + publication window, best title match.
JOURNAL_TA = {"JAMA": "JAMA", "BMJ": "BMJ", "NEJM": "N Engl J Med", "Lancet": "Lancet",
              "Nature Medicine": "Nat Med", "Cell": "Cell", "JACC": "J Am Coll Cardiol",
              "Circulation": "Circulation", "JCO": "J Clin Oncol", "Lancet Oncology": "Lancet Oncol"}


def _words(s: str) -> set[str]:
    return {w[:6] for w in re.findall(r"[a-z][a-z-]{3,}", (s or "").lower()) if w not in _STOP}


def journal_lookup(item: dict, ident: dict) -> dict | None:
    ta = JOURNAL_TA.get(item.get("source_name", ""))
    if not ta:
        return None
    terms = [t for t in (ident.get("intervention"), ident.get("condition")) if t]
    if not terms:
        return None
    pub = item.get("published_at", "")
    try:
        d0 = date.fromisoformat(pub)
    except ValueError:
        return None
    from datetime import timedelta
    mind, maxd = (d0 - timedelta(days=75)).strftime("%Y/%m/%d"), (d0 + timedelta(days=30)).strftime("%Y/%m/%d")
    q = f'"{ta}"[ta] AND ' + " AND ".join(f"({t})" for t in terms)
    ids = []
    for term in (q, f'"{ta}"[ta] AND ({terms[-1]})'):
        raw = _eutils("esearch.fcgi", {"db": "pubmed", "term": term, "retmax": 15, "retmode": "json",
                                       "datetype": "edat", "mindate": mind, "maxdate": maxd})
        try:
            ids += [i for i in json.loads(raw)["esearchresult"]["idlist"] if i not in ids]
        except Exception:
            pass
        if len(ids) >= 5:
            break
    want = _words(item.get("headline", "") + " " + item.get("summary", "") + " " + " ".join(terms))
    best, best_score = None, 0.0
    for a in pubmed_fetch(ids[:20]):
        if not a["abstract"]:
            continue
        tw = _words(a["title"])
        score = len(tw & want) / max(len(tw), 1)
        if score > best_score:
            best, best_score = a, score
    return best if best and best_score >= 0.34 else None


# ─── PubMed background ────────────────────────────────────────────

def _eutils(path: str, params: dict) -> str:
    key = os.getenv("NCBI_API_KEY", "").strip()
    if key:
        params = {**params, "api_key": key}
    url = f"{EUTILS}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(3):
        try:
            out = _get(url, timeout=30)
            time.sleep(0.4)
            return out
        except Exception as e:
            print(f"    · eutils {path} retry {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(1.5 * (attempt + 1))
    return ""


def pubmed_search(term: str, retmax: int = 3) -> list[str]:
    raw = _eutils("esearch.fcgi", {"db": "pubmed", "term": term, "retmax": retmax,
                                   "retmode": "json", "sort": "relevance"})
    try:
        return json.loads(raw)["esearchresult"]["idlist"]
    except Exception:
        return []


def pubmed_fetch(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    raw = _eutils("efetch.fcgi", {"db": "pubmed", "id": ",".join(pmids),
                                  "rettype": "abstract", "retmode": "xml"})
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    out = []
    for art in root.findall(".//PubmedArticle"):
        def txt(path: str) -> str:
            el = art.find(path)
            return "".join(el.itertext()).strip() if el is not None else ""
        parts = []
        for seg in art.findall(".//Abstract/AbstractText"):
            label = seg.attrib.get("Label")
            parts.append((f"{label}: " if label else "") + "".join(seg.itertext()).strip())
        year = txt(".//PubDate/Year") or txt(".//PubDate/MedlineDate")[:4]
        out.append({"pmid": txt(".//PMID"), "title": txt(".//ArticleTitle"),
                    "journal": txt(".//Journal/Title"), "year": year,
                    "abstract": "\n".join(p for p in parts if p)})
    return out


_GENERIC = {"therapy", "treatment", "cancer", "drug", "disease", "patients", "trial",
            "study", "inhibitor", "vaccine", "program", "exercise", "intervention",
            "combination", "with", "plus", "and", "the", "new", "oral", "injection",
            "tablets", "capsules", "dose", "chronic", "acute", "advanced", "receptor"}


def name_tokens(intervention: str) -> list[str]:
    toks = re.findall(r"[A-Za-z][A-Za-z0-9-]{4,}", intervention or "")
    return [t.lower() for t in toks if t.lower() not in _GENERIC]


_DICT: set[str] | None = None


def _dictionary() -> set[str]:
    global _DICT
    if _DICT is None:
        try:
            _DICT = {w.strip().lower() for w in open("/usr/share/dict/words", encoding="utf-8", errors="ignore")}
        except OSError:
            _DICT = set()
    return _DICT


def specific_tokens(intervention: str, aliases: list[str]) -> list[str]:
    """Names that pin down ONE product: FDA-label names, development codes
    (ARO-MAPT, RMC-6236) and words absent from an English dictionary
    (daraxonrasib). "occupational therapy" or "nicotine" pin down a topic,
    and a topic search found an unrelated 2024 trial for a guideline card."""
    out = [a.lower() for a in aliases if a]
    for m in re.findall(r"\b[A-Za-z]{1,6}-?\d{2,7}\b|\b[A-Z]{2,6}-[A-Z0-9]{2,8}\b", intervention or ""):
        out.append(m.lower())
    words = _dictionary()
    if words:
        def english(t: str) -> bool:   # personalized → personal(ize), vaccines → vaccine
            return any(t[:k] in words for k in range(max(5, len(t) - 4), len(t) + 1))
        out += [t for t in name_tokens(intervention)
                if len(t) >= 7 and not english(t) and not t.endswith("-based")]
    return list(dict.fromkeys(out))


def related(query: str | None, condition: str) -> list[dict]:
    """Topic-level reading for the page — links only, never grounding."""
    if not query:
        return []
    cond = name_tokens(condition)
    out = []
    for a in pubmed_fetch(pubmed_search(query, retmax=4)):
        if not cond or any(c in (a["title"] + " " + a["abstract"]).lower() for c in cond):
            out.append({"pmid": a["pmid"], "title": a["title"], "journal": a["journal"], "year": a["year"],
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/"})
    return out[:3]


def background(intervention: str, condition: str, query: str | None,
               aliases: list[str] | None = None) -> list[dict]:
    """Up to 3 PubMed abstracts that name the intervention (or a known alias)
    and the condition. Aliases only widen the search; an abstract is kept only
    if it names one of them AND the condition, so a wrong alias finds nothing."""
    toks = specific_tokens(intervention, [a for a in (aliases or []) if isinstance(a, str)])
    if not toks:
        return []
    cond = [t for t in name_tokens(condition)] or [w.lower() for w in re.findall(r"[A-Za-z]{5,}", condition or "")]
    or_names = " OR ".join(f'"{t}"[Title/Abstract]' for t in toks[:5])
    base = f"({or_names}) AND ({condition})" if condition else f"({or_names})"
    terms = [f"{base} AND (clinical trial[pt] OR randomized[tiab] OR phase[tiab])", base]
    if query:
        terms.append(query)
    seen: list[str] = []
    for t in terms:
        for pmid in pubmed_search(t, retmax=5):
            if pmid not in seen:
                seen.append(pmid)
        if len(seen) >= 5:
            break
    keep = []
    for a in pubmed_fetch(seen[:6]):
        body = (a["title"] + " " + a["abstract"]).lower()
        if a["abstract"] and any(t in body for t in toks) and (not cond or any(c in body for c in cond)):
            keep.append(a)
    return keep[:3]


# ─── FDA label (openFDA, free, no key) ────────────────────────────
# The local model does not know 2026 brand names (it guessed "RSM-1236" for
# Rasonque); the FDA label maps brand ↔ generic deterministically and states
# the approved indication and boxed warning in the regulator's own words.

def fda_label(intervention: str) -> dict | None:
    need = specific_tokens(intervention, [])
    if not need:
        return None
    cands = [intervention] + need
    for c in dict.fromkeys(x.strip() for x in cands if x and len(x.strip()) >= 4):
        for field in ("openfda.brand_name", "openfda.generic_name"):
            q = urllib.parse.quote(f'{field}:"{c}"')
            try:
                d = json.loads(_get(f"https://api.fda.gov/drug/label.json?search={q}&limit=1", timeout=15))
            except Exception:
                continue
            r = (d.get("results") or [None])[0]
            if not r:
                continue
            of = r.get("openfda", {})
            names = " ".join(x.lower() for x in (of.get("brand_name", []) + of.get("generic_name", [])))
            if not all(t in names for t in need):
                # Every specific name must be on the label: "Influenza" (homeopathic)
                # is not baloxavir, an acetaminophen label is not acetaminophen+naproxen.
                continue
            def first(k):
                v = r.get(k) or [""]
                return re.sub(r"\s+", " ", v[0])[:1200]
            return {"brand": (of.get("brand_name") or [""])[0].title(),
                    "generic": (of.get("generic_name") or [""])[0].lower(),
                    "manufacturer": (of.get("manufacturer_name") or [""])[0],
                    "indications": first("indications_and_usage"),
                    "boxed_warning": first("boxed_warning"),
                    "url": f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={urllib.parse.quote(c)}"}
    return None


# ─── LLM ──────────────────────────────────────────────────────────

def ollama_json(prompt: str, num_predict: int = 1400) -> dict | None:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
               "format": "json", "options": {"temperature": 0.1, "num_predict": num_predict,
                                              "num_ctx": 12288}}
    try:
        req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            text = json.loads(r.read()).get("response", "")
    except Exception as e:
        print(f"    ✗ ollama failed: {e}", file=sys.stderr)
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            return None


_IDENTIFY = """Identify what this health-news item is about. Use only the text below.

headline: {headline}
teaser:   {teaser}
source text:
{source}

Return JSON only:
{{"intervention": "the specific drug/test/procedure/behaviour by name as written in the text (brand and generic if both appear), or '' if none is named",
  "condition": "the disease or outcome, short",
  "pubmed_query": "a short PubMed query (2-6 terms) that would find the main trial or study of this intervention for this condition"}}"""


_DETAIL = """You are writing the detail page for a health-news card on an audited evidence site.
Readers are curious non-specialists. Be specific and plain. Use ONLY facts and numbers stated in
the SOURCE or the BACKGROUND ABSTRACTS below. Never invent numbers, trial names, dates or results.
If something is not stated, leave the field empty ("" or []). Background abstracts may be earlier
trials of the same intervention — say so when you use them (e.g. "In the earlier phase 3 trial…").

CARD
headline: {headline}
category/stage: {category} / {stage}
card summary: {summary}

SOURCE ({source_name}, {source_url})
{source}

{label}
BACKGROUND ABSTRACTS (PubMed)
{abstracts}

Return JSON only, with these keys:
{{
 "intervention": "name of the drug/test/procedure/behaviour as in the text, '' if not named",
 "summary": "3-5 sentences: what happened, what was tested in whom, what was found",
 "key_findings": ["up to 5 short bullets, each one concrete result with its numbers"],
 "study": {{"trial_name": "", "design": "e.g. randomized phase 3, double-blind", "participants": "how many, who",
            "comparator": "", "primary_endpoint": "", "follow_up": ""}},
 "regulatory_status": "where it stands with FDA/EMA/guidelines, '' if not stated",
 "caveats": ["up to 4 honest limitations: early phase, surrogate endpoint, small n, side effects, cost, industry funding…"],
 "next_steps": "what happens next (decision, launch, further trials), '' if not stated",
 "who_it_applies_to": "which patients/people this is relevant for",
 "evidence_pmids": ["PMIDs of the background abstracts you actually used"],
 "graphic": null or one of:
    {{"kind":"bar_delta","bars":[{{"label":"...","treatment":N,"control":N}}],"unit":"% or months or ...","treatment_label":"...","control_label":"..."}}
    {{"kind":"kaplan_meier","treatment_label":"...","control_label":"...","median_t":N,"median_c":N,"hr":N,"ci_low":N,"ci_high":N,"x_label":"Months","y_label":"..."}}
    {{"kind":"forest_plot","studies":[{{"name":"...","estimate":N,"ci_low":N,"ci_high":N}}],"x_label":"...","reference":1,"log_scale":true}}
    {{"kind":"recall_pictogram","lots_affected":N,"severity":"Class I|II|III","product":"..."}}
}}
Use a graphic ONLY when the text reports the exact numbers for both arms (or the estimate and CI).
Otherwise "graphic": null.
Also return "source_match": true|false — false if the SOURCE ARTICLE FOUND ON PUBMED (if any) is a different study.
"study" describes the card's own study only, never a background abstract's.
If the source is short, leave fields empty rather than filling them with what such studies usually do
(no guessed settings, sites, delivery details, follow-up lengths or funding)."""


# ─── Grounding ────────────────────────────────────────────────────

_STOP = set("""this that these those with from than then they them their there were was been being have has had
which while where when what whom whose into onto over under about after before between among within without
also such more most less least very much many some only other another each both either neither same just
could would should might must shall will can may does doing done make made makes based using used use uses
patients patient people adults study studies trial trials data result results finding findings effect effects
report reports reported showed shows show suggest suggests suggested include includes included including
compared compare compares versus group groups participants new treatment treatments therapy therapies
however although because therefore thus overall significant significantly associated association risk risks
first second third year years month months week weeks days time further additional larger longer long term
potential potentially likely possible possibly need needed needs confirm confirmed evidence approach
benefit benefits improved improve improves reduce reduced reduces increase increased increases lower higher
general specific certain important key main primary secondary outcome outcomes endpoint endpoints""".split())


def _support(text: str, corpus_words: set[str]) -> float:
    w = _words(text)
    return 1.0 if not w else len(w & corpus_words) / len(w)

def _nums(s: str) -> set[str]:
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s or "")
    out = set()
    for n in re.findall(r"\d+(?:\.\d+)?", s):
        out.add(n)
        if "." in n:
            out.add(n.rstrip("0").rstrip("."))
    return out


def _gnums(g) -> set[str]:
    out: set[str] = set()
    def walk(x, key=""):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            if key == "reference":
                return
            out.add(f"{x:g}")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
    walk(g)
    return out


def _grounded(text: str, corpus: set[str]) -> bool:
    return not (_nums(text) - corpus)


def _valid_graphic(g) -> bool:
    if not isinstance(g, dict):
        return False
    k = g.get("kind")
    try:
        if k == "bar_delta":
            bars = g.get("bars") or []
            return bool(bars) and all(isinstance(b.get("treatment"), (int, float)) and
                                      isinstance(b.get("control"), (int, float)) for b in bars)
        if k == "kaplan_meier":
            return all(isinstance(g.get(x), (int, float)) and g.get(x) > 0 for x in ("median_t", "median_c"))
        if k == "forest_plot":
            st = g.get("studies") or []
            return bool(st) and all(all(isinstance(s.get(x), (int, float)) for x in ("estimate", "ci_low", "ci_high")) for s in st)
        if k == "recall_pictogram":
            return bool(g.get("product"))
    except Exception:
        return False
    return False


def ground_detail(d: dict, corpus_text: str) -> tuple[dict, dict | None, list[str]]:
    """Drop every sentence/field whose numbers are not in corpus_text.
    Returns (clean_detail, grounded_graphic_or_None, dropped_reasons)."""
    corpus = _nums(corpus_text)
    cwords = _words(corpus_text)
    dropped: list[str] = []

    # Numbers must be in the sources. Words too: a factual line whose content
    # words are mostly absent from the sources ("single academic medical
    # center", "trained physiotherapists") is the model filling a thin source.
    def s(v, name, need=0.6):
        v = (v or "").strip() if isinstance(v, str) else ""
        if v and not _grounded(v, corpus):
            dropped.append(f"{name}: {', '.join(sorted(_nums(v) - corpus))}")
            return ""
        if v and _support(v, cwords) < need:
            dropped.append(f"{name}: unsupported wording ({_support(v, cwords):.2f})")
            return ""
        return v

    def lst(v, name, cap, need=0.6):
        out = []
        for x in (v or [])[:cap]:
            x = s(x, name, need) if isinstance(x, str) else ""
            if x:
                out.append(x)
        return out

    summary = d.get("summary") or ""
    # Summary is split into sentences so one bad number does not drop it all.
    sentences = re.split(r"(?<=[.!?])\s+", summary.strip())
    summary = " ".join(x for x in (s(x, "summary") for x in sentences) if x)

    study_in = d.get("study") if isinstance(d.get("study"), dict) else {}
    study = {k: s(study_in.get(k), f"study.{k}") for k in
             ("trial_name", "design", "participants", "comparator", "primary_endpoint", "follow_up")}
    clean = {
        "intervention": s(d.get("intervention"), "intervention"),
        "summary": summary,
        "key_findings": lst(d.get("key_findings"), "finding", 5),
        "study": {k: v for k, v in study.items() if v},
        "regulatory_status": s(d.get("regulatory_status"), "regulatory_status"),
        "caveats": lst(d.get("caveats"), "caveat", 4, need=0.5),
        "next_steps": s(d.get("next_steps"), "next_steps", need=0.5),
        "who_it_applies_to": s(d.get("who_it_applies_to"), "who_it_applies_to", need=0.5),
    }
    g = d.get("graphic")
    if g is not None:
        if isinstance(g, dict) and g.get("kind") == "kaplan_meier":
            # HR/CI are optional on the curve: drop just the ungrounded ones.
            def bad(k):
                v = g.get(k)
                return v is not None and (not isinstance(v, (int, float)) or bool(_gnums(v) - corpus))
            drop = set()
            if bad("hr"):
                drop |= {"hr", "ci_low", "ci_high"}
            elif bad("ci_low") or bad("ci_high"):
                drop |= {"ci_low", "ci_high"}
            if drop:
                dropped.append(f"graphic: {', '.join(sorted(drop))}")
                g = {k: v for k, v in g.items() if k not in drop}
        if not _valid_graphic(g):
            dropped.append("graphic: malformed")
            g = None
        elif _gnums(g) - corpus:
            dropped.append(f"graphic: {', '.join(sorted(_gnums(g) - corpus))}")
            g = None
    return clean, g, dropped


# ─── Orchestration ────────────────────────────────────────────────

def enrich(item: dict, teaser: str = "") -> dict:
    """Return a copy of the card with `detail` filled and `graphic` grounded."""
    src, meta = source_text(item.get("source_url", ""))
    ident = ollama_json(_IDENTIFY.format(headline=item["headline"], teaser=teaser or item.get("summary", ""),
                                         source=src[:3000] or "(unavailable)"), num_predict=200) or {}
    found = journal_lookup(item, ident) if len(src) < 1200 else None
    found_txt = (f"[PMID {found['pmid']}] {found['title']} ({found['journal']}, {found['year']})\n"
                 f"{found['abstract'][:SOURCE_CAP]}") if found else ""
    label = (fda_label(ident.get("intervention", ""))
             if ident.get("intervention") and item.get("stage") in ("approved", "recall", "guideline") else None)
    aliases = [label["generic"], label["brand"]] if label else []
    bg = background(ident.get("intervention", ""), ident.get("condition", ""),
                    ident.get("pubmed_query"), aliases)
    if found:
        bg = [a for a in bg if a["pmid"] != found["pmid"]]
    rel = [] if bg else related(ident.get("pubmed_query"), ident.get("condition", ""))
    label_txt = ""
    if label:
        label_txt = (f"FDA label — {label['brand']} ({label['generic']}), {label['manufacturer']}.\n"
                     f"Indication: {label['indications']}\n"
                     + (f"Boxed warning: {label['boxed_warning']}\n" if label["boxed_warning"] else ""))
    abstracts = "\n\n".join(f"[PMID {a['pmid']}] {a['title']} ({a['journal']}, {a['year']})\n"
                            f"{a['abstract'][:ABSTRACT_CAP]}" for a in bg) or "(none found)"
    source_block = src or teaser or item.get("summary", "")
    if found_txt:
        source_block += ("\n\nSOURCE ARTICLE FOUND ON PUBMED (matched by journal, topic and date — set "
                         "\"source_match\": false if it is NOT the study this card is about):\n" + found_txt)
    if meta.get("kind") == "ctgov" and not meta.get("has_results"):
        source_block += "\n\nNOTE: this is a trial registration; no results have been posted."
    raw = ollama_json(_DETAIL.format(
        headline=item["headline"], category=item.get("category"), stage=item.get("stage"),
        summary=item.get("summary", ""), source_name=item.get("source_name"),
        source_url=item.get("source_url"), source=source_block,
        label=label_txt, abstracts=abstracts))
    out = dict(item)
    if not raw:
        return out
    matched = found if (found and raw.get("source_match") is not False) else None
    used = [str(p) for p in (raw.get("evidence_pmids") or []) if str(p) in {a["pmid"] for a in bg}]
    used_abs = ([matched] if matched else []) + [a for a in bg if a["pmid"] in used]
    corpus = " ".join([item.get("headline", ""), item.get("summary", ""), teaser, src, label_txt] +
                      [a["title"] + " " + a["abstract"] for a in used_abs])
    detail, graphic, dropped = ground_detail(raw, corpus)
    detail["evidence"] = [{"pmid": a["pmid"], "title": a["title"], "journal": a["journal"],
                           "year": a["year"], "url": f"https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/",
                           **({"is_source": True} if a is matched else {})}
                          for a in used_abs]
    if label:
        detail["fda_label"] = {k: label[k] for k in ("brand", "generic", "url")}
    known = {e["pmid"] for e in detail["evidence"]}
    if rel:
        detail["related"] = [r for r in rel if r["pmid"] not in known]
    if meta.get("kind") == "ctgov" and not meta.get("has_results"):
        # A registration is not a finding: say so on the page and keep the
        # card out of the general feed (its headline claimed a result).
        detail["no_results"] = True
        detail["registry_status"] = meta.get("status", "")
        out["audience"] = "technical"
    detail["source_chars"] = len(src) + len(found_txt if matched else "")
    detail["enriched_at"] = date.today().isoformat()
    detail["model"] = OLLAMA_MODEL
    if dropped:
        detail["dropped"] = dropped
    out["detail"] = detail
    out["graphic"] = graphic
    return out


def _save_one(card: dict) -> None:
    """Re-read the feed and replace this card only, so a concurrent daily run
    that appended items is not overwritten."""
    feed = load_feed()
    feed["items"] = [card if i["id"] == card["id"] else i for i in feed.get("items", [])]
    save_feed(feed)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--missing", action="store_true")
    g.add_argument("--id", action="append")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    items = load_feed().get("items", [])
    if args.id:
        items = [i for i in items if i["id"] in args.id]
    elif args.missing:
        items = [i for i in items if not i.get("detail")]
    if args.limit:
        items = items[: args.limit]
    print(f"→ enriching {len(items)} cards with {OLLAMA_MODEL}")
    for n, it in enumerate(items, 1):
        t0 = time.time()
        print(f"[{n}/{len(items)}] {it['id']} {it['headline'][:70]}", flush=True)
        card = enrich(it)
        d = card.get("detail") or {}
        print(f"    src {d.get('source_chars', 0)} chars · {len(d.get('evidence', []))} abstracts · "
              f"{len(d.get('key_findings', []))} findings · graphic "
              f"{(card.get('graphic') or {}).get('kind', 'none')} · dropped {len(d.get('dropped', []))} "
              f"· {time.time() - t0:.0f}s", flush=True)
        if args.dry:
            print(json.dumps({"detail": d, "graphic": card.get("graphic")}, indent=1, ensure_ascii=False))
        elif d:
            _save_one(card)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
