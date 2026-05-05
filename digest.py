"""Daily/weekly digest. Pushes 'what changed' to ntfy and writes a summary
to data/logs/digest-YYYY-MM-DD.md so the user can browse history offline.

ntfy topic mirrors the AIMonitor pattern. No accounts, no PII.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from db import connect

load_dotenv(Path(__file__).parent / ".env", override=True)

NTFY_BASE  = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "healthuniverse-tDr8FqPh3xLmQ2")
LOG_DIR    = Path(__file__).parent / "data" / "logs"


def _changes_since(conn, hours: int) -> list[dict]:
    rows = conn.execute("""
        SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason, h.actor,
               e.id AS edge_id, e.tier, e.direction,
               f.name AS f_name, o.name AS o_name
        FROM edge_history h
        JOIN edge e ON e.id = h.edge_id
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE h.changed_at >= datetime('now', ?)
          AND h.field = 'tier'
        ORDER BY CASE h.new_value WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                 h.changed_at DESC""", (f"-{hours} hours",)).fetchall()
    return [dict(r) for r in rows]


def _format_markdown(rows: list[dict], window: str) -> str:
    if not rows:
        return f"# Health Universe digest ({window})\n\nNo tier changes.\n"
    promotions = [r for r in rows if r["new_value"] in ("A", "B")
                  and r["old_value"] not in ("A", "B")]
    demotions = [r for r in rows if r["old_value"] in ("A", "B")
                 and r["new_value"] not in ("A", "B")]
    other = [r for r in rows if r not in promotions and r not in demotions]
    out = [f"# Health Universe digest ({window})", ""]
    if promotions:
        out += ["## ▲ Promoted to high confidence", ""]
        for r in promotions:
            out.append(f"- **{r['f_name']} → {r['o_name']}** "
                       f"({r['old_value'] or 'new'} → {r['new_value']}) — {r['reason'] or r['actor']}")
        out.append("")
    if demotions:
        out += ["## ▼ Demoted from high confidence", ""]
        for r in demotions:
            out.append(f"- **{r['f_name']} → {r['o_name']}** "
                       f"({r['old_value']} → {r['new_value']}) — {r['reason'] or r['actor']}")
        out.append("")
    if other:
        out += ["## Other tier changes", ""]
        for r in other[:50]:
            out.append(f"- {r['f_name']} → {r['o_name']} "
                       f"({r['old_value'] or 'new'} → {r['new_value']})")
    return "\n".join(out) + "\n"


def _push_ntfy(title: str, body: str, click: str | None = None) -> bool:
    try:
        headers = {"Title": title, "Priority": "default"}
        if click: headers["Click"] = click
        r = httpx.post(f"{NTFY_BASE}/{NTFY_TOPIC}",
                       data=body.encode(), headers=headers, timeout=15.0)
        return r.is_success
    except Exception as e:
        print(f"ntfy push failed: {e}"); return False


def run_personalized(*, hours: int = 24, push: bool = False,
                     stack_slugs: list[str] | None = None,
                     condition_slugs: list[str] | None = None,
                     ntfy_topic: str | None = None) -> dict:
    """Per-user digest: only changes touching the user's stack or conditions."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        rows = _changes_since(conn, hours)
    relevant: list[dict] = []
    for r in rows:
        # changes_since returns f_name and o_name only — match by name OR
        # query underlying entity slug.
        with connect() as conn:
            f_slug = conn.execute(
                "SELECT slug FROM entity WHERE name=? LIMIT 1", (r["f_name"],)
            ).fetchone()
            o_slug = conn.execute(
                "SELECT slug FROM entity WHERE name=? LIMIT 1", (r["o_name"],)
            ).fetchone()
        f, o = (f_slug["slug"] if f_slug else None), (o_slug["slug"] if o_slug else None)
        if (stack_slugs and f in (stack_slugs or [])) or \
           (condition_slugs and o in (condition_slugs or [])):
            relevant.append(r)
    md = _format_markdown(relevant, f"last {hours}h, personalised")
    out_path = LOG_DIR / f"digest-personal-{dt.date.today().isoformat()}.md"
    out_path.write_text(md)
    print(f"[digest-personal] wrote {out_path} ({len(relevant)} relevant)")
    if push and relevant and ntfy_topic:
        body = "\n".join(f"• {r['f_name']} → {r['o_name']} "
                         f"({r['old_value'] or 'new'} → {r['new_value']})"
                         for r in relevant[:5])
        try:
            r2 = httpx.post(f"{NTFY_BASE}/{ntfy_topic}",
                            data=body.encode(),
                            headers={"Title": f"Health Universe — {len(relevant)} personal update(s)"},
                            timeout=15.0)
            print(f"  ntfy {ntfy_topic}: {r2.status_code}")
        except Exception as e:
            print(f"  ntfy failed: {e}")
    return {"changes": len(relevant), "path": str(out_path)}


def run(*, hours: int = 24, push: bool = False) -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        rows = _changes_since(conn, hours)
    window = f"last {hours}h"
    md = _format_markdown(rows, window)
    today = dt.date.today().isoformat()
    out_path = LOG_DIR / f"digest-{today}.md"
    out_path.write_text(md)
    print(f"[digest] wrote {out_path} ({len(rows)} changes)")

    if push and rows:
        promos = [r for r in rows if r["new_value"] in ("A", "B")
                  and r["old_value"] not in ("A", "B")]
        if promos:
            top = promos[0]
            body = "\n".join(f"• {r['f_name']} → {r['o_name']} ({r['new_value']})"
                             for r in promos[:5])
            _push_ntfy(
                title=f"Health Universe — {len(promos)} new high-confidence finding(s)",
                body=body,
                click=f"https://health-universe.vercel.app/edge/{top['edge_id']}",
            )
    return {"changes": len(rows), "path": str(out_path)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    run(hours=a.hours, push=a.push)
