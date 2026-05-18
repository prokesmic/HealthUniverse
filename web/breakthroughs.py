"""Breakthroughs feed — loader + server-side SVG study-graphic generators.

The feed lives in `data/breakthroughs.json`. The Gemma daily job appends
new items; this module reads and renders.

Graphic kinds (chosen by the JSON `graphic.kind`):
  • kaplan_meier    — survival step-curves with median markers
  • forest_plot     — point estimates + 95% CI whiskers, log-x optional
  • bar_delta       — paired bars (treatment vs control) with labels
  • line_trend      — multi-series time-course
  • recall_pictogram — warning chevron + lot/severity callout

Each generator returns an SVG string. They're deterministic — same JSON
in, same SVG out — so they cache safely. No external font deps.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FEED_PATH = ROOT / "data" / "breakthroughs.json"

# ─── Palette (mirrors web/static/style.css) ────────────────────────
INK = "#1f1f1f"
INK_SOFT = "#5a5a5a"
LINE = "#e8e2d0"
GREEN = "#1f3a2e"
GREEN_SOFT = "#3b8e5a"
GOLD = "#c9a961"
HARM = "#9b1c1c"
HARM_SOFT = "#f3b3ad"
PROT = "#1b5e20"
MIX = "#7a5c00"
BG_SOFT = "#faf4dd"
SURFACE = "#ffffff"

# ─── Category & stage metadata ─────────────────────────────────────
CATEGORY_LABEL = {
    "oncology":  "Oncology",
    "cardio":    "Cardiovascular",
    "metabolic": "Metabolic",
    "neuro":     "Neuro & Mental Health",
    "longevity": "Longevity",
    "other":     "Other",
}
CATEGORY_ORDER = ["oncology", "cardio", "metabolic", "neuro", "longevity", "other"]

STAGE_LABEL = {
    "preclinical": "Preclinical",
    "phase1":      "Phase 1",
    "phase2":      "Phase 2",
    "phase3":      "Phase 3",
    "approved":    "Approved / Label",
    "guideline":   "Guideline",
    "recall":      "Recall / Safety",
}
STAGE_TONE = {
    "preclinical": ("#ece6f3", "#3b2a5e"),
    "phase1":      ("#eaf3ff", "#1f3a7e"),
    "phase2":      ("#fff7e0", "#7a5c00"),
    "phase3":      ("#e7f5ec", "#1b5e20"),
    "approved":    ("#e7f5ec", "#1b5e20"),
    "guideline":   ("#fff7e0", "#7a5c00"),
    "recall":      ("#fdecea", "#9b1c1c"),
}

# ─── IO ────────────────────────────────────────────────────────────

def load_feed() -> dict:
    if not FEED_PATH.exists():
        return {"items": [], "updated_at": None}
    return json.loads(FEED_PATH.read_text())


def save_feed(feed: dict) -> None:
    feed["updated_at"] = date.today().isoformat()
    FEED_PATH.write_text(json.dumps(feed, indent=2))


def items(category: str | None = None, limit: int | None = None,
          days: int | None = None, audience: str | None = "general") -> list[dict]:
    """Read the feed with optional filters.

    `audience`: 'general' (default) keeps only entries written for non-specialists.
                Pass `None` to disable the filter (admin, orphan queue).
    """
    feed = load_feed()
    rows = feed.get("items", [])
    if audience:
        rows = [r for r in rows if r.get("audience", "general") == audience]
    if category and category != "all":
        rows = [r for r in rows if r.get("category") == category]
    if days:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        rows = [r for r in rows if r.get("published_at", "") >= cutoff]
    rows = sorted(rows, key=lambda r: r.get("published_at", ""), reverse=True)
    if limit:
        rows = rows[:limit]
    return rows


def get(item_id: str) -> dict | None:
    return next((r for r in load_feed().get("items", []) if r["id"] == item_id), None)


def orphans() -> list[dict]:
    """Items that didn't match a corpus edge — seeding queue."""
    return [r for r in load_feed().get("items", []) if r.get("is_orphan")]


