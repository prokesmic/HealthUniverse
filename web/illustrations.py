"""Procedural box-art system for Health Universe homepage.

Three public modes, all topic-aware and deterministic per (factor, outcome):

  featured_card_svg(...)     — full-bleed premium scene for Featured Evidence
  discovery_card_svg(...)    — lighter variant for Discoveries strip
  strength_wave_svg(tier)    — subtle bottom-wave for Evidence Strength buckets
  edge_svg(...)              — simple per-edge art (kept for /tier, /category lists)
  hero_svg()                 — globe for the home hero

A topic classifier picks one of ~10 scene templates from the slug pair:
mediterranean / supplement-capsule / botanical / heart / brain / sleep /
motion / wave / hexmolecule / cellular / orbital fallback. Palette comes
from kind + tier so it's brand-coherent.
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

# Scene-tinted palettes — warm, restrained, editorial
_SCENE_PALETTE = {
    "mediterranean": ("#6a8a3a", "#c8d49c", "#c9a961", "#fff8e1"),
    "supplement":    ("#c9a961", "#e8d28a", "#3b8e5a", "#fff8e1"),
    "botanical":     ("#5a7a4a", "#b6c995", "#a08560", "#f7f1e3"),
    "heart":         ("#a85a6a", "#e0bfc6", "#c44545", "#fff5f0"),
    "brain":         ("#7a6a8c", "#c5b6dc", "#5a7eb0", "#f5f0fa"),
    "sleep":         ("#5a6a8c", "#b8c5dc", "#c9a961", "#f0f3fa"),
    "motion":        ("#c9a961", "#e8d28a", "#3b8e5a", "#fff8e1"),
    "wave":          ("#7a6a8c", "#c5b6dc", "#5a7eb0", "#f5f0fa"),
    "hexmolecule":   ("#5a7eb0", "#c2d2e8", "#7a6a8c", "#f5f5fa"),
    "cellular":      ("#c44545", "#ec9c9c", "#a85a3a", "#fff5f0"),
    "berry":         ("#7a3a5a", "#d49cb6", "#c9a961", "#fff8e1"),
    "coffee":        ("#5a3a2a", "#b89060", "#c9a961", "#fff5e6"),
    "alcohol":       ("#7a3a3a", "#d49ca0", "#c9a961", "#fff5e6"),
    "fish":          ("#3a6a8c", "#9cc4dc", "#c9a961", "#f0f5fa"),
    "orbital":       ("#c9a961", "#e8d28a", "#3b8e5a", "#fffdf6"),
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
# Topic classifier — slug pair → scene
# ---------------------------------------------------------------------------

def _classify_scene(factor_slug: str, outcome_slug: str,
                    factor_kind: str = "", outcome_kind: str = "") -> str:
    f = (factor_slug or "").lower()
    o = (outcome_slug or "").lower()

    # Outcome-side cues (often more visually defining)
    if any(t in o for t in ("cancer", "tumor", "tumour", "neoplasm", "carcinoma")):
        return "botanical"
    if any(t in o for t in ("alzheimer", "dementia", "cognitive", "parkinson", "schizophrenia", "depression", "anxiety")):
        return "brain"
    if any(t in o for t in ("sleep", "insomnia", "circadian", "rem")):
        return "sleep"
    if any(t in o for t in ("cvd", "cardio", "stroke", "heart", "hypertension", "myocardial", "atrial")):
        return "heart"
    if any(t in o for t in ("microbiome", "gut", "ibd", "ibs")):
        return "cellular"

    # Factor-side cues
    if any(t in f for t in ("olive", "mediterranean", "leafy", "legume", "whole_grain")):
        return "mediterranean"
    if any(t in f for t in ("berry", "berries", "apple", "fruit")):
        return "berry"
    if any(t in f for t in ("coffee", "tea", "caffeine")):
        return "coffee"
    if "alcohol" in f or "wine" in f:
        return "alcohol"
    if any(t in f for t in ("fish", "marine", "seafood")):
        return "fish"
    if any(t in f for t in ("walking", "running", "exercise", "training", "hiit", "yoga")):
        return "motion"
    if any(t in f for t in ("smoke", "smoking", "vap", "pollut", "pm25", "pfas", "bpa", "noise", "shift_work", "screen")):
        return "wave"

    # Kind-based fallbacks
    if factor_kind == "supplement" or any(t in f for t in ("vitamin", "mineral", "magnesium", "creatine", "omega", "zinc", "iron")):
        return "supplement"
    if factor_kind == "drug":
        return "hexmolecule"
    if factor_kind == "environmental":
        return "wave"
    if factor_kind in ("activity", "behavior"):
        return "motion"
    if outcome_kind == "biomarker":
        return "supplement"   # chart-fragment fits biomarker ok via lighter form

    return "orbital"


# ---------------------------------------------------------------------------
# Scene functions — each returns inner SVG markup (no <svg> wrapper)
# Each takes a viewBox (w, h), an rng, and palette tuple (dark, light, accent, surface).
# ---------------------------------------------------------------------------

def _scene_mediterranean(w, h, rng, palette):
    """Olive branch + grain stalks + warm green-gold field."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx, cy = int(w * 0.35), int(h * 0.55)
    # Olive branch — main stem
    sx, sy = int(w * 0.15), int(h * 0.85)
    ex, ey = int(w * 0.85), int(h * 0.25)
    parts.append(
        f'<path d="M {sx} {sy} Q {cx} {cy*0.6} {ex} {ey}" '
        f'fill="none" stroke="{dark}" stroke-width="2.4" stroke-linecap="round" opacity="0.85"/>'
    )
    # Leaves along the stem
    n_leaves = 7 + int(rng() * 3)
    for i in range(n_leaves):
        t = 0.1 + 0.85 * i / n_leaves
        # Bezier point estimation
        bx = (1-t)**2 * sx + 2*(1-t)*t * cx + t**2 * ex
        by = (1-t)**2 * sy + 2*(1-t)*t * (cy*0.6) + t**2 * ey
        side = -1 if i % 2 else 1
        ang = (-30 if side > 0 else 30) + (rng() - 0.5) * 20
        # Leaf shape
        parts.append(
            f'<g transform="translate({bx:.0f} {by:.0f}) rotate({ang:.0f})">'
            f'<ellipse cx="{18 * side}" cy="0" rx="22" ry="8" fill="{light}" '
            f'stroke="{dark}" stroke-width="0.7" opacity="0.92"/>'
            f'<line x1="0" y1="0" x2="{36 * side}" y2="0" stroke="{dark}" stroke-width="0.5" opacity="0.7"/>'
            f'</g>'
        )
    # Olive fruits clustered near the bottom
    for _ in range(5 + int(rng() * 3)):
        ox = sx + int(rng() * (cx - sx) * 0.8)
        oy = sy - 30 - int(rng() * 50)
        parts.append(
            f'<ellipse cx="{ox}" cy="{oy}" rx="8" ry="11" fill="{dark}" opacity="0.85"/>'
            f'<ellipse cx="{ox-2}" cy="{oy-3}" rx="2.5" ry="3" fill="{light}" opacity="0.6"/>'
        )
    # Wheat/grain stalks bottom-right
    gx = int(w * 0.7)
    for i in range(3):
        x = gx + i * 18
        y = int(h * 0.92)
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y - 70}" '
            f'stroke="{accent}" stroke-width="1.4" opacity="0.7"/>'
        )
        for j in range(5):
            yy = y - 18 - j * 12
            parts.append(
                f'<ellipse cx="{x-4}" cy="{yy}" rx="3.5" ry="6" fill="{accent}" opacity="0.85" transform="rotate(-25 {x} {yy})"/>'
                f'<ellipse cx="{x+4}" cy="{yy}" rx="3.5" ry="6" fill="{accent}" opacity="0.85" transform="rotate(25 {x} {yy})"/>'
            )
    return "".join(parts)


