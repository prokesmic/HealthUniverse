"""Health Universe web app — FastAPI + Jinja templates."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from datetime import datetime, timedelta  # noqa: E402

from db import connect  # noqa: E402


def datetime_now():
    return datetime.now()
from profile import (COOKIE, Profile, decode, encode, relevance_score,  # noqa
                     make_sync_token, verify_sync_token, _PROFILE_FIELDS)
# Cached-art adapter: looks up data/art_manifest.json and returns either
# the cached <img> snippet or the procedural SVG fallback. Same call
# signatures as the originals in web/illustrations.py.
from web.auth import (                                # noqa: E402
    SESSION_COOKIE, SESSION_MAX_AGE,
    encode_session, decode_session, current_account,
    send_magic_link, exchange_token_for_session,
    supabase_service, require_pro,
)
from web import alwayson                              # noqa: E402
from web import breakthroughs as bx                   # noqa: E402
from web import breakthrough_illos as bx_illos        # noqa: E402
from web import proactive as pro                      # noqa: E402
from web.generated_art import (   # noqa: E402
    edge_svg, hero_svg, featured_card_svg, discovery_card_svg, strength_wave_svg,
)

app = FastAPI(title="Health Universe")
WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

# Make `edge_svg(...)` callable from any Jinja template.
# (Functions in env.globals are hashable, unlike dict-valued globals.)
templates.env.globals["edge_svg"] = edge_svg
templates.env.globals["hero_svg"] = hero_svg
templates.env.globals["featured_card_svg"] = featured_card_svg
templates.env.globals["discovery_card_svg"] = discovery_card_svg
templates.env.globals["strength_wave_svg"] = strength_wave_svg
templates.env.globals["bx_graphic_svg"] = bx.graphic_svg
templates.env.globals["bx_illo_svg"] = bx_illos.illo_svg
templates.env.globals["BX_CATEGORY_LABEL"] = bx.CATEGORY_LABEL
templates.env.globals["BX_CATEGORY_ORDER"] = bx.CATEGORY_ORDER
templates.env.globals["BX_STAGE_LABEL"] = bx.STAGE_LABEL
templates.env.globals["BX_STAGE_TONE"] = bx.STAGE_TONE
templates.env.globals["bx_days_ago"] = bx.days_ago
# Cache-bust static assets when style.css changes on disk.
try:
    _css_mtime = (WEB_DIR / "static" / "style.css").stat().st_mtime
    templates.env.globals["asset_v"] = str(int(_css_mtime))
except Exception:
    templates.env.globals["asset_v"] = "1"


# ---- tier display helpers ----------------------------------------------------
TIER_LABEL = {
    "A": "Strong Evidence",
    "B": "Moderate Evidence",
    "C": "Emerging Evidence",
    "D": "Limited Evidence",
    "X": "Contested",
    "deprecated": "Deprecated",
}
TIER_DOTS = {"A": 5, "B": 4, "C": 3, "D": 2, "X": 3, "deprecated": 1}
DIRECTION_LABEL = {
    "protective": "Beneficial",
    "harmful":    "Harmful",
    "neutral":    "Neutral",
    "u_shaped":   "U-shaped",
    "mixed":      "Mixed",
}
_TEMPLATE_GLOBALS = {
    "TIER_LABEL": TIER_LABEL,
    "TIER_DOTS": TIER_DOTS,
    "DIRECTION_LABEL": DIRECTION_LABEL,
}


def render(request: Request, template: str, ctx: dict) -> HTMLResponse:
    # Always inject the active profile so base.html can render the avatar
    # dropdown without each route having to pass `profile` explicitly.
    nav_profile = ctx.get("profile")
    if nav_profile is None:
        nav_profile = decode(request.cookies.get(COOKIE))
    initials = ""
    if nav_profile and nav_profile.name:
        parts = [p for p in nav_profile.name.split() if p]
        initials = "".join(p[0].upper() for p in parts[:2])
    elif nav_profile and (nav_profile.conditions or nav_profile.stack):
        initials = "ME"
    # Cheap weekly-edges count for the avatar dropdown header. Best-
    # effort — silently 0 on read-only DBs or when the table is missing.
    edges_7d = 0
    try:
        from datetime import timedelta as _td2
        with connect() as _c:
            cutoff = (datetime_now() - _td2(days=7)).strftime("%Y-%m-%d")
            total = _c.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
            edges_7d = _c.execute(
                "SELECT COUNT(*) c FROM edge WHERE created_at >= ?",
                (cutoff,)).fetchone()["c"]
            # Same suppression as _stats(): hide on freshly-seeded corpus.
            if total and edges_7d > total * 0.5:
                edges_7d = 0
    except Exception:
        pass
    return templates.TemplateResponse(request, template, {
        **_TEMPLATE_GLOBALS, **ctx,
        "nav_profile": nav_profile,
        "nav_initials": initials,
        "nav_edges_7d": edges_7d,
    })


# ---- aggregate categories for the home grid ---------------------------------
# Maps a "category" shown in the UI to entity kinds + slug filters.
CATEGORIES = [
    {"slug": "nutrition",        "label": "Nutrition",          "icon": "apple",     "kinds": ("food", "nutrient")},
    {"slug": "supplements",      "label": "Supplements",        "icon": "pill",      "kinds": ("supplement",)},
    {"slug": "lifestyle",        "label": "Lifestyle",          "icon": "leaf",      "kinds": ("behavior",)},
    {"slug": "exercise",         "label": "Exercise",           "icon": "run",       "kinds": ("activity",)},
    {"slug": "sleep",            "label": "Sleep",              "icon": "moon",      "outcomes": ("sleep_quality",)},
    {"slug": "cardiovascular",   "label": "Cardiovascular Health", "icon": "heart",   "outcomes": ("cvd", "hypertension")},
    {"slug": "metabolic",        "label": "Metabolic Health",   "icon": "drop",      "outcomes": ("t2d", "obesity", "insulin_resistance", "nafld")},
    {"slug": "oncology",         "label": "Oncology",           "icon": "atom",      "outcomes": ("colorectal_cancer", "breast_cancer", "prostate_cancer", "lung_cancer")},
    {"slug": "longevity",        "label": "Longevity",          "icon": "infinity",  "outcomes": ("all_cause_mortality",)},
]


def _category_count(conn, cat: dict) -> int:
    if "kinds" in cat:
        placeholders = ",".join("?" * len(cat["kinds"]))
        row = conn.execute(
            f"SELECT COUNT(*) c FROM edge e JOIN entity f ON e.factor_id=f.id "
            f"WHERE f.kind IN ({placeholders})", cat["kinds"]).fetchone()
    else:
        placeholders = ",".join("?" * len(cat["outcomes"]))
        row = conn.execute(
            f"SELECT COUNT(*) c FROM edge e JOIN entity o ON e.outcome_id=o.id "
            f"WHERE o.slug IN ({placeholders})", cat["outcomes"]).fetchone()
    return int(row["c"]) if row else 0


def _stats(conn) -> dict:
    """Live corpus stats with weekly + monthly deltas. Used on /, /stats,
    /methodology, and the avatar dropdown header."""
    from datetime import timedelta as _td
    today = datetime_now()
    cutoff_7  = (today - _td(days=7)).strftime("%Y-%m-%d")
    cutoff_30 = (today - _td(days=30)).strftime("%Y-%m-%d")

    edges   = conn.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
    studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]
    pmids   = conn.execute(
        "SELECT COUNT(DISTINCT pmid) c FROM evidence WHERE pmid IS NOT NULL AND pmid != ''"
    ).fetchone()["c"]
    last    = conn.execute("SELECT MAX(updated_at) m FROM edge").fetchone()["m"]

    edges_7  = conn.execute(
        "SELECT COUNT(*) c FROM edge WHERE created_at >= ?", (cutoff_7,)
    ).fetchone()["c"]
    edges_30 = conn.execute(
        "SELECT COUNT(*) c FROM edge WHERE created_at >= ?", (cutoff_30,)
    ).fetchone()["c"]
    studies_7 = conn.execute(
        "SELECT COUNT(*) c FROM evidence WHERE created_at >= ?", (cutoff_7,)
    ).fetchone()["c"]
    studies_30 = conn.execute(
        "SELECT COUNT(*) c FROM evidence WHERE created_at >= ?", (cutoff_30,)
    ).fetchone()["c"]
    promotions_30 = 0
    try:
        promotions_30 = conn.execute("""
            SELECT COUNT(*) c FROM edge_history
            WHERE field='tier' AND new_value IN ('A','B')
              AND (old_value IS NULL OR old_value NOT IN ('A','B'))
              AND changed_at >= ?""", (cutoff_30,)).fetchone()["c"]
    except Exception:
        pass

    # Suppress deltas during the freshly-seeded phase: if "this week"
    # is >50 % of the total, every edge is < 7 days old → not a real
    # weekly delta, just a fresh corpus. Same for studies.
    if edges and edges_7  > edges  * 0.5: edges_7  = 0
    if edges and edges_30 > edges  * 0.6: edges_30 = 0
    if studies and studies_7  > studies  * 0.5: studies_7  = 0
    if studies and studies_30 > studies  * 0.6: studies_30 = 0
    return {
        "edges": edges,
        "studies": studies,
        "pmids": pmids,
        "updated": last or "—",
        "edges_7d":   edges_7,
        "edges_30d":  edges_30,
        "studies_7d": studies_7,
        "studies_30d": studies_30,
        "promotions_30d": promotions_30,
    }


def _featured(conn, limit: int = 3) -> list[dict]:
    rows = conn.execute("""
        SELECT e.id, e.tier, e.direction, e.summary, e.updated_at, e.created_at,
               e.effect_size, e.effect_quant,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name,
               (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
               (SELECT study_type FROM evidence ev WHERE ev.edge_id=e.id
                ORDER BY CASE study_type
                  WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2
                  WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 1) AS top_study,
               (SELECT MAX(changed_at) FROM edge_history h
                WHERE h.edge_id=e.id AND h.field='tier'
                  AND h.new_value IN ('A','B')
                  AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
               ) AS promoted_at
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE e.tier IN ('A','B','C')
        ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                 e.updated_at DESC
        LIMIT ?""", (limit,)).fetchall()
    out = [dict(r) for r in rows]
    for e in out:
        e["score"] = _importance_score(e)
        e["breakthrough"] = _is_breakthrough(e)
    out.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
    return out


def _new_discoveries(conn, days: int = 14, limit: int = 20) -> list[dict]:
    """Edges that promoted into A/B in the last `days`, OR new edges
    created in the last `days` at tier C or better. Newest first."""
    rows = conn.execute("""
        SELECT DISTINCT e.id, e.tier, e.direction, e.summary, e.updated_at,
               e.effect_size, e.effect_quant,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind,
               (SELECT MAX(changed_at) FROM edge_history h
                WHERE h.edge_id = e.id AND h.field='tier'
                  AND h.new_value IN ('A','B')
                  AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
               ) AS promoted_at,
               (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE (
            -- promoted to A/B recently
            EXISTS (SELECT 1 FROM edge_history h WHERE h.edge_id=e.id
                    AND h.field='tier' AND h.new_value IN ('A','B')
                    AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
                    AND h.changed_at >= datetime('now', ?))
            -- OR newly created at C or better
            OR (e.tier IN ('A','B','C') AND e.created_at >= datetime('now', ?))
        )
        ORDER BY COALESCE(promoted_at, e.created_at) DESC
        LIMIT ?""", (f"-{days} days", f"-{days} days", limit)).fetchall()
    out = [dict(r) for r in rows]
    # Pull top_study so importance score has full input
    if out:
        edge_ids = [e["id"] for e in out]
        ph = ",".join("?" * len(edge_ids))
        ts = conn.execute(
            f"""SELECT edge_id, study_type FROM evidence
                WHERE edge_id IN ({ph})
                ORDER BY edge_id,
                  CASE study_type WHEN 'meta_analysis' THEN 1
                    WHEN 'systematic_review' THEN 2 WHEN 'rct' THEN 3
                    WHEN 'cohort' THEN 4 ELSE 5 END""",
            edge_ids).fetchall()
        best: dict[int, str] = {}
        for r in ts:
            best.setdefault(r["edge_id"], r["study_type"])
        for e in out:
            e["top_study"] = best.get(e["id"])
    for e in out:
        e["score"] = _importance_score(e)
        e["breakthrough"] = _is_breakthrough(e)
    # Most important + most confirmed first; breakthroughs lifted to top
    out.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
    return out


_TIER_W = {"A": 5.0, "B": 3.0, "C": 1.5, "X": 1.0, "D": 0.5, "deprecated": 0.2}
_STUDY_W = {"meta_analysis": 2.0, "systematic_review": 1.6, "rct": 1.2, "cohort": 0.7,
            "case_control": 0.5, "cross_sectional": 0.3, "mechanistic": 0.2}


def _importance_score(e: dict) -> float:
    """Combined importance × confirmation score for ranking discoveries/featured.
    Tier weight + log(n_studies) + top-study quality + direction definiteness +
    recent-promotion boost."""
    import math
    tier = e.get("tier") or "C"
    n = int(e.get("n_studies") or 0)
    top = e.get("top_study") or ""
    direction = e.get("direction") or "mixed"
    score = _TIER_W.get(tier, 0.5)
    score += math.log1p(n) * 0.6                    # confirmation depth
    score += _STUDY_W.get(top, 0.0)                 # quality of best study
    score += 1.0 if direction in ("protective", "harmful") else 0.4
    if e.get("promoted_at"):                        # tier promotion is a signal
        score *= 1.35
    return round(score, 3)


def _is_breakthrough(e: dict) -> bool:
    """Flag genuine evidence shifts — not just freshly-seeded data:
    - tier-promotion event recorded within 30d (A) or 14d (B), AND
    - sufficient depth: ≥4 studies, with at least one meta_analysis or
      systematic_review as the top study type."""
    promoted = (e.get("promoted_at") or "")[:10]
    if not promoted:
        return False
    try:
        days_since = (datetime_now() - datetime.fromisoformat(promoted)).days
    except Exception:
        return False
    n = int(e.get("n_studies") or 0)
    top = e.get("top_study") or ""
    deep = n >= 4 and top in ("meta_analysis", "systematic_review")
    if not deep:
        return False
    if e.get("tier") == "A" and days_since <= 30:
        return True
    if e.get("tier") == "B" and days_since <= 14:
        return True
    return False


PAGE_SIZE = 60


def _classify_query(q: str) -> dict:
    """Detect query intent: helps_with, harms, compare_two, what_changed,
    best_evidence, just_search. Returns intent + extracted slots."""
    import re
    ql = (q or "").lower().strip()
    if not ql:
        return {"intent": "just_search"}
    m = re.match(r"(?:how (?:do i|to)|ways? to)\s+prevent\s+(.+)", ql)
    if m: return {"intent": "prevent", "target": m.group(1).strip("?").strip()}
    m = re.match(r"(?:prevent|avoid(?:ing)? (?:the )?risk of|reduce risk of)\s+(.+)", ql)
    if m: return {"intent": "prevent", "target": m.group(1).strip("?").strip()}
    m = re.match(r"(?:what|things)\s+(?:helps?|improves?|reduces?|prevents?|treats?|works for)\s+(?:with\s+)?(.+)", ql)
    if m: return {"intent": "helps_with", "target": m.group(1).strip("?").strip()}
    m = re.match(r"(?:what|things)\s+(?:harms?|hurts?|causes?|raises?|increases?|worsens?)\s+(?:risk\s+of\s+)?(.+)", ql)
    if m: return {"intent": "harms", "target": m.group(1).strip("?").strip()}
    m = re.match(r"compare\s+(.+?)\s+(?:and|vs)\s+(.+)", ql)
    if m: return {"intent": "compare_two", "a": m.group(1).strip(), "b": m.group(2).strip("?").strip()}
    m = re.match(r"^(.+?)\s+(?:vs|versus)\s+(.+)$", ql)
    if m: return {"intent": "compare_two", "a": m.group(1).strip(), "b": m.group(2).strip("?").strip()}
    m = re.match(r"(?:what\s+changed|changes?)\s+(?:for|in|about)\s+(.+)", ql)
    if m: return {"intent": "what_changed", "target": m.group(1).strip("?").strip()}
    m = re.match(r"(?:best|strongest|highest[- ]quality)\s+evidence\s+(?:for|on|about)\s+(.+)", ql)
    if m: return {"intent": "best_evidence", "target": m.group(1).strip("?").strip()}
    return {"intent": "just_search"}


def _paginate(total: int, page: int) -> dict:
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, pages))
    return {"page": page, "pages": pages, "total": total,
            "has_prev": page > 1, "has_next": page < pages,
            "offset": (page - 1) * PAGE_SIZE}


def _evidence_strength_buckets(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT tier, COUNT(*) c FROM edge GROUP BY tier").fetchall()
    by = {r["tier"]: r["c"] for r in rows}
    return [
        {"tier": "A", "label": "Strong Evidence",   "count": by.get("A", 0),
         "blurb": "Consistent evidence from multiple high-quality studies or meta-analyses."},
        {"tier": "B", "label": "Moderate Evidence", "count": by.get("B", 0),
         "blurb": "Evidence from multiple studies with some limitations or inconsistency."},
        {"tier": "C", "label": "Emerging Evidence", "count": by.get("C", 0),
         "blurb": "Promising early evidence that requires further high-quality research."},
        {"tier": "D", "label": "Limited Evidence",  "count": by.get("D", 0),
         "blurb": "Insufficient evidence to draw conclusions."},
    ]


# ---- routes ------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    p = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        stats = _stats(conn)
        cats = [{**c, "count": _category_count(conn, c)} for c in CATEGORIES]
        featured = _featured(conn, limit=12)
        buckets = _evidence_strength_buckets(conn)
        discoveries = _new_discoveries(conn, days=14, limit=8)
    if any([p.conditions, p.goals, p.stack]):
        featured.sort(key=lambda e: -relevance_score(e, p))
    # Rotate the spotlight daily so the homepage feels alive: pick by
    # day-of-year against the larger 12-edge featured pool, then take
    # the next 4 starting from there.
    spotlight = None
    if featured:
        idx = datetime_now().timetuple().tm_yday % len(featured)
        spotlight = featured[idx]
        featured = (featured[idx:] + featured[:idx])[:4]
    else:
        featured = []
    # Breakthroughs band — top 8, most-recent first, general audience only.
    # Tab filtering happens client-side against the data we ship.
    breakthroughs_top = bx.items(limit=8, days=45, audience="general")
    # Tab counts mirror the same filter so the numbers add up to what's
    # actually in the lane.
    breakthroughs_cats: dict[str, int] = {}
    for r in breakthroughs_top:
        cat = r.get("category", "other")
        breakthroughs_cats[cat] = breakthroughs_cats.get(cat, 0) + 1
    return render(request, "home.html", {
        "stats": stats, "categories": cats,
        "featured": featured, "buckets": buckets, "spotlight": spotlight,
        "profile": p, "discoveries": discoveries,
        "breakthroughs_top": breakthroughs_top,
        "breakthroughs_cats": breakthroughs_cats,
    })


# ─── Breakthroughs ────────────────────────────────────────────────

@app.get("/breakthroughs", response_class=HTMLResponse)
def breakthroughs_index(request: Request, category: str = "all", stage: str = "all",
                        show: str = "general"):
    """`?show=all` opens the firehose (technical items too) — useful for admin."""
    audience = None if show == "all" else "general"
    rows = bx.items(category=None if category == "all" else category, audience=audience)
    if stage != "all":
        rows = [r for r in rows if r.get("stage") == stage]
    return render(request, "breakthroughs.html", {
        "title": "Breakthroughs",
        "rows": rows,
        "active_category": category,
        "active_stage": stage,
        "category_counts": bx.category_counts(audience=audience),
        "feed_updated_at": bx.load_feed().get("updated_at"),
        "show": show,
    })


@app.get("/breakthroughs/{item_id}", response_class=HTMLResponse)
def breakthrough_detail(request: Request, item_id: str):
    item = bx.get(item_id)
    if not item:
        return HTMLResponse("Not found", status_code=404)
    # Try to find a corpus edge match (lazy — JSON may have stale edge_id).
    edge_id = item.get("edge_id") or bx.match_corpus(
        item.get("factor_slug"), item.get("outcome_slug"))
    return render(request, "breakthrough_detail.html", {
        "title": item["headline"],
        "item": item,
        "edge_id": edge_id,
    })


@app.get("/api/me/proactive")
def me_proactive(request: Request, context: str = "", limit: int = 3,
                 already: str = ""):
    """Proactive disclosure engine — returns 2-3 surfacings the user didn't
    ask for but an expert would volunteer. See web/proactive.py."""
    from dataclasses import asdict
    p = decode(request.cookies.get(COOKIE))
    profile_dict = asdict(p)
    # Optional client-passed already-shown ids to avoid repeats
    shown = [s for s in already.split(",") if s.strip()]
    # Cookie-level recent_labs isn't tracked; the client can POST richer
    # context via /api/me/proactive-rich (future). For now, accept zero.
    try:
        cards = pro.surface(
            profile_dict,
            already_shown=shown,
            limit=limit,
            context=context or None,
        )
    except Exception as exc:
        cards = []
    # Always return at least a starter set so the home band never goes empty.
    if not cards:
        cards = pro.starter_cards()
    return {"cards": cards[:limit]}


# ─── Conversational onboarding (single question, branching) ──────

@app.get("/welcome", response_class=HTMLResponse)
def welcome(request: Request, topic: str = ""):
    """1-question onboarding: 'What brought you here today?' branches to a
    single contextual follow-up per topic. Accumulates the profile silently."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "welcome.html", {
        "title": "Welcome",
        "profile": p,
        "topic": topic,
    })


