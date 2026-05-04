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
from db import connect  # noqa: E402
from profile import COOKIE, Profile, decode, encode, relevance_score  # noqa: E402
from web.illustrations import edge_svg  # noqa: E402

app = FastAPI(title="Health Universe")
WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

# Make `edge_svg(...)` callable from any Jinja template.
# (Functions in env.globals are hashable, unlike dict-valued globals.)
templates.env.globals["edge_svg"] = edge_svg


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
        SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name,
               (SELECT COUNT(*) FROM evidence ev WHERE ev.edge_id=e.id) AS n_studies,
               (SELECT study_type FROM evidence ev WHERE ev.edge_id=e.id
                ORDER BY CASE study_type
                  WHEN 'meta_analysis' THEN 1 WHEN 'systematic_review' THEN 2
                  WHEN 'rct' THEN 3 WHEN 'cohort' THEN 4 ELSE 5 END LIMIT 1) AS top_study
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE e.tier IN ('A','B','C')
        ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                 e.updated_at DESC
        LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


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
    return [dict(r) for r in rows]


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
    featured = featured[:3]
    spotlight = featured[0] if featured else None
    return render(request, "home.html", {
        "stats": stats, "categories": cats,
        "featured": featured, "buckets": buckets, "spotlight": spotlight,
        "profile": p, "discoveries": discoveries,
    })


@app.get("/discoveries", response_class=HTMLResponse)
def discoveries(request: Request, days: int = 30):
    with connect() as conn:
        rows = _new_discoveries(conn, days=days, limit=200)
    return render(request, "discoveries.html", {
        "title": "Discoveries", "rows": rows, "days": days,
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
    return render(request, "me.html", {
        "profile": p,
        "factors": [dict(r) for r in all_factors],
        "outcomes": [dict(r) for r in all_outcomes],
        "relevant": relevant,
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


@app.post("/me/clear")
def me_clear():
    resp = RedirectResponse("/me", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


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
        evidence = conn.execute(
            "SELECT * FROM evidence WHERE edge_id = ? ORDER BY year DESC",
            (edge_id,)).fetchall()
        history = conn.execute(
            "SELECT * FROM edge_history WHERE edge_id = ? ORDER BY changed_at DESC",
            (edge_id,)).fetchall()
    return render(request, "edge.html", {
        "e": dict(e),
        "evidence": [dict(r) for r in evidence],
        "history": [dict(r) for r in history],
    })


@app.get("/tier/{tier}", response_class=HTMLResponse)
def by_tier(request: Request, tier: str):
    with connect() as conn:
        rows = conn.execute("""
            SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                   f.name AS f_name, o.name AS o_name
            FROM edge e
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE e.tier = ?
            ORDER BY e.updated_at DESC""", (tier,)).fetchall()
    return render(request, "list.html", {
        "title": TIER_LABEL.get(tier, tier),
        "edges": [dict(r) for r in rows],
    })


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    q = q.strip()
    edges: list[dict] = []
    entities: list[dict] = []
    if q:
        like = f"%{q}%"
        with connect() as conn:
            edges = [dict(r) for r in conn.execute("""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.name AS f_name, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE f.name LIKE ? OR o.name LIKE ?
                   OR e.summary LIKE ? OR e.mechanism LIKE ?
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END
                LIMIT 50""", (like, like, like, like)).fetchall()]
            entities = [dict(r) for r in conn.execute(
                "SELECT slug, name, kind FROM entity WHERE name LIKE ? "
                "ORDER BY name LIMIT 20", (like,)).fetchall()]
    return render(request, "search.html", {
        "title": f"Search: {q}" if q else "Search",
        "q": q, "edges": edges, "entities": entities,
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
def changes(request: Request, days: int = 14):
    """What changed recently — tier promotions/demotions, new edges."""
    with connect() as conn:
        rows = conn.execute("""
            SELECT h.changed_at, h.field, h.old_value, h.new_value, h.reason, h.actor,
                   e.id AS edge_id, e.tier, e.direction,
                   f.name AS f_name, o.name AS o_name
            FROM edge_history h
            JOIN edge e ON e.id = h.edge_id
            JOIN entity f ON f.id = e.factor_id
            JOIN entity o ON o.id = e.outcome_id
            WHERE h.changed_at >= datetime('now', ?)
            ORDER BY h.changed_at DESC LIMIT 200""",
            (f"-{int(days)} days",)).fetchall()
    return render(request, "changes.html", {
        "title": "What changed",
        "rows": [dict(r) for r in rows],
        "days": days,
    })


@app.get("/category/{slug}", response_class=HTMLResponse)
def category(request: Request, slug: str):
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return HTMLResponse("Not found", status_code=404)
    with connect() as conn:
        if "kinds" in cat:
            placeholders = ",".join("?" * len(cat["kinds"]))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.name AS f_name, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE f.kind IN ({placeholders})
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END,
                         e.updated_at DESC""", cat["kinds"]).fetchall()
        else:
            placeholders = ",".join("?" * len(cat["outcomes"]))
            rows = conn.execute(f"""
                SELECT e.id, e.tier, e.direction, e.summary, e.updated_at,
                       f.name AS f_name, o.name AS o_name
                FROM edge e
                JOIN entity f ON f.id = e.factor_id
                JOIN entity o ON o.id = e.outcome_id
                WHERE o.slug IN ({placeholders})
                ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2
                              WHEN 'C' THEN 3 WHEN 'X' THEN 4 ELSE 5 END,
                         e.updated_at DESC""", cat["outcomes"]).fetchall()
    return render(request, "list.html", {
        "title": cat["label"],
        "edges": [dict(r) for r in rows],
    })