def _scene_supplement(w, h, rng, palette):
    """Capsule cluster with glassy highlights + droplet + amber dust."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    centers = []
    # 3 capsules at varied angles
    for i in range(3 + int(rng() * 2)):
        cx = int(w * (0.2 + i * 0.22 + rng() * 0.05))
        cy = int(h * (0.4 + (rng() - 0.5) * 0.3))
        rw, rh = 60, 22
        rot = int((rng() - 0.5) * 80)
        centers.append((cx, cy, rot))
        parts.append(
            f'<g transform="translate({cx} {cy}) rotate({rot})">'
            # Shadow
            f'<rect x="{-rw + 2}" y="{-rh/2 + 4}" width="{2*rw - 2}" height="{rh:.0f}" '
            f'fill="#000" opacity="0.08" rx="{rh/2:.0f}" ry="{rh/2:.0f}"/>'
            # Body (filled half)
            f'<rect x="{-rw}" y="{-rh/2:.0f}" width="{rw}" height="{rh:.0f}" '
            f'fill="{dark}" rx="{rh/2:.0f}"/>'
            # Body (clear half)
            f'<rect x="0" y="{-rh/2:.0f}" width="{rw}" height="{rh:.0f}" '
            f'fill="{light}" stroke="{dark}" stroke-width="0.8" rx="{rh/2:.0f}"/>'
            # Glassy highlight
            f'<path d="M {-rw + 8} {-rh/4:.0f} Q {-rw/2} {-rh/2 - 1:.0f} {-8} {-rh/4:.0f}" '
            f'stroke="white" stroke-width="2" fill="none" opacity="0.45"/>'
            f'<path d="M {8} {-rh/4:.0f} Q {rw/2} {-rh/2 - 1:.0f} {rw - 8} {-rh/4:.0f}" '
            f'stroke="white" stroke-width="2" fill="none" opacity="0.55"/>'
            f'</g>'
        )
    # Amber droplet bottom-right
    dx, dy = int(w * 0.78), int(h * 0.78)
    parts.append(
        f'<path d="M {dx} {dy - 22} Q {dx - 14} {dy + 4} {dx} {dy + 12} '
        f'Q {dx + 14} {dy + 4} {dx} {dy - 22} Z" '
        f'fill="{accent}" opacity="0.85"/>'
        f'<ellipse cx="{dx - 5}" cy="{dy - 6}" rx="3" ry="5" fill="white" opacity="0.55"/>'
    )
    # Floating amber specks
    for _ in range(20):
        x, y = int(rng() * w), int(rng() * h)
        r = 0.8 + rng() * 1.6
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{accent}" opacity="{0.3+rng()*0.4:.2f}"/>')
    return "".join(parts)


def _scene_botanical(w, h, rng, palette):
    """Calmer botanical leaves + small flowers — for cancer/oncology topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    # Several leaves fanning from a single base point bottom-left
    bx, by = int(w * 0.22), int(h * 0.95)
    n = 6 + int(rng() * 3)
    for i in range(n):
        ang_deg = -160 + (i * 35) + (rng() - 0.5) * 8
        ang = math.radians(ang_deg)
        L = 70 + rng() * 50
        ex = bx + math.cos(ang) * L
        ey = by + math.sin(ang) * L
        # Leaf
        parts.append(
            f'<g transform="translate({(bx+ex)/2:.0f} {(by+ey)/2:.0f}) rotate({ang_deg + 90:.0f})">'
            f'<ellipse cx="0" cy="0" rx="{L*0.45:.0f}" ry="{L*0.18:.0f}" '
            f'fill="{light}" stroke="{dark}" stroke-width="0.8" opacity="0.85"/>'
            f'<line x1="{-L*0.4:.0f}" y1="0" x2="{L*0.4:.0f}" y2="0" stroke="{dark}" stroke-width="0.6" opacity="0.55"/>'
            f'</g>'
        )
    # Small flowers (5-petal abstracted) right side
    for k in range(2):
        fx = int(w * (0.65 + k * 0.18))
        fy = int(h * (0.3 + k * 0.25))
        for p in range(5):
            ang = math.radians(p * 72)
            px = fx + math.cos(ang) * 9
            py = fy + math.sin(ang) * 9
            parts.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="6" fill="{accent}" opacity="0.7"/>')
        parts.append(f'<circle cx="{fx}" cy="{fy}" r="4" fill="{dark}"/>')
    # Faint speckles
    for _ in range(14):
        parts.append(f'<circle cx="{int(rng()*w)}" cy="{int(rng()*h)}" r="{1+rng():.1f}" fill="{dark}" opacity="{0.2+rng()*0.3:.2f}"/>')
    return "".join(parts)