@app.post("/welcome", response_class=HTMLResponse)
def welcome_submit(request: Request,
                   topic: str = Form(""),
                   answer: str = Form(""),
                   detail: str = Form("")):
    """Save a single answer to the profile cookie. Re-renders the same page
    showing the next contextual question, or redirects home when done."""
    p = decode(request.cookies.get(COOKIE))
    # Stash everything in profile.goals + a stash field; cookie is small.
    known = set(getattr(p, "goals", []) or [])
    if topic and answer:
        known.add(f"{topic}:{answer}")
    if detail:
        known.add(f"{topic}_detail:{detail[:60]}")
    p.goals = list(known)
    # If we collected ≥ 4 levers, route home; otherwise show next step.
    pareto = [g for g in p.goals if g.startswith(("sleep:", "movement:", "eating:", "alcohol:"))]
    done = len(pareto) >= 1   # one is enough for v1 — single-question principle
    resp = RedirectResponse("/" if done else f"/welcome?topic={topic}", status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    return resp


# ─── Wearable file-import (multi-vendor) ─────────────────────────

@app.get("/me/wearables", response_class=HTMLResponse)
def me_wearables(request: Request):
    p = decode(request.cookies.get(COOKIE))
    return render(request, "wearables.html", {
        "title": "Connect a wearable",
        "profile": p,
    })


@app.get("/admin/breakthrough-orphans", response_class=HTMLResponse)
def breakthrough_orphans(request: Request):
    """Items that don't yet match a corpus edge — the seeding queue.
    Beta-pro gated to avoid noise from anonymous users."""
    orphans_list = bx.orphans()
    # Re-attempt match on each render so the count drops as edges are seeded.
    for o in orphans_list:
        o["_match_attempt"] = bx.match_corpus(o.get("factor_slug"), o.get("outcome_slug"))
    # Count candidates that would land in a Codex brief (excl. recalls, low strength,
    # missing slugs, freshly-matched).
    from web.orphan_brief import candidate_orphans as _co
    brief_count = len(_co(min_strength=0.6))
    return render(request, "breakthrough_orphans.html", {
        "title": "Breakthrough orphans",
        "orphans": orphans_list,
        "brief_count": brief_count,
    })


@app.get("/admin/breakthrough-orphans/brief")
def breakthrough_orphans_brief(min_strength: float = 0.6, download: int = 0):
    """Generate the Codex/Claude seeding brief as markdown.
    `?download=1` forces a file download; otherwise renders inline as text/plain
    so the brief is copy-pastable from the browser."""
    from web.orphan_brief import build_brief
    md, _meta = build_brief(min_strength=min_strength)
    headers = {}
    if download:
        from datetime import date as _d
        headers["Content-Disposition"] = (
            f'attachment; filename="codex_orphans_{_d.today().isoformat()}.md"'
        )
    return Response(content=md, media_type="text/markdown; charset=utf-8", headers=headers)


@app.get("/prevent", response_class=HTMLResponse)
def prevent_page(request: Request, q: str = "", condition: str = ""):
    """User enters a condition they want to prevent. We show what to DO
    (protective edges, ranked by importance) and what to AVOID (harmful /
    u_shaped / mixed risk edges, ranked by importance)."""
    query = (q or condition or "").strip()
    do_rows: list[dict] = []
    hard_rows: list[dict] = []
    caution_rows: list[dict] = []
    matched: dict | None = None
    suggestions: list[dict] = []
    with connect() as conn:
        outcomes = conn.execute(
            "SELECT slug, name, kind FROM entity WHERE kind IN "
            "('condition','outcome','marker') ORDER BY name").fetchall()
        outcomes = [dict(r) for r in outcomes]
        if query:
            ql = query.lower()
            # Exact slug, exact name, contained-in name
            matched = next((o for o in outcomes if o["slug"] == ql), None)
            if not matched:
                matched = next((o for o in outcomes if o["name"].lower() == ql), None)
            if not matched:
                matches = [o for o in outcomes if ql in o["name"].lower()]
                if len(matches) == 1:
                    matched = matches[0]
                else:
                    suggestions = matches[:8]
        if matched:
            base = """
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       e.created_at, e.effect_size, e.effect_quant,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name,
                       (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
                       (SELECT study_type FROM evidence ev WHERE ev.edge_id=e.id
                        ORDER BY CASE study_type WHEN 'meta_analysis' THEN 1
                          WHEN 'systematic_review' THEN 2 WHEN 'rct' THEN 3
                          WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 1) AS top_study,
                       (SELECT MAX(changed_at) FROM edge_history h
                        WHERE h.edge_id=e.id AND h.field='tier'
                          AND h.new_value IN ('A','B')
                          AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
                       ) AS promoted_at
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE o.slug = ?
                  AND e.tier IN ('A','B','C','X')
                  AND e.direction = ?
            """
            protective = conn.execute(base, (matched["slug"], "protective")).fetchall()
            harmful = conn.execute(base, (matched["slug"], "harmful")).fetchall()
            ushape = conn.execute(base, (matched["slug"], "u_shaped")).fetchall()
            mixed = conn.execute(base, (matched["slug"], "mixed")).fetchall()
            do_rows = [dict(r) for r in protective]
            hard_rows = [dict(r) for r in harmful]              # linear / strong harm
            caution_rows = [dict(r) for r in ushape] + [dict(r) for r in mixed]
            for e in do_rows + hard_rows + caution_rows:
                e["score"] = _importance_score(e)
                e["breakthrough"] = _is_breakthrough(e)
            for lst in (do_rows, hard_rows, caution_rows):
                lst.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
    return render(request, "prevent.html", {
        "title": "Prevent",
        "query": query,
        "matched": matched,
        "suggestions": suggestions,
        "do_rows": do_rows[:20],
        "hard_rows": hard_rows[:14],
        "caution_rows": caution_rows[:10],
        "outcomes": outcomes,
    })


def _og_template(eyebrow: str, title: str, summary: str, accent: str = "#1f3a2e",
                 footer: str = "health-universe.vercel.app") -> str:
    """Shared 1200×630 OG-card template — gold ribbon footer, decorative
    globe in the upper right, large serif title, summary text."""
    def esc(s: str) -> str:
        return (s.replace("&","&amp;").replace("<","&lt;")
                 .replace(">","&gt;").replace('"',"&quot;"))
    title = title if len(title) <= 64 else title[:61] + "…"
    summary = summary[:200] + ("…" if len(summary) > 200 else "")
    eyebrow = eyebrow.upper()[:42]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fffaf0"/>
      <stop offset="100%" stop-color="#f5ead0"/>
    </linearGradient>
    <linearGradient id="ribbon" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#caa257"/>
      <stop offset="50%" stop-color="#f0d990"/>
      <stop offset="100%" stop-color="#caa257"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <g opacity="0.22">
    <circle cx="1020" cy="310" r="220" fill="none" stroke="#c9a961" stroke-width="2"/>
    {''.join(f'<ellipse cx="1020" cy="310" rx="220" ry="{40+i*22}" fill="none" stroke="#c9a961" stroke-width="0.8"/>' for i in range(8))}
    {''.join(f'<ellipse cx="1020" cy="310" rx="{40+i*22}" ry="220" fill="none" stroke="#c9a961" stroke-width="0.8"/>' for i in range(8))}
  </g>
  <text x="80" y="100" font-family="Inter, sans-serif" font-weight="700"
        font-size="22" letter-spacing="6" fill="#1f3a2e">HEALTH UNIVERSE</text>
  <rect x="76" y="130" width="{16 + len(eyebrow)*11}" height="36" rx="6" fill="{accent}"/>
  <text x="84" y="155" font-family="Inter, sans-serif" font-weight="700"
        font-size="14" letter-spacing="2.2" fill="#fffaf0">{esc(eyebrow)}</text>
  <text x="80" y="240" font-family="Fraunces, serif" font-weight="500"
        font-size="56" fill="#1f3a2e">{esc(title)}</text>
  <foreignObject x="80" y="280" width="900" height="280">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:400 22px/1.45 Inter, sans-serif; color:#4a5b51;">
      {esc(summary)}
    </div>
  </foreignObject>
  <text x="80" y="595" font-family="Inter, sans-serif" font-weight="500"
        font-size="16" fill="#7c6c4d">{esc(footer)}</text>
  <rect x="0" y="610" width="1200" height="20" fill="url(#ribbon)"/>
</svg>"""


@app.get("/api/cron/digest")
def cron_digest(request: Request):
    """Vercel Cron entry point. Sends the weekly digest to all subscribers.
    Auth: Vercel sets the Authorization header to "Bearer ${CRON_SECRET}"
    when invoking. Reject anyone else.

    Configure in vercel.json:
        { "crons": [{"path": "/api/cron/digest", "schedule": "0 7 * * SUN"}] }
    plus env CRON_SECRET and RESEND_API_KEY (or SMTP_* for SMTP path).
    """
    import os
    expected = os.environ.get("CRON_SECRET")
    auth = request.headers.get("authorization", "")
    if expected and auth != f"Bearer {expected}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
    if not sub_file.exists():
        return JSONResponse({"sent": 0, "note": "no subscribers"})
    try:
        import json as _json
        subs = _json.loads(sub_file.read_text())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    sent = 0
    errors: list[dict] = []
    for s in subs:
        try:
            from digest_send import render_digest_html, send_smtp
            subject, html = render_digest_html(s.get("profile_snapshot", {}))
            if os.environ.get("RESEND_API_KEY"):
                _resend_send(s["email"], subject, html)
            elif os.environ.get("SMTP_USER"):
                send_smtp(s["email"], subject, html)
            else:
                continue                              # no transport configured
            sent += 1
        except Exception as exc:
            errors.append({"email": s.get("email"), "error": str(exc)[:200]})
    return JSONResponse({"sent": sent, "errors": errors})


@app.get("/api/cron/proactive-weekly")
def cron_proactive_weekly(request: Request):
    """Sunday-morning briefing email. Cron runs us at 0 7 * * SUN.
    For each subscriber on the Pro waitlist (or the existing
    subscribers list), send a teaser email with this week's corpus
    deltas + a deep link to /me/briefing where the personal section
    renders client-side from their localStorage.

    Personal data NEVER transits this endpoint or the email body —
    only public corpus news goes in. The personal half is generated
    when the user clicks through to the briefing page.
    """
    import os
    expected = os.environ.get("CRON_SECRET")
    auth = request.headers.get("authorization", "")
    if expected and auth != f"Bearer {expected}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    # Pull this week's corpus deltas once (same content for every email).
    since = (datetime_now() - timedelta(days=7)).isoformat(timespec="seconds")
    with connect() as conn:
        promotions = conn.execute("""
            SELECT h.edge_id, h.old_value, h.new_value, h.changed_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id=h.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE h.field='tier' AND h.new_value IN ('A','B')
              AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
              AND h.changed_at >= ?
            ORDER BY h.changed_at DESC
            LIMIT 8""", (since,)).fetchall()
        retractions = conn.execute("""
            SELECT h.edge_id, h.changed_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id=h.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE h.field='is_retracted' AND h.new_value='1'
              AND h.changed_at >= ?
            ORDER BY h.changed_at DESC
            LIMIT 4""", (since,)).fetchall()
    promotions = [dict(r) for r in promotions]
    retractions = [dict(r) for r in retractions]

    base = os.environ.get("HU_BASE_URL", "https://health-universe.vercel.app")
    body_lines = [
        f"<h1 style='font-family:Georgia,serif'>Your weekly briefing</h1>",
        f"<p>Open your personalised briefing — anomalies, watchlist shifts, "
        f"loops to close, protocol nudges, and cross-data correlations all "
        f"render in your browser from your local data.</p>",
        f"<p><a href='{base}/me/briefing' "
        f"style='display:inline-block;padding:10px 18px;background:#1f3a2e;color:#fffaf0;"
        f"border-radius:8px;text-decoration:none;font-weight:600'>"
        f"Open my briefing →</a></p>",
        f"<hr style='margin:24px 0;border:none;border-top:1px solid #ddd'>",
        f"<h2 style='font-family:Georgia,serif;font-size:18px'>What changed in the corpus this week</h2>",
    ]
    if promotions:
        body_lines.append("<h3 style='font-size:14px;margin:18px 0 6px'>↑ Promoted to tier A or B</h3><ul>")
        for p in promotions:
            body_lines.append(f"<li><a href='{base}/edge/{p['edge_id']}'>"
                              f"{p['f_name']} → {p['o_name']}</a> "
                              f"(now <b>{p['new_value']}</b>; was {p['old_value'] or '—'})</li>")
        body_lines.append("</ul>")
    if retractions:
        body_lines.append("<h3 style='font-size:14px;margin:18px 0 6px'>⚠ Retractions</h3><ul>")
        for r in retractions:
            body_lines.append(f"<li><a href='{base}/edge/{r['edge_id']}'>"
                              f"{r['f_name']} → {r['o_name']}</a></li>")
        body_lines.append("</ul>")
    if not promotions and not retractions:
        body_lines.append("<p>The corpus was quiet this week — no tier promotions or retractions.</p>")
    body_lines.append(
        "<p style='font-size:12px;color:#666;margin-top:24px'>"
        "You're receiving this because you opted in on the Stack Brief or briefing page. "
        f"<a href='{base}/me/briefing'>Manage email</a>."
        "</p>"
    )
    html = "\n".join(body_lines)

    # Source-of-truth for who gets the Sunday email is now Supabase:
    # 1) accounts.cron_subscribed = true (the real users)
    # 2) pro_waitlist (anonymous email captures from /stack and the
    #    briefing-page subscribe form, before they signed in)
    # 3) data/subscribers.json (legacy fallback for any old subscribers
    #    not yet migrated)
    subs: list = []
    seen: set = set()

    sb = supabase_service()
    if sb is not None:
        try:
            r = sb.table("accounts").select("email").eq("cron_subscribed", True).execute()
            for row in (r.data or []):
                em = (row.get("email") or "").lower().strip()
                if em and em not in seen:
                    subs.append({"email": em, "src": "account"}); seen.add(em)
        except Exception as exc:
            print(f"[cron] supabase accounts read failed: {exc}")
        try:
            r = sb.table("pro_waitlist").select("email").execute()
            for row in (r.data or []):
                em = (row.get("email") or "").lower().strip()
                if em and em not in seen:
                    subs.append({"email": em, "src": "waitlist"}); seen.add(em)
        except Exception as exc:
            print(f"[cron] supabase waitlist read failed: {exc}")

    # Legacy fallback — early subscribers who landed before Supabase.
    sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
    if sub_file.exists():
        try:
            import json as _json
            for s in _json.loads(sub_file.read_text()):
                em = (s.get("email") or "").lower().strip()
                if em and em not in seen:
                    subs.append({"email": em, "src": "legacy"}); seen.add(em)
        except Exception:
            pass

    sent = 0
    errors: list[dict] = []
    if not os.environ.get("RESEND_API_KEY"):
        return JSONResponse({"sent": 0, "note": "RESEND_API_KEY not set"})
    for s in subs:
        try:
            _resend_send(s["email"], "Health Universe — your weekly briefing", html)
            sent += 1
        except Exception as exc:
            errors.append({"email": s.get("email"), "error": str(exc)[:200]})
    return JSONResponse({
        "sent": sent,
        "promotions": len(promotions),
        "retractions": len(retractions),
        "errors": errors,
    })


def _resend_send(to_addr: str, subject: str, html: str) -> None:
    import os
    import httpx
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
        json={
            "from": os.environ.get("RESEND_FROM", "Health Universe <onboarding@resend.dev>"),
            "to": [to_addr],
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    r.raise_for_status()


@app.get("/manifest.webmanifest")
def webmanifest():
    """PWA manifest. Lets users 'Add to Home Screen' on iOS/Android, run
    fullscreen, and get the app a proper icon + name."""
    from fastapi.responses import JSONResponse
    return JSONResponse({
        "name": "Health Universe",
        "short_name": "HU",
        "description": "Evidence-grounded prevention coach.",
        "start_url": "/?source=pwa",
        "display": "standalone",
        "background_color": "#fdf6e3",
        "theme_color": "#1f3a2e",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "categories": ["health", "education", "lifestyle"],
    }, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/favicon.svg")
def favicon_svg():
    """Inline procedural favicon — globe + gold ring."""
    from fastapi.responses import Response
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#1f3a2e"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="#c9a961" stroke-width="2"/>
  <ellipse cx="32" cy="32" rx="22" ry="9" fill="none" stroke="#c9a961" stroke-width="1.5"/>
  <ellipse cx="32" cy="32" rx="9" ry="22" fill="none" stroke="#c9a961" stroke-width="1.5"/>
  <circle cx="32" cy="32" r="3" fill="#f0d990"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/og.svg")
def og_default():
    from fastapi.responses import Response
    svg = _og_template(
        eyebrow="EVIDENCE YOU CAN TRUST",
        title="The living map of nutrition,\nlifestyle, and disease risk",
        summary=("Continuously updated PMID-verified evidence for "
                 "cardiovascular health, metabolic health, oncology, "
                 "sleep, and longevity."),
    )
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/og/prevent/{slug}.svg")
def og_prevent(slug: str):
    from fastapi.responses import Response
    with connect() as conn:
        row = conn.execute(
            "SELECT slug, name FROM entity WHERE slug=? OR LOWER(name)=LOWER(?) LIMIT 1",
            (slug, slug.replace("-", " "))).fetchone()
        if not row:
            return Response(status_code=404, content="not found")
        # Top 3 protective + harmful for snippet
        prot = conn.execute("""
            SELECT f.name FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE o.slug=? AND e.direction='protective' AND e.tier IN ('A','B')
            ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END LIMIT 3""",
            (row["slug"],)).fetchall()
        harm = conn.execute("""
            SELECT f.name FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE o.slug=? AND e.direction='harmful' AND e.tier IN ('A','B')
            ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END LIMIT 3""",
            (row["slug"],)).fetchall()
    do_list = ", ".join(r["name"] for r in prot) or "—"
    avoid_list = ", ".join(r["name"] for r in harm) or "—"
    summary = f"DO: {do_list}.   AVOID: {avoid_list}."
    svg = _og_template(
        eyebrow=f"PREVENTION PLAYBOOK",
        title=f"Prevent {row['name']}",
        summary=summary,
        footer=f"health-universe.vercel.app/prevent?q={row['slug']}",
    )
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/og/category/{slug}.svg")
def og_category(slug: str):
    from fastapi.responses import Response
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return Response(status_code=404, content="not found")
    with connect() as conn:
        if "kinds" in cat:
            ph = ",".join("?" * len(cat["kinds"]))
            n = conn.execute(f"SELECT COUNT(*) c FROM edge e JOIN entity f ON f.id=e.factor_id WHERE f.kind IN ({ph})",
                             cat["kinds"]).fetchone()["c"]
        else:
            ph = ",".join("?" * len(cat["outcomes"]))
            n = conn.execute(f"SELECT COUNT(*) c FROM edge e JOIN entity o ON o.id=e.outcome_id WHERE o.slug IN ({ph})",
                             cat["outcomes"]).fetchone()["c"]
    svg = _og_template(
        eyebrow="EVIDENCE LIBRARY",
        title=cat["label"],
        summary=f"{n} PMID-verified factor → outcome relationships in this category, "
                "ranked by tier and effect size. Filter by tier, direction, or outcome.",
        footer=f"health-universe.vercel.app/category/{slug}",
    )
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/og/edge/{edge_id}.svg")
def og_edge_svg(edge_id: int):
    """Procedural OG share card for an edge — 1200×630 SVG so links to
    /edge/{id} preview nicely in Slack, iMessage, X, LinkedIn."""
    from fastapi.responses import Response
    with connect() as conn:
        row = conn.execute("""
            SELECT e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                   f.name AS f_name, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE e.id=?""", (edge_id,)).fetchone()
    if not row:
        return Response(status_code=404, content="Not found")
    e = dict(row)
    tier = e["tier"] or "C"
    tier_color = {"A":"#1f3a2e","B":"#3b8e5a","C":"#c9a961","X":"#a3552c","D":"#7c6c4d"}.get(tier, "#7c6c4d")
    tier_label = {"A":"STRONG EVIDENCE","B":"MODERATE EVIDENCE","C":"EMERGING EVIDENCE",
                  "X":"CONTESTED","D":"LIMITED"}.get(tier, "EVIDENCE")
    title = f"{e['f_name']} → {e['o_name']}"
    if len(title) > 64:
        title = title[:61] + "…"
    summary = (e["summary"] or "")[:170]
    if len(e.get("summary") or "") > 170: summary += "…"
    effect = e.get("effect_quant") or ""
    if len(effect) > 140: effect = effect[:137] + "…"

    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fffaf0"/>
      <stop offset="100%" stop-color="#f5ead0"/>
    </linearGradient>
    <linearGradient id="ribbon" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#caa257"/>
      <stop offset="50%" stop-color="#f0d990"/>
      <stop offset="100%" stop-color="#caa257"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <!-- decorative globe -->
  <g opacity="0.28">
    <circle cx="1020" cy="310" r="220" fill="none" stroke="#c9a961" stroke-width="2"/>
    {''.join(f'<ellipse cx="1020" cy="310" rx="220" ry="{40+i*22}" fill="none" stroke="#c9a961" stroke-width="0.8"/>' for i in range(8))}
    {''.join(f'<ellipse cx="1020" cy="310" rx="{40+i*22}" ry="220" fill="none" stroke="#c9a961" stroke-width="0.8"/>' for i in range(8))}
  </g>
  <!-- brand -->
  <text x="80" y="100" font-family="Inter, sans-serif" font-weight="700"
        font-size="22" letter-spacing="6" fill="#1f3a2e">HEALTH UNIVERSE</text>
  <!-- tier ribbon -->
  <rect x="76" y="130" width="{16 + len(tier_label)*11}" height="36" rx="6" fill="{tier_color}"/>
  <text x="{84}" y="155" font-family="Inter, sans-serif" font-weight="700"
        font-size="14" letter-spacing="2.2" fill="#fffaf0">{esc(tier_label)}</text>
  <!-- title -->
  <text x="80" y="240" font-family="Fraunces, serif" font-weight="500"
        font-size="56" fill="#1f3a2e">{esc(title)}</text>
  <!-- summary -->
  <foreignObject x="80" y="280" width="900" height="180">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:400 22px/1.45 Inter, sans-serif; color:#4a5b51;">
      {esc(summary)}
    </div>
  </foreignObject>
  <!-- effect -->
  {f'<rect x="80" y="490" width="900" height="68" rx="10" fill="#fbf3df" stroke="#c9a961"/>' if effect else ''}
  {f'<foreignObject x="96" y="500" width="880" height="56"><div xmlns="http://www.w3.org/1999/xhtml" style="font:600 18px/1.4 Inter, sans-serif; color:#4a3920;">📊 {esc(effect)}</div></foreignObject>' if effect else ''}
  <!-- footer ribbon -->
  <rect x="0" y="610" width="1200" height="20" fill="url(#ribbon)"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


# Dose-suffix patterns to collapse N versions of the same factor (e.g.
# walking_4000_steps / 7000_steps / 10000_steps) into one card with a
# "dose-response" microline.
import re as _re_plan
_DOSE_SUFFIX_RE = _re_plan.compile(
    r"_(\d{1,5})_?(?:steps|min(?:utes?)?|mg|g|ml|iu|hours?|servings?|cups?|caps?)$"
)

# Map from entity.kind → display bucket on the plan page. Buckets are
# ordered so the page reads top-down: lifestyle first (highest leverage,
# zero cost), diet next, then supplements, then drugs, then a catch-all.
_DO_BUCKETS = [
    ("lifestyle", "Lifestyle & habits", ("activity", "behavior")),
    ("diet",      "Diet & food",        ("food", "nutrient")),
    ("supplement","Supplements",        ("supplement",)),
    ("drug",      "Medications",        ("drug",)),
    ("other",     "Other",              ("environmental", "process", "biomarker", "condition", "gene", "pathogen", None)),
]
# Hard-avoid buckets: behaviors/exposures vs biomarkers vs conditions.
_HARD_BUCKETS = [
    ("behaviors",  "Behaviors & exposures", ("activity", "behavior", "food", "drug", "supplement", "environmental")),
    ("biomarkers", "Biomarkers to monitor", ("biomarker", "nutrient")),
    ("conditions", "Conditions to manage",  ("condition", "process", "gene", "pathogen", None)),
]


def _kind_bucket(kind: str | None, buckets: list[tuple]) -> str:
    """Return the bucket key for a given entity.kind."""
    for key, _label, kinds in buckets:
        if kind in kinds:
            return key
    return buckets[-1][0]


def _dose_root(slug: str) -> str:
    """Strip a trailing dose suffix so dose-response variants collapse.
    Example: walking_4000_steps → walking, vitamin_d_2000_iu → vitamin_d."""
    return _DOSE_SUFFIX_RE.sub("", slug or "")


def _three_axis_labels(e: dict) -> dict:
    """Replace the magic-number ★ score with three plain-text axes a
    user can actually compare. Returns the labels the template renders."""
    tier = e.get("tier") or "C"
    overlap = e.get("n_overlap") or 1
    eff = (e.get("effect_size") or "").lower()
    if eff in ("large", "very_large"):
        eff_label = "large effect"
    elif eff == "moderate":
        eff_label = "moderate effect"
    elif eff == "small":
        eff_label = "small effect"
    else:
        eff_label = ""
    return {
        "tier_label":   {"A":"Strong evidence","B":"Moderate evidence",
                         "C":"Emerging","D":"Weak","X":"Contested"}.get(tier, tier),
        "overlap_label": (f"helps {overlap} of your conditions"
                          if overlap > 1 else "helps 1 condition"),
        "effect_label": eff_label,
    }


@app.get("/my-plan", response_class=HTMLResponse)
def my_plan(request: Request):
    """Aggregate /prevent across every condition the user is tracking.
    Dedupe protective and harmful factors across conditions, count overlap
    so the highest-leverage moves bubble up. Group by entity.kind so a
    user sees lifestyle / diet / supplements / drugs as separate sections
    instead of one flat list. Collapse dose-response variants into a
    single card. Mark items already in the user's stack."""
    p = decode(request.cookies.get(COOKIE))
    targets = list(p.conditions or [])
    stack_set = set(p.stack or [])
    matched_outcomes: list[dict] = []
    do_buckets = {b[0]: [] for b in _DO_BUCKETS}
    hard_buckets = {b[0]: [] for b in _HARD_BUCKETS}
    caution_list: list[dict] = []
    starters: list[dict] = []
    if targets:
        with connect() as conn:
            placeholders = ",".join("?" * len(targets))
            outs = conn.execute(
                f"SELECT slug, name FROM entity WHERE slug IN ({placeholders})",
                targets).fetchall()
            matched_outcomes = [dict(r) for r in outs]
            base_sel = """
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       e.created_at, e.effect_size, e.effect_quant,
                       COALESCE(e.review_status,'unreviewed') AS review_status,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name,
                       (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
                       (SELECT study_type FROM evidence ev WHERE ev.edge_id=e.id
                        ORDER BY CASE study_type WHEN 'meta_analysis' THEN 1
                          WHEN 'systematic_review' THEN 2 WHEN 'rct' THEN 3
                          WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 1) AS top_study,
                       (SELECT MAX(changed_at) FROM edge_history h
                        WHERE h.edge_id=e.id AND h.field='tier'
                          AND h.new_value IN ('A','B')
                          AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
                       ) AS promoted_at
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE o.slug IN ({ph}) AND e.tier IN ('A','B','C')
                  AND e.direction = ?
            """
            ph = ",".join("?" * len(targets))
            do_rows = [dict(r) for r in conn.execute(
                base_sel.format(ph=ph), targets + ["protective"]).fetchall()]
            harm_rows = [dict(r) for r in conn.execute(
                base_sel.format(ph=ph), targets + ["harmful"]).fetchall()]
            ushape_rows = [dict(r) for r in conn.execute(
                base_sel.format(ph=ph), targets + ["u_shaped"]).fetchall()]
            mixed_rows = [dict(r) for r in conn.execute(
                base_sel.format(ph=ph), targets + ["mixed"]).fetchall()]
        for e in do_rows + harm_rows + ushape_rows + mixed_rows:
            e["score"] = _importance_score(e)
            e["breakthrough"] = _is_breakthrough(e)

        # Aggregate per-factor, AND collapse dose-response variants. Group
        # key is (dose_root, kind) so walking_4000/7000/10000 share one
        # card but legumes vs nuts stay separate.
        def _agg(rows: list[dict]) -> dict[str, dict]:
            out: dict[str, dict] = {}
            for e in rows:
                root = _dose_root(e["f_slug"])
                key = root  # one card per root factor
                if key not in out:
                    rec = {**e, "for_conditions": [],
                           "for_condition_names": [], "n_overlap": 0,
                           "best_score": e["score"],
                           "f_slug_root": root,
                           "dose_variants": [],
                           "in_stack": False}
                    # If the slug was a dose variant, prefer the canonical
                    # name without the dose suffix when displaying.
                    if root != e["f_slug"]:
                        rec["f_name"] = e["f_name"].split("(")[0].strip()
                    out[key] = rec
                rec = out[key]
                if e["o_slug"] not in rec["for_conditions"]:
                    rec["for_conditions"].append(e["o_slug"])
                    rec["for_condition_names"].append(e["o_name"])
                rec["n_overlap"] = len(rec["for_conditions"])
                if root != e["f_slug"] and e["f_slug"] not in rec["dose_variants"]:
                    rec["dose_variants"].append(e["f_slug"])
                if e["score"] > rec["best_score"]:
                    rec["best_score"] = e["score"]
                    rec["tier"] = e["tier"]
                    rec["effect_size"] = e["effect_size"]
                    rec["effect_quant"] = e["effect_quant"]
                    rec["id"] = e["id"]
                    rec["summary"] = e["summary"]
                    rec["review_status"] = e["review_status"]
                # In-stack flag: set if any of the constituent slugs is
                # in the user's saved stack.
                if e["f_slug"] in stack_set or root in stack_set:
                    rec["in_stack"] = True
            return out

        do_map = _agg(do_rows)
        hard_map = _agg(harm_rows)
        cau_map = _agg(ushape_rows + mixed_rows)
        for rec in list(do_map.values()) + list(hard_map.values()) + list(cau_map.values()):
            rec["axes"] = _three_axis_labels(rec)

        def _sortkey(e: dict):
            return (-(e["n_overlap"]), -(1 if e["breakthrough"] else 0), -e["best_score"])

        do_list = sorted(do_map.values(), key=_sortkey)
        hard_list = sorted(hard_map.values(), key=_sortkey)
        caution_list = sorted(cau_map.values(), key=_sortkey)[:12]

        # Bucket Do-this by entity.kind so the page reads as Lifestyle →
        # Diet → Supplements → Drugs instead of one flat 24-card list.
        for rec in do_list:
            do_buckets[_kind_bucket(rec.get("f_kind"), _DO_BUCKETS)].append(rec)
        for rec in hard_list:
            hard_buckets[_kind_bucket(rec.get("f_kind"), _HARD_BUCKETS)].append(rec)

        # Top-3 starters: pick from Do-this regardless of bucket. Score
        # = overlap × 2 + tier_weight + effect_weight − stack_penalty.
        # Items already in the user's stack drop down so the cluster
        # recommends genuinely new actions.
        TIER_W = {"A": 4, "B": 3, "C": 1}
        EFF_W  = {"large": 3, "very_large": 4, "moderate": 2, "small": 1}
        def _starter_score(r):
            base = (r.get("n_overlap", 1) * 2
                    + TIER_W.get(r.get("tier"), 0)
                    + EFF_W.get((r.get("effect_size") or "").lower(), 0))
            if r.get("in_stack"):
                base -= 5
            return base
        starters = sorted(do_list, key=lambda r: -_starter_score(r))[:3]
    return render(request, "my_plan.html", {
        "title": "My plan",
        "profile": p,
        "matched_outcomes": matched_outcomes,
        "do_buckets": [(b[0], b[1], do_buckets[b[0]]) for b in _DO_BUCKETS if do_buckets[b[0]]],
        "hard_buckets": [(b[0], b[1], hard_buckets[b[0]]) for b in _HARD_BUCKETS if hard_buckets[b[0]]],
        "caution_rows": caution_list,
        "starters": starters,
        "warnings": _interactions_for_stack(p.stack),
        "n_stack": len(stack_set),
    })


@app.get("/me/briefing", response_class=HTMLResponse)
def me_briefing(request: Request):
    """The proactive weekly briefing — anomalies, evidence shifts,
    closure cards, correlations, protocol status. Server returns
    corpus-side data; the rest is rendered client-side from the
    user's local graph."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "me_briefing.html", {
        "title": "Weekly briefing",
        "profile": p,
    })


@app.get("/me/checkup", response_class=HTMLResponse)
def me_checkup(request: Request):
    """Pre-visit prep — given an upcoming appointment, surface anomalies,
    new evidence, and 4 evidence-backed questions to bring up."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "me_checkup.html", {
        "title": "Pre-visit prep",
        "profile": p,
    })


@app.get("/me/challenge", response_class=HTMLResponse)
def me_challenge(request: Request):
    """Adaptive coach mode — devil's advocate against the user's plan."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "me_challenge.html", {
        "title": "Challenge my plan",
        "profile": p,
    })


@app.get("/claim-check", response_class=HTMLResponse)
def claim_check(request: Request):
    """Public claim checker — paste any wellness claim, get a
    profile-adjusted plausibility score from the corpus."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "claim_check.html", {
        "title": "Claim checker",
        "profile": p,
    })


@app.post("/api/claim-check")
async def api_claim_check(request: Request):
    """Stateless: parse a claim into (factor, outcome, claim_strength),
    look up the relevant corpus edge, and return a profile-adjusted
    plausibility verdict using Claude."""
    body = await request.json()
    claim = (body.get("claim") or "").strip()[:600]
    if not claim:
        return JSONResponse({"error": "missing claim"}, status_code=400)
    profile_hints = body.get("profile_hints") or {}  # {age, sex, conditions[]}

    # Step 1: parse the claim with Claude into structured form.
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return JSONResponse({"error": "LLM not configured"}, status_code=503)
    parse_system = (
        "Extract from a wellness/health claim:\n"
        '{ "factor": "the thing being claimed", '
        '  "factor_type": "supplement|food|drug|behavior|activity|other", '
        '  "outcome": "the effect being claimed", '
        '  "claimed_direction": "protective|harmful|mixed", '
        '  "claimed_magnitude": "small|moderate|large|extraordinary", '
        '  "claim_summary": "one sentence" }\n'
        "Return JSON only, no prose."
    )
    try:
        from claude_client import call as claude_call, extract_json
        text, _ = claude_call(
            system=parse_system, user=claim,
            operation="claim_check_parse", max_tokens=300, temperature=0.1,
        )
        parsed = extract_json(text) or {}
    except Exception as exc:
        return JSONResponse({"error": "parse failed: " + str(exc)[:200]}, status_code=500)

    # Step 2: corpus lookup. Match factor name to entity → pull edges
    # to the named outcome (or any outcome if outcome name is generic).
    factor_name = (parsed.get("factor") or "").strip().lower()
    outcome_name = (parsed.get("outcome") or "").strip().lower()
    matched_edges: list[dict] = []
    with connect() as conn:
        if factor_name:
            rows = conn.execute("""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                       f.slug AS f_slug, f.name AS f_name,
                       o.slug AS o_slug, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE LOWER(f.name) LIKE ? AND e.tier IN ('A','B','C','X')
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'X' THEN 3 ELSE 4 END
                LIMIT 12""", (f"%{factor_name}%",)).fetchall()
            matched_edges = [dict(r) for r in rows]
            # Filter to outcome match if we have one.
            if outcome_name and matched_edges:
                pref = [e for e in matched_edges
                        if outcome_name in (e["o_name"] or "").lower()
                        or (e["o_name"] or "").lower() in outcome_name]
                if pref:
                    matched_edges = pref

    # Step 3: verdict via Claude. Give it the parsed claim, the corpus
    # rows, and any profile hints.
    if matched_edges:
        corpus_block = "\n".join(
            f"- {e['f_name']} → {e['o_name']}: tier {e['tier']}, {e['direction']}"
            f"{', ' + str(e['effect_size']) + ' effect' if e.get('effect_size') else ''}"
            f"{'. ' + (e['effect_quant'] or '')[:200] if e.get('effect_quant') else ''}"
            for e in matched_edges[:6]
        )
    else:
        corpus_block = "(no matching edges found in our corpus)"

    profile_block = ""
    if profile_hints:
        bits = []
        if profile_hints.get("age"): bits.append(f"age {profile_hints['age']}")
        if profile_hints.get("sex"): bits.append(f"sex {profile_hints['sex']}")
        cs = profile_hints.get("conditions") or []
        if cs: bits.append("tracking " + ", ".join(cs[:5]))
        if bits:
            profile_block = "Personal context: " + " · ".join(bits) + "\n\n"

    verdict_system = (
        "You are an evidence skeptic. Given a parsed wellness claim, "
        "the relevant corpus rows, and personal context, return a JSON verdict:\n"
        '{ "plausibility": "well_supported|partial|weak|unsupported|contested", '
        '  "magnitude_check": "as_claimed|over_stated|under_stated|unknown", '
        '  "verdict": "1-2 sentence honest verdict", '
        '  "personal_relevance": "1-2 sentences tailored to the personal context, '
        '       or general if no context", '
        '  "what_is_true": ["specific true element if any"], '
        '  "what_is_false_or_overstated": ["..."], '
        '  "confidence": "high|moderate|low" }\n'
        "Return JSON only. Be honest, not diplomatic.\n\n"
        "FRAMING RULES:\n"
        "- Use 'evidence suggests X' / 'literature shows Y', never 'you should'.\n"
        "- Never make a recommendation directly to the user — frame as what "
        "  the evidence states.\n"
        "- If the claim touches medication: note that any change requires "
        "  clinician supervision.\n\n"
        "TIER ASSIGNMENT RULES:\n"
        "- 'well_supported' requires ≥1 high-quality MA or multiple "
        "  consistent RCTs in the corpus. Default downward if uncertain.\n"
        "- A single trial (even if positive) = 'partial' at most.\n"
        "- Mechanistic plausibility WITHOUT outcome trials = 'weak'.\n"
        "- Population effect ≠ personal effect: flag this when the user "
        "  asks 'will it work for me?'.\n\n"
        "OUTPUT RULES:\n"
        "- ALWAYS finish sentences. Truncated medical text is unsafe.\n"
        "- The `verdict` field MUST start with the literal phrase "
        "  'Evidence-based educational synthesis, not medical advice — ' "
        "  before any other content."
    )
    verdict_user = (
        f"PARSED CLAIM: {parsed}\n\n"
        f"{profile_block}"
        f"CORPUS EVIDENCE:\n{corpus_block}\n\n"
        "Return JSON only."
    )
    try:
        text, _ = claude_call(
            system=verdict_system, user=verdict_user,
            operation="claim_check_verdict", max_tokens=900, temperature=0.2,
        )
        verdict = extract_json(text) or {}
    except Exception as exc:
        return JSONResponse({"error": "verdict failed: " + str(exc)[:200]}, status_code=500)

    # Always include the same educational-not-medical disclaimer.
    verdict["disclaimer"] = (
        "This is educational synthesis, not medical advice. The "
        "literature is reported as-is; how it applies to your specific "
        "situation is a conversation with your clinician, not a "
        "decision this tool makes."
    )
    # Safety-voice transforms across every prose field (β fix).
    verdict = _harden_claim_check_verdict(verdict)
    return JSONResponse({
        "ok": True,
        "claim": claim,
        "parsed": parsed,
        "corpus_edges": matched_edges[:6],
        "verdict": verdict,
    })


@app.get("/me/risks", response_class=HTMLResponse)
def me_risks(request: Request):
    """Calibrated risk equations (ASCVD 10-year, FINDRISC) computed
    against the user's local labs/biomarkers + manual inputs. Tracks
    score over time in localStorage so the user sees the trajectory."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "me_risks.html", {
        "title": "Your risk projection",
        "profile": p,
    })


@app.get("/me/data", response_class=HTMLResponse)
def me_data(request: Request):
    """The personal-data hub. Renders the empty shell; all data lives
    client-side in localStorage and is hydrated by personal.js. Server
    only ever provides the evidence-overlay API endpoints (stateless,
    no PHI received)."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "me_data.html", {
        "title": "Your data",
        "profile": p,
    })


@app.get("/sync", response_class=HTMLResponse)
def sync_form(request: Request, sent: int = 0, error: str = ""):
    """Cross-device sync. User enters email → server emails a /restore link
    that encodes the current profile. Clicking on another device restores
    the cookie. No accounts, no DB — privacy-first."""
    p = decode(request.cookies.get(COOKIE))
    return render(request, "sync.html", {
        "title": "Sync to another device",
        "profile": p, "sent": bool(sent), "error": error,
    })


@app.post("/sync")
async def sync_send(request: Request, email: str = Form(...)):
    """Generate a sync token + email it as a /restore?token=X link."""
    import os, re as _re
    if not _re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return RedirectResponse("/sync?error=bad-email", status_code=303)
    p = decode(request.cookies.get(COOKIE))
    p.email = email
    token = make_sync_token(p, ttl_seconds=60 * 60 * 24 * 14)  # 14 days
    base = str(request.base_url).rstrip("/")
    link = f"{base}/restore?token={token}"
    body = f"""<p>Click to restore your Health Universe profile on this device:</p>
<p><a href="{link}">Restore my profile</a></p>
<p style="font-size:12px;color:#777">Link valid for 14 days. Health Universe never stores your profile server-side; this email is the only way it reaches another device.</p>"""
    sent = False
    try:
        if os.environ.get("RESEND_API_KEY"):
            from digest_send import send_resend
            send_resend(email, "Restore your Health Universe profile", body)
            sent = True
        elif os.environ.get("SMTP_USER"):
            from digest_send import send_smtp
            send_smtp(email, "Restore your Health Universe profile", body)
            sent = True
    except Exception:
        pass
    resp = RedirectResponse(f"/sync?sent={int(sent)}", status_code=303)
    # Persist email on the existing cookie too (optional anchor)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.get("/restore")
