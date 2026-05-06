"""Weekly digest email sender. Local cron-driven; reads
data/subscribers.json and dispatches one HTML email per subscriber.

Usage:
    python digest_send.py              # dry-run, prints what would send
    python digest_send.py --send       # actually send via SMTP
    python digest_send.py --dump dest/  # write HTML files instead

Env vars (required for --send):
    SMTP_HOST       (e.g. smtp.gmail.com)
    SMTP_PORT       (587 default)
    SMTP_USER       (your email or app account)
    SMTP_PASS       (app password — never your normal password)
    SMTP_FROM       (display name + email; defaults to SMTP_USER)

Or, alternative — use Resend API:
    RESEND_API_KEY  (key from resend.com)
"""
from __future__ import annotations
import argparse
import json
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

PROJECT = Path(__file__).parent
sys.path.insert(0, str(PROJECT))

# Imports after sys.path
from web.app import templates, _new_discoveries, _no_regret_movers, _red_flags_in_stack  # noqa
from db import connect  # noqa
from profile import Profile  # noqa


def render_digest_html(profile_dict: dict, days: int = 7) -> tuple[str, str]:
    """Return (subject, html_body) for one subscriber."""
    p = Profile(**{k: v for k, v in profile_dict.items()
                   if k in {"age", "sex", "conditions", "goals", "stack",
                            "watch_factors", "watch_outcomes", "watch_edges"}})
    has_profile = bool(p.conditions or p.watch_factors or p.watch_outcomes or p.watch_edges)
    sections: list[dict] = []
    with connect() as conn:
        all_disc = _new_discoveries(conn, days=days, limit=80)
        if has_profile:
            tracked_o = set(p.conditions) | set(p.watch_outcomes)
            tracked_f = set(p.watch_factors)
            relevant = [d for d in all_disc
                        if (tracked_o and d["o_slug"] in tracked_o)
                        or (tracked_f and d["f_slug"] in tracked_f)
                        or d.get("breakthrough")]
        else:
            relevant = [d for d in all_disc if d.get("breakthrough")] or all_disc[:5]
        sections.append({
            "title": "This week's evidence shifts",
            "rows": relevant[:6],
        })
        if p.conditions:
            sections.append({
                "title": "Top no-regret moves",
                "rows": _no_regret_movers(conn, p, limit=4),
            })
            red = _red_flags_in_stack(conn, p, limit=4)
            if red:
                sections.append({"title": "Watch outs", "rows": red})
    subject = f"Health Universe — {len(sections[0]['rows'])} shifts in your tracked areas"
    html = templates.get_template("digest.html").render({
        "request": None, "title": "Weekly digest",
        "profile": p, "has_profile": has_profile,
        "days": days, "sections": sections,
        "today": datetime.now().strftime("%A %d %B %Y"),
        "TIER_LABEL": {"A":"Strong","B":"Moderate","C":"Emerging","D":"Limited","X":"Contested","deprecated":"Deprecated"},
        "DIRECTION_LABEL": {"protective":"Beneficial","harmful":"Harmful","neutral":"Neutral","u_shaped":"U-shaped","mixed":"Mixed"},
        "TIER_DOTS": {"A":5,"B":4,"C":3,"D":2,"X":3,"deprecated":1},
        "asset_v": "1",
    })
    return subject, html


def send_smtp(to_addr: str, subject: str, html: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM", os.environ["SMTP_USER"])
    msg["To"] = to_addr
    msg.set_content("Open in an HTML-capable mail client.")
    msg.add_alternative(html, subtype="html")
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Actually send via SMTP")
    parser.add_argument("--dump", help="Write HTML files to this directory instead")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    sub_file = PROJECT / "data" / "subscribers.json"
    if not sub_file.exists():
        print("No subscribers — nothing to send.")
        return
    subs = json.loads(sub_file.read_text())
    print(f"[digest] {len(subs)} subscriber(s)")
    out_dir = Path(args.dump) if args.dump else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
    for s in subs:
        email = s["email"]
        subject, html = render_digest_html(s.get("profile_snapshot", {}), days=args.days)
        if out_dir:
            (out_dir / f"{email.replace('@','_at_')}.html").write_text(html)
            print(f"  wrote → {email}")
        elif args.send:
            try:
                send_smtp(email, subject, html)
                print(f"  sent → {email}")
            except Exception as exc:
                print(f"  ERR  → {email}: {exc}")
        else:
            print(f"  [dry] would send to {email} ({subject})")


if __name__ == "__main__":
    main()
