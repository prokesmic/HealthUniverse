"""Procedural SVG illustrations per edge.

v3: dramatically richer than v2. Each card now layers:
  - cream backdrop with a subtle paper-grain noise filter
  - two soft color washes positioned by seed (fades out toward edges)
  - a kind-specific FOREGROUND motif (organic seed-pod, capsule, hexagonal
    molecular structure, motion arc, particle wave field, DNA helix,
    chart fragment, cellular cluster, orbital rings)
  - a dense scatter of fine accent dots in tier color + gold
  - a deliberate factor→outcome connecting curve

Deterministic from (factor_slug, outcome_slug, tier).
Free, runs on Vercel, no GPU, no external assets.

Public API:
    edge_svg(factor_slug, outcome_slug, tier, factor_kind, outcome_kind, w, h)

For the hero illustration:
    hero_svg(stats=...) — richer globe with orbiting node ring and label dots
"""
from __future__ import annotations

import hashlib
import math


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

_TIER_ACCENT = {
    "A": ("#3b8e5a", "#86c79b"),
    "B": ("#c8a02a", "#e8d28a"),
    "C": ("#d97757", "#f0b8a0"),
    "D": ("#c44545", "#ec9c9c"),
    "X": ("#7a6a8c", "#c5b6dc"),
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
# Deterministic PRNG
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
# Backdrop with paper grain + softer color washes
# ---------------------------------------------------------------------------

def _backdrop(w: int, h: int, seed: int, *, c1: str, c2: str, c3: str) -> str:
    return f"""
<defs>
  <radialGradient id="bg1-{seed}" cx="28%" cy="38%" r="62%">
    <stop offset="0%"  stop-color="{c1}" stop-opacity="0.95"/>
    <stop offset="55%" stop-color="{c1}" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="bg2-{seed}" cx="78%" cy="68%" r="60%">
    <stop offset="0%"  stop-color="{c2}" stop-opacity="0.85"/>
    <stop offset="55%" stop-color="{c2}" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="bg3-{seed}" cx="58%" cy="22%" r="48%">
    <stop offset="0%"  stop-color="{c3}" stop-opacity="0.5"/>
    <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bgL-{seed}" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%"  stop-color="#fffdf6"/>
    <stop offset="100%" stop-color="#f7f1e3"/>
  </linearGradient>
  <filter id="grain-{seed}" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="{seed % 65535}" />
    <feColorMatrix values="0 0 0 0 0.5
                           0 0 0 0 0.45
                           0 0 0 0 0.35
                           0 0 0 0.06 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
</defs>
<rect width="{w}" height="{h}" fill="url(#bgL-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg1-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg2-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg3-{seed})"/>
<rect width="{w}" height="{h}" filter="url(#grain-{seed})" opacity="0.4"/>"""


# ---------------------------------------------------------------------------
# Per-kind motifs — denser and more distinctive
# ---------------------------------------------------------------------------

def _art_food(w, h, rng, *, accent, light):
    """Layered ovate seeds/pods with veining, plus tiny 'grain' specks."""
    parts: list[str] = []
    n = 4 + int(rng() * 3)
    for _ in range(n):
        cx, cy = int(rng() * w), int(h * (0.25 + rng() * 0.55))
        rx = 36 + rng() * 50
        ry = rx * (0.42 + rng() * 0.45)
        rot = int(rng() * 180)
        # Soft fill
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="{light}" opacity="{0.45 + rng()*0.35:.2f}" '
            f'transform="rotate({rot} {cx} {cy})"/>'
        )
        # Outline
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="none" stroke="{accent}" stroke-width="0.9" opacity="0.55" '
            f'transform="rotate({rot} {cx} {cy})"/>'
        )
        # Veining
        if rng() > 0.3:
            parts.append(
                f'<line x1="{cx-rx*0.7:.0f}" y1="{cy}" x2="{cx+rx*0.7:.0f}" y2="{cy}" '
                f'stroke="{accent}" stroke-width="0.6" opacity="0.55" '
                f'transform="rotate({rot} {cx} {cy})"/>'
            )
        # Side veins
        for s in range(2 + int(rng()*3)):
            sy = cy + (s - 1) * ry * 0.25
            parts.append(
                f'<line x1="{cx-rx*0.3:.0f}" y1="{cy}" x2="{cx+rx*0.5:.0f}" y2="{sy:.0f}" '
                f'stroke="{accent}" stroke-width="0.4" opacity="0.4" '
                f'transform="rotate({rot} {cx} {cy})"/>'
            )
    # Grain specks
    for _ in range(20 + int(rng()*15)):
        x, y = rng()*w, rng()*h
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{0.6+rng()*1.2:.1f}" fill="{accent}" opacity="{0.25+rng()*0.4:.2f}"/>')
    return "".join(parts)