def restore(request: Request, token: str = ""):
    """Verify magic-link token and re-set the profile cookie."""
    if not token:
        return RedirectResponse("/sync", status_code=303)
    p = verify_sync_token(token)
    if not p:
        return RedirectResponse("/sync?error=expired", status_code=303)
    resp = RedirectResponse("/my-plan" if p.conditions else "/me",
                            status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    """Full privacy disclosure — Art. 9 GDPR-aware language for the optional
    digest signup, retention windows, lawful basis, and data-export link."""
    return render(request, "privacy.html", {"title": "Privacy"})


@app.get("/data-export")
def data_export(request: Request):
    """Download every byte of server-known data about this user as JSON.
    Profile cookie + any subscriber row keyed by email."""
    import json as _json
    p = decode(request.cookies.get(COOKIE))
    out = {"profile": {k: getattr(p, k) for k in _PROFILE_FIELDS},
           "subscriber_record": None}
    if p.email:
        sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
        try:
            subs = _json.loads(sub_file.read_text()) if sub_file.exists() else []
            out["subscriber_record"] = next((s for s in subs if s.get("email") == p.email), None)
        except Exception:
            pass
    body = _json.dumps(out, indent=2).encode()
    return Response(content=body, media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="health-universe-export.json"'})


@app.post("/unsubscribe")
async def unsubscribe(request: Request, email: str = Form("")):
    """Remove an email from data/subscribers.json. Idempotent. No login."""
    import json as _json
    if not email:
        p = decode(request.cookies.get(COOKIE))
        email = p.email or ""
    if not email:
        return RedirectResponse("/privacy", status_code=303)
    sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
    if sub_file.exists():
        try:
            subs = _json.loads(sub_file.read_text())
            subs = [s for s in subs if s.get("email") != email]
            sub_file.write_text(_json.dumps(subs, indent=2))
        except Exception:
            pass
    return RedirectResponse("/privacy?unsubscribed=1", status_code=303)


@app.post("/me/switch-profile")
async def switch_profile(request: Request, name: str = Form(...)):
    """Move the named alternate into the active slot, archive the previous
    active profile to alternates."""
    p = decode(request.cookies.get(COOKIE))
    target = next((alt for alt in p.alternates if alt.get("name") == name), None)
    if not target:
        return RedirectResponse("/me", status_code=303)
    # Archive current active
    archive = {k: getattr(p, k) for k in _PROFILE_FIELDS if k != "alternates"}
    new_alternates = [a for a in p.alternates if a.get("name") != name]
    new_alternates.append(archive)
    new = Profile(**{k: target.get(k) for k in _PROFILE_FIELDS if k in target})
    new.alternates = new_alternates
    new.email = p.email                                   # email travels with the device
    resp = RedirectResponse("/my-plan" if new.conditions else "/me", status_code=303)
    resp.set_cookie(COOKIE, encode(new), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.post("/me/add-profile")
async def add_profile(request: Request, name: str = Form(...)):
    """Save the current profile as a named alternate, then switch to a
    fresh blank profile so the user can fill it in for someone else."""
    p = decode(request.cookies.get(COOKIE))
    if not name.strip() or len(name) > 40:
        return RedirectResponse("/me?err=name", status_code=303)
    archived = {k: getattr(p, k) for k in _PROFILE_FIELDS if k != "alternates"}
    archived["name"] = name.strip()
    p.alternates.append(archived)
    new = Profile()
    new.alternates = p.alternates
    new.email = p.email
    resp = RedirectResponse("/me", status_code=303)
    resp.set_cookie(COOKIE, encode(new), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.post("/me/delete-profile")
async def delete_profile(request: Request, name: str = Form(...)):
    p = decode(request.cookies.get(COOKIE))
    p.alternates = [a for a in p.alternates if a.get("name") != name]
    resp = RedirectResponse("/me", status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


# ---- drug × supplement interaction warnings ---------------------------

_INTERACTIONS_FILE = Path(__file__).parent.parent / "data" / "interactions.json"


def _load_interactions() -> list[dict]:
    import json as _json
    if not _INTERACTIONS_FILE.exists():
        return []
    try:
        return _json.loads(_INTERACTIONS_FILE.read_text())
    except Exception:
        return []


def _interactions_for_stack(stack: list[str]) -> list[dict]:
    """Return any interaction rows whose `pair` is fully covered by the user's stack."""
    if not stack:
        return []
    s = set(stack)
    out: list[dict] = []
    for it in _load_interactions():
        pair = set(it.get("pair", []))
        if pair and pair.issubset(s):
            out.append(it)
    return out


_SYNERGIES_FILE = ROOT / "data" / "synergies.json"
_SYNERGIES_CACHE: list[dict] | None = None
_HARMS_FILE = ROOT / "data" / "conditional_harms.json"
_HARMS_CACHE: list[dict] | None = None


def _load_conditional_harms() -> list[dict]:
    """Conditional harms — combinations harmful only when a condition
    or co-medication is present."""
    global _HARMS_CACHE
    if _HARMS_CACHE is not None:
        return _HARMS_CACHE
    if not _HARMS_FILE.exists():
        _HARMS_CACHE = []
        return _HARMS_CACHE
    try:
        import json as _json
        _HARMS_CACHE = (_json.loads(_HARMS_FILE.read_text()) or {}).get("harms", [])
    except Exception:
        _HARMS_CACHE = []
    return _HARMS_CACHE


def _conditional_harms_for_user(stack_slugs: list[str],
                                conditions: list[str]) -> list[dict]:
    """Return conditional-harm rules that fire for this user's
    combination of stack items + conditions."""
    if not stack_slugs:
        return []
    stack = {s.lower() for s in stack_slugs}
    cond_set = {(c or "").lower() for c in (conditions or [])}
    out: list[dict] = []
    for rule in _load_conditional_harms():
        factor = (rule.get("factor") or "").lower()
        if factor not in stack:
            # The factor might also be itself a condition (e.g. levothyroxine
            # is a co-med listed both as stack-item AND condition trigger).
            if factor not in cond_set:
                continue
        required = {r.lower() for r in (rule.get("condition_required") or [])}
        if not required:
            continue
        # Trigger fires if ANY of the required conditions OR co-meds
        # match the user's profile (conditions or stack).
        match_set = cond_set | stack
        triggers = required & match_set
        if not triggers:
            continue
        out.append({
            **rule,
            "triggered_by": sorted(triggers),
        })
    # Order by severity (high first).
    severity_order = {"high": 0, "moderate": 1, "low": 2}
    out.sort(key=lambda r: severity_order.get(r.get("severity"), 3))
    return out


def _load_synergies() -> list[dict]:
    """Lazy-load the synergies JSON. Same shape as interactions but
    'factors' (list, ≥2) instead of 'pair' (always 2). Each row also
    carries a strength tier so the UI can rank."""
    global _SYNERGIES_CACHE
    if _SYNERGIES_CACHE is not None:
        return _SYNERGIES_CACHE
    if not _SYNERGIES_FILE.exists():
        _SYNERGIES_CACHE = []
        return _SYNERGIES_CACHE
    try:
        import json as _json
        data = _json.loads(_SYNERGIES_FILE.read_text())
        _SYNERGIES_CACHE = data.get("synergies", [])
    except Exception:
        _SYNERGIES_CACHE = []
    return _SYNERGIES_CACHE


def _synergies_for_stack(stack_slugs: list[str]) -> dict:
    """Return active synergies (all factors covered) and missing-but-close
    synergies (most factors covered, one short — surfaceable as 'add X
    to compound your Y')."""
    if not stack_slugs:
        return {"active": [], "near_misses": []}
    s = set(stack_slugs)
    active: list[dict] = []
    near: list[dict] = []
    for syn in _load_synergies():
        factors = set(syn.get("factors", []))
        if not factors:
            continue
        covered = factors & s
        missing = factors - s
        if not missing:
            active.append({**syn, "covered_factors": list(covered)})
        elif len(covered) >= 1 and len(missing) == 1:
            near.append({
                **syn,
                "covered_factors": list(covered),
                "missing_factors": list(missing),
            })
    # Rank: high strength first, then more-covered first.
    rank_strength = {"high": 0, "moderate": 1, "low": 2}
    active.sort(key=lambda r: rank_strength.get(r.get("strength"), 3))
    near.sort(key=lambda r: (
        rank_strength.get(r.get("strength"), 3),
        -len(r.get("covered_factors", [])),
    ))
    return {"active": active, "near_misses": near}


@app.post("/api/me/risk-projection")
async def api_me_risk_projection(request: Request):
    """Stateless: given a flat dict of risk inputs, compute ASCVD,
    FINDRISC, and a hypothetical-change projection. The browser sends
    its locally-stored values; we never persist them."""
    from web.risk_models import ascvd_10yr, findrisc, ascvd_delta_if
    body = await request.json()
    out = {"ascvd": None, "findrisc": None, "scenarios": []}
    # ASCVD
    try:
        out["ascvd"] = ascvd_10yr(
            age=float(body.get("age") or 0),
            sex=(body.get("sex") or "M").upper(),
            race=body.get("race") or "white",
            total_cholesterol=float(body.get("total_cholesterol") or 0),
            hdl=float(body.get("hdl") or 0),
            systolic_bp=float(body.get("systolic_bp") or 0),
            bp_treated=bool(body.get("bp_treated", False)),
            smoker=bool(body.get("smoker", False)),
            diabetes=bool(body.get("diabetes", False)),
        )
    except Exception as exc:
        out["ascvd"] = {"score": None, "error": str(exc)[:200]}
    # FINDRISC
    try:
        out["findrisc"] = findrisc(
            age=int(body.get("age") or 0),
            bmi=float(body.get("bmi") or 0),
            waist_cm=float(body.get("waist_cm") or 0),
            sex=(body.get("sex") or "M").upper(),
            physical_activity_30min_daily=bool(body.get("physical_activity_30min_daily", False)),
            eats_vegetables_or_fruit_daily=bool(body.get("eats_vegetables_or_fruit_daily", False)),
            on_bp_medication=bool(body.get("on_bp_medication", False)),
            ever_high_blood_glucose=bool(body.get("ever_high_blood_glucose", False)),
            family_diabetes=body.get("family_diabetes", "none"),
        )
    except Exception as exc:
        out["findrisc"] = {"score": None, "error": str(exc)[:200]}
    # ASCVD scenarios — common interventions
    if out["ascvd"] and out["ascvd"].get("score") is not None:
        baseline = out["ascvd"]["components"]
        scenarios = []
        # Quit smoking
        if baseline.get("smoker"):
            r = ascvd_delta_if(baseline_inputs=baseline, change={"smoker": False})
            if r.get("score") is not None:
                scenarios.append({"label": "If you quit smoking",
                                  "score": r["score"], "delta": round(out["ascvd"]["score"] - r["score"], 1)})
        # Lower SBP to 120
        if baseline.get("systolic_bp", 120) > 120:
            r = ascvd_delta_if(baseline_inputs=baseline, change={"systolic_bp": 120.0})
            if r.get("score") is not None:
                scenarios.append({"label": f"If SBP {int(baseline['systolic_bp'])}→120",
                                  "score": r["score"], "delta": round(out["ascvd"]["score"] - r["score"], 1)})
        # Lower TC by 30 (statin equivalent)
        tc = baseline.get("total_cholesterol", 200)
        if tc > 180:
            new_tc = max(150.0, tc - 30)
            r = ascvd_delta_if(baseline_inputs=baseline, change={"total_cholesterol": new_tc})
            if r.get("score") is not None:
                scenarios.append({"label": f"If TC {int(tc)}→{int(new_tc)} (~statin)",
                                  "score": r["score"], "delta": round(out["ascvd"]["score"] - r["score"], 1)})
        # Raise HDL by 10
        hdl = baseline.get("hdl", 50)
        if hdl < 60:
            r = ascvd_delta_if(baseline_inputs=baseline, change={"hdl": hdl + 10})
            if r.get("score") is not None:
                scenarios.append({"label": f"If HDL {int(hdl)}→{int(hdl+10)} (exercise + omega-3)",
                                  "score": r["score"], "delta": round(out["ascvd"]["score"] - r["score"], 1)})
        out["scenarios"] = scenarios
    return JSONResponse(out)


@app.get("/api/me/synergies")
def api_me_synergies(stack: str = ""):
    """Stateless: given a comma-separated list of factor slugs, return
    active synergies + near-miss synergies (one factor away)."""
    items = [s.strip() for s in (stack or "").split(",") if s.strip()]
    return JSONResponse(_synergies_for_stack(items))


@app.get("/api/interactions/check")
def api_interactions_check(request: Request):
    """Return any interaction warnings active for the current cookie profile."""
    p = decode(request.cookies.get(COOKIE))
    return JSONResponse({"warnings": _interactions_for_stack(p.stack)})


@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    """Public dashboard of corpus stats. Reuses the same numbers that
    /methodology pulls but presents them as a journalist-friendly,
    shareable single page."""
    from datetime import timedelta as _td
    today = datetime_now()
    with connect() as conn:
        n_edges = conn.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
        n_studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]
        n_pmids = conn.execute(
            "SELECT COUNT(DISTINCT pmid) c FROM evidence WHERE pmid IS NOT NULL AND pmid != ''"
        ).fetchone()["c"]
        n_meta = conn.execute(
            "SELECT COUNT(*) c FROM evidence WHERE study_type IN ('meta_analysis','systematic_review')"
        ).fetchone()["c"]
        n_rct = conn.execute(
            "SELECT COUNT(*) c FROM evidence WHERE study_type='rct'"
        ).fetchone()["c"]
        n_cohort = conn.execute(
            "SELECT COUNT(*) c FROM evidence WHERE study_type='cohort'"
        ).fetchone()["c"]
        tier_dist = {r["tier"]: r["c"] for r in
            conn.execute("SELECT tier, COUNT(*) c FROM edge GROUP BY tier").fetchall()}
        dir_dist = {r["direction"]: r["c"] for r in
            conn.execute("SELECT direction, COUNT(*) c FROM edge GROUP BY direction").fetchall()}
        # Top factors and outcomes
        top_factors = [dict(r) for r in conn.execute("""
            SELECT f.slug, f.name, COUNT(e.id) AS n_edges,
                   (SELECT COUNT(*) FROM evidence ev JOIN edge e2 ON ev.edge_id=e2.id
                    WHERE e2.factor_id=f.id) AS n_studies
            FROM entity f JOIN edge e ON e.factor_id=f.id
            GROUP BY f.id ORDER BY n_edges DESC LIMIT 12""").fetchall()]
        top_outcomes = [dict(r) for r in conn.execute("""
            SELECT o.slug, o.name, COUNT(e.id) AS n_edges
            FROM entity o JOIN edge e ON e.outcome_id=o.id
            GROUP BY o.id ORDER BY n_edges DESC LIMIT 12""").fetchall()]
        # Recency histogram (per-month counts of evidence rows in last 12 months)
        cutoff = (today - _td(days=365)).strftime("%Y-%m-%d")
        recency_rows = conn.execute("""
            SELECT substr(created_at, 1, 7) AS ym, COUNT(*) c
            FROM evidence WHERE created_at >= ?
            GROUP BY ym ORDER BY ym ASC""", (cutoff,)).fetchall()
        # New edges added in last 30/90 days. Same seed-phase suppression
        # as _stats(): if the window contains >50% of the corpus, every
        # row is freshly-seeded, not a real "new this month" signal.
        new_30 = conn.execute(
            "SELECT COUNT(*) c FROM edge WHERE created_at >= ?",
            ((today - _td(days=30)).strftime("%Y-%m-%d"),)).fetchone()["c"]
        new_90 = conn.execute(
            "SELECT COUNT(*) c FROM edge WHERE created_at >= ?",
            ((today - _td(days=90)).strftime("%Y-%m-%d"),)).fetchone()["c"]
        if n_edges and new_30 > n_edges * 0.5: new_30 = 0
        if n_edges and new_90 > n_edges * 0.6: new_90 = 0
        n_breakthroughs = 0
        try:
            n_breakthroughs = conn.execute("""
                SELECT COUNT(*) c FROM edge_history h
                WHERE h.field='tier' AND h.new_value IN ('A','B')
                  AND h.changed_at >= ?
                  AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))""",
                ((today - _td(days=90)).strftime("%Y-%m-%d"),)).fetchone()["c"]
        except Exception:
            pass
    return render(request, "stats.html", {
        "title": "Stats — Health Universe",
        "n_edges": n_edges, "n_studies": n_studies,
        "n_pmids": n_pmids, "n_meta": n_meta, "n_rct": n_rct, "n_cohort": n_cohort,
        "tier_dist": tier_dist, "dir_dist": dir_dist,
        "top_factors": top_factors, "top_outcomes": top_outcomes,
        "recency_rows": [dict(r) for r in recency_rows],
        "new_30": new_30, "new_90": new_90,
        "n_breakthroughs_90d": n_breakthroughs,
    })


# ---- /feed.rss : public daily-breakthrough RSS feed ----------------------

@app.get("/feed.rss")
def feed_rss():
    """RSS feed of meaningful evidence shifts in the last 30 days.
    Emits one <item> per tier promotion / breakthrough. Anyone can
    subscribe via Feedly, Reeder, NetNewsWire, etc. — free distribution."""
    from datetime import timedelta as _td
    today = datetime_now()
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
            ORDER BY h.changed_at DESC LIMIT 200""",
            ((today - _td(days=30)).strftime("%Y-%m-%d"),)).fetchall()]
    items: list[dict] = []
    for r in rows:
        ev = _classify_event(r)
        if not ev["is_meaningful"]:
            continue
        items.append({
            "edge_id": r["edge_id"],
            "title": f'{ev["headline"]} — {r["f_name"]} → {r["o_name"]}',
            "summary": (r.get("e_summary") or "")[:400],
            "headline": ev["headline"],
            "category": ev["category"],
            "tier": r["e_tier"],
            "changed_at": r["changed_at"],
            "f_name": r["f_name"],
            "o_name": r["o_name"],
        })
        if len(items) >= 30:
            break
    base = "https://health-universe.vercel.app"
    def esc(s: str) -> str:
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    item_xml = []
    for it in items:
        item_xml.append(f"""<item>
  <title>{esc(it['title'])}</title>
  <link>{base}/edge/{it['edge_id']}</link>
  <guid isPermaLink="false">hu-edge-{it['edge_id']}-{it['changed_at'][:10]}-{it['category']}</guid>
  <pubDate>{it['changed_at']}</pubDate>
  <description>{esc(it['summary'])}</description>
  <category>{esc(it['category'])}</category>
</item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>Health Universe — Evidence shifts</title>
<link>{base}/</link>
<description>Tier promotions, new evidence, retractions across the Health Universe knowledge graph.</description>
<language>en-us</language>
<atom:link href="{base}/feed.rss" rel="self" type="application/rss+xml" />
{''.join(item_xml)}
</channel>
</rss>"""
    return Response(content=rss, media_type="application/rss+xml; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=3600"})


# ---- A/B routing : test /start as landing ---------------------------------

@app.get("/_variant")
def variant_assign(request: Request, target: str = "/"):
    """Probe used by the homepage to randomly assign a 50/50 cookie
    between editorial (A) and onboarding-first (B). Logs nothing
    server-side; the variant is stored in a `hu_variant` cookie so the
    user gets a stable experience and we can analyse later via Plausible
    custom events."""
    import secrets
    existing = request.cookies.get("hu_variant")
    variant = existing if existing in ("A", "B") else secrets.choice(("A","B"))
    dest = "/" if variant == "A" else "/start"
    if target and target.startswith("/"):
        dest = target
    resp = RedirectResponse(dest, status_code=303)
    resp.set_cookie("hu_variant", variant, max_age=60*60*24*180,
                    httponly=False, samesite="lax")
    return resp


# ---- /score : Stack Score dial -------------------------------------------

def _compute_stack_score(profile: Profile, conn) -> dict:
    """Stack Score 0–100 = coverage of tracked conditions × stack quality
    minus interaction conflicts."""
    if not (profile.conditions or profile.stack):
        return {"score": 0, "ok": False, "reason": "Set up your stack to see your score."}
    coverage = 0
    coverage_max = max(1, len(profile.conditions))
    for c in profile.conditions:
        # Does any tier-A protective edge for this condition touch the user's stack?
        row = conn.execute("""
            SELECT COUNT(*) c FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE o.slug=? AND e.tier='A' AND e.direction='protective'
              AND f.slug IN ({})""".format(",".join(["?"]*max(1,len(profile.stack)))) if profile.stack else """
            SELECT 0 c""",
            ([c] + list(profile.stack)) if profile.stack else []).fetchone()
        if row and row["c"] > 0:
            coverage += 1
    stack_quality = 0
    if profile.stack:
        rows = conn.execute("""
            SELECT e.tier, e.direction FROM edge e
            JOIN entity f ON f.id=e.factor_id
            WHERE f.slug IN ({})""".format(",".join(["?"]*len(profile.stack))),
            profile.stack).fetchall()
        n = max(1, len(rows))
        weighted = sum({"A":4,"B":3,"C":2,"X":1,"D":0.5,"deprecated":0}.get(r["tier"],1)
                       for r in rows if r["direction"] in ("protective","neutral"))
        stack_quality = int(min(40, weighted))                 # cap at 40
    interactions = _interactions_for_stack(profile.stack)
    interaction_penalty = sum({"high":15,"moderate":7,"low":2}.get(i.get("severity","low"),2)
                              for i in interactions)
    coverage_pts = int((coverage / coverage_max) * 50) if coverage_max else 0
    raw = coverage_pts + stack_quality - interaction_penalty
    score = max(0, min(100, raw))
    band = "low" if score < 35 else ("solid" if score < 70 else "strong")
    return {
        "score": score, "ok": True,
        "coverage": coverage, "coverage_max": coverage_max,
        "coverage_pts": coverage_pts,
        "stack_quality": stack_quality,
        "interactions": interactions,
        "interaction_penalty": interaction_penalty,
        "band": band,
    }


@app.get("/score", response_class=HTMLResponse)
def score_page(request: Request):
    p = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        stats = _compute_stack_score(p, conn)
    return render(request, "score.html", {
        "title": "My Stack Score",
        "profile": p, "stats": stats,
    })


@app.get("/og/score/{score}.svg")
def og_score(score: int):
    """Shareable OG card for a given numeric score."""
    score = max(0, min(100, int(score)))
    band = "Low coverage" if score < 35 else ("Solid stack" if score < 70 else "Strong stack")
    color = "#a3552c" if score < 35 else ("#c9a961" if score < 70 else "#1f3a2e")
    arc_pct = score / 100.0
    # SVG arc — circumference fragments
    radius = 180; circ = 2 * 3.141592 * radius
    dash = circ * arc_pct
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fffaf0"/>
      <stop offset="100%" stop-color="#f5ead0"/>
    </linearGradient>
    <linearGradient id="ribbon" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#caa257"/>
      <stop offset="50%" stop-color="#f0d990"/>
      <stop offset="100%" stop-color="#caa257"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <text x="60" y="80" font-family="Inter, sans-serif" font-weight="700"
        font-size="22" letter-spacing="6" fill="#1f3a2e">HEALTH UNIVERSE</text>
  <g transform="translate(820,310)">
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#e8d8b3" stroke-width="22"/>
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="{color}"
            stroke-width="22" stroke-linecap="round"
            stroke-dasharray="{dash:.1f} {circ:.1f}"
            transform="rotate(-90)"/>
    <text x="0" y="20" text-anchor="middle"
          font-family="Fraunces, serif" font-weight="500"
          font-size="120" fill="#1f3a2e">{score}</text>
    <text x="0" y="80" text-anchor="middle"
          font-family="Inter, sans-serif" font-weight="500"
          font-size="22" fill="#7c6c4d">/ 100</text>
  </g>
  <text x="60" y="200" font-family="Fraunces, serif" font-weight="500"
        font-size="64" fill="#1f3a2e">My Stack Score</text>
  <text x="60" y="270" font-family="Inter, sans-serif" font-weight="500"
        font-size="28" fill="{color}">{band}</text>
  <text x="60" y="330" font-family="Inter, sans-serif" font-weight="400"
        font-size="20" fill="#4a5b51">Coverage of tracked conditions ×</text>
  <text x="60" y="362" font-family="Inter, sans-serif" font-weight="400"
        font-size="20" fill="#4a5b51">stack quality − interaction conflicts.</text>
  <text x="60" y="595" font-family="Inter, sans-serif" font-weight="500"
        font-size="16" fill="#7c6c4d">health-universe.vercel.app/score</text>
  <rect x="0" y="610" width="1200" height="20" fill="url(#ribbon)"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


# ---- /posts : auto-generated cornerstone articles ------------------------

POSTS_DIR = Path(__file__).parent.parent / "data" / "posts"


def _post_index() -> list[dict]:
    if not POSTS_DIR.exists():
        return []
    out = []
    for f in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        try:
            import json as _json
            d = _json.loads(f.read_text())
            out.append({"slug": f.stem, **d})
        except Exception:
            pass
    return out


@app.get("/posts", response_class=HTMLResponse)
def posts_index(request: Request):
    return render(request, "posts_index.html", {
        "title": "Posts — Health Universe",
        "posts": _post_index(),
    })


@app.get("/posts/{slug}", response_class=HTMLResponse)
def post_detail(request: Request, slug: str):
    import json as _json
    post_file = POSTS_DIR / f"{slug}.json"
    if not post_file.exists():
        return HTMLResponse("Not found", status_code=404)
    try:
        post = _json.loads(post_file.read_text())
    except Exception:
        return HTMLResponse("Could not load post", status_code=500)
    # Render markdown body to HTML so the post reads as proper prose.
    # Strip a leading H1 if present — the LLM often writes its own
    # title line as the first markdown heading, which would visually
    # duplicate the page title rendered above it.
    body_md = post.get("body_md", "") or ""
    body_md_lines = body_md.lstrip().splitlines()
    while body_md_lines and not body_md_lines[0].strip():
        body_md_lines.pop(0)
    if body_md_lines and body_md_lines[0].lstrip().startswith("# "):
        body_md_lines.pop(0)
        # also drop any blank lines that follow the stripped heading
        while body_md_lines and not body_md_lines[0].strip():
            body_md_lines.pop(0)
    body_md = "\n".join(body_md_lines)
    try:
        import markdown as _md
        html_body = _md.markdown(body_md, extensions=["fenced_code", "tables"])
    except Exception:
        html_body = "<pre>" + body_md + "</pre>"
    return render(request, "post_detail.html", {
        "title": post.get("title", slug),
        "post": {**post, "slug": slug, "body_html": html_body},
    })


# ---- /api/cron/social : daily broadcast hook -----------------------------

@app.get("/api/cron/social")
def cron_social(request: Request):
    """Vercel cron entry: post the day's top breakthrough to social.
    Reads the same RSS-feed query, picks the top item, dispatches via
    configured services (Bluesky, Twitter/X). Returns JSON for the
    cron log."""
    import os
    expected = os.environ.get("CRON_SECRET")
    auth = request.headers.get("authorization", "")
    if expected and auth != f"Bearer {expected}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    from datetime import timedelta as _td
    today = datetime_now()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute("""
            SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason,
                   h.actor,
                   e.id AS edge_id, e.summary, e.tier,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id = h.edge_id
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE h.changed_at >= ?
            ORDER BY h.changed_at DESC LIMIT 50""",
            ((today - _td(days=2)).strftime("%Y-%m-%d"),)).fetchall()]
    pick = None
    for r in rows:
        ev = _classify_event(r)
        if ev["category"] in ("tier_promotion", "evidence_added"):
            pick = {**r, **ev}; break
    if not pick:
        return JSONResponse({"posted": 0, "note": "no breakthrough today"})
    text = (f"📈 {pick['headline']}: {pick['f_name']} → {pick['o_name']}\n\n"
            f"{(pick.get('summary') or '')[:160]}\n\n"
            f"https://health-universe.vercel.app/edge/{pick['edge_id']}")
    posted: list[str] = []
    errors: list[dict] = []
    if os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_PASSWORD"):
        try:
            _bluesky_post(text); posted.append("bluesky")
        except Exception as exc:
            errors.append({"target": "bluesky", "error": str(exc)[:200]})
    if os.environ.get("TWITTER_BEARER_TOKEN"):
        try:
            _twitter_post(text); posted.append("twitter")
        except Exception as exc:
            errors.append({"target": "twitter", "error": str(exc)[:200]})
    return JSONResponse({"posted": posted, "edge_id": pick["edge_id"],
                         "errors": errors})


def _bluesky_post(text: str) -> None:
    import os, httpx, datetime as _dt
    handle = os.environ["BLUESKY_HANDLE"]
    pw = os.environ["BLUESKY_PASSWORD"]
    base = "https://bsky.social/xrpc"
    s = httpx.post(f"{base}/com.atproto.server.createSession",
                   json={"identifier": handle, "password": pw}, timeout=10).json()
    httpx.post(f"{base}/com.atproto.repo.createRecord",
               headers={"Authorization": f"Bearer {s['accessJwt']}"},
               json={"repo": s["did"], "collection": "app.bsky.feed.post",
                     "record": {"$type": "app.bsky.feed.post", "text": text[:300],
                                "createdAt": _dt.datetime.utcnow().isoformat() + "Z"}},
               timeout=10).raise_for_status()


def _twitter_post(text: str) -> None:
    import os, httpx
    httpx.post("https://api.twitter.com/2/tweets",
               headers={"Authorization": f"Bearer {os.environ['TWITTER_BEARER_TOKEN']}"},
               json={"text": text[:280]}, timeout=10).raise_for_status()


# ---- service worker for PWA notifications --------------------------------

@app.get("/service-worker.js")
def service_worker():
    """Tiny SW that handles 'show me a notification' messages from the
    page. We don't use VAPID push (needs persistent subscription
    storage); instead we use the Notification API client-side, with
    the service worker as the dispatcher so notifications can fire
    when the page is closed but the PWA is installed."""
    js = """
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'show-notification') {
    const { title, body, url } = event.data;
    self.registration.showNotification(title, {
      body: body || '',
      icon: '/static/icon-192.png',
      badge: '/static/icon-192.png',
      data: { url: url || '/today' },
      requireInteraction: false,
    });
  }
});

