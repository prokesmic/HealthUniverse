"""Procedural SVG illustrations per edge.

Deterministic from (factor_slug, outcome_slug) so every reload is the same
artwork. Kind-specific art templates so a "food" card looks like organic
seeds/leaves while a "drug" card looks like a molecular diagram. Stays
on-brand (cream + gold + tier tint) without ever hitting the network.

Public API:
    edge_svg(factor_slug, outcome_slug, tier, factor_kind, outcome_kind, w, h)
"""
from __future__ import annotations

import hashlib
import math


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

_TIER_ACCENT = {
    "A": ("#3b8e5a", "#86c79b"),     # green
    "B": ("#c8a02a", "#e8d28a"),     # gold/yellow
    "C": ("#d97757", "#f0b8a0"),     # orange
    "D": ("#c44545", "#ec9c9c"),     # coral
    "X": ("#7a6a8c", "#c5b6dc"),     # violet
}

_KIND_PALETTE = {
    "food":          [("#7c8e3a", "#cfd9a5"), ("#a08560", "#e0cda3"), ("#8a4a3a", "#dfb09f")],
    "nutrient":      [("#7c8e3a", "#cfd9a5"), ("#3b8e5a", "#9bc7ac")],
    "supplement":    [("#3b8e5a", "#9bc7ac"), ("#5a7eb0", "#b8c8de")],
    "drug":          [("#5a7eb0", "#c2d2e8"), ("#7a6a8c", "#c5b6dc")],
    "activity":      [("#c9a961", "#e8d8a6"), ("#a85a3a", "#dfb09f")],
    "behavior":      [("#a08560", "#dccba9"), ("#7a6a8c", "#c5b6dc")],
    "environmental": [("#7a6a8c", "#c5b6dc"), ("#5a7eb0", "#b8c8de")],
    "pathogen":      [("#a08560", "#dccba9")],
    "gene":          [("#5a7eb0", "#c2d2e8"), ("#7a6a8c", "#c5b6dc")],
    "biomarker":     [("#3b8e5a", "#86c79b"), ("#c9a961", "#e8d28a")],
    "condition":     [("#c44545", "#ec9c9c"), ("#a85a3a", "#dfb09f")],
    "process":       [("#1f3a2e", "#86a395"), ("#3b8e5a", "#9bc7ac")],
}


# ---------------------------------------------------------------------------
# Deterministic PRNG seeded from (factor, outcome, tier)
# ---------------------------------------------------------------------------