def _art_pill(w, h, rng, *, accent, light):
    """Capsules + scattered molecular nodes connected by faint bonds."""
    parts: list[str] = []
    # Capsules (2-3)
    for _ in range(2 + int(rng() * 2)):
        cx, cy = int(rng() * w), int(h * (0.3 + rng() * 0.5))
        rw, rh = 50 + rng() * 30, 22 + rng() * 6
        rot = int(rng() * 180)
        parts.append(
            f'<g transform="translate({cx} {cy}) rotate({rot})">'
            f'<rect x="{-rw:.0f}" y="{-rh/2:.0f}" width="{rw:.0f}" height="{rh:.0f}" '
            f'fill="{light}" stroke="{accent}" stroke-width="1.0" rx="{rh/2:.0f}"/>'
            f'<rect x="0" y="{-rh/2:.0f}" width="{rw:.0f}" height="{rh:.0f}" '
            f'fill="#fffdf6" stroke="{accent}" stroke-width="1.0" rx="{rh/2:.0f}"/>'
            f'<line x1="0" y1="{-rh/2:.0f}" x2="0" y2="{rh/2:.0f}" stroke="{accent}" stroke-width="1.0"/>'
            f'</g>'
        )
    # Molecule cluster — connected dots
    centers = [(rng()*w, rng()*h) for _ in range(6 + int(rng()*4))]
    for i, (x, y) in enumerate(centers):
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{2.5+rng()*2:.1f}" fill="{accent}" opacity="0.7"/>')
        # Connect to nearest neighbor
        if i > 0:
            x0, y0 = centers[i-1]
            parts.append(
                f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x:.0f}" y2="{y:.0f}" '
                f'stroke="{accent}" stroke-width="0.6" opacity="0.4"/>'
            )
    return "".join(parts)


def _art_molecule(w, h, rng, *, accent, light):
    """3 hexagonal rings connected — for drugs."""
    parts: list[str] = []
    centers = [
        (int(w*0.3), int(h*0.45 + rng()*30)),
        (int(w*0.55), int(h*0.4 + rng()*20)),
        (int(w*0.78), int(h*0.55 + rng()*25)),
    ]
    for cx, cy in centers:
        r = 26 + rng() * 12
        pts = []
        for i in range(6):
            ang = math.pi * i / 3 + rng()*0.05
            pts.append(f"{cx+math.cos(ang)*r:.1f},{cy+math.sin(ang)*r:.1f}")
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.4" '
            f'stroke="{accent}" stroke-width="1.2"/>'
        )
        for p in pts:
            x, y = p.split(",")
            parts.append(f'<circle cx="{x}" cy="{y}" r="2.8" fill="{accent}"/>')
    # Bonds
    for i in range(len(centers)-1):
        x1, y1 = centers[i]; x2, y2 = centers[i+1]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{accent}" stroke-width="1.5" opacity="0.5"/>'
        )
        # Double bond
        parts.append(
            f'<line x1="{x1+5}" y1="{y1+3}" x2="{x2+5}" y2="{y2+3}" '
            f'stroke="{accent}" stroke-width="0.8" opacity="0.4"/>'
        )
    # Wandering label dots
    for _ in range(10):
        parts.append(f'<circle cx="{int(rng()*w)}" cy="{int(rng()*h)}" r="{1.5+rng()*1.5:.1f}" fill="#c9a961" opacity="0.55"/>')
    return "".join(parts)


