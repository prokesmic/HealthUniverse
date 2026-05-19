"""Proactive disclosure engine.

The principle: an expert reading a user's query/state runs three parallel
queries — "what did they ask, what do I know, what *adjacent* things should
I volunteer?" Current LLM products only do the first two. This module does
the third: given user profile (+ optional context), it returns the 2-5
highest-value things an expert would surface that the user didn't ask about.

Sources of surfacings, in roughly the order they tend to matter:

  1. Conditional harms       — combos in the user's stack that are risky
                                given a condition/comed they have
  2. Synergies missing       — combos that would help but aren't in stack
  3. Lab-recheck cadence     — labs past due for re-check (or never drawn)
  4. Behavioural Pareto gaps — sleep regularity / movement / eating window /
                                alcohol; the four levers that move 60-70%
                                of chronic-disease outcomes
  5. Stack-condition gap     — well-graded protective edges for their
                                conditions that aren't in their stack
  6. Recent breakthroughs    — general-audience studies touching their
                                stack or conditions in the last 45 days

Each surfacing has the same shape:

  {
    "id":         "uniq-id-for-dedupe",
    "kind":       "harm" | "synergy" | "lab" | "behaviour" | "gap" | "news",
    "title":      "≤90 chars, plain English",
    "why":        "≤180 chars, what this means for you specifically",
    "action":     "≤60 chars, a <30 second next step",
    "action_href":"/...",            # optional deep link
    "tone":       "warning" | "good" | "neutral",
    "score":      float in [0, 100], for ranking
  }

The scoring is `relevance × novelty × actionability`. Novelty comes from a
"already-shown" set the caller can pass in (profile-bound or cookie-bound).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent

# ─── Cached data loads ────────────────────────────────────────────

def _load(name: str) -> dict:
    p = ROOT / "data" / name
    if not p.exists():
        return {}
    return json.loads(p.read_text())


_HARMS    = _load("conditional_harms.json").get("harms", []) or []
_SYNS     = _load("synergies.json").get("synergies", []) or _load("synergies.json").get("rows", []) or []
_LAB_INT  = _load("lab_recheck_intervals.json").get("rules", []) or _load("lab_recheck_intervals.json").get("intervals", []) or []


# ─── Behavioural Pareto questions ─────────────────────────────────
# The four levers that move the most chronic-disease outcomes for the
# average western adult. If we don't know a given lever for a user, we
# ask one question about it (rotated, never more than one per visit).

_PARETO_PROMPTS = [
    {
        "key":   "sleep_regularity_min",
        "kind":  "behaviour",
        "title": "How regular is your bedtime, within 30 minutes?",
        "why":   "Sleep *regularity* — not total duration — is the single biggest behavioural predictor of all-cause mortality and HRV.",
        "action": "Tell us",
        "action_href": "/welcome?topic=sleep",
        "tone":  "neutral",
        "score": 88,
    },
    {
        "key":   "active_minutes_week",
        "kind":  "behaviour",
        "title": "Roughly how many minutes a week do you move above a brisk pace?",
        "why":   "The first 150 minutes a week cut early-death risk by ~27%. Anything below 60/wk is the riskiest place to be.",
        "action": "Estimate it",
        "action_href": "/welcome?topic=movement",
        "tone":  "neutral",
        "score": 86,
    },
    {
        "key":   "eating_window_h",
        "kind":  "behaviour",
        "title": "What's your typical eating window — first food to last food?",
        "why":   "When you eat is a stronger lever on metabolic health than what you eat for most people. A 10-hour window is a low-effort first move.",
        "action": "Pick a window",
        "action_href": "/welcome?topic=eating",
        "tone":  "neutral",
        "score": 82,
    },
    {
        "key":   "alcohol_units_7d",
        "kind":  "behaviour",
        "title": "Drinks per week, roughly?",
        "why":   "Alcohol affects HRV, sleep, liver enzymes, and BP — all your top labs. Even 3-4 drinks/wk shows up.",
        "action": "Add a number",
        "action_href": "/welcome?topic=alcohol",
        "tone":  "neutral",
        "score": 80,
    },
]


# ─── Surfacing builders ───────────────────────────────────────────

def _harm_surfacings(profile: dict) -> list[dict]:
    """Combos in the user's current stack/conditions that are explicitly flagged."""
    stack = set((profile.get("stack") or []))
    conds = set((profile.get("conditions") or []))
    out: list[dict] = []
    for h in _HARMS:
        factor = h.get("factor")
        required = set(h.get("condition_required") or [])
        if factor not in stack:
            continue
        if not (required & (stack | conds)):
            continue
        triggered_by = ", ".join((required & (stack | conds)) or required)
        out.append({
            "id": f"harm:{factor}:{triggered_by}",
            "kind": "harm",
            "title": h.get("label") or f"{factor} + {triggered_by}",
            "why": h.get("context") or h.get("mechanism", "")[:180],
            "action": "Read the mechanism",
            "action_href": f"/me/synergies?focus={factor}",
            "tone": "warning",
            "score": 100 if h.get("severity") == "high" else 80,
        })
    return out