def _seed(*parts: str) -> int:
    h = hashlib.sha256("::".join(parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


def _rng(seed: int):
    state = seed & 0xFFFFFFFF
    def r() -> float:
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF
    return r


def _pick(rng, options):
    return options[int(rng() * len(options)) % len(options)]


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _backdrop(w: int, h: int, seed: int, *, c1: str, c2: str) -> str:
    """Cream backdrop with two soft color washes positioned by seed."""
    return f"""
<defs>
  <radialGradient id="bg1-{seed}" cx="30%" cy="40%" r="60%">
    <stop offset="0%"  stop-color="{c1}" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="bg2-{seed}" cx="80%" cy="70%" r="60%">
    <stop offset="0%"  stop-color="{c2}" stop-opacity="0.75"/>
    <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bgL-{seed}" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%"  stop-color="#fffdf6"/>
    <stop offset="100%" stop-color="#f7f1e3"/>
  </linearGradient>
</defs>
<rect width="{w}" height="{h}" fill="url(#bgL-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg1-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg2-{seed})"/>"""


# ----- per-kind art primitives ----------------------------------------------

def _art_food(w, h, rng, *, accent: str, light: str) -> str:
    """Organic seed/leaf forms. Random ovate shapes with veining."""
    parts = []
    n = 3 + int(rng() * 3)
    for _ in range(n):
        cx, cy = int(rng() * w), int(h * (0.3 + rng() * 0.5))
        rx = 30 + rng() * 50
        ry = rx * (0.45 + rng() * 0.4)
        rot = int(rng() * 180)
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="{light}" opacity="{0.35 + rng()*0.4:.2f}" '
            f'stroke="{accent}" stroke-width="0.8" '
            f'transform="rotate({rot} {cx} {cy})"/>'
        )
        # Subtle veining
        if rng() > 0.4:
            parts.append(
                f'<line x1="{cx-rx*0.7:.0f}" y1="{cy}" x2="{cx+rx*0.7:.0f}" y2="{cy}" '
                f'stroke="{accent}" stroke-width="0.5" opacity="0.5" '
                f'transform="rotate({rot} {cx} {cy})"/>'
            )
    return "".join(parts)


def _art_pill(w, h, rng, *, accent: str, light: str) -> str:
    """Capsule shapes + molecular nodes."""
    parts = []
    # Capsules
    for _ in range(2 + int(rng() * 2)):
        cx, cy = int(rng() * w), int(h * (0.3 + rng() * 0.5))
        rw, rh = 50 + rng() * 30, 22 + rng() * 6
        rot = int(rng() * 180)
        parts.append(
            f'<g transform="translate({cx} {cy}) rotate({rot})">'
            f'<rect x="{-rw:.0f}" y="{-rh/2:.0f}" width="{rw:.0f}" height="{rh:.0f}" '
            f'fill="{light}" stroke="{accent}" stroke-width="0.8" rx="{rh/2:.0f}"/>'
            f'<rect x="0" y="{-rh/2:.0f}" width="{rw:.0f}" height="{rh:.0f}" '
            f'fill="#fffdf6" stroke="{accent}" stroke-width="0.8" rx="{rh/2:.0f}"/>'
            f'</g>'
        )
    # Molecular dots
    for _ in range(8 + int(rng() * 6)):
        x, y = int(rng() * w), int(rng() * h)
        r = 1.5 + rng() * 2.5
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{accent}" opacity="{0.3+rng()*0.4:.2f}"/>')
    return "".join(parts)


def _art_molecule(w, h, rng, *, accent: str, light: str) -> str:
    """Hexagonal molecular structure — for drugs."""
    parts = []
    # Two or three hex rings + connecting bonds
    centers = [(int(w*0.3 + rng()*60), int(h*(0.4+rng()*0.3))),
               (int(w*0.6 + rng()*40), int(h*(0.35+rng()*0.25)))]
    for cx, cy in centers:
        r = 28 + rng() * 12
        pts = []
        for i in range(6):
            ang = math.pi * i / 3 + rng()*0.1
            pts.append(f"{cx+math.cos(ang)*r:.1f},{cy+math.sin(ang)*r:.1f}")
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.35" '
            f'stroke="{accent}" stroke-width="1.0"/>'
        )
        for p in pts:
            x, y = p.split(",")
            parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{accent}"/>')
    # Bond between centers
    if len(centers) >= 2:
        x1, y1 = centers[0]; x2, y2 = centers[1]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{accent}" stroke-width="1.4" opacity="0.6"/>'
        )
    # Sparse decoration
    for _ in range(6):
        x, y = int(rng()*w), int(rng()*h)
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.5" fill="#c9a961" opacity="0.55"/>')
    return "".join(parts)


def _art_motion(w, h, rng, *, accent: str, light: str) -> str:
    """Motion arcs and dashed trails — for activities."""
    parts = []
    # Big sweeping arc
    for _ in range(3 + int(rng() * 2)):
        cx = int(w * (0.3 + rng() * 0.4))
        cy = int(h * (0.5 + (rng()-0.5) * 0.3))
        r = 80 + rng() * 60
        a0 = rng() * math.pi
        a1 = a0 + math.pi * (0.4 + rng() * 0.5)
        x1 = cx + math.cos(a0) * r; y1 = cy + math.sin(a0) * r
        x2 = cx + math.cos(a1) * r; y2 = cy + math.sin(a1) * r
        parts.append(
            f'<path d="M {x1:.0f} {y1:.0f} A {r:.0f} {r:.0f} 0 0 1 {x2:.0f} {y2:.0f}" '
            f'fill="none" stroke="{accent}" stroke-width="2.2" stroke-linecap="round" '
            f'opacity="{0.5+rng()*0.3:.2f}"/>'
        )
    # Dashed trails
    for _ in range(2 + int(rng()*2)):
        x = int(rng()*w); y = int(rng()*h*0.8)
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x+40+rng()*30:.0f}" y2="{y+10+rng()*15:.0f}" '
            f'stroke="{light}" stroke-width="3" stroke-dasharray="2 4" opacity="0.6"/>'
        )
    return "".join(parts)