def _art_motion(w, h, rng, *, accent, light):
    """Dynamic motion arcs + dashed trails — for activities."""
    parts: list[str] = []
    # Several sweeping arcs
    for _ in range(4 + int(rng() * 2)):
        cx = int(w * (0.2 + rng() * 0.6))
        cy = int(h * (0.4 + (rng()-0.5) * 0.4))
        r = 70 + rng() * 70
        a0 = rng() * math.pi
        a1 = a0 + math.pi * (0.35 + rng() * 0.55)
        x1 = cx + math.cos(a0) * r; y1 = cy + math.sin(a0) * r
        x2 = cx + math.cos(a1) * r; y2 = cy + math.sin(a1) * r
        sw = 2.0 + rng() * 1.5
        parts.append(
            f'<path d="M {x1:.0f} {y1:.0f} A {r:.0f} {r:.0f} 0 0 1 {x2:.0f} {y2:.0f}" '
            f'fill="none" stroke="{accent}" stroke-width="{sw:.1f}" '
            f'stroke-linecap="round" opacity="{0.55+rng()*0.3:.2f}"/>'
        )
        # Endpoint dot
        parts.append(f'<circle cx="{x2:.0f}" cy="{y2:.0f}" r="3" fill="{accent}"/>')
    # Dashed trails
    for _ in range(3 + int(rng()*3)):
        x = int(rng()*w); y = int(rng()*h*0.85)
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x+45+rng()*30:.0f}" y2="{y+12+rng()*15:.0f}" '
            f'stroke="{light}" stroke-width="3" stroke-dasharray="3 5" opacity="0.6"/>'
        )
    return "".join(parts)


def _art_particles(w, h, rng, *, accent, light):
    """Multiple wave layers + fine particle field — environmental."""
    parts: list[str] = []
    n_waves = 5 + int(rng()*2)
    for i in range(n_waves):
        y0 = int(h * (0.15 + i * 0.14))
        amp = 14 + rng() * 22
        period = 60 + rng() * 30
        path = [f"M 0 {y0}"]
        x = 0
        while x < w:
            x += period
            path.append(f"Q {x-period/2:.0f} {y0 + amp:.0f} {x:.0f} {y0:.0f}")
            x += period
            path.append(f"Q {x-period/2:.0f} {y0 - amp:.0f} {x:.0f} {y0:.0f}")
        parts.append(
            f'<path d="{" ".join(path)}" fill="none" stroke="{accent}" '
            f'stroke-width="{0.8 + rng()*0.6:.1f}" opacity="{0.25+rng()*0.35:.2f}"/>'
        )
    # Particle field
    for _ in range(40 + int(rng()*25)):
        x, y = rng()*w, rng()*h
        r = 0.7 + rng() * 1.8
        col = accent if rng() < 0.6 else light
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" opacity="{0.35+rng()*0.5:.2f}"/>')
    return "".join(parts)


def _art_helix(w, h, rng, *, accent, light):
    """DNA double-helix — for genes. Now denser with phosphate-style backbone."""
    parts: list[str] = []
    cx = w // 2 + int((rng() - 0.5) * 60)
    n = 18
    height = h * 0.8
    amp = 50
    for i in range(n):
        t = i / (n - 1)
        y = h * 0.1 + t * height
        offset = math.sin(t * math.pi * 2.6) * amp
        x1 = cx - 32 + offset
        x2 = cx + 32 + offset
        parts.append(f'<circle cx="{x1:.0f}" cy="{y:.0f}" r="3.5" fill="{accent}"/>')
        parts.append(f'<circle cx="{x2:.0f}" cy="{y:.0f}" r="3.5" fill="{light}" stroke="{accent}" stroke-width="0.9"/>')
        parts.append(
            f'<line x1="{x1:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y:.0f}" '
            f'stroke="{accent}" stroke-width="0.8" opacity="0.6"/>'
        )
    # Smooth backbone curves
    for x_off in (-32, 32):
        path = []
        for i in range(n):
            t = i / (n - 1)
            y = h * 0.1 + t * height
            x = cx + x_off + math.sin(t * math.pi * 2.6) * amp
            path.append(f"{'M' if i == 0 else 'L'} {x:.0f} {y:.0f}")
        parts.append(
            f'<path d="{" ".join(path)}" fill="none" stroke="{accent}" '
            f'stroke-width="1.6" opacity="0.55"/>'
        )
    return "".join(parts)


