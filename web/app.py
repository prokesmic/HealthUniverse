"""Health Universe web app — FastAPI + Jinja templates."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from db import connect  # noqa: E402

app = FastAPI(title="Health Universe")
WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


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
    with connect() as conn:
        stats = _stats(conn)
        cats = [{**c, "count": _category_count(conn, c)} for c in CATEGORIES]
        featured = _featured(conn, limit=3)
        buckets = _evidence_strength_buckets(conn)
        spotlight = featured[0] if featured else None
    return render(request, "home.html", {
        "stats": stats, "categories": cats,
        "featured": featured, "buckets": buckets, "spotlight": spotlight,
    })


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