def _art_particles(w, h, rng, *, accent: str, light: str) -> str:
    """Particle cloud / wave field — for environmental."""
    parts = []
    # Wavy lines
    for i in range(4 + int(rng()*2)):
        y0 = int(h * (0.2 + i * 0.15))
        path = [f"M 0 {y0}"]
        x = 0
        while x < w:
            x += 25 + rng() * 15
            dy = (rng() - 0.5) * 30
            path.append(f"Q {x-12:.0f} {y0+dy:.0f} {x:.0f} {y0:.0f}")
        parts.append(
            f'<path d="{" ".join(path)}" fill="none" stroke="{accent}" '
            f'stroke-width="1.0" opacity="{0.25+rng()*0.3:.2f}"/>'
        )
    # Particle field
    for _ in range(30 + int(rng()*20)):
        x, y = rng()*w, rng()*h
        r = 0.8 + rng() * 1.8
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{accent}" opacity="{0.3+rng()*0.5:.2f}"/>')
    return "".join(parts)


def _art_helix(w, h, rng, *, accent: str, light: str) -> str:
    """Helix / DNA ladder — for genes."""
    parts = []
    cx = w // 2 + (rng() - 0.5) * 60
    n = 14
    height = h * 0.7
    for i in range(n):
        t = i / (n - 1)
        y = h * 0.15 + t * height
        offset = math.sin(t * math.pi * 2.4) * 40
        x1 = cx - 30 + offset
        x2 = cx + 30 + offset
        parts.append(f'<circle cx="{x1:.0f}" cy="{y:.0f}" r="3.5" fill="{accent}"/>')
        parts.append(f'<circle cx="{x2:.0f}" cy="{y:.0f}" r="3.5" fill="{light}" stroke="{accent}" stroke-width="0.8"/>')
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y:.0f}" '
            f'stroke="{accent}" stroke-width="0.7" opacity="0.55"/>'
        )
    # Connecting curves
    for x_off in (-30, 30):
        path = [f"M {cx + x_off + math.sin(0)*40:.0f} {h*0.15:.0f}"]
        for i in range(1, n):
            t = i / (n - 1)
            y = h * 0.15 + t * height
            x = cx + x_off + math.sin(t * math.pi * 2.4) * 40
            path.append(f"L {x:.0f} {y:.0f}")
        parts.append(
            f'<path d="{" ".join(path)}" fill="none" stroke="{accent}" '
            f'stroke-width="1.2" opacity="0.45"/>'
        )
    return "".join(parts)


def _art_chart(w, h, rng, *, accent: str, light: str) -> str:
    """Chart fragment — for biomarkers."""
    parts = []
    # Grid
    for i in range(1, 6):
        y = h * i / 6
        parts.append(f'<line x1="40" y1="{y:.0f}" x2="{w-40}" y2="{y:.0f}" stroke="{accent}" stroke-width="0.4" opacity="0.25"/>')
    # Trend line
    pts = []
    n = 12
    for i in range(n):
        x = 40 + (w - 80) * i / (n - 1)
        y = h * (0.25 + 0.4 * rng() + 0.2 * math.sin(i * 0.7))
        pts.append((x, y))
    path = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    parts.append(f'<path d="{path}" fill="none" stroke="{accent}" stroke-width="2.0" opacity="0.7"/>')
    # Bars under
    for i, (x, y) in enumerate(pts[::2]):
        parts.append(f'<rect x="{x-8:.0f}" y="{h-30:.0f}" width="6" height="{18 + rng()*12:.0f}" fill="{light}" opacity="0.6"/>')
    # End point dot
    if pts:
        x, y = pts[-1]
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{accent}"/>')
    return "".join(parts)


def _art_cells(w, h, rng, *, accent: str, light: str) -> str:
    """Organic cellular cluster — for conditions / processes."""
    parts = []
    n = 6 + int(rng() * 4)
    centers = []
    for _ in range(n):
        cx = int(rng() * w)
        cy = int(h * (0.25 + rng() * 0.5))
        r = 18 + rng() * 22
        centers.append((cx, cy, r))
        # Cell membrane (organic blob)
        m = 12
        pts = []
        for i in range(m):
            ang = 2 * math.pi * i / m
            rr = r * (0.85 + rng() * 0.3)
            pts.append(f"{cx + math.cos(ang)*rr:.0f},{cy + math.sin(ang)*rr:.0f}")
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.5" '
            f'stroke="{accent}" stroke-width="0.8"/>'
        )
        # Nucleus
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r*0.35:.0f}" fill="{accent}" opacity="0.45"/>')
    return "".join(parts)


