"""Ask My Universe — RAG-grounded Q&A over the knowledge graph.

Pipeline:
  1. Embed the user's query (nomic-embed-text via Ollama)
  2. Cosine-similarity rank against every edge embedding (in-memory)
  3. Pull top-K edges with their evidence (supporting + counter)
  4. If user has a /me profile, weight relevance with their stack/conditions
  5. Format a strict prompt for local Gemma asking for a 3-paragraph
     cited answer plus a list of edges referenced
  6. Return the answer + citation links + any retracted-evidence flags

Costs $0 per query (everything local).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                                    # noqa: E402
from embeddings import embed, unpack, cosine, EmbeddingsUnavailable  # noqa: E402
from ollama_client import call, OllamaUnavailable         # noqa: E402
from profile import Profile, relevance_score              # noqa: E402

TOP_K = 8
MIN_SIM = 0.45      # below this: refuse with "no evidence in graph"


SYSTEM = """You are a careful evidence-grounded health-research assistant. \
You answer using ONLY the edges and evidence rows you receive — do not bring in outside knowledge. \
If the evidence is thin or contradictory, say so plainly. \
If no provided edge actually addresses the question, refuse and say "I don't have evidence in my graph for this." \
Always end with the disclaimer: \
'Not medical advice — consult a clinician.' \
Cite specific edges in your answer with markdown links of the form [edge#ID](/edge/ID). \
Keep the answer to 3 short paragraphs maximum."""


USER_TMPL = """Question: {question}

{profile_block}

Top relevant edges from the knowledge graph (with evidence summaries):
{edges_block}

Write a grounded 3-paragraph answer. Quote specific tier and cite edges with [edge#ID](/edge/ID) links. \
If a cited paper is retracted, mention it. End with the disclaimer.
"""


def _profile_block(p: Profile) -> str:
    if not (p.age or p.sex or p.conditions or p.stack):
        return "User profile: not provided."
    lines = ["User profile (use this to personalize):"]
    if p.age: lines.append(f"  age: {p.age}")
    if p.sex: lines.append(f"  sex: {p.sex}")
    if p.conditions: lines.append(f"  conditions: {', '.join(p.conditions)}")
    if p.stack: lines.append(f"  current stack: {', '.join(p.stack)}")
    return "\n".join(lines)


def _format_edge(e: dict, evidence: list[dict], counter: list[dict]) -> str:
    lines = [
        f"edge#{e['id']}: {e['f_name']} -> {e['o_name']}",
        f"  tier={e['tier']}, direction={e['direction']}, "
        f"population={e.get('population','general adult')}",
        f"  summary: {(e.get('summary') or '')[:280]}",
    ]
    if e.get("mechanism"):
        lines.append(f"  mechanism: {e['mechanism'][:240]}")
    if evidence:
        lines.append("  supporting evidence (top 3):")
        for ev in evidence[:3]:
            n = f", n={ev['n_participants']:,}" if ev.get("n_participants") else ""
            ret = " [RETRACTED]" if ev.get("is_retracted") else ""
            lines.append(f"    - {ev.get('citation','')[:120]} "
                         f"({ev.get('study_type','')}{n}, quality {ev.get('quality','')}){ret}")
    if counter:
        lines.append("  counter-evidence (disagreeing studies):")
        for ev in counter[:2]:
            n = f", n={ev['n_participants']:,}" if ev.get("n_participants") else ""
            lines.append(f"    - {ev.get('citation','')[:120]} "
                         f"({ev.get('study_type','')}{n}, direction={ev.get('direction','')}){n}")
    return "\n".join(lines)


def _retrieve(qvec: list[float], p: Profile, k: int = TOP_K) -> list[dict]:
    """Return top-k edges by (cosine + personalization bonus)."""
    with connect() as conn:
        cands = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.mechanism, e.population,
                   e.embedding,
                   f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE e.embedding IS NOT NULL""").fetchall()
    scored: list[tuple[float, dict]] = []
    for r in cands:
        d = {k: r[k] for k in r.keys() if k != "embedding"}
        sim = cosine(qvec, unpack(r["embedding"]))
        rel = relevance_score(d, p)            # adds 5 for matching condition, etc.
        score = sim + rel * 0.05               # rel adds up to ~0.5 max
        scored.append((score, sim, d))
    scored.sort(key=lambda x: -x[0])
    return [{**d, "_sim": s, "_score": sc} for sc, s, d in scored[:k]]


def _evidence_for(edge_id: int, *, counter: bool = False) -> list[dict]:
    with connect() as conn:
        try:
            rows = conn.execute("""
                SELECT ev.*, COALESCE(s.is_retracted, 0) AS is_retracted
                FROM evidence ev
                LEFT JOIN evidence_status s ON s.pmid = ev.pmid
                WHERE ev.edge_id=? AND COALESCE(ev.is_counter,0)=?
                ORDER BY CASE ev.study_type
                  WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2
                  WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END
                LIMIT 5""", (edge_id, 1 if counter else 0)).fetchall()
        except Exception:
            rows = conn.execute(
                "SELECT *, 0 AS is_retracted FROM evidence "
                "WHERE edge_id=? AND COALESCE(is_counter,0)=? LIMIT 5",
                (edge_id, 1 if counter else 0)).fetchall()
    return [dict(r) for r in rows]


def ask(question: str, profile: Profile | None = None, *, k: int = TOP_K) -> dict:
    """Returns {answer, citations, edges_used, refused?, error?}"""
    profile = profile or Profile()
    question = (question or "").strip()
    if not question:
        return {"refused": True, "answer": "Ask a question."}

    try:
        qvec = embed(question)
    except EmbeddingsUnavailable as e:
        return {"error": f"Embeddings unavailable: {e}", "answer": ""}
    if not qvec:
        return {"error": "Empty embedding", "answer": ""}

    edges = _retrieve(qvec, profile, k=k)
    if not edges or edges[0]["_sim"] < MIN_SIM:
        return {
            "refused": True,
            "answer": ("I don't have evidence in my graph for that. "
                       "The closest topics I cover have only weak overlap with your "
                       "question — please consult a clinician or rephrase."),
            "edges_used": [],
        }

    edge_blocks = []
    edges_used: list[dict] = []
    any_retracted = False
    for e in edges:
        ev = _evidence_for(e["id"])
        co = _evidence_for(e["id"], counter=True)
        if any(x.get("is_retracted") for x in ev + co):
            any_retracted = True
        edge_blocks.append(_format_edge(e, ev, co))
        edges_used.append({k: e[k] for k in
            ("id", "tier", "direction", "f_name", "o_name", "_sim")})

    user = USER_TMPL.format(
        question=question,
        profile_block=_profile_block(profile),
        edges_block="\n\n".join(edge_blocks),
    )
    try:
        text = call(system=SYSTEM, user=user, temperature=0.2, num_predict=2000)
    except OllamaUnavailable as e:
        return {"error": f"Local Gemma unavailable: {e}", "answer": ""}

    return {
        "answer": text.strip(),
        "edges_used": edges_used,
        "any_retracted": any_retracted,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    a = ap.parse_args()
    r = ask(a.question)
    print(r.get("answer", r.get("error")))
    print("\n--- edges used ---")
    for e in r.get("edges_used", []):
        print(f"  edge#{e['id']:4} sim={e['_sim']:.3f} tier={e['tier']} {e['f_name']} -> {e['o_name']}")