def _scene_heart(w, h, rng, palette):
    """Stylized heart silhouette + soft pulse trace — cardiovascular."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    # Heart path (centered roughly)
    cx, cy = int(w * 0.35), int(h * 0.5)
    s = 70 + rng() * 10
    # Smooth heart via cubic curves
    parts.append(
        f'<path d="M {cx} {cy + s*0.5} '
        f'C {cx - s*1.1} {cy - s*0.1}, {cx - s*0.55} {cy - s*0.7}, {cx} {cy - s*0.25} '
        f'C {cx + s*0.55} {cy - s*0.7}, {cx + s*1.1} {cy - s*0.1}, {cx} {cy + s*0.5} Z" '
        f'fill="{light}" stroke="{dark}" stroke-width="1.4" opacity="0.92"/>'
    )
    # Inner highlight
    parts.append(
        f'<path d="M {cx - s*0.25} {cy - s*0.32} C {cx - s*0.1} {cy - s*0.45}, {cx - s*0.05} {cy - s*0.35}, {cx - s*0.15} {cy - s*0.18}" '
        f'fill="none" stroke="white" stroke-width="2.5" opacity="0.55"/>'
    )
    # Pulse trace across entire width
    py = int(h * 0.78)
    parts.append(
        f'<path d="M 10 {py} L {w*0.25:.0f} {py} L {w*0.32:.0f} {py - 18} L {w*0.36:.0f} {py + 22} L {w*0.42:.0f} {py - 8} L {w*0.5:.0f} {py} L {w-10:.0f} {py}" '
        f'fill="none" stroke="{accent}" stroke-width="1.8" opacity="0.7" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    # Faint pulse echo
    parts.append(
        f'<path d="M 10 {py + 8} L {w-10:.0f} {py + 8}" stroke="{dark}" stroke-width="0.4" opacity="0.25"/>'
    )
    return "".join(parts)


def _scene_brain(w, h, rng, palette):
    """Organic brain-suggesting curves + neural sparks — cognition."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    # Soft mass on the right
    cx, cy = int(w * 0.65), int(h * 0.5)
    # Outer blob
    parts.append(
        f'<ellipse cx="{cx}" cy="{cy}" rx="100" ry="80" fill="{light}" '
        f'stroke="{dark}" stroke-width="1.4" opacity="0.85"/>'
    )
    # Brain-like fold curves
    for i in range(5):
        y_off = -45 + i * 22
        parts.append(
            f'<path d="M {cx - 80} {cy + y_off} C {cx - 30} {cy + y_off - 18}, '
            f'{cx + 30} {cy + y_off + 16}, {cx + 80} {cy + y_off}" '
            f'fill="none" stroke="{dark}" stroke-width="1.0" opacity="{0.45 + i*0.08:.2f}"/>'
        )
    # Neural connection nodes on the left
    nodes = [(int(w*0.15 + rng()*30), int(h*0.2 + rng()*h*0.6)) for _ in range(7)]
    for i, (x, y) in enumerate(nodes):
        parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{accent}"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{accent}" opacity="0.18"/>')
        if i > 0:
            x0, y0 = nodes[i - 1]
            parts.append(
                f'<line x1="{x0}" y1="{y0}" x2="{x}" y2="{y}" '
                f'stroke="{accent}" stroke-width="0.7" opacity="0.55"/>'
            )
    # Bridge from neural net into the brain
    if nodes:
        x0, y0 = nodes[-1]
        parts.append(
            f'<line x1="{x0}" y1="{y0}" x2="{cx - 90}" y2="{cy}" '
            f'stroke="{accent}" stroke-width="0.8" opacity="0.5"/>'
        )
    return "".join(parts)


