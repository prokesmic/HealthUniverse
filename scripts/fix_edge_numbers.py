#!/usr/bin/env python3
"""Make every number on an edge page traceable to its sources (18.10.2026).

scripts/edge_audit.py found ~520 edges whose summary / effect_quant /
mechanism / caveats / population carry numbers that appear in none of the
edge's own evidence (abstracts, titles, citations, notes, years) — mostly the
original Claude seeds and the Codex batches: often close to a real paper
("RR 0.79, 95% CI 0.74–0.85" where the abstract says 0.73–0.85), sometimes
not. A reader cannot check either, so for each such field:

  1. the local model rewrites the field using ONLY numbers from the edge's
     abstracts (keeping the meaning; a figure it cannot source is dropped);
  2. the rewrite is kept only if (a) no material number is left that the
     sources lack, and (b) it adds no new wording — ≥85 % of its content words
     come from the old text or the abstracts;
  3. otherwise the sentences carrying unsourced numbers are removed
     deterministically (a field that would be left empty becomes NULL,
     except summary, which keeps its first number-free sentence or a neutral
     line).

Each changed field is written to edge_history (actor 'number_audit') with the
old value, so any edit can be reverted. Local model only.

  python scripts/fix_edge_numbers.py --dry --limit 8
  python scripts/fix_edge_numbers.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import edge_audit as ea  # noqa: E402
from breakthrough_enrich import ollama_json  # noqa: E402

FIELDS = ea.TEXT_FIELDS          # summary, effect_quant, mechanism, caveats, population
STOP = set("""this that these those with from than then they them their there were was been being have has
had which while where when what about after before between among within also such more most less very much many
some only other each both same just could would should might must will can may does done made based using used
shows show suggest suggests found finding findings study studies trial trials evidence data effect effects risk
associated association people adults patients higher lower increase increased decrease reduced reduce overall""".split())


def _connect():
    from db import connect  # type: ignore
    return connect()


def words(s: str) -> set[str]:
    return {w[:6] for w in re.findall(r"[a-z][a-z-]{3,}", (s or "").lower()) if w not in STOP}


def ungrounded(text: str, src_nums: set[str]) -> set[str]:
    return ea.material(ea.nums(text) - src_nums)


_ABBR = re.compile(r"(\b(vs|e\.g|i\.e|approx|ca|al|cf|incl)\.|\b[A-Z]\.)$")   # 'H. pylori', 'E. coli'



def sentences(text: str) -> list[str]:
    """Split on . ; ! ? — but not after 'vs.', 'e.g.', 'et al.' ('… vs. least sedentary' was cut in two)."""
    out, cur = [], ""
    for piece in re.split(r"(?<=[.;!?])\s+", (text or "").strip()):
        cur = f"{cur} {piece}".strip() if cur else piece
        # a ';' inside an open bracket does not end anything: "(cohorts; ages 18–85)"
        if not _ABBR.search(cur) and cur.count("(") <= cur.count(")"):
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def fragment(s: str) -> bool:
    s = s.strip()
    return len(s.split()) < 2 or (s[:1].islower() and len(s.split()) < 8)


# Brackets and em-dash asides only: an en dash is a range ("0.76–0.94"), and
# treating it as an aside cut "~13% lower (HR 0.87, 95% CI 0.76–0.94)" to rubble.
_ASIDE = re.compile(r"\s*(\([^()]*\)|—[^—]*—)")


def drop_asides(sentence: str, src_nums: set[str]) -> str:
    """'Eating nuts—roughly a small handful (28–30 g)—is linked…': lose the aside, keep the claim."""
    def repl(m):
        return " " if ungrounded(m.group(0), src_nums) else m.group(0)
    out = re.sub(r"\s{2,}", " ", _ASIDE.sub(repl, sentence)).strip()
    return re.sub(r"\s+([,.;:])", r"\1", out)


def strip_sentences(text: str, src_nums: set[str]) -> str:
    keep = []
    for p in sentences(text):
        if p and ungrounded(p, src_nums):
            p = drop_asides(p, src_nums)
        if p and not ungrounded(p, src_nums):
            keep.append(p)
    keep = [k[:1].upper() + k[1:] if k[:1].islower() else k for k in keep]
    out = " ".join(keep).strip().rstrip(";").strip()
    return "" if fragment(out) else out


def quoted(sentence: str, abstract_sents: list[tuple[set[str], set[str]]]) -> bool:
    """Every material number of this sentence sits in ONE abstract sentence that
    shares ≥2 content words with it — a real estimate, not a number borrowed
    from elsewhere ('15–25 % lower' became '25 % lower' on 18.10)."""
    need = ea.material(ea.nums(sentence))
    if not need:
        return True
    w = words(sentence)
    return any(need <= n and len(w & aw) >= 2 for n, aw in abstract_sents)


_REWRITE = """Rewrite this "{field}" text for a health-evidence page about "{pair}" so that every number in it
appears in the SOURCE ABSTRACTS below. Keep the meaning and the wording otherwise. Replace a figure with the
matching figure from an abstract only when it clearly describes the same estimate; otherwise remove the figure
(and words that only made sense with it). Do not add facts, studies, names or numbers that are not in the text
or the abstracts. Plain English, same length or shorter.

