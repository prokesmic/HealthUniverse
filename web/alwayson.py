"""Always-on assistant — server-side compute, push, memory.

Architecture:

  • synced_data         — end-to-end-encrypted blob of the user's
                          localStorage. Server stores ciphertext bytes
                          only; the decryption key never leaves the
                          user's browser.
  • compute_summaries   — opt-in minimal "what the server can read"
                          view: anomaly z-scores, watchlist edges,
                          open recommendations, next visit, flagged
                          labs. NOT raw PHI. The daily cron reads
                          this to run per-user computations.
  • push_subscriptions  — Web Push API endpoints (one per device).
  • daily_briefings     — the system's memory. Each daily run produces
                          one row. The next run reads the last 7 rows
                          to ground its output.
  • shift_alerts        — event-driven queue: when an edge on a user's
                          watchlist changes tier or gets retracted,
                          we enqueue a row here for immediate push.

Privacy model: the server can compute proactively for a user ONLY if
that user has explicitly opted in via compute_summaries with
agreed_to_daily_compute=true. Anonymous users and opted-out users get
weekly briefings only (no per-user compute).
"""
from __future__ import annotations

import json as _json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from web.auth import supabase_service


# ─── Push helpers ────────────────────────────────────────────────────


def send_web_push(endpoint: str, p256dh: str, auth: str, payload: dict) -> tuple[bool, str]:
    """Send one Web Push notification. Returns (ok, error_message)."""
    try:
        from pywebpush import webpush, WebPushException
    except Exception as exc:
        return False, f"pywebpush not installed: {exc}"
    vapid_priv = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subj = os.environ.get("VAPID_SUBJECT", "mailto:noreply@health-universe.app")
    if not vapid_priv:
        return False, "VAPID_PRIVATE_KEY not set"
    try:
        # pywebpush expects standard PEM-format private key. We stored
        # a raw base64url 32-byte scalar from py_vapid, so reconstruct.
        import base64
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        raw = base64.urlsafe_b64decode(vapid_priv + "=" * (-len(vapid_priv) % 4))
        scalar = int.from_bytes(raw, "big")
        priv_key = ec.derive_private_key(scalar, ec.SECP256R1())
        pem = priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=_json.dumps(payload),
            vapid_private_key=pem,
            vapid_claims={"sub": vapid_subj},
            ttl=12 * 3600,
        )
        return True, "ok"
    except WebPushException as exc:
        msg = str(exc)[:200]
        # 410 = subscription expired/unregistered; caller can delete.
        if "410" in msg:
            return False, "expired"
        return False, msg
    except Exception as exc:
        return False, str(exc)[:200]


# ─── Compute helpers (the "always-on" brain) ────────────────────────