def days_ago(published_at: str) -> int:
    try:
        d = datetime.fromisoformat(published_at).date()
        return (date.today() - d).days
    except Exception:
        return 0


def category_counts(audience: str | None = "general", days: int | None = None) -> dict[str, int]:
    """Per-category counts, scoped to the same filters used by the lane."""
    rows = items(audience=audience, days=days)
    out = {k: 0 for k in CATEGORY_ORDER}
    for r in rows:
        c = r.get("category", "other")
        out[c] = out.get(c, 0) + 1
    return out


# ─── SVG primitives ────────────────────────────────────────────────

def _svg_open(w: int, h: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="100%" height="100%" preserveAspectRatio="xMidYMid meet" '
            f'role="img" aria-hidden="true">')


def _bg(w: int, h: int, fill: str = BG_SOFT) -> str:
    return f'<rect x="0" y="0" width="{w}" height="{h}" fill="{fill}"/>'


def _text(x: float, y: float, txt: str, size: int = 10,
          color: str = INK_SOFT, anchor: str = "start",
          weight: int = 400, family: str = "Inter, system-ui, sans-serif") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{txt}</text>')


# ─── Kaplan-Meier ──────────────────────────────────────────────────

def km_svg(g: dict, w: int = 400, h: int = 220) -> str:
    """Schematic survival curve. Step-down from 100% at t=0 toward an
    asymptote consistent with the reported median.

    Required keys: median_t (months), median_c (months), x_label, y_label
    Optional: hr, ci_low, ci_high, treatment_label, control_label
    """
    pad_l, pad_r, pad_t, pad_b = 56, 14, 22, 36
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    x_max = max(g.get("median_t", 18), g.get("median_c", 12)) * 2.0  # 2× median

    def to_x(t: float) -> float: return pad_l + (t / x_max) * plot_w
    def to_y(s: float) -> float: return pad_t + (1 - s) * plot_h

    def curve_points(median: float, n_steps: int = 16) -> list[tuple[float, float]]:
        # Exponential approximation: S(t) = exp(-ln(2)*t/median)
        pts: list[tuple[float, float]] = []
        for i in range(n_steps + 1):
            t = (i / n_steps) * x_max
            s = math.exp(-math.log(2) * t / max(median, 0.1))
            pts.append((t, s))
        return pts

    def step_path(median: float) -> str:
        pts = curve_points(median)
        d = f"M {to_x(0):.1f} {to_y(1):.1f} "
        for i in range(1, len(pts)):
            t0, s0 = pts[i - 1]
            t1, s1 = pts[i]
            # horizontal then vertical = step look
            d += f"L {to_x(t1):.1f} {to_y(s0):.1f} L {to_x(t1):.1f} {to_y(s1):.1f} "
        return d

    parts = [_svg_open(w, h), _bg(w, h)]

    # y-axis grid + labels
    for s_pct in (0, 25, 50, 75, 100):
        y = to_y(s_pct / 100)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        parts.append(_text(pad_l - 8, y + 3, f"{s_pct}", 9, anchor="end"))

    # x-axis labels at 0 / median / 2× median
    for tick in (0, x_max / 2, x_max):
        parts.append(_text(to_x(tick), h - pad_b + 14, f"{tick:.0f}", 9, anchor="middle"))

    # 50% reference (median survival line)
    y50 = to_y(0.5)
    parts.append(f'<line x1="{pad_l}" y1="{y50:.1f}" x2="{w - pad_r}" y2="{y50:.1f}" stroke="{GOLD}" stroke-width="1" stroke-dasharray="3 3"/>')

    # Curves
    parts.append(f'<path d="{step_path(g["median_c"])}" fill="none" stroke="{INK_SOFT}" stroke-width="2"/>')
    parts.append(f'<path d="{step_path(g["median_t"])}" fill="none" stroke="{GREEN}" stroke-width="2.5"/>')

    # Median tick markers
    parts.append(f'<line x1="{to_x(g["median_c"]):.1f}" y1="{y50:.1f}" x2="{to_x(g["median_c"]):.1f}" y2="{h - pad_b:.1f}" stroke="{INK_SOFT}" stroke-width="1" stroke-dasharray="2 2"/>')
    parts.append(f'<line x1="{to_x(g["median_t"]):.1f}" y1="{y50:.1f}" x2="{to_x(g["median_t"]):.1f}" y2="{h - pad_b:.1f}" stroke="{GREEN}" stroke-width="1" stroke-dasharray="2 2"/>')

    # Axis titles
    parts.append(_text(pad_l + plot_w / 2, h - 6, g.get("x_label", "Months"), 10, anchor="middle", color=INK))
    parts.append(_text(14, pad_t + plot_h / 2, g.get("y_label", "Survival"), 10, anchor="middle", color=INK,
                       weight=500))

    # Legend (top right)
    lx = pad_l + 6
    parts.append(f'<rect x="{lx}" y="{pad_t - 2}" width="10" height="3" fill="{GREEN}"/>')
    parts.append(_text(lx + 14, pad_t + 2, f'{g.get("treatment_label", "Treatment")} (median {g["median_t"]})', 10, color=INK))
    parts.append(f'<rect x="{lx}" y="{pad_t + 12}" width="10" height="3" fill="{INK_SOFT}"/>')
    parts.append(_text(lx + 14, pad_t + 16, f'{g.get("control_label", "Control")} (median {g["median_c"]})', 10, color=INK_SOFT))

    # HR badge bottom-right
    if g.get("hr"):
        hr = g["hr"]; lo = g.get("ci_low"); hi = g.get("ci_high")
        label = f"HR {hr:.2f}"
        if lo and hi:
            label += f"  ({lo:.2f}–{hi:.2f})"
        parts.append(f'<rect x="{w - pad_r - 132}" y="{h - pad_b - 22}" width="124" height="18" rx="9" fill="{GREEN}" opacity="0.92"/>')
        parts.append(_text(w - pad_r - 70, h - pad_b - 9, label, 10, color="#ffffff", anchor="middle", weight=600))

    parts.append("</svg>")
    return "".join(parts)