def _scene_sleep(w, h, rng, palette):
    """Crescent moon + scattered stars + soft horizon — sleep topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    # Soft sky gradient suggestion: a horizon line
    parts.append(
        f'<path d="M 0 {h*0.78:.0f} L {w} {h*0.78:.0f}" stroke="{light}" stroke-width="1" opacity="0.35"/>'
    )
    # Crescent moon
    mx, my, mr = int(w * 0.62), int(h * 0.42), 56
    parts.append(f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="{light}" opacity="0.95"/>')
    # Carve out the crescent
    parts.append(f'<circle cx="{mx + 22}" cy="{my - 6}" r="{mr - 6}" fill="{surface}" opacity="1"/>')
    # Soft halo
    parts.append(f'<circle cx="{mx}" cy="{my}" r="{mr + 14}" fill="none" stroke="{accent}" stroke-width="0.5" opacity="0.45"/>')
    # Stars
    for _ in range(14):
        x = int(rng() * w)
        y = int(rng() * h * 0.7)
        s = 1 + rng() * 2.5
        col = "#c9a961" if rng() < 0.7 else dark
        parts.append(
            f'<g transform="translate({x} {y})">'
            f'<line x1="-{s:.1f}" y1="0" x2="{s:.1f}" y2="0" stroke="{col}" stroke-width="0.7" opacity="0.85"/>'
            f'<line x1="0" y1="-{s:.1f}" x2="0" y2="{s:.1f}" stroke="{col}" stroke-width="0.7" opacity="0.85"/>'
            f'</g>'
        )
    # Small "Z" cluster bottom-left for sleep
    zx, zy = int(w * 0.12), int(h * 0.7)
    parts.append(
        f'<text x="{zx}" y="{zy}" font-family="Fraunces, serif" font-size="22" '
        f'fill="{dark}" opacity="0.5">z</text>'
        f'<text x="{zx + 12}" y="{zy - 14}" font-family="Fraunces, serif" font-size="16" '
        f'fill="{dark}" opacity="0.4">z</text>'
        f'<text x="{zx + 22}" y="{zy - 26}" font-family="Fraunces, serif" font-size="12" '
        f'fill="{dark}" opacity="0.3">z</text>'
    )
    return "".join(parts)


def _scene_motion(w, h, rng, palette):
    """Sweeping arcs + dashed trail + endpoint marker — exercise."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    for _ in range(4 + int(rng()*2)):
        cx = int(w * (0.2 + rng() * 0.6))
        cy = int(h * (0.4 + (rng()-0.5) * 0.4))
        r = 80 + rng() * 70
        a0 = rng() * math.pi
        a1 = a0 + math.pi * (0.45 + rng() * 0.5)
        x1 = cx + math.cos(a0) * r; y1 = cy + math.sin(a0) * r
        x2 = cx + math.cos(a1) * r; y2 = cy + math.sin(a1) * r
        sw = 2.4 + rng() * 1.5
        parts.append(
            f'<path d="M {x1:.0f} {y1:.0f} A {r:.0f} {r:.0f} 0 0 1 {x2:.0f} {y2:.0f}" '
            f'fill="none" stroke="{dark}" stroke-width="{sw:.1f}" '
            f'stroke-linecap="round" opacity="{0.55+rng()*0.3:.2f}"/>'
        )
        parts.append(f'<circle cx="{x2:.0f}" cy="{y2:.0f}" r="3.5" fill="{dark}"/>')
    # Footstep / trail dots along bottom
    for i in range(8):
        x = 30 + i * (w - 60) / 8
        y = h * 0.86 + (i % 2) * 8
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="{accent}" opacity="{0.55-(i*0.05):.2f}"/>')
    return "".join(parts)


