"""Auto-generate weekly 'cornerstone' articles from edge_history.

Pipeline:
  1. Pull every meaningful edge_history event in the past N days.
  2. Group by category (promotions, demotions, new evidence, retractions).
  3. Render a structured prose post via the local Gemma loop, falling
     back to Claude (cost-capped) if Ollama is offline.
  4. Save each post to data/posts/{YYYY-MM-week-WW}.json.

Designed to be cron-driven (run weekly) but can be invoked manually:

    python posts_build.py                     # past 7 days
    python posts_build.py --days 30           # last month
    python posts_build.py --print --no-write  # preview without saving
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                          # noqa: E402
from web.app import _classify_event             # noqa: E402

POSTS_DIR = ROOT / "data" / "posts"


SYSTEM = """You are a careful, dry science writer for an evidence-graph
publication. Given a structured list of evidence shifts (tier promotions,
new studies added, retractions) over a time window, write a short
cornerstone article (~600 words, 3 sections) summarising what changed
and why it matters.

Constraints:
- Cite specific edges with markdown links of form [factor → outcome](/edge/ID).
- DO NOT invent doses, mechanisms, or PMIDs that aren't in the input.
- End with: 'Educational synthesis only — not medical advice.'
- Tone: confident but careful. No hype. No emoji.
- Markdown sections: an opening paragraph, '## Notable promotions', '## New evidence',
  optionally '## Watchouts' if there are demotions or retractions, '## Closing'.
"""


def collect_events(days: int) -> list[dict]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("""
            SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason,
                   h.actor,
                   e.id AS edge_id, e.summary AS e_summary, e.tier AS e_tier,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id = h.edge_id
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE h.changed_at >= ?
            ORDER BY h.changed_at DESC""", (cutoff,)).fetchall()]
    out = []
    for r in rows:
        ev = _classify_event(r)
        if not ev["is_meaningful"]:
            continue
        out.append({
            **ev,
            "edge_id": r["edge_id"],
            "f_name":  r["f_name"],
            "o_name":  r["o_name"],
            "tier":    r["e_tier"],
            "summary": (r.get("e_summary") or "")[:240],
        })
    return out


def build_input_block(events: list[dict]) -> str:
    lines = []
    by_cat = {}
    for ev in events:
        by_cat.setdefault(ev["category"], []).append(ev)
    for cat in ("tier_promotion", "evidence_added", "tier_demotion", "retraction"):
        items = by_cat.get(cat, [])
        if not items:
            continue
        label = {"tier_promotion":"PROMOTIONS","evidence_added":"NEW EVIDENCE",
                 "tier_demotion":"DEMOTIONS","retraction":"RETRACTIONS"}[cat]
        lines.append(f"\n# {label}")
        for ev in items[:12]:
            lines.append(
                f"- [edge#{ev['edge_id']}] {ev['f_name']} → {ev['o_name']} "
                f"({ev['headline']}, tier {ev.get('tier','?')}) — {ev['summary'][:160]}")
    return "\n".join(lines)


def render_with_llm(window_label: str, events: list[dict]) -> tuple[str, str]:
    user_msg = (f"Time window: {window_label}\n"
                f"Total meaningful events: {len(events)}\n"
                f"{build_input_block(events)}\n\n"
                "Write the article now.")
    # Prefer local Gemma
    try:
        from ollama_client import call as ollama_call, OllamaUnavailable
        text = ollama_call(system=SYSTEM, user=user_msg,
                           num_predict=2000, retries=0)
        return text, "local-gemma"
    except Exception:
        pass
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        from claude_client import call as claude_call
        text, _u = claude_call(system=SYSTEM, user=user_msg,
                               operation="post-build", max_tokens=2000)
        return text, "claude-sonnet"
    raise RuntimeError("No LLM available (Ollama down + ANTHROPIC_API_KEY unset).")


def slug_for(today: datetime) -> str:
    iso_year, iso_week, _ = today.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--no-write", action="store_true",
                    help="Render but don't save to data/posts/")
    ap.add_argument("--print", action="store_true", dest="print_text")
    args = ap.parse_args()

    today = datetime.now()
    events = collect_events(args.days)
    if not events:
        print(f"[posts] no meaningful events in last {args.days} days — nothing to write.")
        return

    window_label = f"Last {args.days} days · ending {today.strftime('%Y-%m-%d')}"
    text, model = render_with_llm(window_label, events)
    title = f"Evidence shifts · week of {today.strftime('%Y-%m-%d')}"
    slug = slug_for(today)
    post = {
        "title": title,
        "subtitle": f"{len(events)} meaningful events · written by {model}",
        "window_days": args.days,
        "ending_at": today.strftime("%Y-%m-%d"),
        "n_events": len(events),
        "events_summary": [
            {k: ev[k] for k in ("category", "headline", "edge_id", "f_name", "o_name")}
            for ev in events[:30]
        ],
        "body_md": text,
        "model": model,
        "generated_at": today.isoformat(),
    }
    if args.print_text:
        print(json.dumps(post, indent=2))
    if not args.no_write:
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        out_file = POSTS_DIR / f"{slug}.json"
        out_file.write_text(json.dumps(post, indent=2))
        print(f"[posts] wrote → {out_file}")


if __name__ == "__main__":
    main()