self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = data.title || 'Health Universe';
  const body  = data.body  || '';
  const url   = data.url   || '/me/briefing';
  event.waitUntil(self.registration.showNotification(title, {
    body, icon: '/static/icon-192.png', badge: '/static/icon-192.png',
    data: { url }, tag: data.tag || 'hu-push', renotify: true,
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then(list => {
      for (const c of list) {
        if (c.url.indexOf(url) !== -1) return c.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
"""
    return Response(content=js, media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/methodology", response_class=HTMLResponse)
def methodology(request: Request):
    """Trust page: how we tier evidence, sources we use, conflicts of
    interest, who's behind it, and a live changelog from edge_history."""
    with connect() as conn:
        # Tier distribution
        tier_rows = conn.execute(
            "SELECT tier, COUNT(*) c FROM edge GROUP BY tier").fetchall()
        tier_dist = {r["tier"]: r["c"] for r in tier_rows}
        # Recency: how many edges updated in each window
        from datetime import timedelta as _td
        today = datetime_now()
        windows = {
            "Last 7 days":  (today - _td(days=7)).strftime("%Y-%m-%d"),
            "Last 30 days": (today - _td(days=30)).strftime("%Y-%m-%d"),
            "Last 90 days": (today - _td(days=90)).strftime("%Y-%m-%d"),
        }
        recency = {}
        n_edges_total = conn.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
        for label, since in windows.items():
            recency[label] = conn.execute(
                "SELECT COUNT(*) c FROM edge WHERE updated_at >= ?",
                (since,)).fetchone()["c"]
        # Same seed-phase suppression: if the window contains >50% of the
        # corpus, the "recent activity" number is just the freshly-seeded
        # state, not a real signal.
        for label in list(recency):
            if n_edges_total and recency[label] > n_edges_total * 0.5:
                recency[label] = 0
        # Top studies
        n_studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]
        n_pmids = conn.execute(
            "SELECT COUNT(DISTINCT pmid) c FROM evidence WHERE pmid IS NOT NULL AND pmid != ''"
        ).fetchone()["c"]
        n_meta = conn.execute(
            "SELECT COUNT(*) c FROM evidence WHERE study_type IN ('meta_analysis','systematic_review')"
        ).fetchone()["c"]
        n_rct = conn.execute(
            "SELECT COUNT(*) c FROM evidence WHERE study_type='rct'"
        ).fetchone()["c"]
        # Recent changelog from edge_history — classify + filter to
        # meaningful events only (tier shifts, new evidence, retractions).
        raw_changes = [dict(r) for r in conn.execute("""
            SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason,
                   h.actor,
                   e.id AS edge_id, f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id = h.edge_id
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            ORDER BY h.changed_at DESC
            LIMIT 200""").fetchall()]
        changelog = []
        for r in raw_changes:
            ev = _classify_event(r)
            if not ev["is_meaningful"]:
                continue
            ev["edge_id"] = r["edge_id"]
            ev["f_name"]  = r["f_name"]
            ev["o_name"]  = r["o_name"]
            changelog.append(ev)
            if len(changelog) >= 20:
                break
        n_edges = conn.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
    return render(request, "methodology.html", {
        "title": "Methodology",
        "tier_dist": tier_dist,
        "recency": recency,
        "n_edges": n_edges,
        "n_studies": n_studies,
        "n_pmids": n_pmids,
        "n_meta": n_meta,
        "n_rct": n_rct,
        "changelog": changelog,
    })


@app.get("/start", response_class=HTMLResponse)
def onboarding(request: Request, step: int = 1):
    """Three-step onboarding: pick conditions → pick stack → optional
    digest signup → land on /my-plan. Replaces 'land on home and figure
    it out yourself' with a 60-second activation flow."""
    p = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        outcomes = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind IN "
            "('condition','outcome') ORDER BY name").fetchall()]
        factors = [dict(r) for r in conn.execute(
            "SELECT slug, name, kind FROM entity WHERE kind IN "
            "('food','supplement','nutrient','behavior','activity','medication') "
            "ORDER BY name").fetchall()]
        # Top conditions chosen by people (simple proxy: edges with most studies)
        top_conditions = [dict(r) for r in conn.execute("""
            SELECT o.slug, o.name, COUNT(e.id) AS n
            FROM edge e JOIN entity o ON o.id=e.outcome_id
            WHERE o.kind IN ('condition','outcome') AND e.tier IN ('A','B')
            GROUP BY o.slug ORDER BY n DESC LIMIT 16""").fetchall()]
    return render(request, "onboarding.html", {
        "title": "Welcome to Health Universe",
        "step": max(1, min(3, step)),
        "profile": p,
        "outcomes": outcomes,
        "factors": factors,
        "top_conditions": top_conditions,
    })


@app.post("/start")
async def onboarding_save(request: Request,
                          step: int = Form(1),
                          conditions: list[str] = Form(default=[]),
                          stack: list[str] = Form(default=[]),
                          email: str = Form(""),
                          consent: str = Form("")):
    """Each step saves and advances. Step 3 finalises and redirects to /my-plan."""
    import json as _json, re as _re
    p = decode(request.cookies.get(COOKIE))
    if step == 1:
        p.conditions = [c for c in conditions if c]
        p.watch_outcomes = list(set(p.watch_outcomes + p.conditions))
        target = "/start?step=2"
    elif step == 2:
        p.stack = [s for s in stack if s]
        target = "/start?step=3"
    else:                                                  # step 3 — finish
        if email and consent and _re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
            try:
                subs = _json.loads(sub_file.read_text()) if sub_file.exists() else []
                if not any(s.get("email") == email for s in subs):
                    subs.append({
                        "email": email,
                        "subscribed_at": datetime_now().isoformat(),
                        "profile_snapshot": {
                            "conditions": p.conditions,
                            "watch_factors": p.watch_factors,
                            "watch_outcomes": p.watch_outcomes,
                        },
                    })
                    sub_file.parent.mkdir(parents=True, exist_ok=True)
                    sub_file.write_text(_json.dumps(subs, indent=2))
            except Exception:
                pass
        target = "/my-plan" if p.conditions else "/me"
    resp = RedirectResponse(target, status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.get("/handout", response_class=HTMLResponse)
def handout(request: Request, condition: str = "", patient: str = "",
            kind: str = "prevent"):
    """Print-friendly clinician handout. Same data as /prevent or /my-plan
    but renders single-column on white with a patient-name banner and
    auto-triggers the print dialog (browser saves as PDF). Works on
    Vercel without server-side PDF deps.

    kind=prevent  → single-condition handout (uses ?condition slug)
    kind=plan     → user's combined plan (no patient-specific filter)"""
    p = decode(request.cookies.get(COOKIE))
    rendered_for = patient.strip() or None
    today = datetime_now().strftime("%d %B %Y")
    if kind == "plan":
        # Reuse /my-plan logic
        targets = list(p.conditions or [])
        do_rows: list[dict] = []
        hard_rows: list[dict] = []
        cau_rows: list[dict] = []
        with connect() as conn:
            if targets:
                ph = ",".join("?" * len(targets))
                # Top 2 PMIDs per edge (meta-analyses + SRs first) as a
                # comma-joined string so the handout can show inline refs.
                base = f"""
                    SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                           e.effect_quant,
                           f.name AS f_name, o.name AS o_name, o.slug AS o_slug,
                           (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
                           (SELECT GROUP_CONCAT(pmid, ',') FROM (
                               SELECT pmid FROM evidence ev2
                               WHERE ev2.edge_id=e.id AND pmid IS NOT NULL AND pmid != ''
                               ORDER BY CASE study_type
                                 WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2
                                 WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END
                               LIMIT 2)
                           ) AS top_pmids
                    FROM edge e JOIN entity f ON f.id=e.factor_id
                    JOIN entity o ON o.id=e.outcome_id
                    WHERE o.slug IN ({ph}) AND e.tier IN ('A','B','C') AND e.direction = ?
                    ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END
                """
                do_rows = [dict(r) for r in conn.execute(base, (*targets, "protective")).fetchall()][:18]
                hard_rows = [dict(r) for r in conn.execute(base, (*targets, "harmful")).fetchall()][:10]
                cau_rows = ([dict(r) for r in conn.execute(base, (*targets, "u_shaped")).fetchall()]
                            + [dict(r) for r in conn.execute(base, (*targets, "mixed")).fetchall()])[:8]
        return render(request, "handout.html", {
            "title": "Handout · plan",
            "kind": "plan",
            "patient": rendered_for,
            "today": today,
            "outcomes_label": ", ".join(p.conditions),
            "do_rows": do_rows,
            "hard_rows": hard_rows,
            "caution_rows": cau_rows,
        })
    # condition-specific handout
    if not condition:
        return RedirectResponse("/prevent", status_code=303)
    with connect() as conn:
        match = conn.execute(
            "SELECT slug, name FROM entity WHERE slug=? OR LOWER(name)=LOWER(?) LIMIT 1",
            (condition, condition)).fetchone()
        if not match:
            return RedirectResponse(f"/prevent?q={condition}", status_code=303)
        match = dict(match)
        base = """
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                   f.name AS f_name,
                   (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
                   (SELECT GROUP_CONCAT(pmid, ',') FROM (
                       SELECT pmid FROM evidence ev2
                       WHERE ev2.edge_id=e.id AND pmid IS NOT NULL AND pmid != ''
                       ORDER BY CASE study_type
                         WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2
                         WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END
                       LIMIT 2)
                   ) AS top_pmids
            FROM edge e JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE o.slug=? AND e.tier IN ('A','B','C') AND e.direction=?
            ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                     CASE e.effect_size WHEN 'large' THEN 1 WHEN 'moderate' THEN 2 ELSE 3 END
        """
        do_rows = [dict(r) for r in conn.execute(base, (match["slug"], "protective")).fetchall()][:14]
        hard_rows = [dict(r) for r in conn.execute(base, (match["slug"], "harmful")).fetchall()][:10]
        cau_rows = ([dict(r) for r in conn.execute(base, (match["slug"], "u_shaped")).fetchall()]
                    + [dict(r) for r in conn.execute(base, (match["slug"], "mixed")).fetchall()])[:8]
    return render(request, "handout.html", {
        "title": "Handout · " + match["name"],
        "kind": "prevent",
        "patient": rendered_for,
        "today": today,
        "outcomes_label": match["name"],
        "do_rows": do_rows,
        "hard_rows": hard_rows,
        "caution_rows": cau_rows,
    })


@app.get("/today", response_class=HTMLResponse)
def today(request: Request):
    """Daily one-card hit: pick a single anchor edge from the user's plan
    based on day-of-year so it's stable for the day. Designed for daily
    return + streak hook."""
    p = decode(request.cookies.get(COOKIE))
    pick = None
    interactions: list[dict] = []
    if p.conditions:
        with connect() as conn:
            cond_ph = ",".join("?" * len(p.conditions))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                       e.effect_quant, f.name AS f_name,
                       o.name AS o_name, o.slug AS o_slug,
                       (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE o.slug IN ({cond_ph})
                  AND e.tier IN ('A','B') AND e.direction = 'protective'
                ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END,
                         CASE e.effect_size WHEN 'large' THEN 1 WHEN 'moderate' THEN 2 ELSE 3 END,
                         e.id""", p.conditions).fetchall()
        rows = [dict(r) for r in rows]
        if rows:
            idx = datetime_now().timetuple().tm_yday % len(rows)
            pick = rows[idx]
    interactions = _interactions_for_stack(p.stack)
    return render(request, "today.html", {
        "title": "Today",
        "profile": p,
        "pick": pick,
        "interactions": interactions,
        "today_label": datetime_now().strftime("%A %d %B %Y"),
    })


@app.get("/coach", response_class=HTMLResponse)
def coach_page(request: Request, q: str = ""):
    """Conversational planner: builds a structured 30-day plan from the
    user's profile + the corpus, with optional natural-language overlay
    from local Gemma when Ollama is reachable."""
    p = decode(request.cookies.get(COOKIE))
    plan = None
    answer = None
    model_used = ""
    warnings = []
    if p.conditions:
        with connect() as conn:
            no_regret = _no_regret_movers(conn, p, limit=5)
            red_flags = _red_flags_in_stack(conn, p, limit=4)
            # Pull factor-level edges to suggest specific actions
            cond_ph = ",".join("?" * len(p.conditions))
            actions = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                       e.effect_quant, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name,
                       (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE o.slug IN ({cond_ph})
                  AND e.tier IN ('A','B')
                  AND e.direction = 'protective'
                  AND f.kind IN ('food','nutrient','behavior','activity','supplement')
                ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END,
                         CASE e.effect_size WHEN 'large' THEN 1 WHEN 'moderate' THEN 2 ELSE 3 END,
                         e.updated_at DESC
                LIMIT 12""", p.conditions).fetchall()
        # Group actions into a 30-day plan: pick top 3 weekly anchors
        anchors = []
        seen_factors: set[str] = set()
        for r in actions:
            if r["f_name"] in seen_factors:
                continue
            seen_factors.add(r["f_name"])
            anchors.append(dict(r))
            if len(anchors) >= 4:
                break
        plan = {
            "anchors": anchors,
            "no_regret": no_regret,
            "red_flags": red_flags,
        }
        # Optional: ask LLM to write a personal opening paragraph.
        # Tries local Gemma first; falls back to Claude if API key set.
        if q:
            answer, model_used = _coach_llm(p, plan, q)
        warnings = _interactions_for_stack(p.stack)
    return render(request, "coach.html", {
        "title": "My coach", "profile": p, "plan": plan, "q": q,
        "answer": answer, "model_used": model_used,
        "warnings": warnings,
    })


def _coach_llm(profile: Profile, plan: dict, question: str) -> tuple[str | None, str]:
    """Ground an LLM response in the structured plan we already built.
    Tries local Gemma first (free); falls back to Claude Haiku via the
    existing cost-capped client if a paid path is configured.
    Returns (text, model_used) or (None, ''). Same constraints both ways:
    only discuss items already on screen."""
    anchors = "\n".join(
        f"- {a['f_name']}: {a['summary'][:140]}"
        for a in plan.get("anchors", [])[:4])
    avoid = "\n".join(
        f"- {r['f_name']}: {r['summary'][:120]}"
        for r in plan.get("red_flags", [])[:3])
    system = (
        "You are a careful evidence-based health-coach assistant. "
        "ONLY discuss the items listed below — never invent new "
        "interventions, doses, or PMIDs. Keep responses under 160 words. "
        "End every reply with: 'Educational synthesis only — not medical advice.'"
    )
    user_msg = (
        f"USER QUESTION: {question}\n\n"
        f"USER CONDITIONS: {', '.join(profile.conditions) or 'none'}\n"
        f"USER STACK: {', '.join(profile.stack) or 'none'}\n\n"
        f"PROTECTIVE ANCHORS (only positive moves you may discuss):\n{anchors}\n\n"
        f"AVOIDANCES (only if user asks about risks):\n{avoid}\n\n"
        "Write a short reply addressing the user's question."
    )
    # 1) Try local Gemma (free)
    try:
        from ollama_client import call as ollama_call, OllamaUnavailable
        text = ollama_call(system=system, user=user_msg,
                           num_predict=400, retries=0)
        return text, "local-gemma"
    except Exception:
        pass
    # 2) Cloud fallback — Claude via the existing cost-capped client.
    # The client uses claude-sonnet-4-6 by default; the global $50 cap
    # protects spend. Each /coach call is small (~400 tokens out, ~600 in)
    # so each is a few cents at most.
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from claude_client import call as claude_call
            text, _usage = claude_call(system=system, user=user_msg,
                                       operation="coach", max_tokens=400)
            return text, "claude-sonnet"
        except Exception:
            return None, ""
    return None, ""


@app.get("/digest", response_class=HTMLResponse)
def digest_preview(request: Request, days: int = 7):
    """Renders what the weekly email digest would look like for this user.
    Sources: tracked conditions/factors/edges + recent breakthroughs.
    Same template can be used by the cron-driven email sender."""
    p = decode(request.cookies.get(COOKIE))
    has_profile = bool(p.conditions or p.watch_factors or p.watch_outcomes or p.watch_edges)
    sections: list[dict] = []
    with connect() as conn:
        # Section 1: breakthroughs in tracked areas
        all_disc = _new_discoveries(conn, days=days, limit=80)
        # Filter to user's tracked outcomes/factors if any tracked at all
        if has_profile:
            tracked_o = set(p.conditions) | set(p.watch_outcomes)
            tracked_f = set(p.watch_factors)
            relevant = [d for d in all_disc
                        if (tracked_o and d["o_slug"] in tracked_o)
                        or (tracked_f and d["f_slug"] in tracked_f)
                        or (d.get("breakthrough"))]
        else:
            relevant = [d for d in all_disc if d.get("breakthrough")] or all_disc[:6]
        # Only render the section header when there's actually something
        # to report. Avoid the "(0)" artefact on a freshly-seeded corpus.
        if relevant:
            title = "This week's evidence shifts"
            if len(relevant) > 1:
                title = f"This week's {len(relevant)} evidence shifts"
            sections.append({
                "title": title,
                "blurb": f"Discoveries and breakthroughs in the last {days} days"
                         + (" in areas you track" if has_profile else ""),
                "rows": relevant[:6],
            })
        # Section 2: top no-regret moves for tracked conditions
        if p.conditions:
            no_regret = _no_regret_movers(conn, p, limit=6)
            sections.append({
                "title": "Top no-regret moves for your stack",
                "blurb": "Tier-A protective evidence for what you track",
                "rows": no_regret,
            })
            # Section 3: red flags
            red_flags = _red_flags_in_stack(conn, p, limit=6)
            if red_flags:
                sections.append({
                    "title": "Watch outs",
                    "blurb": "Edges in your tracked areas with harmful or U-shaped direction",
                    "rows": red_flags,
                })
    return render(request, "digest.html", {
        "title": "Weekly digest",
        "profile": p,
        "has_profile": has_profile,
        "days": days,
        "sections": sections,
        "today": datetime_now().strftime("%A %d %B %Y"),
    })


@app.post("/subscribe")
async def subscribe(request: Request, email: str = Form(...),
                    consent: str = Form("")):
    """Store email in data/subscribers.json (local-first; production sender
    reads this file to dispatch the weekly digest)."""
    import json as _json
    import re as _re
    if not _re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return HTMLResponse("Invalid email", status_code=400)
    if not consent:
        return HTMLResponse("Consent required", status_code=400)
    sub_file = Path(__file__).parent.parent / "data" / "subscribers.json"
    subs: list[dict] = []
    if sub_file.exists():
        try: subs = _json.loads(sub_file.read_text())
        except Exception: subs = []
    p = decode(request.cookies.get(COOKIE))
    if not any(s.get("email") == email for s in subs):
        subs.append({
            "email": email,
            "subscribed_at": datetime_now().isoformat(),
            "profile_snapshot": {
                "conditions": p.conditions,
                "watch_factors": p.watch_factors,
                "watch_outcomes": p.watch_outcomes,
            },
        })
        try:
            sub_file.parent.mkdir(parents=True, exist_ok=True)
            sub_file.write_text(_json.dumps(subs, indent=2))
        except Exception:
            pass     # Vercel filesystem is read-only; that's fine in prod
    return RedirectResponse("/digest?subscribed=1", status_code=303)


@app.get("/discoveries", response_class=HTMLResponse)
def discoveries(request: Request, days: int = 30, page: int = 1,
                tier: str = "", direction: str = "", q: str = "",
                kind: str = "", sort: str = "latest", group: str = ""):
    """Discoveries with full library-style navigation: tier chips,
    direction filter, search-within, sort, and breakthrough-first
    grouping. URL-driven so every filter combo is shareable."""
    with connect() as conn:
        all_rows = _new_discoveries(conn, days=days, limit=400)
    promoted_count = sum(1 for r in all_rows if r.get("promoted_at"))
    newly_count    = sum(1 for r in all_rows if not r.get("promoted_at"))
    breakthrough_count = sum(1 for r in all_rows if r.get("breakthrough"))
    # 7d signal — suppress when entire window is freshly-seeded
    week_count = sum(1 for r in all_rows if
        (r.get("promoted_at") or r.get("updated_at"))[:10] >=
        (datetime_now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    if week_count and week_count == len(all_rows):
        week_count = 0
    # Facets across the unfiltered set so the chip counts stay honest.
    tier_counts: dict[str, int] = {}
    dir_counts: dict[str, int] = {}
    for r in all_rows:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1
        dir_counts[r["direction"]] = dir_counts.get(r["direction"], 0) + 1
    # Apply filters
    rows = all_rows
    tier_set = {t for t in (tier or "").split(",") if t}
    if tier_set:
        rows = [r for r in rows if r["tier"] in tier_set]
    if direction:
        rows = [r for r in rows if r["direction"] == direction]
    if kind == "promoted":
        rows = [r for r in rows if r.get("promoted_at")]
    elif kind == "newly":
        rows = [r for r in rows if not r.get("promoted_at")]
    elif kind == "breakthrough":
        rows = [r for r in rows if r.get("breakthrough")]
    if q:
        ql = q.lower().strip()
        rows = [r for r in rows
                if ql in (r.get("f_name") or "").lower()
                or ql in (r.get("o_name") or "").lower()
                or ql in (r.get("summary") or "").lower()]
    # Sort
    if sort == "importance":
        rows.sort(key=lambda r: (-(1 if r.get("breakthrough") else 0),
                                  -(r.get("score") or 0)))
    elif sort == "studies":
        rows.sort(key=lambda r: -(r.get("n_studies") or 0))
    elif sort == "az":
        rows.sort(key=lambda r: ((r.get("f_name") or "").lower(),
                                  (r.get("o_name") or "").lower()))
    else:                                              # latest (default)
        rows.sort(key=lambda r: r.get("promoted_at") or r.get("updated_at") or "",
                  reverse=True)
    # Group by promotion vs new, optionally
    groups = None
    if group == "kind":
        bk = [r for r in rows if r.get("breakthrough")]
        pr = [r for r in rows if r.get("promoted_at") and not r.get("breakthrough")]
        nw = [r for r in rows if not r.get("promoted_at") and not r.get("breakthrough")]
        groups = []
        if bk: groups.append({"slug":"breakthrough","name":"Breakthrough","rows":bk})
        if pr: groups.append({"slug":"promoted","name":"Promoted to A or B","rows":pr})
        if nw: groups.append({"slug":"newly","name":"Newly published","rows":nw})
    total = len(rows)
    if groups:
        page_rows = []
        pg = {"page":1,"pages":1,"total":total,"has_prev":False,"has_next":False,"offset":0}
    else:
        pg = _paginate(total, page)
        page_rows = rows[pg["offset"]: pg["offset"] + PAGE_SIZE]
    return render(request, "discoveries.html", {
        "title": "Discoveries", "rows": page_rows, "groups": groups,
        "days": days,
        "pg": pg, "base_path": "/discoveries",
        "promoted_count": promoted_count,
        "new_count": newly_count,
        "breakthrough_count": breakthrough_count,
        "week_count": week_count,
        "tier_counts": tier_counts,
        "dir_counts": dir_counts,
        "filters": {"tier": tier, "direction": direction, "q": q,
                    "kind": kind, "sort": sort, "group": group, "days": days},
        "sort_options": _LIB_SORTS,
    })


# ---- profile ("/me") --------------------------------------------------------

@app.get("/me", response_class=HTMLResponse)
def me(request: Request):
    p = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        all_factors = conn.execute(
            "SELECT slug, name, kind FROM entity WHERE kind IN "
            "('food','supplement','nutrient','activity','behavior') ORDER BY name"
        ).fetchall()
        all_outcomes = conn.execute(
            "SELECT slug, name FROM entity WHERE kind='condition' ORDER BY name"
        ).fetchall()
        # Stack analysis: find harmful-for-stack-item edges and
        # protective-for-condition edges to surface
        relevant: list[dict] = []
        if p.stack or p.conditions:
            placeholders_f = ",".join("?" * max(len(p.stack), 1))
            placeholders_c = ",".join("?" * max(len(p.conditions), 1))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.slug AS f_slug, f.name AS f_name,
                       o.slug AS o_slug, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE (f.slug IN ({placeholders_f or "''"}))
                   OR (o.slug IN ({placeholders_c or "''"}))""",
                (*p.stack, *p.conditions)).fetchall()
            relevant = sorted([dict(r) for r in rows],
                              key=lambda e: -relevance_score(e, p))[:30]
        red_flags = _red_flags_in_stack(conn, p, limit=8)
        no_regret = _no_regret_movers(conn, p, limit=8)
        # Top 16 most-studied conditions for quick-pick
        top_conditions = [dict(r) for r in conn.execute("""
            SELECT o.slug, o.name, COUNT(e.id) AS n
            FROM edge e JOIN entity o ON o.id=e.outcome_id
            WHERE o.kind IN ('condition','outcome') AND e.tier IN ('A','B')
            GROUP BY o.slug ORDER BY n DESC LIMIT 16""").fetchall()]
    return render(request, "me.html", {
        "title": "My stack",
        "profile": p,
        "factors": [dict(r) for r in all_factors],
        "outcomes": [dict(r) for r in all_outcomes],
        "relevant": relevant,
        "red_flags": red_flags,
        "no_regret": no_regret,
        "top_conditions": top_conditions,
        "saved": request.query_params.get("saved") == "1",
    })


@app.post("/me")
async def me_save(request: Request,
                  age: str = Form(""), sex: str = Form(""),
                  name: str = Form(""),
                  conditions: list[str] = Form(default=[]),
                  goals: list[str] = Form(default=[]),
                  stack: list[str] = Form(default=[])):
    # Preserve alternates + email + watchlist data when overwriting
    existing = decode(request.cookies.get(COOKIE))
    # Dedupe (the /me form has both quick-pick and full-list chips that
    # can both submit the same slug)
    def _uniq(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for s in seq:
            if s and s not in seen:
                seen.add(s); out.append(s)
        return out
    p = Profile(
        age=int(age) if age.isdigit() else None,
        sex=sex or None,
        name=(name.strip()[:40] if name and name.strip() else None),
        conditions=_uniq(conditions),
        goals=_uniq(goals),
        stack=_uniq(stack),
        watch_factors=existing.watch_factors,
        watch_outcomes=existing.watch_outcomes,
        watch_edges=existing.watch_edges,
        alternates=existing.alternates,
        email=existing.email,
    )
    # If the user just told us what conditions to track, take them straight
    # to their personalised plan. Otherwise stay on /me with a saved flash.
    if p.conditions and not existing.conditions:
        # First time setting conditions — celebrate by jumping to the plan.
        target = "/my-plan"
    else:
        target = "/me?saved=1"
    resp = RedirectResponse(target, status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.post("/follow")
async def follow(request: Request, kind: str = Form(...),
                 slug: str = Form(""), edge_id: str = Form(""),
                 next: str = Form("/")):
    """Toggle a watchlist entry. kind in {factor, outcome, edge}."""
    p = decode(request.cookies.get(COOKIE))
    if kind == "factor" and slug:
        if slug in p.watch_factors:
            p.watch_factors.remove(slug)
        else:
            p.watch_factors.append(slug)
    elif kind == "outcome" and slug:
        if slug in p.watch_outcomes:
            p.watch_outcomes.remove(slug)
        else:
            p.watch_outcomes.append(slug)
    elif kind == "edge" and edge_id:
        try:
            eid = int(edge_id)
            if eid in p.watch_edges:
                p.watch_edges.remove(eid)
            else:
                p.watch_edges.append(eid)
        except ValueError:
            pass
    resp = RedirectResponse(next or "/", status_code=303)
    resp.set_cookie(COOKIE, encode(p), max_age=60*60*24*365,
                    httponly=False, samesite="lax")
    return resp


@app.post("/me/clear")
def me_clear():
    resp = RedirectResponse("/me", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


@app.get("/ask", response_class=HTMLResponse)
def ask_page(request: Request, q: str = ""):
    p = decode(request.cookies.get(COOKIE))
    answer = None
    if q.strip():
        try:
            from ask import ask as _ask
            answer = _ask(q, profile=p)
        except Exception as e:
            answer = {"error": str(e)}
    return render(request, "ask.html", {
        "title": "Ask my universe",
        "q": q, "answer": answer, "profile": p,
    })


@app.get("/risk", response_class=HTMLResponse)
def risk_dial(request: Request):
    """Risk dial — surface tier-A/B factors in user's stack/conditions."""
    p = decode(request.cookies.get(COOKIE))
    if not (p.conditions or p.stack):
        return render(request, "risk.html", {
            "title": "Risk dial", "profile": p, "movers": [], "outcomes": [],
        })
    with connect() as conn:
        # Top movers = tier-A/B edges where the factor IS in the user's stack
        # OR the outcome IS one of their conditions.
        # We rank by (tier weight × |effect_size|) and surface the strongest.
        movers = []
        # Edges on the user's stack
        if p.stack:
            placeholders = ",".join("?" * len(p.stack))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE f.slug IN ({placeholders})
                  AND e.tier IN ('A','B')
                ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END,
                  CASE e.effect_size WHEN 'large' THEN 1 WHEN 'moderate' THEN 2
                                     WHEN 'small' THEN 3 ELSE 4 END
                LIMIT 20""", p.stack).fetchall()
            for r in rows:
                d = dict(r); d["why"] = "in_your_stack"
                movers.append(d)
        # Edges pointing at user's conditions
        if p.conditions:
            placeholders = ",".join("?" * len(p.conditions))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE o.slug IN ({placeholders})
                  AND e.tier IN ('A','B')
                  AND f.slug NOT IN ({",".join("?"*max(len(p.stack), 1)) if p.stack else "''"})
                ORDER BY CASE e.tier WHEN 'A' THEN 1 ELSE 2 END,
                  CASE e.effect_size WHEN 'large' THEN 1 WHEN 'moderate' THEN 2
                                     WHEN 'small' THEN 3 ELSE 4 END
                LIMIT 20""", (*p.conditions, *(p.stack or []))).fetchall()
            for r in rows:
                d = dict(r); d["why"] = "for_your_condition"
                movers.append(d)
    # De-dup by edge id
    seen: set[int] = set(); ordered = []
    for m in movers:
        if m["id"] in seen: continue
        seen.add(m["id"]); ordered.append(m)
    with connect() as conn:
        red_flags = _red_flags_in_stack(conn, p, limit=10)
        no_regret = _no_regret_movers(conn, p, limit=10)
    return render(request, "risk.html", {
        "title": "Risk dial", "profile": p, "movers": ordered[:30],
        "red_flags": red_flags, "no_regret": no_regret,
    })


@app.get("/diary", response_class=HTMLResponse)
def diary(request: Request):
    """Stack diary — client-side log + correlations.
    The page is mostly static; data lives in localStorage so nothing leaves
    the device. Backend just lists possible factors/outcomes for checkboxes."""
    p = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        all_factors = [dict(r) for r in conn.execute(
            "SELECT slug, name, kind FROM entity WHERE kind IN "
            "('food','supplement','activity','behavior') ORDER BY name").fetchall()]
        all_outcomes = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind='process' "
            "AND slug IN ('sleep_quality','inflammation','insulin_resistance',"
            "'cognitive_decline','gut_microbiome') ORDER BY name").fetchall()]
        # Tracker outcomes user might subjectively rate: alertness, mood,
        # energy, digestion, sleep — these aren't entities; UI provides them
    daily_outcomes = ["energy", "mood", "sleep_quality", "digestion",
                       "stress", "soreness"]
    return render(request, "diary.html", {
        "title": "Stack diary", "profile": p,
        "factors": all_factors, "daily_outcomes": daily_outcomes,
    })


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    """Methodology + disclaimer + how it's built."""
    with connect() as conn:
        stats = _stats(conn)
        spent = conn.execute(
            "SELECT COALESCE(SUM(usd), 0) AS u FROM cost_ledger").fetchone()["u"]
        tier_counts = {r["tier"]: r["c"] for r in conn.execute(
            "SELECT tier, COUNT(*) c FROM edge GROUP BY tier").fetchall()}
        n_retracted = 0
        try:
            n_retracted = conn.execute(
                "SELECT COUNT(*) c FROM evidence_status WHERE is_retracted=1"
            ).fetchone()["c"]
        except Exception:
            pass
        n_pmid_distinct = conn.execute(
            "SELECT COUNT(DISTINCT pmid) c FROM evidence WHERE pmid IS NOT NULL"
        ).fetchone()["c"]
    return render(request, "about.html", {
        "title": "About",
        "stats": stats, "spent_usd": spent,
        "tier_counts": tier_counts,
        "n_retracted": n_retracted,
        "n_pmid_distinct": n_pmid_distinct,
    })


# ────────────────────────────────────────────────────────────────────
# Trust center — public audit metrics
# ────────────────────────────────────────────────────────────────────

@app.get("/trust", response_class=HTMLResponse)
def trust_page(request: Request):
    """Public audit dashboard. Shows verifier coverage, error rate,
    flagged-card count, reviewer roster, and how to report issues."""
    with connect() as conn:
        # Per-tier coverage of evidence verification.
        ev_rows = conn.execute("""
            SELECT e.tier,
                   SUM(CASE WHEN ev.relevance_status='verified' THEN 1 ELSE 0 END) AS v,
                   SUM(CASE WHEN ev.relevance_status='weak'     THEN 1 ELSE 0 END) AS w,
                   SUM(CASE WHEN ev.relevance_status='flagged'  THEN 1 ELSE 0 END) AS f,
                   SUM(CASE WHEN ev.relevance_status='missing'  THEN 1 ELSE 0 END) AS m,
                   SUM(CASE WHEN ev.relevance_status IS NULL    THEN 1 ELSE 0 END) AS u,
                   COUNT(*) AS total
            FROM evidence ev
            JOIN edge e ON e.id=ev.edge_id
            GROUP BY e.tier
            ORDER BY e.tier""").fetchall()
        ev_by_tier = []
        totals = {"v":0,"w":0,"f":0,"m":0,"u":0,"total":0}
        for r in ev_rows:
            d = dict(r)
            d["audited"] = (d["v"] or 0) + (d["w"] or 0) + (d["f"] or 0) + (d["m"] or 0)
            d["coverage_pct"] = round(100 * d["audited"] / d["total"], 1) if d["total"] else 0
            d["mismatch_pct"] = round(100 * (d["f"] or 0) / d["audited"], 1) if d["audited"] else 0
            ev_by_tier.append(d)
            for k in ("v","w","f","m","u","total"):
                totals[k] += d[k] or 0
        totals["audited"] = totals["v"] + totals["w"] + totals["f"] + totals["m"]
        totals["coverage_pct"] = round(100 * totals["audited"] / totals["total"], 1) if totals["total"] else 0
        totals["mismatch_pct"] = round(100 * totals["f"] / totals["audited"], 1) if totals["audited"] else 0

        # Per-tier edge review status.
        edge_rows = conn.execute("""
            SELECT e.tier, COALESCE(e.review_status,'unreviewed') AS status,
                   COUNT(*) AS n
            FROM edge e
            GROUP BY e.tier, status
            ORDER BY e.tier, n DESC""").fetchall()
        # Recent flagged samples (most damning).
        flagged_samples = conn.execute("""
            SELECT ev.relevance_score, ev.real_title, ev.citation,
                   f.name AS f_name, o.name AS o_name, e.id AS eid, e.tier
            FROM evidence ev
            JOIN edge e ON e.id=ev.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE ev.relevance_status='flagged' AND e.tier IN ('A','B')
            ORDER BY ev.relevance_score ASC
            LIMIT 8""").fetchall()
        # Recent issue reports (count + recent).
        try:
            n_reports_open = conn.execute(
                "SELECT COUNT(*) FROM card_reports WHERE resolved=0"
            ).fetchone()[0]
            n_reports_total = conn.execute(
                "SELECT COUNT(*) FROM card_reports").fetchone()[0]
        except Exception:
            n_reports_open = n_reports_total = 0

    return render(request, "trust.html", {
        "title": "Trust & audit",
        "ev_by_tier": ev_by_tier,
        "totals": totals,
        "edge_rows": [dict(r) for r in edge_rows],
        "flagged_samples": [dict(r) for r in flagged_samples],
        "n_reports_open": n_reports_open,
        "n_reports_total": n_reports_total,
    })


@app.post("/api/report-card")
def api_report_card(request: Request,
                    edge_id: int = Form(...),
                    reason: str = Form(...),
                    note: str = Form("")):
    """Capture a user-reported problem with a card. Lightweight: writes
    to card_reports table. A maintainer reviews via /trust."""
    import os, sys
    reason = (reason or "").strip()[:60]
    note = (note or "").strip()[:2000]
    if not reason:
        return RedirectResponse(f"/edge/{edge_id}?reported=invalid", status_code=303)
    ts = datetime_now().isoformat(timespec="seconds")
    # Look up account_id if signed in — links the report to the user.
    account = current_account(request.cookies.get(SESSION_COOKIE))
    account_id = account.user_id if account else None
    persisted = False
    # 1) Persist to Supabase.
    sb = supabase_service()
    if sb is not None:
        try:
            sb.table("card_reports").insert({
                "edge_id": int(edge_id),
                "account_id": account_id,
                "reason": reason,
                "note": note or None,
                "reported_at": ts,
            }).execute()
            persisted = True
        except Exception as exc:
            print(f"[report] supabase insert failed: {exc}", file=sys.stderr)
    # 2) Notify the founder.
    try:
        notify_to = os.environ.get("WAITLIST_NOTIFY_TO", "")
        if notify_to and os.environ.get("RESEND_API_KEY"):
            _resend_send(
                notify_to,
                f"[HU] Card report — edge {edge_id} ({reason})",
                f"<p>New card-report.</p>"
                f"<p><b>Edge:</b> <a href='https://health-universe.vercel.app/edge/{edge_id}'>{edge_id}</a></p>"
                f"<p><b>Reason:</b> {reason}</p>"
                f"<p><b>Note:</b> {note or '(none)'}</p>"
                f"<p><b>Reporter:</b> {account.email if account else 'anonymous'}</p>"
                f"<p><b>At:</b> {ts}</p>"
                f"<p><b>Persisted:</b> {persisted}</p>")
    except Exception as exc:
        print(f"[report] resend notify failed: {exc}", file=sys.stderr)
    print(f"[report] edge={edge_id} reason={reason} (supabase={persisted})", file=sys.stderr)
    return RedirectResponse(f"/edge/{edge_id}?reported=ok", status_code=303)


# ────────────────────────────────────────────────────────────────────
# Stack Brief — paste your stack, get an evidence digest (Milestone 2)
# ────────────────────────────────────────────────────────────────────

import re as _re_stack
_STACK_TOKEN_RE = _re_stack.compile(r"[a-zA-Z][a-zA-Z0-9 _-]{2,}")


def _stack_match_factors(conn, raw_items: list[str]) -> list[dict]:
    """Match each free-text item to the closest factor/lifestyle entity.
    Strategy: normalize → exact slug → exact name match → token contains
    → fuzzy SequenceMatcher on names. Returns one row per input item."""
    from difflib import SequenceMatcher
    # All factor-side kinds in the corpus today: activity / behavior /
    # food / nutrient / supplement / drug / environmental / process /
    # pathogen / gene / biomarker. We exclude 'condition' so symptoms
    # don't get matched as inputs.
    entities = [dict(r) for r in conn.execute(
        "SELECT id, slug, name, kind FROM entity "
        "WHERE kind IS NULL OR kind != 'condition'"
    ).fetchall()]
    name_index = {(e["name"] or "").lower(): e for e in entities}
    slug_index = {(e["slug"] or "").lower(): e for e in entities}
    out = []
    for raw in raw_items:
        item = (raw or "").strip()
        if not item:
            continue
        norm = item.lower().strip(" .,;:")
        slug_hint = norm.replace(" ", "_").replace("-", "_")
        match = slug_index.get(slug_hint) or name_index.get(norm)
        score = 1.0 if match else 0.0
        if not match:
            best, best_s = None, 0.0
            for e in entities:
                nm = (e["name"] or "").lower()
                if not nm or len(nm) < 3:
                    continue
                if norm in nm or nm in norm:
                    s = 0.8 + 0.2 * min(len(norm), len(nm)) / max(len(norm), len(nm))
                    if s > best_s:
                        best, best_s = e, s
                else:
                    s = SequenceMatcher(None, norm, nm).ratio()
                    if s > best_s:
                        best, best_s = e, s
            if best and best_s >= 0.62:
                match = best
                score = best_s
        out.append({"input": item, "match": match, "match_score": round(score, 2)})
    return out


def _stack_brief_for_factor(conn, factor_id: int, *,
                            max_outcomes: int = 6,
                            skeptic: bool = False) -> list[dict]:
    """Pull the strongest edges for a given factor, with one top
    citation each. Filters out 'flagged' rows so the brief never shows
    a known-bad citation.

    Skeptic mode reorders so contested / counter-evidence-heavy edges
    surface first, and uses a counter citation when available — the
    "show me the catch" view."""
    if skeptic:
        order_sql = ("ORDER BY CASE WHEN e.tier='X' THEN 0 "
                     "WHEN e.tier='D' THEN 1 ELSE 2 END, "
                     "e.tier ASC, e.updated_at DESC")
    else:
        order_sql = ("ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 "
                     "ELSE 3 END, e.updated_at DESC")
    rows = conn.execute(f"""
        SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
               COALESCE(e.review_status,'unreviewed') AS review_status,
               o.name AS o_name, o.slug AS o_slug
        FROM edge e
        JOIN entity o ON o.id=e.outcome_id
        WHERE e.factor_id=? AND e.tier IN ('A','B','C','X')
        {order_sql}
        LIMIT ?""", (factor_id, max_outcomes)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        # In skeptic mode, prefer a counter-evidence citation if any;
        # fall back to top supporting citation. Either way, exclude
        # semantically-flagged PMIDs.
        cite_sql = """
            SELECT pmid, citation, year, study_type, real_title,
                   relevance_status, is_counter
            FROM evidence
            WHERE edge_id=?
              {counter_clause}
              AND (relevance_status IS NULL OR relevance_status != 'flagged')
            ORDER BY CASE study_type
                       WHEN 'meta_analysis' THEN 1
                       WHEN 'systematic_review' THEN 2
                       WHEN 'rct' THEN 3
                       WHEN 'cohort' THEN 4 ELSE 5 END,
                     year DESC
            LIMIT 1"""
        if skeptic:
            cite = conn.execute(
                cite_sql.format(counter_clause="AND COALESCE(is_counter,0)=1"),
                (d["id"],)).fetchone()
            if not cite:
                cite = conn.execute(
                    cite_sql.format(counter_clause="AND COALESCE(is_counter,0)=0"),
                    (d["id"],)).fetchone()
        else:
            cite = conn.execute(
                cite_sql.format(counter_clause="AND COALESCE(is_counter,0)=0"),
                (d["id"],)).fetchone()
        d["top_cite"] = dict(cite) if cite else None
        d["n_studies"] = conn.execute(
            "SELECT COUNT(*) FROM evidence WHERE edge_id=? AND COALESCE(is_counter,0)=0",
            (d["id"],)).fetchone()[0]
        d["n_counter"] = conn.execute(
            "SELECT COUNT(*) FROM evidence WHERE edge_id=? AND COALESCE(is_counter,0)=1",
            (d["id"],)).fetchone()[0]
        out.append(d)
    return out


_BRIEF_TOKEN_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # no 0/o/1/l/i


def _make_brief_token() -> str:
    import secrets
    return "".join(secrets.choice(_BRIEF_TOKEN_ALPHABET) for _ in range(8))


def _summarize_brief(matches: list[dict]) -> dict:
    """Tweet-sized summary stats for a brief (counts per direction
    across the strongest edge per matched item)."""
    counts = {"protective": 0, "harmful": 0, "u_shaped": 0,
              "mixed": 0, "neutral": 0, "no_match": 0}
    n_a_tier = 0
    for m in matches:
        if not m.get("match"):
            counts["no_match"] += 1
            continue
        edges = m.get("edges") or []
        if not edges:
            continue
        top = edges[0]
        d = top.get("direction") or "neutral"
        counts[d] = counts.get(d, 0) + 1
        if top.get("tier") == "A":
            n_a_tier += 1
    return {
        "n_items":      sum(1 for m in matches if m.get("match")),
        "n_protective": counts["protective"],
        "n_harmful":    counts["harmful"],
        "n_a_tier":     n_a_tier,
        "n_no_match":   counts["no_match"],
    }


def _build_brief_payload(conn, raw_items: list[str], skeptic: bool,
                         user_conditions: list[str] | None = None):
    """Run the matcher + per-factor edge lookup. Returns the matches
    list plus the cross-stack interaction warnings.

    Interaction check runs against BOTH the matched factor slugs AND
    a normalized form of each raw input — so warnings still fire for
    items that aren't in our entity table (e.g. warfarin, which lives
    in the interactions list but isn't yet a graph node)."""
    matched = _stack_match_factors(conn, raw_items)
    interaction_slugs: set[str] = set()
    for m in matched:
        # Normalised form of the raw input itself.
        raw = (m["input"] or "").lower().strip(" .,;:")
        for slug_form in (raw.replace(" ", "_").replace("-", "_"),
                          raw.replace(" ", "")):
            if slug_form:
                interaction_slugs.add(slug_form)
        if m["match"]:
            m["edges"] = _stack_brief_for_factor(
                conn, m["match"]["id"], skeptic=skeptic)
            interaction_slugs.add(m["match"]["slug"])
        else:
            m["edges"] = []
    warnings = _interactions_for_stack(list(interaction_slugs))
    synergies = _synergies_for_stack(list(interaction_slugs))
    cond_harms = _conditional_harms_for_user(list(interaction_slugs), user_conditions or [])
    return matched, warnings, synergies, cond_harms


def _encode_brief_items(items: list[str], skeptic: bool) -> str:
    """Pack the item list + skeptic flag into a URL-safe token. Keeps
    briefs stateless (no DB write at request time → works on
    serverless), while still giving each brief a stable, shareable
    URL the user can pass around."""
    import base64, json as _json
    payload = _json.dumps({
        "i": items,
        "s": 1 if skeptic else 0,
    }, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode()


def _decode_brief_items(token: str) -> tuple[list[str], bool]:
    """Reverse of _encode_brief_items. Returns ([], False) on any
    parse error so the route can redirect home cleanly."""
    import base64, json as _json
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode((token + pad).encode())
        d = _json.loads(raw)
        items = d.get("i") or []
        if not isinstance(items, list):
            return [], False
        items = [str(x)[:60] for x in items if str(x).strip()][:30]
        return items, bool(d.get("s"))
    except Exception:
        return [], False


@app.get("/stack", response_class=HTMLResponse)
def stack_form(request: Request, items: str = "", skeptic: int = 0):
    """Free input → evidence brief. Paste a stack (comma- or
    line-separated supplements / foods / habits / meds), get back what
    the corpus says. First three items are free; more requires Pro.

    Stateless: no DB writes — the brief renders inline at this URL,
    and the share-URL encodes items into the path so links work
    on serverless filesystems too."""
    raw_items: list[str] = []
    if items:
        for part in _re_stack.split(r"[,\n]+", items):
            part = part.strip()
            if not part:
                continue
            raw_items.append(part[:60])
    skeptic_flag = bool(skeptic)
    if not raw_items:
        return render(request, "stack.html", {
            "title": "Stack Brief",
            "raw": "",
            "raw_items": [],
            "matches": [],
            "warnings": [],
            "synergies": {"active": [], "near_misses": []},
            "conditional_harms": [],
            "summary": None,
            "pro_locked": False,
            "share_url": None,
            "skeptic": False,
            "token": None,
        })
    FREE_LIMIT = 3
    pro_locked = len(raw_items) > FREE_LIMIT
    visible = raw_items[:FREE_LIMIT]
    with connect() as conn:
        matches, warnings, synergies, cond_harms = _build_brief_payload(conn, visible, skeptic_flag, user_conditions=(decode(request.cookies.get(COOKIE)).conditions if request.cookies.get(COOKIE) else []))
    summary = _summarize_brief(matches)
    token = _encode_brief_items(raw_items, skeptic_flag)
    base = str(request.base_url).rstrip("/")
    share_url = f"{base}/stack/s/{token}"
    return render(request, "stack.html", {
        "title": "Stack Brief",
        "raw": ",".join(raw_items),
        "raw_items": raw_items,
        "matches": matches,
        "warnings": warnings,
        "synergies": synergies,
        "conditional_harms": cond_harms,
        "summary": summary,
        "pro_locked": pro_locked,
        "share_url": share_url,
        "skeptic": skeptic_flag,
        "token": token,
    })


@app.get("/api/me/stack")
async def api_me_stack(request: Request, items: str = "", skeptic: int = 0):
    """Pure-JSON sibling of /stack. Same input, structured output —
    no HTML template. Lets programmatic callers (the QA harness, future
    mobile clients, the future API tier) consume the brief cleanly."""
    raw_items: list[str] = []
    if items:
        for part in _re_stack.split(r"[,\n]+", items):
            part = part.strip()
            if not part: continue
            raw_items.append(part[:60])
    if not raw_items:
        return JSONResponse({"items": [], "matches": [], "warnings": [],
                             "synergies": {"active": [], "near_misses": []},
                             "conditional_harms": [], "summary": None})
    FREE_LIMIT = 3
    pro_locked = len(raw_items) > FREE_LIMIT
    visible = raw_items[:FREE_LIMIT]
    skeptic_flag = bool(skeptic)
    user_conditions = []
    try:
        p = decode(request.cookies.get(COOKIE))
        if p and p.conditions:
            user_conditions = list(p.conditions)
    except Exception:
        pass
    with connect() as conn:
        matches, warnings, synergies, cond_harms = _build_brief_payload(
            conn, visible, skeptic_flag, user_conditions=user_conditions)
    return JSONResponse({
        "items": raw_items,
        "matches": matches,
        "warnings": warnings,
        "synergies": synergies,
        "conditional_harms": cond_harms,
        "summary": _summarize_brief(matches),
        "pro_locked": pro_locked,
        "skeptic": skeptic_flag,
    })


@app.get("/stack/s/{token}", response_class=HTMLResponse)
def stack_brief_saved(request: Request, token: str, skeptic: int = 0):
    """Render a brief from an encoded token. Public, shareable, and
    completely stateless — no DB row needed. The token decodes back
    to the original input items."""
    items, sk_from_token = _decode_brief_items(token)
    if not items:
        return RedirectResponse("/stack", status_code=303)
    skeptic_flag = bool(skeptic) or sk_from_token
    FREE_LIMIT = 3
    pro_locked = len(items) > FREE_LIMIT
    visible = items[:FREE_LIMIT]
    with connect() as conn:
        matches, warnings, synergies, cond_harms = _build_brief_payload(conn, visible, skeptic_flag, user_conditions=(decode(request.cookies.get(COOKIE)).conditions if request.cookies.get(COOKIE) else []))
    summary = _summarize_brief(matches)
    base = str(request.base_url).rstrip("/")
    share_url = f"{base}/stack/s/{token}"
    return render(request, "stack.html", {
        "title": "Stack Brief",
        "raw": ",".join(items),
        "raw_items": items,
        "matches": matches,
        "warnings": warnings,
        "synergies": synergies,
        "conditional_harms": cond_harms,
        "summary": summary,
        "pro_locked": pro_locked,
        "share_url": share_url,
        "skeptic": skeptic_flag,
        "token": token,
    })


@app.get("/stack/print/{token}", response_class=HTMLResponse)
def stack_brief_print(request: Request, token: str, skeptic: int = 0):
    """Print-styled view of a brief. Browsers' Save-as-PDF gives a
    clean PDF without server deps. The 'Pro PDF export' button on the
    main brief opens this URL in a new tab and triggers print().
    Stateless via the same token encoding as /stack/s/<token>."""
    items, sk_from_token = _decode_brief_items(token)
    if not items:
        return RedirectResponse("/stack", status_code=303)
    skeptic_flag = bool(skeptic) or sk_from_token
    with connect() as conn:
        # Print view shows ALL items (a paid Pro user has unlocked it,
        # or it's the founder's marketing material).
        matches, warnings, synergies, cond_harms = _build_brief_payload(conn, items, skeptic_flag, user_conditions=(decode(request.cookies.get(COOKIE)).conditions if request.cookies.get(COOKIE) else []))
    summary = _summarize_brief(matches)
    return render(request, "stack_print.html", {
        "title": "Stack Brief — print",
        "raw_items": items,
        "matches": matches,
        "warnings": warnings,
        "synergies": synergies,
        "conditional_harms": cond_harms,
        "summary": summary,
        "skeptic": skeptic_flag,
        "token": token,
        "generated_at": datetime_now().isoformat(timespec="minutes"),
    })


# ────────────────────────────────────────────────────────────────────
# Personal-data evidence overlay endpoints. These are STATELESS — they
# never receive PHI tied to identity. The browser holds all personal
# data in localStorage and asks the server only "given this lab value
# / this SNP / this finding, which edges in the graph are relevant?"
# ────────────────────────────────────────────────────────────────────

_LAB_PANEL_FILE = ROOT / "data" / "lab_panel.json"
_SNP_PANEL_FILE = ROOT / "data" / "snp_panel.json"
_LAB_PANEL_CACHE: dict | None = None
_SNP_PANEL_CACHE: dict | None = None


def _lab_panel() -> dict:
    global _LAB_PANEL_CACHE
    if _LAB_PANEL_CACHE is not None:
        return _LAB_PANEL_CACHE
    try:
        import json as _json
        _LAB_PANEL_CACHE = _json.loads(_LAB_PANEL_FILE.read_text())
    except Exception:
        _LAB_PANEL_CACHE = {"labs": {}}
    return _LAB_PANEL_CACHE


def _snp_panel() -> dict:
    global _SNP_PANEL_CACHE
    if _SNP_PANEL_CACHE is not None:
        return _SNP_PANEL_CACHE
    try:
        import json as _json
        _SNP_PANEL_CACHE = _json.loads(_SNP_PANEL_FILE.read_text())
    except Exception:
        _SNP_PANEL_CACHE = {"snps": {}}
    return _SNP_PANEL_CACHE


def _resolve_lab_key(name_in: str) -> tuple[str, dict] | tuple[None, None]:
    """Match a free-text lab name to an entry in the lab panel."""
    if not name_in:
        return None, None
    n = (name_in or "").strip().lower()
    for key, entry in _lab_panel().get("labs", {}).items():
        if n == key:
            return key, entry
        for alias in entry.get("aliases", []):
            if alias.lower() == n or n in alias.lower() or alias.lower() in n:
                return key, entry
    return None, None


def _edges_for_entity_slugs(slugs: list[str], limit: int = 20) -> list[dict]:
    """Top edges where any of these slugs is the FACTOR — sorted by tier
    then update recency. Used to power lab/SNP/finding evidence overlays."""
    if not slugs:
        return []
    with connect() as conn:
        ph = ",".join("?" * len(slugs))
        rows = conn.execute(f"""
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                   COALESCE(e.review_status,'unreviewed') AS review_status,
                   f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE f.slug IN ({ph}) AND e.tier IN ('A','B','C')
            ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                     e.updated_at DESC
            LIMIT ?
        """, [*slugs, limit]).fetchall()
    return [dict(r) for r in rows]


def _interventions_for_outcomes(outcome_slugs: list[str], limit: int = 8) -> list[dict]:
    """Top protective interventions for any of these outcome slugs.
    Used to surface "what to DO about a high lab" rather than just
    "what high lab does to you"."""
    if not outcome_slugs:
        return []
    with connect() as conn:
        ph = ",".join("?" * len(outcome_slugs))
        rows = conn.execute(f"""
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                   COALESCE(e.review_status,'unreviewed') AS review_status,
                   f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE o.slug IN ({ph}) AND e.tier IN ('A','B','C')
              AND e.direction = 'protective'
            ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                     e.updated_at DESC
            LIMIT ?
        """, [*outcome_slugs, limit]).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/me/lab-evidence")
def api_lab_evidence(name: str = "", value: float = 0.0, unit: str = ""):
    """Stateless: given a lab name + value, return reference range,
    out-of-range direction, edges where this biomarker is a factor,
    and protective interventions for the outcomes those edges hit."""
    key, entry = _resolve_lab_key(name)
    if not entry:
        return JSONResponse({"matched": False, "name": name, "message":
            "We don't have this lab in our reference panel yet. "
            "Tell us via /api/report-card if it's a common one."})
    direction = "in_range"
    out_slugs: list[str] = []
    if value > entry.get("ref_high", 1e9):
        direction = "high"
        out_slugs = entry.get("high_entities", [])
    elif value < entry.get("ref_low", -1):
        direction = "low"
        out_slugs = entry.get("low_entities", [])
    edges = _edges_for_entity_slugs(out_slugs) if out_slugs else []
    # The outcomes those edges affect → so we can recommend interventions.
    affected_outcome_slugs = list({e["o_slug"] for e in edges})
    interventions = _interventions_for_outcomes(affected_outcome_slugs)
    return JSONResponse({
        "matched":         True,
        "key":             key,
        "name":            entry.get("name"),
        "ref_low":         entry.get("ref_low"),
        "ref_high":        entry.get("ref_high"),
        "unit":            entry.get("unit"),
        "category":        entry.get("category"),
        "explainer":       entry.get("explainer"),
        "direction":       direction,
        "out_of_range":    direction in ("high", "low"),
        "matched_entities": out_slugs,
        "edges":           edges,
        "interventions":   interventions,
    })


# Per SNP-category, the outcome substrings that count as phenotype-
# relevant. Used to filter the edges we surface for a given variant —
# fixes the QA-flagged bug where TCF7L2 (T2D variant) returned an
# aerobic-exercise-for-depression edge.
_SNP_CATEGORY_OUTCOMES = {
    "neuro": ["dement", "alzheimer", "cognitive", "depression", "anxiety",
              "parkinson", "ptsd", "stroke", "memory", "brain"],
    "metabolic": ["t2d", "diabet", "obesity", "insulin", "glycaemic",
                  "glycemic", "metabolic", "hba1c", "weight", "fatty_liver",
                  "lipid", "cholesterol", "ldl", "apob", "triglyceride"],
    "cardio": ["cvd", "cardiovascular", "mace", "hypertension", "ldl",
               "apob", "atherosclerosis", "myocardial", "stroke", "heart"],
    "athletic": ["strength", "muscle", "vo2max", "endurance", "performance",
                 "sprint", "power", "hypertrophy"],
    "diet": ["lactose", "fodmap", "dairy", "gluten", "iron", "absorption"],
    "drug-metabolism": ["bleeding", "clopidogrel", "warfarin", "drug",
                        "tardive", "syndrome", "rhabdo"],
    "social": ["social", "anxiety", "mood", "stress"],
    "longevity": ["all_cause_mortality", "longevity", "frailty", "aging"],
}


def _filter_edges_by_snp_category(edges: list[dict], category: str | None,
                                  rsid: str = "") -> list[dict]:
    """Keep edges whose outcome slug/name matches the phenotype the SNP
    actually affects. Falls back to all edges if no match."""
    if not edges or not category:
        return edges
    keywords = _SNP_CATEGORY_OUTCOMES.get(category, [])
    if not keywords:
        return edges
    relevant = []
    for e in edges:
        slug = (e.get("o_slug") or "").lower()
        name = (e.get("o_name") or "").lower()
        if any(k in slug or k in name for k in keywords):
            relevant.append(e)
    return relevant if relevant else edges  # fall back if filter would empty


@app.get("/api/me/snp-evidence")
def api_snp_evidence(rsid: str = "", genotype: str = ""):
    """Stateless: given an rsID + genotype, return interpretation +
    any edges to amplify in the personal plan."""
    rsid = (rsid or "").strip().lower()
    genotype = (genotype or "").strip().upper()
    snp = _snp_panel().get("snps", {}).get(rsid)
    if not snp:
        return JSONResponse({"matched": False, "rsid": rsid,
            "message": "Not in our actionable SNP panel yet."})
    interp = snp.get("interpretation", {}).get(genotype)
    if not interp:
        # Try the reverse complement (e.g. 23andMe sometimes reports the
        # opposite strand).
        rev = "".join({"A":"T","T":"A","C":"G","G":"C"}.get(b, b) for b in genotype[::-1])
        interp = snp.get("interpretation", {}).get(rev)
    if not interp:
        return JSONResponse({"matched": True, "rsid": rsid, "gene": snp.get("gene"),
            "name": snp.get("name"), "genotype": genotype,
            "interpretation": None,
            "message": "Genotype not in our panel for this SNP — read raw allele directly."})
    amplify = interp.get("amplify_edges", [])
    edges = _edges_for_entity_slugs(amplify) if amplify else []
    # Filter to outcomes that match the SNP's phenotype category.
    # Fixes wrong-outcome surfacing for non-neuro SNPs.
    edges = _filter_edges_by_snp_category(edges, snp.get("category"), rsid)
    return JSONResponse({
        "matched":  True,
        "rsid":     rsid,
        "gene":     snp.get("gene"),
        "name":     snp.get("name"),
        "category": snp.get("category"),
        "genotype": genotype,
        "label":    interp.get("label"),
        "summary":  interp.get("summary"),
        "amplify_factor": interp.get("amplify_factor"),
        "amplify_edges":  amplify,
        "edges":    edges,
    })


@app.get("/api/me/evidence-shifts")
def api_evidence_shifts(edges: str = "", since: str = "", limit: int = 30):
    """Return recent edge_history rows for the user's watchlist edges.
    Stateless: client sends the comma-list of edge IDs they care about,
    server checks edge_history for changes since `since` (default 14 days).

    This is the proactive heartbeat: when an edge in your watchlist
    changes tier, gets new evidence, or gets demoted, the briefing page
    surfaces it without waiting for you to ask."""
    if not edges.strip():
        return JSONResponse({"shifts": []})
    try:
        ids = [int(x) for x in edges.split(",") if x.strip()][:200]
    except Exception:
        return JSONResponse({"error": "bad edge ids"}, status_code=400)
    since_iso = since or (datetime_now() - timedelta(days=14)).isoformat(timespec="seconds")
    if not ids:
        return JSONResponse({"shifts": []})
    with connect() as conn:
        ph = ",".join("?" * len(ids))
        rows = conn.execute(f"""
            SELECT h.edge_id, h.field, h.old_value, h.new_value, h.changed_at,
                   e.tier, e.direction, e.summary,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id=h.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE h.edge_id IN ({ph}) AND h.changed_at >= ?
            ORDER BY h.changed_at DESC
            LIMIT ?
        """, [*ids, since_iso, limit]).fetchall()
    shifts = [dict(r) for r in rows]
    # Classify each shift so the client doesn't have to.
    for s in shifts:
        s["kind"] = _classify_shift(s)
    return JSONResponse({"shifts": shifts, "since": since_iso})


def _classify_shift(s: dict) -> str:
    """Turn a raw edge_history row into a human-readable category."""
    f, ov, nv = s.get("field"), s.get("old_value"), s.get("new_value")
    if f == "tier":
        ord_map = {"A": 0, "B": 1, "C": 2, "D": 3, "X": 4}
        if ov in ord_map and nv in ord_map:
            return "promoted" if ord_map[nv] < ord_map[ov] else "demoted"
        return "tier_changed"
    if f == "direction":
        return "direction_flipped"
    if f == "is_retracted":
        return "retraction"
    if f == "summary":
        return "prose_refresh"
    return "other"


@app.get("/api/me/corpus-deltas")
def api_corpus_deltas(days: int = 7, limit: int = 8):
    """What changed in the corpus this week — for the Sunday briefing
    email body (which can't include personal data, only public news)."""
    since = (datetime_now() - timedelta(days=int(days))).isoformat(timespec="seconds")
    with connect() as conn:
        promotions = conn.execute("""
            SELECT h.edge_id, h.old_value, h.new_value, h.changed_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id=h.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE h.field='tier' AND h.new_value IN ('A','B')
              AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
              AND h.changed_at >= ?
            ORDER BY h.changed_at DESC
            LIMIT ?""", (since, limit)).fetchall()
        retractions = conn.execute("""
            SELECT h.edge_id, h.changed_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id=h.edge_id
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE h.field='is_retracted' AND h.new_value='1'
              AND h.changed_at >= ?
            ORDER BY h.changed_at DESC
            LIMIT ?""", (since, max(2, limit // 2))).fetchall()
    return JSONResponse({
        "since": since,
        "promotions": [dict(r) for r in promotions],
        "retractions": [dict(r) for r in retractions],
    })


@app.post("/api/me/parse-lab-image")
async def api_parse_lab_image(request: Request):
    """Pro-only endpoint. Parse a lab PDF or image into structured
    {name,value,unit,date} rows. Configurable backend:

      1) HU_VISION_MODEL env set + Ollama reachable → local vision
         model (no data leaves the user's machine). Set this for
         maximally-private local use.
      2) ANTHROPIC_API_KEY env set → Claude Haiku with vision
         (image transits Anthropic once, not stored, ~$0.01/image).
      3) Neither → returns 503 with a helpful explainer.

    The endpoint NEVER stores the uploaded image. The browser holds the
    image, posts it once, gets parsed text back, throws the bytes away."""
    import base64
    import os
    import json as _json

    # Pro gate. Falls through to a 401/402 if the user is anon or free.
    account = current_account(request.cookies.get(SESSION_COOKIE))
    pro_block = require_pro(account)
    if pro_block is not None:
        return pro_block

    form = await request.form()
    upload = form.get("file")
    if not upload or not hasattr(upload, "read"):
        return JSONResponse({"error": "no file"}, status_code=400)

    raw = await upload.read()
    if not raw:
        return JSONResponse({"error": "empty file"}, status_code=400)
    if len(raw) > 8 * 1024 * 1024:
        return JSONResponse({"error": "file too large (max 8 MB)"}, status_code=413)

    mime = upload.content_type or "application/octet-stream"
    is_pdf = mime == "application/pdf" or upload.filename.lower().endswith(".pdf")

    instruction = (
        "You are a lab-report parser. Extract every laboratory test "
        "result from this document. Return JSON ONLY, of the form:\n"
        '{"labs":[{"name":"TSH","value":3.8,"unit":"mIU/L","date":"2024-09-12"}]}\n'
        "Rules:\n"
        "- 'name' is the canonical short test name (TSH, Free T4, ApoB, "
        "  HbA1c, Vitamin D 25-OH, etc.). If the report uses a long "
        "  name, normalize.\n"
        "- 'value' is a number. If the report shows '<5' use 5; if '>200' "
        "  use 200. If a range like '90-110' is given as a single value, "
        "  pick the midpoint.\n"
        "- 'unit' is the lab's unit string (mg/dL, mIU/L, ng/mL, %, etc.).\n"
        "- 'date' is the collection date in YYYY-MM-DD if you can find it.\n"
        "- IGNORE reference ranges, comments, and any non-numeric tests.\n"
        "- Skip rows where the value is missing or unparseable.\n"
        "- Return ONLY the JSON object, no prose, no markdown fence."
    )

    backend = "unconfigured"
    parsed: dict | None = None

    # ── (1) Local Ollama vision route ──────────────────────────────
    vision_model = os.environ.get("HU_VISION_MODEL")
    if vision_model:
        import urllib.request
        ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        try:
            body = _json.dumps({
                "model": vision_model,
                "prompt": instruction,
                "images": [base64.b64encode(raw).decode()],
                "stream": False,
                "format": "json",
            }).encode()
            req = urllib.request.Request(
                f"{ollama_url}/api/generate", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                ollama_resp = _json.loads(resp.read())
            text = ollama_resp.get("response", "")
            try:
                parsed = _json.loads(text)
                backend = f"ollama:{vision_model}"
            except Exception:
                # Try to find the JSON in mixed output.
                import re as _re
                m = _re.search(r"\{[\s\S]*\}", text)
                if m:
                    parsed = _json.loads(m.group(0))
                    backend = f"ollama:{vision_model}"
        except Exception as exc:
            print(f"[parse-lab] ollama path failed: {exc}", flush=True)

    # ── (2) Cloud fallback via Anthropic Claude vision ─────────────
    if parsed is None and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from anthropic import Anthropic
            client = Anthropic()
            content = []
            if is_pdf:
                content.append({
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf",
                               "data": base64.b64encode(raw).decode()},
                })
            else:
                # Default to JPEG; Anthropic also accepts png/gif/webp.
                content.append({
                    "type": "image",
                    "source": {"type": "base64",
                               "media_type": mime if mime.startswith("image/") else "image/jpeg",
                               "data": base64.b64encode(raw).decode()},
                })
            content.append({"type": "text", "text": instruction})
            resp = client.messages.create(
                model=os.environ.get("HU_PARSE_MODEL", "claude-haiku-4-5"),
                max_tokens=2048,
                messages=[{"role": "user", "content": content}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            try:
                parsed = _json.loads(text)
            except Exception:
                import re as _re
                m = _re.search(r"\{[\s\S]*\}", text)
                if m:
                    parsed = _json.loads(m.group(0))
            backend = "anthropic-haiku"
            # Best-effort cost record.
            try:
                from claude_client import cost_of, MODEL as _M
                from db import record_cost
                with connect() as conn:
                    record_cost(conn, provider="anthropic",
                                model=os.environ.get("HU_PARSE_MODEL", "claude-haiku-4-5"),
                                operation="parse_lab_image",
                                input_tokens=resp.usage.input_tokens,
                                output_tokens=resp.usage.output_tokens,
                                usd=0.0,  # Haiku pricing not in PRICE_PER_MTOK; logged as 0
                                ref="me-data")
            except Exception:
                pass
        except Exception as exc:
            print(f"[parse-lab] anthropic path failed: {exc}", flush=True)

    if parsed is None:
        return JSONResponse({
            "error": "parser-unavailable",
            "message": (
                "Neither local Ollama nor Claude is configured on this "
                "server. Set HU_VISION_MODEL=llava:7b for local parsing, "
                "or ANTHROPIC_API_KEY for cloud."
            ),
        }, status_code=503)

    labs = parsed.get("labs") if isinstance(parsed, dict) else None
    if not isinstance(labs, list):
        return JSONResponse({"error": "no labs found", "raw": parsed}, status_code=200)
    return JSONResponse({"labs": labs, "backend": backend, "count": len(labs)})


@app.get("/api/me/finding-evidence")
def api_finding_evidence(slug: str = ""):
    """Stateless: given a medical-record finding slug (e.g.
    'disc_degeneration'), return relevant edges from the corpus."""
    slug = (slug or "").strip().lower()
    if not slug:
        return JSONResponse({"matched": False})
    edges = _edges_for_entity_slugs([slug])
    interventions = _interventions_for_outcomes([slug])
    return JSONResponse({
        "matched":      bool(edges or interventions),
        "slug":         slug,
        "edges":        edges,
        "interventions": interventions,
    })


# ────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────
# Auth endpoints — magic-link login via Supabase, signed session cookie
# ────────────────────────────────────────────────────────────────────


@app.post("/api/auth/login")
def api_auth_login(request: Request, email: str = Form(...)):
    """User submits an email; we ask Supabase to send a magic link.
    The link points back to /auth/callback which finalises the session."""
    em = (email or "").strip().lower()
    if "@" not in em or len(em) > 200:
        return JSONResponse({"ok": False, "error": "invalid email"}, status_code=400)
    base = str(request.base_url).rstrip("/")
    redirect = f"{base}/auth/callback"
    ok, msg = send_magic_link(em, redirect)
    if not ok:
        return JSONResponse({"ok": False, "error": msg}, status_code=502)
    return JSONResponse({"ok": True, "message":
        "Check your inbox — we just sent a magic link to " + em + "."})


@app.get("/auth/callback", response_class=HTMLResponse)
def auth_callback_page(request: Request):
    """Supabase redirects here after the user clicks the magic link.
    The token comes back in the URL hash (#access_token=...) which the
    server can't see directly, so we render a tiny page that extracts
    it client-side and POSTs it to /auth/exchange. After that POST,
    we redirect to /me/data with the session cookie set."""
    return render(request, "auth_callback.html", {"title": "Signing you in…"})


@app.post("/auth/exchange")
def auth_exchange(request: Request, access_token: str = Form(...)):
    """Verify the access_token Supabase returned, set our signed
    session cookie, and respond with where to redirect."""
    if not access_token:
        return JSONResponse({"ok": False, "error": "missing token"}, status_code=400)
    account, msg = exchange_token_for_session(access_token)
    if not account:
        return JSONResponse({"ok": False, "error": msg}, status_code=401)
    cookie = encode_session(account.user_id, account.email)
    resp = JSONResponse({"ok": True, "redirect": "/me/data?welcome=1",
                         "email": account.email})
    resp.set_cookie(
        SESSION_COOKIE, cookie,
        max_age=SESSION_MAX_AGE, httponly=True, samesite="lax",
        secure=request.url.scheme == "https",
    )
    return resp


# Categories of plans the challenge endpoint refuses to engage with
# beyond an immediate safety-escalation message. Surfaced from a real
# QA-harness P0 finding ("user asked to stop statin without telling
# doctor; system gave detailed counterpoints"). These plans require
# a clinician, not an LLM.
_DANGER_PATTERNS = [
    # Medication discontinuation without supervision.
    (r"stop\s+(my|taking)?\s*(statin|warfarin|coumadin|anticoagulant|"
     r"apixaban|rivaroxaban|dabigatran|edoxaban|lithium|insulin|"
     r"levothyroxine|antidepressant|ssri|snri|antipsychotic|"
     r"chemotherapy|immunosuppressant|methadone|buprenorphine|"
     r"benzodiazepine|gabapentin|opioid|prednisone|corticosteroid)",
     "discontinue_high_risk_medication"),
    (r"(without\s+telling|behind\s+(my|the)\s+(doctor|gp)'?s?\s+back|"
     r"don'?t\s+tell\s+(my\s+)?(doctor|gp))",
     "withholding_from_clinician"),
    (r"quit\s+(my)?\s*(insulin|warfarin|lithium|antidepressant|"
     r"chemotherapy|methadone|antipsychotic)",
     "discontinue_high_risk_medication"),
    # Self-harm / suicidal ideation (escalation, not engagement).
    (r"(kill\s+myself|end\s+my\s+life|suicide|overdose\s+on)",
     "self_harm_signal"),
    # Extreme fasting in vulnerable groups.
    (r"(14[-\s]?day|21[-\s]?day|30[-\s]?day|month\s*long)\s+"
     r"(water\s+)?fast",
     "extreme_fasting"),
]


def _safety_classify(plan: str) -> tuple[str | None, str | None]:
    """Detect plans that need a hard safety response instead of the
    usual devil's-advocate treatment. Returns (category, message) or
    (None, None) if the plan is fine to challenge normally."""
    import re as _re
    p = (plan or "").lower()
    for pattern, category in _DANGER_PATTERNS:
        if _re.search(pattern, p):
            messages = {
                "discontinue_high_risk_medication":
                    "This plan involves stopping a medication that needs "
                    "clinician supervision. Sudden withdrawal of statins "
                    "(rebound MI risk), anticoagulants (clot risk), "
                    "insulin or thyroid hormone (organ-level destabilisation), "
                    "antidepressants (discontinuation syndrome) — all of these "
                    "carry documented harm when stopped abruptly. We won't "
                    "produce a counterpoints list for this category. Please "
                    "talk to your prescriber first.",
                "withholding_from_clinician":
                    "We won't help you make medical changes your prescriber "
                    "doesn't know about. The safest version of any change "
                    "is one your clinician has been briefed on — even if "
                    "their answer is 'yes, that's fine.'",
                "self_harm_signal":
                    "If you're thinking about hurting yourself, this isn't "
                    "the right tool. In the US: 988 (Suicide & Crisis "
                    "Lifeline). In the UK: 116 123 (Samaritans). In the EU: "
                    "112. We'll be here when you're ready.",
                "extreme_fasting":
                    "Fasts of two weeks or longer carry meaningful refeeding-"
                    "syndrome and electrolyte risks, especially for anyone on "
                    "medication, with diabetes, or with a history of "
                    "disordered eating. We won't produce a counterpoints "
                    "list — this needs clinical supervision (it's done in "
                    "monitored settings, not unsupervised).",
            }
            return category, messages.get(category)
    return None, None


@app.post("/api/me/challenge")
async def api_me_challenge(request: Request):
    """Adaptive devil's-advocate. The user states what they're
    thinking of doing; we look up the relevant edges in the corpus,
    pull the strongest counter-evidence, then ask Claude to write a
    structured challenge. The LLM only ever sees PUBLIC corpus rows
    plus a small set of fields the user explicitly puts in their plan
    statement — no PHI from /me/data.

    SAFETY GATE: plans that fall into well-known dangerous categories
    (medication discontinuation without supervision, self-harm signals,
    extreme fasting) bypass the LLM entirely and return a
    safety_block response with a mandatory clinician-escalation CTA."""
    body = await request.json()
    plan = (body.get("plan") or "").strip()[:1000]
    if not plan:
        return JSONResponse({"error": "missing plan"}, status_code=400)

    # SAFETY GATE — handle dangerous-category plans BEFORE the LLM.
    safety_category, safety_message = _safety_classify(plan)
    if safety_category:
        challenge_payload = {
            "summary": safety_message,
            "counterpoints": [],
            "questions_for_clinician": [
                "Why was this medication originally prescribed?",
                "What would replace its protective effect if we stop it?",
                "If we do decide to stop, what's the safest taper?",
                "What symptoms should I watch for during/after?",
            ],
            "signals_to_watch": [],
            "mandatory_action": (
                "Talk to your prescriber or pharmacist BEFORE making "
                "any change. If urgent: NHS 111 / 911 / your local "
                "after-hours line."
            ),
            "disclaimer": (
                "This is educational synthesis, not medical advice. "
                "Stopping medications without clinician supervision can "
                "be dangerous regardless of how confident you feel."
            ),
        }
        # Apply safety-voice middleware to the questions list too.
        challenge_payload["questions_for_clinician"] = _apply_safety_voice_to_list(
            challenge_payload["questions_for_clinician"])
        return JSONResponse({
            "ok": True,
            "plan": plan,
            "safety_block": True,
            "safety_category": safety_category,
            "challenge": challenge_payload,
            "matched_factors": [],
            "corpus_edges": [],
        })
    # Find candidate factors mentioned in the plan: simple keyword
    # match against entity names. Anything we recognise becomes a
    # corpus lookup.
    plan_lower = plan.lower()
    factor_slugs: list[str] = []
    candidate_edges: list[dict] = []
    with connect() as conn:
        # Pull factor names + slugs and check substring inclusion.
        ents = conn.execute(
            "SELECT slug, name, kind FROM entity "
            "WHERE kind IN ('drug','supplement','food','behavior','activity','nutrient','process')"
        ).fetchall()
        for e in ents:
            n = (e["name"] or "").lower()
            if not n or len(n) < 4:
                continue
            if n in plan_lower:
                factor_slugs.append(e["slug"])
        factor_slugs = list(dict.fromkeys(factor_slugs))[:6]
        if factor_slugs:
            ph = ",".join("?" * len(factor_slugs))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, e.effect_quant,
                       f.slug AS f_slug, f.name AS f_name, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id=e.factor_id
                JOIN entity o ON o.id=e.outcome_id
                WHERE f.slug IN ({ph}) AND e.tier IN ('A','B','C','X')
                ORDER BY CASE e.direction
                    WHEN 'harmful' THEN 1
                    WHEN 'u_shaped' THEN 2
                    WHEN 'mixed' THEN 3
                    ELSE 4 END,
                  CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'X' THEN 3 ELSE 4 END
                LIMIT 12""", factor_slugs).fetchall()
            candidate_edges = [dict(r) for r in rows]

    # Build the corpus context as plain text — no LLM slop, just facts.
    corpus_lines = []
    for e in candidate_edges[:8]:
        corpus_lines.append(
            f"- {e['f_name']} → {e['o_name']}: tier {e['tier']}, "
            f"{e['direction']}{', ' + str(e['effect_size']) + ' effect' if e.get('effect_size') else ''}"
            f"{'. ' + e['summary'] if e.get('summary') else ''}"
        )
    corpus_block = "\n".join(corpus_lines) if corpus_lines else "(no directly-matching edges found)"

    system = (
        "You are an evidence-grounded skeptic for a personal health platform. "
        "The user states a plan. Your job is to challenge it productively — "
        "surface the strongest counter-evidence, the contested edges, and the "
        "questions the user should ask their clinician BEFORE acting. "
        "Never tell them not to do it. Never tell them to do it. Frame "
        "as: 'here's what the literature says you should weigh.' "
        "Cite the corpus block. Stay under 280 words.\n\n"
        "HARD RULES:\n"
        "- If the plan involves changing a prescription medication, the "
        "  first counterpoint MUST start with 'Talk to your prescriber "
        "  before changing the dose or stopping.'\n"
        "- If the plan involves stopping a medication, you MUST flag the "
        "  specific clinical risk class (rebound CV events for statins, "
        "  clot risk for anticoagulants, discontinuation syndrome for "
        "  SSRIs, etc.). Be specific, not generic.\n"
        "- Output is read by patients with widely varying literacy. "
        "  Plain language, not jargon.\n"
        "- ALWAYS FINISH YOUR SENTENCES. If you're running short on token "
        "  budget, return FEWER bullet points rather than truncated ones. "
        "  Truncated safety guidance is a P0 bug.\n"
        "- The `summary` field MUST start with the literal text "
        "  'Evidence-based educational synthesis, not medical advice — ' "
        "  before any other content.\n\n"
        "Respond in this strict JSON shape:\n"
        '{ "summary": "1-2 sentence framing", '
        '"counterpoints": ["...", "..."], '
        '"questions_for_clinician": ["...", "...", "..."], '
        '"signals_to_watch": ["...", "..."], '
        '"mandatory_action": "1 sentence ALWAYS reminding them to talk to a clinician before acting" }'
    )
    user = (
        f"USER'S STATED PLAN:\n{plan}\n\n"
        f"RELEVANT EDGES FROM OUR CORPUS:\n{corpus_block}\n\n"
        "Return JSON only."
    )

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return JSONResponse({"error": "LLM not configured", "corpus": candidate_edges}, status_code=503)
    try:
        from claude_client import call as claude_call, extract_json
        text, _usage = claude_call(
            system=system, user=user,
            operation="challenge", max_tokens=900, temperature=0.3,
        )
        # Robust JSON extraction: extract_json may return None or
        # raise on unbalanced output. Fall through to a deterministic
        # template rather than 500-ing on the user.
        parsed: dict | None = None
        try:
            parsed = extract_json(text)
            if not isinstance(parsed, dict):
                parsed = None
        except Exception as exc:
            print(f"[challenge] extract_json failed: {exc}")
        if not parsed:
            # LLM output unparseable — use a structured fallback so the
            # UI still renders something useful.
            parsed = _deterministic_challenge_fallback(plan, candidate_edges)
        # Always enforce the clinician-escalation CTA.
        if not parsed.get("mandatory_action"):
            parsed["mandatory_action"] = (
                "Talk to your prescriber, pharmacist, or another "
                "qualified clinician before acting on any of this."
            )
        # Always lead with an explicit "educational, not medical advice"
        # disclaimer (P0 #3 + P1 missing-disclaimer pattern).
        parsed["disclaimer"] = (
            "This is educational synthesis, not medical advice. "
            "Discuss any change to medication, supplement, or "
            "lifestyle with a qualified clinician who knows your full "
            "history before acting."
        )
        # Safety-voice transforms across every prose field (β fix).
        parsed = _harden_challenge_payload(parsed)
        return JSONResponse({
            "ok": True,
            "plan": plan,
            "safety_block": False,
            "matched_factors": factor_slugs,
            "corpus_edges": candidate_edges[:6],
            "challenge": parsed,
        })
    except Exception as exc:
        # Even on a hard exception, give the UI something to render.
        print(f"[challenge] hard error: {exc}")
        return JSONResponse({
            "ok": True,
            "plan": plan,
            "safety_block": False,
            "matched_factors": factor_slugs,
            "corpus_edges": candidate_edges[:6],
            "challenge": _deterministic_challenge_fallback(plan, candidate_edges),
            "degraded": True,
        })


# ────────────────────────────────────────────────────────────────────
# Safety-voice middleware (β fix from QA sweep)
# ────────────────────────────────────────────────────────────────────
#
# Every LLM-generated piece of prose runs through _apply_safety_voice
# before serialisation. Three transforms, all surgical:
#
#   1. Prepend the educational-disclaimer phrase to the leading
#      summary/verdict if it isn't already there. Reviewers consistently
#      flagged prose that lacks an opening disclaimer even when a
#      separate disclaimer field was populated.
#
#   2. Soften prescriptive verbs to evidence-framed ones. "Don't do
#      this" → "the literature suggests caution here". "Stop" →
#      "consider whether to continue". This is the single biggest lever
#      against the claim-creep finding category (67 hits last sweep).
#
#   3. Append "discuss with your clinician" to any sentence that names
#      a medication, dose, or "should/must" verb. Cheap, but
#      consistently caught by the privacy / CDS reviewer.
#
# The function is idempotent — running it twice produces the same
# output, so the daily cron + the live request paths can both call it
# without doubling phrasing.

_DISCLAIMER_PREFIX = "Evidence-based educational synthesis, not medical advice — "

_PRESCRIPTIVE_PATTERNS = [
    # (regex, replacement). Case-insensitive.
    (r"\byou should not\b", "the evidence suggests caution against"),
    (r"\byou must not\b", "the evidence is consistent that avoiding this is safer"),
    (r"\byou should\b", "the evidence supports"),
    (r"\byou must\b", "evidence points strongly toward"),
    (r"\bdon't\b", "consider not"),
    (r"\bdo not\b", "consider not"),
    (r"\bstop taking\b", "discuss stopping with your clinician for"),
    (r"\bquit taking\b", "discuss discontinuation with your clinician for"),
    (r"\bnever take\b", "evidence suggests avoiding"),
    (r"\bavoid\b", "the literature flags caution about"),
    # Hedge confident first-person framings.
    (r"\bi recommend\b", "the literature suggests"),
    (r"\bi suggest\b", "the literature suggests"),
    (r"\bwe recommend\b", "the evidence supports considering"),
]

_CLINICAL_TERMS = _re_stack.compile(
    r"\b(statin|warfarin|anticoagulant|insulin|levothyroxine|ssri|snri|"
    r"benzo|opioid|ace[i]?|arb|antibiotic|chemo|antipsychotic|"
    r"metformin|sglt2|glp1|semaglutide|tirzepatide|methotrexate|"
    r"clozapine|lithium|gabapentin|prednisone|cortico|amiodarone)",
    _re_stack.IGNORECASE,
)


def _apply_safety_voice(text: Optional[str], *, is_summary: bool = False) -> str:
    """Run all three safety-voice transforms on a string. Idempotent.
    Pass is_summary=True to enforce the leading disclaimer prefix."""
    if not text or not isinstance(text, str):
        return text or ""
    s = text.strip()
    # Transform 1: prepend the disclaimer prefix on summary-class fields.
    if is_summary and not s.startswith(_DISCLAIMER_PREFIX):
        # If the model produced its own variant ("Educational synthesis...")
        # be permissive — don't double-prefix.
        if not _re_stack.match(r"^(evidence[- ]based )?educational( synthesis)?", s, _re_stack.IGNORECASE):
            s = _DISCLAIMER_PREFIX + (s[:1].lower() + s[1:] if s else s)
    # Transform 2: prescriptive → evidence-framed.
    for pattern, replacement in _PRESCRIPTIVE_PATTERNS:
        s = _re_stack.sub(pattern, replacement, s, flags=_re_stack.IGNORECASE)
    # Transform 3: trailing clinician clause where medication terms appear
    # and the sentence is short enough to append cleanly.
    if _CLINICAL_TERMS.search(s) and "clinician" not in s.lower():
        if len(s) < 600 and not s.endswith((".", "—", "?")):
            s += "."
        if len(s) < 600 and "discuss with" not in s.lower() and "talk to your" not in s.lower():
            s = s.rstrip(".") + " — discuss with your clinician before acting."
    return s


def _apply_safety_voice_to_list(items: Optional[list]) -> list:
    """Map the safety-voice transform across an iterable of strings."""
    if not items:
        return []
    out: list = []
    for x in items:
        if isinstance(x, str):
            out.append(_apply_safety_voice(x))
        else:
            out.append(x)
    return out


def _harden_challenge_payload(parsed: dict) -> dict:
    """Apply safety-voice transforms across every prose field of a
    /api/me/challenge response."""
    if not isinstance(parsed, dict):
        return parsed
    parsed["summary"] = _apply_safety_voice(parsed.get("summary"), is_summary=True)
    parsed["counterpoints"] = _apply_safety_voice_to_list(parsed.get("counterpoints"))
    parsed["questions_for_clinician"] = _apply_safety_voice_to_list(parsed.get("questions_for_clinician"))
    parsed["signals_to_watch"] = _apply_safety_voice_to_list(parsed.get("signals_to_watch"))
    parsed["mandatory_action"] = _apply_safety_voice(parsed.get("mandatory_action"))
    return parsed


def _harden_claim_check_verdict(verdict: dict) -> dict:
    """Apply safety-voice transforms across every prose field of a
    /api/claim-check verdict."""
    if not isinstance(verdict, dict):
        return verdict
    verdict["verdict"] = _apply_safety_voice(verdict.get("verdict"), is_summary=True)
    verdict["personal_relevance"] = _apply_safety_voice(verdict.get("personal_relevance"))
    verdict["what_is_true"] = _apply_safety_voice_to_list(verdict.get("what_is_true"))
    verdict["what_is_false_or_overstated"] = _apply_safety_voice_to_list(
        verdict.get("what_is_false_or_overstated"))
    return verdict


def _deterministic_challenge_fallback(plan: str, edges: list[dict]) -> dict:
    """When the LLM is unavailable or returns unparseable output, emit a
    structured response built from corpus rows alone."""
    summary = "We couldn't synthesize a full response right now. Here's what the corpus shows for the factors in your plan."
    counterpoints = []
    questions = []
    signals = []
    if edges:
        harmful = [e for e in edges if e.get("direction") == "harmful"]
        contested = [e for e in edges if e.get("direction") in ("u_shaped", "mixed")]
        for e in harmful[:3]:
            counterpoints.append(
                f"{e.get('f_name','')} → {e.get('o_name','')} "
                f"(tier {e.get('tier','?')}, harmful). {(e.get('summary') or '')[:180]}"
            )
        for e in contested[:2]:
            counterpoints.append(
                f"Contested: {e.get('f_name','')} → {e.get('o_name','')} "
                f"(tier {e.get('tier','?')}). {(e.get('summary') or '')[:180]}"
            )
    if not counterpoints:
        counterpoints.append("No directly-matching corpus rows; consider rephrasing the plan to a specific factor.")
    questions = [
        "Is this aligned with your current medications and conditions?",
        "What's the smallest version of this plan you could test first?",
        "What outcome would tell you it's working — and over what window?",
        "What outcome would tell you to stop?",
    ]
    signals = [
        "Track any change in symptoms in the first 2 weeks.",
        "Re-test relevant labs at the cadence appropriate for the intervention.",
    ]
    return {
        "summary": summary,
        "counterpoints": counterpoints,
        "questions_for_clinician": questions,
        "signals_to_watch": signals,
    }


# ────────────────────────────────────────────────────────────────────
# Always-on endpoints — encrypted sync, push subscribe, daily compute,
# shift-alert queue, settings.
# ────────────────────────────────────────────────────────────────────


@app.get("/api/me/synced-blob")
async def api_me_synced_blob(request: Request):
    """Return the user's encrypted blob if one exists. Auth required."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    try:
        r = (sb.table("synced_data").select("*")
             .eq("account_id", account.user_id).limit(1).execute())
        rows = list(r.data or [])
        return JSONResponse(rows[0] if rows else None)
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)


@app.post("/api/me/synced-blob")
async def api_me_synced_blob_save(request: Request):
    """Upsert the user's encrypted blob. Server stores ciphertext only."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    body = await request.json()
    if not body.get("ciphertext") or not body.get("iv") or not body.get("salt"):
        return JSONResponse({"error": "missing_fields"}, status_code=400)
    if len(body["ciphertext"]) > 1_500_000:  # ~1.5 MB cap
        return JSONResponse({"error": "too_large"}, status_code=413)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    try:
        sb.table("synced_data").upsert({
            "account_id": account.user_id,
            "ciphertext": body["ciphertext"],
            "iv": body["iv"],
            "salt": body["salt"],
            "iterations": int(body.get("iterations", 200000)),
            "updated_at": datetime_now().isoformat(timespec="seconds"),
        }, on_conflict="account_id").execute()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)


@app.post("/api/me/compute-summary")
async def api_me_compute_summary(request: Request):
    """Write the user's opt-in 'summary view' the server can read for
    daily compute. Anonymous = no-op. PHI is intentionally NOT here —
    only derived signals (z-scores, edge IDs, dates, flags)."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    body = await request.json()
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    payload = {
        "account_id": account.user_id,
        "timezone": (body.get("timezone") or "UTC")[:80],
        "watch_edges": [int(x) for x in (body.get("watch_edges") or [])][:500],
        "anomaly_zscores": body.get("anomaly_zscores") or {},
        "recent_trends": body.get("recent_trends") or {},
        "open_recommendations": body.get("open_recommendations") or [],
        "next_visit": body.get("next_visit"),
        "flagged_labs": body.get("flagged_labs") or [],
        "active_protocols": body.get("active_protocols") or [],
        "agreed_to_daily_compute": bool(body.get("agreed_to_daily_compute", False)),
        "updated_at": datetime_now().isoformat(timespec="seconds"),
    }
    if payload["agreed_to_daily_compute"]:
        payload["agreed_at"] = payload["updated_at"]
    try:
        sb.table("compute_summaries").upsert(
            payload, on_conflict="account_id"
        ).execute()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)


@app.get("/api/me/compute-summary")
async def api_me_compute_summary_get(request: Request):
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"agreed_to_daily_compute": False})
    try:
        r = (sb.table("compute_summaries").select("*")
             .eq("account_id", account.user_id).limit(1).execute())
        rows = list(r.data or [])
        return JSONResponse(rows[0] if rows else {"agreed_to_daily_compute": False})
    except Exception:
        return JSONResponse({"agreed_to_daily_compute": False})


# ─── Weekly self-report check-in ──────────────────────────────────


@app.get("/api/me/checkin")
def api_me_checkin_get(request: Request):
    """Return the user's last 12 weekly check-ins."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    rows = alwayson.fetch_recent_checkins(account.user_id, n=12)
    return JSONResponse({"checkins": rows})


@app.post("/api/me/checkin")
async def api_me_checkin_post(request: Request):
    """Submit a weekly self-report. Idempotent per (account, week)."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    body = await request.json()
    # Snap to Monday of the week (ISO week start).
    week_start = body.get("for_week_start")
    if not week_start:
        d = datetime_now().date()
        week_start = (d - timedelta(days=d.weekday())).isoformat()
    def _i(field):
        v = body.get(field)
        try:
            n = int(v)
            return min(10, max(1, n))
        except Exception:
            return None
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    try:
        sb.table("weekly_checkins").upsert({
            "account_id": account.user_id,
            "for_week_start": week_start,
            "energy": _i("energy"),
            "sleep_quality": _i("sleep_quality"),
            "mood": _i("mood"),
            "stress": _i("stress"),
            "new_symptoms": (body.get("new_symptoms") or "").strip()[:500] or None,
            "changed_in_stack": (body.get("changed_in_stack") or "").strip()[:500] or None,
            "submitted_at": datetime_now().isoformat(timespec="seconds"),
        }, on_conflict="account_id,for_week_start").execute()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)


# ─── Stack composition + lab-recheck analysis (read-only views) ─────


@app.get("/api/me/stack-analysis")
async def api_me_stack_analysis(request: Request):
    """Return stack-cluster findings + flagged labs the user could be
    pairing them with. Works for both anon (uses body) and signed-in
    (uses compute summary). Anonymous callers should POST instead."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"findings": [], "rechecks_due": []})
    try:
        r = (sb.table("compute_summaries").select("*")
             .eq("account_id", account.user_id).limit(1).execute())
        rows = list(r.data or [])
        summary = rows[0] if rows else {}
    except Exception:
        summary = {}
    stack_slugs = [p.get("factor") for p in (summary.get("active_protocols") or []) if p.get("factor")]
    lab_names = [l.get("name") for l in (summary.get("flagged_labs") or []) if l.get("name")]
    findings = alwayson.stack_composition_findings(stack_slugs, lab_names)
    rechecks = alwayson.due_lab_rechecks(summary)
    return JSONResponse({
        "findings": findings,
        "rechecks_due": rechecks,
        "stack_size": len(stack_slugs),
        "labs_count": len(lab_names),
    })


@app.post("/api/me/stack-analysis")
async def api_me_stack_analysis_post(request: Request):
    """Anonymous-friendly: pass {stack_slugs:[], lab_names:[]} directly."""
    body = await request.json()
    stack_slugs = [s for s in (body.get("stack_slugs") or []) if isinstance(s, str)]
    lab_names = [s for s in (body.get("lab_names") or []) if isinstance(s, str)]
    findings = alwayson.stack_composition_findings(stack_slugs, lab_names)
    fake_summary = {
        "flagged_labs": [{"name": n} for n in lab_names],
        "active_protocols": [{"factor": s} for s in stack_slugs],
        "open_recommendations": [],
    }
    rechecks = alwayson.due_lab_rechecks(fake_summary)
    return JSONResponse({
        "findings": findings,
        "rechecks_due": rechecks,
        "stack_size": len(stack_slugs),
        "labs_count": len(lab_names),
    })


@app.post("/api/me/push-subscribe")
async def api_me_push_subscribe(request: Request):
    """Register a Web Push subscription for the current account."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    body = await request.json()
    sub = body.get("subscription") or {}
    endpoint = sub.get("endpoint")
    keys = sub.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth_key = keys.get("auth")
    if not (endpoint and p256dh and auth_key):
        return JSONResponse({"error": "incomplete subscription"}, status_code=400)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    try:
        sb.table("push_subscriptions").upsert({
            "account_id": account.user_id,
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth_key,
            "user_agent": request.headers.get("user-agent", "")[:200],
            "last_seen_at": datetime_now().isoformat(timespec="seconds"),
        }, on_conflict="endpoint").execute()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)


@app.get("/api/vapid-key")
def api_vapid_key():
    import os
    return JSONResponse({"public_key": os.environ.get("VAPID_PUBLIC_KEY", "")})


@app.get("/api/cron/proactive-daily")
def cron_proactive_daily(request: Request):
    """Daily personal compute. Runs once per ~24h via vercel cron.
    For each account with agreed_to_daily_compute=true, generates a
    daily briefing, stores it in daily_briefings, delivers via push
    (or email fallback). Idempotent: dedupes by (account, date)."""
    import os
    expected = os.environ.get("CRON_SECRET")
    auth = request.headers.get("authorization", "")
    if expected and auth != f"Bearer {expected}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"error": "no_supabase"}, status_code=503)
    # Pull all accounts with daily compute opted in.
    try:
        r = (sb.table("compute_summaries").select("*")
             .eq("agreed_to_daily_compute", True).execute())
        summaries = list(r.data or [])
    except Exception as exc:
        return JSONResponse({"error": str(exc)[:200]}, status_code=500)

    # Look up accounts in one batched call.
    ids = [s["account_id"] for s in summaries]
    accounts_by_id: dict = {}
    if ids:
        try:
            ar = (sb.table("accounts").select("id, email").in_("id", ids).execute())
            for a in (ar.data or []):
                accounts_by_id[a["id"]] = a
        except Exception:
            pass

    composed = 0
    delivered = 0
    skipped = 0
    for summary in summaries:
        account = accounts_by_id.get(summary["account_id"])
        if not account:
            skipped += 1
            continue
        # Skip if we already generated today.
        try:
            existing = (sb.table("daily_briefings")
                        .select("id")
                        .eq("account_id", account["id"])
                        .eq("generated_for_date",
                            alwayson._user_local_date(summary.get("timezone") or "UTC").isoformat())
                        .limit(1).execute())
            if existing.data:
                skipped += 1
                continue
        except Exception:
            pass
        briefing = alwayson.compute_daily_for_account(account, summary)
        if not briefing:
            skipped += 1
            continue
        composed += 1
        sent = alwayson.deliver_briefing(account, briefing)
        alwayson.save_briefing(account["id"], briefing, sent)
        if sent:
            delivered += 1

    # Also drain queued shift alerts (Move 5).
    shifts_sent = alwayson.drain_shift_alerts()

    return JSONResponse({
        "composed": composed,
        "delivered": delivered,
        "skipped": skipped,
        "shift_alerts_delivered": shifts_sent,
    })


@app.post("/api/cron/proactive-daily")
def cron_proactive_daily_post(request: Request):
    """POST mirror for one-click test runs from the dashboard."""
    return cron_proactive_daily(request)


@app.post("/api/me/recommendation")
async def api_me_recommendation(request: Request):
    """Mirror a client-side recommendation into Supabase, but ONLY if
    the user is signed in. Anonymous users keep their log in localStorage
    only. Idempotent — same (account_id, edge_id, source) within 14 days
    is a no-op via on_conflict."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"ok": False, "skipped": "anonymous"})
    body = await request.json()
    edge_id = body.get("edge_id")
    edge_label = (body.get("edge_label") or "")[:200]
    source = (body.get("source") or "system")[:40]
    if not edge_id:
        return JSONResponse({"ok": False, "error": "missing edge_id"}, status_code=400)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"ok": False, "skipped": "no_supabase"})
    try:
        # Avoid duplicates: query for an existing open recommendation
        # within 14 days for this (account, edge, source).
        from datetime import timedelta as _td
        since = (datetime_now() - _td(days=14)).isoformat(timespec="seconds")
        existing = sb.table("recommendations_log").select("id").eq(
            "account_id", account.user_id).eq("edge_id", int(edge_id)).eq(
            "source", source).gte("suggested_at", since).limit(1).execute()
        if existing.data:
            return JSONResponse({"ok": True, "deduped": True})
        sb.table("recommendations_log").insert({
            "account_id": account.user_id,
            "edge_id": int(edge_id),
            "edge_label": edge_label,
            "source": source,
        }).execute()
        return JSONResponse({"ok": True, "logged": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)


@app.post("/api/me/recommendation/close")
async def api_me_recommendation_close(request: Request):
    """Close a recommendation with a verdict (helped / no_change /
    harmed / never_tried). Used by the verdict buttons on /me/briefing
    when the user is signed in (vs anonymous, where state lives only
    in localStorage)."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"ok": False, "skipped": "anonymous"})
    body = await request.json()
    edge_id = body.get("edge_id")
    verdict = (body.get("verdict") or "").strip()
    if verdict not in ("helped", "no_change", "harmed", "never_tried"):
        return JSONResponse({"ok": False, "error": "bad verdict"}, status_code=400)
    sb = supabase_service()
    if sb is None:
        return JSONResponse({"ok": False, "skipped": "no_supabase"})
    try:
        sb.table("recommendations_log").update({
            "verdict": verdict,
            "closed_at": datetime_now().isoformat(timespec="seconds"),
        }).eq("account_id", account.user_id).eq("edge_id", int(edge_id)).is_(
            "closed_at", "null"
        ).execute()
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)


@app.post("/api/auth/logout")
def api_auth_logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/api/me/account")
def api_me_account(request: Request):
    """Returns the currently-logged-in account or null. Client uses
    this to decide whether to show 'Sign in' or the account chip."""
    account = current_account(request.cookies.get(SESSION_COOKIE))
    if not account:
        return JSONResponse({"signed_in": False})
    return JSONResponse({
        "signed_in": True,
        "email": account.email,
        "pro": account.is_pro,
        "pro_until": account.pro_until,
        "cron_subscribed": account.cron_subscribed,
    })


@app.post("/api/pro-waitlist")
def api_pro_waitlist(request: Request,
                     email: str = Form(...),
                     source: str = Form("")):
    """Capture an email for the Pro waitlist. Persists to Supabase
    (Vercel-safe writeable backend); falls back to email notification
    + stderr log if Supabase isn't configured."""
    import os, sys
    em = (email or "").strip().lower()
    if "@" not in em or len(em) > 200:
        return RedirectResponse("/stack?waitlist=invalid", status_code=303)
    src = (source or "")[:40]
    ts = datetime_now().isoformat(timespec="seconds")
    persisted = False
    # 1) Persist to Supabase (RLS allows anon insert on pro_waitlist).
    sb = supabase_service()
    if sb is not None:
        try:
            sb.table("pro_waitlist").upsert(
                {"email": em, "source": src, "signed_up_at": ts},
                on_conflict="email"
            ).execute()
            persisted = True
        except Exception as exc:
            print(f"[waitlist] supabase upsert failed: {exc}", file=sys.stderr)
    # 2) Best-effort email notification.
    try:
        notify_to = os.environ.get("WAITLIST_NOTIFY_TO", "")
        if notify_to and os.environ.get("RESEND_API_KEY"):
            _resend_send(
                notify_to,
                f"[HU] Pro waitlist: {em}",
                f"<p>New Pro waitlist signup.</p>"
                f"<p><b>Email:</b> {em}</p>"
                f"<p><b>Source:</b> {src or '(none)'}</p>"
                f"<p><b>At:</b> {ts}</p>"
                f"<p><b>Persisted to Supabase:</b> {persisted}</p>")
    except Exception as exc:
        print(f"[waitlist] resend notify failed: {exc}", file=sys.stderr)
    print(f"[waitlist] {em} via {src} at {ts} (supabase={persisted})", file=sys.stderr)
    return RedirectResponse("/stack?waitlist=ok", status_code=303)


@app.get("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\nSitemap: https://health-universe.vercel.app/sitemap.xml\n",
        media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    base = "https://health-universe.vercel.app"
    urls = [f"{base}/", f"{base}/discoveries", f"{base}/myths", f"{base}/changes",
            f"{base}/me", f"{base}/search"]
    urls += [f"{base}/tier/{t}" for t in ("A", "B", "C", "D", "X")]
    with connect() as conn:
        urls += [f"{base}/category/{c['slug']}" for c in CATEGORIES]
        for r in conn.execute("SELECT id, updated_at FROM edge").fetchall():
            urls.append(f"{base}/edge/{r['id']}")
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"<url><loc>{u}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")


# ---- public JSON API --------------------------------------------------------

@app.get("/labs", response_class=HTMLResponse)
def labs_page(request: Request):
    """Lab + wearable ingestion foundations. Data stays in localStorage on
    this device (consistent with profile + diary trust model). The UI
    accepts blood-marker entries and a JSON upload from common formats.
    Future: feed these values into profile-aware ranking via /api/profile-brief."""
    # The set of biomarker entities we already track in the graph
    with connect() as conn:
        biomarkers = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind='biomarker' ORDER BY name"
        ).fetchall()]
    return render(request, "labs.html", {
        "title": "Labs and wearables",
        "biomarkers": biomarkers,
    })


# ---- /api/labs/parse-pdf and /api/labs/relevant-edges ------------------

_LAB_REGEXES = [
    # marker_slug, regex, unit_hint
    ("ldl_cholesterol",   r"\b(?:LDL[-\s]?C(?:holesterol)?)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", "mg/dL"),
    ("hdl_cholesterol",   r"\b(?:HDL[-\s]?C(?:holesterol)?)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", "mg/dL"),
    ("total_cholesterol", r"\b(?:Total[-\s]?C(?:holesterol)?|Cholesterol total)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", "mg/dL"),
    ("triglycerides",     r"\bTriglycerides\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", "mg/dL"),
    ("hba1c",             r"\b(?:HbA1c|A1c|Glycated[\s-]Hemoglobin)\D{0,40}?(\d{1,2}(?:\.\d+)?)\s*%?", "%"),
    ("fasting_glucose",   r"\b(?:Fasting\s+Glucose|Glucose\s+Fasting|FPG)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|mmol/L)?", "mg/dL"),
    ("ferritin",          r"\bFerritin\D{0,40}?(\d{1,4}(?:\.\d+)?)\s*(?:ng/mL|µg/L|ug/L)?", "ng/mL"),
    ("vitamin_d",         r"\b(?:25[-\s]?OH[-\s]?Vitamin[-\s]D|Vitamin\s+D|25\(OH\)D)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:ng/mL|nmol/L)?", "ng/mL"),
    ("crp",               r"\b(?:hs-?CRP|C-?reactive\s+Protein|CRP)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/L|mg/dL)?", "mg/L"),
    ("apob",              r"\bApoB\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|g/L)?", "mg/dL"),
    ("blood_pressure_systolic",  r"\b(?:Systolic\s+BP|SBP|Blood Pressure)\D{0,40}?(\d{2,3})\s*(?:/\d{2,3})?\s*mmHg?", "mmHg"),
    ("blood_pressure_diastolic", r"\b(?:Diastolic\s+BP|DBP)\D{0,40}?(\d{2,3})\s*mmHg?", "mmHg"),
    ("egfr",              r"\b(?:eGFR)\D{0,40}?(\d{1,3}(?:\.\d+)?)", "mL/min/1.73m²"),
    ("alt",               r"\b(?:ALT|SGPT)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*U/L?", "U/L"),
    ("ast",               r"\b(?:AST|SGOT)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*U/L?", "U/L"),
    ("tsh",               r"\bTSH\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mIU/L|µIU/mL)?", "mIU/L"),
    ("uric_acid",         r"\b(?:Uric\s+Acid)\D{0,40}?(\d{1,3}(?:\.\d+)?)\s*(?:mg/dL|µmol/L)?", "mg/dL"),
]


@app.post("/api/labs/parse-pdf")
async def labs_parse_pdf(request: Request):
    """Accepts a single PDF upload, extracts text, returns matched
    biomarkers as JSON. Parsing happens server-side but values are
    returned to the client and stored only in localStorage."""
    import re as _re
    form = await request.form()
    upload = form.get("file")
    if upload is None:
        return JSONResponse({"error": "no file"}, status_code=400)
    raw = await upload.read()
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(raw))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:
        return JSONResponse({"error": f"pdf parse: {exc}"}, status_code=400)
    found: list[dict] = []
    for slug, pattern, unit in _LAB_REGEXES:
        m = _re.search(pattern, text, _re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
            except Exception:
                continue
            found.append({"slug": slug, "value": val, "unit": unit,
                          "match": m.group(0)[:80]})
    return JSONResponse({"markers": found, "n_chars": len(text)})


@app.post("/api/labs/relevant-edges")
async def labs_relevant_edges(request: Request):
    """Given a list of marker slugs from the client, return the top
    evidence edges that mention them as factor or outcome. The client
    posts JSON: {"markers": ["ldl_cholesterol", "ferritin"]}."""
    body = await request.json()
    markers = [m for m in (body.get("markers") or []) if isinstance(m, str)]
    if not markers:
        return JSONResponse({"edges": []})
    ph = ",".join("?" * len(markers))
    with connect() as conn:
        rows = conn.execute(f"""
            SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                   f.slug AS f_slug, f.name AS f_name,
                   o.slug AS o_slug, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id
            WHERE (f.slug IN ({ph}) OR o.slug IN ({ph}))
              AND e.tier IN ('A','B','C')
            ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                     e.updated_at DESC
            LIMIT 24""", markers + markers).fetchall()
    return JSONResponse({"edges": [dict(r) for r in rows]})


@app.get("/protocols", response_class=HTMLResponse)
def protocols_index(request: Request):
    """N-of-1 protocol builder. State lives in localStorage on the
    user's device — same trust model as /diary. We ship a few templates."""
    templates_data = [
        {"slug": "magnesium-sleep",
         "title": "Magnesium for sleep onset",
         "factor": "magnesium",
         "outcome": "sleep_quality",
         "duration_days": 14,
         "intervention": "Take 200–300 mg magnesium glycinate ~1 hour before bed.",
         "measures": ["sleep_onset_min", "wake_count", "morning_freshness"],
         "evidence_edges": [],
         "blurb": "A small randomized signal exists. Two weeks is short but enough to notice direction."},
        {"slug": "earlier-dinner-glucose",
         "title": "Earlier dinner for glucose / sleep",
         "factor": "intermittent_fasting",
         "outcome": "insulin_resistance",
         "duration_days": 21,
         "intervention": "Finish dinner ≥3 hours before bed for 3 weeks.",
         "measures": ["fasting_glucose_proxy", "morning_freshness", "evening_hunger"],
         "blurb": "Time-restricted eating with an earlier window has small but real signal in cohorts."},
        {"slug": "creatine-strength",
         "title": "Creatine for strength + cognition",
         "factor": "creatine",
         "outcome": "sarcopenia",
         "duration_days": 56,
         "intervention": "5 g creatine monohydrate daily after the heaviest meal.",
         "measures": ["grip_or_pushups", "perceived_focus", "subjective_fatigue"],
         "blurb": "Tier-A on muscle outcomes; cognition signal is weaker but real for vegetarians and older adults."},
        {"slug": "morning-light-mood",
         "title": "Morning bright light for mood",
         "factor": "daylight_morning",
         "outcome": "depression",
         "duration_days": 14,
         "intervention": "≥10 minutes of outdoor daylight within an hour of waking.",
         "measures": ["morning_freshness", "mood", "afternoon_dip"],
         "blurb": "Cheap to try. Effect on circadian phase is well-established; subjective mood effect varies."},
        {"slug": "walking-mood",
         "title": "Daily walking for mood",
         "factor": "walking_daily",
         "outcome": "depression",
         "duration_days": 28,
         "intervention": "≥7000 steps daily, no calendar gaps.",
         "measures": ["mood", "energy", "stress"],
         "blurb": "Strong evidence on mortality + meaningful evidence on mood. Easy compliance test."},
    ]
    return render(request, "protocols.html", {
        "title": "N-of-1 protocols",
        "templates": templates_data,
    })


@app.get("/protocol/{slug}", response_class=HTMLResponse)
def protocol_detail(request: Request, slug: str):
    """Detail for a specific protocol template, including a 'start this'
    button that adds it to the localStorage diary protocol list."""
    return render(request, "protocol.html", {
        "title": "Protocol", "slug": slug,
    })


@app.get("/products", response_class=HTMLResponse)
def products_index(request: Request, entity: str = ""):
    """Supplement product-quality layer. Browse products keyed to
    supplement entities. Where we don't have independent testing data,
    we say so explicitly."""
    with connect() as conn:
        try:
            sql = ("SELECT p.*, e.name AS entity_name "
                   "FROM product p LEFT JOIN entity e ON e.slug = p.entity_slug")
            params: list = []
            if entity:
                sql += " WHERE p.entity_slug = ?"; params.append(entity)
            sql += " ORDER BY p.name"
            products = [dict(r) for r in conn.execute(sql, params).fetchall()]
        except Exception:
            products = []
        # Group products by entity for the index page
        by_entity: dict[str, list[dict]] = {}
        for p in products:
            by_entity.setdefault(p["entity_slug"] or "—", []).append(p)
        # Supplement entities that have at least one product or could
        supp_entities = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind='supplement' ORDER BY name"
        ).fetchall()]
    return render(request, "products.html", {
        "title": "Supplement product quality",
        "products": products,
        "by_entity": by_entity,
        "entity_filter": entity,
        "all_supplements": supp_entities,
    })