def _scene_wave(w, h, rng, palette):
    """Layered horizontal waves + particle field — environmental, pollution, shift work."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    # 5 waves at varying y/amplitude
    for i in range(5):
        y0 = h * (0.18 + i * 0.16)
        amp = 14 + rng() * 22
        period = 70 + rng() * 30
        path = [f"M 0 {y0:.0f}"]
        x = 0
        toggle = 1
        while x < w:
            x += period / 2
            path.append(f"Q {x - period/4:.0f} {y0 + amp * toggle:.0f} {x:.0f} {y0:.0f}")
            toggle *= -1
        parts.append(
            f'<path d="{" ".join(path)}" fill="none" stroke="{dark}" '
            f'stroke-width="{0.8 + rng()*0.7:.1f}" opacity="{0.3+rng()*0.3:.2f}"/>'
        )
    for _ in range(35 + int(rng()*15)):
        x, y = rng()*w, rng()*h
        r = 0.7 + rng() * 1.6
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{accent}" opacity="{0.35+rng()*0.45:.2f}"/>')
    return "".join(parts)


def _scene_hexmolecule(w, h, rng, palette):
    """Three connected hexagons + bonds — drug/molecular topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    centers = [(int(w*0.3), int(h*0.5)), (int(w*0.55), int(h*0.4)), (int(w*0.78), int(h*0.55))]
    for cx, cy in centers:
        r = 32
        pts = []
        for i in range(6):
            ang = math.pi * i / 3
            pts.append(f"{cx+math.cos(ang)*r:.1f},{cy+math.sin(ang)*r:.1f}")
        parts.append(
            f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.5" '
            f'stroke="{dark}" stroke-width="1.4"/>'
        )
        for p in pts:
            x, y = p.split(",")
            parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{dark}"/>')
    # Bonds
    for i in range(len(centers)-1):
        x1, y1 = centers[i]; x2, y2 = centers[i+1]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{dark}" stroke-width="1.6" opacity="0.55"/>')
        parts.append(f'<line x1="{x1+5}" y1="{y1+4}" x2="{x2+5}" y2="{y2+4}" stroke="{dark}" stroke-width="0.8" opacity="0.4"/>')
    # Floating accent dots
    for _ in range(8):
        parts.append(f'<circle cx="{int(rng()*w)}" cy="{int(rng()*h)}" r="{1.5+rng():.1f}" fill="{accent}" opacity="0.65"/>')
    return "".join(parts)


def _scene_cellular(w, h, rng, palette):
    """Soft cellular cluster — microbiome / gut / IBD."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    n = 8 + int(rng() * 5)
    for _ in range(n):
        cx = int(rng() * w)
        cy = int(h * (0.2 + rng() * 0.6))
        r = 24 + rng() * 26
        m = 14
        pts = []
        for i in range(m):
            ang = 2 * math.pi * i / m
            rr = r * (0.85 + rng() * 0.32)
            pts.append(f"{cx + math.cos(ang)*rr:.0f},{cy + math.sin(ang)*rr:.0f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{light}" opacity="0.55" stroke="{dark}" stroke-width="0.9"/>')
        nucr = r * 0.32
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{nucr:.0f}" fill="{accent}" opacity="0.55"/>')
        parts.append(f'<circle cx="{cx-2}" cy="{cy-2}" r="{nucr*0.5:.0f}" fill="white" opacity="0.4"/>')
    return "".join(parts)


def _scene_berry(w, h, rng, palette):
    """Berry cluster + leaves — for berry/fruit topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx, cy = int(w * 0.55), int(h * 0.5)
    # Stem
    parts.append(f'<path d="M {cx - 30} {h - 20} Q {cx - 10} {cy + 20} {cx} {cy - 10}" stroke="{accent}" stroke-width="2" fill="none" opacity="0.7"/>')
    # Berries clustered
    for _ in range(9 + int(rng()*4)):
        bx = cx + int((rng() - 0.5) * 90)
        by = cy + int((rng() - 0.5) * 80)
        r = 11 + rng() * 4
        parts.append(f'<circle cx="{bx}" cy="{by}" r="{r:.0f}" fill="{dark}" opacity="0.92"/>')
        parts.append(f'<circle cx="{bx-3:.0f}" cy="{by-3:.0f}" r="{r*0.3:.1f}" fill="white" opacity="0.55"/>')
    # Leaf above
    parts.append(
        f'<ellipse cx="{cx + 8}" cy="{cy - 50}" rx="22" ry="9" fill="{light}" stroke="{accent}" stroke-width="0.7" '
        f'transform="rotate(30 {cx + 8} {cy - 50})" opacity="0.9"/>'
    )
    return "".join(parts)