# ─── Forest plot ───────────────────────────────────────────────────

def forest_svg(g: dict, w: int = 400, h: int = 220) -> str:
    """Vertical study list with point estimates + 95% CI whiskers.
    Reference line at `reference` (HR=1.0 for hazard, baseline % for incidence)."""
    studies = g.get("studies", [])
    if not studies:
        return f'{_svg_open(w, h)}{_bg(w, h)}</svg>'
    pad_l, pad_r, pad_t, pad_b = 96, 36, 22, 36
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    ref = g.get("reference", 1.0)
    log = bool(g.get("log_scale"))

    all_vals = []
    for s in studies:
        all_vals += [s.get("estimate", ref), s.get("ci_low", ref), s.get("ci_high", ref)]
    lo, hi = min(all_vals + [ref * 0.5]), max(all_vals + [ref * 1.5])
    if log:
        lo_t, hi_t = math.log(max(lo, 0.01)), math.log(hi)
        def to_x(v: float) -> float:
            return pad_l + ((math.log(max(v, 0.01)) - lo_t) / (hi_t - lo_t)) * plot_w
    else:
        def to_x(v: float) -> float:
            return pad_l + ((v - lo) / (hi - lo)) * plot_w

    row_h = plot_h / max(len(studies), 1)
    parts = [_svg_open(w, h), _bg(w, h)]

    # Reference line
    parts.append(f'<line x1="{to_x(ref):.1f}" y1="{pad_t}" x2="{to_x(ref):.1f}" y2="{h - pad_b}" stroke="{INK_SOFT}" stroke-width="1" stroke-dasharray="3 3"/>')

    # Study rows
    for i, s in enumerate(studies):
        cy = pad_t + row_h * (i + 0.5)
        est = s.get("estimate", ref); cl = s.get("ci_low", est); ch = s.get("ci_high", est)
        better = est < ref
        color = PROT if better else HARM if est > ref * 1.05 else MIX
        # name
        parts.append(_text(pad_l - 8, cy + 3, s.get("name", ""), 10, anchor="end", color=INK, weight=500))
        # whiskers
        parts.append(f'<line x1="{to_x(cl):.1f}" y1="{cy:.1f}" x2="{to_x(ch):.1f}" y2="{cy:.1f}" stroke="{color}" stroke-width="1.5"/>')
        parts.append(f'<line x1="{to_x(cl):.1f}" y1="{cy - 5:.1f}" x2="{to_x(cl):.1f}" y2="{cy + 5:.1f}" stroke="{color}" stroke-width="1.5"/>')
        parts.append(f'<line x1="{to_x(ch):.1f}" y1="{cy - 5:.1f}" x2="{to_x(ch):.1f}" y2="{cy + 5:.1f}" stroke="{color}" stroke-width="1.5"/>')
        # point
        size = 6
        parts.append(f'<rect x="{to_x(est) - size/2:.1f}" y="{cy - size/2:.1f}" width="{size}" height="{size}" fill="{color}" transform="rotate(45 {to_x(est):.1f} {cy:.1f})"/>')
        # estimate label to right
        label = f"{est:.2f}" if est < 10 else f"{est:.1f}"
        parts.append(_text(w - pad_r + 4, cy + 3, label, 9, color=color, weight=600))

    # X-axis label
    parts.append(_text(pad_l + plot_w / 2, h - 6, g.get("x_label", "Estimate"), 10, anchor="middle", color=INK))

    # Tick marks at lo / ref / hi
    for v in (lo, ref, hi):
        x = to_x(v)
        parts.append(f'<line x1="{x:.1f}" y1="{h - pad_b}" x2="{x:.1f}" y2="{h - pad_b + 4}" stroke="{INK_SOFT}" stroke-width="1"/>')
        label = f"{v:.2f}" if v < 10 else f"{v:.0f}"
        parts.append(_text(x, h - pad_b + 14, label, 9, anchor="middle"))

    parts.append("</svg>")
    return "".join(parts)