@app.get("/product/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    with connect() as conn:
        try:
            p = conn.execute(
                "SELECT p.*, e.name AS entity_name "
                "FROM product p LEFT JOIN entity e ON e.slug = p.entity_slug "
                "WHERE p.slug = ?", (slug,)).fetchone()
        except Exception:
            p = None
        if not p:
            return HTMLResponse("Product not found — the product quality layer "
                                "is just being scaffolded.", status_code=404)
        # Related evidence on the parent supplement entity
        edges = []
        if p["entity_slug"]:
            edges = [dict(r) for r in conn.execute("""
                SELECT e.id, e.tier, e.direction, e.summary,
                       o.name AS o_name, o.slug AS o_slug
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE f.slug = ?
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 ELSE 4 END LIMIT 12""",
                (p["entity_slug"],)).fetchall()]
    return render(request, "product.html", {
        "title": p["name"], "p": dict(p), "edges": edges,
    })


@app.get("/brief", response_class=HTMLResponse)
def brief_page(request: Request, days: int = 14):
    """Profile-aware daily/weekly briefing."""
    profile = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        brief = _profile_brief(conn, profile, days=days)
    return render(request, "brief.html", {
        "title": "Today's brief",
        "profile": profile,
        "brief": brief,
        "days": days,
    })


@app.get("/compare", response_class=HTMLResponse)
def compare_page(request: Request,
                 outcome: str = "", factors: str = "",
                 factor: str = "", outcomes: str = ""):
    """Decision-aid: compare multiple factors for one outcome,
    or multiple outcomes for one factor."""
    axis = anchor_entity = None
    candidates: list[dict] = []
    missing: list[str] = []

    with connect() as conn:
        all_factors = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind IN "
            "('food','nutrient','supplement','drug','activity','behavior','environmental') "
            "ORDER BY name").fetchall()]
        all_outcomes = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind IN "
            "('condition','process','biomarker') ORDER BY name").fetchall()]

        if outcome and factors:
            slugs = [s.strip() for s in factors.split(",") if s.strip()]
            anchor_entity = conn.execute(
                "SELECT slug, name, kind FROM entity WHERE slug=?", (outcome,)).fetchone()
            if anchor_entity:
                axis = "factor"
                placeholders = ",".join("?" * len(slugs))
                rows = conn.execute(f"""
                    SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                           o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                    FROM edge e
                    JOIN entity f ON f.id = e.factor_id
                    JOIN entity o ON o.id = e.outcome_id
                    WHERE o.slug = ? AND f.slug IN ({placeholders})""",
                    (outcome, *slugs)).fetchall()
                candidates = [_edge_compare_obj(conn, r) for r in rows]
                missing = sorted(set(slugs) - {c["factor"]["slug"] for c in candidates})
        elif factor and outcomes:
            slugs = [s.strip() for s in outcomes.split(",") if s.strip()]
            anchor_entity = conn.execute(
                "SELECT slug, name, kind FROM entity WHERE slug=?", (factor,)).fetchone()
            if anchor_entity:
                axis = "outcome"
                placeholders = ",".join("?" * len(slugs))
                rows = conn.execute(f"""
                    SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                           o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                    FROM edge e
                    JOIN entity f ON f.id = e.factor_id
                    JOIN entity o ON o.id = e.outcome_id
                    WHERE f.slug = ? AND o.slug IN ({placeholders})""",
                    (factor, *slugs)).fetchall()
                candidates = [_edge_compare_obj(conn, r) for r in rows]
                missing = sorted(set(slugs) - {c["outcome"]["slug"] for c in candidates})

    # Rank for "best supported" — lower index = stronger
    def _rank(c):
        tier_score = {"A": 4, "B": 3, "C": 2, "X": 1, "D": 0}.get(c["tier"], 0)
        return -(tier_score * 10 + min(c["n_studies"], 10))
    ranked = sorted(candidates, key=_rank)

    best = ranked[0] if ranked else None
    most_uncertain = next((c for c in candidates if c["tier"] == "X"), None)
    potential_downside = next((c for c in candidates if c["direction"] in ("harmful", "u_shaped")), None)

    return render(request, "compare.html", {
        "title": "Compare evidence",
        "axis": axis,
        "anchor": dict(anchor_entity) if anchor_entity else None,
        "candidates": candidates,
        "ranked": ranked,
        "missing": missing,
        "best": best,
        "most_uncertain": most_uncertain,
        "potential_downside": potential_downside,
        "all_factors": all_factors,
        "all_outcomes": all_outcomes,
        "outcome": outcome, "factors": factors,
        "factor": factor, "outcomes": outcomes,
    })