def _scene_coffee(w, h, rng, palette):
    """Mug silhouette + steam swirls — coffee/tea topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx, cy = int(w * 0.38), int(h * 0.62)
    # Mug body
    parts.append(
        f'<rect x="{cx - 50}" y="{cy - 25}" width="80" height="64" rx="6" '
        f'fill="{light}" stroke="{dark}" stroke-width="1.6"/>'
    )
    # Coffee surface (ellipse)
    parts.append(
        f'<ellipse cx="{cx - 10}" cy="{cy - 25}" rx="40" ry="6" fill="{dark}" opacity="0.85"/>'
    )
    # Handle
    parts.append(
        f'<path d="M {cx + 30} {cy - 12} C {cx + 60} {cy - 12}, {cx + 60} {cy + 26}, {cx + 30} {cy + 26}" '
        f'fill="none" stroke="{dark}" stroke-width="3"/>'
    )
    # Saucer
    parts.append(
        f'<ellipse cx="{cx - 10}" cy="{cy + 44}" rx="56" ry="6" fill="{dark}" opacity="0.5"/>'
    )
    # Steam swirls
    for i in range(3):
        sx = cx - 30 + i * 18
        sy = cy - 35
        parts.append(
            f'<path d="M {sx} {sy} q -10 -16 0 -32 q 10 -16 0 -32" '
            f'fill="none" stroke="{accent}" stroke-width="1.6" opacity="{0.7 - i*0.15:.2f}" stroke-linecap="round"/>'
        )
    # Background accent dots
    for _ in range(10):
        parts.append(f'<circle cx="{int(rng()*w)}" cy="{int(rng()*h*0.4)}" r="{1+rng():.1f}" fill="{accent}" opacity="{0.3+rng()*0.4:.2f}"/>')
    return "".join(parts)


def _scene_alcohol(w, h, rng, palette):
    """Wine glass silhouette + droplets — alcohol topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx, cy = int(w * 0.42), int(h * 0.5)
    # Bowl
    parts.append(
        f'<path d="M {cx - 35} {cy - 30} '
        f'Q {cx - 35} {cy + 30} {cx} {cy + 35} '
        f'Q {cx + 35} {cy + 30} {cx + 35} {cy - 30} Z" '
        f'fill="{light}" stroke="{dark}" stroke-width="1.5"/>'
    )
    # Wine fill
    parts.append(
        f'<path d="M {cx - 32} {cy - 8} '
        f'Q {cx - 33} {cy + 28} {cx} {cy + 32} '
        f'Q {cx + 33} {cy + 28} {cx + 32} {cy - 8} '
        f'L {cx - 32} {cy - 8} Z" '
        f'fill="{dark}" opacity="0.78"/>'
    )
    # Highlight
    parts.append(
        f'<ellipse cx="{cx - 15}" cy="{cy + 12}" rx="6" ry="14" fill="white" opacity="0.3" transform="rotate(-20 {cx - 15} {cy + 12})"/>'
    )
    # Stem
    parts.append(f'<line x1="{cx}" y1="{cy + 35}" x2="{cx}" y2="{cy + 90}" stroke="{dark}" stroke-width="2"/>')
    # Base
    parts.append(f'<ellipse cx="{cx}" cy="{cy + 92}" rx="32" ry="5" fill="{dark}" opacity="0.85"/>')
    # Background droplets
    for _ in range(12):
        x, y = int(rng() * w), int(rng() * h)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{1+rng()*2:.1f}" fill="{accent}" opacity="{0.3+rng()*0.4:.2f}"/>')
    return "".join(parts)