TEXT:
{text}

SOURCE ABSTRACTS:
{abstracts}

Return JSON only: {{"text": "the rewritten text"}}"""


def rewrite(field: str, pair: str, text: str, abstracts: str, src_nums: set[str], src_words: set[str]) -> tuple[str, str]:
    """(new_text, how) — how ∈ {'model', 'stripped'}."""
    if abstracts.strip():
        j = ollama_json(_REWRITE.format(field=field, pair=pair, text=text, abstracts=abstracts[:7000]),
                        num_predict=500) or {}
        new = (j.get("text") or "").strip()
        asents = [(ea.nums(x), words(x)) for x in re.split(r"(?<=[.;!?])\s+", abstracts)]
        if new and not ungrounded(new, src_nums) and all(quoted(x, asents) for x in sentences(new)) \
                and not fragment(new):
            allowed = words(text) | src_words
            w = words(new)
            if not w or len(w & allowed) / len(w) >= 0.85:
                return new, "model"
    return strip_sentences(text, src_nums), "stripped"


# Abbreviations case-sensitive: "or =2 to <4 h/d" is the word "or", not an odds ratio.
_EST = re.compile(r"(?:\b(?:RR|HR|OR|SRR|aHR|aOR)\b|\b(?i:relative risk|hazard ratio|odds ratio|risk ratio)\b)"
                  r"[^.;]{0,25}?(\d+\.\d+)[^.;]{0,60}?\bCI\b[^.;]{0,40}?\d+\.\d+\s*(?:[-–,]|to)\s*\d+\.\d+\)?")
_RANK = {"meta_analysis": 0, "systematic_review": 1, "rct": 2, "cohort": 3}


def estimate_quote(evidence: list, cache: dict, direction: str, f_name: str = "", o_name: str = "") -> str | None:
    """A verbatim RR/HR/OR + CI clause from the strongest study's abstract, in the
    edge's direction — grounded by construction, labelled with its source."""
    for r in sorted(evidence, key=lambda r: _RANK.get(r["study_type"] or "", 9)):
        ab = cache.get(r["pmid"] or "", {}).get("abstract", "")
        fw, ow = words(f_name), words(o_name)
        if fw and not (fw & words(ab)):
            continue          # an abstract that never names the factor is a mis-attached paper (18.10: alcohol ← brain health)
        for m in _EST.finditer(ab):
            sent = ab[ab.rfind(".", 0, m.start()) + 1: ab.find(".", m.end()) if ab.find(".", m.end()) > 0 else len(ab)]
            if (fw or ow) and not (words(sent) & (fw | ow)):
                continue      # the estimate must be about this factor or outcome
            v = float(m.group(1))
            if (direction == "protective" and v >= 1) or (direction == "harmful" and v <= 1):
                continue
            q = re.sub(r"\s+", " ", m.group(0)).strip()
            q = re.sub(r"^(\w+)\]", r"\1", q)        # "RR] = 1.06" — bracket from "[RR]" in the abstract
            while q.count(")") > q.count("("):
                q = q[: q.rindex(")")] + q[q.rindex(")") + 1:]
            while q.count("(") > q.count(")"):
                q += ")"
            if len(q) <= 180:
                cite = (r["citation"] or "").split(" et al")[0].strip()
                if not cite or len(cite.split()) > 4:          # citation is a title, not "Author …"
                    cite = f"PMID {r['pmid']}"
                year = r["year"] or ""
                return f"{q} ({cite}{' ' + str(year) if year else ''})"
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--edge", type=int, action="append")
    a = ap.parse_args(argv)
    cache = ea.load_cache()
    st = Counter()
    with _connect() as conn:
        edges = conn.execute(f"""SELECT e.id, e.direction, {', '.join('e.' + f for f in FIELDS)}, f.name AS f_name, o.name AS o_name
                                 FROM edge e JOIN entity f ON f.id=e.factor_id JOIN entity o ON o.id=e.outcome_id
                                 WHERE e.tier != 'deprecated'""").fetchall()
        if a.edge:
            edges = [e for e in edges if e["id"] in a.edge]
        todo = []
        for e in edges:
            ev = conn.execute("""SELECT pmid, citation, notes, year, n_participants, real_title, study_type
                                 FROM evidence WHERE edge_id=? AND COALESCE(is_counter,0)=0""", (e["id"],)).fetchall()
            src_txt, abstracts = [], []
            for r in ev:
                rec = cache.get(r["pmid"] or "", {})
                src_txt += [r["citation"] or "", r["notes"] or "", str(r["year"] or ""), str(r["n_participants"] or ""),
                            r["real_title"] or "", rec.get("title", ""), rec.get("abstract", "")]
                if rec.get("abstract"):
                    abstracts.append(f"[{r['citation'] or r['pmid']}] {rec.get('title', '')}\n{rec['abstract'][:1500]}")
            src = " ".join(src_txt)
            src_nums = ea.nums(src)
            bad = [f for f in FIELDS if e[f] and ungrounded(e[f], src_nums)]
            if bad:
                todo.append((e, bad, src_nums, words(src), "\n\n".join(abstracts), ev))
        if a.limit:
            todo = todo[: a.limit]
        print(f"→ {len(todo)} edges with unsourced numbers")
        for n, (e, bad, src_nums, src_words, abstracts, ev) in enumerate(todo, 1):
            t0 = time.time()
            pair = f"{e['f_name']} → {e['o_name']}"
            changes = {}
            for f in bad:
                new, how = rewrite(f, pair, e[f], abstracts, src_nums, src_words)
                if f == "effect_quant" and not new:
                    q = estimate_quote(ev, cache, e["direction"], e["f_name"], e["o_name"])
                    if q:
                        new, how = q, "quoted"
                if f == "summary" and not new:
                    first = strip_sentences(e[f].split(". ")[0] + ".", src_nums)
                    new, how = (first or f"Evidence on {pair} — see the studies below."), "stripped"
                changes[f] = (new or None, how)
                st[how] += 1
            st["edges"] += 1
            print(f"[{n}/{len(todo)}] #{e['id']} {pair[:55]} " +
                  " ".join(f"{f}:{h}" for f, (_, h) in changes.items()) + f" {time.time() - t0:.0f}s", flush=True)
            if a.dry:
                for f, (new, how) in changes.items():
                    print(f"   - {f} OLD: {e[f][:240]}\n     NEW ({how}): {(new or '∅')[:240]}")
                continue
            for f, (new, how) in changes.items():
                conn.execute(f"UPDATE edge SET {f}=?, updated_at=datetime('now') WHERE id=?", (new, e["id"]))
                conn.execute("""INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
                                VALUES (?,?,?,?,?, 'number_audit')""",
                             (e["id"], f, e[f], new,
                              "numbers not found in any of this edge's sources " +
                              ("— rewritten with figures from the abstracts" if how == "model"
                               else "— sentences carrying them removed")))
            conn.commit()
    print(dict(st))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