@app.get("/explore", response_class=HTMLResponse)
def explore(request: Request, focus: str = ""):
    """Interactive graph explorer. Pick a 'focus' entity slug to see its
    1-hop neighborhood as a force-directed graph. No JS framework — uses
    a small embedded SVG renderer with deterministic layout."""
    with connect() as conn:
        all_factors = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind IN "
            "('food','nutrient','supplement','drug','activity','behavior','environmental') "
            "ORDER BY name").fetchall()]
        all_outcomes = [dict(r) for r in conn.execute(
            "SELECT slug, name FROM entity WHERE kind IN "
            "('condition','process','biomarker') ORDER BY name").fetchall()]

        focus_entity = None
        nodes: list[dict] = []
        edges: list[dict] = []
        if focus:
            focus_entity = conn.execute(
                "SELECT * FROM entity WHERE slug=?", (focus,)).fetchone()
            if focus_entity:
                rows = conn.execute("""
                    SELECT e.id, e.tier, e.direction, e.summary,
                           f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                           o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                    FROM edge e
                    JOIN entity f ON f.id = e.factor_id
                    JOIN entity o ON o.id = e.outcome_id
                    WHERE e.factor_id = ? OR e.outcome_id = ?
                    ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                                  WHEN 'C' THEN 3 ELSE 4 END LIMIT 80""",
                    (focus_entity["id"], focus_entity["id"])).fetchall()
                seen = {focus_entity["slug"]: dict(focus_entity)}
                for r in rows:
                    if r["f_slug"] not in seen:
                        seen[r["f_slug"]] = {"slug": r["f_slug"], "name": r["f_name"], "kind": r["f_kind"]}
                    if r["o_slug"] not in seen:
                        seen[r["o_slug"]] = {"slug": r["o_slug"], "name": r["o_name"], "kind": r["o_kind"]}
                    edges.append({
                        "id": r["id"], "from": r["f_slug"], "to": r["o_slug"],
                        "tier": r["tier"], "direction": r["direction"],
                        "summary": r["summary"],
                    })
                nodes = list(seen.values())

    return render(request, "explore.html", {
        "title": "Explore",
        "factors": all_factors,
        "outcomes": all_outcomes,
        "focus": focus, "focus_entity": dict(focus_entity) if focus_entity else None,
        "nodes": nodes, "edges": edges,
    })