def _scene_fish(w, h, rng, palette):
    """Stylized fish silhouette + ripples — fish/marine topics."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx, cy = int(w * 0.42), int(h * 0.5)
    # Fish body (almond shape)
    parts.append(
        f'<path d="M {cx - 60} {cy} '
        f'Q {cx - 25} {cy - 28} {cx + 35} {cy} '
        f'Q {cx - 25} {cy + 28} {cx - 60} {cy} Z" '
        f'fill="{light}" stroke="{dark}" stroke-width="1.4"/>'
    )
    # Tail
    parts.append(
        f'<path d="M {cx + 35} {cy} L {cx + 70} {cy - 22} L {cx + 60} {cy} L {cx + 70} {cy + 22} Z" '
        f'fill="{dark}" opacity="0.85"/>'
    )
    # Eye
    parts.append(f'<circle cx="{cx - 38}" cy="{cy - 4}" r="3" fill="{dark}"/>')
    # Gill
    parts.append(f'<path d="M {cx - 26} {cy - 16} Q {cx - 22} {cy} {cx - 26} {cy + 16}" stroke="{dark}" stroke-width="0.9" fill="none" opacity="0.6"/>')
    # Scales pattern
    for r_idx in range(3):
        for c_idx in range(5):
            sx = cx - 18 + c_idx * 12
            sy = cy - 12 + r_idx * 10 + (c_idx % 2) * 5
            parts.append(f'<path d="M {sx} {sy} q 5 -3 10 0" stroke="{dark}" stroke-width="0.5" fill="none" opacity="0.55"/>')
    # Ripples
    for r in (40, 70, 100):
        parts.append(f'<ellipse cx="{int(w*0.7)}" cy="{int(h*0.78)}" rx="{r}" ry="{r/4:.0f}" fill="none" stroke="{accent}" stroke-width="0.6" opacity="{0.5 - r/400:.2f}"/>')
    return "".join(parts)


def _scene_orbital(w, h, rng, palette):
    """Concentric orbital rings — fallback."""
    dark, light, accent, surface = palette
    parts: list[str] = []
    cx = int(w * (0.35 + rng() * 0.3))
    cy = int(h * (0.5 + (rng() - 0.5) * 0.2))
    n_rings = 6 + int(rng() * 3)
    for i in range(n_rings):
        rx = 50 + i * (40 + rng() * 24)
        ry = 28 + i * (22 + rng() * 16)
        rot = int(rng() * 180)
        opacity = 0.12 + 0.08 * (n_rings - i) / n_rings
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="none" stroke="{accent}" stroke-width="0.8" '
            f'opacity="{opacity:.2f}" transform="rotate({rot} {cx} {cy})"/>'
        )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="{dark}" opacity="0.8"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="none" stroke="{dark}" stroke-width="1" opacity="0.4"/>')
    # Ring dots
    for i in range(n_rings):
        ang = i * 0.85
        r = 50 + i * 38
        ox = cx + math.cos(ang) * r
        oy = cy + math.sin(ang) * r * 0.6
        parts.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="2.5" fill="{accent}"/>')
    return "".join(parts)


_SCENE_FUNCS = {
    "mediterranean": _scene_mediterranean,
    "supplement":    _scene_supplement,
    "botanical":     _scene_botanical,
    "heart":         _scene_heart,
    "brain":         _scene_brain,
    "sleep":         _scene_sleep,
    "motion":        _scene_motion,
    "wave":          _scene_wave,
    "hexmolecule":   _scene_hexmolecule,
    "cellular":      _scene_cellular,
    "berry":         _scene_berry,
    "coffee":        _scene_coffee,
    "alcohol":       _scene_alcohol,
    "fish":          _scene_fish,
    "orbital":       _scene_orbital,
}


# ---------------------------------------------------------------------------
# Backdrop with two soft washes — used by all card modes
# ---------------------------------------------------------------------------

def _backdrop(w: int, h: int, seed: int, *, c1: str, c2: str, surface: str) -> str:
    return f"""
<defs>
  <linearGradient id="bgL-{seed}" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%"  stop-color="{surface}"/>
    <stop offset="100%" stop-color="#f7f1e3"/>
  </linearGradient>
  <radialGradient id="bg1-{seed}" cx="30%" cy="35%" r="65%">
    <stop offset="0%"  stop-color="{c1}" stop-opacity="0.65"/>
    <stop offset="100%" stop-color="{surface}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="bg2-{seed}" cx="78%" cy="72%" r="62%">
    <stop offset="0%"  stop-color="{c2}" stop-opacity="0.55"/>
    <stop offset="100%" stop-color="{surface}" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="{w}" height="{h}" fill="url(#bgL-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg1-{seed})"/>
