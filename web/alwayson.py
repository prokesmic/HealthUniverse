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

    # ── Move A: lab-recheck cadence
    rechecks_due = due_lab_rechecks(summary)
    # ── Move B: personalised corpus feed (broader than strict watchlist)
    corpus_feed = personal_corpus_feed(account_row["id"], summary)
    # ── Move C: cadence-aware nudges
    schedule_next_nudge_for_recs(account_row["id"])
    nudges = due_nudges(account_row["id"])
    # ── Move D: weekly-checkin anomalies
    checkins = fetch_recent_checkins(account_row["id"], n=12)
    self_anomalies = checkin_anomalies(checkins)
    # ── Move E: stack composition findings
    stack_slugs = [p.get("factor") for p in (active_protos or []) if p.get("factor")]
    recent_lab_names = [l.get("name") for l in (flagged_labs or []) if l.get("name")]
    stack_findings = stack_composition_findings(stack_slugs, recent_lab_names)

    # 2) If there's nothing to say, skip (avoid daily-spam fatigue).
    nothing_to_say = (
        not anomalies and not flagged_labs and not shifts
        and not _due_check_ins(open_recs)
        and not _imminent_visit(next_visit, today)
        and not _due_protocols(active_protos, today)
        and not rechecks_due and not corpus_feed and not nudges
        and not self_anomalies and not stack_findings
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
    for a in self_anomalies:
        pieces.append(
            f"weekly-checkin {a['stream']}: z={a['z']} "
            f"({a['recent_mean']} vs baseline {a['baseline_mean']}); is_bad={a['is_bad']}"
        )
    if flagged_labs:
        for l in flagged_labs[:5]:
            pieces.append(f"lab {l.get('name')} = {l.get('value')} {l.get('unit','')} ({l.get('direction')})")
    for rc in rechecks_due[:3]:
        pieces.append(
            f"LAB RECHECK DUE: {rc['lab_name']} (last {rc['last_date']}, "
            f"next due {rc['next_recheck_due']}, {rc['days_overdue']}d overdue, "
            f"urgency {rc['urgency']})"
        )
    if shifts:
        for s in shifts[:3]:
            pieces.append(
                f"corpus shift: {s.get('f_name')} → {s.get('o_name')} "
                f"{s.get('field')} {s.get('old_value')} → {s.get('new_value')}"
            )
    for cf in corpus_feed[:3]:
        pieces.append(
            f"new corpus signal ({cf.get('source')}): "
            f"{cf.get('f_name')} → {cf.get('o_name')} now {cf.get('tier')}"
        )
    for sf in stack_findings[:3]:
        already = " (already tracking)" if sf.get("already_have_lab") else ""
        pieces.append(f"stack pattern '{sf['key']}': {sf['message']}{already}")
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
    for n in nudges[:3]:
        days_open = 0
        try:
            sug = datetime.fromisoformat((n.get("suggested_at") or "").replace("Z", "+00:00")).replace(tzinfo=None)
            days_open = (datetime.utcnow() - sug).days
        except Exception: pass
        pieces.append(
            f"due nudge: {n.get('edge_label')} (suggested {days_open}d ago, "
            f"class {n.get('intervention_class')})"
        )
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

    # Advance any nudges we just included so they don't refire tomorrow.
    for n in nudges[:3]:
        try:
            advance_nudge(n["id"])
        except Exception:
            pass

    return {
        "generated_for_date": today.isoformat(),
        "headline": parsed.get("headline") or "Daily check-in",
        "observations": parsed.get("observations") or [],
        "actions": parsed.get("actions") or [],
        "doctor_question": parsed.get("doctor_question"),
        "trends_snapshot": {
            "signals_count": len(pieces),
            "shifts_count": len(shifts),
            "rechecks_due_count": len(rechecks_due),
            "corpus_feed_count": len(corpus_feed),
            "nudge_count": len(nudges),
            "self_anomalies_count": len(self_anomalies),
            "stack_findings_count": len(stack_findings),
        },
    }


def _due_check_ins(open_recs: list[dict]) -> bool:
    return any((r.get("days_open") or 0) >= 28 for r in (open_recs or []))


# ─── Lab-recheck cadence (Move A) ──────────────────────────────────


_RECHECK_FILE = None
_RECHECK_CACHE: list[dict] | None = None


def _load_recheck_rules() -> list[dict]:
    """Lazy-load the recheck-interval rules."""
    global _RECHECK_CACHE, _RECHECK_FILE
    if _RECHECK_CACHE is not None:
        return _RECHECK_CACHE
    try:
        from pathlib import Path
        path = Path(__file__).parent.parent / "data" / "lab_recheck_intervals.json"
        _RECHECK_CACHE = (_json.loads(path.read_text()) or {}).get("rules", [])
    except Exception:
        _RECHECK_CACHE = []
    return _RECHECK_CACHE


def _match_rule(lab_name: str, rules: list[dict]) -> Optional[dict]:
    n = (lab_name or "").strip().lower()
    if not n:
        return None
    # Most specific (longest alias) first.
    for rule in sorted(rules, key=lambda r: -max(len(a) for a in r.get("aliases", []) or [""])):
        for alias in rule.get("aliases", []):
            if alias.lower() in n or n in alias.lower():
                return rule
    return None


def due_lab_rechecks(summary: dict) -> list[dict]:
    """Walk the user's flagged_labs against the recheck-interval rules.
    Returns a list of due recheck items, newest-trigger first."""
    rules = _load_recheck_rules()
    if not rules:
        return []
    labs = summary.get("flagged_labs") or []
    stack = summary.get("active_protocols") or []
    stack_factors: set[str] = set()
    for p in stack:
        if p.get("factor"):
            stack_factors.add(p["factor"])
    # Also consider open-recommendation factors (proxy for "started this").
    for r in summary.get("open_recommendations") or []:
        # Heuristic: pull factor from edge_label if it's "X for Y"
        lbl = (r.get("edge_label") or "").lower()
        for tok in lbl.split(" for ")[0:1]:
            stack_factors.add(tok.strip().replace(" ", "_"))
    today = date.today()
    out: list[dict] = []
    seen_keys: set[str] = set()
    # Newest-first per lab name; keep only the most recent.
    by_name: dict[str, dict] = {}
    for lab in labs:
        name = (lab.get("name") or "").lower()
        d = lab.get("date") or ""
        if name not in by_name or d > (by_name[name].get("date") or ""):
            by_name[name] = lab
    for lab in by_name.values():
        rule = _match_rule(lab.get("name", ""), rules)
        if not rule:
            continue
        if rule["key"] in seen_keys:
            continue
        try:
            lab_date = date.fromisoformat((lab.get("date") or today.isoformat())[:10])
        except Exception:
            continue
        weeks_baseline = int(rule.get("weeks") or 26)
        triggered = bool(set(rule.get("triggered_by_stack", []) or []) & stack_factors)
        weeks = int(rule.get("weeks_after_stack_change", weeks_baseline)) if triggered else weeks_baseline
        if weeks >= 9999:
            continue  # once-in-a-lifetime
        next_recheck = lab_date + timedelta(weeks=weeks)
        if today < next_recheck:
            continue
        days_overdue = (today - next_recheck).days
        urgency = rule.get("urgency_if_out_of_range", "low")
        out.append({
            "key": rule["key"],
            "label": rule.get("label") or rule["key"].replace("_", " "),
            "lab_name": lab.get("name"),
            "last_value": lab.get("value"),
            "last_unit": lab.get("unit"),
            "last_date": lab_date.isoformat(),
            "next_recheck_due": next_recheck.isoformat(),
            "days_overdue": days_overdue,
            "weeks_interval": weeks,
            "triggered_by_stack_change": triggered,
            "urgency": urgency,
        })
        seen_keys.add(rule["key"])
    # Sort: most-overdue first.
    out.sort(key=lambda r: -r["days_overdue"])
    return out


# ─── Personalised corpus-shift feed (Move B) ────────────────────────


def personal_corpus_feed(account_id: str, summary: dict, days: int = 7) -> list[dict]:
    """Beyond the strict watchlist: surface ANY recent corpus shift
    that touches the user's tracked conditions, stack factors, or
    genetic profile. Returns top-N ranked by relevance × recency."""
    from db import connect
    out: list[dict] = []
    sb = supabase_service()
    last_seen = None
    if sb is not None:
        try:
            r = (sb.table("corpus_feed_state").select("last_seen_history_at")
                 .eq("account_id", account_id).limit(1).execute())
            rows = list(r.data or [])
            if rows:
                last_seen = rows[0].get("last_seen_history_at")
        except Exception:
            pass
    since = last_seen or (datetime.utcnow() - timedelta(days=days)).isoformat()
    # Collect signals: watchlist edge IDs, active protocol factor slugs,
    # condition slugs from recent recommendations (proxy).
    watch_edges = summary.get("watch_edges") or []
    stack_slugs: list[str] = []
    for p in summary.get("active_protocols") or []:
        if p.get("factor"):
            stack_slugs.append(p["factor"])
    try:
        with connect() as conn:
            # Bucket 1: direct watchlist edge_history shifts.
            shifts: list[dict] = []
            if watch_edges:
                ph = ",".join("?" * len(watch_edges))
                rows = conn.execute(f"""
                    SELECT h.edge_id, h.field, h.old_value, h.new_value, h.changed_at,
                           e.tier, e.direction, f.name AS f_name, o.name AS o_name
                    FROM edge_history h
                    JOIN edge e ON e.id=h.edge_id
                    JOIN entity f ON f.id=e.factor_id
                    JOIN entity o ON o.id=e.outcome_id
                    WHERE h.edge_id IN ({ph}) AND h.changed_at >= ?
                      AND h.field IN ('tier','is_retracted','direction')
                    ORDER BY h.changed_at DESC LIMIT 20""",
                    [*watch_edges, since]).fetchall()
                for r in rows:
                    d = dict(r)
                    d["source"] = "watchlist"
                    d["score"] = 100
                    shifts.append(d)
            # Bucket 2: shifts on edges where a stack-factor matches.
            if stack_slugs:
                ph = ",".join("?" * len(stack_slugs))
                rows = conn.execute(f"""
                    SELECT h.edge_id, h.field, h.old_value, h.new_value, h.changed_at,
                           e.tier, e.direction, f.name AS f_name, o.name AS o_name
                    FROM edge_history h
                    JOIN edge e ON e.id=h.edge_id
                    JOIN entity f ON f.id=e.factor_id
                    JOIN entity o ON o.id=e.outcome_id
                    WHERE f.slug IN ({ph}) AND h.changed_at >= ?
                      AND h.field IN ('tier','is_retracted')
                    ORDER BY h.changed_at DESC LIMIT 20""",
                    [*stack_slugs, since]).fetchall()
                for r in rows:
                    d = dict(r)
                    d["source"] = "stack_factor"
                    d["score"] = 60
                    shifts.append(d)
            # Bucket 3: brand-new tier-A/B edges (last `days` days) whose
            # factor or outcome touches anything in the user's profile.
            rows = conn.execute(f"""
                SELECT e.id AS edge_id, e.tier, e.direction, e.summary,
                       f.slug AS f_slug, f.name AS f_name,
                       o.slug AS o_slug, o.name AS o_name,
                       e.updated_at AS changed_at
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE e.tier IN ('A','B') AND e.updated_at >= ?
                ORDER BY e.updated_at DESC LIMIT 50""",
                [since]).fetchall()
            personal_slugs = set(stack_slugs)
            for r in rows:
                d = dict(r)
                hits = 0
                if d["f_slug"] in personal_slugs: hits += 2
                if d["o_slug"] in personal_slugs: hits += 1
                if hits == 0:
                    continue
                d["source"] = "new_tierA_or_B"
                d["score"] = 40 + hits * 10
                d["field"] = "new_edge"
                d["new_value"] = d["tier"]
                d["old_value"] = ""
                shifts.append(d)
        # Dedupe by edge_id, keep highest-scoring entry.
        best: dict[int, dict] = {}
        for s in shifts:
            eid = s["edge_id"]
            if eid not in best or s["score"] > best[eid]["score"]:
                best[eid] = s
        out = sorted(best.values(), key=lambda s: (-s["score"], s["changed_at"]))[:8]
    except Exception as exc:
        print(f"[alwayson] corpus feed failed: {exc}")
    # Update high-watermark so we don't re-send next time.
    if sb is not None and out:
        try:
            sb.table("corpus_feed_state").upsert({
                "account_id": account_id,
                "last_seen_history_at": datetime.utcnow().isoformat(timespec="seconds"),
            }, on_conflict="account_id").execute()
        except Exception:
            pass
    return out


# ─── Cadence-aware loop closure (Move C) ────────────────────────────


# Per intervention class, the nudge cadence in days from `suggested_at`.
_NUDGE_CADENCE = {
    "sleep":          [7, 21, 56],
    "mood":           [14, 35, 90],
    "energy":         [14, 35, 90],
    "strength":       [28, 56, 84],
    "body_comp":      [28, 56, 84, 168],
    "lipid":          [56, 168],
    "glycaemic":      [90, 180],
    "blood_pressure": [28, 84, 180],
    "cognitive":      [56, 168],
    "general":        [28, 56, 84],
}


def classify_intervention(edge_label: str) -> str:
    """Heuristic classifier for intervention class — used to pick the
    right follow-up cadence."""
    s = (edge_label or "").lower()
    if any(t in s for t in ("sleep", "insomnia", "rem")): return "sleep"
    if any(t in s for t in ("depression", "anxiety", "mood", "stress")): return "mood"
    if any(t in s for t in ("energy", "fatigue", "tiredness")): return "energy"
    if any(t in s for t in ("strength", "muscle", "hypertrophy", "sarcopenia")): return "strength"
    if any(t in s for t in ("weight", "obesity", "body composition", "fat")): return "body_comp"
    if any(t in s for t in ("ldl", "apob", "lipid", "cholesterol", "triglyceride")): return "lipid"
    if any(t in s for t in ("hba1c", "glucose", "insulin resistance", "diabet")): return "glycaemic"
    if any(t in s for t in ("hypertension", "blood pressure", "bp")): return "blood_pressure"
    if any(t in s for t in ("cognit", "memory", "dementia", "alzheimer")): return "cognitive"
    return "general"


def schedule_next_nudge_for_recs(account_id: str) -> int:
    """Walks open recommendations for one account and sets next_nudge_at
    on rows whose cadence-step hasn't been scheduled yet. Returns count
    of rows updated."""
    sb = supabase_service()
    if sb is None: return 0
    try:
        r = (sb.table("recommendations_log").select("*")
             .eq("account_id", account_id).is_("closed_at", "null").execute())
        rows = list(r.data or [])
    except Exception:
        return 0
    updates = 0
    now = datetime.utcnow()
    for rec in rows:
        cls = rec.get("intervention_class") or classify_intervention(rec.get("edge_label", ""))
        cadence = _NUDGE_CADENCE.get(cls, _NUDGE_CADENCE["general"])
        nudge_count = int(rec.get("nudge_count") or 0)
        if nudge_count >= len(cadence):
            continue
        try:
            suggested = datetime.fromisoformat((rec.get("suggested_at") or "").replace("Z", "+00:00"))
            suggested = suggested.replace(tzinfo=None)
        except Exception:
            continue
        next_due = suggested + timedelta(days=cadence[nudge_count])
        try:
            sb.table("recommendations_log").update({
                "next_nudge_at": next_due.isoformat(),
                "intervention_class": cls,
            }).eq("id", rec["id"]).execute()
            updates += 1
        except Exception:
            pass
    return updates


def due_nudges(account_id: str) -> list[dict]:
    """Return open recommendations whose next_nudge_at has elapsed."""
    sb = supabase_service()
    if sb is None: return []
    now = datetime.utcnow().isoformat()
    try:
        r = (sb.table("recommendations_log").select("*")
             .eq("account_id", account_id).is_("closed_at", "null")
             .lte("next_nudge_at", now).execute())
        return list(r.data or [])
    except Exception:
        return []


def advance_nudge(rec_id: str) -> None:
    """Mark a nudge as delivered: increment nudge_count and schedule
    the next nudge if more cadence-steps remain."""
    sb = supabase_service()
    if sb is None: return
    try:
        r = (sb.table("recommendations_log").select("*").eq("id", rec_id).limit(1).execute())
        rows = list(r.data or [])
        if not rows: return
        rec = rows[0]
        cls = rec.get("intervention_class") or "general"
        cadence = _NUDGE_CADENCE.get(cls, _NUDGE_CADENCE["general"])
        new_count = int(rec.get("nudge_count") or 0) + 1
        update = {"nudge_count": new_count}
        if new_count < len(cadence):
            try:
                suggested = datetime.fromisoformat((rec.get("suggested_at") or "").replace("Z", "+00:00")).replace(tzinfo=None)
                next_due = suggested + timedelta(days=cadence[new_count])
                update["next_nudge_at"] = next_due.isoformat()
            except Exception:
                pass
        else:
            update["next_nudge_at"] = None
        sb.table("recommendations_log").update(update).eq("id", rec_id).execute()
    except Exception:
        pass


# ─── Weekly self-report (Move D) ────────────────────────────────────


def fetch_recent_checkins(account_id: str, n: int = 12) -> list[dict]:
    sb = supabase_service()
    if sb is None: return []
    try:
        r = (sb.table("weekly_checkins").select("*").eq("account_id", account_id)
             .order("for_week_start", desc=True).limit(n).execute())
        return list(r.data or [])
    except Exception:
        return []


def checkin_anomalies(rows: list[dict]) -> list[dict]:
    """Detect downtrends or z-score anomalies in the user's weekly
    self-report stream. Same shape as wearable anomalies so the
    briefing renderer treats them uniformly."""
    if len(rows) < 3:
        return []
    import statistics
    out: list[dict] = []
    for field in ("energy", "sleep_quality", "mood", "stress"):
        values = [r[field] for r in rows if r.get(field) is not None]
        if len(values) < 3:
            continue
        recent = values[:2]      # rows are newest-first
        baseline = values[2:]
        if not recent or len(baseline) < 2:
            continue
        baseline_mean = statistics.mean(baseline)
        baseline_sd = statistics.pstdev(baseline) or 1.0
        recent_mean = statistics.mean(recent)
        z = (recent_mean - baseline_mean) / baseline_sd
        # For "stress" higher is worse; flip the sign convention so
        # "is_bad = z > 1.5" works uniformly.
        is_bad = abs(z) >= 1.2 and (
            (field == "stress" and z > 0) or
            (field != "stress" and z < 0)
        )
        if abs(z) >= 1.2:
            out.append({
                "stream": "weekly_" + field,
                "z": round(z, 2),
                "direction": "up" if z > 0 else "down",
                "recent_mean": round(recent_mean, 1),
                "baseline_mean": round(baseline_mean, 1),
                "is_bad": is_bad,
                "n_recent": len(recent), "n_baseline": len(baseline),
                "severity": "high" if abs(z) >= 2.0 else "moderate",
            })
    return out


# ─── Stack composition analysis (Move E) ────────────────────────────


# Curated cluster definitions: when the user's stack contains ≥N items
# from a cluster, surface a follow-up.
_STACK_CLUSTERS = [
    {
        "key": "inflammation",
        "members": ["curcumin", "omega3_high_dose", "boswellia_serrata", "fish_oil",
                    "epa_high_dose", "ginger", "tart_cherry_juice"],
        "threshold": 3,
        "message": "Inflammation cluster detected. Worth tracking hs-CRP if you haven't recently — it tells you whether the stack is actually moving the needle.",
        "suggest_lab": "hs-CRP",
    },
    {
        "key": "sleep",
        "members": ["magnesium_glycinate", "l_theanine", "melatonin", "ashwagandha",
                    "glycine", "valerian_extract", "chamomile", "lavender_aromatherapy"],
        "threshold": 3,
        "message": "Multi-supplement sleep stack. Are you tracking sleep quality (PSQI, Oura, Whoop, or weekly self-report)? Without measurement you can't attribute which is working.",
        "suggest_lab": None
    },
    {
        "key": "cardiometabolic_safety_net",
        "members": ["omega3_high_dose", "vitamin_k2", "coq10", "magnesium",
                    "vitamin_d", "berberine", "garlic_aged_extract"],
        "threshold": 3,
        "message": "Cardiometabolic safety-net stack. The highest-leverage check-in here is ApoB and Lp(a) — fastest, cheapest CV markers.",
        "suggest_lab": "ApoB"
    },
    {
        "key": "cognitive",
        "members": ["bacopa_monnieri", "lion_s_mane_hericium", "alpha_gpc", "citicoline",
                    "phosphatidylserine", "ginkgo_biloba_240mg", "rhodiola_rosea",
                    "panax_ginseng"],
        "threshold": 3,
        "message": "Nootropic stack. Cognitive supplements have notoriously contested evidence — a 28-day n-of-1 protocol with a daily reaction-time or working-memory check is the only way to know whether YOU respond.",
        "suggest_lab": None
    },
    {
        "key": "longevity",
        "members": ["nicotinamide_riboside", "nicotinamide_mononucleotide", "resveratrol",
                    "spermidine", "urolithin_a", "metformin_in_non_diabetics",
                    "low_dose_rapamycin", "fisetin"],
        "threshold": 2,
        "message": "Longevity stack — most of these have early-stage evidence at best. Worth tracking biomarkers of aging (epigenetic age, fasting glucose, hsCRP) if you're investing the cost.",
        "suggest_lab": "biological age panel"
    },
    {
        "key": "androgenic",
        "members": ["tongkat_ali_eurycoma", "fadogia_agrestis", "boron_supplementation",
                    "zinc", "vitamin_d", "dhea_supplementation_men",
                    "testosterone_replacement_hypogonadal"],
        "threshold": 3,
        "message": "T-optimization stack. Without a recent total-and-free testosterone + SHBG panel, you can't tell which interventions are doing anything.",
        "suggest_lab": "Testosterone (total + free), SHBG, estradiol"
    },
    {
        "key": "athletic_performance",
        "members": ["creatine_monohydrate", "beta_alanine", "citrulline_malate",
                    "caffeine_pre_exercise", "nitrate_beetroot_juice", "sodium_bicarbonate"],
        "threshold": 3,
        "message": "Performance stack. The cleanest read is a single n-of-1 protocol per ergogenic — measure the actual performance dependent variable (1RM, time-to-exhaustion, sprint).",
        "suggest_lab": None
    }
]


def stack_composition_findings(stack_slugs: list[str], recent_lab_names: list[str]) -> list[dict]:
    """Detect known stack-pattern clusters in the user's stack and
    surface follow-ups."""
    if not stack_slugs:
        return []
    stack = {s.lower() for s in stack_slugs}
    out: list[dict] = []
    for cluster in _STACK_CLUSTERS:
        members = set(cluster["members"])
        hits = stack & members
        if len(hits) < cluster["threshold"]:
            continue
        suggest = cluster.get("suggest_lab")
        already_have = bool(suggest) and any(suggest.lower().split("(")[0].strip() in (n or "").lower()
                                              for n in recent_lab_names)
        out.append({
            "key": cluster["key"],
            "message": cluster["message"],
            "hits": sorted(hits),
            "suggest_lab": suggest,
            "already_have_lab": already_have,
        })
    # Also surface "you added ≥3 things in 60d" — a separate heuristic.
    return out


def stack_recent_additions(stack_with_dates: list[dict], window_days: int = 60) -> list[dict]:
    """Pull items the user added recently — proxy for 'they're trying
    things and we should help them isolate variables.'"""
    if not stack_with_dates:
        return []
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    out = []
    for item in stack_with_dates:
        added = item.get("added_at")
        if not added: continue
        try:
            ts = datetime.fromisoformat(added.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            continue
        if ts >= cutoff:
            out.append(item)
    return out


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
