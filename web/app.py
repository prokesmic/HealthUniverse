"""Health Universe web app — FastAPI + Jinja templates."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import wrap

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from db import connect  # noqa: E402

app = FastAPI(title="Health Universe")
WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
OG_CACHE_DIR = ROOT / "data" / "cache" / "og"
BASE_DESCRIPTION = (
    "Continuously updated evidence for nutrition, lifestyle, supplements, "
    "cardiovascular health, metabolic health, oncology, sleep, and longevity."
)


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
    meta = {
        "meta_title": ctx.get("meta_title", "Health Universe"),
        "meta_description": ctx.get("meta_description", BASE_DESCRIPTION),
        "meta_url": ctx.get("meta_url", str(request.url)),
        "meta_image": ctx.get("meta_image", str(request.url_for("static", path="og-default.svg"))),
        "meta_type": ctx.get("meta_type", "website"),
    }
    return templates.TemplateResponse(request, template, {**_TEMPLATE_GLOBALS, **ctx, **meta})


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


def _edge_row(conn, edge_id: int):
    return conn.execute("""
        SELECT e.*, f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE e.id = ?""", (edge_id,)).fetchone()


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


def _search_edges(conn, query: str) -> list[dict]:
    like = f"%{query.lower()}%"
    rows = conn.execute("""
        SELECT DISTINCT e.id, e.tier, e.direction, e.summary, e.updated_at,
               f.name AS f_name, f.slug AS f_slug, f.aliases AS f_aliases,
               o.name AS o_name, o.slug AS o_slug, o.aliases AS o_aliases
        FROM edge e
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE lower(f.name) LIKE ?
           OR lower(COALESCE(f.aliases, '')) LIKE ?
           OR lower(o.name) LIKE ?
           OR lower(COALESCE(o.aliases, '')) LIKE ?
           OR lower(COALESCE(e.summary, '')) LIKE ?
        ORDER BY CASE e.tier
                   WHEN 'A' THEN 1
                   WHEN 'B' THEN 2
                   WHEN 'C' THEN 3
                   WHEN 'X' THEN 4
                   ELSE 5
                 END,
                 e.updated_at DESC
    """, (like, like, like, like, like)).fetchall()
    return [dict(r) for r in rows]


def _font(size: int, *, serif: bool = False):
    candidates = (
        ["Fraunces-Regular.ttf", "Georgia.ttf", "Times New Roman.ttf", "DejaVuSerif.ttf"]
        if serif
        else ["Inter-Regular.ttf", "Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf"]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _build_og_card(edge: dict) -> Image.Image:
    image = Image.new("RGB", (1200, 630), "#f7f1e3")
    draw = ImageDraw.Draw(image)

    draw.ellipse((30, 20, 390, 300), fill="#fbf4e7")
    draw.ellipse((860, 40, 1160, 240), fill="#f1e8d3")
    draw.rounded_rectangle((44, 44, 1156, 586), radius=42, fill="#fffdf6", outline="#e7decb", width=2)
    draw.rounded_rectangle((720, 84, 1108, 546), radius=34, fill="#fbf4e7", outline="#e7decb", width=2)

    gold = "#c9a961"
    for i in range(6):
        inset = i * 16
        draw.arc((770 - inset, 180 - inset, 1058 + inset, 468 + inset), 30, 330, fill=gold, width=1)

    title_font = _font(68, serif=True)
    body_font = _font(26)
    label_font = _font(22)
    value_font = _font(28)
    badge_font = _font(20)

    draw.text((92, 92), "HEALTH UNIVERSE", fill="#8a8278", font=label_font)

    tier_fill = {
        "A": "#e6efe1",
        "B": "#f7eecf",
        "C": "#f7d9c7",
        "D": "#f4cece",
        "X": "#ebe2f2",
    }.get(edge["tier"], "#ece6d8")
    tier_text = {
        "A": "#3b8e5a",
        "B": "#8a6c18",
        "C": "#a64a28",
        "D": "#8a2929",
        "X": "#4a3e5a",
    }.get(edge["tier"], "#5a544c")
    draw.rounded_rectangle((92, 136, 320, 176), radius=18, fill=tier_fill)
    draw.text((112, 145), TIER_LABEL.get(edge["tier"], edge["tier"]).upper(), fill=tier_text, font=badge_font)

    headline = f"{edge['f_name']} and {edge['o_name']}"
    y = 208
    for line in _wrap_lines(draw, headline, title_font, 560)[:3]:
        draw.text((92, y), line, fill="#2a2520", font=title_font)
        y += 76

    summary = edge.get("summary") or ""
    summary_lines = []
    for paragraph in wrap(summary, 220):
        summary_lines.extend(_wrap_lines(draw, paragraph, body_font, 560))
    for line in summary_lines[:4]:
        draw.text((92, y + 8), line, fill="#5a544c", font=body_font)
        y += 36

    draw.text((770, 110), "Confidence", fill="#8a8278", font=label_font)
    draw.text((770, 150), TIER_LABEL.get(edge["tier"], edge["tier"]), fill="#1f3a2e", font=value_font)
    draw.text((770, 236), "Direction", fill="#8a8278", font=label_font)
    draw.text((770, 276), DIRECTION_LABEL.get(edge["direction"], edge["direction"]), fill="#2a2520", font=value_font)
    draw.text((770, 362), "Updated", fill="#8a8278", font=label_font)
    draw.text((770, 402), edge["updated_at"][:10], fill="#2a2520", font=value_font)
    draw.text((770, 488), "health-universe.vercel.app", fill="#5a544c", font=label_font)
    return image


def _write_og_card(edge: dict) -> Path | None:
    OG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OG_CACHE_DIR / f"{edge['id']}.png"
    _build_og_card(edge).save(out_path, format="PNG")
    return out_path


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
        "meta_title": "Health Universe",
        "meta_description": BASE_DESCRIPTION,
    })


@app.get("/edge/{edge_id}.png", name="edge_share_card")
def edge_share_card(edge_id: int):
    with connect() as conn:
        e = _edge_row(conn, edge_id)
    if not e:
        return Response("Not found", media_type="text/plain", status_code=404)
    try:
        out_path = _write_og_card(dict(e))
    except OSError:
        out_path = None

    if out_path and out_path.exists():
        return FileResponse(out_path, media_type="image/png")

    image = _build_og_card(dict(e))
    from io import BytesIO

    buf = BytesIO()
    image.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")


@app.get("/edge/{edge_id}", response_class=HTMLResponse)
def edge_detail(request: Request, edge_id: int):
    with connect() as conn:
        e = _edge_row(conn, edge_id)
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
        "meta_title": f"{e['f_name']} and {e['o_name']} — Health Universe",
        "meta_description": e["summary"],
        "meta_image": str(request.url_for("edge_share_card", edge_id=edge_id)),
        "meta_type": "article",
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
        "meta_title": f"{TIER_LABEL.get(tier, tier)} — Health Universe",
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
        "meta_title": f"{cat['label']} — Health Universe",
    })


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    query = q.strip()
    edges: list[dict] = []
    if query:
        with connect() as conn:
            edges = _search_edges(conn, query)
    return render(request, "search.html", {
        "title": "Search",
        "query": query,
        "edges": edges,
        "meta_title": f"Search: {query} — Health Universe" if query else "Search — Health Universe",
        "meta_description": f"Search evidence relationships for {query}." if query else BASE_DESCRIPTION,
    })


@app.get("/sitemap.xml")
def sitemap(request: Request):
    with connect() as conn:
        edge_rows = conn.execute("SELECT id, updated_at FROM edge ORDER BY updated_at DESC").fetchall()
    base = str(request.base_url).rstrip("/")
    urls = [f"{base}/"]
    urls.extend(f"{base}/category/{cat['slug']}" for cat in CATEGORIES)
    urls.extend(f"{base}/tier/{tier}" for tier in ("A", "B", "C", "D", "X"))
    urls.extend(f"{base}/edge/{row['id']}" for row in edge_rows)
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        body.append("  <url>")
        body.append(f"    <loc>{url}</loc>")
        body.append("  </url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")


@app.get("/robots.txt")
def robots(request: Request):
    base = str(request.base_url).rstrip("/")
    return Response(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", media_type="text/plain")