# ─── Bar delta (treatment vs control, multiple endpoints) ──────────

def bar_delta_svg(g: dict, w: int = 400, h: int = 220) -> str:
    bars = g.get("bars", [])
    if not bars:
        return f'{_svg_open(w, h)}{_bg(w, h)}</svg>'
    pad_l, pad_r, pad_t, pad_b = 28, 24, 38, 50
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    all_vals = [abs(b["treatment"]) for b in bars] + [abs(b["control"]) for b in bars]
    vmax = max(all_vals + [1]) * 1.15
    group_w = plot_w / len(bars)
    bar_w = min(group_w * 0.32, 28)

    parts = [_svg_open(w, h), _bg(w, h)]
    parts.append(_text(pad_l, pad_t - 22, g.get("treatment_label", "Treatment"), 10, color=GREEN, weight=600))
    parts.append(f'<rect x="{pad_l}" y="{pad_t - 14}" width="10" height="8" fill="{GREEN}"/>')
    parts.append(_text(pad_l + 90, pad_t - 22, g.get("control_label", "Control"), 10, color=INK_SOFT, weight=600))
    parts.append(f'<rect x="{pad_l + 90}" y="{pad_t - 14}" width="10" height="8" fill="{INK_SOFT}"/>')

    zero_y = pad_t + plot_h  # x-axis baseline
    # Baseline
    parts.append(f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{w - pad_r}" y2="{zero_y:.1f}" stroke="{LINE}" stroke-width="1"/>')

    for i, b in enumerate(bars):
        cx = pad_l + group_w * (i + 0.5)
        t = b["treatment"]; c = b["control"]
        # Handle negative values (e.g. MADRS change)
        t_h = (abs(t) / vmax) * plot_h
        c_h = (abs(c) / vmax) * plot_h
        t_y = zero_y - t_h if t >= 0 else zero_y
        c_y = zero_y - c_h if c >= 0 else zero_y
        # Treatment bar (green) left
        parts.append(f'<rect x="{cx - bar_w - 2:.1f}" y="{t_y:.1f}" width="{bar_w}" height="{t_h:.1f}" fill="{GREEN}" rx="2"/>')
        # Control bar (soft) right
        parts.append(f'<rect x="{cx + 2:.1f}" y="{c_y:.1f}" width="{bar_w}" height="{c_h:.1f}" fill="{INK_SOFT}" opacity="0.75" rx="2"/>')
        # Value labels above bars
        unit_suffix = "%" if g.get("unit") == "%" else ""
        parts.append(_text(cx - bar_w / 2 - 2, t_y - 4, f"{t:g}{unit_suffix}", 10, anchor="middle", color=GREEN, weight=600))
        parts.append(_text(cx + bar_w / 2 + 2, c_y - 4, f"{c:g}{unit_suffix}", 10, anchor="middle", color=INK_SOFT, weight=500))
        # Endpoint label below
        label = b["label"]
        if len(label) > 24:
            # break into two lines
            words = label.split(" ")
            mid = len(words) // 2
            l1, l2 = " ".join(words[:mid]), " ".join(words[mid:])
            parts.append(_text(cx, zero_y + 14, l1, 10, anchor="middle", color=INK))
            parts.append(_text(cx, zero_y + 26, l2, 10, anchor="middle", color=INK))
        else:
            parts.append(_text(cx, zero_y + 16, label, 10, anchor="middle", color=INK))

    parts.append("</svg>")
    return "".join(parts)


# ─── Line trend ────────────────────────────────────────────────────

def line_trend_svg(g: dict, w: int = 400, h: int = 220) -> str:
    series = g.get("series", [])
    if not series:
        return f'{_svg_open(w, h)}{_bg(w, h)}</svg>'
    pad_l, pad_r, pad_t, pad_b = 50, 14, 22, 38
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    all_x = [p[0] for s in series for p in s["points"]]
    all_y = [p[1] for s in series for p in s["points"]]
    xmin, xmax = min(all_x), max(all_x) or 1
    ymin, ymax = min(all_y + [0]), max(all_y + [100])
    yspan = max(ymax - ymin, 1)

    def to_x(x): return pad_l + ((x - xmin) / max(xmax - xmin, 1)) * plot_w
    def to_y(y): return pad_t + (1 - (y - ymin) / yspan) * plot_h

    parts = [_svg_open(w, h), _bg(w, h)]
    # Y grid (4 lines)
    for f in (0, 0.25, 0.5, 0.75, 1):
        yv = ymin + f * yspan
        y = to_y(yv)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        parts.append(_text(pad_l - 6, y + 3, f"{yv:.0f}", 9, anchor="end"))
    # X ticks (start, mid, end)
    for x_v in (xmin, (xmin + xmax) / 2, xmax):
        parts.append(_text(to_x(x_v), h - pad_b + 14, f"{x_v:g}", 9, anchor="middle"))

    palette = [GREEN, INK_SOFT, GOLD, HARM]
    for i, s in enumerate(series):
        color = palette[i % len(palette)]
        pts = s["points"]
        d = "M " + " L ".join(f"{to_x(x):.1f} {to_y(y):.1f}" for x, y in pts)
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{2.5 if i == 0 else 1.8}"/>')
        for x, y in pts:
            parts.append(f'<circle cx="{to_x(x):.1f}" cy="{to_y(y):.1f}" r="2.5" fill="{color}"/>')
        # Legend
        lx, ly = pad_l + 6, pad_t + 4 + i * 14
        parts.append(f'<rect x="{lx}" y="{ly}" width="10" height="3" fill="{color}"/>')
        parts.append(_text(lx + 14, ly + 4, s["label"], 10, color=color if i == 0 else INK_SOFT, weight=600 if i == 0 else 400))

    # Axis titles
    parts.append(_text(pad_l + plot_w / 2, h - 6, g.get("x_label", ""), 10, anchor="middle", color=INK))
    parts.append(_text(12, pad_t + plot_h / 2, g.get("y_label", ""), 10, anchor="middle", color=INK, weight=500))
    parts.append("</svg>")
    return "".join(parts)


# ─── Recall pictogram ──────────────────────────────────────────────

def recall_svg(g: dict, w: int = 400, h: int = 220) -> str:
    parts = [_svg_open(w, h), _bg(w, h, "#fff8f7")]
    # Border-left rose stripe
    parts.append(f'<rect x="0" y="0" width="6" height="{h}" fill="{HARM}"/>')
    # Warning triangle
    cx, cy = 90, h / 2
    s = 56
    parts.append(f'<path d="M {cx} {cy - s} L {cx - s * 0.95} {cy + s * 0.55} L {cx + s * 0.95} {cy + s * 0.55} Z" '
                 f'fill="{HARM_SOFT}" stroke="{HARM}" stroke-width="2.5" stroke-linejoin="round"/>')
    parts.append(_text(cx, cy + 6, "!", 38, anchor="middle", color=HARM, weight=700,
                       family="Fraunces, Georgia, serif"))
    # Text block
    tx = 170
    parts.append(_text(tx, cy - 28, g.get("severity", "Recall"), 13, color=HARM, weight=700))
    parts.append(_text(tx, cy - 8, g.get("product", ""), 18, color=INK, weight=600,
                       family="Fraunces, Georgia, serif"))
    parts.append(_text(tx, cy + 14, f"{g.get('lots_affected', '?')} affected lots", 11, color=INK_SOFT))
    parts.append(_text(tx, cy + 30, "Check NDC against FDA notice → swap to different generic", 10, color=INK_SOFT))
    parts.append("</svg>")
    return "".join(parts)


# ─── Dispatch ──────────────────────────────────────────────────────

_RENDERERS = {
    "kaplan_meier":      km_svg,
    "forest_plot":       forest_svg,
    "bar_delta":         bar_delta_svg,
    "line_trend":        line_trend_svg,
    "recall_pictogram":  recall_svg,
}


def graphic_svg(item: dict, w: int = 400, h: int = 220) -> str:
    g = item.get("graphic") or {}
    kind = g.get("kind", "bar_delta")
    fn = _RENDERERS.get(kind, bar_delta_svg)
    try:
        return fn(g, w=w, h=h)
    except Exception:
        # Never blow up a card render — show an empty cream placeholder.
        return f'{_svg_open(w, h)}{_bg(w, h)}{_text(w/2, h/2, "—", 14, anchor="middle")}</svg>'


# ─── Match-to-corpus helper (used by daily job and on read) ────────

def match_corpus(factor_slug: str | None, outcome_slug: str | None) -> str | None:
    """Return an edge id if both slugs exist in our SQLite corpus, else None.
    Lazy import so this module stays usable in scripts without the FastAPI app."""
    if not factor_slug or not outcome_slug:
        return None
    try:
        from db import connect  # type: ignore
    except Exception:
        return None
    try:
        with connect() as conn:
            row = conn.execute(
                """SELECT e.id FROM edge e
                   JOIN entity f ON f.id=e.factor_id
                   JOIN entity o ON o.id=e.outcome_id
                   WHERE f.slug=? AND o.slug=? LIMIT 1""",
                (factor_slug, outcome_slug),
            ).fetchone()
            return row[0] if row else None
    except Exception:
        return None