def _art_chart(w, h, rng, *, accent, light):
    """Chart fragment with grid + trend + bars — biomarkers."""
    parts: list[str] = []
    # Grid
    for i in range(1, 7):
        y = h * i / 7
        parts.append(f'<line x1="32" y1="{y:.0f}" x2="{w-32}" y2="{y:.0f}" stroke="{accent}" stroke-width="0.4" opacity="0.22"/>')
    # Y-axis labels (decorative)
    for i in range(1, 5):
        y = h * i / 5
        parts.append(f'<circle cx="22" cy="{y:.0f}" r="1.5" fill="{accent}" opacity="0.5"/>')
    # Bars under
    n_bars = 12
    for i in range(n_bars):
        x = 32 + (w - 64) * i / n_bars
        bh = 14 + rng() * 26
        parts.append(f'<rect x="{x:.0f}" y="{h-30:.0f}" width="{(w-64)/n_bars-3:.0f}" '
                     f'height="{bh:.0f}" fill="{light}" opacity="{0.55+rng()*0.3:.2f}"/>')
    # Trend line
    pts = []
    n = 14
    for i in range(n):
        x = 32 + (w - 64) * i / (n - 1)
        y = h * (0.25 + 0.4 * rng() + 0.18 * math.sin(i * 0.7))
        pts.append((x, y))
    path = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    parts.append(f'<path d="{path}" fill="none" stroke="{accent}" stroke-width="2.2" opacity="0.75"/>')
    # Endpoint marker
    if pts:
        x, y = pts[-1]
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="{accent}"/>')
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="none" stroke="{accent}" stroke-width="1" opacity="0.4"/>')
    return "".join(parts)


def _art_cells(w, h, rng, *, accent, light):
    """Organic cellular cluster with nucleus — conditions / processes."""
    parts: list[str] = []
    n = 7 + int(rng() * 4)
    for _ in range(n):
        cx = int(rng() * w)
        cy = int(h * (0.2 + rng() * 0.6))
        r = 22 + rng() * 26
        m = 14
        pts = []
        for i in range(m):
            ang = 2 * math.pi * i / m
            rr = r * (0.85 + rng() * 0.32)
            pts.append(f"{cx + math.cos(ang)*rr:.0f},{cy + math.sin(ang)*rr:.0f}")
        # Membrane
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.55" '
            f'stroke="{accent}" stroke-width="0.9"/>'
        )
        # Nucleus
        nucr = r * (0.3 + rng() * 0.15)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{nucr:.0f}" fill="{accent}" opacity="0.55"/>')
        parts.append(f'<circle cx="{cx-2}" cy="{cy-2}" r="{nucr*0.5:.0f}" fill="#fffdf6" opacity="0.4"/>')
        # Organelle dots
        for _ in range(2 + int(rng()*3)):
            ox = cx + (rng() - 0.5) * r
            oy = cy + (rng() - 0.5) * r
            parts.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="{1.5+rng()*1.5:.1f}" fill="{accent}" opacity="0.6"/>')
    return "".join(parts)


def _art_orbital(w, h, rng, *, accent, light):
    """Concentric orbital rings — fallback / clean look."""
    parts: list[str] = []
    cx = int(w * (0.25 + rng() * 0.5))
    cy = int(h * (0.5 + (rng() - 0.5) * 0.4))
    n_rings = 5 + int(rng() * 3)
    for i in range(n_rings):
        rx = 50 + i * (38 + rng() * 28)
        ry = 28 + i * (18 + rng() * 18)
        rot = int(rng() * 180)
        opacity = 0.12 + 0.08 * (n_rings - i) / n_rings
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="none" stroke="#c9a961" stroke-width="0.8" '
            f'opacity="{opacity:.2f}" transform="rotate({rot} {cx} {cy})"/>'
        )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{accent}" opacity="0.75"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="14" fill="none" stroke="{accent}" stroke-width="1" opacity="0.4"/>')
    # Sparse orbit dots
    for i in range(n_rings * 2):
        ang = i * 0.7
        r = 50 + (i % n_rings) * 38
        ox = cx + math.cos(ang) * r
        oy = cy + math.sin(ang) * r * 0.6
        parts.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="2" fill="#c9a961" opacity="0.7"/>')
    return "".join(parts)


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
    sx, sy = 0, int(h * (0.35 + rng() * 0.35))
    ex, ey = w, int(h * (0.4 + rng() * 0.3))
    c1x, c1y = int(w * 0.3), int(h * (0.1 + rng() * 0.3))
    c2x, c2y = int(w * 0.7), int(h * (0.6 + rng() * 0.3))
    return (f'<path d="M {sx} {sy} C {c1x} {c1y}, {c2x} {c2y}, {ex} {ey}" '
            f'fill="none" stroke="{accent}" stroke-width="1.6" '
            f'opacity="0.5" stroke-linecap="round"/>')