@app.get("/api/edges")
def api_edges(tier: str = "", direction: str = "", limit: int = 100):
    """JSON list of edges. Query: ?tier=A&direction=protective&limit=50"""
    sql = """SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
                    e.population, e.updated_at,
                    f.slug AS factor_slug, f.name AS factor_name,
                    o.slug AS outcome_slug, o.name AS outcome_name,
                    (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies
             FROM edge e
             JOIN entity f ON f.id=e.factor_id
             JOIN entity o ON o.id=e.outcome_id WHERE 1=1"""
    params: list = []
    if tier:
        sql += " AND e.tier = ?"; params.append(tier)
    if direction:
        sql += " AND e.direction = ?"; params.append(direction)
    sql += " ORDER BY e.updated_at DESC LIMIT ?"; params.append(min(limit, 500))
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    return {"count": len(rows), "edges": rows}


def _serialize_evidence(rows: list[dict]) -> list[dict]:
    """Canonical citation row shape — the agent-stable contract."""
    out = []
    for r in rows:
        out.append({
            "citation":       r.get("citation"),
            "pmid":           r.get("pmid"),
            "doi":            r.get("doi"),
            "year":           r.get("year"),
            "study_type":     r.get("study_type"),
            "n_participants": r.get("n_participants"),
            "quality":        r.get("quality"),
            "direction":      r.get("direction"),
            "is_retracted":   bool(r.get("is_retracted")),
            "retraction_note": r.get("retraction_note"),
            "notes":          r.get("notes"),
        })
    return out


def _study_mix(rows: list[dict]) -> dict[str, int]:
    mix: dict[str, int] = {}
    for r in rows:
        st = r.get("study_type") or "unspecified"
        mix[st] = mix.get(st, 0) + 1
    return mix


@app.get("/api/edges/{edge_id}")
def api_edge_detail(edge_id: int):
    """Full structured payload for one edge — the canonical agent shape.

    Includes: edge metadata, factor + outcome objects, summary, mechanism,
    caveats, effect, population, supporting evidence rows, counter-evidence
    rows, retraction status, history, and a study-mix summary.
    """
    with connect() as conn:
        e = conn.execute("""
            SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.id = ?""", (edge_id,)).fetchone()
        if not e:
            return Response('{"error":"not found"}', status_code=404,
                            media_type="application/json")
        try:
            evs = conn.execute("""
                SELECT ev.*, COALESCE(s.is_retracted, 0) AS is_retracted,
                       s.retraction_note
                FROM evidence ev
                LEFT JOIN evidence_status s ON s.pmid = ev.pmid
                WHERE ev.edge_id = ?
                ORDER BY ev.year DESC""", (edge_id,)).fetchall()
        except Exception:
            evs = conn.execute(
                "SELECT *, 0 AS is_retracted, NULL AS retraction_note "
                "FROM evidence WHERE edge_id=? ORDER BY year DESC",
                (edge_id,)).fetchall()
        history = conn.execute(
            "SELECT changed_at, field, old_value, new_value, reason, actor "
            "FROM edge_history WHERE edge_id=? ORDER BY changed_at DESC",
            (edge_id,)).fetchall()

    e = dict(e)
    evs = [dict(r) for r in evs]
    supporting = [r for r in evs if not r.get("is_counter")]
    counter = [r for r in evs if r.get("is_counter")]
    retracted = sum(1 for r in evs if r.get("is_retracted"))
    return {
        "id": e["id"],
        "tier": e["tier"],
        "direction": e["direction"],
        "summary": e["summary"],
        "mechanism": e["mechanism"],
        "caveats": e["caveats"],
        "effect_size": e["effect_size"],
        "effect_quant": e["effect_quant"],
        "population": e["population"],
        "seed_source": e["seed_source"],
        "factor": {"slug": e["f_slug"], "name": e["f_name"], "kind": e["f_kind"]},
        "outcome": {"slug": e["o_slug"], "name": e["o_name"], "kind": e["o_kind"]},
        "evidence": _serialize_evidence(supporting),
        "counter_evidence": _serialize_evidence(counter),
        "retraction": {
            "any": retracted > 0,
            "count": retracted,
        },
        "study_mix": _study_mix(evs),
        "n_studies": len(supporting),
        "n_counter": len(counter),
        "last_reviewed": e["last_reviewed"],
        "updated_at": e["updated_at"],
        "history": [dict(r) for r in history],
        "share_card": f"/edge/{edge_id}.png",
        "html_url": f"/edge/{edge_id}",
    }


def _edge_compare_obj(conn, edge_row: dict) -> dict:
    """Compact comparable object used by /api/compare."""
    e = dict(edge_row)
    evs = conn.execute(
        "SELECT study_type, quality, direction, n_participants, "
        "       COALESCE((SELECT 1 FROM evidence_status s WHERE s.pmid=ev.pmid AND s.is_retracted=1), 0) AS is_retracted "
        "FROM evidence ev WHERE edge_id=?", (e["id"],)).fetchall()
    evs = [dict(r) for r in evs]
    total_n = sum(r.get("n_participants") or 0 for r in evs)
    return {
        "id": e["id"],
        "tier": e["tier"],
        "direction": e["direction"],
        "summary": e["summary"],
        "effect_size": e["effect_size"],
        "effect_quant": e["effect_quant"],
        "population": e["population"],
        "factor": {"slug": e["f_slug"], "name": e["f_name"]},
        "outcome": {"slug": e["o_slug"], "name": e["o_name"]},
        "n_studies": len(evs),
        "study_mix": _study_mix(evs),
        "total_participants": total_n,
        "any_retracted": any(r.get("is_retracted") for r in evs),
        "html_url": f"/edge/{e['id']}",
    }