def _synergy_surfacings(profile: dict) -> list[dict]:
    """Synergies where the user has one half but not the other."""
    stack = set((profile.get("stack") or []))
    out: list[dict] = []
    for s in _SYNS:
        pair = s.get("pair") or s.get("factors") or []
        if isinstance(pair, str):
            pair = [p.strip() for p in pair.split("+")]
        if len(pair) < 2:
            continue
        have = set(pair) & stack
        miss = set(pair) - stack
        if len(have) >= 1 and len(miss) >= 1:
            other = list(miss)[0]
            out.append({
                "id": f"synergy:{'+'.join(sorted(pair))}",
                "kind": "synergy",
                "title": s.get("label") or f"{pair[0]} works better with {pair[1]}",
                "why": (s.get("mechanism") or s.get("rationale") or "")[:180],
                "action": f"Read about {other}",
                "action_href": f"/edge/?factor={other}",
                "tone": "good",
                "score": 70,
            })
    return out


def _lab_surfacings(profile: dict, recent_labs: dict | None = None) -> list[dict]:
    """Labs that are past due (or never drawn) for the user's profile.

    `recent_labs` is an optional dict `{lab_name: 'YYYY-MM-DD'}` from the
    client-side store. When missing we still surface the most important
    "never drawn" labs the user's age/conditions imply.
    """
    out: list[dict] = []
    age = profile.get("age") or 40
    sex = profile.get("sex") or "other"
    conds = set((profile.get("conditions") or []))
    recent_labs = recent_labs or {}
    for rule in _LAB_INT:
        lab = rule.get("lab") or rule.get("name")
        if not lab:
            continue
        # Filter by age/sex/condition triggers if present
        if rule.get("age_min") and age < rule["age_min"]:
            continue
        if rule.get("sex") and rule["sex"] != sex and rule["sex"] != "any":
            continue
        if rule.get("if_condition") and not (set(rule["if_condition"]) & conds):
            continue
        cadence_days = rule.get("cadence_days") or 365
        last = recent_labs.get(lab)
        days_since = 9999
        if last:
            try:
                days_since = (date.today() - datetime.fromisoformat(last).date()).days
            except Exception:
                pass
        overdue = days_since > cadence_days
        if not overdue and last:
            continue
        why = (
            f"You haven't drawn this in {days_since} days — recommended every {cadence_days // 30} months for your profile."
            if last else
            f"You haven't drawn this yet. Recommended every {cadence_days // 30} months for your profile."
        )
        out.append({
            "id": f"lab:{lab}",
            "kind": "lab",
            "title": f"Re-check your {lab}",
            "why": why,
            "action": "Add to next blood draw",
            "action_href": f"/me/data?lab={lab}",
            "tone": "neutral",
            "score": 75 - min(days_since // 30, 30),
        })
    return out


def _behaviour_surfacings(profile: dict) -> list[dict]:
    """Pareto-four behaviours. Only surface ones we don't yet know."""
    known = set((profile.get("known_metrics") or []))
    out: list[dict] = []
    for prompt in _PARETO_PROMPTS:
        if prompt["key"] in known:
            continue
        out.append({**prompt, "id": f"behaviour:{prompt['key']}"})
    return out


def _gap_surfacings(profile: dict) -> list[dict]:
    """Well-graded protective edges for the user's conditions that aren't in
    their stack. Pulled from the live corpus (SQLite)."""
    conds = list((profile.get("conditions") or []))
    stack = set((profile.get("stack") or []))
    if not conds:
        return []
    try:
        from db import connect  # type: ignore
    except Exception:
        return []
    out: list[dict] = []
    with connect() as conn:
        rows = conn.execute(
            """SELECT e.id, e.tier, e.direction, e.summary,
                      f.slug AS f_slug, f.name AS f_name,
                      o.slug AS o_slug, o.name AS o_name
               FROM edge e
               JOIN entity f ON f.id=e.factor_id
               JOIN entity o ON o.id=e.outcome_id
               WHERE o.slug IN ({placeholders})
                 AND e.direction='protective'
                 AND e.tier IN ('A','B')
               ORDER BY e.tier, e.id DESC
               LIMIT 60""".format(placeholders=",".join("?" * len(conds))),
            conds,
        ).fetchall()
        for r in rows[:30]:
            if r["f_slug"] in stack:
                continue
            out.append({
                "id": f"gap:{r['id']}",
                "kind": "gap",
                "title": f"You don't have {r['f_name']} in your stack — it's well-graded for {r['o_name']}",
                "why": (r["summary"] or "")[:180],
                "action": "Read the dossier",
                "action_href": f"/edge/{r['id']}",
                "tone": "good",
                "score": 78 if r["tier"] == "A" else 62,
            })
    return out


def _news_surfacings(profile: dict) -> list[dict]:
    """Recent general-audience breakthroughs touching the user's stack or
    conditions in the last 45 days."""
    try:
        from web import breakthroughs as bx
    except Exception:
        return []
    stack = set((profile.get("stack") or []))
    conds = set((profile.get("conditions") or []))
    out: list[dict] = []
    for it in bx.items(audience="general", days=45):
        f = it.get("factor_slug"); o = it.get("outcome_slug")
        if (f and f in stack) or (o and o in conds):
            out.append({
                "id": f"news:{it['id']}",
                "kind": "news",
                "title": it.get("headline", ""),
                "why": (it.get("why_it_matters") or it.get("summary", ""))[:180],
                "action": "Read the breakdown",
                "action_href": f"/breakthroughs/{it['id']}",
                "tone": "good",
                "score": 65 + (10 if f in stack else 0),
            })
    return out


# ─── Public entry point ───────────────────────────────────────────

def surface(
    profile: dict,
    *,
    recent_labs: dict | None = None,
    already_shown: Iterable[str] = (),
    limit: int = 3,
    context: str | None = None,
) -> list[dict]:
    """Return up to `limit` proactive cards for this user.

    `profile`:        a dict-like view of Profile (`asdict`-style is fine).
    `recent_labs`:    {lab_name: 'YYYY-MM-DD'} — comes from client-side store.
    `already_shown`:  surfacing ids the caller has already shown to this
                      user; we skip them so the home page doesn't repeat.
    `context`:        optional factor/outcome slug the user just touched —
                      surfacings related to it get a +20 boost.
    """
    cards = (
        _harm_surfacings(profile)
        + _synergy_surfacings(profile)
        + _lab_surfacings(profile, recent_labs)
        + _gap_surfacings(profile)
        + _news_surfacings(profile)
        + _behaviour_surfacings(profile)
    )

    # Context boost
    if context:
        for c in cards:
            if context.lower() in (c.get("id", "") + c.get("title", "")).lower():
                c["score"] = c.get("score", 0) + 20

    # Already-shown drop
    shown = set(already_shown)
    cards = [c for c in cards if c["id"] not in shown]

    # Dedupe by id, keep highest-score wins
    by_id: dict[str, dict] = {}
    for c in cards:
        if c["id"] not in by_id or c["score"] > by_id[c["id"]]["score"]:
            by_id[c["id"]] = c
    cards = sorted(by_id.values(), key=lambda c: -c["score"])

    # Diversity — avoid 3 cards of the same kind in a row when possible
    out: list[dict] = []
    seen_kinds: dict[str, int] = {}
    for c in cards:
        if len(out) >= limit:
            break
        if seen_kinds.get(c["kind"], 0) >= 2:
            continue
        out.append(c)
        seen_kinds[c["kind"]] = seen_kinds.get(c["kind"], 0) + 1
    return out


# ─── Empty-profile fallback ───────────────────────────────────────

def starter_cards() -> list[dict]:
    """What we show on the home page when we know nothing about the user yet.
    Lead with one Pareto-behaviour prompt + one zero-cost suggestion +
    one trust anchor."""
    return [
        {
            "id": "starter:welcome",
            "kind": "onboarding",
            "title": "One question gets you set up — no form.",
            "why": "Tell us what brought you here today and we'll personalise everything else from that single answer.",
            "action": "Take 30 seconds",
            "action_href": "/welcome",
            "tone": "good",
            "score": 100,
        },
        {
            "id": "starter:wearables",
            "kind": "onboarding",
            "title": "Wear an Apple Watch, Oura, Garmin, Whoop or Polar?",
            "why": "Drop in an export file and we'll pull in your sleep, HRV, and resting heart rate. Strictly local-first.",
            "action": "Import a file",
            "action_href": "/me/wearables",
            "tone": "good",
            "score": 95,
        },
        {
            "id": "starter:pareto-sleep",
            "kind": "behaviour",
            "title": "How regular is your bedtime, within 30 minutes?",
            "why": "Sleep regularity is the single biggest behavioural predictor of all-cause mortality and HRV — even ahead of total sleep.",
            "action": "Tell us",
            "action_href": "/welcome?topic=sleep",
            "tone": "neutral",
            "score": 88,
        },
    ]
