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
from web.illustrations import (   # noqa: E402
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
    return render(request, "home.html", {
        "stats": stats, "categories": cats,
        "featured": featured, "buckets": buckets, "spotlight": spotlight,
        "profile": p, "discoveries": discoveries,
    })


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


@app.get("/my-plan", response_class=HTMLResponse)
def my_plan(request: Request):
    """Aggregate /prevent across every condition the user is tracking.
    Dedupe protective and harmful factors across conditions, count overlap
    so the highest-leverage moves bubble up."""
    p = decode(request.cookies.get(COOKIE))
    targets = list(p.conditions or [])
    do_map: dict[str, dict] = {}
    avoid_map: dict[str, dict] = {}
    matched_outcomes: list[dict] = []
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
        # Aggregate by factor: factor that helps THREE conditions ranks higher.
        for e in do_rows + harm_rows + ushape_rows + mixed_rows:
            e["score"] = _importance_score(e)
            e["breakthrough"] = _is_breakthrough(e)
        def _agg(rows: list[dict]) -> dict[str, dict]:
            out: dict[str, dict] = {}
            for e in rows:
                k = e["f_slug"]
                if k not in out:
                    out[k] = {**e, "for_conditions": [],
                              "for_condition_names": [], "n_overlap": 0,
                              "best_score": e["score"]}
                rec = out[k]
                if e["o_slug"] not in rec["for_conditions"]:
                    rec["for_conditions"].append(e["o_slug"])
                    rec["for_condition_names"].append(e["o_name"])
                rec["n_overlap"] = len(rec["for_conditions"])
                if e["score"] > rec["best_score"]:
                    rec["best_score"] = e["score"]
                    rec["tier"] = e["tier"]
                    rec["effect_size"] = e["effect_size"]
                    rec["effect_quant"] = e["effect_quant"]
                    rec["id"] = e["id"]
                    rec["summary"] = e["summary"]
            return out
        do_map = _agg(do_rows)
        hard_map = _agg(harm_rows)
        cau_map = _agg(ushape_rows + mixed_rows)
        # Sort: overlap desc, then importance score desc.
        def _sortkey(e: dict):
            return (-(e["n_overlap"]), -(1 if e["breakthrough"] else 0), -e["best_score"])
        do_list = sorted(do_map.values(), key=_sortkey)
        hard_list = sorted(hard_map.values(), key=_sortkey)
        caution_list = sorted(cau_map.values(), key=_sortkey)
    else:
        do_list = hard_list = caution_list = []
    return render(request, "my_plan.html", {
        "title": "My plan",
        "profile": p,
        "matched_outcomes": matched_outcomes,
        "do_rows": do_list[:24],
        "hard_rows": hard_list[:18],
        "caution_rows": caution_list[:12],
        "warnings": _interactions_for_stack(p.stack),
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
def discoveries(request: Request, days: int = 30, page: int = 1):
    with connect() as conn:
        all_rows = _new_discoveries(conn, days=days, limit=200)
        # Split into "promoted into A/B" vs "newly created at C+"
        promoted = [r for r in all_rows if r.get("promoted_at")]
        newly_created = [r for r in all_rows if not r.get("promoted_at")]
        # Total over the last 7 days for a "this week" headline
        week_count = sum(1 for r in all_rows if
            (r.get("promoted_at") or r.get("updated_at"))[:10] >=
            (datetime_now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        # Suppress the "this past week" stat when it equals the total —
        # that just means everything in the window is freshly seeded.
        if week_count and week_count == len(all_rows):
            week_count = 0
    pg = _paginate(len(all_rows), page)
    rows = all_rows[pg["offset"]: pg["offset"] + PAGE_SIZE]
    return render(request, "discoveries.html", {
        "title": "Discoveries", "rows": rows, "days": days,
        "pg": pg, "base_path": "/discoveries",
        "promoted_count": len(promoted),
        "new_count": len(newly_created),
        "week_count": week_count,
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
