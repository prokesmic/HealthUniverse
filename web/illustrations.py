"""Procedural SVG illustrations per edge.

Deterministic from (factor_slug, outcome_slug) so every reload is the same
artwork. Stays on-brand (cream + gold + tier tint, organic curves, orbital
dots) without ever hitting the network or pulling raster assets.
"""
from __future__ import annotations

import hashlib
import math


# Tier accent colors — paired with cream backdrop
_TIER_ACCENT = {
    "A": ("#3b8e5a", "#86c79b"),     # green
    "B": ("#c8a02a", "#e8d28a"),     # gold/yellow
    "C": ("#d97757", "#f0b8a0"),     # orange
    "D": ("#c44545", "#ec9c9c"),     # coral
    "X": ("#7a6a8c", "#c5b6dc"),     # violet (contested)
}
_KIND_HUE = {
    "food":          ("#7c8e3a", "#cfd9a5"),
    "nutrient":      ("#7c8e3a", "#cfd9a5"),
    "supplement":    ("#3b8e5a", "#9bc7ac"),
    "drug":          ("#5a7eb0", "#c2d2e8"),
    "activity":      ("#c9a961", "#e8d8a6"),
    "behavior":      ("#a08560", "#dccba9"),
    "environmental": ("#7a6a8c", "#c5b6dc"),
    "process":       ("#1f3a2e", "#86a395"),
    "condition":     ("#c44545", "#ec9c9c"),
    "biomarker":     ("#3b8e5a", "#86c79b"),
}


def _seed(*parts: str) -> int:
    h = hashlib.sha256("::".join(parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


def _rng(seed: int):
    """Deterministic PRNG. Returns a function call → float in [0,1)."""
    state = seed & 0xFFFFFFFF
    def r() -> float:
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF
    return r


def edge_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
             factor_kind: str = "supplement",
             outcome_kind: str = "condition", w: int = 600, h: int = 280) -> str:
    """Return a self-contained <svg>…</svg> string."""
    seed = _seed(factor_slug, outcome_slug, tier)
    rng = _rng(seed)
    accent_dark, accent_light = _TIER_ACCENT.get(tier, _TIER_ACCENT["C"])
    f_dark, f_light = _KIND_HUE.get(factor_kind, _KIND_HUE["supplement"])
    o_dark, o_light = _KIND_HUE.get(outcome_kind, _KIND_HUE["condition"])

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="abstract illustration for {factor_slug} and {outcome_slug}">'
    )

    # Defs — gradients
    parts.append(f'''<defs>
      <radialGradient id="g1-{seed}" cx="30%" cy="40%" r="60%">
        <stop offset="0%"  stop-color="{f_light}" stop-opacity="0.9"/>
        <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="g2-{seed}" cx="80%" cy="70%" r="60%">
        <stop offset="0%"  stop-color="{o_light}" stop-opacity="0.85"/>
        <stop offset="100%" stop-color="#f7f1e3" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="bg-{seed}" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%"  stop-color="#fffdf6"/>
        <stop offset="100%" stop-color="#f7f1e3"/>
      </linearGradient>
    </defs>''')

    # Cream backdrop with two soft color washes
    parts.append(f'<rect width="{w}" height="{h}" fill="url(#bg-{seed})"/>')
    parts.append(f'<rect width="{w}" height="{h}" fill="url(#g1-{seed})"/>')
    parts.append(f'<rect width="{w}" height="{h}" fill="url(#g2-{seed})"/>')

    # Concentric "orbit" rings — gold accent, faint
    cx = int(w * (0.25 + rng() * 0.5))
    cy = int(h * (0.5 + (rng() - 0.5) * 0.4))
    n_rings = 4 + int(rng() * 3)
    for i in range(n_rings):
        rx = 60 + i * (40 + rng() * 30)
        ry = 30 + i * (20 + rng() * 20)
        rot = int(rng() * 180)
        opacity = 0.10 + 0.06 * (n_rings - i) / n_rings
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="none" stroke="#c9a961" stroke-width="0.7" '
            f'opacity="{opacity:.2f}" transform="rotate({rot} {cx} {cy})"/>'
        )

    # Organic blob silhouette — biological / leaf feel, tier-tinted
    n_blob = 18
    cx2 = int(w * (0.3 + rng() * 0.4))
    cy2 = int(h * (0.55 + (rng() - 0.5) * 0.3))
    base_r = min(w, h) * (0.18 + rng() * 0.08)
    pts: list[str] = []
    for i in range(n_blob):
        ang = 2 * math.pi * i / n_blob
        rr = base_r * (0.85 + rng() * 0.4)
        x = cx2 + math.cos(ang) * rr
        y = cy2 + math.sin(ang) * rr * 0.85
        pts.append(f"{x:.1f},{y:.1f}")
    parts.append(
        f'<polygon points="{ " ".join(pts) }" fill="{accent_dark}" '
        f'opacity="0.10" />'
    )
    parts.append(
        f'<polygon points="{ " ".join(pts) }" fill="none" '
        f'stroke="{accent_dark}" stroke-width="0.8" opacity="0.45"/>'
    )

    # Sparse star/dot field — gold + tier accent
    n_dots = 14 + int(rng() * 8)
    for _ in range(n_dots):
        x = int(rng() * w)
        y = int(rng() * h)
        r = 1.2 + rng() * 2.4
        color = "#c9a961" if rng() < 0.65 else accent_dark
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{color}" opacity="{(0.4 + rng()*0.55):.2f}"/>')

    # A single deliberate connecting curve from factor side -> outcome side
    sx, sy = 0, int(h * (0.4 + rng() * 0.3))
    ex, ey = w, int(h * (0.4 + rng() * 0.3))
    c1x, c1y = int(w * 0.3), int(h * (0.1 + rng() * 0.3))
    c2x, c2y = int(w * 0.7), int(h * (0.6 + rng() * 0.3))
    parts.append(
        f'<path d="M {sx} {sy} C {c1x} {c1y}, {c2x} {c2y}, {ex} {ey}" '
        f'fill="none" stroke="{accent_dark}" stroke-width="1.4" opacity="0.55"/>'
    )

    parts.append('</svg>')
    return "".join(parts)