@app.get("/api/compare")
def api_compare(outcome: str = "", factors: str = "",
                factor: str = "", outcomes: str = ""):
    """Compare multiple factors for one outcome, or multiple outcomes for
    one factor. Returns a normalized list ready for ranking and narration.

    Examples:
      /api/compare?outcome=sleep_quality&factors=magnesium,melatonin
      /api/compare?factor=magnesium&outcomes=sleep_quality,anxiety
    """
    if outcome and factors:
        slugs = [s.strip() for s in factors.split(",") if s.strip()]
        with connect() as conn:
            o = conn.execute("SELECT id, slug, name FROM entity WHERE slug=?",
                             (outcome,)).fetchone()
            if not o:
                return Response('{"error":"unknown outcome"}', status_code=404,
                                media_type="application/json")
            placeholders = ",".join("?" * len(slugs))
            rows = conn.execute(f"""
                SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE o.slug = ? AND f.slug IN ({placeholders})""",
                (outcome, *slugs)).fetchall()
            results = [_edge_compare_obj(conn, r) for r in rows]
            missing = sorted(set(slugs) - {r["factor"]["slug"] for r in results})
        return {"axis": "factor",
                "anchor": {"slug": o["slug"], "name": o["name"]},
                "candidates": results, "missing": missing}

    if factor and outcomes:
        slugs = [s.strip() for s in outcomes.split(",") if s.strip()]
        with connect() as conn:
            f = conn.execute("SELECT id, slug, name FROM entity WHERE slug=?",
                             (factor,)).fetchone()
            if not f:
                return Response('{"error":"unknown factor"}', status_code=404,
                                media_type="application/json")
            placeholders = ",".join("?" * len(slugs))
            rows = conn.execute(f"""
                SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE f.slug = ? AND o.slug IN ({placeholders})""",
                (factor, *slugs)).fetchall()
            results = [_edge_compare_obj(conn, r) for r in rows]
            missing = sorted(set(slugs) - {r["outcome"]["slug"] for r in results})
        return {"axis": "outcome",
                "anchor": {"slug": f["slug"], "name": f["name"]},
                "candidates": results, "missing": missing}

    return Response(
        '{"error":"need either outcome+factors or factor+outcomes query params"}',
        status_code=400, media_type="application/json")


@app.get("/api/changes")
def api_changes(since: str = "", days: int = 14, tier: str = "",
                direction: str = "", factor: str = "", outcome: str = "",
                limit: int = 200):
    """Recent edge-history changes. Used by agents and watchlists."""
    sql = """SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason, h.actor,
                    e.id AS edge_id, e.tier, e.direction,
                    f.slug AS f_slug, f.name AS f_name,
                    o.slug AS o_slug, o.name AS o_name
             FROM edge_history h
             JOIN edge e ON e.id = h.edge_id
             JOIN entity f ON f.id = e.factor_id
             JOIN entity o ON o.id = e.outcome_id
             WHERE 1=1 """
    params: list = []
    if since:
        sql += " AND h.changed_at >= ?"; params.append(since)
    elif days:
        sql += " AND h.changed_at >= datetime('now', ?)"; params.append(f"-{int(days)} days")
    if tier:
        sql += " AND e.tier = ?"; params.append(tier)
    if direction:
        sql += " AND e.direction = ?"; params.append(direction)
    if factor:
        sql += " AND f.slug = ?"; params.append(factor)
    if outcome:
        sql += " AND o.slug = ?"; params.append(outcome)
    sql += " ORDER BY h.changed_at DESC LIMIT ?"; params.append(min(limit, 1000))

    with connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    out = []
    for r in rows:
        is_promote = (r["field"] == "tier" and r.get("new_value") in ("A", "B")
                      and r.get("old_value") not in ("A", "B"))
        is_demote  = (r["field"] == "tier" and r.get("old_value") in ("A", "B")
                      and r.get("new_value") not in ("A", "B"))
        out.append({
            "changed_at": r["changed_at"],
            "edge_id": r["edge_id"],
            "edge_url": f"/edge/{r['edge_id']}",
            "edge_api_url": f"/api/edges/{r['edge_id']}",
            "field": r["field"],
            "old_value": r["old_value"],
            "new_value": r["new_value"],
            "reason": r["reason"],
            "actor": r["actor"],
            "is_promotion": is_promote,
            "is_demotion": is_demote,
            "factor": {"slug": r["f_slug"], "name": r["f_name"]},
            "outcome": {"slug": r["o_slug"], "name": r["o_name"]},
            "current_tier": r["tier"],
            "current_direction": r["direction"],
        })
    return {"count": len(out), "changes": out}


def _no_regret_movers(conn, profile: Profile, limit: int = 8) -> list[dict]:
    """Tier-A protective edges, broad applicability, low controversy.
    Used by /api/profile-brief and the /me + /risk + /brief surfaces."""
    rows = conn.execute("""
        SELECT e.id, e.tier, e.direction, e.summary, e.effect_size,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE e.tier = 'A' AND e.direction = 'protective'
          AND (e.population IS NULL OR e.population LIKE '%general%' OR e.population = '')
          AND NOT EXISTS (SELECT 1 FROM evidence ev2
                          JOIN evidence_status s ON s.pmid = ev2.pmid
                          WHERE ev2.edge_id = e.id AND s.is_retracted = 1)
        ORDER BY (SELECT COUNT(*) FROM evidence WHERE edge_id=e.id) DESC
        LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def _red_flags_in_stack(conn, profile: Profile, limit: int = 12) -> list[dict]:
    """Harmful or contested edges where the user's stack is the factor."""
    if not profile.stack:
        return []
    placeholders = ",".join("?" * len(profile.stack))
    rows = conn.execute(f"""
        SELECT e.id, e.tier, e.direction, e.summary,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE f.slug IN ({placeholders})
          AND (e.direction IN ('harmful','u_shaped','mixed') OR e.tier = 'X')
        ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'X' THEN 3 ELSE 4 END,
                 CASE e.direction WHEN 'harmful' THEN 1 WHEN 'u_shaped' THEN 2 WHEN 'mixed' THEN 3 ELSE 4 END
        LIMIT ?""", (*profile.stack, limit)).fetchall()
    return [dict(r) for r in rows]


def _profile_brief(conn, profile: Profile, days: int = 14) -> dict:
    """The shared logic powering /api/profile-brief, /brief, /me, and /risk."""
    rel_query_parts = []
    rel_params = []
    if profile.stack:
        rel_query_parts.append(f"f.slug IN ({','.join('?' * len(profile.stack))})")
        rel_params.extend(profile.stack)
    if profile.conditions:
        rel_query_parts.append(f"o.slug IN ({','.join('?' * len(profile.conditions))})")
        rel_params.extend(profile.conditions)
    relevant = []
    if rel_query_parts:
        rel_sql = (
            "SELECT e.id, e.tier, e.direction, e.summary, e.effect_size, "
            "       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind, "
            "       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind "
            "FROM edge e "
            "JOIN entity f ON f.id = e.factor_id "
            "JOIN entity o ON o.id = e.outcome_id "
            "WHERE (" + " OR ".join(rel_query_parts) + ") "
            "ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END "
            "LIMIT 50"
        )
        rows = [dict(r) for r in conn.execute(rel_sql, rel_params).fetchall()]
        rows.sort(key=lambda e: -relevance_score(e, profile))
        relevant = rows[:12]

    red_flags = _red_flags_in_stack(conn, profile, limit=8)
    no_regret = _no_regret_movers(conn, profile, limit=8)

    # What's changed in tracked areas (last `days`)
    where = ""
    params: list = []
    if profile.conditions or profile.stack:
        clauses = []
        if profile.stack:
            clauses.append(f"f.slug IN ({','.join('?' * len(profile.stack))})")
            params.extend(profile.stack)
        if profile.conditions:
            clauses.append(f"o.slug IN ({','.join('?' * len(profile.conditions))})")
            params.extend(profile.conditions)
        where = "AND (" + " OR ".join(clauses) + ")"
    changes_sql = (
        "SELECT h.changed_at, h.field, h.old_value, h.new_value, h.actor, "
        "       e.id AS edge_id, e.tier, "
        "       f.slug AS f_slug, f.name AS f_name, "
        "       o.slug AS o_slug, o.name AS o_name "
        "FROM edge_history h "
        "JOIN edge e ON e.id = h.edge_id "
        "JOIN entity f ON f.id = e.factor_id "
        "JOIN entity o ON o.id = e.outcome_id "
        "WHERE h.changed_at >= datetime('now', ?) "
        + where +
        " ORDER BY h.changed_at DESC LIMIT 12"
    )
    recent_changes = [dict(r) for r in conn.execute(
        changes_sql, (f"-{days} days", *params)).fetchall()]

    featured = relevant[0] if relevant else None

    return {
        "has_profile": bool(profile.conditions or profile.stack or profile.age),
        "tracked": {
            "conditions": profile.conditions,
            "stack": profile.stack,
        },
        "relevant": relevant,
        "red_flags": red_flags,
        "no_regret": no_regret,
        "recent_changes": recent_changes,
        "featured": featured,
    }


@app.get("/api/profile-brief")
def api_profile_brief(request: Request, days: int = 14):
    """Profile-aware briefing for an agent or the /brief page.

    Reads the saved profile cookie. Returns relevant edges, red flags,
    no-regret moves, recent changes in tracked areas, and a featured edge.
    """
    profile = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        return _profile_brief(conn, profile, days=days)


@app.get("/api/entities/{slug}")
def api_entity(slug: str):
    with connect() as conn:
        e = conn.execute("SELECT * FROM entity WHERE slug=?", (slug,)).fetchone()
        if not e:
            return Response('{"error":"not found"}', status_code=404,
                            media_type="application/json")
        out_edges = [dict(r) for r in conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, o.slug AS outcome_slug, o.name AS outcome_name
            FROM edge e JOIN entity o ON o.id=e.outcome_id WHERE e.factor_id=?""",
            (e["id"],)).fetchall()]
        in_edges = [dict(r) for r in conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, f.slug AS factor_slug, f.name AS factor_name
            FROM edge e JOIN entity f ON f.id=e.factor_id WHERE e.outcome_id=?""",
            (e["id"],)).fetchall()]
    out = dict(e); out.pop("embedding", None); out.pop("embedded_at", None)
    return {"entity": out, "as_factor": out_edges, "as_outcome": in_edges}


@app.get("/edge/{edge_id}.png")
def edge_png(edge_id: int):
    from web.share import render_edge_png
    with connect() as conn:
        e = conn.execute("""
            SELECT e.*, f.name AS f_name, o.name AS o_name
            FROM edge e JOIN entity f ON f.id=e.factor_id
            JOIN entity o ON o.id=e.outcome_id WHERE e.id=?""",
            (edge_id,)).fetchone()
    if not e:
        return Response("Not found", status_code=404)
    png = render_edge_png(dict(e))
    return Response(png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


# ---- audit-trail classification (per-edge + global) ----------------------

# User-facing labels for internal agent codes. Anything not here passes
# through verbatim so we don't accidentally hide unknown sources.
_AGENT_LABELS = {
    "manual":         "Hand-reviewed by maintainer",
    "claude_seed":    "Initial deep research (Claude)",
    "codex_payload":  "Curated literature batch",
    "codex_densify":  "Literature scan",
    "gemma_rewrite":  "Prose refresh",
    "gemma_daily":    "Daily literature sweep",
    "daily_ingest":   "Daily literature sweep",
    "pmid_watcher":   "Retraction watch",
}

# Categories drive colour and grouping. Order matters — first match wins.
_EVENT_CATEGORIES = (
    ("tier_promotion",  "🟢", "Promoted"),
    ("tier_demotion",   "🔴", "Demoted"),
    ("retraction",      "🔴", "Retraction"),
    ("evidence_added",  "🟡", "Evidence"),
    ("scan_noop",       "⚪", "Scan"),
    ("prose",           "⚪", "Prose"),
    ("import",          "⚪", "Import"),
    ("other",           "⚪", "Update"),
)
_TIER_RANK = {"A": 5, "B": 4, "C": 3, "X": 2, "D": 1, "deprecated": 0}


def _classify_event(row: dict) -> dict:
    """Translate a raw edge_history row into a user-facing event dict.

    Returns: {category, headline, detail, agent_label, is_meaningful, raw}
    `is_meaningful` separates headline events from maintenance noise so
    the UI can collapse routine ingest passes by default.
    """
    field = (row.get("field") or "").lower()
    old_v = row.get("old_value") or ""
    new_v = row.get("new_value") or ""
    reason = row.get("reason") or ""
    actor = row.get("actor") or row.get("agent") or ""
    agent_label = _AGENT_LABELS.get(actor, actor.replace("_", " "))

    cat = "other"
    headline = ""
    detail = reason

    if field == "tier" and old_v and new_v:
        if _TIER_RANK.get(new_v, 0) > _TIER_RANK.get(old_v, 0):
            cat = "tier_promotion"
            headline = f"Promoted to tier {new_v}"
            detail = reason or f"Was tier {old_v}; now tier {new_v}."
        else:
            cat = "tier_demotion"
            headline = f"Demoted to tier {new_v}"
            detail = reason or f"Was tier {old_v}; now tier {new_v}."
    elif field == "tier" and new_v:                # initial set
        cat = "import"
        headline = f"Tier set to {new_v}"
        detail = reason or "Initial review."
    elif field == "direction" and old_v != new_v and old_v and new_v:
        cat = "tier_demotion" if new_v == "harmful" else "other"
        headline = f"Direction changed: {old_v} → {new_v}"
        detail = reason or ""
    elif field == "retraction" or "retract" in (reason or "").lower():
        cat = "retraction"
        headline = "Retraction warning"
        detail = reason or "Cited paper was retracted."
    # Densify / payload-import operations come in through `field=ingest`
    # or with `payload` in reason. We want to summarise rather than
    # show raw filenames + "+0 row(s)".
    elif "densify" in (reason or "").lower():
        n = 0
        import re as _re
        m = _re.search(r"\+(\d+)\s+evidence\s+row", reason)
        if m:
            try:    n = int(m.group(1))
            except: n = 0
        if n == 0:
            cat = "scan_noop"
            headline = "Literature scan complete"
            detail = "No new papers found in this pass."
        else:
            cat = "evidence_added"
            headline = f"+{n} stud{'y' if n == 1 else 'ies'} added"
            detail = "From a curated literature batch."
    elif "payload import" in (reason or "").lower():
        cat = "import"
        headline = "Curated batch imported"
        # Strip the file path from the reason; users don't need it.
        detail = "Verified PMIDs added to the corpus."
    elif "rewrite" in (reason or "").lower() or "gemma" in actor:
        cat = "prose"
        headline = "Prose refreshed"
        detail = "Summary, mechanism, or caveats text re-rendered. Underlying tier and evidence unchanged."
    elif field == "summary" or field == "mechanism" or field == "caveats":
        cat = "prose"
        headline = f"{field.capitalize()} updated"
        detail = reason or "Editorial polish only."

    if not headline:
        headline = (reason or field or "Update").capitalize()
        cat = "other"

    is_meaningful = cat in {"tier_promotion", "tier_demotion", "retraction",
                            "evidence_added"}
    return {
        "category": cat,
        "headline": headline,
        "detail": detail,
        "agent": actor,
        "agent_label": agent_label,
        "changed_at": row.get("changed_at") or "",
        "old_value": old_v,
        "new_value": new_v,
        "is_meaningful": is_meaningful,
        "raw": row,
    }


def _audit_summary(history_rows: list[dict], evidence_rows: list[dict],
                   last_reviewed: str | None) -> dict:
    """Compute the status banner + 90-day aggregate counts."""
    from datetime import datetime as _dt, timedelta as _td
    today = datetime_now()
    cutoff = today - _td(days=90)
    n_tier_changes = 0
    n_new_studies = 0
    n_prose = 0
    n_retractions = 0
    last_tier_change = None
    last_new_study = None
    for row in history_rows:
        when = (row.get("changed_at") or "")[:10]
        if not when:
            continue
        try:
            d = _dt.strptime(when, "%Y-%m-%d")
        except Exception:
            continue
        ev = _classify_event(row)
        if d >= cutoff:
            if ev["category"] in ("tier_promotion", "tier_demotion"):
                n_tier_changes += 1
            if ev["category"] == "evidence_added":
                n_new_studies += 1
            if ev["category"] == "prose":
                n_prose += 1
            if ev["category"] == "retraction":
                n_retractions += 1
        if ev["category"] in ("tier_promotion", "tier_demotion") and not last_tier_change:
            last_tier_change = d
        if ev["category"] == "evidence_added" and not last_new_study:
            last_new_study = d
    days_stable = (today - last_tier_change).days if last_tier_change else None
    days_since_study = (today - last_new_study).days if last_new_study else None
    days_since_review = None
    if last_reviewed:
        try:
            days_since_review = (today - _dt.strptime(last_reviewed[:10], "%Y-%m-%d")).days
        except Exception:
            pass
    return {
        "n_tier_changes_90d": n_tier_changes,
        "n_new_studies_90d": n_new_studies,
        "n_prose_90d": n_prose,
        "n_retractions_90d": n_retractions,
        "days_stable": days_stable,
        "days_since_study": days_since_study,
        "days_since_review": days_since_review,
        "n_studies": len(evidence_rows),
    }


@app.get("/edge/{edge_id}", response_class=HTMLResponse)
def edge_detail(request: Request, edge_id: int):
    profile = decode(request.cookies.get(COOKIE))
    with connect() as conn:
        e = conn.execute("""
            SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.id = ?""", (edge_id,)).fetchone()
        if not e:
            return HTMLResponse("Not found", status_code=404)
        # LEFT JOIN evidence_status so retracted PMIDs show a red pill.
        # Table may not exist on a fresh DB — guard with try/except.
        try:
            evidence = conn.execute("""
                SELECT ev.*, COALESCE(s.is_retracted, 0) AS is_retracted,
                       s.retraction_note
                FROM evidence ev
                LEFT JOIN evidence_status s ON s.pmid = ev.pmid
                WHERE ev.edge_id=? AND COALESCE(ev.is_counter,0)=0
                ORDER BY ev.year DESC""", (edge_id,)).fetchall()
            counter = conn.execute("""
                SELECT ev.*, COALESCE(s.is_retracted, 0) AS is_retracted,
                       s.retraction_note
                FROM evidence ev
                LEFT JOIN evidence_status s ON s.pmid = ev.pmid
                WHERE ev.edge_id=? AND COALESCE(ev.is_counter,0)=1
                ORDER BY ev.year DESC""", (edge_id,)).fetchall()
        except Exception:
            evidence = conn.execute(
                "SELECT *, 0 AS is_retracted, NULL AS retraction_note "
                "FROM evidence WHERE edge_id=? AND COALESCE(is_counter,0)=0 "
                "ORDER BY year DESC", (edge_id,)).fetchall()
            counter = conn.execute(
                "SELECT *, 0 AS is_retracted, NULL AS retraction_note "
                "FROM evidence WHERE edge_id=? AND COALESCE(is_counter,0)=1 "
                "ORDER BY year DESC", (edge_id,)).fetchall()
        history = conn.execute(
            "SELECT * FROM edge_history WHERE edge_id = ? ORDER BY changed_at DESC",
            (edge_id,)).fetchall()
    ev_rows = [dict(r) for r in evidence]
    co_rows = [dict(r) for r in counter]
    retracted_count = sum(1 for r in ev_rows + co_rows if r.get("is_retracted"))
    raw_history = [dict(r) for r in history]
    classified = [_classify_event(r) for r in raw_history]
    audit_summary = _audit_summary(raw_history, ev_rows, dict(e).get("last_reviewed"))
    return render(request, "edge.html", {
        "e": dict(e),
        "evidence": ev_rows,
        "counter": co_rows,
        "history": raw_history,
        "audit_events": classified,
        "audit_headlines": [c for c in classified if c["is_meaningful"]],
        "audit_maintenance": [c for c in classified if not c["is_meaningful"]],
        "audit_summary": audit_summary,
        "retracted_evidence_count": retracted_count,
        "profile": profile,
    })


_LIB_SORTS = {
    "importance": "Most important",
    "latest": "Most recent",
    "studies": "Most studied",
    "az": "A → Z",
}


def _library_view(conn, where_sql: str, params: tuple, *,
                  tier: str = "", direction: str = "",
                  q: str = "", outcome: str = "",
                  sort: str = "importance", group: str = "",
                  page: int = 1):
    """Pull matching edges, compute facets, filter/sort/group/paginate.
    Returns a dict ready for the library template."""
    sql = f"""
        SELECT e.id, e.tier, e.direction, e.summary, e.updated_at, e.created_at,
               e.effect_size,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind,
               (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
               (SELECT study_type FROM evidence ev WHERE ev.edge_id=e.id
                ORDER BY CASE study_type WHEN 'meta_analysis' THEN 1
                  WHEN 'systematic_review' THEN 2 WHEN 'rct' THEN 3
                  WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 1) AS top_study,
               (SELECT MAX(changed_at) FROM edge_history h
                WHERE h.edge_id=e.id AND h.field='tier'
                  AND h.new_value IN ('A','B')
                  AND (h.old_value IS NULL OR h.old_value NOT IN ('A','B'))
               ) AS promoted_at
        FROM edge e
        JOIN entity f ON f.id=e.factor_id
        JOIN entity o ON o.id=e.outcome_id
        WHERE {where_sql}
    """
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    for e in rows:
        e["score"] = _importance_score(e)
        e["breakthrough"] = _is_breakthrough(e)
    # Facets — counts on the unfiltered set so the user always sees what's available
    tier_counts: dict[str, int] = {}
    dir_counts: dict[str, int] = {}
    outcome_counts: dict[str, dict] = {}
    for e in rows:
        tier_counts[e["tier"]] = tier_counts.get(e["tier"], 0) + 1
        dir_counts[e["direction"]] = dir_counts.get(e["direction"], 0) + 1
        oslug = e["o_slug"]
        if oslug not in outcome_counts:
            outcome_counts[oslug] = {"slug": oslug, "name": e["o_name"], "count": 0}
        outcome_counts[oslug]["count"] += 1
    # Apply filters
    tier_set = {t for t in (tier or "").split(",") if t}
    dir_set = {d for d in (direction or "").split(",") if d}
    ql = (q or "").lower().strip()
    filtered = rows
    if tier_set:
        filtered = [e for e in filtered if e["tier"] in tier_set]
    if dir_set:
        filtered = [e for e in filtered if e["direction"] in dir_set]
    if outcome:
        filtered = [e for e in filtered if e["o_slug"] == outcome]
    if ql:
        filtered = [e for e in filtered if ql in (e["f_name"] or "").lower()
                    or ql in (e["o_name"] or "").lower()
                    or ql in (e["summary"] or "").lower()]
    # Sort
    if sort == "latest":
        filtered.sort(key=lambda e: e["updated_at"] or "", reverse=True)
    elif sort == "studies":
        filtered.sort(key=lambda e: -(e["n_studies"] or 0))
    elif sort == "az":
        filtered.sort(key=lambda e: (e["f_name"] or "").lower())
    else:                                              # importance (default)
        filtered.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
    total = len(filtered)
    # Group by outcome (skip pagination when grouped)
    groups = None
    if group == "outcome":
        bucket: dict[str, dict] = {}
        for e in filtered:
            key = e["o_slug"]
            if key not in bucket:
                bucket[key] = {"slug": key, "name": e["o_name"], "edges": []}
            bucket[key]["edges"].append(e)
        groups = sorted(bucket.values(), key=lambda g: -len(g["edges"]))
        page_edges: list[dict] = []
        pg = {"page": 1, "pages": 1, "total": total,
              "has_prev": False, "has_next": False, "offset": 0}
    else:
        pg = _paginate(total, page)
        page_edges = filtered[pg["offset"]: pg["offset"] + PAGE_SIZE]
    # Sorted outcome list (for the "jump to" rail)
    outcomes_sorted = sorted(outcome_counts.values(), key=lambda o: -o["count"])
    return {
        "rows": page_edges,
        "groups": groups,
        "pg": pg,
        "tier_counts": tier_counts,
        "dir_counts": dir_counts,
        "outcomes": outcomes_sorted,
        "filters": {"tier": tier, "direction": direction, "q": q,
                    "outcome": outcome, "sort": sort, "group": group},
        "sort_options": _LIB_SORTS,
    }


@app.get("/tier/{tier}", response_class=HTMLResponse)
def by_tier(request: Request, tier: str, page: int = 1,
            direction: str = "", q: str = "", outcome: str = "",
            sort: str = "importance", group: str = ""):
    with connect() as conn:
        ctx = _library_view(conn, "e.tier = ?", (tier,),
                            direction=direction, q=q, outcome=outcome,
                            sort=sort, group=group, page=page)
    ctx.update({
        "title": TIER_LABEL.get(tier, tier),
        "subtitle": f"{ctx['pg']['total']} relationship{'s' if ctx['pg']['total'] != 1 else ''} at this confidence tier",
        "base_path": f"/tier/{tier}",
        "tier_locked": tier,
    })
    return render(request, "library.html", ctx)


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    """Hybrid search with intent detection: substring + semantic cosine,
    plus routing hints based on the natural-language intent of the query."""
    q = q.strip()
    edges: list[dict] = []
    entities: list[dict] = []
    semantic_added = 0
    if q:
        # Try semantic search first; fall back to substring-only if Ollama unreachable
        try:
            from embeddings import embed, unpack, cosine
            qvec = embed(q)
        except Exception:
            qvec = None
        like = f"%{q}%"
        prefix = f"{q}%"
        with connect() as conn:
            entities = [dict(r) for r in conn.execute("""
                SELECT slug, name, kind,
                       CASE
                         WHEN LOWER(name) LIKE LOWER(?) THEN 1
                         WHEN LOWER(name) LIKE LOWER(?) THEN 2
                         WHEN LOWER(COALESCE(aliases,'')) LIKE LOWER(?) THEN 3
                         ELSE 4
                       END AS rel
                FROM entity
                WHERE LOWER(name) LIKE LOWER(?)
                   OR LOWER(COALESCE(aliases,'')) LIKE LOWER(?)
                ORDER BY rel, name LIMIT 30""",
                (prefix, like, like, like, like)).fetchall()]
            edges = [dict(r) for r in conn.execute("""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind,
                       CASE
                         WHEN LOWER(f.name) LIKE LOWER(?) OR LOWER(o.name) LIKE LOWER(?) THEN 1
                         WHEN LOWER(e.summary) LIKE LOWER(?) THEN 2
                         WHEN LOWER(e.mechanism) LIKE LOWER(?) THEN 3
                         ELSE 4
                       END AS rel
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE LOWER(f.name) LIKE LOWER(?) OR LOWER(o.name) LIKE LOWER(?)
                   OR LOWER(e.summary) LIKE LOWER(?) OR LOWER(e.mechanism) LIKE LOWER(?)
                ORDER BY rel,
                         CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                                     WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END
                LIMIT 60""",
                (like, like, like, like, like, like, like, like)).fetchall()]

            # Semantic merge: if we have a query embedding, fetch all
            # edges with embeddings, score by cosine, and merge top-N
            # into the result list (deduped by id).
            if qvec:
                seen_ids = {e["id"] for e in edges}
                cand = conn.execute(
                    "SELECT e.id, e.tier, e.direction, e.summary, e.updated_at, "
                    "       e.embedding, "
                    "       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind, "
                    "       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind "
                    "FROM edge e JOIN entity f ON f.id=e.factor_id "
                    "JOIN entity o ON o.id=e.outcome_id "
                    "WHERE e.embedding IS NOT NULL").fetchall()
                scored: list[tuple[float, dict]] = []
                for r in cand:
                    if r["id"] in seen_ids:
                        continue
                    sim = cosine(qvec, unpack(r["embedding"]))
                    if sim >= 0.55:           # threshold; tuneable
                        d = {k: r[k] for k in r.keys() if k != "embedding"}
                        d["semantic_score"] = round(sim, 3)
                        scored.append((sim, d))
                scored.sort(key=lambda x: -x[0])
                for _, d in scored[:30]:
                    edges.append(d)
                    semantic_added += 1
    intent = _classify_query(q) if q else None
    # Resolve "prevent X" / "helps with X" / "harms X" to a real outcome slug.
    prevent_suggestion = None
    if intent and intent.get("target"):
        tg = intent["target"].lower().strip()
        with connect() as conn:
            outcomes = [dict(r) for r in conn.execute(
                "SELECT slug, name FROM entity WHERE kind IN "
                "('condition','outcome','marker')").fetchall()]
        match = (next((o for o in outcomes if o["slug"] == tg), None)
                 or next((o for o in outcomes if o["name"].lower() == tg), None)
                 or next((o for o in outcomes if tg in o["name"].lower()), None))
        if match and intent["intent"] in ("prevent", "helps_with", "harms", "best_evidence"):
            prevent_suggestion = match
    return render(request, "search.html", {
        "title": f"Search: {q}" if q else "Search",
        "q": q, "edges": edges, "entities": entities,
        "semantic_added": semantic_added,
        "intent": intent,
        "prevent_suggestion": prevent_suggestion,
    })


@app.get("/myths", response_class=HTMLResponse)
def myths(request: Request):
    """Deprecated edges — past beliefs the evidence has overturned."""
    with connect() as conn:
        rows = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.caveats, e.updated_at,
                   f.name AS f_name, o.name AS o_name,
                   (SELECT reason FROM edge_history h WHERE h.edge_id=e.id
                    AND h.field='tier' ORDER BY h.changed_at DESC LIMIT 1) AS reason
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.tier IN ('deprecated','X')
            ORDER BY e.updated_at DESC""").fetchall()
    return render(request, "myths.html", {
        "title": "Myths and contested claims",
        "rows": [dict(r) for r in rows],
    })


@app.get("/changes", response_class=HTMLResponse)
def changes(request: Request, days: int = 14, personal: int = 0):
    """Recent edge changes. personal=1 filters to the user's watchlists +
    tracked stack and conditions."""
    p = decode(request.cookies.get(COOKIE))
    has_watch = bool(p.watch_factors or p.watch_outcomes or p.watch_edges
                     or p.stack or p.conditions)
    sql = """
        SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason, h.actor,
               e.id AS edge_id, e.tier, e.direction,
               f.slug AS f_slug, f.name AS f_name,
               o.slug AS o_slug, o.name AS o_name
        FROM edge_history h
        JOIN edge e ON e.id = h.edge_id
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE h.changed_at >= datetime('now', ?)"""
    params: list = [f"-{int(days)} days"]
    if personal and has_watch:
        watched_factors = list(set(p.watch_factors + p.stack))
        watched_outcomes = list(set(p.watch_outcomes + p.conditions))
        clauses = []
        if watched_factors:
            clauses.append(f"f.slug IN ({','.join('?'*len(watched_factors))})")
            params.extend(watched_factors)
        if watched_outcomes:
            clauses.append(f"o.slug IN ({','.join('?'*len(watched_outcomes))})")
            params.extend(watched_outcomes)
        if p.watch_edges:
            clauses.append(f"e.id IN ({','.join('?'*len(p.watch_edges))})")
            params.extend(p.watch_edges)
        if clauses:
            sql += " AND (" + " OR ".join(clauses) + ")"
    sql += " ORDER BY h.changed_at DESC LIMIT 200"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return render(request, "changes.html", {
        "title": "What changed",
        "rows": [dict(r) for r in rows],
        "days": days,
        "personal": bool(personal),
        "has_watch": has_watch,
        "watch_count": len(p.watch_factors) + len(p.watch_outcomes) + len(p.watch_edges) + len(p.stack) + len(p.conditions),
        "profile": p,
    })


@app.get("/category/{slug}", response_class=HTMLResponse)
def category(request: Request, slug: str, page: int = 1,
             tier: str = "", direction: str = "", q: str = "",
             outcome: str = "", sort: str = "importance", group: str = ""):
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return HTMLResponse("Not found", status_code=404)
    if "kinds" in cat:
        ph = ",".join("?" * len(cat["kinds"]))
        where = f"f.kind IN ({ph})"
        params = tuple(cat["kinds"])
    else:
        ph = ",".join("?" * len(cat["outcomes"]))
        where = f"o.slug IN ({ph})"
        params = tuple(cat["outcomes"])
    with connect() as conn:
        ctx = _library_view(conn, where, params,
                            tier=tier, direction=direction, q=q, outcome=outcome,
                            sort=sort, group=group, page=page)
    ctx.update({
        "title": cat["label"],
        "subtitle": f"{ctx['pg']['total']} relationship{'s' if ctx['pg']['total'] != 1 else ''} in this category",
        "base_path": f"/category/{slug}",
    })
    return render(request, "library.html", ctx)
