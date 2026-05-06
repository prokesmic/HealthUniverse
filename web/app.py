"""Health Universe web app — FastAPI + Jinja templates."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from datetime import datetime, timedelta  # noqa: E402

from db import connect  # noqa: E402


def datetime_now():
    return datetime.now()
from profile import COOKIE, Profile, decode, encode, relevance_score  # noqa: E402
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
    return templates.TemplateResponse(request, template, {**_TEMPLATE_GLOBALS, **ctx})


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
    edges = conn.execute("SELECT COUNT(*) c FROM edge").fetchone()["c"]
    studies = conn.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"]
    last = conn.execute("SELECT MAX(updated_at) m FROM edge").fetchone()["m"]
    return {"edges": edges, "studies": studies, "updated": last or "—"}


def _featured(conn, limit: int = 3) -> list[dict]:
    rows = conn.execute("""
        SELECT e.id, e.tier, e.direction, e.summary, e.updated_at, e.created_at,
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
    featured = featured[:4]
    spotlight = featured[0] if featured else None
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
    avoid_rows: list[dict] = []
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
                       e.created_at,
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
            avoid_rows = [dict(r) for r in harmful] + [dict(r) for r in ushape] + [dict(r) for r in mixed]
            for e in do_rows + avoid_rows:
                e["score"] = _importance_score(e)
                e["breakthrough"] = _is_breakthrough(e)
            do_rows.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
            avoid_rows.sort(key=lambda e: (-(1 if e["breakthrough"] else 0), -e["score"]))
    return render(request, "prevent.html", {
        "title": "Prevent",
        "query": query,
        "matched": matched,
        "suggestions": suggestions,
        "do_rows": do_rows[:20],
        "avoid_rows": avoid_rows[:20],
        "outcomes": outcomes,
    })


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
    return render(request, "me.html", {
        "profile": p,
        "factors": [dict(r) for r in all_factors],
        "outcomes": [dict(r) for r in all_outcomes],
        "relevant": relevant,
        "red_flags": red_flags,
        "no_regret": no_regret,
    })


@app.post("/me")
async def me_save(request: Request,
                  age: str = Form(""), sex: str = Form(""),
                  conditions: list[str] = Form(default=[]),
                  goals: list[str] = Form(default=[]),
                  stack: list[str] = Form(default=[])):
    p = Profile(
        age=int(age) if age.isdigit() else None,
        sex=sex or None,
        conditions=[c for c in conditions if c],
        goals=[g for g in goals if g],
        stack=[s for s in stack if s],
    )
    resp = RedirectResponse("/me", status_code=303)
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
    return render(request, "edge.html", {
        "e": dict(e),
        "evidence": ev_rows,
        "counter": co_rows,
        "history": [dict(r) for r in history],
        "retracted_evidence_count": retracted_count,
        "profile": profile,
    })


@app.get("/tier/{tier}", response_class=HTMLResponse)
def by_tier(request: Request, tier: str, page: int = 1):
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) c FROM edge WHERE tier=?", (tier,)).fetchone()["c"]
        pg = _paginate(total, page)
        rows = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                   f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                   o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.tier = ?
            ORDER BY e.updated_at DESC LIMIT ? OFFSET ?""",
            (tier, PAGE_SIZE, pg["offset"])).fetchall()
    return render(request, "list.html", {
        "title": TIER_LABEL.get(tier, tier),
        "edges": [dict(r) for r in rows],
        "pg": pg, "base_path": f"/tier/{tier}",
    })


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
    return render(request, "search.html", {
        "title": f"Search: {q}" if q else "Search",
        "q": q, "edges": edges, "entities": entities,
        "semantic_added": semantic_added,
        "intent": _classify_query(q) if q else None,
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
def category(request: Request, slug: str, page: int = 1):
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return HTMLResponse("Not found", status_code=404)
    with connect() as conn:
        if "kinds" in cat:
            placeholders = ",".join("?" * len(cat["kinds"]))
            total = conn.execute(
                f"SELECT COUNT(*) c FROM edge e JOIN entity f ON e.factor_id=f.id "
                f"WHERE f.kind IN ({placeholders})", cat["kinds"]).fetchone()["c"]
            pg = _paginate(total, page)
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE f.kind IN ({placeholders})
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END,
                         e.updated_at DESC LIMIT ? OFFSET ?""",
                (*cat["kinds"], PAGE_SIZE, pg["offset"])).fetchall()
        else:
            placeholders = ",".join("?" * len(cat["outcomes"]))
            total = conn.execute(
                f"SELECT COUNT(*) c FROM edge e JOIN entity o ON e.outcome_id=o.id "
                f"WHERE o.slug IN ({placeholders})", cat["outcomes"]).fetchone()["c"]
            pg = _paginate(total, page)
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
                       o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE o.slug IN ({placeholders})
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END,
                         e.updated_at DESC LIMIT ? OFFSET ?""",
                (*cat["outcomes"], PAGE_SIZE, pg["offset"])).fetchall()
    return render(request, "list.html", {
        "title": cat["label"],
        "edges": [dict(r) for r in rows],
        "pg": pg, "base_path": f"/category/{slug}",
    })