<rect width="{w}" height="{h}" fill="url(#bg2-{seed})"/>"""


# ---------------------------------------------------------------------------
# Public: featured_card_svg — premium full-bleed scene
# ---------------------------------------------------------------------------

def featured_card_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
                      factor_kind: str = "supplement", outcome_kind: str = "condition",
                      w: int = 600, h: int = 360) -> str:
    seed = _seed("featured", factor_slug, outcome_slug, tier)
    rng = _rng(seed)
    scene = _classify_scene(factor_slug, outcome_slug, factor_kind, outcome_kind)
    palette = _SCENE_PALETTE.get(scene, _SCENE_PALETTE["orbital"])
    dark, light, accent, surface = palette

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="{scene} scene for {factor_slug} → {outcome_slug}">'
    ]
    parts.append(_backdrop(w, h, seed, c1=light, c2=accent, surface=surface))
    parts.append(_SCENE_FUNCS[scene](w, h, rng, palette))
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Public: discovery_card_svg — lighter / more compact variant
# ---------------------------------------------------------------------------

def discovery_card_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
                       factor_kind: str = "supplement", outcome_kind: str = "condition",
                       w: int = 320, h: int = 160) -> str:
    """Same scene system as featured but smaller, lighter opacity, and
    rendered into a tighter aspect ratio so it doesn't fight the heading."""
    seed = _seed("discovery", factor_slug, outcome_slug, tier)
    rng = _rng(seed)
    scene = _classify_scene(factor_slug, outcome_slug, factor_kind, outcome_kind)
    palette = _SCENE_PALETTE.get(scene, _SCENE_PALETTE["orbital"])
    light = palette[1]; surface = palette[3]

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="{scene} motif for {factor_slug} → {outcome_slug}">'
    ]
    parts.append(_backdrop(w, h, seed, c1=light, c2=palette[2], surface=surface))
    # Wrap scene in a group at 70% opacity so it stays light
    parts.append('<g opacity="0.78">')
    parts.append(_SCENE_FUNCS[scene](w, h, rng, palette))
    parts.append('</g>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Public: strength_wave_svg — subtle bottom wave for evidence-strength buckets
# ---------------------------------------------------------------------------

def strength_wave_svg(tier: str = "C", w: int = 320, h: int = 60) -> str:
    """Subtle layered curves at the bottom — no scene art. Tier-tinted."""
    accent_dark, accent_light = _TIER_ACCENT.get(tier, _TIER_ACCENT["C"])
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="none" width="100%" height="100%" aria-hidden="true">'
    ]
    parts.append(f"""
<defs>
  <linearGradient id="wf1-{tier}" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0%"  stop-color="{accent_light}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{accent_light}" stop-opacity="0.7"/>
  </linearGradient>
</defs>""")
    # Layered wave fills
    parts.append(
        f'<path d="M 0 {h*0.7:.0f} '
        f'C {w*0.25:.0f} {h*0.5:.0f}, {w*0.5:.0f} {h*0.85:.0f}, {w*0.75:.0f} {h*0.65:.0f} '
        f'S {w} {h*0.7:.0f}, {w} {h*0.7:.0f} L {w} {h} L 0 {h} Z" '
        f'fill="url(#wf1-{tier})"/>'
    )
    parts.append(
        f'<path d="M 0 {h*0.85:.0f} '
        f'C {w*0.3:.0f} {h*0.7:.0f}, {w*0.6:.0f} {h*0.95:.0f}, {w}, {h*0.85:.0f} L {w} {h} L 0 {h} Z" '
        f'fill="{accent_dark}" opacity="0.18"/>'
    )
    # Dot stitch
    for i in range(8):
        x = (i + 0.5) * w / 8
        parts.append(f'<circle cx="{x:.0f}" cy="{h*0.92:.0f}" r="1.6" fill="{accent_dark}" opacity="0.7"/>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Public: edge_svg — kept simple for /tier and /category list pages
# ---------------------------------------------------------------------------

def edge_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
             factor_kind: str = "supplement",
             outcome_kind: str = "condition", w: int = 600, h: int = 280) -> str:
    """Lean orbital art for list pages — calmer than the featured cards.
    Codex feedback: original simpler treatment."""
    seed = _seed("edge", factor_slug, outcome_slug, tier)
    rng = _rng(seed)
    accent_dark, accent_light = _TIER_ACCENT.get(tier, _TIER_ACCENT["C"])

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'role="img" aria-label="illustration for {factor_slug} and {outcome_slug}">'
    ]
    parts.append(_backdrop(w, h, seed, c1=accent_light, c2=accent_light, surface="#fffdf6"))
    parts.append(_scene_orbital(w, h, rng, (accent_dark, accent_light, "#c9a961", "#fffdf6")))
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Hero globe (unchanged from rich version)
# ---------------------------------------------------------------------------

def hero_svg() -> str:
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
    parts.append('<circle cx="230" cy="230" r="200" fill="url(#globe-glow)"/>')
    parts.append('<circle cx="230" cy="230" r="170" fill="url(#globe)"/>')
    for i in range(20):
        parts.append(f'<ellipse cx="230" cy="230" rx="{40 + i*7}" ry="170" '
                     f'fill="none" stroke="#c9a961" stroke-width="0.4" opacity="0.4" '
                     f'transform="rotate({i*9} 230 230)"/>')
    for i in range(8):
        parts.append(f'<ellipse cx="230" cy="230" rx="170" ry="{40 + i*16}" '
                     f'fill="none" stroke="#c9a961" stroke-width="0.35" opacity="0.32" '
                     f'transform="rotate({i*22} 230 230)"/>')
    parts.append('<ellipse cx="230" cy="230" rx="195" ry="60" fill="none" '
                 'stroke="#c9a961" stroke-width="0.7" opacity="0.6" transform="rotate(-12 230 230)"/>')
    nodes = [(148, 142, 3.5), (210, 96, 3.0), (296, 132, 4.0), (340, 200, 3.0),
             (322, 290, 3.5), (240, 332, 3.0), (152, 322, 3.5), (108, 252, 3.0),
             (192, 200, 2.5), (272, 252, 3.0), (210, 252, 2.0), (164, 198, 2.5)]
    for x, y, r in nodes:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#c9a961"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r*2.5:.1f}" fill="#c9a961" opacity="0.18"/>')
    for a, b in [(0, 4), (1, 5), (2, 7), (3, 6), (8, 10)]:
        x1, y1, _ = nodes[a]; x2, y2, _ = nodes[b]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c9a961" stroke-width="0.5" opacity="0.5"/>')
    parts.append('<circle cx="425" cy="218" r="5" fill="#1f3a2e"/>')
    parts.append('<circle cx="38" cy="246" r="3.5" fill="#3b8e5a"/>')
    parts.append('</svg>')
    return "".join(parts)