def _user_local_date(tz: str) -> date:
    """Return the user's local 'today'."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz)).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def _fetch_recent_briefings(account_id: str, n: int = 7) -> list[dict]:
    """Pull the last n daily briefings to ground today's prompt
    (the system's memory). Newest last so the LLM reads them in order."""
    sb = supabase_service()
    if sb is None:
        return []
    try:
        r = (sb.table("daily_briefings")
             .select("generated_for_date, headline, observations, actions")
             .eq("account_id", account_id)
             .order("generated_for_date", desc=True)
             .limit(n)
             .execute())
        rows = list(r.data or [])
        rows.reverse()
        return rows
    except Exception as exc:
        print(f"[alwayson] memory fetch failed: {exc}")
        return []


def _shifts_for_user(account_id: str, watch_edges: list[int],
                     since: datetime) -> list[dict]:
    """Pull recent edge_history shifts that affect the user's watchlist.
    NOTE: this queries the local SQLite corpus (read-only)."""
    if not watch_edges:
        return []
    from db import connect
    try:
        with connect() as conn:
            ph = ",".join("?" * len(watch_edges))
            rows = conn.execute(f"""
                SELECT h.edge_id, h.field, h.old_value, h.new_value, h.changed_at,
                       e.tier, f.name AS f_name, o.name AS o_name
                FROM edge_history h
                JOIN edge e ON e.id=h.edge_id
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE h.edge_id IN ({ph}) AND h.changed_at >= ?
                  AND h.field IN ('tier','is_retracted','direction')
                ORDER BY h.changed_at DESC
                LIMIT 20""",
                [*watch_edges, since.isoformat()]).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[alwayson] shifts query failed: {exc}")
        return []


def compute_daily_for_account(account_row: dict, summary: dict) -> Optional[dict]:
    """Run the full daily compute for one account.
    Returns the briefing dict or None if the user has too little data."""
    if not summary.get("agreed_to_daily_compute"):
        return None

    tz = summary.get("timezone") or "UTC"
    today = _user_local_date(tz)
    yesterday = today - timedelta(days=1)

    # 1) Collect signals
    anomalies = summary.get("anomaly_zscores") or {}
    flagged_labs = summary.get("flagged_labs") or []
    open_recs = summary.get("open_recommendations") or []
    next_visit = summary.get("next_visit") or None
    active_protos = summary.get("active_protocols") or []
    watch_edges = summary.get("watch_edges") or []

    yesterday_dt = datetime.utcnow() - timedelta(days=2)
    shifts = _shifts_for_user(account_row["id"], watch_edges, yesterday_dt)
    memory = _fetch_recent_briefings(account_row["id"], n=7)

    # 2) If there's nothing to say, skip (avoid daily-spam fatigue).
    nothing_to_say = (
        not anomalies and not flagged_labs and not shifts
        and not _due_check_ins(open_recs)
        and not _imminent_visit(next_visit, today)
        and not _due_protocols(active_protos, today)
    )
    if nothing_to_say:
        return None

    # 3) Build a deterministic, lightweight summary string for the LLM.
    pieces = []
    for stream, info in (anomalies or {}).items():
        z = info.get("z")
        if z is None: continue
        pieces.append(
            f"{stream}: z={z} ({info.get('dir','')}, "
            f"{info.get('recent_mean','?')} vs baseline {info.get('baseline_mean','?')})"
        )
    if flagged_labs:
        for l in flagged_labs[:5]:
            pieces.append(f"lab {l.get('name')} = {l.get('value')} {l.get('unit','')} ({l.get('direction')})")
    if shifts:
        for s in shifts[:3]:
            pieces.append(
                f"corpus shift: {s.get('f_name')} → {s.get('o_name')} "
                f"{s.get('field')} {s.get('old_value')} → {s.get('new_value')}"
            )
    if next_visit:
        d = next_visit.get("date", "")
        if d:
            try:
                days = (date.fromisoformat(d) - today).days
                if 0 <= days <= 7:
                    pieces.append(f"appointment in {days} days with {next_visit.get('clinician','clinician')}")
            except Exception: pass
    for r in (open_recs or [])[:3]:
        days = r.get("days_open", 0)
        if days >= 7:
            pieces.append(f"open rec {days} days: {r.get('edge_label')}")
    for p in active_protos[:2]:
        if p.get("ends_at") and p["ends_at"] <= today.isoformat():
            pieces.append(f"protocol due to close: {p.get('factor')}")

    mem_lines = []
    for m in memory[-3:]:
        if m.get("headline"):
            mem_lines.append(f"{m.get('generated_for_date')}: {m['headline']}")

    # 4) Ask Claude Haiku to write a 1-paragraph note + 1-3 actions.
    try:
        text = _llm_brief(today.isoformat(), pieces, mem_lines)
        parsed = _json.loads(text) if text else None
    except Exception as exc:
        print(f"[alwayson] LLM failed, falling back to template: {exc}")
        parsed = None
    if not parsed:
        # Deterministic fallback so the user still gets something useful.
        parsed = {
            "headline": "Your daily check-in",
            "observations": [f"Today's signals: {p}" for p in pieces[:3]],
            "actions": ["Review your /me/briefing for full detail."],
            "doctor_question": None,
        }

    return {
        "generated_for_date": today.isoformat(),
        "headline": parsed.get("headline") or "Daily check-in",
        "observations": parsed.get("observations") or [],
        "actions": parsed.get("actions") or [],
        "doctor_question": parsed.get("doctor_question"),
        "trends_snapshot": {"signals_count": len(pieces), "shifts_count": len(shifts)},
    }


def _due_check_ins(open_recs: list[dict]) -> bool:
    return any((r.get("days_open") or 0) >= 28 for r in (open_recs or []))


def _imminent_visit(visit: Optional[dict], today: date) -> bool:
    if not visit: return False
    try:
        return 0 <= (date.fromisoformat(visit.get("date", "")) - today).days <= 7
    except Exception:
        return False


def _due_protocols(protos: list[dict], today: date) -> bool:
    for p in (protos or []):
        if p.get("ends_at") and p["ends_at"] <= today.isoformat():
            return True
    return False


def _llm_brief(date_iso: str, signals: list[str], memory_lines: list[str]) -> Optional[str]:
    """Ask Claude Haiku for the briefing. JSON-only."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from anthropic import Anthropic
        client = Anthropic()
        system = (
            "You write daily health briefings. Tone: a careful, knowledgeable "
            "friend — not a chatbot, not a doctor. Output STRICT JSON ONLY:\n"
            '{"headline": "ONE sentence summary", '
            '"observations": ["2-3 short bullets connecting signals"], '
            '"actions": ["1-3 specific concrete things they could do TODAY"], '
            '"doctor_question": "if appointment imminent, ONE question; else null"}\n'
            "Constraints:\n"
            "- Reference prior days when continuity exists (e.g. 'third day in a row…')\n"
            "- Never diagnose. Never tell them to stop medication.\n"
            "- Specific over generic ('zone-2 today instead of intervals' > 'consider rest')\n"
            "- Under 280 words total. No emoji. No markdown.\n"
        )
        user = (
            f"DATE: {date_iso}\n\n"
            f"TODAY'S SIGNALS:\n" + ("\n".join(f"- {s}" for s in signals) or "(none significant)") + "\n\n"
            f"RECENT BRIEFINGS (memory):\n"
            + ("\n".join(f"- {m}" for m in memory_lines) or "(none)") + "\n\n"
            "Return JSON only."
        )
        resp = client.messages.create(
            model=os.environ.get("HU_DAILY_MODEL", "claude-haiku-4-5"),
            max_tokens=500, temperature=0.2,
            system=system, messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        # Strip code fences if any.
        import re as _re
        m = _re.search(r"\{[\s\S]*\}", text)
        return m.group(0) if m else text
    except Exception as exc:
        print(f"[alwayson] anthropic call failed: {exc}")
        return None


# ─── Storage helpers ─────────────────────────────────────────────────


def save_briefing(account_id: str, briefing: dict, sent_via: list[str]) -> None:
    sb = supabase_service()
    if sb is None:
        return
    try:
        sb.table("daily_briefings").upsert({
            "account_id": account_id,
            "generated_for_date": briefing["generated_for_date"],
            "headline": briefing.get("headline"),
            "observations": briefing.get("observations") or [],
            "actions": briefing.get("actions") or [],
            "doctor_question": briefing.get("doctor_question"),
            "trends_snapshot": briefing.get("trends_snapshot") or {},
            "sent_via": sent_via,
        }, on_conflict="account_id,generated_for_date").execute()
    except Exception as exc:
        print(f"[alwayson] briefing save failed: {exc}")


def deliver_briefing(account: dict, briefing: dict) -> list[str]:
    """Send via push (preferred) and email (fallback). Returns the
    channels actually delivered to."""
    sent: list[str] = []
    sb = supabase_service()
    if sb is None:
        return sent
    # 1) Push to all registered devices.
    try:
        r = sb.table("push_subscriptions").select("*").eq("account_id", account["id"]).execute()
        subs = list(r.data or [])
    except Exception:
        subs = []
    payload = {
        "title": briefing.get("headline", "Daily check-in"),
        "body": (briefing.get("observations") or ["Open your briefing"])[0][:140],
        "url": "/me/briefing",
        "tag": "daily-" + briefing["generated_for_date"],
    }
    for sub in subs:
        ok, err = send_web_push(sub["endpoint"], sub["p256dh"], sub["auth"], payload)
        if ok:
            sent.append("push")
        elif err == "expired":
            # Auto-clean dead endpoints.
            try:
                sb.table("push_subscriptions").delete().eq("id", sub["id"]).execute()
            except Exception: pass
    if "push" in sent:
        return sent
    # 2) Fallback to email if no push delivered.
    try:
        from web.app import _resend_send                          # noqa: E402
        if os.environ.get("RESEND_API_KEY"):
            html = _render_briefing_html(briefing)
            _resend_send(account["email"], briefing.get("headline", "Health Universe — daily"), html)
            sent.append("email")
    except Exception as exc:
        print(f"[alwayson] email fallback failed: {exc}")
    return sent


def _render_briefing_html(b: dict) -> str:
    obs = "".join(f"<li>{_esc(x)}</li>" for x in (b.get("observations") or []))
    acts = "".join(f"<li>{_esc(x)}</li>" for x in (b.get("actions") or []))
    dq = f"<p style='margin:14px 0;padding:10px;background:#fffbe7;border-left:3px solid #c9a961'><b>For your next clinician visit:</b> {_esc(b.get('doctor_question',''))}</p>" if b.get("doctor_question") else ""
    return (
        f"<div style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px'>"
        f"<h1 style='font-family:Georgia,serif'>{_esc(b.get('headline','Daily check-in'))}</h1>"
        f"<h3 style='margin-top:18px;font-size:14px;color:#666;text-transform:uppercase;letter-spacing:0.06em'>What I'm seeing</h3>"
        f"<ul>{obs}</ul>"
        f"<h3 style='margin-top:18px;font-size:14px;color:#666;text-transform:uppercase;letter-spacing:0.06em'>One thing for today</h3>"
        f"<ul>{acts}</ul>"
        f"{dq}"
        f"<p style='margin-top:24px'><a href='https://health-universe.vercel.app/me/briefing' "
        f"style='display:inline-block;padding:10px 18px;background:#1f3a2e;color:#fff;border-radius:8px;text-decoration:none'>"
        f"Open my full briefing</a></p>"
        f"<p style='font-size:12px;color:#888;margin-top:24px'>"
        f"Daily briefing generated from your synced data. "
        f"<a href='https://health-universe.vercel.app/me/data'>Adjust preferences</a> · "
        f"<a href='https://health-universe.vercel.app/api/auth/logout'>Unsubscribe</a>."
        f"</p>"
        f"</div>"
    )


def _esc(s: Any) -> str:
    if s is None: return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ─── Shift-alert queueing (Move 5) ──────────────────────────────────


def enqueue_shift_alerts(edge_id: int, shift_kind: str, old: str, new: str, changed_at: str) -> int:
    """Called when corpus edge_history is appended. Finds every account
    whose compute_summary.watch_edges contains edge_id and queues an
    alert row. Returns count of alerts queued."""
    sb = supabase_service()
    if sb is None: return 0
    try:
        # Need accounts whose compute_summaries.watch_edges contains the
        # edge_id. Supabase Postgres lets us use array @> with cs filter.
        r = (sb.table("compute_summaries")
             .select("account_id, watch_edges")
             .contains("watch_edges", [edge_id])
             .execute())
        rows = list(r.data or [])
        if not rows: return 0
        inserts = [{
            "account_id": row["account_id"],
            "edge_id": edge_id,
            "shift_kind": shift_kind,
            "old_value": old, "new_value": new,
            "changed_at": changed_at,
        } for row in rows]
        sb.table("shift_alerts").insert(inserts).execute()
        return len(inserts)
    except Exception as exc:
        print(f"[alwayson] shift queue failed: {exc}")
        return 0


def drain_shift_alerts() -> int:
    """Send pending shift alerts via push. Returns count delivered."""
    sb = supabase_service()
    if sb is None: return 0
    try:
        r = (sb.table("shift_alerts")
             .select("*").is_("delivered_at", "null")
             .limit(200).execute())
        alerts = list(r.data or [])
    except Exception:
        return 0
    delivered = 0
    for a in alerts:
        # Look up the edge's friendly names from corpus.
        from db import connect
        try:
            with connect() as conn:
                row = conn.execute("""
                    SELECT f.name AS f_name, o.name AS o_name, e.tier
                    FROM edge e
                    JOIN entity f ON f.id=e.factor_id
                    JOIN entity o ON o.id=e.outcome_id
                    WHERE e.id=?""", (a["edge_id"],)).fetchone()
                names = dict(row) if row else {"f_name": "factor", "o_name": "outcome", "tier": "?"}
        except Exception:
            names = {"f_name": "factor", "o_name": "outcome", "tier": "?"}
        # Look up the account's push subs.
        try:
            sr = sb.table("push_subscriptions").select("*").eq("account_id", a["account_id"]).execute()
            subs = list(sr.data or [])
        except Exception:
            subs = []
        any_ok = False
        for sub in subs:
            ok, err = send_web_push(sub["endpoint"], sub["p256dh"], sub["auth"], {
                "title": f"Watchlist update: {names['f_name']} → {names['o_name']}",
                "body": f"{a['shift_kind']} · {a['old_value']} → {a['new_value']}",
                "url": f"/edge/{a['edge_id']}",
                "tag": f"shift-{a['id']}",
            })
            if ok: any_ok = True
            elif err == "expired":
                sb.table("push_subscriptions").delete().eq("id", sub["id"]).execute()
        if any_ok:
            try:
                (sb.table("shift_alerts").update({
                    "delivered_at": datetime.utcnow().isoformat(),
                    "delivered_via": "push",
                }).eq("id", a["id"]).execute())
                delivered += 1
            except Exception: pass
    return delivered