def _art_orbital(w, h, rng, *, accent: str, light: str) -> str:
    """Concentric orbital rings (default fallback) — generic clean look."""
    parts = []
    cx = int(w * (0.25 + rng() * 0.5))
    cy = int(h * (0.5 + (rng() - 0.5) * 0.4))
    n_rings = 4 + int(rng() * 3)
    for i in range(n_rings):
        rx = 60 + i * (40 + rng() * 30)
        ry = 30 + i * (20 + rng() * 20)
        rot = int(rng() * 180)
        opacity = 0.10 + 0.06 * (n_rings - i) / n_rings
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="none" stroke="#c9a961" stroke-width="0.7" '
            f'opacity="{opacity:.2f}" transform="rotate({rot} {cx} {cy})"/>'
        )
    # Single accent dot at center
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{accent}" opacity="0.7"/>')
    return "".join(parts)


# Map each kind to one or more art templates. Multiple = pick by hash for variety.
_KIND_ART = {
    "food":          (_art_food,),
    "nutrient":      (_art_food, _art_orbital),
    "supplement":    (_art_pill,),
    "drug":          (_art_molecule, _art_pill),
    "activity":      (_art_motion,),
    "behavior":      (_art_motion, _art_particles),
    "environmental": (_art_particles,),
    "pathogen":      (_art_cells,),
    "gene":          (_art_helix,),
    "biomarker":     (_art_chart,),
    "condition":     (_art_cells, _art_orbital),
    "process":       (_art_cells, _art_motion),
}


def _connecting_curve(w, h, rng, *, accent: str) -> str:
    """A single deliberate factor→outcome connecting curve."""
    sx, sy = 0, int(h * (0.4 + rng() * 0.3))
    ex, ey = w, int(h * (0.4 + rng() * 0.3))
    c1x, c1y = int(w * 0.3), int(h * (0.1 + rng() * 0.3))
    c2x, c2y = int(w * 0.7), int(h * (0.6 + rng() * 0.3))
    return (f'<path d="M {sx} {sy} C {c1x} {c1y}, {c2x} {c2y}, {ex} {ey}" '
            f'fill="none" stroke="{accent}" stroke-width="1.4" '
            f'opacity="0.45" stroke-linecap="round"/>')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def edge_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
             factor_kind: str = "supplement",
             outcome_kind: str = "condition", w: int = 600, h: int = 280) -> str:
    seed = _seed(factor_slug, outcome_slug, tier)
    rng = _rng(seed)

    accent_dark, accent_light = _TIER_ACCENT.get(tier, _TIER_ACCENT["C"])
    f_palette = _KIND_PALETTE.get(factor_kind, _KIND_PALETTE["supplement"])
    o_palette = _KIND_PALETTE.get(outcome_kind, _KIND_PALETTE["condition"])
    f_dark, f_light = _pick(rng, f_palette)
    o_dark, o_light = _pick(rng, o_palette)

    # Pick which art primitives to layer
    f_art = _pick(rng, _KIND_ART.get(factor_kind, _KIND_ART["supplement"]))
    o_art = _pick(rng, _KIND_ART.get(outcome_kind, _KIND_ART["condition"]))

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="illustration for {factor_slug} and {outcome_slug}">'
    ]
    parts.append(_backdrop(w, h, seed, c1=f_light, c2=o_light))

    # Two layers of kind-art, slightly offset so they don't sit on top of each other
    # Factor art occupies left half; outcome art right half.
    parts.append(f'<g transform="translate({-int(w*0.05)} 0)">')
    parts.append(f_art(int(w*0.6), h, rng, accent=f_dark, light=f_light))
    parts.append('</g>')
    parts.append(f'<g transform="translate({int(w*0.4)} 0)">')
    parts.append(o_art(int(w*0.6), h, rng, accent=o_dark, light=o_light))
    parts.append('</g>')

    # Tier accent dots scattered
    for _ in range(8 + int(rng() * 8)):
        x, y = int(rng() * w), int(rng() * h)
        r = 1.0 + rng() * 2.0
        col = accent_dark if rng() < 0.5 else "#c9a961"
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{col}" opacity="{0.35+rng()*0.45:.2f}"/>')

    # Connecting curve overlay
    parts.append(_connecting_curve(w, h, rng, accent=accent_dark))

    parts.append("</svg>")
    return "".join(parts)