# ---------------------------------------------------------------------------
# Public: edge_svg
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

    f_art = _pick(rng, _KIND_ART.get(factor_kind, _KIND_ART["supplement"]))
    o_art = _pick(rng, _KIND_ART.get(outcome_kind, _KIND_ART["condition"]))

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="illustration for {factor_slug} and {outcome_slug}">'
    ]
    parts.append(_backdrop(w, h, seed, c1=f_light, c2=o_light, c3=accent_light))

    # Factor art on the left half
    parts.append(f'<g transform="translate({-int(w*0.05)} 0)">')
    parts.append(f_art(int(w*0.62), h, rng, accent=f_dark, light=f_light))
    parts.append('</g>')
    # Outcome art on the right half
    parts.append(f'<g transform="translate({int(w*0.42)} 0)">')
    parts.append(o_art(int(w*0.62), h, rng, accent=o_dark, light=o_light))
    parts.append('</g>')

    # Connecting curve
    parts.append(_connecting_curve(w, h, rng, accent=accent_dark))

    # Tier accent dots — denser
    for _ in range(14 + int(rng() * 10)):
        x, y = int(rng() * w), int(rng() * h)
        r = 1.2 + rng() * 2.4
        col = accent_dark if rng() < 0.45 else "#c9a961"
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{col}" opacity="{0.4+rng()*0.5:.2f}"/>')

    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Public: hero_svg — richer globe with ring of orbiting nodes
# ---------------------------------------------------------------------------

def hero_svg() -> str:
    """Decorative hero illustration — orbiting node sphere on cream backdrop.
    Replaces the old static globe in home.html."""
    rng = _rng(0xc9a961)  # fixed seed → consistent across reloads
    parts: list[str] = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 460" '
                 'width="100%" height="100%" aria-hidden="true">')
    parts.append("""
<defs>
  <radialGradient id="globe" cx="48%" cy="42%" r="55%">
    <stop offset="0%"  stop-color="#fffdf6"/>
    <stop offset="60%" stop-color="#f3ead2"/>
    <stop offset="100%" stop-color="#e3d4ad"/>
  </radialGradient>
  <radialGradient id="globe-glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%"  stop-color="#fff4d4" stop-opacity="0.8"/>
    <stop offset="100%" stop-color="#fff4d4" stop-opacity="0"/>
  </radialGradient>
</defs>""")
    # Outer glow
    parts.append('<circle cx="230" cy="230" r="200" fill="url(#globe-glow)"/>')
    # Sphere
    parts.append('<circle cx="230" cy="230" r="170" fill="url(#globe)"/>')
    # Concentric latitude rings (ellipses rotated)
    for i in range(20):
        a = i * 9
        parts.append(
            f'<ellipse cx="230" cy="230" rx="{40 + i*7}" ry="170" '
            f'fill="none" stroke="#c9a961" stroke-width="0.4" opacity="0.4" '
            f'transform="rotate({a} 230 230)"/>'
        )
    # Crossing meridians (denser)
    for i in range(8):
        a = i * 22
        parts.append(
            f'<ellipse cx="230" cy="230" rx="170" ry="{40 + i*16}" '
            f'fill="none" stroke="#c9a961" stroke-width="0.35" opacity="0.32" '
            f'transform="rotate({a} 230 230)"/>'
        )
    # Orbit ring
    parts.append('<ellipse cx="230" cy="230" rx="195" ry="60" '
                 'fill="none" stroke="#c9a961" stroke-width="0.7" '
                 'opacity="0.6" transform="rotate(-12 230 230)"/>')
    # Nodes scattered on globe surface
    nodes = [
        (148, 142, 3.5), (210, 96, 3.0), (296, 132, 4.0), (340, 200, 3.0),
        (322, 290, 3.5), (240, 332, 3.0), (152, 322, 3.5), (108, 252, 3.0),
        (192, 200, 2.5), (272, 252, 3.0), (210, 252, 2.0), (164, 198, 2.5),
    ]
    for x, y, r in nodes:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#c9a961"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r*2.5:.1f}" fill="#c9a961" opacity="0.18"/>')
    # Connecting lines between a few nodes
    for a, b in [(0, 4), (1, 5), (2, 7), (3, 6), (8, 10)]:
        x1, y1, _ = nodes[a]; x2, y2, _ = nodes[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                     f'stroke="#c9a961" stroke-width="0.5" opacity="0.5"/>')
    # Orbit dots (planetoid)
    parts.append('<circle cx="425" cy="218" r="5" fill="#1f3a2e"/>')
    parts.append('<circle cx="38" cy="246" r="3.5" fill="#3b8e5a"/>')
    parts.append('</svg>')
    return "".join(parts)
