"""Topic-driven cornerstone-post builder.

Pulls every edge in the corpus that matches a topic spec (factor slug
LIKE pattern, outcome slug LIKE pattern, or keyword in summary), feeds
them to Claude as structured input, and writes a long-form post.

    python posts_topic.py --slug 2026-W19-coffee-cancer \\
        --title "Coffee and cancer · what the evidence actually shows" \\
        --factor coffee
    python posts_topic.py --slug 2026-W19-benzos-elderly \\
        --title "Benzodiazepines in older adults · cognition, falls, fractures" \\
        --factor benzodiazepines
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                             # noqa: E402

POSTS_DIR = ROOT / "data" / "posts"

SYSTEM = """You are a careful, dry science writer for an evidence-graph
publication. Given a structured list of factor → outcome edges with
their PMID-verified evidence, write a cornerstone article (~700 words)
that synthesises what the evidence actually shows.

Constraints:
- Cite specific edges with markdown links of form [factor → outcome](/edge/ID).
- DO NOT invent doses, mechanisms, or PMIDs that aren't in the input.
- End with: 'Educational synthesis only — not medical advice.'
- Tone: confident but careful. No hype. No emoji.
- Markdown sections: opening paragraph, '## What the evidence shows',
  '## Where the picture is mixed', '## Practical takeaways',
  '## Closing'.
- When effect_quant is present, cite the actual numbers (e.g. RR 0.85,
  95% CI 0.80–0.91).
- Group cancer outcomes / similar-direction outcomes together.
"""


def collect_edges(factor: str | None, outcome: str | None,
                  keyword: str | None) -> list[dict]:
    where = []; params = []
    if factor:
        where.append("(f.slug LIKE ? OR f.name LIKE ?)")
        params += [f"%{factor}%", f"%{factor}%"]
    if outcome:
        where.append("(o.slug LIKE ? OR o.name LIKE ?)")
        params += [f"%{outcome}%", f"%{outcome}%"]
    if keyword:
        where.append("(e.summary LIKE ? OR e.mechanism LIKE ?)")
        params += [f"%{keyword}%", f"%{keyword}%"]
    where_sql = " AND ".join(where) if where else "1=1"
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(f"""
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                   e.effect_quant, e.population,
                   f.slug AS f_slug, f.name AS f_name,
                   o.slug AS o_slug, o.name AS o_name,
                   (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE {where_sql} AND e.tier IN ('A','B','C')
            ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                     e.id""", params).fetchall()]
    return rows


def build_input(edges: list[dict]) -> str:
    lines = []
    for e in edges:
        line = (f"[edge#{e['id']}] {e['f_name']} → {e['o_name']} "
                f"(tier {e['tier']}, {e['direction']}, "
                f"{e['n_studies']} studies, effect={e.get('effect_size','?')})\n"
                f"  summary: {(e.get('summary') or '')[:240]}\n"
                f"  effect_quant: {(e.get('effect_quant') or '—')[:200]}")
        lines.append(line)
    return "\n\n".join(lines)


def render(title: str, edges: list[dict]) -> tuple[str, str]:
    user_msg = (f"Article title: {title}\n"
                f"Total relevant edges: {len(edges)}\n\n"
                f"EDGES:\n{build_input(edges)}\n\n"
                "Write the article now.")
    try:
        from ollama_client import call as ollama_call, OllamaUnavailable
        text = ollama_call(system=SYSTEM, user=user_msg, num_predict=2400, retries=0)
        return text, "local-gemma"
    except Exception:
        pass
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        from claude_client import call as claude_call
        text, _u = claude_call(system=SYSTEM, user=user_msg,
                               operation="cornerstone-post", max_tokens=2400)
        return text, "claude-sonnet"
    raise RuntimeError("No LLM available.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--factor", help="filter on factor slug/name (substring)")
    ap.add_argument("--outcome", help="filter on outcome slug/name (substring)")
    ap.add_argument("--keyword", help="filter on summary/mechanism (substring)")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    edges = collect_edges(args.factor, args.outcome, args.keyword)
    if not edges:
        print(f"[posts] no edges matched — nothing to write.")
        return
    print(f"[posts] {len(edges)} edges matched. Generating article…")
    text, model = render(args.title, edges)
    today = datetime.now()
    post = {
        "title": args.title,
        "subtitle": args.subtitle or f"Cornerstone synthesis · {len(edges)} edges · written by {model}",
        "ending_at": today.strftime("%Y-%m-%d"),
        "n_events": len(edges),
        "events_summary": [
            {"category": "topic", "headline": e["direction"], "edge_id": e["id"],
             "f_name": e["f_name"], "o_name": e["o_name"]}
            for e in edges[:30]
        ],
        "body_md": text,
        "model": model,
        "generated_at": today.isoformat(),
        "topic": True,
    }
    if not args.no_write:
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        out = POSTS_DIR / f"{args.slug}.json"
        out.write_text(json.dumps(post, indent=2))
        print(f"[posts] wrote → {out}")
    else:
        print(text[:600] + "…")


if __name__ == "__main__":
    main()
